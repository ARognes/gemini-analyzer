import os
import sqlite3
import json
import shutil
from src.parser import parse_takeout_html

def init_synthesis_tables(conn):
    cursor = conn.cursor()
    
    # 1. Thread Categories & Taxonomy Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS thread_categories (
            group_key TEXT PRIMARY KEY,
            primary_category TEXT,
            secondary_categories_json TEXT,
            keywords_json TEXT,
            outlier_score REAL
        );
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cat_primary ON thread_categories(primary_category);')

    # 2. Cross-Thread Relations & Knowledge Links Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS thread_relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_key TEXT,
            target_key TEXT,
            similarity_score REAL,
            shared_topics_json TEXT
        );
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rel_source ON thread_relations(source_key);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rel_target ON thread_relations(target_key);')

    # 3. Archive Metadata Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS archive_meta (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    ''')
    conn.commit()

def build_database_and_archive(takeout_dir, data_dir):
    os.makedirs(data_dir, exist_ok=True)
    media_dir = os.path.join(data_dir, 'media')
    os.makedirs(media_dir, exist_ok=True)
    
    db_path = os.path.join(data_dir, 'gemini_archive.db')
    json_path = os.path.join(data_dir, 'chats.json')
    html_path = os.path.join(takeout_dir, 'MyActivity.html')
    
    print(f"Step 1: Parsing Takeout HTML at {html_path}...")
    chats = parse_takeout_html(html_path)
    
    print(f"Step 2: Building SQLite database at {db_path}...")
    if os.path.exists(db_path):
        os.remove(db_path)
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE chats (
            id INTEGER PRIMARY KEY,
            thread_id TEXT,
            timestamp_iso TEXT,
            timestamp_raw TEXT,
            prompt_text TEXT,
            response_html TEXT,
            response_plain TEXT,
            media_files_json TEXT,
            details_url TEXT,
            was_audio_input INTEGER
        );
    ''')
    
    cursor.execute('CREATE INDEX idx_chats_thread_id ON chats(thread_id);')
    cursor.execute('CREATE INDEX idx_chats_timestamp ON chats(timestamp_iso);')
    
    cursor.execute('''
        CREATE VIRTUAL TABLE chats_fts USING fts5(
            prompt_text,
            response_plain,
            content='chats',
            content_rowid='id'
        );
    ''')
    
    cursor.execute('''
        CREATE TRIGGER chats_ai AFTER INSERT ON chats BEGIN
            INSERT INTO chats_fts(rowid, prompt_text, response_plain)
            VALUES (new.id, new.prompt_text, new.response_plain);
        END;
    ''')
    cursor.execute('''
        CREATE TRIGGER chats_ad AFTER DELETE ON chats BEGIN
            INSERT INTO chats_fts(chats_fts, rowid, prompt_text, response_plain)
            VALUES('delete', old.id, old.prompt_text, old.response_plain);
        END;
    ''')
    cursor.execute('''
        CREATE TRIGGER chats_au AFTER UPDATE ON chats BEGIN
            INSERT INTO chats_fts(chats_fts, rowid, prompt_text, response_plain)
            VALUES('delete', old.id, old.prompt_text, old.response_plain);
            INSERT INTO chats_fts(rowid, prompt_text, response_plain)
            VALUES (new.id, new.prompt_text, new.response_plain);
        END;
    ''')
    
    init_synthesis_tables(conn)

    rows_to_insert = []
    for c in chats:
        rows_to_insert.append((
            c['id'],
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
        
    cursor.executemany('''
        INSERT INTO chats (id, thread_id, timestamp_iso, timestamp_raw, prompt_text, response_html, response_plain, media_files_json, details_url, was_audio_input)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    ''', rows_to_insert)
    
    conn.commit()
    print(f"Inserted {len(rows_to_insert)} chat records into SQLite.")
    
    print(f"Step 3: Exporting JSON archive to {json_path}...")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(chats, f, indent=2, ensure_ascii=False)
        
    print(f"Step 4: Syncing non-wav media files to {media_dir}...")
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
            
    print(f"Media Sync Complete: Copied {copied_count} media files. Skipped {skipped_wav_count} .wav audio files.")
    conn.close()
    print("Database and archive build complete!")

if __name__ == '__main__':
    takeout_path = '/Users/austinrognes/Seagate-NAS/Gemini'
    project_data = '/Users/austinrognes/Documents/Projects/gemini-analyzer/data'
    build_database_and_archive(takeout_path, project_data)
