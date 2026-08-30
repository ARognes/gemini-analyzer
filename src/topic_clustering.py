import os
import sqlite3
import json
import re
import math
import collections

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
DB_PATH = os.path.join(DATA_DIR, 'gemini_archive.db')

CUSTOM_STOPWORDS = set([
    'like', 'but', 'because', 'really', 'just', 'can', 'make', 'use', 'get', 'would', 'one',
    'contentmetadata', 'toolattribution', 'displayname', 'href', 'width', 'html', 'titled',
    'cleared', 'previous', 'system', 'kind', 'meta', 'aug', 'https', 'http', 'com', 'www',
    'title', 'created', 'canvas', 'google', 'link', 'feedback', 'opened', 'open', 'cdt',
    'tag', 'tags', 'json', 'data', 'text', 'string', 'file', 'files', 'code', 'function',
    'value', 'type', 'list', 'name', 'user', 'prompt', 'response', 'time', 'year', 'month',
    'day', 'date', 'item', 'items', 'page', 'pages', 'view', 'views', 'set', 'get', 'add',
    'using', 'need', 'want', 'how', 'what', 'why', 'where', 'when', 'which', 'who', 'this',
    'that', 'these', 'those', 'with', 'from', 'for', 'about', 'into', 'over', 'after', 'also',
    'have', 'has', 'had', 'been', 'were', 'was', 'are', 'is', 'be', 'being', 'am', 'an', 'a',
    'the', 'and', 'or', 'if', 'then', 'else', 'when', 'while', 'so', 'not', 'no', 'nor',
    'they', 'them', 'their', 'theirs', 'you', 'your', 'yours', 'his', 'him', 'she', 'her',
    'hers', 'our', 'ours', 'us', 'we', 'mean', 'hey', 'yes', 'please', 'attached', 'keep',
    'different', 'good', 'well', 'way', 'new', 'see', 'saw', 'said', 'say', 'know', 'think',
    'look', 'take', 'come', 'go', 'going', 'give', 'put', 'let', 'show', 'find', 'try', 'tell'
])

APP_COMMAND_PATTERNS = [
    r'^\s*(open|launch|start|run|show|go to|play|set alarm|call|message|text|navigate to|search for)\b',
    r'^\s*(youtube|home depot|maps|photos|audible|snapchat|play store|pandora|chrome|settings|meet|drive|keep|perplexity|allegiant|calendar|clock|contacts|gmail|messages|phone)\b'
]

def is_app_command_prompt(prompt_text):
    if not prompt_text:
        return False
    p = prompt_text.strip()
    for pat in APP_COMMAND_PATTERNS:
        if re.search(pat, p, re.IGNORECASE):
            return True
    return False

def tokenize(text):
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    words = text.lower().split()
    cleaned = [w for w in words if len(w) >= 3 and w not in CUSTOM_STOPWORDS and not w.isdigit()]
    
    tokens = list(cleaned)
    for i in range(len(cleaned) - 1):
        bigram = f"{cleaned[i]}_{cleaned[i+1]}"
        tokens.append(bigram)
        
    return tokens

