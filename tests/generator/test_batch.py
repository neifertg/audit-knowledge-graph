"""Child f (010): the full-size AI-text batch, tested offline with a fake client (no network, no cost).

The Message Batches API is the one external boundary these tests replace; everything else is real.
"""
import json
import random
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from src.features.generator import batch_text as bt
from src.features.generator.prompts import SAMPLE_PROMPT_HASH, prompt_hash

from .helpers import ROOT

_LOG = Path(bt.COST_LOG).read_text(encoding="utf-8")
EMPTY_LOG = _LOG[:_LOG.index("|---|")] + "|---|---|---|---|---|---|\n"  # header only, no rows
PER_ITEM = (bt.MEASURED_IN * bt.PRICE_IN + bt.MEASURED_OUT * bt.PRICE_OUT) * bt.MARGIN


def item(n: int, file: str = "risk_ia", draft: str = "A plain draft.", opening: str = "") -> bt.Item:
    return bt.Item(f"risk_ia:theme@entity-{n}", file, draft, "Title", "a voice", opening, f"hash{n}")


def items_costing(usd: float) -> list:
    return [item(n) for n in range(round(usd / PER_ITEM))]


class FakeError(Exception):
    def __init__(self, status_code):
        super().__init__(f"HTTP {status_code}")
        self.status_code = status_code


class FakeBatches:
    def __init__(self, results=(), fail_with=None):
        self.created, self._results, self.fail_with = [], list(results), fail_with

    def create(self, requests):
        if self.fail_with:
            raise self.fail_with
        self.created.append(requests)
        return SimpleNamespace(id="msgbatch_fake1")

    def retrieve(self, batch_id):
        return SimpleNamespace(processing_status="ended")

    def results(self, batch_id):
        return iter(self._results)


class FakeClient:
    def __init__(self, **kwargs):
        self.messages = SimpleNamespace(batches=FakeBatches(**kwargs))


def succeeded(cid, text, stop="end_turn", tokens=(1000, 200)):
    message = SimpleNamespace(stop_reason=stop, usage=SimpleNamespace(input_tokens=tokens[0], output_tokens=tokens[1]),
                              content=[SimpleNamespace(type="text", text=text)])
    return SimpleNamespace(custom_id=cid, result=SimpleNamespace(type="succeeded", message=message))


def failed(cid, kind):
    return SimpleNamespace(custom_id=cid, result=SimpleNamespace(type=kind))


class BatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="akg-batch-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.log = self.tmp / "cost_log.md"
        self.log.write_text(EMPTY_LOG, encoding="utf-8")
        self.batches = self.tmp / "batches"
        self.calls = 0

    def factory(self, client=None):
        def make():
            self.calls += 1  # secrets.yaml is read only inside a real factory; never before the budget check
            return client or FakeClient()
        return make

    def add_row(self, line: str):
        with open(self.log, "a", encoding="utf-8", newline="\n") as f:
            f.write(line + "\n")

    def submit(self, items, budget=10.0, client=None, **kwargs):
        return bt.submit(self.factory(client), items, budget, log=self.log, batch_dir=self.batches, **kwargs)

    # --- AC-1 -------------------------------------------------------------------------------
    def test_ac1_over_budget_refused_before_any_client(self):
        five = items_costing(5.0)
        for label, row in (("submitted", "| msgbatch_a | risk_ia | 1 | 6.0000 |  | submitted |"),
                           ("collected", "| msgbatch_b | risk_ia | 1 | 4.0000 | 6.0000 | collected |"),
                           ("submitting", "| pending-x | risk_ia | 1 | 6.0000 |  | submitting |")):
            with self.subTest(row=label):
                self.log.write_text(EMPTY_LOG, encoding="utf-8")
                self.add_row(row)
                with self.assertRaises(bt.BudgetError):
                    self.submit(five)
                self.assertEqual(self.calls, 0, "no client (and no secrets) before the budget check")
        self.log.write_text(EMPTY_LOG, encoding="utf-8")
        self.add_row("| msgbatch_c | risk_ia | 1 | 6.0000 |  | rejected |")
        self.assertEqual(self.submit(five), "msgbatch_fake1", "a rejected batch costs nothing")
        for label, row in (("unparseable", "| msgbatch_d | risk_ia | one | 6.0 |  | submitted |"),
                           ("unknown status", "| msgbatch_e | risk_ia | 1 | 0.1000 |  | done |")):
            with self.subTest(row=label):
                self.log.write_text(EMPTY_LOG, encoding="utf-8")
                self.add_row(row)
                with self.assertRaises(bt.BudgetError):
                    self.submit(items_costing(0.1))
        self.log.unlink()
        with self.assertRaises(bt.BudgetError):
            self.submit(items_costing(0.1))

    def test_ac1_submission_and_collection_log_cost(self):
        items = [item(n) for n in range(3)]
        rows = lambda: bt.parse_log(self.log)[1]
        client = FakeClient(results=[succeeded(bt.custom_id(i.key), f"Plain rewrite number {n}.", tokens=(1000, 200))
                                     for n, i in enumerate(items)])
        batch_id = self.submit(items, client=client)
        self.assertEqual([(r.batch_id, r.status) for r in rows()], [(batch_id, "submitted")])
        self.assertAlmostEqual(rows()[0].estimated, 3 * PER_ITEM, places=3)  # the log stores 4 decimals
        outcome = bt.collect(lambda: client, batch_id, items, self.tmp / "text.jsonl", log=self.log,
                             batch_dir=self.batches)
        self.assertEqual(outcome["failures"], {})
        self.assertEqual(rows()[0].status, "collected")
        self.assertAlmostEqual(rows()[0].actual, 3 * (1000 * bt.PRICE_IN + 200 * bt.PRICE_OUT), places=3)  # the log stores 4 decimals
        # a definite rejection is logged at $0; an ambiguous failure stays `submitting` (counts as spend)
        for status, expected in ((400, "rejected"), (500, "submitting")):
            with self.subTest(status=status):
                self.log.write_text(EMPTY_LOG, encoding="utf-8")
                with self.assertRaises(FakeError):
                    self.submit(items, client=FakeClient(fail_with=FakeError(status)))
                self.assertEqual(rows()[-1].status, expected)

    # --- AC-2 -------------------------------------------------------------------------------
    def test_ac2_results_matched_by_custom_id_not_order(self):
        items = [item(n) for n in range(6)]
        ids = [bt.custom_id(i.key) for i in items]
        self.assertEqual(len(set(ids)), len(ids))
        for cid in ids:
            self.assertRegex(cid, r"^[a-zA-Z0-9_-]{1,64}$")
        params = bt.request(items[0], bt.MAX_TOKENS)["params"]
        for forbidden in ("fallbacks", "stream", "speed"):
            self.assertNotIn(forbidden, params, f"the Batches API rejects {forbidden}")
        results = [succeeded(ids[0], "Rewrite zero."), succeeded(ids[1], "Rewrite one."),
                   failed(ids[2], "errored"), failed(ids[3], "expired"), failed(ids[4], "canceled"),
                   succeeded(ids[5], "Cut off", stop="max_tokens"), succeeded("kunknown", "Stray.")]
        random.Random(7).shuffle(results)
        client = FakeClient(results=results)
        batch_id = self.submit(items, client=client)
        text = self.tmp / "text.jsonl"
        outcome = bt.collect(lambda: client, batch_id, items, text, log=self.log, batch_dir=self.batches)
        stored = bt.load_text(text)
        self.assertEqual(stored[items[0].key]["text"], "Rewrite zero.")
        self.assertEqual(stored[items[1].key]["text"], "Rewrite one.")
        self.assertEqual(outcome["unknown"], ["kunknown"])
        for n, reason in ((2, "errored"), (3, "expired"), (4, "canceled"), (5, "max_tokens")):
            self.assertIn(reason, outcome["failures"][items[n].key])
        refused = [item(9)]
        client = FakeClient(results=[succeeded(bt.custom_id(refused[0].key), "x", stop="refusal")])
        self.log.write_text(EMPTY_LOG, encoding="utf-8")
        batch_id = self.submit(refused, client=client)
        outcome = bt.collect(lambda: client, batch_id, refused, text, log=self.log, batch_dir=self.batches)
        self.assertIn("refusal", outcome["failures"][refused[0].key])
        # a request with no result at all is reported by name
        missing = [item(20), item(21)]
        client = FakeClient(results=[succeeded(bt.custom_id(missing[0].key), "Only one.")])
        self.log.write_text(EMPTY_LOG, encoding="utf-8")
        batch_id = self.submit(missing, client=client)
        outcome = bt.collect(lambda: client, batch_id, missing, text, log=self.log, batch_dir=self.batches)
        self.assertEqual(outcome["missing"], [missing[1].key])

    # --- AC-3 -------------------------------------------------------------------------------
    def test_ac3_capitalized_words_allow_bank_names_only(self):
        from src.features.generator.text_rules import stray_capitals
        allowed = ("The audit of Cash Management & Vault covers counts.",   # the bank's auditable entity
                   "Reviewed by the Front Office team.",                       # a word in the item's own draft
                   "Limits are Board-approved and reviewed in March.",         # compound of an allowed word; a month
                   "Exceptions list the customer IDs.")
        for text in allowed:
            with self.subTest(text=text):
                self.assertEqual(stray_capitals(text, draft="The Front Office reviews it."), [])
        self.assertEqual(stray_capitals("Reviewed by the Zorblat team.", draft="The Front Office reviews it."),
                         ["Zorblat"])

    def test_ac3_rules_resubmit_once_then_block(self):
        cases = [
            (item(1, draft="Wires are confirmed by callback."), "Wires in Brisance Wire Manager are confirmed.",
             "systems"),
            (item(2, file="control_erm", draft="Approvals are checked."),
             "Approvals are checked. A second sentence follows.", "one sentence"),
            (item(3, file="control_erm", draft="Approvals are checked."), " ".join(["word"] * 31) + ".",
             "30 words"),
            (item(4, file="issue", draft="Testing found that x.", opening="Testing found that"),
             "We found that x.", "begin with"),
            (item(5, draft="A plain draft."), "This mirrors practice at KeyBank today.", "real institution"),
            (item(6, draft="A plain draft."), "Reviewed by the Zorblat team monthly.", "capitalized"),
        ]
        items = [c[0] for c in cases]
        client = FakeClient(results=[succeeded(bt.custom_id(i.key), text) for i, text, _ in cases])
        batch_id = self.submit(items, client=client)
        outcome = bt.collect(lambda: client, batch_id, items, self.tmp / "text.jsonl", log=self.log,
                             batch_dir=self.batches)
        for i, _, reason in cases:
            with self.subTest(rule=reason):
                self.assertIn(reason, outcome["failures"][i.key])
        self.assertEqual(bt.load_text(self.tmp / "text.jsonl"), {}, "nothing failing is stored")
        retry, blocked = bt.failures_to_retry(self.batches)
        self.assertEqual(set(retry), {i.key for i in items})
        self.assertEqual(blocked, {})
        # the resubmission is priced at its worst case and uses the higher cap
        client = FakeClient(results=[succeeded(bt.custom_id(i.key), "Still We found nothing.") for i in items])
        retry_id = "msgbatch_fake1"
        bt.submit(lambda: client, items, 10.0, attempt=2, notes={i.key: "fix it" for i in items}, log=self.log,
                  batch_dir=self.batches)
        sent = client.messages.batches.created[-1]
        self.assertTrue(all(r["params"]["max_tokens"] == bt.RETRY_MAX_TOKENS for r in sent))
        self.assertIn("fix it", sent[0]["params"]["messages"][0]["content"])
        last = bt.parse_log(self.log)[1][-1]
        self.assertAlmostEqual(last.estimated, sum(bt.estimate(items, bt.RETRY_MAX_TOKENS).values()), places=3)  # the log stores 4 decimals
        bt.collect(lambda: client, retry_id, items, self.tmp / "text.jsonl", log=self.log, batch_dir=self.batches)
        retry, blocked = bt.failures_to_retry(self.batches)
        self.assertEqual(retry, {}, "an item is resubmitted once only")
        self.assertTrue(blocked, "items failing twice are blocked for the owner")

    # --- AC-6 -------------------------------------------------------------------------------
    def test_ac6_tests_never_import_anthropic(self):
        code = ("import sys, unittest\n"
                "suite = unittest.defaultTestLoader.loadTestsFromNames(["
                "'tests.generator.test_batch.BatchTests.test_ac1_over_budget_refused_before_any_client',"
                "'tests.generator.test_batch.BatchTests.test_ac1_submission_and_collection_log_cost',"
                "'tests.generator.test_batch.BatchTests.test_ac2_results_matched_by_custom_id_not_order',"
                "'tests.generator.test_batch.BatchTests.test_ac3_rules_resubmit_once_then_block'])\n"
                "result = unittest.TextTestRunner(stream=open('nul' if sys.platform == 'win32' else '/dev/null', 'w'))"
                ".run(suite)\n"
                "sys.exit(3 if 'anthropic' in sys.modules else (0 if result.wasSuccessful() else 1))\n")
        result = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, "the batch tests failed or imported anthropic")

    def test_sample_prompt_is_pinned(self):
        self.assertEqual(prompt_hash(full=False), SAMPLE_PROMPT_HASH,
                         "the sample prompt changed; the committed sample text was written with the pinned one")
        self.assertNotEqual(prompt_hash(full=True), SAMPLE_PROMPT_HASH)


if __name__ == "__main__":
    unittest.main()
