import os
import sqlite3
import json
import re
import math
import collections
import urllib.parse
import mimetypes
from datetime import datetime
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
DB_PATH = os.path.join(DATA_DIR, 'gemini_archive.db')
MEDIA_DIR = os.path.join(DATA_DIR, 'media')
TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates', 'index.html')
FRONTEND_BUILD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend', 'build')

CATEGORY_COLORS = {
    'ai_agents': '#c084fc',
    'software': '#38bdf8',
    'hardware': '#f59e0b',
    'creative': '#f43f5e',
    'finance': '#10b981',
    'outliers': '#64748b'
}

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def parse_iso_ts(ts_str):
    try:
        dt = datetime.strptime(ts_str[:19], '%Y-%m-%d %H:%M:%S')
        return dt.timestamp()
    except Exception:
        return 0

def is_noise_or_sensitive(text):
    if not text or not text.strip():
        return True
    t = text.strip().lower()
    
    # Short one-word fillers
    if len(t) < 8 and t in ['yes', 'yes.', 'no', 'no.', 'sure', 'sure.', 'okay', 'okay.', 'ok', 'ok.', 'thanks', 'hi', 'hello', 'bye']:
        return True
        
    # App launcher / system utility commands
    if (t.startswith('open ') or t.startswith('launch ') or t.startswith('go to ') or t.startswith('turn on ') or t.startswith('turn off ') or t.startswith('run ')) and len(t) < 40:
        return True

    # Sensitive keywords
    sensitive_keywords = ['password', 'passwd', 'secret_key', 'private_key', 'api_key', 'auth_token', 'credit card', 'cvv', 'social security', 'ssn']
    for kw in sensitive_keywords:
        if kw in t:
            return True
            
    return False

def get_analytics_data(cursor):
    cursor.execute('''
        SELECT substr(timestamp_iso, 1, 10) as date_key, COUNT(*) as cnt
        FROM chats
        WHERE timestamp_iso != "1970-01-01 00:00:00"
        GROUP BY date_key
        ORDER BY date_key ASC
    ''')
    daily_heatmap = {r['date_key']: r['cnt'] for r in cursor.fetchall()}

    cursor.execute('''
        SELECT substr(timestamp_iso, 12, 2) as hour, COUNT(*) as cnt
        FROM chats
        WHERE timestamp_iso != "1970-01-01 00:00:00"
        GROUP BY hour
        ORDER BY hour ASC
    ''')
    hourly = {int(r['hour']): r['cnt'] for r in cursor.fetchall() if r['hour'].isdigit()}

    cursor.execute('''
        SELECT id, COALESCE(NULLIF(thread_id, ''), CAST(id AS TEXT)) as group_key, timestamp_iso, media_files_json, prompt_text
        FROM chats
        WHERE media_files_json != '[]'
        ORDER BY timestamp_iso DESC
    ''')
    media_rows = cursor.fetchall()
    media_items = []
    for r in media_rows:
        try:
            files = json.loads(r['media_files_json'])
            for f in files:
                ext = f.split('.')[-1].lower() if '.' in f else 'file'
                media_items.append({
                    'filename': f,
                    'ext': ext,
                    'is_img': ext in ['jpg', 'jpeg', 'png', 'webp', 'gif', 'svg'],
                    'chat_id': r['id'],
                    'group_key': r['group_key'],
                    'timestamp': r['timestamp_iso'],
                    'snippet': (r['prompt_text'] or '')[:80]
                })
        except Exception:
            pass

    return {
        'daily_heatmap': daily_heatmap,
        'hourly_distribution': [hourly.get(h, 0) for h in range(24)],
        'media_items': media_items
    }

def get_categories_data(cursor):
    cursor.execute('''
        SELECT 
            tc.primary_category,
            COUNT(*) as thread_count,
            AVG(tc.outlier_score) as avg_outlier_score
        FROM thread_categories tc
        GROUP BY tc.primary_category
        ORDER BY thread_count DESC
    ''')
    cat_summary = [dict(r) for r in cursor.fetchall()]

    cursor.execute('''
        SELECT 
            tc.group_key,
            tc.primary_category,
            tc.keywords_json,
            tc.outlier_score,
            MIN(c.timestamp_iso) as first_timestamp,
            COUNT(*) as turn_count,
            c.prompt_text as title_snippet
        FROM thread_categories tc
        JOIN chats c ON tc.group_key = COALESCE(NULLIF(c.thread_id, ''), CAST(c.id AS TEXT))
        GROUP BY tc.group_key
        ORDER BY c.timestamp_iso DESC
    ''')
    threads = [dict(r) for r in cursor.fetchall()]

    return {
        'categories_summary': cat_summary,
        'threads': threads
    }

