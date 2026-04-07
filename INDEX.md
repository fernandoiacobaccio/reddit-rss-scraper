# Reddit RSS Scraper - Project Atlas

> Master navigation document.
> A Python automation script that syncs Reddit saved posts to Google Sheets via RSS feed.

---

## Quick Navigation

| Section | Description |
|---------|-------------|
| [Project Structure](#project-structure) | File layout |
| [How It Works](#how-it-works) | Script logic overview |
| [Configuration](#configuration) | Key settings |
| [Documentation](#documentation) | Docs and workflows |
| [Current Work](#current-work) | Active explorations |
| [Archive](#archived-explorations) | Completed work |

---

## Project Structure

```
reddit_rss_scraper/
  scraper.py              # Main script
  requirements.txt        # Python dependencies
  google_credentials.json # Service account key (NOT committed)
  run_scraper.bat         # Windows Task Scheduler launcher
  run_scraper.sh          # Mac/Linux cron launcher
  task_scheduler.xml      # Task Scheduler import config
  scraper.log             # Runtime log (auto-generated)
  CLAUDE.md               # Claude Code project rules
  INDEX.md                # This file
  docs/
    workflows/
      GIT.md              # Git workflow
      TESTING.md          # Testing protocol
    templates/
      STATE_TEMPLATE.md   # Session state template
      REQUIREMENTS_TEMPLATE.md  # Feature requirements template
  wip/                    # Active explorations
  archive/
    features/             # Completed feature work
    bugfixes/             # Completed bug fixes
    research/             # Research explorations
```

---

## How It Works

```
Reddit RSS Feed  -->  fetch_rss()  -->  parse entries
                                          |
Google Sheet  <--  append_new()  <--  dedup against existing URLs
```

1. `fetch_rss()` — GETs the private Reddit RSS URL, parses Atom XML entries
2. `ensure_header()` — Writes header row if sheet is empty, returns existing URLs
3. `append_new()` — Skips already-seen URLs, appends only new rows
4. Sheet columns: `URL | Title | Subreddit | Type | Date Fetched | Status | Comment`

**Dedup key:** URL. The script never overwrites existing rows.

---

## Configuration

All config is at the top of `scraper.py` (~line 20):

| Variable | Purpose |
|----------|---------|
| `RSS_URL` | Reddit private RSS URL (contains secret token) |
| `SPREADSHEET_NAME` | Exact Google Sheet name (`Reddit Saved Assets`) |
| `WORKSHEET_NAME` | Tab name (`Assets`) |
| `GOOGLE_CREDENTIALS_FILE` | Service account JSON path |

---

## Documentation

| Document | Purpose | Location |
|----------|---------|----------|
| Project Rules | Claude Code instructions | `CLAUDE.md` |
| Git Workflow | Branching, commits | `docs/workflows/GIT.md` |
| Testing Protocol | When/how to test | `docs/workflows/TESTING.md` |
| State Template | Session tracking | `docs/templates/STATE_TEMPLATE.md` |
| Requirements Template | Feature scoping | `docs/templates/REQUIREMENTS_TEMPLATE.md` |

---

## Current Work

| Exploration | Status | Location |
|-------------|--------|----------|
| _(none active)_ | — | — |

---

## Archived Explorations

### Features
| Exploration | Description | Status |
|-------------|-------------|--------|
| _(none yet)_ | | |

### Bugfixes
| Exploration | Issue | Status |
|-------------|-------|--------|
| _(none yet)_ | | |

### Research
| Exploration | Focus | Status |
|-------------|-------|--------|
| _(none yet)_ | | |

---

## Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| RSS over Reddit API | No API approval needed; RSS token from reddit.com/prefs/feeds/ |
| Append-only sheet | Never overwrite existing rows — Status/Comment are manually edited |
| Dedup by URL | URLs are stable unique identifiers for Reddit posts/comments |
| 25-post RSS limit | Reddit caps RSS at 25 most recent saves — run every 4h to avoid gaps |
| Service account auth | No OAuth flow required; service account email gets Editor on the sheet |
