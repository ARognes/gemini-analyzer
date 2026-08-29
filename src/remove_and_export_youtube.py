import os
import sys
import sqlite3
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.classifier import run_thread_classification
from src.linker import run_knowledge_linker
from src.db import init_synthesis_tables

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
DB_PATH = os.path.join(DATA_DIR, 'gemini_archive.db')
OUTPUT_FILE = '/Users/austinrognes/.gemini/antigravity/brain/e97a8e80-4d41-421d-9ff9-b48ac283ba78/.system_generated/steps/477/output.txt'

EXPORT_JSON = os.path.join(DATA_DIR, 'alex_hormozi_transcripts.json')
EXPORT_DB = os.path.join(DATA_DIR, 'alex_hormozi_transcripts.db')

def export_and_clean():
    print("📦 Step 1: Exporting Alex Hormozi YouTube Transcripts to standalone files...")
    
    # Load video list
    with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    all_results = raw_data.get('content', {}).get('results', [])
    valid_videos = [v for v in all_results if v.get('lengthText') != 'Upcoming']

    export_records = []
    for idx, v in enumerate(valid_videos, start=1):
        vid_id = v['videoId']
        title = v['title']
        duration = v['lengthText']
        views = v.get('viewCountText', '')
        details_url = f"https://www.youtube.com/watch?v={vid_id}"

        export_records.append({
            'sequence_number': idx,
            'video_id': vid_id,
            'title': title,
            'duration': duration,
            'views': views,
            'channel': 'Alex Hormozi',
            'url': details_url,
            'transcript_snippet': f"YouTube Video: {title}\nDuration: {duration} | Views: {views}"
        })

    # Save to JSON
    with open(EXPORT_JSON, 'w', encoding='utf-8') as f:
        json.dump({
            'channel': 'Alex Hormozi',
            'total_videos': len(export_records),
            'videos': export_records
        }, f, indent=2, ensure_ascii=False)
    print(f"   ✓ Exported standalone JSON archive: {EXPORT_JSON}")

    # Save to Standalone SQLite DB
    if os.path.exists(EXPORT_DB):
        os.remove(EXPORT_DB)

    s_conn = sqlite3.connect(EXPORT_DB)
    s_cursor = s_conn.cursor()
    s_cursor.execute('''
        CREATE TABLE hormozi_transcripts (
            id INTEGER PRIMARY KEY,
            video_id TEXT UNIQUE,
            title TEXT,
            duration TEXT,
            views TEXT,
            url TEXT,
            channel TEXT
        );
    ''')

    s_cursor.executemany('''
        INSERT INTO hormozi_transcripts (id, video_id, title, duration, views, url, channel)
        VALUES (?, ?, ?, ?, ?, ?, ?);
    ''', [(r['sequence_number'], r['video_id'], r['title'], r['duration'], r['views'], r['url'], r['channel']) for r in export_records])

    s_conn.commit()
    s_conn.close()
    print(f"   ✓ Exported standalone SQLite DB:  {EXPORT_DB}")

    # Step 2: Remove from primary gemini_archive.db
    print("\n🧹 Step 2: Removing YouTube entries from primary gemini_archive.db...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('DELETE FROM chats WHERE thread_id = "youtube_alex_hormozi";')
    deleted_chats = cursor.rowcount

    cursor.execute('DELETE FROM thread_categories WHERE group_key = "youtube_alex_hormozi";')
    cursor.execute('DELETE FROM thread_relations WHERE source_key = "youtube_alex_hormozi" OR target_key = "youtube_alex_hormozi";')

    # Update metadata
    cursor.execute('SELECT COUNT(*) FROM chats;')
    total_chats = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(DISTINCT COALESCE(NULLIF(thread_id, ""), CAST(id AS TEXT))) FROM chats;')
    total_threads = cursor.fetchone()[0]

    cursor.execute('INSERT OR REPLACE INTO archive_meta (key, value) VALUES (?, ?);', ('total_chats', str(total_chats)))
    cursor.execute('INSERT OR REPLACE INTO archive_meta (key, value) VALUES (?, ?);', ('total_threads', str(total_threads)))
    conn.commit()
    conn.close()

    print(f"   ✓ Deleted {deleted_chats} YouTube chat entries from main Gemini database.")

    # Re-run Classifier & Knowledge Linker to restore original pristine taxonomy
    print("\n🔄 Step 3: Re-classifying primary Gemini Archive database back to original state...")
    run_thread_classification(DB_PATH)
    run_knowledge_linker(DB_PATH)

    print(f"\n✨ Cleanup Complete! Gemini Archive restored to {total_chats} chats across {total_threads} threads.")

if __name__ == '__main__':
    export_and_clean()
