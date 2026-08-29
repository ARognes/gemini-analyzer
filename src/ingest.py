import os
import sys
import sqlite3
import json
import hashlib
import shutil
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.parser import parse_takeout_html
from src.classifier import run_thread_classification
from src.linker import run_knowledge_linker
from src.db import init_synthesis_tables

def compute_card_hash(thread_id, timestamp_iso, prompt_text):
    sig = f"{thread_id or ''}|{timestamp_iso or ''}|{(prompt_text or '')[:100]}"
    return hashlib.sha256(sig.encode('utf-8')).hexdigest()[:16]

def run_incremental_ingestion(takeout_dir, data_dir):
    os.makedirs(data_dir, exist_ok=True)
    media_dir = os.path.join(data_dir, 'media')
    os.makedirs(media_dir, exist_ok=True)

    db_path = os.path.join(data_dir, 'gemini_archive.db')
    json_path = os.path.join(data_dir, 'chats.json')
    html_path = os.path.join(takeout_dir, 'MyActivity.html')

    if not os.path.exists(html_path):
        print(f"❌ Error: Takeout file {html_path} not found.")
        return False

    print(f"Step 1: Parsing Takeout HTML at {html_path}...")
    new_chats = parse_takeout_html(html_path)

    print(f"Step 2: Connecting to SQLite database at {db_path}...")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    init_synthesis_tables(conn)

    # Fetch existing chat signatures for deduplication
    cursor.execute('SELECT thread_id, timestamp_iso, prompt_text FROM chats;')
    existing_rows = cursor.fetchall()
    existing_hashes = {
        compute_card_hash(r['thread_id'], r['timestamp_iso'], r['prompt_text'])
        for r in existing_rows
    }

    print(f"Existing chat signatures in archive: {len(existing_hashes)}")

    # Filter out duplicate chats
    inserted_count = 0
    rows_to_insert = []
    
    # Get max existing ID
    cursor.execute('SELECT MAX(id) FROM chats;')
    max_id_row = cursor.fetchone()[0]
    next_id = (max_id_row or 0) + 1

    for c in new_chats:
        c_hash = compute_card_hash(c['thread_id'], c['timestamp_iso'], c['prompt_text'])
        if c_hash not in existing_hashes:
            existing_hashes.add(c_hash)
            rows_to_insert.append((
                next_id,
                c['thread_id'],
                c['timestamp_iso'],
                c['timestamp_raw'],
                c['prompt_text'],
                c['response_html'],
                c['response_plain'],
                json.dumps(c['media_files']),
                c['details_url'],
                c['was_audio_input']
            ))
            next_id += 1

    if rows_to_insert:
        print(f"Step 3: Ingesting {len(rows_to_insert)} new chat records...")
        cursor.executemany('''
            INSERT INTO chats (id, thread_id, timestamp_iso, timestamp_raw, prompt_text, response_html, response_plain, media_files_json, details_url, was_audio_input)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        ''', rows_to_insert)
        conn.commit()
    else:
        print("Step 3: No new chat entries found. Archive is already up to date!")

    # Step 4: Sync Media
    print(f"Step 4: Syncing media files to {media_dir}...")
    copied_count = 0
    skipped_wav_count = 0

    for filename in os.listdir(takeout_dir):
        src_file = os.path.join(takeout_dir, filename)
        if not os.path.isfile(src_file):
            continue
        if filename.endswith('.wav'):
            skipped_wav_count += 1
            continue
        if filename == 'MyActivity.html':
            continue

        dst_file = os.path.join(media_dir, filename)
        if not os.path.exists(dst_file):
            shutil.copy2(src_file, dst_file)
            copied_count += 1

    print(f"Media Sync: Copied {copied_count} new files. Skipped {skipped_wav_count} WAVs.")

    # Update metadata
    cursor.execute('SELECT COUNT(*) FROM chats;')
    total_chats = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(DISTINCT COALESCE(NULLIF(thread_id, ""), CAST(id AS TEXT))) FROM chats;')
    total_threads = cursor.fetchone()[0]

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('INSERT OR REPLACE INTO archive_meta (key, value) VALUES (?, ?);', ('last_ingest_date', now_str))
    cursor.execute('INSERT OR REPLACE INTO archive_meta (key, value) VALUES (?, ?);', ('total_chats', str(total_chats)))
    cursor.execute('INSERT OR REPLACE INTO archive_meta (key, value) VALUES (?, ?);', ('total_threads', str(total_threads)))
    conn.commit()
    conn.close()

    # Step 5: Run Classifier & Knowledge Linker
    print("Step 5: Updating Domain Taxonomy Classifications & Knowledge Links...")
    run_thread_classification(db_path)
    run_knowledge_linker(db_path)

    print(f"✨ Monthly Ingestion Complete! Archive contains {total_chats} chats across {total_threads} threads.")
    return True

if __name__ == '__main__':
    takeout_path = '/Users/austinrognes/Seagate-NAS/Gemini'
    project_data = '/Users/austinrognes/Documents/Projects/gemini-analyzer/data'
    run_incremental_ingestion(takeout_path, project_data)
