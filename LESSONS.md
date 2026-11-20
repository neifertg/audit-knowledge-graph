# Lessons

One entry per lesson, added with `python -m capitan learn "<title>" --area <a,b> --body "..."`.
Plans search this file automatically. A lesson that keeps recurring should become a check (a test, a lint rule, a hook), not a longer entry.

Format: `### L-NNN (YYYY-MM-DD) [areas] Title`, then what happened and what to do next time.

### L-001 (2026-11-20) [workflow] Owner-run commands: copy-paste blocks, never an editor
When the owner must run something (capitan approve, capitan allow-governance, committing a governance file such as .gitignore), give one complete PowerShell block to paste, including branch switches and the allow-governance step. Never give a git command that opens an editor: use git merge --no-edit, git commit -m, git commit --no-edit. A plain git merge dropped the owner into Vim (2026-11-20).
Source: 005-sample-pack-for-realism-review
Scope: general

### L-002 (2026-11-20) [src/features/generator] AI rewrites invent facts unless code enforces the rule
Asked to rewrite drafts, claude-opus-5-5 added system names absent from the draft (even when the prompt said not to) and expanded brief ERM controls into detailed ones, which made matched ERM/IA pairs too similar (killed hard negatives) and less realistic. Next time: state the rule in the prompt AND check it in code with a retry plus a test (write_text.added_systems); regenerate the whole set after any prompt change so all text shares one prompt.
Source: 005-sample-pack-for-realism-review

### L-003 (2026-11-20) [src/features/generator] Cross-source text needs shared domain vocabulary for realistic near-misses
ERM risk statements and IA audit-universe entries shared almost no words, so TF-IDF found no hard negatives (non-match >= matched median). Prefixing IA entries with their audit area and letting sibling scopes overlap fixed it realistically. At ~15 rows the hard-negative check is fragile (0.18 vs 0.19 margins); children c/d should measure it at full size before tuning content.
Source: 005-sample-pack-for-realism-review

### L-004 (2026-11-20) [workflow] capitan rescue runs from main and leaves files uncommitted
capitan rescue <id> refuses on the change branch ('switch to main first'), copies knowledge into main's working tree, and expects you to commit there; the branch switch back then fails until you commit. Sequence: commit on branch, git switch main, capitan rescue <id>, commit on main, git switch back, git merge --no-edit main.
Source: 005-sample-pack-for-realism-review

### L-005 (2026-11-20) [src/features/generator] Give every per-row choice its own random stream from day one
rng.choice consumes a variable number of random bits depending on the list length, so drawing issue owners from the issue stream made the person count shift every later issue draw (006). Fixing it later changes existing output and conflicts with criteria that freeze it. Next time: any draw from another entity's population (owners, links) gets its own stream named after the relationship file, from the first commit.
Source: 006-organization-regulations-taxonomies-and

### L-006 (2026-11-20) [workflow] Check new criteria against output-freezing criteria before approval
006's AC-5 froze sample output while AC-6 demanded a --count PERSON independence that could only be reached by changing sample output; the conflict surfaced mid-build and cost a plan revision. Next time: when a plan freezes existing output, check every other criterion for whether it needs that output to change, and probe the code (one quick run) before approval.
Source: 006-organization-regulations-taxonomies-and
