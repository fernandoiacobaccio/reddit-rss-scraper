# Git Workflow

## Session Start

Always check state first:
```bash
git status
git branch
```

## Branch Rules

| When | Action |
|------|--------|
| Creating/modifying files | Create feature branch |
| Only reading or running existing code | No branch needed |
| New feature | `feature/description` |
| Bug fix | `fix/description` |
| Research/exploration | `research/description` |

## Commit Discipline

- Commit frequently with meaningful messages
- Always `git diff` before staging
- Never push without user approval
- Never commit `google_credentials.json`

**Good messages:** `feat: filter out comment saves`, `fix: handle empty RSS feed gracefully`
**Bad messages:** `fix`, `update`, `changes`, `stuff`

## Safety Rules

- NEVER push without explicit user approval
- NEVER force push unless explicitly requested
- NEVER commit secrets (`google_credentials.json`, RSS token URLs)

## .gitignore Essentials

```
google_credentials.json
scraper.log
__pycache__/
*.pyc
.env
```
