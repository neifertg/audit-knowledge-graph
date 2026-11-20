# Research: R2 synthetic text realism

Objective: O1 (also O3)
Question: Do templated or AI-written (Anthropic SDK, generated once and committed) risk, control and issue descriptions read as real to the owner? Answered through the sample pack (E1 child a), which shows both side by side.
Timebox: half a day. Past this, decide with what you have. Cost approved: a few dollars.

## Findings
- Owner review of `sample_pack.md` (change 005), 2026-11-20: every entity type marked realistic (segment, business_unit, auditable_entity, process, system, person, regulation, taxonomy_node_erm, taxonomy_node_ia, risk_erm, risk_ia, control_erm, control_ia, audit, issue). Name lists accepted (INV-9 one-time review).
- Owner: both text variants "look good"; the choice was delegated to the builder.
- Templated text repeats fixed frames in every row ("Risk that ... due to ..., resulting in ...", "Review scope: ..."). Real registers do not, and the frames are a cue a matcher could exploit, which would flatter E2's precision and recall.
- AI text (claude-opus-5-5, low effort) needed guarding: unguarded, it added system names absent from the draft and expanded brief ERM controls, which erased hard negatives (lesson L-002). With the prompt rule plus a code check and retry (`write_text.added_systems`, tested in AC-4), all 75 sample items keep their draft's facts and pass AC-2, AC-4 and AC-7.
- Cost: the 75-item sample cost well under a dollar. Full size (about 1,300 descriptions across risks, controls and issues) is estimated at roughly $10-15, above this item's "few dollars" approval.

## Decision
Decision: GO
Why: The owner found every entity type realistic. AI-written descriptions are chosen: they read like records written by different people, avoid the repeated frames that would make reconciliation artificially easy, and are guarded and committed, so the build stays offline and deterministic. Templated text remains available (`--text templated`) as a fallback.
Next: Child b (E1) switches the build default to `--text ai` and regenerates the golden checksums. Before children c-e generate full-size AI text, the owner approves the estimated $10-15 cost (or picks a cheaper model or keeps templated text for some files). Parked review findings for c-e apply (positional issue keys; matched controls sharing all attributes).
