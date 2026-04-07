# Testing Protocol

## Simple Rule

| Change Type | Run Tests? |
|-------------|-----------|
| `scraper.py` (any change) | YES — run the script |
| `requirements.txt` | YES — `pip install -r requirements.txt` + run script |
| `.md` (documentation only) | NO |
| `.bat` / `.sh` launcher scripts | YES — run the launcher |

## Test Command

**Must pass before ANY commit touching Python files:**

```bash
python scraper.py
```

Then check `scraper.log` for:
- No `ERROR` lines
- `=== Done. X new item(s) added. ===` at the end (or "already up to date")

## Full Smoke Test Checklist

When making significant changes to `scraper.py`:

- [ ] Script runs without exceptions
- [ ] Sheet connection succeeds
- [ ] RSS feed fetches successfully (log shows entry count)
- [ ] No duplicate rows added to the sheet
- [ ] New rows appear in correct columns (URL, Title, Subreddit, Type, Date Fetched, Status=Pending, Comment=empty)

## NO EXCEPTIONS

- Applies to ALL changes: one line or the whole file
- Applies to ALL branches
- If the script errors, fix it before committing
