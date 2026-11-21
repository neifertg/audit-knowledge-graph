# AI text cost log (R2, E1 child f)

One row per Message Batch. The batch script reads this file before every submission and refuses a run when spend (actual cost where collected, the estimate for `submitting` and `submitted` rows, nothing for `rejected`) plus the new estimate exceeds the owner's budget ($10, approved 2026-11-20). A missing file, an unparseable row or an unknown status refuses the run.

If a submission's outcome is ambiguous (a crash or lost response leaves a `submitting` row): check the account's batches in the Anthropic Console. If the batch exists, replace `pending-...` with its ID and set the status to `submitted`, then collect it; if it does not exist, set the status to `rejected`. Only the owner makes that edit.

| batch_id | files | items | estimated_usd | actual_usd | status |
|---|---|---|---|---|---|
| msgbatch_01CPTdmg3kWqsNyc8z73sS1W | control_erm,control_ia,issue,risk_erm,risk_ia | 1274 | 6.2617 | 4.9137 | collected |
| msgbatch_011p1tuqcWxPQ384DWboLp61 | control_erm,control_ia,issue | 26 | 0.2845 | 0.0920 | collected |
| msgbatch_01HDJe9gWpwv3BL9p7gGzQ2G | risk_erm | 13 | 0.0639 | 0.0773 | collected |
| msgbatch_01W9xUuXhjrQi6nouv52bTkJ | risk_erm | 1 | 0.0109 | 0.0075 | collected |
| msgbatch_013zGF5hA4EbfwhnbfM9wCQ5 | risk_erm | 13 | 0.0639 | 0.0730 | collected |
| msgbatch_01DkLzzmPxfh7NLWKtAGBccW | risk_erm | 2 | 0.0219 | 0.0088 | collected |
| msgbatch_01GszppUJM9v4HBjid7hfaos | risk_erm | 13 | 0.0639 | 0.0813 | collected |
| msgbatch_016VP4mmYx5SUcg3en2WfNLm | risk_erm | 1 | 0.0109 | 0.0052 | collected |
