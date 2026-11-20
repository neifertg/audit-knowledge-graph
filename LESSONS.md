# Lessons

One entry per lesson, added with `python -m capitan learn "<title>" --area <a,b> --body "..."`.
Plans search this file automatically. A lesson that keeps recurring should become a check (a test, a lint rule, a hook), not a longer entry.

Format: `### L-NNN (YYYY-MM-DD) [areas] Title`, then what happened and what to do next time.

### L-001 (2026-11-20) [workflow] Owner-run commands: copy-paste blocks, never an editor
When the owner must run something (capitan approve, capitan allow-governance, committing a governance file such as .gitignore), give one complete PowerShell block to paste, including branch switches and the allow-governance step. Never give a git command that opens an editor: use git merge --no-edit, git commit -m, git commit --no-edit. A plain git merge dropped the owner into Vim (2026-11-20).
Source: 005-sample-pack-for-realism-review
Scope: general
