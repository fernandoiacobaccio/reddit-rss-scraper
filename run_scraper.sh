#!/bin/bash
# ── Edit this path to match where you saved the project ──
PROJECT_DIR="$HOME/reddit_rss_scraper"

cd "$PROJECT_DIR" || exit 1
python3 scraper.py >> scraper.log 2>&1
