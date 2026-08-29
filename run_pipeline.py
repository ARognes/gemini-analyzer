#!/usr/bin/env python3
import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.db import build_database_and_archive
from src.classifier import run_thread_classification
from src.linker import run_knowledge_linker
from src.ingest import run_incremental_ingestion
from src.server import run_server

def main():
    parser = argparse.ArgumentParser(description="Gemini Chat History Archival & Intelligence System")
    parser.add_argument('--rebuild', action='store_true', help="Rebuild database from scratch from Takeout folder")
    parser.add_argument('--ingest', action='store_true', help="Incrementally ingest new Takeout export")
    parser.add_argument('--port', type=int, default=8765, help="Port to run web server (default: 8765)")
    parser.add_argument('--takeout', type=str, default='/Users/austinrognes/Seagate-NAS/Gemini', help="Path to Google Takeout Gemini folder")
    parser.add_argument('--data', type=str, default=os.path.join(os.path.dirname(__file__), 'data'), help="Output data directory")

    args = parser.parse_args()

    db_file = os.path.join(args.data, 'gemini_archive.db')

    if args.rebuild or not os.path.exists(db_file):
        print(f"🔨 Building archive database at {args.data}...")
        build_database_and_archive(args.takeout, args.data)
        run_thread_classification(db_file)
        run_knowledge_linker(db_file)
    elif args.ingest:
        print(f"📥 Incrementally ingesting Takeout export from {args.takeout}...")
        run_incremental_ingestion(args.takeout, args.data)

    print(f"🚀 Starting Gemini Archive Web Viewer on http://localhost:{args.port}/")
    run_server(port=args.port)

if __name__ == '__main__':
    main()
