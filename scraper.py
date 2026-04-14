"""
Reddit Saved Posts (RSS) → Google Sheets
-----------------------------------------
Fetches saved posts from a Reddit private RSS feed and appends
new ones to a Google Sheet. No Reddit API key required.

Features:
  - Deduplication by URL
  - Media detection: Image / GIF / Video / Redgif / Gallery / Text / Link / Comment
  - Repost detection: title fuzzy match + perceptual image hash
  - Header row with freeze on first run

Run manually or schedule with Task Scheduler (Windows) / cron (Mac).
"""

import io
import sys
import time
import logging
from datetime import datetime, timezone

import requests
import xml.etree.ElementTree as ET
import gspread
from google.oauth2.service_account import Credentials

try:
    from thefuzz import fuzz
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False

try:
    from PIL import Image
    import imagehash
    IMAGE_HASH_AVAILABLE = True
except ImportError:
    IMAGE_HASH_AVAILABLE = False

# ─── CONFIG — edit these lines, nothing else ──────────────────────────────────

RSS_URL = "https://www.reddit.com/user/DirectionEuphoric275/saved.rss?feed=7d202c884b326cb4ef634954444288b694b6b0bd&user=DirectionEuphoric275"

SPREADSHEET_NAME        = "Reddit Saved Assets"   # main sheet name
WORKSHEET_NAME          = "Assets"                # tab inside main sheet

GOOGLE_CREDENTIALS_FILE = "google_credentials.json"

TITLE_SIMILARITY_THRESHOLD = 85   # 0–100; scores above this flag a potential repost
IMAGE_HASH_THRESHOLD       = 10   # hamming distance; values below this flag a potential repost

REDDIT_API_DELAY           = 0.6  # seconds between Reddit JSON API calls (rate limit courtesy)

# ─── LOGGING ──────────────────────────────────────────────────────────────────

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

# Column order — do not reorder without updating index constants below
HEADER = [
    "URL",               # 0
    "Title",             # 1
    "Subreddit",         # 2
    "Type",              # 3
    "Date Fetched",      # 4
    "Status",            # 5
    "Comment",           # 6
    "Image Hash",        # 7
    "Potential Repost",  # 8
    "Media Type",        # 9
    "Media URL",         # 10
]

COL_URL        = 0
COL_TITLE      = 1
COL_HASH       = 7
COL_REPOST     = 8
COL_MEDIA_TYPE = 9
COL_MEDIA_URL  = 10

NS = {
    "atom":  "http://www.w3.org/2005/Atom",
    "media": "http://search.yahoo.com/mrss/",
}

REDDIT_HEADERS = {"User-Agent": "reddit-saved-rss-reader/1.0"}

# ─── GOOGLE SHEETS ────────────────────────────────────────────────────────────

def connect_sheets():
    """Connect to the assets spreadsheet. Returns the assets worksheet."""
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
        worksheet = spreadsheet.add_worksheet(title=WORKSHEET_NAME, rows=2000, cols=20)
        log.info(f"Created new worksheet '{WORKSHEET_NAME}'.")

    return worksheet


def ensure_header(worksheet):
    """
    Write header and freeze row 1 on first run.
    Updates header silently if new columns were added.
    Returns (existing_urls, existing_rows).
    """
    rows = worksheet.get_all_values()

    if not rows:
        worksheet.append_row(HEADER, value_input_option="RAW")
        worksheet.freeze(rows=1)
        log.info("Header row written and frozen.")
        return [], []

    if rows[0] != HEADER:
        worksheet.update([HEADER], "A1")
        worksheet.freeze(rows=1)
        log.info("Header row updated and frozen.")

    existing_rows = rows[1:]
    existing_urls = [row[COL_URL] for row in existing_rows if row and row[COL_URL]]
    return existing_urls, existing_rows


# ─── MEDIA DETECTION ──────────────────────────────────────────────────────────

