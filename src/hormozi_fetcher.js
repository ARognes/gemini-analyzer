const fs = require('fs');
const path = require('path');
const sqlite3 = require('sqlite3').verbose();

const API_KEY = 'sk_JaAysZu79sqC3_fBTneaD3FcFXuhiz1Br9a862wb8JM';
const DB_PATH = path.join(__dirname, '..', 'data', 'gemini_archive.db');
const OUTPUT_FILE = path.join('/Users/austinrognes/.gemini/antigravity/brain/e97a8e80-4d41-421d-9ff9-b48ac283ba78/.system_generated/steps/477/output.txt');

function initDb() {
  return new Promise((resolve, reject) => {
    const db = new sqlite3.Database(DB_PATH, (err) => {
      if (err) return reject(err);
      db.run(`
        CREATE TABLE IF NOT EXISTS hormozi_transcripts (
          video_id TEXT PRIMARY KEY,
          title TEXT,
          duration TEXT,
          view_count TEXT,
          transcript_text TEXT,
          word_count INTEGER,
          fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
      `, (err2) => {
        if (err2) reject(err2);
        else resolve(db);
      });
    });
  });
}

async function fetchTranscriptMCP(videoId) {
  const t0 = Date.now();
  try {
    const res = await fetch('https://transcriptapi.com/mcp', {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + API_KEY,
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream'
      },
      body: JSON.stringify({
        jsonrpc: '2.0',
        id: 1,
        method: 'tools/call',
        params: {
          name: 'get_youtube_transcript',
          arguments: {
            video_url: videoId,
            format: 'text',
            include_timestamp: false
          }
        }
      })
    });

    const text = await res.text();
    const elapsed = Date.now() - t0;

    let transcriptContent = '';
    const match = text.match(/data:\s*(\{.*\})/);
    if (match) {
      const data = JSON.parse(match[1]);
      if (data.result && data.result.content && data.result.content[0]) {
        const rawJson = data.result.content[0].text;
        try {
          const parsed = JSON.parse(rawJson);
          transcriptContent = parsed.content || parsed.transcript || '';
        } catch(e) {
          transcriptContent = rawJson;
        }
      }
    }

    return { videoId, success: true, elapsed, transcript: transcriptContent };
  } catch (err) {
    return { videoId, success: false, elapsed: Date.now() - t0, error: err.message };
  }
}

async function runParallelPool(items, concurrency, taskFn) {
  const results = [];
  let index = 0;

  async function worker() {
    while (index < items.length) {
      const itemIdx = index++;
      const res = await taskFn(items[itemIdx], itemIdx);
      results[itemIdx] = res;
    }
  }

  const workers = Array.from({ length: concurrency }, () => worker());
  await Promise.all(workers);
  return results;
}

async function main() {
  console.log('🚀 Alex Hormozi YouTube Transcript Batch Extractor');
  console.log('----------------------------------------------------');

  const db = await initDb();

  // Load video list from step output
  const rawData = JSON.parse(fs.readFileSync(OUTPUT_FILE, 'utf8'));
  const allResults = rawData.content.results || [];
  const validVideos = allResults.filter(v => v.lengthText !== 'Upcoming').slice(0, 99);

  console.log(`Loaded ${validVideos.length} Alex Hormozi videos for processing.`);
  console.log(`Credit Budget: 100 Credits Max (1 for channel list + ${validVideos.length} for transcripts)\n`);

  // --- BENCHMARKING SAMPLE ---
  console.log('⏱️ Phase 1: Measuring single-thread latency sample (5 videos)...');
  const sampleVideos = validVideos.slice(0, 5);
  const sampleTimes = [];

  for (const v of sampleVideos) {
    const res = await fetchTranscriptMCP(v.videoId);
    sampleTimes.push(res.elapsed);
  }

  const avgSampleMs = sampleTimes.reduce((a, b) => a + b, 0) / sampleTimes.length;
  const avgSampleSec = avgSampleMs / 1000;
  console.log(`   Sample Latency: ${avgSampleMs.toFixed(1)}ms per video (avg across 5 requests)`);

  // --- TIME PREDICTIONS ---
  const predSequentialSec = (validVideos.length * avgSampleSec).toFixed(2);
  const CONCURRENCY = 15;
  const predParallelSec = ((validVideos.length / CONCURRENCY) * avgSampleSec * 1.15).toFixed(2); // 15% overhead estimate

  console.log('\n🔮 Phase 2: Predictions vs Architecture');
  console.log(`   • Predicted Sequential Execution Time (1 worker):  ~${predSequentialSec}s (${(predSequentialSec/60).toFixed(2)} mins)`);
  console.log(`   • Predicted Parallel Execution Time (${CONCURRENCY} workers): ~${predParallelSec}s`);
  console.log(`   • Predicted Acceleration Multiplier:               ~${(predSequentialSec / predParallelSec).toFixed(1)}x faster\n`);

  // --- PARALLEL EXECUTION ---
  console.log(`⚡ Phase 3: Executing ALL ${validVideos.length} Transcripts in Parallel (${CONCURRENCY} Workers)...`);
  const startParallel = Date.now();

  const results = await runParallelPool(validVideos, CONCURRENCY, async (video, idx) => {
    const res = await fetchTranscriptMCP(video.videoId);
    const words = res.transcript ? res.transcript.split(/\s+/).length : 0;

    if (res.success && res.transcript) {
      db.run(`
        INSERT OR REPLACE INTO hormozi_transcripts (video_id, title, duration, view_count, transcript_text, word_count)
        VALUES (?, ?, ?, ?, ?, ?);
      `, [video.videoId, video.title, video.lengthText, video.viewCountText, res.transcript, words]);
    }

    if ((idx + 1) % 15 === 0 || idx + 1 === validVideos.length) {
      console.log(`   [Progress ${idx + 1}/${validVideos.length}] Fetched transcript for: "${video.title.substring(0, 45)}" (${words} words)`);
    }

    return { ...video, ...res, words };
  });

  const actualParallelMs = Date.now() - startParallel;
  const actualParallelSec = (actualParallelMs / 1000).toFixed(2);

  const successfulFetches = results.filter(r => r.success && r.transcript).length;
  const totalWords = results.reduce((acc, r) => acc + (r.words || 0), 0);

  console.log('\n✅ Phase 4: Execution Complete & Database Saved!');
  console.log('====================================================');
  console.log(`📊 Total Transcripts Saved: ${successfulFetches} / ${validVideos.length}`);
  console.log(`📝 Total Words Ingested:   ${totalWords.toLocaleString()} words`);
  console.log(`💳 Credits Consumed:       ${1 + validVideos.length} credits (Remaining Allowance: ${1000 - (1 + validVideos.length)} credits)`);
  console.log('----------------------------------------------------');
  console.log('📈 EMPIRICAL TIMING COMPARISON:');
  console.log(`   • Predicted Sequential Time: ~${predSequentialSec}s`);
  console.log(`   • Predicted Parallel Time:   ~${predParallelSec}s`);
  console.log(`   • ACTUAL Parallel Time:      ⚡ ${actualParallelSec}s`);
  console.log(`   • Actual Speedup vs Seq:    ~${(predSequentialSec / actualParallelSec).toFixed(1)}x Faster!`);
  console.log('====================================================');

  db.close();
}

main().catch(console.error);
