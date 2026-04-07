# Reddit Saved Posts → Google Sheets
## Setup guide (RSS version — no Reddit API approval needed)

---

## What you need before starting

- Python 3.8+ → https://www.python.org/downloads/
- A Google account

That's it. No Reddit developer account, no API keys, no approval process.

---

## Step 1 — Install Python packages

Open Terminal (Mac) or Command Prompt (Windows) inside the project folder and run:

```
pip install -r requirements.txt
```

---

## Step 2 — Regenerate the RSS feed URL (important for security)

The RSS URL you already have works, but since it was shared in a chat,
generate a fresh one so only you have it:

1. Your boss logs into Reddit.
2. Go to: https://www.reddit.com/prefs/feeds/
3. Find "Saved Links" in the list.
4. Click the orange **RSS** button next to it.
5. Copy the full URL from the browser address bar.
   It looks like:
   https://www.reddit.com/user/USERNAME/saved.rss?feed=LONGTOKEN&user=USERNAME

6. Open `scraper.py` and paste it as the value of `RSS_URL` on line 16.

---

## Step 3 — Set up Google Sheets credentials (5 minutes)

### 3a. Create a Google Cloud service account

1. Go to https://console.cloud.google.com
2. Create a new project (top-left dropdown → New Project). Name it anything.
3. Enable two APIs — search each by name and click Enable:
   - **Google Sheets API**
   - **Google Drive API**
4. Go to **IAM & Admin → Service Accounts → + Create Service Account**
   - Name: `reddit-scraper` (anything)
   - Click **Create and Continue → Done**
5. Click the service account you just created.
6. Go to the **Keys** tab → **Add Key → Create new key → JSON**
7. A file downloads automatically. Rename it `google_credentials.json`.
8. Move it into the same folder as `scraper.py`.

### 3b. Create and share the Google Sheet

1. Go to https://sheets.google.com and create a new spreadsheet.
2. Name it exactly: `Reddit Saved Assets`
   (must match `SPREADSHEET_NAME` in scraper.py)
3. Click **Share**.
4. Open `google_credentials.json` and find the `"client_email"` field.
   It looks like: `reddit-scraper@your-project.iam.gserviceaccount.com`
5. Paste that email into the Share dialog.
6. Give it **Editor** access → click **Share**.

---

## Step 4 — Run the script manually to test

In Terminal / Command Prompt, from the project folder:

```
python scraper.py          # Mac/Linux
python scraper.py          # Windows
```

Expected output:
```
2026-04-06 10:00:01  INFO     === Reddit RSS Scraper starting ===
2026-04-06 10:00:02  INFO     Sheet currently has 0 entries.
2026-04-06 10:00:03  INFO     RSS feed returned 25 entries.
2026-04-06 10:00:05  INFO     Added 25 new row(s).
2026-04-06 10:00:05  INFO     === Done. 25 new item(s) added. ===
```

Open your Google Sheet — it should now have all the saved posts.

---

## Step 5 — Schedule it to run automatically

### Windows (Task Scheduler)

1. Edit `run_scraper.bat`: update `PROJECT_DIR` to your actual folder path.
2. Open **Task Scheduler** (search in Start menu).
3. Click **Create Basic Task…**
4. Name: `Reddit RSS Scraper`
5. Trigger: **Daily**
6. Action: **Start a program** → browse to `run_scraper.bat`
7. Finish, then right-click the task → Properties → Triggers → Edit →
   check **Repeat task every 4 hours** → OK.

### Mac (cron — simplest option)

1. Edit `run_scraper.sh` — update `PROJECT_DIR` to your real path.
2. Make it executable:
   ```
   chmod +x run_scraper.sh
   ```
3. Open crontab:
   ```
   crontab -e
   ```
4. Add this line (runs every 4 hours):
   ```
   0 */4 * * * /Users/yourname/reddit_rss_scraper/run_scraper.sh
   ```
5. Save and exit. Done.

---

## What lands in the sheet

| URL | Title | Subreddit | Type | Date Fetched | Status | Comment |
|-----|-------|-----------|------|--------------|--------|---------|
| https://reddit.com/… | Post title | marketing | Post | 2026-04-06 | Pending | |

- **Status** starts as `Pending`. Change it to `Approved` or `Ignored` manually.
- **Comment** is free text for your notes.
- The script **never overwrites** existing rows — only appends new ones.
- Safe to run as often as you want — duplicates are always skipped.

---

## Important: the 25-post RSS limit

Reddit's RSS feed only returns the **25 most recently saved** items per request.
This means:
- If your boss saves more than 25 posts between script runs, the oldest ones
  in that batch will be missed.
- Running every 4 hours is sufficient for normal use.
- If your boss goes on a heavy saving spree, run the script manually mid-day.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` again |
| `Spreadsheet not found` | Check the name in scraper.py matches exactly, and the sheet is shared with the service account email |
| `403 from Google` | Service account wasn't given Editor access to the sheet |
| RSS returns 0 entries | The RSS URL may have expired — regenerate it at reddit.com/prefs/feeds/ |
| Script adds 0 rows | No new saves since last run — that's normal |

---

## Security reminder

- `google_credentials.json` is sensitive — don't share it or commit it to GitHub.
- The RSS URL contains a private token — treat it like a password.
  Regenerate it at `reddit.com/prefs/feeds/` if it's ever exposed.