def fetch_post_media(post_url, kind):
    """
    Fetch Reddit's JSON API for a post and detect the media type + direct URL.

    Returns (media_type, media_url, thumbnail_url) where media_type is one of:
      Image | GIF | Video | Redgif | Gallery | Text | Link | Comment | Unknown
    """
    if kind == "Comment":
        return "Comment", "", ""

    json_url = post_url.rstrip("/") + ".json"
    try:
        resp = requests.get(json_url, headers=REDDIT_HEADERS, timeout=15)
        resp.raise_for_status()
        data      = resp.json()
        post_data = data[0]["data"]["children"][0]["data"]
    except Exception as e:
        log.debug(f"Could not fetch post metadata for {post_url}: {e}")
        return "Unknown", "", ""

    asset_url  = post_data.get("url", "")
    post_hint  = post_data.get("post_hint", "")
    is_video   = post_data.get("is_video", False)
    is_self    = post_data.get("is_self", False)
    media      = post_data.get("media") or {}

    # ── Thumbnail: prefer highest-res preview image ──
    thumbnail_url = ""
    preview = post_data.get("preview") or {}
    images  = preview.get("images", [])
    if images:
        resolutions = images[0].get("resolutions", [])
        source      = images[0].get("source", {})
        best        = resolutions[-1] if resolutions else source
        thumbnail_url = best.get("url", "").replace("&amp;", "&")

    if not thumbnail_url:
        raw_thumb = post_data.get("thumbnail", "")
        if raw_thumb not in ("self", "default", "nsfw", "spoiler", "image", ""):
            thumbnail_url = raw_thumb

    # ── Redgifs ──
    if "redgifs.com" in asset_url or "redgifs.com" in str(media).lower():
        return "Redgif", asset_url, thumbnail_url

    # ── Reddit-hosted video ──
    if is_video or post_hint == "hosted:video":
        reddit_video = media.get("reddit_video", {})
        video_url    = reddit_video.get("fallback_url", asset_url)
        return "Video", video_url, thumbnail_url

    # ── External rich video (YouTube, Streamable, etc.) ──
    if post_hint == "rich:video":
        oembed   = media.get("oembed", {})
        provider = oembed.get("provider_name", "").lower()
        if "redgifs" in provider or "redgifs" in asset_url:
            return "Redgif", asset_url, thumbnail_url
        return "Video", asset_url, thumbnail_url

    # ── v.redd.it direct video links ──
    if "v.redd.it" in asset_url:
        return "Video", asset_url, thumbnail_url

    # ── Reddit gallery ──
    if post_hint == "gallery" or post_data.get("is_gallery"):
        return "Gallery", asset_url, thumbnail_url

    # ── Image ──
    if post_hint == "image":
        lower = asset_url.lower()
        if lower.endswith(".gif") or "giphy.com" in lower:
            return "GIF", asset_url, thumbnail_url
        return "Image", asset_url, thumbnail_url

    # ── URL-extension fallback ──
    lower = asset_url.lower().split("?")[0]
    if lower.endswith((".jpg", ".jpeg", ".png", ".webp")):
        return "Image", asset_url, thumbnail_url
    if lower.endswith(".gif"):
        return "GIF", asset_url, thumbnail_url
    if lower.endswith((".gifv", ".mp4", ".webm")):
        return "Video", asset_url, thumbnail_url
    if "i.redd.it" in asset_url or "i.imgur.com" in asset_url:
        return "Image", asset_url, thumbnail_url

    # ── Text / self post ──
    if is_self or post_hint == "self":
        return "Text", "", thumbnail_url

    # ── Anything else is an external link ──
    return "Link", asset_url, thumbnail_url

# ─── IMAGE HASHING ────────────────────────────────────────────────────────────

def fetch_image_hash(thumbnail_url):
    """Download thumbnail and return perceptual hash string, or '' on failure."""
    if not IMAGE_HASH_AVAILABLE or not thumbnail_url:
        return ""
    try:
        resp = requests.get(thumbnail_url, timeout=10, headers=REDDIT_HEADERS)
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content)).convert("RGB")
        return str(imagehash.phash(img))
    except Exception as e:
        log.debug(f"Image hash failed for {thumbnail_url}: {e}")
        return ""

# ─── REPOST DETECTION ─────────────────────────────────────────────────────────

