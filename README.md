# Gemini Chat History Archival & Filtering System

A fast, searchable local archive for Google Takeout Gemini chat exports.

## Features
- **Input Audio Filtered**: All 691 `.wav` raw input audio recordings and audio links have been excluded to save storage space and focus purely on chat text and outputs.
- **Attachments & Images Preserved**: 867 non-audio media assets (including 526 `.jpg`/`.png`/`.webp` images, PDFs, CSVs, and ZIPs) are preserved and linked.
- **SQLite FTS5 Full-Text Search**: Indexed search across all **8,258 chat entries** with sub-millisecond response times.
- **Clean JSON & Database Storage**: Complete parsed chat exports in `data/chats.json` and `data/gemini_archive.db`.
- **Local Web UI Browser**: Interactive web interface for searching, filtering by voice input vs text, and reading past conversations with syntax highlighting and image previews.

---

## Directory Overview
```
gemini-analyzer/
├── data/
│   ├── gemini_archive.db      # SQLite database with FTS5 search index
│   ├── chats.json             # Structured JSON export of all 8,258 chats
│   └── media/                 # Preserved images, PDFs, CSVs, and ZIP attachments
├── src/
│   ├── parser.py              # Takeout HTML streaming card parser
│   ├── db.py                  # Database & asset archiving engine
│   └── server.py              # Lightweight HTTP server & REST API
├── templates/
│   └── index.html             # Responsive Web UI client
└── run_pipeline.py            # Main launcher CLI
```

---

## How to Run

### Start the Web Viewer
To launch the chat archive web UI on `http://localhost:8765/`:
```bash
python3 run_pipeline.py --port 8765
```
Open [http://localhost:8765/](http://localhost:8765/) in your browser to search and browse your chat history.

### Rebuild the Archive
If you add new Google Takeout files to `/Users/austinrognes/Seagate-NAS/Gemini`:
```bash
python3 run_pipeline.py --rebuild --takeout /Users/austinrognes/Seagate-NAS/Gemini
```

---

## API Endpoints

- **`GET /api/stats`**: Summary statistics (total chats, voice input chats count).
- **`GET /api/chats?q=<keyword>&sort=desc&audio_only=0&page=1`**: Full-text search & paginated chats.
- **`GET /media/<filename>`**: Serve archived images and document attachments.