def get_data_driven_tags(cursor):
    cursor.execute('''
        SELECT tag_id, tag_label, thread_count, thread_keys_json
        FROM data_driven_tags
        ORDER BY thread_count DESC
        LIMIT 60
    ''')
    rows = cursor.fetchall()
    
    tags = []
    for r in rows:
        tags.append({
            'tag_id': r[0],
            'tag_label': r[1],
            'thread_count': r[2],
            'thread_keys': json.loads(r[3] or '[]')
        })
    return tags

def get_subgraph_search(cursor, q):
    if not q or not q.strip():
        return {
            'query': '',
            'matching_node_ids': [],
            'path_edge_ids': [],
            'snippets': {},
            'total_matches': 0,
            'threads': []
        }

    clean_q = q.strip()
    clean_terms = [t for t in re.sub(r'[^\w\s]', ' ', clean_q).split() if t.strip()]

    if not clean_terms:
        return {
            'query': q,
            'matching_node_ids': [],
            'path_edge_ids': [],
            'snippets': {},
            'total_matches': 0,
            'threads': []
        }

    like_conds = " AND ".join(["(c.prompt_text LIKE ? OR COALESCE(c.response_plain, '') LIKE ?)" for _ in clean_terms])
    params = []
    for term in clean_terms:
        p = f"%{term}%"
        params.extend([p, p])

    sql = f'''
        SELECT 
            COALESCE(NULLIF(c.thread_id, ''), CAST(c.id AS TEXT)) as group_key,
            c.id as turn_id,
            COALESCE(NULLIF(c.prompt_text, ''), 'Untitled Thread') as title,
            c.prompt_text,
            COALESCE(c.response_plain, '') as response_text,
            c.timestamp_iso
        FROM chats c
        WHERE {like_conds}
        ORDER BY c.timestamp_iso DESC
    '''
    cursor.execute(sql, params)
    rows = [dict(r) for r in cursor.fetchall()]

    matching_keys_set = set()
    snippets = {}
    threads_map = {}

    for r in rows:
        g_key = r['group_key']
        matching_keys_set.add(g_key)

        prompt = r['prompt_text'] or ''
        response = r['response_text'] or ''
        title = r['title'] or ''

        match_snippet = ""
        for term in clean_terms:
            low_p = prompt.lower()
            idx = low_p.find(term.lower())
            if idx >= 0:
                start = max(0, idx - 40)
                end = min(len(prompt), idx + 80)
                match_snippet = ("..." if start > 0 else "") + prompt[start:end] + ("..." if end < len(prompt) else "")
                break
            low_r = response.lower()
            idx_r = low_r.find(term.lower())
            if idx_r >= 0:
                start = max(0, idx_r - 40)
                end = min(len(response), idx_r + 80)
                match_snippet = ("..." if start > 0 else "") + response[start:end] + ("..." if end < len(response) else "")
                break

        if not match_snippet:
            match_snippet = title[:100]

        snippets[g_key] = match_snippet

        if g_key not in threads_map:
            threads_map[g_key] = {
                'id': g_key,
                'title': title,
                'snippet': match_snippet,
                'timestamp': r['timestamp_iso']
            }

    matching_node_ids = list(matching_keys_set)

    path_edge_ids = []
    if len(matching_node_ids) >= 2:
        placeholders = ",".join(["?"] * len(matching_node_ids))
        edge_sql = f'''
            SELECT source_key, target_key, similarity_score
            FROM thread_relations
            WHERE source_key IN ({placeholders}) AND target_key IN ({placeholders})
        '''
        cursor.execute(edge_sql, matching_node_ids + matching_node_ids)
        edge_rows = [dict(r) for r in cursor.fetchall()]
        for e in edge_rows:
            path_edge_ids.append({
                'source': e['source_key'],
                'target': e['target_key'],
                'score': round(e['similarity_score'], 3)
            })

    return {
        'query': clean_q,
        'matching_node_ids': matching_node_ids,
        'path_edge_ids': path_edge_ids,
        'snippets': snippets,
        'total_matches': len(matching_node_ids),
        'threads': list(threads_map.values())
    }

