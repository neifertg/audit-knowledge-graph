# Goals

Filled in by the kickoff interview (`capitan/playbooks/kickoff.md`, 2026-11-19). Every standard change names one objective below; work that serves none of them waits.

## Problem
CAEs, audit analytics managers and AI/data people inside risk functions hear "knowledge graph" everywhere but rarely see a credible, audit-specific demonstration of when it beats their existing SQL/GRC tooling, and when it does not. Meanwhile audit planning misses risk that lives *between* tables: shared-system exposure, repeat findings filed under different names, stale coverage. Real institutions also lack a common risk and control framework, because ERM and Internal Audit keep separate, overlapping populations; most demos assume that problem away.

This project is a public showcase (and reusable template) on the owner's GitHub Pages. Its audience is CAEs, audit analytics managers and AI/data roles inside risk functions. The action wanted from them: invite the owner to interview, and share the project with their team.

## Objectives
Outcomes, not tasks, ranked: when two conflict, the higher one wins. O5 is the outcome the others serve; it is tracked, not built.
- **O1**: A CAE grasps the value in about 60 seconds without technical background. Signal: 2-3 audit people known to the owner read only the top section and each restates the value correctly in one sentence (milestone 1 passes at 2 of 3).
- **O2**: A data scientist finds every claim credible and reproducible. Signal: one command reproduces every number on the page from a fresh clone; CI is green; every SQL-vs-Cypher round has a test proving both return the same answer; the page makes no claim without a test or a cited method.
- **O3**: It shows, and measures, the realistic hard part: reconciling ERM's and IA's separate risk taxonomies, risks and controls into one framework (ERM's Basel-style taxonomy). Signal: precision and recall of the reconciliation against the generator's answer key are published on the page, and low-confidence matches go to a human review queue rather than being merged silently.
- **O4**: An audit team can adapt it to their own data. Signal: someone following only the README loads a differently shaped dataset and runs the planning queries in under an hour.
- **O5** (tracked): The project starts hiring conversations. Signal: 3 conversations or interview invitations that mention the project within 6 months of publishing.

## Current milestone
**M1: messy -> reconciled -> graph -> insights.** A synthetic US regional bank (about $60B in assets) with separate ERM and IA populations, two taxonomies (L1-L4 risk), the audit universe of auditable entities, and 3 years of audits and issues. A reconciliation pipeline with measured accuracy. SQLite and Neo4j loaders. Seven head-to-head planning rounds with SQL/Cypher agreement tests. CI. Page v1 (a CAE layer, the rounds, an operating model with pros/cons, keys for success and maintenance, and a technical appendix), published on GitHub Pages.

Done when: the page is live; CI is green, including the agreement tests; reconciliation precision and recall are on the page; 2 of 3 readers pass the O1 test. No deadline.

Riskiest assumption: that the synthetic bank data reads as real to audit professionals. Tested first: E1's first change is a sample pack (about 15 rows per entity, both taxonomies, hard duplicates, templated vs AI-written text side by side) that the owner reviews before the full generator is built.

Next milestones (parked until M1 is done): **M2**, the unstructured layer (workpapers, RCMs, audit reports, vector store, document-to-graph links, pre-recorded GraphRAG examples), plus a scaling benchmark and centrality analysis. **M3**, the template kit (import templates, query library, a test run on a differently shaped dataset).

## Non-goals
- Not a GRC replacement: the graph is an analysis layer over a system of record.
- No real data, ever, and no fictional institution whose name or branding resembles a real one.
- No hosted live database for visitors: the page shows precomputed results that anyone can reproduce locally.
- No performance claims at demo scale; speed is claimed only where the benchmark shows it. No vendor endorsement.
- No automated risk scoring or audit plan: the graph informs auditor judgment, it does not replace it.
- No live GraphRAG chat (parked): document Q&A is retrieval plus pre-recorded examples.

## Constraints
- Own public repo with its own GitHub Pages site; the risk-analytics-portfolio links to it.
- Python 3.12, SQLite, Neo4j 5 Community (Neo4j Desktop locally, a service container in CI).
- Approved packages: `neo4j`, `networkx`, `scikit-learn`, `pandas`, `anthropic`. Anything else needs the owner's OK.
- API keys come from `~/.claude/secrets.yaml` at runtime. CI jobs on pull requests never use secrets.
- Synthetic data is seeded and deterministic. AI-generated text is generated once and committed; builds never call an API.
- No deadline. AI text generation cost: a few dollars, approved.
