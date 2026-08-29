import os
import sys
import json
import time
import sqlite3
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

API_KEY = 'sk_JaAysZu79sqC3_fBTneaD3FcFXuhiz1Br9a862wb8JM'
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'gemini_archive.db')
OUTPUT_FILE = '/Users/austinrognes/.gemini/antigravity/brain/e97a8e80-4d41-421d-9ff9-b48ac283ba78/.system_generated/steps/477/output.txt'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hormozi_transcripts (
            video_id TEXT PRIMARY KEY,
            title TEXT,
            duration TEXT,
            view_count TEXT,
            transcript_text TEXT,
            word_count INTEGER,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    return conn

def fetch_transcript_mcp(video_id):
    t0 = time.time()
    url = 'https://transcriptapi.com/mcp'
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream'
    }
    payload = {
        'jsonrpc': '2.0',
        'id': 1,
        'method': 'tools/call',
        'params': {
            'name': 'get_youtube_transcript',
            'arguments': {
                'video_url': video_id,
                'format': 'text',
                'include_timestamp': False
            }
        }
    }
    
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            text = resp.read().decode('utf-8')
            elapsed = (time.time() - t0) * 1000

            match = re.search(r'data:\s*(\{.*\})', text)
            transcript_content = ""
            if match:
                data = json.loads(match.group(1))
                if data.get('result', {}).get('content'):
                    raw_text = data['result']['content'][0].get('text', '')
                    try:
                        parsed = json.loads(raw_text)
                        transcript_content = parsed.get('content') or parsed.get('transcript') or ""
                    except Exception:
                        transcript_content = raw_text

            return {'video_id': video_id, 'success': True, 'elapsed_ms': elapsed, 'transcript': transcript_content}
    except Exception as e:
        return {'video_id': video_id, 'success': False, 'elapsed_ms': (time.time() - t0) * 1000, 'error': str(e)}

def main():
    print("🚀 Alex Hormozi YouTube Transcript Batch Extractor (Parallel Suite)")
    print("-------------------------------------------------------------------")

    conn = init_db()

    with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    all_results = raw_data.get('content', {}).get('results', [])
    valid_videos = [v for v in all_results if v.get('lengthText') != 'Upcoming'][:99]

    print(f"Loaded {len(valid_videos)} Alex Hormozi videos for processing.")
    print(f"Credit Budget: 100 Credits Max (1 for channel list + {len(valid_videos)} for transcripts)\n")

    # --- BENCHMARKING SAMPLE ---
    print("⏱️ Phase 1: Measuring single-thread latency sample (5 videos)...")
    sample_videos = valid_videos[:5]
    sample_times = []

    for v in sample_videos:
        res = fetch_transcript_mcp(v['videoId'])
        sample_times.append(res['elapsed_ms'])

    avg_sample_ms = sum(sample_times) / len(sample_times)
    avg_sample_sec = avg_sample_ms / 1000.0
    print(f"   Sample Latency: {avg_sample_ms:.1f}ms per video (avg across 5 requests)")

    # --- TIME PREDICTIONS ---
    pred_seq_sec = valid_videos.length if hasattr(valid_videos, 'length') else len(valid_videos)
    pred_seq_sec = len(valid_videos) * avg_sample_sec
    concurrency = 15
    pred_par_sec = (len(valid_videos) / concurrency) * avg_sample_sec * 1.15 # 15% concurrency overhead estimate

    print("\n🔮 Phase 2: Predictions vs Architecture")
    print(f"   • Predicted Sequential Execution Time (1 worker):  ~{pred_seq_sec:.2f}s ({pred_seq_sec/60:.2f} mins)")
    print(f"   • Predicted Parallel Execution Time ({concurrency} workers): ~{pred_par_sec:.2f}s")
    print(f"   • Predicted Acceleration Multiplier:               ~{(pred_seq_sec / pred_par_sec):.1f}x faster\n")

    # --- PARALLEL EXECUTION ---
    print(f"⚡ Phase 3: Executing ALL {len(valid_videos)} Transcripts in Parallel ({concurrency} Workers)...")
    start_parallel = time.time()

    completed_results = []
    
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        future_to_video = {
            executor.submit(fetch_transcript_mcp, v['videoId']): v
            for v in valid_videos
        }

        for idx, future in enumerate(as_completed(future_to_video), start=1):
            v = future_to_video[future]
            res = future.result()
            words = len(res['transcript'].split()) if res.get('transcript') else 0

            if res['success'] and res['transcript']:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO hormozi_transcripts (video_id, title, duration, view_count, transcript_text, word_count)
                    VALUES (?, ?, ?, ?, ?, ?);
                ''', (v['videoId'], v['title'], v['lengthText'], v['viewCountText'], res['transcript'], words))
                conn.commit()

            completed_results.append({**v, **res, 'words': words})

            if idx % 15 == 0 or idx == len(valid_videos):
                print(f"   [Progress {idx:2d}/{len(valid_videos)}] Fetched: \"{v['title'][:45]}\" ({words} words)")

    actual_par_sec = time.time() - start_parallel

    successful = [r for r in completed_results if r.get('success') and r.get('transcript')]
    total_words = sum(r.get('words', 0) for r in completed_results)

    print("\n✅ Phase 4: Execution Complete & Database Saved!")
    print("===================================================================")
    print(f"📊 Total Transcripts Saved: {len(successful)} / {len(valid_videos)}")
    print(f"📝 Total Words Ingested:   {total_words:,} words")
    print(f"💳 Credits Consumed:       {1 + len(valid_videos)} credits (Remaining Allowance: {1000 - (1 + len(valid_videos))} credits)")
    print("-------------------------------------------------------------------")
    print("📈 EMPIRICAL TIMING COMPARISON:")
    print(f"   • Predicted Sequential Time: ~{pred_seq_sec:.2f}s ({(pred_seq_sec/60):.2f} mins)")
    print(f"   • Predicted Parallel Time:   ~{pred_par_sec:.2f}s")
    print(f"   • ACTUAL Parallel Time:      ⚡ {actual_par_sec:.2f}s")
    print(f"   • Actual Speedup vs Seq:    ~{(pred_seq_sec / actual_par_sec):.1f}x Faster!")
    print("===================================================================")

    conn.close()

if __name__ == '__main__':
    main()
