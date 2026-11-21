VERDICT: READY

Previous critique: all seven items are answered.
- (1, major) There is now a measured verdict beside the expected one, the page publishes the measured verdict and says where the two differ, and round 6 is "close".
- (2) Round 5 opens the overlay with an explicit `BEGIN` and has a before/after test of counts and INV-8 parity.
- (3) Owner concentration has its path, ranking and tie rule, and is marked as derived, not planted.
- (4) E4's overlap is acknowledged, but E4 has not been changed yet (see 1).
- (5) The lock has a 10-minute staleness rule and is excluded from parity.
- (6) The export carries the seed, the reconciled-golden checksum and the weights fingerprint.
- (7) Round 2 dates "tested" by the audit's end date, and round 7's top riser is the largest absolute increase. Round 5's vendor and overlay are deferred to d's plan.

The issues left are minor and belong in the child plans. None blocks the epic contract.

1. [minor] The E4 follow-up exists only as a sentence in this epic. The epic says "E4 needs a matching revision" twice: once because owner concentration is derived, and once because child e creates the repo. `changes/004-e4-page-v1-and-publish/epic.md` still says "the three planted stories (... owner concentration)" (child a) and "create the public GitHub repo and Pages site" (child c). Nothing in ROADMAP's parking lot tracks this. -> Before approving, either edit E4 now (it is still a draft) or `capitan park` the follow-up, so the page does not end up calling a derived finding "planted".
2. [minor] Round 5 can pass with an empty answer. Agreement and the oracle both hold when both stores return no newly exposed entities, and the overlay is generated, not planted. -> d's plan should require at least one entity that is newly exposed only through fourth parties for the pinned vendor at seed 42, and that a known direct-only entity is excluded from the "new" set.
3. [minor] Round 5's "directly through its systems" path is still open. It could be process -> runs_on -> system, control -> depends_on -> system, or both. The epic defers only "the vendor asked about and the overlay's construction" to d's plan. -> Add the direct-exposure path to what d's plan pins.
4. [minor] The overlay transaction in Neo4j has a trap. Neo4j 5 refuses a schema change (a constraint or index) and data writes in one transaction. If d's overlay adds a constraint on a new label, the rolled-back-transaction design fails. -> d's plan should state that the overlay adds no schema in Neo4j, or that it handles schema outside the transaction with explicit cleanup, which the before/after test then covers.
5. [minor] The lock protects loading, not a test run. "Two test runs must not share one local server at the same time" is a rule, but the lock is released once loading ends. A second run can then clear and reload the shared fixture while the first is still querying it, and the first run fails in a way that is hard to diagnose. -> b's plan should either keep the lock for the whole test run (refreshing its timestamp so the 10-minute staleness does not expire it) or say plainly that concurrent local runs are unsupported. CI is unaffected because it runs one job per container.
6. [minor] The measured-verdict rule is pinned in c's plan but also scores d's rounds 5-7 and E4's page. -> c's plan should write the rule down as a function with its own test (given lines of code, joins or hops and moving parts, it returns a verdict), so d can reuse it without changing it.

Not checked: CI's reliability and wall time with the Neo4j service container (unknown until child e runs); whether a seeded fourth-party overlay over the existing vendors yields any newly exposed entities (see 2); the timebox of about 6 days, which looks plausible. The seed-42 facts from the previous critique (round 2's containment, round 6 matching exactly, round 7's riser being ERMT-679) were not re-run, because the rules they depend on did not change in a way that affects them.
