"""
Reddit Saved Posts (RSS) → Google Sheets
-----------------------------------------
Fetches saved posts from a Reddit private RSS feed and appends
new ones to a Google Sheet. No Reddit API key required.

Run manually or schedule with Task Scheduler (Windows) / launchd (Mac).
"""

import requests
import xml.etree.ElementTree as ET
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import logging
import sys

# ─── CONFIG — edit these three lines, nothing else ───────────────────────────

RSS_URL = "https://www.reddit.com/user/DirectionEuphoric275/saved.rss?feed=7d202c884b326cb4ef634954444288b694b6b0bd&user=DirectionEuphoric275"

SPREADSHEET_NAME = "Reddit Saved Assets"   # exact name of your Google Sheet
WORKSHEET_NAME   = "Assets"                # tab name inside the sheet

GOOGLE_CREDENTIALS_FILE = "google_credentials.json"  # keep in same folder as this script

# ─── LOGGING ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("scraper.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# ─── CONSTANTS ────────────────────────────────────────────────────────────────

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

HEADER = ["URL", "Title", "Subreddit", "Type", "Date Fetched", "Status", "Comment"]

# Reddit Atom feed namespace
NS = {"atom": "http://www.w3.org/2005/Atom"}

# ─── GOOGLE SHEETS ────────────────────────────────────────────────────────────

def connect_sheets():
    creds  = Credentials.from_service_account_file(GOOGLE_CREDENTIALS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)
    except gspread.SpreadsheetNotFound:
        log.error(
            f"Spreadsheet '{SPREADSHEET_NAME}' not found. "
            "Create it in Google Sheets and share it with your service account email."
        )
        sys.exit(1)
    try:
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=WORKSHEET_NAME, rows=2000, cols=10)
        log.info(f"Created new worksheet '{WORKSHEET_NAME}'.")
    return worksheet


def ensure_header(worksheet):
    """Write header if sheet is empty. Returns list of existing URLs."""
    rows = worksheet.get_all_values()
    if not rows:
        worksheet.append_row(HEADER, value_input_option="RAW")
        log.info("Header row written.")
        return []
    return [row[0] for row in rows[1:] if row and row[0]]

# ─── RSS PARSING ──────────────────────────────────────────────────────────────

def fetch_rss(url):
    headers = {"User-Agent": "reddit-saved-rss-reader/1.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        log.error(f"Failed to fetch RSS feed: {e}")
        sys.exit(1)

    root = ET.fromstring(resp.content)
    entries = root.findall("atom:entry", NS)
    log.info(f"RSS feed returned {len(entries)} entries.")

    items = []
    for entry in entries:
        # URL — prefer the <link rel="alternate"> href
        link_el = entry.find("atom:link[@rel='alternate']", NS)
        if link_el is None:
            link_el = entry.find("atom:link", NS)
        url_val = link_el.attrib.get("href", "").strip() if link_el is not None else ""

        # Normalise to new.reddit.com links
        url_val = url_val.replace("old.reddit.com", "www.reddit.com")

        if not url_val or "reddit.com" not in url_val:
            continue

        title = (entry.findtext("atom:title", default="", namespaces=NS) or "").strip()

        # Subreddit from <category> label attribute
        cat = entry.find("atom:category", NS)
        subreddit = ""
        if cat is not None:
            label = cat.attrib.get("label", "")          # e.g. "r/marketing"
            subreddit = label.lstrip("r/") if label else cat.attrib.get("term", "")

        # Post vs Comment — comments have /comments/.../comment_id/ in URL
        kind = "Comment" if "/comment/" in url_val else "Post"

        date_fetched = datetime.utcnow().strftime("%Y-%m-%d")

        items.append((url_val, title, subreddit, kind, date_fetched))

    return items

# ─── DEDUP + APPEND ───────────────────────────────────────────────────────────

def append_new(worksheet, existing_urls, items):
    existing_set = set(existing_urls)
    new_rows = []
    for url, title, subreddit, kind, date_fetched in items:
        if url not in existing_set:
            new_rows.append([url, title, subreddit, kind, date_fetched, "Pending", ""])
            existing_set.add(url)

    if not new_rows:
        log.info("No new items — sheet is already up to date.")
        return 0

    worksheet.append_rows(new_rows, value_input_option="RAW")
    log.info(f"Added {len(new_rows)} new row(s).")
    return len(new_rows)

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    log.info("=== Reddit RSS Scraper starting ===")
    worksheet     = connect_sheets()
    existing_urls = ensure_header(worksheet)
    log.info(f"Sheet currently has {len(existing_urls)} entries.")

    items = fetch_rss(RSS_URL)
    added = append_new(worksheet, existing_urls, items)

    log.info(f"=== Done. {added} new item(s) added. ===")

if __name__ == "__main__":
    main()
