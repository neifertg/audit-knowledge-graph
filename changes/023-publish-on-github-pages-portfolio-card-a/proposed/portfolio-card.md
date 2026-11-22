### Audit Knowledge Graph

**Planning.** Risk that lives between tables: shared systems, repeat findings, concentrated ownership.

**Problem.** ERM and Internal Audit keep separate risk and control records, in different words, so exposure that crosses them goes unseen in audit planning.

**What it does.** It reconciles the two into one framework, connects them as a graph beside a SQL database, and asks the same planning questions of both.

**Why it's trustworthy.** Every answer is checked against the other engine and an independent computation, and against the scenario planted in the synthetic data where one was planted; the page says where the graph helped, where SQL did, and where they came out close.

<details>
<summary>Under the hood</summary>
<p>A synthetic regional bank, generated with two separate risk taxonomies, reconciled with a measured matcher and a human review queue, and loaded into SQLite and Neo4j with a parity test. Every figure on the page is rendered from committed results and checked by the test suite, which runs against a real Neo4j on every push.</p>
</details>

[The page](https://neifertg.github.io/audit-knowledge-graph/)
· [Source and tests](https://github.com/neifertg/audit-knowledge-graph)
