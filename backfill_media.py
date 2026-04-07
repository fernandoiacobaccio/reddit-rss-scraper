"""
Backfill Media Type, Media URL, and Image Hash for existing rows.

One-time script — run once to populate the new columns for all
rows that were added before media detection was implemented.
Safe to re-run: skips rows that already have a Media Type value.
"""

import time
import sys
import logging

import gspread
from google.oauth2.service_account import Credentials

from scraper import (
    GOOGLE_CREDENTIALS_FILE,
    SPREADSHEET_NAME,
    WORKSHEET_NAME,
    SCOPES,
    COL_URL,
    COL_TITLE,
    COL_HASH,
    COL_MEDIA_TYPE,
    COL_MEDIA_URL,
    REDDIT_API_DELAY,
    fetch_post_media,
    fetch_image_hash,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)


def col_letter(index):
    """Convert 0-based column index to A1 letter (e.g. 0 → A, 9 → J)."""
    return chr(ord("A") + index)


def main():
    log.info("=== Backfill starting ===")

    creds     = Credentials.from_service_account_file(GOOGLE_CREDENTIALS_FILE, scopes=SCOPES)
    client    = gspread.authorize(creds)
    sheet     = client.open(SPREADSHEET_NAME)
    worksheet = sheet.worksheet(WORKSHEET_NAME)

    rows = worksheet.get_all_values()
    if not rows:
        log.info("Sheet is empty. Nothing to backfill.")
        return

    header    = rows[0]
    data_rows = rows[1:]     # skip header row
    total     = len(data_rows)
    log.info(f"Found {total} data rows. Scanning for empty Media Type...")

    # Collect cell updates to batch into one Sheets API call at the end
    updates   = []
    processed = 0

    for i, row in enumerate(data_rows):
        sheet_row = i + 2   # 1-based, +1 for header

        url_val    = row[COL_URL]   if len(row) > COL_URL        else ""
        kind_val   = row[3]         if len(row) > 3              else "Post"
        media_type = row[COL_MEDIA_TYPE] if len(row) > COL_MEDIA_TYPE else ""
        img_hash   = row[COL_HASH]  if len(row) > COL_HASH       else ""

        # Skip if already filled
        if media_type:
            continue

        if not url_val:
            continue

        log.info(f"  [{processed + 1}] Row {sheet_row}: {url_val[:70]}")

        m_type, m_url, thumb_url = fetch_post_media(url_val, kind_val)
        time.sleep(REDDIT_API_DELAY)

        # Only fetch image hash if we don't already have one
        if not img_hash and thumb_url:
            img_hash = fetch_image_hash(thumb_url)

        log.info(f"       -> {m_type} | {m_url[:60] if m_url else '(none)'}")

        # Queue cell updates
        updates.append({
            "range":  f"{col_letter(COL_MEDIA_TYPE)}{sheet_row}:{col_letter(COL_MEDIA_URL)}{sheet_row}",
            "values": [[m_type, m_url]],
        })
        if img_hash:
            updates.append({
                "range":  f"{col_letter(COL_HASH)}{sheet_row}",
                "values": [[img_hash]],
            })

        processed += 1

        # Write to sheet in batches of 20 to avoid hitting API limits
        if len(updates) >= 20:
            worksheet.batch_update(updates)
            log.info(f"  Wrote batch of {len(updates)} updates to sheet.")
            updates = []

    # Write any remaining updates
    if updates:
        worksheet.batch_update(updates)
        log.info(f"  Wrote final batch of {len(updates)} updates to sheet.")

    log.info(f"=== Backfill complete. Processed {processed} rows. ===")


if __name__ == "__main__":
    main()
