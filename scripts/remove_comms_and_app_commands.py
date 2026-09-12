#!/usr/bin/env python3
import os
import sys
import json
import re
import collections

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, 'frontend', 'static', 'data')
THREADS_DIR = os.path.join(DATA_DIR, 'threads')

APP_COMMAND_PATTERNS = [
    r'^\s*(open|launch|start|run|show|go to|play|set alarm|call|message|text|navigate to|search for)\b',
    r'^\s*(youtube|home depot|maps|photos|audible|snapchat|play store|pandora|chrome|settings|meet|drive|keep|perplexity|allegiant|calendar|clock|contacts|gmail|messages|phone)\b'
]

def is_app_cmd(text):
    if not text: return False
    p = text.strip()
    for pat in APP_COMMAND_PATTERNS:
        if re.search(pat, p, re.IGNORECASE):
            return True
    return False

def prune_non_pertinent():
    print("🔍 Step 1: Identifying Communications Queries and App Commands...")
    
    threads_to_remove = set()
    removed_chat_ids = set()
    reason_map = {}

    all_thread_files = [f for f in os.listdir(THREADS_DIR) if f.endswith('.json')]
    for fn in all_thread_files:
        tid = fn[:-5]
        fp = os.path.join(THREADS_DIR, fn)
        with open(fp, 'r', encoding='utf-8') as f:
            tdata = json.load(f)
        
        turns = tdata.get('turns', [])
        turn_count = len(turns) or tdata.get('turn_count', 1)
        prompt = ''
        if turns:
            prompt = (turns[0].get('prompt_text') or '').strip()
        else:
            prompt = (tdata.get('first_prompt') or tdata.get('prompt_text') or '').strip()
        
        title = (tdata.get('title') or '').strip()
        tier = tdata.get('actionability_tier')

        is_comm = (
            'communications query' in prompt.lower() or 
            'communications query' in title.lower() or 
            prompt.lower() == 'a communications query.' or
            title.lower() == 'a communications query.'
        )
        is_cmd = (tier == 'app_command') or (turn_count == 1 and is_app_cmd(prompt))

        if is_comm:
            threads_to_remove.add(tid)
            reason_map[tid] = f"Comms Query: {prompt[:40]}"
            for turn in turns:
                if 'id' in turn:
                    removed_chat_ids.add(turn['id'])
        elif is_cmd:
            threads_to_remove.add(tid)
            reason_map[tid] = f"App Command: {prompt[:40]}"
            for turn in turns:
                if 'id' in turn:
                    removed_chat_ids.add(turn['id'])

    # Also check overlap.json nodes
    overlap_path = os.path.join(DATA_DIR, 'overlap.json')
    with open(overlap_path, 'r', encoding='utf-8') as f:
        overlap_data = json.load(f)

    for n in overlap_data.get('nodes', []):
        nid = n.get('id')
        title = (n.get('title') or n.get('label') or '').strip()
        tier = n.get('actionability_tier')
        if 'communications query' in title.lower():
            threads_to_remove.add(nid)
            reason_map[nid] = f"Comms Query (overlap): {title[:40]}"
        elif tier == 'app_command':
            threads_to_remove.add(nid)
            reason_map[nid] = f"App Command (overlap): {title[:40]}"

    print(f"Total non-pertinent threads to remove: {len(threads_to_remove)}")
    print(f"  - Communications Queries: {sum(1 for r in reason_map.values() if 'Comms Query' in r)}")
    print(f"  - App Commands: {sum(1 for r in reason_map.values() if 'App Command' in r)}")

    # 1. Delete thread files
    print("\n🗑️ Step 2: Deleting individual thread JSON files...")
    deleted_files = 0
    for tid in threads_to_remove:
        tp = os.path.join(THREADS_DIR, f"{tid}.json")
        if os.path.exists(tp):
            os.remove(tp)
            deleted_files += 1
    print(f"   ✓ Deleted {deleted_files} files from {THREADS_DIR}")

    # 2. Update overlap.json
    print("\n📦 Step 3: Updating overlap.json (Constellation graph)...")
    orig_node_count = len(overlap_data.get('nodes', []))
    orig_link_count = len(overlap_data.get('relations', []))

    new_nodes = [n for n in overlap_data.get('nodes', []) if n.get('id') not in threads_to_remove]
    surviving_node_ids = {n.get('id') for n in new_nodes}

    new_relations = []
    for rel in overlap_data.get('relations', []):
        src_id = rel.get('source_key') or rel.get('source')
        tgt_id = rel.get('target_key') or rel.get('target')
        if isinstance(src_id, dict):
            src_id = src_id.get('id')
        if isinstance(tgt_id, dict):
            tgt_id = tgt_id.get('id')

        if src_id in surviving_node_ids and tgt_id in surviving_node_ids:
            new_relations.append(rel)

    overlap_data['nodes'] = new_nodes
    overlap_data['relations'] = new_relations
    overlap_data['total_links'] = len(new_relations)

    with open(overlap_path, 'w', encoding='utf-8') as f:
        json.dump(overlap_data, f)
    print(f"   ✓ overlap.json: Nodes {orig_node_count} -> {len(new_nodes)}, Links {orig_link_count} -> {len(new_relations)}")

    # 3. Update categories.json
    print("\n📦 Step 4: Updating categories.json...")
    cat_path = os.path.join(DATA_DIR, 'categories.json')
    with open(cat_path, 'r', encoding='utf-8') as f:
        cat_data = json.load(f)

    orig_threads = cat_data.get('threads', [])
    new_threads = [t for t in orig_threads if (t.get('group_key') or str(t.get('id'))) not in threads_to_remove]
    cat_data['threads'] = new_threads

    # Recalculate categories_summary
    cat_counts = collections.Counter()
    for t in new_threads:
        cat = t.get('primary_category') or 'outliers'
        cat_counts[cat] += 1

    for csum in cat_data.get('categories_summary', []):
        cat_id = csum.get('category')
        if cat_id in cat_counts:
            csum['thread_count'] = cat_counts[cat_id]

    with open(cat_path, 'w', encoding='utf-8') as f:
        json.dump(cat_data, f, indent=2)
    print(f"   ✓ categories.json: Threads {len(orig_threads)} -> {len(new_threads)}")

    # 4. Update data_tags.json
    print("\n📦 Step 5: Updating data_tags.json...")
    tags_path = os.path.join(DATA_DIR, 'data_tags.json')
    with open(tags_path, 'r', encoding='utf-8') as f:
        tags_data = json.load(f)

    new_tags = []
    for tag in tags_data:
        if tag.get('tag_id') == 'communications_query':
            continue
        valid_keys = [k for k in tag.get('thread_keys', []) if k not in threads_to_remove]
        if len(valid_keys) >= 2:
            tag['thread_keys'] = valid_keys
            tag['thread_count'] = len(valid_keys)
            new_tags.append(tag)

    with open(tags_path, 'w', encoding='utf-8') as f:
        json.dump(new_tags, f, indent=2)
    print(f"   ✓ data_tags.json: Tags {len(tags_data)} -> {len(new_tags)}")

    # 5. Update search_index.json
    print("\n📦 Step 6: Updating search_index.json...")
    search_path = os.path.join(DATA_DIR, 'search_index.json')
    with open(search_path, 'r', encoding='utf-8') as f:
        search_data = json.load(f)

    new_search = [item for item in search_data if item.get('id') not in threads_to_remove]
    with open(search_path, 'w', encoding='utf-8') as f:
        json.dump(new_search, f)
    print(f"   ✓ search_index.json: Entries {len(search_data)} -> {len(new_search)}")

    # 6. Update correlation_stats.json
    print("\n📦 Step 7: Updating correlation_stats.json...")
    corr_path = os.path.join(DATA_DIR, 'correlation_stats.json')
    with open(corr_path, 'r', encoding='utf-8') as f:
        corr_data = json.load(f)

    new_samples = []
    for pair in corr_data.get('sample_pairs', []):
        s_id = pair.get('source_key') or pair.get('source_id')
        t_id = pair.get('target_key') or pair.get('target_id')
        s_title = (pair.get('source_title') or '').lower()
        t_title = (pair.get('target_title') or '').lower()
        if (s_id and s_id in threads_to_remove) or (t_id and t_id in threads_to_remove):
            continue
        if 'communications query' in s_title or 'communications query' in t_title:
            continue
        new_samples.append(pair)

    corr_data['sample_pairs'] = new_samples
    corr_data['qualified_pairs'] = len(new_relations)
    corr_data['total_pairs'] = int(len(new_nodes) * (len(new_nodes) - 1) / 2) if len(new_nodes) > 1 else 0

    with open(corr_path, 'w', encoding='utf-8') as f:
        json.dump(corr_data, f, indent=2)
    print(f"   ✓ correlation_stats.json updated")

    # 7. Update stats.json and analytics.json by scanning surviving threads
    print("\n📦 Step 8: Updating stats.json & analytics.json...")
    total_chats = 0
    voice_chats = 0
    surviving_tfiles = [f for f in os.listdir(THREADS_DIR) if f.endswith('.json')]
    total_threads = len(surviving_tfiles)

    daily_heatmap = collections.Counter()
    hourly_distribution = collections.Counter()

    for fn in surviving_tfiles:
        fp = os.path.join(THREADS_DIR, fn)
        with open(fp, 'r', encoding='utf-8') as f:
            tdata = json.load(f)
        
        turns = tdata.get('turns', [])
        turn_count = len(turns) or tdata.get('turn_count', 1)
        total_chats += turn_count
        if tdata.get('has_audio_input'):
            voice_chats += 1

        for turn in turns:
            ts_iso = turn.get('timestamp_iso', '')
            if ts_iso and not ts_iso.startswith('1970-01-01'):
                date_key = ts_iso[:10]
                daily_heatmap[date_key] += 1
                if len(ts_iso) >= 13:
                    hr = ts_iso[11:13]
                    if hr.isdigit():
                        hourly_distribution[int(hr)] += 1

    stats_path = os.path.join(DATA_DIR, 'stats.json')
    stats_data = {
        'total_chats': total_chats,
        'voice_chats': voice_chats,
        'total_threads': total_threads
    }
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats_data, f, indent=2)
    print(f"   ✓ stats.json: {stats_data}")

    # analytics.json
    analytics_path = os.path.join(DATA_DIR, 'analytics.json')
    with open(analytics_path, 'r', encoding='utf-8') as f:
        analytics_data = json.load(f)

    analytics_data['daily_heatmap'] = dict(sorted(daily_heatmap.items()))
    analytics_data['hourly_distribution'] = {str(k): v for k, v in sorted(hourly_distribution.items())}
    analytics_data['media_items'] = [
        m for m in analytics_data.get('media_items', [])
        if m.get('group_key') not in threads_to_remove and m.get('chat_id') not in removed_chat_ids
    ]

    with open(analytics_path, 'w', encoding='utf-8') as f:
        json.dump(analytics_data, f, indent=2)
    print(f"   ✓ analytics.json updated")

    # 8. Update mindmap_tree.json
    print("\n📦 Step 9: Updating mindmap_tree.json...")
    mindmap_path = os.path.join(DATA_DIR, 'mindmap_tree.json')
    with open(mindmap_path, 'r', encoding='utf-8') as f:
        tree_data = json.load(f)

    def prune_tree(node):
        if not node:
            return 0, 0
        if 'children' in node and node['children']:
            child_threads = 0
            child_chats = 0
            new_children = []
            for child in node['children']:
                t_cnt, c_cnt = prune_tree(child)
                if t_cnt > 0:
                    new_children.append(child)
                    child_threads += t_cnt
                    child_chats += c_cnt
            node['children'] = new_children
            node['thread_count'] = child_threads
            node['chat_count'] = child_chats
            return child_threads, child_chats
        else:
            return node.get('thread_count', 0), node.get('chat_count', 0)

    tree_data['thread_count'] = total_threads
    tree_data['chat_count'] = total_chats
    prune_tree(tree_data)

    with open(mindmap_path, 'w', encoding='utf-8') as f:
        json.dump(tree_data, f, indent=2)
    print(f"   ✓ mindmap_tree.json updated")

    print("\n✨ All static JSON files successfully cleaned!")

if __name__ == '__main__':
    prune_non_pertinent()