def run_ground_up_clustering(db_path=DB_PATH):
    print(f"Loading chats from {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT 
            COALESCE(NULLIF(c.thread_id, ''), CAST(c.id AS TEXT)) as group_key,
            COALESCE(tc.primary_category, 'outliers') as category,
            GROUP_CONCAT(c.prompt_text, ' ') as full_text,
            COUNT(*) as turn_count,
            MIN(c.prompt_text) as sample_prompt
        FROM chats c
        LEFT JOIN thread_categories tc ON COALESCE(NULLIF(c.thread_id, ''), CAST(c.id AS TEXT)) = tc.group_key
        WHERE c.timestamp_iso != "1970-01-01 00:00:00"
        GROUP BY group_key
    ''')
    rows = cursor.fetchall()
    total_docs = len(rows)
    print(f"Processing {total_docs} threads...")

    app_command_count = 0
    for r in rows:
        gk, cat, raw_text, turn_count, sample_prompt = r[0], r[1], r[2] or '', r[3], r[4] or ''
        if turn_count == 1 and is_app_command_prompt(sample_prompt):
            cursor.execute("UPDATE thread_categories SET actionability_tier = 'app_command' WHERE group_key = ?", (gk,))
            app_command_count += 1

    print(f"Categorized {app_command_count} single-turn chats as actionability_tier = 'app_command'.")

    doc_tokens = {}
    df_counts = collections.Counter()

    for r in rows:
        gk, cat, raw_text = r[0], r[1], r[2] or ''
        toks = tokenize(raw_text)
        doc_tokens[gk] = toks
        unique_toks = set(toks)
        for t in unique_toks:
            df_counts[t] += 1

    tag_clusters = collections.defaultdict(list)
    thread_primary_tags = {}

    for gk, toks in doc_tokens.items():
        tf = collections.Counter(toks)
        doc_len = max(1, len(toks))
        
        scores = {}
        for t, freq in tf.items():
            df = df_counts[t]
            if df >= 2 and df <= (total_docs * 0.35):
                idf = math.log((total_docs + 1) / (df + 1)) + 1
                scores[t] = (freq / doc_len) * idf

        sorted_terms = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        if sorted_terms:
            primary_tag = sorted_terms[0][0]
            secondary_tags = [t[0] for t in sorted_terms[:5]]
            thread_primary_tags[gk] = (primary_tag, secondary_tags)
            tag_clusters[primary_tag].append(gk)
        else:
            primary_tag = 'general'
            thread_primary_tags[gk] = (primary_tag, ['general'])
            tag_clusters[primary_tag].append(gk)

    qualified_tags = []
    for tag_name, gks in tag_clusters.items():
        if len(gks) >= 2 and tag_name != 'general':
            label = tag_name.replace('_', ' ').title()
            qualified_tags.append({
                'tag_id': tag_name,
                'tag_label': label,
                'thread_count': len(gks),
                'thread_keys': gks
            })

    qualified_tags.sort(key=lambda x: x['thread_count'], reverse=True)
    print(f"Identified {len(qualified_tags)} qualified data-driven tag clusters.")

    cursor.execute('DROP TABLE IF EXISTS data_driven_tags')
    cursor.execute('''
        CREATE TABLE data_driven_tags (
            tag_id TEXT PRIMARY KEY,
            tag_label TEXT NOT NULL,
            thread_count INTEGER NOT NULL,
            keywords_json TEXT NOT NULL,
            thread_keys_json TEXT NOT NULL
        )
    ''')

    cursor.execute('DROP TABLE IF EXISTS thread_data_tags')
    cursor.execute('''
        CREATE TABLE thread_data_tags (
            group_key TEXT PRIMARY KEY,
            primary_tag TEXT NOT NULL,
            secondary_tags_json TEXT NOT NULL
        )
    ''')

    for q in qualified_tags:
        cursor.execute('''
            INSERT INTO data_driven_tags (tag_id, tag_label, thread_count, keywords_json, thread_keys_json)
            VALUES (?, ?, ?, ?, ?)
        ''', (q['tag_id'], q['tag_label'], q['thread_count'], json.dumps([q['tag_label']]), json.dumps(q['thread_keys'])))

    for gk, (p_tag, all_tags) in thread_primary_tags.items():
        cursor.execute('''
            INSERT INTO thread_data_tags (group_key, primary_tag, secondary_tags_json)
            VALUES (?, ?, ?)
        ''', (gk, p_tag, json.dumps(all_tags)))

    conn.commit()
    conn.close()
    print("✅ Ground-Up Data-Driven Tag Clustering Complete!")
    return len(qualified_tags)

if __name__ == '__main__':
    run_ground_up_clustering()