def get_overlap_data(cursor, min_similarity=0.38, category="", topic="", limit=2000):
    # Fetch all clean threads from category taxonomy and data-driven tags
    cursor.execute('''
        SELECT 
            tc.group_key as id,
            COALESCE(tc.primary_category, 'outliers') as category,
            COALESCE(tc.actionability_tier, 'one_off') as actionability_tier,
            COALESCE(tdt.primary_tag, 'general') as data_tag,
            tc.actionability_tags_json,
            MIN(c.timestamp_iso) as timestamp,
            c.prompt_text as title,
            COUNT(*) as turn_count
        FROM thread_categories tc
        JOIN chats c ON tc.group_key = COALESCE(NULLIF(c.thread_id, ''), CAST(c.id AS TEXT))
        LEFT JOIN thread_data_tags tdt ON tc.group_key = tdt.group_key
        GROUP BY tc.group_key
    ''')
    all_cat_nodes = [dict(r) for r in cursor.fetchall()]
    
    # Filter out noise & sensitive nodes
    clean_nodes_map = {}
    for n in all_cat_nodes:
        if not is_noise_or_sensitive(n['title']):
            n['color'] = CATEGORY_COLORS.get(n['category'], '#64748b')
            try:
                n['actionability_tags'] = json.loads(n.get('actionability_tags_json') or '[]')
            except Exception:
                n['actionability_tags'] = []
            clean_nodes_map[n['id']] = n

    params = [min_similarity]
    extra_clause = ""

    if category:
        extra_clause += " AND (tc1.primary_category = ? OR tc2.primary_category = ?)"
        params.extend([category, category])

    if topic:
        extra_clause += " AND tr.shared_topics_json LIKE ?"
        params.append(f'%{topic}%')

    params.append(limit)

    query_sql = f'''
        SELECT 
            tr.source_key,
            tr.target_key,
            tr.similarity_score,
            tr.shared_topics_json,
            tc1.primary_category as source_category,
            tc2.primary_category as target_category
        FROM thread_relations tr
        LEFT JOIN thread_categories tc1 ON tr.source_key = tc1.group_key
        LEFT JOIN thread_categories tc2 ON tr.target_key = tc2.group_key
        WHERE tr.similarity_score >= ? {extra_clause}
        ORDER BY tr.similarity_score DESC
        LIMIT ?
    '''
    cursor.execute(query_sql, params)
    relations_raw = [dict(r) for r in cursor.fetchall()]

    # Batch fetch snippets for involved keys
    keys_needed = set()
    for rel in relations_raw:
        keys_needed.add(rel['source_key'])
        keys_needed.add(rel['target_key'])

    snippets_map = {}
    timestamps_map = {}

    if keys_needed:
        placeholders = ','.join('?' for _ in keys_needed)
        cursor.execute(f'''
            SELECT 
                COALESCE(NULLIF(thread_id, ''), CAST(id AS TEXT)) as gk,
                prompt_text,
                timestamp_iso
            FROM chats
            WHERE COALESCE(NULLIF(thread_id, ''), CAST(id AS TEXT)) IN ({placeholders})
            GROUP BY gk
        ''', list(keys_needed))
        for r in cursor.fetchall():
            snippets_map[r['gk']] = (r['prompt_text'] or '')[:80]
            timestamps_map[r['gk']] = r['timestamp_iso']

    relations = []
    topic_counts = {}

    for rel in relations_raw:
        s_key = rel['source_key']
        t_key = rel['target_key']

        s_snippet = snippets_map.get(s_key, 'Thread A')
        t_snippet = snippets_map.get(t_key, 'Thread B')

        # Skip relations involving noise or sensitive prompts
        if is_noise_or_sensitive(s_snippet) or is_noise_or_sensitive(t_snippet):
            continue

        s_ts = timestamps_map.get(s_key, '')
        t_ts = timestamps_map.get(t_key, '')

        rel['source_snippet'] = s_snippet
        rel['target_snippet'] = t_snippet
        rel['source_ts'] = s_ts
        rel['target_ts'] = t_ts

        relations.append(rel)

        try:
            topics = json.loads(rel.get('shared_topics_json', '[]'))
            for t in topics:
                topic_counts[t] = topic_counts.get(t, 0) + 1
        except Exception:
            pass

    sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:25]

    return {
        'total_links': len(relations),
        'nodes': list(clean_nodes_map.values()),
        'relations': relations,
        'top_topics': [t[0] for t in sorted_topics]
    }

def get_domain_matrix_data(cursor, min_similarity=0.38):
    cursor.execute('''
        SELECT 
            COALESCE(tc1.primary_category, 'outliers') as source_cat,
            COALESCE(tc2.primary_category, 'outliers') as target_cat,
            COUNT(*) as link_count
        FROM thread_relations tr
        LEFT JOIN thread_categories tc1 ON tr.source_key = tc1.group_key
        LEFT JOIN thread_categories tc2 ON tr.target_key = tc2.group_key
        WHERE tr.similarity_score >= ?
        GROUP BY source_cat, target_cat
        ORDER BY link_count DESC
    ''', (min_similarity,))
    rows = cursor.fetchall()
    
    matrix = [dict(r) for r in rows]
    categories = list(CATEGORY_COLORS.keys())

    return {
        'categories': categories,
        'matrix': matrix
    }

