#!/usr/bin/env python3
import os
import sys
import json
import sqlite3

# Insert root directory into python path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from src.server import (
    get_db,
    get_analytics_data,
    get_categories_data,
    get_data_driven_tags,
    get_overlap_data,
    get_domain_matrix_data,
    get_correlation_spectrum_data,
    get_mindmap_tree_data,
    get_stitched_threads
)

def export_static_data():
    db_path = os.path.join(ROOT_DIR, 'data', 'gemini_archive.db')
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        sys.exit(1)

    out_dir = os.path.join(ROOT_DIR, 'frontend', 'static', 'data')
    threads_dir = os.path.join(out_dir, 'threads')
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(threads_dir, exist_ok=True)

    conn = get_db()
    cursor = conn.cursor()

    print("📦 Exporting stats.json...")
    cursor.execute('SELECT COUNT(*) FROM chats')
    total_chats = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM chats WHERE was_audio_input = 1')
    voice_chats = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(DISTINCT COALESCE(NULLIF(thread_id, ""), CAST(id AS TEXT))) FROM chats')
    total_threads = cursor.fetchone()[0]
    stats_data = {
        'total_chats': total_chats,
        'voice_chats': voice_chats,
        'total_threads': total_threads
    }
    with open(os.path.join(out_dir, 'stats.json'), 'w', encoding='utf-8') as f:
        json.dump(stats_data, f, indent=2)

    print("📦 Exporting analytics.json...")
    analytics_data = get_analytics_data(cursor)
    with open(os.path.join(out_dir, 'analytics.json'), 'w', encoding='utf-8') as f:
        json.dump(analytics_data, f, indent=2)

    print("📦 Exporting categories.json...")
    cat_data = get_categories_data(cursor)
    with open(os.path.join(out_dir, 'categories.json'), 'w', encoding='utf-8') as f:
        json.dump(cat_data, f, indent=2)

    print("📦 Exporting data_tags.json...")
    tags_data = get_data_driven_tags(cursor)
    with open(os.path.join(out_dir, 'data_tags.json'), 'w', encoding='utf-8') as f:
        json.dump(tags_data, f, indent=2)

    print("📦 Exporting overlap.json...")
    overlap_data = get_overlap_data(cursor, min_similarity=0.38, limit=3000)
    with open(os.path.join(out_dir, 'overlap.json'), 'w', encoding='utf-8') as f:
        json.dump(overlap_data, f)

    print("📦 Exporting correlation_stats.json...")
    corr_data = get_correlation_spectrum_data(cursor, min_similarity=0.30)
    with open(os.path.join(out_dir, 'correlation_stats.json'), 'w', encoding='utf-8') as f:
        json.dump(corr_data, f, indent=2)

    print("📦 Exporting mindmap_tree.json...")
    mindmap_data = get_mindmap_tree_data(cursor)
    with open(os.path.join(out_dir, 'mindmap_tree.json'), 'w', encoding='utf-8') as f:
        json.dump(mindmap_data, f, indent=2)

    print("📦 Exporting domain_matrix.json...")
    matrix_data = get_domain_matrix_data(cursor, min_similarity=0.38)
    with open(os.path.join(out_dir, 'domain_matrix.json'), 'w', encoding='utf-8') as f:
        json.dump(matrix_data, f, indent=2)

    print("📦 Exporting individual thread files into data/threads/*.json...")
    total_t, all_threads = get_stitched_threads(cursor, limit=10000, offset=0)
    search_index = []

    for t in all_threads:
        key = t.get('group_key') or str(t.get('id'))
        if not key:
            continue
        # Export single thread file
        thread_file = os.path.join(threads_dir, f"{key}.json")
        with open(thread_file, 'w', encoding='utf-8') as f:
            json.dump(t, f)
        
        # Build search index entry
        first_prompt = (t.get('first_prompt') or t.get('prompt_text') or '')[:120]
        search_index.append({
            'id': key,
            'title': t.get('title') or first_prompt or 'Untitled Thread',
            'snippet': first_prompt,
            'timestamp': t.get('first_timestamp') or ''
        })

    print("📦 Exporting search_index.json...")
    with open(os.path.join(out_dir, 'search_index.json'), 'w', encoding='utf-8') as f:
        json.dump(search_index, f)

    conn.close()
    print("✅ Static JSON data export complete! All files exported to frontend/static/data/")

if __name__ == '__main__':
    export_static_data()
