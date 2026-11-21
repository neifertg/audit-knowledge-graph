"""Prompts for AI-written descriptions, shared by the sample script and the full-size batch.

The sample text was written with SAMPLE prompt; its stored hashes do not include a prompt
version, so a test pins SAMPLE_PROMPT_HASH to catch any edit that would silently change it.
Full-size text adds one instruction (issue openings) and stores the full prompt version in each
input hash, so text from two prompt versions is detected as stale (010).

Note: the prompt lists every system name and allowed term, so editing those name lists changes
the full prompt version and makes all full-size text stale (a paid regeneration).
"""
import hashlib

from .names import load

MODEL = "claude-opus-5-5"
SAMPLE_PROMPT_HASH = "600f6ca9a07105e1"  # the prompt the committed sample text was written with

VOICE = {
    "risk_erm": "an ERM risk register (RCSA) risk statement: one or two sentences in cause, event, impact form",
    "risk_ia": "an Internal Audit universe entry: one or two sentences naming the risk area and what the audit "
               "of it covers",
    "control_erm": "an ERM RCSA control description: one short, high-level sentence written by the business, "
                   "with no step-by-step detail",
    "control_ia": "an Internal Audit risk and control matrix (RCM) control description: two to four sentences "
                  "saying who performs it, what they do, when, and what evidence is kept",
    "issue": "an issue description recorded by {source}: one to three sentences stating the condition found",
}

OPENING_RULE = ("- For issue descriptions: begin with exactly the opening words given as 'Opening', then continue "
                "in your own words.\n")


def system_prompt(full: bool = False) -> str:
    proper = ", ".join(load("systems") + load("allow_terms"))
    return (
        "You write record text for a fictional US regional bank's risk and audit data. Rewrite the draft "
        "you are given so it reads like a real record written by the stated author.\n"
        "Rules:\n"
        "- Keep every fact in the draft: numbers, thresholds, systems, roles and timeframes. You may reword, "
        "reorder and add plausible operational detail.\n"
        "- Add no new names of people, companies, vendors, products, systems, laws or places. Mention a "
        "system only if the draft names it.\n"
        f"- The only capitalized terms you may use, other than the first word of a sentence, are: {proper}.\n"
        "- Do not reuse any full sentence from the draft.\n"
        + (OPENING_RULE if full else "")
        + "- Plain prose only: no headings, lists, quotation marks or preamble. Reply with the rewritten text "
        "and nothing else."
    )


def prompt_hash(full: bool) -> str:
    material = system_prompt(full) + "\x1f" + "\x1f".join(f"{k}={v}" for k, v in sorted(VOICE.items()))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


def full_prompt_version() -> str:
    return prompt_hash(full=True)


# 010 revision 1: an ERM duplicate is the same risk re-entered by another team, so its AI text is
# rewritten from its original's AI text (per-item note; the system prompt is unchanged).
DUPLICATE_NOTE = ("This is the same risk entered again in another team's register, copied from the original "
                  "team's statement in the draft above and then edited. Keep the original's final (impact) "
                  "sentence almost word for word, as a team copying a register entry would, but write the cause "
                  "and the event in this team's own words. This team's own wording of the cause: {own_draft}")


def duplicate_note(own_draft: str) -> str:
    return DUPLICATE_NOTE.format(own_draft=own_draft)