def get_correlation_spectrum_data(cursor, min_similarity=0.30):
    # 1. Get all similarity scores for histogram bucketing
    cursor.execute('SELECT similarity_score FROM thread_relations')
    all_scores = [r[0] for r in cursor.fetchall()]
    total_pairs = len(all_scores)

    # 2. Build 5% width histogram buckets (15% to 100%)
    bucket_counts = {round(b / 100.0, 2): 0 for b in range(15, 100, 5)}
    for s in all_scores:
        b_key = round(max(0.15, min(0.95, (int(s * 100 // 5) * 5) / 100.0)), 2)
        if b_key in bucket_counts:
            bucket_counts[b_key] += 1

    buckets = []
    for b_min in sorted(bucket_counts.keys()):
        b_max = round(b_min + 0.05, 2)
        c = bucket_counts[b_min]
        buckets.append({
            'min': b_min,
            'max': b_max,
            'min_pct': int(b_min * 100),
            'max_pct': int(b_max * 100),
            'label': f"{int(b_min * 100)}–{int(b_max * 100)}%",
            'count': c,
            'is_qualified': b_min >= min_similarity
        })

    # 3. Qualified Slice Telemetry
    cursor.execute('''
        SELECT COUNT(*) FROM thread_relations WHERE similarity_score >= ?
    ''', (min_similarity,))
    tel_row = cursor.fetchone()
    qualified_pairs = tel_row[0] if tel_row else 0

    # 4. Fast Title Map & Sample Pairs Fetch
    cursor.execute('''
        SELECT 
            COALESCE(NULLIF(thread_id, ''), CAST(id AS TEXT)) as gk,
            COALESCE(prompt_text, '') as title
        FROM chats
        GROUP BY gk
    ''')
    title_map = {r[0]: (r[1] or '').strip()[:70] for r in cursor.fetchall()}

    cursor.execute('''
        SELECT 
            tr.source_key,
            tr.target_key,
            tr.similarity_score,
            tr.shared_topics_json,
            COALESCE(tc1.primary_category, 'outliers') as source_cat,
            COALESCE(tc2.primary_category, 'outliers') as target_cat
        FROM thread_relations tr
        LEFT JOIN thread_categories tc1 ON tr.source_key = tc1.group_key
        LEFT JOIN thread_categories tc2 ON tr.target_key = tc2.group_key
        WHERE tr.similarity_score >= ?
        ORDER BY tr.similarity_score DESC
        LIMIT 40
    ''', (min_similarity,))
    sample_rows = cursor.fetchall()

    sample_pairs = []
    for r in sample_rows:
        shared = []
        try:
            shared = json.loads(r[3] or '[]')
        except:
            pass

        s_key = r[0]
        t_key = r[1]
        sample_pairs.append({
            'source_key': s_key,
            'target_key': t_key,
            'similarity_score': round(r[2], 3),
            'similarity_pct': int(round(r[2] * 100)),
            'source_title': title_map.get(s_key, s_key),
            'target_title': title_map.get(t_key, t_key),
            'source_cat': r[4],
            'target_cat': r[5],
            'shared_topics': shared
        })

    return {
        'threshold': min_similarity,
        'threshold_pct': int(round(min_similarity * 100)),
        'total_pairs': total_pairs,
        'qualified_pairs': qualified_pairs,
        'buckets': buckets,
        'sample_pairs': sample_pairs
    }

def get_mindmap_tree_data(cursor):
    cursor.execute('SELECT COUNT(*) FROM chats')
    total_chats = cursor.fetchone()[0]

    cursor.execute('''
        SELECT 
            COALESCE(NULLIF(c.thread_id, ''), CAST(c.id AS TEXT)) as group_key,
            COALESCE(tc.primary_category, 'outliers') as category,
            COALESCE(tc.actionability_tier, 'one_off') as actionability_tier,
            COUNT(*) as turn_count,
            MAX(c.was_audio_input) as has_audio,
            MIN(c.timestamp_iso) as first_ts,
            COALESCE(c.prompt_text, '') as title
        FROM chats c
        LEFT JOIN thread_categories tc ON COALESCE(NULLIF(c.thread_id, ''), CAST(c.id AS TEXT)) = tc.group_key
        WHERE c.timestamp_iso != "1970-01-01 00:00:00"
        GROUP BY group_key
        ORDER BY first_ts DESC
    ''')
    thread_rows = cursor.fetchall()
    total_threads = len(thread_rows)

    cursor.execute('''
        SELECT source_key, target_key, similarity_score, shared_topics_json
        FROM thread_relations
        WHERE similarity_score >= 0.35
        ORDER BY similarity_score DESC
    ''')
    rel_rows = cursor.fetchall()

    rel_map = collections.defaultdict(list)
    for r in rel_rows:
        s_key, t_key, sim = r[0], r[1], r[2]
        rel_map[s_key].append({'target': t_key, 'sim_pct': int(round(sim * 100))})
        rel_map[t_key].append({'target': s_key, 'sim_pct': int(round(sim * 100))})

    tree = {
        'id': 'root',
        'name': '🌐 Gemini Archive',
        'thread_count': total_threads,
        'chat_count': total_chats,
        'children': []
    }

    category_threads = collections.defaultdict(list)
    for r in thread_rows:
        category_threads[r[1]].append({
            'id': r[0],
            'category': r[1],
            'tier': r[2],
            'turn_count': r[3],
            'has_audio': r[4],
            'first_ts': r[5],
            'title': (r[6] or '').strip()[:70],
            'matches': rel_map.get(r[0], [])[:3]
        })

    cat_labels = {
        'ai_agents': ('🤖 AI Agents', '#c084fc'),
        'software': ('💻 Software Engineering', '#38bdf8'),
        'hardware': ('🛠️ Hardware & Electronics', '#34d399'),
        'creative': ('🎨 Creative & Content', '#f59e0b'),
        'finance': ('💼 Finance & Markets', '#f43f5e'),
        'outliers': ('🔬 Specialty & Outliers', '#94a3b8')
    }

    tier_labels = {
        'large_project': '🚀 Large Projects',
        'specialty_project': '🔬 Specialty Projects',
        'small_project': '📌 Small Projects',
        'journal': '📔 Journal Entries',
        'theory': '💡 Theories & Ideas',
        'one_off': '💬 One-off Chats'
    }

    for cat_key, (cat_name, cat_color) in cat_labels.items():
        cat_items = category_threads[cat_key]
        if not cat_items:
            continue

        domain_node = {
            'id': f'domain_{cat_key}',
            'name': cat_name,
            'color': cat_color,
            'thread_count': len(cat_items),
            'children': []
        }

        tier_groups = collections.defaultdict(list)
        for item in cat_items:
            tier_groups[item['tier']].append(item)

        for tier_key, tier_name in tier_labels.items():
            t_items = tier_groups[tier_key]
            if not t_items:
                continue

            tier_node = {
                'id': f'tier_{cat_key}_{tier_key}',
                'name': tier_name,
                'color': cat_color,
                'thread_count': len(t_items),
                'children': [
                    {
                        'id': item['id'],
                        'name': item['title'],
                        'category': cat_key,
                        'tier': item['tier'],
                        'turn_count': item['turn_count'],
                        'has_audio': item['has_audio'],
                        'first_ts': item['first_ts'],
                        'matches': item['matches']
                    }
                    for item in t_items[:20]
                ]
            }
            domain_node['children'].append(tier_node)

        tree['children'].append(domain_node)

    return tree

def get_canvas_constellation_data(cursor, granularity='chat'):
    if granularity == 'year':
        group_expr = "substr(timestamp_iso, 1, 4)"
    elif granularity == 'month':
        group_expr = "substr(timestamp_iso, 1, 7)"
    elif granularity == 'week':
        group_expr = "strftime('%Y-%W', timestamp_iso)"
    elif granularity == 'day':
        group_expr = "substr(timestamp_iso, 1, 10)"
    else: # chat
        group_expr = "COALESCE(NULLIF(thread_id, ''), CAST(id AS TEXT))"

    if granularity == 'chat':
        cursor.execute('''
            SELECT 
                COALESCE(NULLIF(thread_id, ''), CAST(id AS TEXT)) as group_key,
                thread_id,
                MIN(timestamp_iso) as first_timestamp,
                MAX(timestamp_iso) as last_timestamp,
                COUNT(*) as turn_count,
                MAX(was_audio_input) as has_audio_input,
                prompt_text as title_snippet,
                details_url
            FROM chats
            WHERE timestamp_iso != "1970-01-01 00:00:00"
            GROUP BY group_key
            ORDER BY first_timestamp ASC
        ''')
        rows = cursor.fetchall()

        threads_list = []
        all_ts = []
        for r in rows:
            ts_start = parse_iso_ts(r['first_timestamp'])
            ts_end = parse_iso_ts(r['last_timestamp'])
            if ts_start > 0: all_ts.append(ts_start)

            turn_cnt = r['turn_count']
            log_scale = math.log10(1 + turn_cnt)

            threads_list.append({
                'group_key': r['group_key'],
                'thread_id': r['thread_id'] or "",
                'first_timestamp': r['first_timestamp'],
                'last_timestamp': r['last_timestamp'],
                'ts_unix': ts_start,
                'turn_count': turn_cnt,
                'has_audio_input': r['has_audio_input'],
                'log_scale': round(log_scale, 3),
                'title_snippet': (r['title_snippet'] or '')[:120],
                'details_url': r['details_url'] or ""
            })

        min_ts = min(all_ts) if all_ts else 0
        max_ts = max(all_ts) if all_ts else 1

        return {
            'granularity': 'chat',
            'min_ts': min_ts,
            'max_ts': max_ts,
            'total_threads': len(threads_list),
            'total_dots': len(threads_list),
            'threads': threads_list
        }
    else:
        cursor.execute(f'''
            SELECT 
                {group_expr} as period_key,
                MIN(timestamp_iso) as first_timestamp,
                MAX(timestamp_iso) as last_timestamp,
                COUNT(DISTINCT COALESCE(NULLIF(thread_id, ''), CAST(id AS TEXT))) as thread_count,
                COUNT(*) as turn_count,
                MAX(was_audio_input) as has_audio_input,
                prompt_text as title_snippet
            FROM chats
            WHERE timestamp_iso != "1970-01-01 00:00:00"
            GROUP BY period_key
            ORDER BY first_timestamp ASC
        ''')
        rows = cursor.fetchall()

        nodes = []
        all_ts = []
        for r in rows:
            t_start = parse_iso_ts(r['first_timestamp'])
            t_end = parse_iso_ts(r['last_timestamp'])
            if t_start > 0: all_ts.append(t_start)
            if t_end > 0: all_ts.append(t_end)

            log_turns = math.log10(1 + r['turn_count'])
            log_chats = math.log10(1 + r['thread_count'])

            nodes.append({
                'period_key': r['period_key'],
                'first_timestamp': r['first_timestamp'],
                'last_timestamp': r['last_timestamp'],
                'start_ts': t_start,
                'end_ts': t_end,
                'thread_count': r['thread_count'],
                'turn_count': r['turn_count'],
                'has_audio_input': r['has_audio_input'],
                'log_turns': round(log_turns, 3),
                'log_chats': round(log_chats, 3),
                'title_snippet': (r['title_snippet'] or '')[:100]
            })

        min_ts = min(all_ts) if all_ts else 0
        max_ts = max(all_ts) if all_ts else 1

        return {
            'granularity': granularity,
            'min_ts': min_ts,
            'max_ts': max_ts,
            'total_nodes': len(nodes),
            'nodes': nodes
        }

def get_stitched_threads(cursor, q="", sort="desc", audio_only=0, category="", tier="", thread_id="", limit=20, offset=0):
    audio_clause = "AND c.was_audio_input = 1" if audio_only else ""
    cat_clause = "AND tc.primary_category = ?" if category else ""
    tier_clause = "AND tc.actionability_tier = ?" if tier else ""
    order_clause = "DESC" if sort == "desc" else "ASC"

    params_count = []
    if category: params_count.append(category)
    if tier: params_count.append(tier)

    if thread_id:
        group_keys = [(thread_id, thread_id)]
        total = 1
    elif not q or not q.strip():
        count_sql = f'''
            SELECT COUNT(DISTINCT COALESCE(NULLIF(c.thread_id, ''), CAST(c.id AS TEXT)))
            FROM chats c
            LEFT JOIN thread_categories tc ON COALESCE(NULLIF(c.thread_id, ''), CAST(c.id AS TEXT)) = tc.group_key
            WHERE 1=1 {audio_clause} {cat_clause} {tier_clause}
        '''
        cursor.execute(count_sql, params_count)
        total = cursor.fetchone()[0]

        groups_sql = f'''
            SELECT 
                COALESCE(NULLIF(c.thread_id, ''), CAST(c.id AS TEXT)) as group_key,
                c.thread_id,
                MAX(c.timestamp_iso) as max_ts
            FROM chats c
            LEFT JOIN thread_categories tc ON COALESCE(NULLIF(c.thread_id, ''), CAST(c.id AS TEXT)) = tc.group_key
            WHERE 1=1 {audio_clause} {cat_clause} {tier_clause}
            GROUP BY group_key
            ORDER BY max_ts {order_clause}
            LIMIT ? OFFSET ?
        '''
        params_groups = list(params_count) + [limit, offset]
        cursor.execute(groups_sql, params_groups)
        group_keys = [(r['group_key'], r['thread_id']) for r in cursor.fetchall()]
    else:
        clean_terms = [t for t in re.sub(r'[^\w\s]', ' ', q).split() if t.strip()]
        if not clean_terms:
            fts_query = f'"{q.strip()}*"'
        else:
            fts_query = ' AND '.join(f'"{t}*"' for t in clean_terms)

        try:
            count_sql = f'''
                SELECT COUNT(DISTINCT COALESCE(NULLIF(c.thread_id, ''), CAST(c.id AS TEXT)))
                FROM chats c
                JOIN chats_fts fts ON c.id = fts.rowid
                LEFT JOIN thread_categories tc ON COALESCE(NULLIF(c.thread_id, ''), CAST(c.id AS TEXT)) = tc.group_key
                WHERE chats_fts MATCH ? {audio_clause} {cat_clause} {tier_clause}
            '''
            cursor.execute(count_sql, [fts_query] + params_count)
            total = cursor.fetchone()[0]

            groups_sql = f'''
                SELECT 
                    COALESCE(NULLIF(c.thread_id, ''), CAST(c.id AS TEXT)) as group_key,
                    c.thread_id,
                    MAX(c.timestamp_iso) as max_ts
                FROM chats c
                JOIN chats_fts fts ON c.id = fts.rowid
                LEFT JOIN thread_categories tc ON COALESCE(NULLIF(c.thread_id, ''), CAST(c.id AS TEXT)) = tc.group_key
                WHERE chats_fts MATCH ? {audio_clause} {cat_clause} {tier_clause}
                GROUP BY group_key
                ORDER BY max_ts {order_clause}
                LIMIT ? OFFSET ?
            '''
            cursor.execute(groups_sql, [fts_query] + params_count + [limit, offset])
            group_keys = [(r['group_key'], r['thread_id']) for r in cursor.fetchall()]
        except Exception:
            like_term = f'%{q.strip()}%'
            count_sql = f'''
                SELECT COUNT(DISTINCT COALESCE(NULLIF(c.thread_id, ''), CAST(c.id AS TEXT)))
                FROM chats c
                LEFT JOIN thread_categories tc ON COALESCE(NULLIF(c.thread_id, ''), CAST(c.id AS TEXT)) = tc.group_key
                WHERE (c.prompt_text LIKE ? OR c.response_plain LIKE ?) {audio_clause} {cat_clause} {tier_clause}
            '''
            cursor.execute(count_sql, [like_term, like_term] + params_count)
            total = cursor.fetchone()[0]

            groups_sql = f'''
                SELECT 
                    COALESCE(NULLIF(c.thread_id, ''), CAST(c.id AS TEXT)) as group_key,
                    c.thread_id,
                    MAX(c.timestamp_iso) as max_ts
                FROM chats c
                LEFT JOIN thread_categories tc ON COALESCE(NULLIF(c.thread_id, ''), CAST(c.id AS TEXT)) = tc.group_key
                WHERE (c.prompt_text LIKE ? OR c.response_plain LIKE ?) {audio_clause} {cat_clause} {tier_clause}
                GROUP BY group_key
                ORDER BY max_ts {order_clause}
                LIMIT ? OFFSET ?
            '''
            cursor.execute(groups_sql, [like_term, like_term] + params_count + [limit, offset])
            group_keys = [(r['group_key'], r['thread_id']) for r in cursor.fetchall()]

    threads_out = []

    for group_key, t_id in group_keys:
        if t_id:
            cursor.execute('''
                SELECT id, thread_id, timestamp_iso, timestamp_raw, prompt_text, response_html, response_plain, media_files_json, details_url, was_audio_input
                FROM chats
                WHERE thread_id = ?
                ORDER BY timestamp_iso ASC
            ''', (t_id,))
        else:
            cursor.execute('''
                SELECT id, thread_id, timestamp_iso, timestamp_raw, prompt_text, response_html, response_plain, media_files_json, details_url, was_audio_input
                FROM chats
                WHERE id = ?
            ''', (group_key,))
            
        rows = [dict(r) for r in cursor.fetchall()]
        if not rows:
            continue

        first_ts = rows[0]['timestamp_iso']
        last_ts = rows[-1]['timestamp_iso']
        has_audio = any(r['was_audio_input'] == 1 for r in rows)
        details_url = next((r['details_url'] for r in rows if r['details_url']), "")

        threads_out.append({
            'group_key': group_key,
            'thread_id': t_id or "",
            'turn_count': len(rows),
            'first_timestamp': first_ts,
            'last_timestamp': last_ts,
            'has_audio_input': 1 if has_audio else 0,
            'details_url': details_url,
            'turns': rows
        })

    return total, threads_out

class ArchiveRequestHandler(BaseHTTPRequestHandler):

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        svelte_index = os.path.join(FRONTEND_BUILD_DIR, 'index.html')
        if (path == '/' or path == '/index.html') and os.path.exists(svelte_index):
            with open(svelte_index, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return

        if path.startswith('/_app/'):
            asset_path = os.path.join(FRONTEND_BUILD_DIR, path.lstrip('/'))
            if os.path.exists(asset_path) and os.path.isfile(asset_path):
                ctype, _ = mimetypes.guess_type(asset_path)
                if not ctype: ctype = 'application/octet-stream'
                with open(asset_path, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', ctype)
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return

        if path == '/' or path == '/index.html':
            if os.path.exists(TEMPLATE_PATH):
                with open(TEMPLATE_PATH, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, "Template index.html not found")
            return

        if path == '/api/stats':
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM chats')
            total_chats = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM chats WHERE was_audio_input = 1')
            voice_chats = cursor.fetchone()[0]
            cursor.execute('''
                SELECT COUNT(DISTINCT COALESCE(NULLIF(thread_id, ''), CAST(id AS TEXT))) FROM chats
            ''')
            total_threads = cursor.fetchone()[0]
            conn.close()
            self.send_json({
                'total_chats': total_chats,
                'voice_chats': voice_chats,
                'total_threads': total_threads
            })
            return

        if path == '/api/analytics':
            conn = get_db()
            cursor = conn.cursor()
            data = get_analytics_data(cursor)
            conn.close()
            self.send_json(data)
            return

        if path == '/api/categories':
            conn = get_db()
            cursor = conn.cursor()
            data = get_categories_data(cursor)
            conn.close()
            self.send_json(data)
            return

        if path == '/api/overlap':
            min_sim = float(query.get('min_similarity', ['0.38'])[0] or '0.38')
            cat = query.get('category', [''])[0]
            topic = query.get('topic', [''])[0]
            limit = int(query.get('limit', ['150'])[0] or '150')

            conn = get_db()
            cursor = conn.cursor()
            data = get_overlap_data(cursor, min_sim, cat, topic, limit)
            conn.close()
            self.send_json(data)
            return

        if path == '/api/domain_matrix':
            min_sim = float(query.get('min_similarity', ['0.38'])[0] or '0.38')
            conn = get_db()
            cursor = conn.cursor()
            data = get_domain_matrix_data(cursor, min_sim)
            conn.close()
            self.send_json(data)
            return

        if path == '/api/correlation_stats':
            min_sim = float(query.get('min_similarity', ['0.30'])[0] or '0.30')
            conn = get_db()
            cursor = conn.cursor()
            data = get_correlation_spectrum_data(cursor, min_sim)
            conn.close()
            self.send_json(data)
            return

        if path == '/api/mindmap_tree':
            conn = get_db()
            cursor = conn.cursor()
            data = get_mindmap_tree_data(cursor)
            conn.close()
            self.send_json(data)
            return

        if path == '/api/search_subgraph':
            q_val = query.get('q', [''])[0]
            conn = get_db()
            cursor = conn.cursor()
            data = get_subgraph_search(cursor, q_val)
            conn.close()
            self.send_json(data)
            return

        if path == '/api/data_tags':
            conn = get_db()
            cursor = conn.cursor()
            data = get_data_driven_tags(cursor)
            conn.close()
            self.send_json(data)
            return

        if path == '/api/canvas':
            granularity = query.get('granularity', ['chat'])[0]
            conn = get_db()
            cursor = conn.cursor()
            data = get_canvas_constellation_data(cursor, granularity)
            conn.close()
            self.send_json(data)
            return

        if path == '/api/actionability_stats':
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    COALESCE(tc.actionability_tier, 'one_off') as tier,
                    COUNT(*) as count
                FROM thread_categories tc
                GROUP BY tier
                ORDER BY count DESC
            ''')
            rows = [dict(r) for r in cursor.fetchall()]
            conn.close()
            self.send_json({'tiers': rows})
            return

        if path == '/api/chats':
            q = query.get('q', [''])[0]
            sort = query.get('sort', ['desc'])[0]
            audio_only = int(query.get('audio_only', ['0'])[0] or '0')
            category = query.get('category', [''])[0]
            tier = query.get('tier', [''])[0]
            thread_id = query.get('thread_id', [''])[0]
            page = max(1, int(query.get('page', ['1'])[0] or '1'))
            limit = min(50, max(1, int(query.get('limit', ['10'])[0] or '10')))
            offset = (page - 1) * limit

            conn = get_db()
            cursor = conn.cursor()
            total, threads = get_stitched_threads(cursor, q, sort, audio_only, category, tier, thread_id, limit, offset)
            conn.close()

            self.send_json({
                'total': total,
                'page': page,
                'limit': limit,
                'threads': threads
            })
            return

        if path.startswith('/media/'):
            filename = urllib.parse.unquote(path[7:])
            filepath = os.path.join(MEDIA_DIR, filename)
            if os.path.exists(filepath) and os.path.isfile(filepath):
                ctype, _ = mimetypes.guess_type(filepath)
                if not ctype:
                    ctype = 'application/octet-stream'
                with open(filepath, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', ctype)
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, f"Media file {filename} not found")
            return

        self.send_error(404, "Page Not Found")

def run_server(port=8080):
    server_address = ('', port)
    httpd = ThreadingHTTPServer(server_address, ArchiveRequestHandler)
    print(f"🚀 Gemini Archive Threaded Server running at http://localhost:{port}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()

if __name__ == '__main__':
    run_server()