def find_repost(title, img_hash, existing_rows):
    """
    Check title similarity and image hash against all existing rows.
    Returns the URL of the suspected original post, or ''.
    A match requires EITHER a close-enough title OR a close-enough image hash.
    """
    for row in existing_rows:
        if len(row) < 2:
            continue

        existing_url   = row[COL_URL]   if len(row) > COL_URL   else ""
        existing_title = row[COL_TITLE] if len(row) > COL_TITLE else ""
        existing_hash  = row[COL_HASH]  if len(row) > COL_HASH  else ""

        if FUZZY_AVAILABLE and title and existing_title:
            if fuzz.token_sort_ratio(title.lower(), existing_title.lower()) >= TITLE_SIMILARITY_THRESHOLD:
                return existing_url

        if IMAGE_HASH_AVAILABLE and img_hash and existing_hash:
            try:
                if (imagehash.hex_to_hash(img_hash) - imagehash.hex_to_hash(existing_hash)) <= IMAGE_HASH_THRESHOLD:
                    return existing_url
            except Exception:
                pass

    return ""

# ─── RSS PARSING ──────────────────────────────────────────────────────────────

def fetch_rss(url):
    try:
        resp = requests.get(url, headers=REDDIT_HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        log.error(f"Failed to fetch RSS feed: {e}")
        sys.exit(1)

    root    = ET.fromstring(resp.content)
    entries = root.findall("atom:entry", NS)
    log.info(f"RSS feed returned {len(entries)} entries.")

    items = []
    for entry in entries:
        link_el = entry.find("atom:link[@rel='alternate']", NS)
        if link_el is None:
            link_el = entry.find("atom:link", NS)
        url_val = link_el.attrib.get("href", "").strip() if link_el is not None else ""
        url_val = url_val.replace("old.reddit.com", "www.reddit.com")

        if not url_val or "reddit.com" not in url_val:
            continue

        title = (entry.findtext("atom:title", default="", namespaces=NS) or "").strip()

        cat       = entry.find("atom:category", NS)
        subreddit = ""
        if cat is not None:
            label     = cat.attrib.get("label", "")
            subreddit = label.lstrip("r/") if label else cat.attrib.get("term", "")

        kind         = "Comment" if "/comment/" in url_val else "Post"
        date_fetched = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        items.append((url_val, title, subreddit, kind, date_fetched))

    return items

# ─── DEDUP + APPEND ───────────────────────────────────────────────────────────

def append_new(worksheet, existing_urls, existing_rows, items):
    existing_set = set(existing_urls)
    all_rows     = list(existing_rows)
    new_rows     = []

    for url_val, title, subreddit, kind, date_fetched in items:
        if url_val in existing_set:
            continue

        # Fetch media info from Reddit JSON API
        media_type, media_url, thumbnail_url = fetch_post_media(url_val, kind)
        log.info(f"  [{media_type}] {title[:60]}")
        time.sleep(REDDIT_API_DELAY)

        img_hash  = fetch_image_hash(thumbnail_url)
        repost_of = find_repost(title, img_hash, all_rows)

        if repost_of:
            log.info(f"  Potential repost detected -> {repost_of}")

        row = [
            url_val, title, subreddit, kind, date_fetched,
            "Pending", "",
            img_hash, repost_of,
            media_type, media_url,
        ]
        new_rows.append(row)
        existing_set.add(url_val)
        all_rows.append(row)

    if not new_rows:
        log.info("No new items — sheet is already up to date.")
        return 0

    worksheet.append_rows(new_rows, value_input_option="RAW")
    log.info(f"Added {len(new_rows)} new row(s).")
    return len(new_rows)

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    log.info("=== Reddit RSS Scraper starting ===")

    if not FUZZY_AVAILABLE:
        log.warning("thefuzz not installed — title similarity detection disabled.")
    if not IMAGE_HASH_AVAILABLE:
        log.warning("Pillow/imagehash not installed — image hash detection disabled.")

    worksheet                    = connect_sheets()
    existing_urls, existing_rows = ensure_header(worksheet)
    log.info(f"Sheet currently has {len(existing_urls)} entries.")

    items = fetch_rss(RSS_URL)
    added = append_new(worksheet, existing_urls, existing_rows, items)
    log.info(f"=== Done. {added} new item(s) added. ===")


if __name__ == "__main__":
    main()
