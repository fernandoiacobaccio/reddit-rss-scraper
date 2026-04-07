# Reddit RSS Scraper - Project Rules

Project-specific rules for Claude Code.

---

## Post-Compaction Rule
**Priority:** CRITICAL

When conversation is compacted:
1. Complete current task first
2. Re-read `CLAUDE.md` in full
3. Acknowledge refresh
4. Continue with next task

---

## Project Overview

**Reddit RSS Scraper** is a Python automation script that reads a Reddit user's private saved posts RSS feed and appends new entries to a Google Sheet. No Reddit API key required — only an RSS token from Reddit's preferences page.

**Tech Stack:** Python 3.8+ / gspread / Google Sheets API
**Target Users:** 1 user (runs on a schedule via Windows Task Scheduler)

---

## Project Organization
**Priority:** CRITICAL

### Directory Structure

| Folder | Contents |
|--------|----------|
| `scraper.py` | Main script — RSS fetch, dedup, Google Sheets append |
| `requirements.txt` | Python dependencies |
| `google_credentials.json` | Google service account key (NEVER commit) |
| `run_scraper.bat` | Windows Task Scheduler launcher |
| `run_scraper.sh` | Mac/Linux cron launcher |
| `task_scheduler.xml` | Windows Task Scheduler import config |
| `scraper.log` | Runtime log output (auto-generated) |
| `docs/` | Project documentation |
| `docs/workflows/` | Development workflow guides |
| `docs/templates/` | Document templates (STATE.md, REQUIREMENTS.md) |
| `wip/` | Active explorations / feature work |
| `archive/` | Completed explorations |

### Exploration Lifecycle

```
wip/exploration_name_YYYYMM/  -->  archive/[category]/exploration_name_YYYYMM/
```

**Requirements:**
- WIP explorations in `wip/exploration_name_YYYYMM/`
- Completed explorations move to `archive/` subfolder
- Every exploration MUST have: `README.md` + `RESULTS.md` + `STATE.md`
- New features SHOULD have: `REQUIREMENTS.md`

### Archive Categories

| Category | Path | Use For |
|----------|------|---------|
| Features | `archive/features/` | New functionality added to the scraper |
| Bugfixes | `archive/bugfixes/` | Bug fix documentation |
| Research | `archive/research/` | Research explorations |

---

## Security
**Priority:** CRITICAL

- **NEVER commit `google_credentials.json`** — contains private service account key
- **NEVER commit the RSS URL** with its token if it changes — treat like a password
- The `RSS_URL` in `scraper.py` contains a private Reddit token. Regenerate at `reddit.com/prefs/feeds/` if ever exposed.
- `scraper.log` is safe to commit (contains no secrets)

---

## Config Variables
**Priority:** CRITICAL

All user-specific config lives at the top of `scraper.py`:

| Variable | Line | Purpose |
|----------|------|---------|
| `RSS_URL` | ~20 | Reddit private RSS feed URL (contains token) |
| `SPREADSHEET_NAME` | ~22 | Exact name of the Google Sheet |
| `WORKSHEET_NAME` | ~23 | Tab name inside the sheet |
| `GOOGLE_CREDENTIALS_FILE` | ~25 | Path to service account JSON |

**NEVER hardcode values outside this config block.**

---

## Mandatory Testing
**Priority:** CRITICAL

**Before EVERY commit:**
```bash
python scraper.py
```

The script must run without errors. Check `scraper.log` for output.

See: `docs/workflows/TESTING.md` for full protocol.

---

## Commit Protocol
**Priority:** CRITICAL

- **NEVER push** without explicit user approval
- **NEVER commit `google_credentials.json`**
- Always `git diff` before staging
- Use meaningful commit messages (see `docs/workflows/GIT.md`)

---

## Anti-Patterns

- Committing `google_credentials.json` or RSS tokens
- Hardcoding config values outside the config block at the top of `scraper.py`
- Adding features beyond what was explicitly requested
- Pushing without explicit user approval
- Overwriting existing rows in the sheet (always append-only)
- Adding new Python dependencies without updating `requirements.txt`

---

## Reference Documents

| Document | Purpose | Location |
|----------|---------|----------|
| Project Atlas | Master navigation | `INDEX.md` |
| Git Workflow | Branching, commits | `docs/workflows/GIT.md` |
| Testing Protocol | When/how to run tests | `docs/workflows/TESTING.md` |
| State Template | Session tracking | `docs/templates/STATE_TEMPLATE.md` |
| Requirements Template | Feature scoping | `docs/templates/REQUIREMENTS_TEMPLATE.md` |
