# O1 reader test: script

GOALS' signal for O1: audit people the owner knows read only the top section of the page and restate its value correctly in one sentence. M1 passes at 2 of 3. This script and its pass rule were written before any answer (change 023).

## Who and how many
Send it to three readers: audit people the owner knows (a CAE, an audit manager, an audit analytics lead, or similar). Record each by role only, never by name.

## What to send
> Could you give me a minute on something? Please open https://neifertg.github.io/audit-knowledge-graph/ and read only the top section, stopping at the heading "The rounds". Then reply with one sentence: **In one sentence, what does this show, and why would an audit leader care?**

Do not explain the page first, and do not prompt with the words on it. Record the reply exactly as written.

## The pass rule (fixed before any answer)
A sentence passes when it says **both**:
- **(a)** that records from two teams or systems are connected or reconciled (ERM and Internal Audit, or risk and control records, or tables), or that risk is found across them; **and**
- **(b)** a planning benefit: finding shared-system exposure, repeat findings, concentrated ownership, or better audit coverage or planning.

Wording does not need the terms ERM, IA or graph. A sentence that says only what the tool is (a) or only that it helps (b) does not pass.

### Worked examples
- Passes: "It joins up the risk register and the audit team's control records so you can see where one system failure hits lots of business units, which tells an audit leader where to focus coverage."
- Passes: "It connects risk and audit data that usually sit in separate tables, so repeat findings and over-reliance on a few control owners show up before planning, not after."
- Fails: "It's a graph database demo comparing SQL and Cypher." (no planning benefit, and nothing about connecting the two teams' records)
- Fails: "It helps auditors plan better." (a benefit, but nothing about what it connects or finds across records)

## Judging
The owner and the agent each judge every answer against the rule above, **independently**, before comparing. Where they differ, **the stricter reading** stands (the answer fails). Both judgments and the reason are recorded in `results.md`. If fewer than 2 of 3 pass, the epic's path applies: revise the top section in a small change, re-test with readers who have not seen the page, and after a second miss the owner decides.
