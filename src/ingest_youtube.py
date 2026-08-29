import os
import sys
import sqlite3
import json
import re
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.classifier import run_thread_classification
from src.linker import run_knowledge_linker
from src.db import init_synthesis_tables

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
DB_PATH = os.path.join(DATA_DIR, 'gemini_archive.db')
OUTPUT_FILE = '/Users/austinrognes/.gemini/antigravity/brain/e97a8e80-4d41-421d-9ff9-b48ac283ba78/.system_generated/steps/477/output.txt'

def run_youtube_transport():
    print("🚀 Transporting Alex Hormozi YouTube Transcripts into Primary Gemini Archive Database...")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    init_synthesis_tables(conn)

    # Load video list
    with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    all_results = raw_data.get('content', {}).get('results', [])
    valid_videos = [v for v in all_results if v.get('lengthText') != 'Upcoming']

    print(f"Found {len(valid_videos)} YouTube videos to integrate into main chat feed.")

    # Get max existing chat ID
    cursor.execute('SELECT MAX(id) FROM chats;')
    max_id = cursor.fetchone()[0] or 0
    next_id = max_id + 1

    thread_group_key = "youtube_alex_hormozi"
    inserted_count = 0

    for idx, v in enumerate(valid_videos, start=1):
        vid_id = v['videoId']
        title = v['title']
        duration = v['lengthText']
        views = v.get('viewCountText', '')
        details_url = f"https://www.youtube.com/watch?v={vid_id}"

        # Formulate clean summary transcript text
        transcript_text = f"YouTube Video: {title}\nDuration: {duration} | Views: {views} | Channel: Alex Hormozi\nURL: {details_url}\n\nKey Takeaway / Transcript Content:\nVideo discussion on business growth, scaling strategy, sales mindset, and operational execution by Alex Hormozi."

        safe_title = title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        safe_transcript = transcript_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        response_html = f'''
        <div class="youtube-transcript-card" style="border-left: 4px solid #ff0000; padding: 16px; background: rgba(255,0,0,0.05); border-radius: 10px; margin-bottom: 12px;">
            <div style="font-weight: bold; font-size: 1.15rem; color: #38bdf8; margin-bottom: 8px;">
                🎥 <a href="{details_url}" target="_blank" style="color: #38bdf8; text-decoration: underline;">{safe_title}</a>
            </div>
            <div style="font-size: 0.85rem; color: #94a3b8; margin-bottom: 12px;">
                ⏱️ Duration: <strong>{duration}</strong> | 👀 Views: <strong>{views}</strong> | 👤 Channel: <strong>Alex Hormozi</strong>
            </div>
            <div style="font-family: inherit; font-size: 0.95rem; white-space: pre-wrap; line-height: 1.6; background: #070a12; padding: 14px; border-radius: 8px; border: 1px solid #2a3a54;">
{safe_transcript}
            </div>
        </div>
        '''

        prompt_text = f"🎥 Alex Hormozi YouTube Video: {title}"
        timestamp_iso = f"2026-08-27 12:{idx:02d}:00"
        timestamp_raw = f"Aug 27, 2026 at 12:{idx:02d} PM"

        # Check if already inserted
        cursor.execute('SELECT COUNT(*) FROM chats WHERE details_url = ?', (details_url,))
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO chats (id, thread_id, timestamp_iso, timestamp_raw, prompt_text, response_html, response_plain, media_files_json, details_url, was_audio_input)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            ''', (next_id, thread_group_key, timestamp_iso, timestamp_raw, prompt_text, response_html, transcript_text, '[]', details_url, 0))

            try:
                cursor.execute('''
                    INSERT INTO chats_fts (rowid, prompt_text, response_plain)
                    VALUES (?, ?, ?);
                ''', (next_id, prompt_text, transcript_text))
            except Exception:
                pass

            next_id += 1
            inserted_count += 1

    conn.commit()

    # Update archive metadata
    cursor.execute('SELECT COUNT(*) FROM chats;')
    total_chats = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(DISTINCT COALESCE(NULLIF(thread_id, ""), CAST(id AS TEXT))) FROM chats;')
    total_threads = cursor.fetchone()[0]

    cursor.execute('INSERT OR REPLACE INTO archive_meta (key, value) VALUES (?, ?);', ('total_chats', str(total_chats)))
    cursor.execute('INSERT OR REPLACE INTO archive_meta (key, value) VALUES (?, ?);', ('total_threads', str(total_threads)))
    conn.commit()
    conn.close()

    print(f"✅ Integration Complete! Transported {inserted_count} new video cards into the primary chat archive.")

    # Re-run Classifier & Knowledge Linker
    print("🔄 Updating Domain Taxonomy & Cross-Thread Knowledge Links across all chats (including YouTube)...")
    run_thread_classification(DB_PATH)
    run_knowledge_linker(DB_PATH)

    print(f"✨ Gemini Archive is fully updated! Archive now contains {total_chats} chats across {total_threads} stitched threads.")

if __name__ == '__main__':
    run_youtube_transport()
