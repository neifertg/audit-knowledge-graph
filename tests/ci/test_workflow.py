"""E3 child e (019): the CI workflow, the README and CI doc, and the CI environment in test subprocesses.

The workflow is read as text: pyyaml is approved only for one-off secrets scripts.
"""
import os
import re
import unittest
from pathlib import Path
from unittest import mock

from tests.generator.helpers import ROOT, akg_env

WORKFLOW = ROOT / ".github" / "workflows" / "tests.yml"


class WorkflowTests(unittest.TestCase):
    def test_ac2_workflow_runs_every_test_with_a_real_neo4j(self):
        self.assertTrue(WORKFLOW.exists(), "the owner commits .github/workflows/tests.yml in block B1")
        text = WORKFLOW.read_text(encoding="utf-8")
        triggers = text.split("\npermissions:")[0]
        self.assertRegex(triggers, r"\n  push:")
        self.assertRegex(triggers, r"\n  pull_request:")
        self.assertIn("runs-on: ubuntu-latest", text)
        self.assertRegex(text, r'python-version: "3\.12"')
        self.assertIn("pip install -r requirements.txt", text)
        self.assertIn("image: neo4j:5.26.33-community", text)
        self.assertIn("--health-cmd", text)
        self.assertIn("cypher-shell", text)
        self.assertIn("NEO4J_server_memory_heap_max__size: 1G", text)
        self.assertIn("NEO4J_server_memory_pagecache_size: 512m", text)
        self.assertIn("verify_connectivity", text)
        self.assertIn("last error", text)
        for name in ("NEO4J_URI: bolt://localhost:7687", "NEO4J_USER: neo4j", "NEO4J_PASSWORD:"):
            self.assertIn(name, text)
        self.assertIn('AKG_REQUIRE_NEO4J: "1"', text)
        self.assertNotIn("secrets.", text, "CI never uses secrets")
        self.assertRegex(text, r"permissions:\n  contents: read")
        self.assertRegex(text, r"timeout-minutes: \d+")
        self.assertIn("concurrency:", text)
        self.assertIn("python -m unittest discover -s tests", text)
        self.assertIn("set -o pipefail", text)
        self.assertIn(r'grep -qE "^(OK|FAILED) \(.*skipped=[0-9]+"', text, "the skip guard reads the summary line")
        # the job-local password in the service matches the one the tests use
        password = re.search(r"NEO4J_PASSWORD: (\S+)", text).group(1)
        self.assertIn(f"NEO4J_AUTH: neo4j/{password}", text)

    def test_ac4_readme_ci_doc_and_gitignore(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        ci = (ROOT / "docs" / "ci.md").read_text(encoding="utf-8")
        for phrase in ("pip install -r requirements.txt", "python -m akg build", "python -m unittest discover -s tests",
                       "with_neo4j", "actions/workflows/tests.yml/badge.svg", "docs/ci.md"):
            self.assertIn(phrase, readme, phrase)
        for phrase in ("neo4j:5.26.33-community", "readiness", "AKG_REQUIRE_NEO4J", "skipped", "secrets",
                       "First run", "wall time", "reproduce"):
            self.assertIn(phrase, ci, phrase)
        # The first green run's URL and wall time are recorded in "First run" after that run (AC-3, checked in
        # review): a test inside CI cannot require the URL of the run it is part of.
        self.assertIn("## First run", ci)
        ignored = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertIn("data/", [line.strip() for line in ignored])

    # ---------------- 023: the Pages workflow, the reader test, the docs ----------------

    def test_ac2_023_pages_workflow_deploys_only_current_tested_head(self):
        pages = ROOT / ".github" / "workflows" / "pages.yml"
        # re-pointed in 024 to its guard-fix draft (docs/pages.md, 'Changing the workflow later')
        proposed = ROOT / "changes" / "024-live-check-portfolio-card-and-the-o1-rea" / "proposed" / "pages.yml"
        self.assertTrue(pages.exists(), "the owner commits .github/workflows/pages.yml in block B1")
        self.assertEqual(pages.read_bytes(), proposed.read_bytes(), "the committed workflow is the reviewed draft")
        lines = [line.rstrip() for line in pages.read_text(encoding="utf-8").splitlines()
                 if line.strip() and not line.strip().startswith("#")]
        code = "\n".join(lines)
        for line in ("  workflow_run:", "    workflows: [tests]", "    types: [completed]", "    branches: [main]",
                     "    if: github.event.workflow_run.conclusion == 'success' && github.event.workflow_run.event == 'push'",
                     "    needs: guard", "    if: needs.guard.outputs.current == 'true'",
                     "          ref: ${{ github.event.workflow_run.head_sha }}",
                     "        run: python -m src.features.site.build --out _site",
                     "      - uses: actions/configure-pages@v6", "      - uses: actions/upload-pages-artifact@v5",
                     "        uses: actions/deploy-pages@v5", "      pages: write", "      id-token: write",
                     "      name: github-pages", "  group: pages", "  cancel-in-progress: false"):
            self.assertIn(line, lines, line)
        # the guard compares the tested commit with main's current head, and only the deploy job has an environment
        self.assertRegex(code, r'head=\$\(git ls-remote "https://github\.com/\$\{\{ github\.repository \}\}" refs/heads/main')
        self.assertIn('if [ "$head" = "${{ github.event.workflow_run.head_sha }}" ]; then', code)
        self.assertEqual(code.count("environment:"), 1)
        guard = code.split("  guard:")[1].split("  deploy:")[0]
        self.assertNotIn("environment:", guard)
        self.assertNotIn("pip install", code)
        self.assertNotIn("secrets.", code)

    def test_ac3_023_reader_test_prepared(self):
        folder = ROOT / "research" / "o1-reader-test"
        script = (folder / "script.md").read_text(encoding="utf-8")
        results = (folder / "results.md").read_text(encoding="utf-8")
        self.assertTrue((folder / "decision.md").exists(), "started with capitan research")
        for phrase in ("https://neifertg.github.io/audit-knowledge-graph/", "The rounds",
                       "In one sentence, what does this show, and why would an audit leader care?",
                       "three readers", "(a)", "(b)", "stricter reading", "independently",
                       "Passes:", "Fails:"):
            self.assertIn(phrase, script, phrase)
        self.assertEqual(script.count("Passes:"), 2)
        self.assertEqual(script.count("Fails:"), 2)
        for field in ("Reader A", "Reader B", "Reader C", "Role", "Date", "Sentence", "Owner's judgment",
                      "Agent's judgment", "Result", "Reason"):
            self.assertIn(field, results, field)

    def test_ac4_023_pages_docs(self):
        pages = (ROOT / "docs" / "pages.md").read_text(encoding="utf-8")
        for phrase in ("python -m src.features.site.build", "workflow_run", "main's head", "build_type=workflow",
                       "## Live check", "byte for byte", "proposed/pages.yml", "refused"):
            self.assertIn(phrase, pages, phrase)
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("https://neifertg.github.io/audit-knowledge-graph/", readme)
        self.assertIn("docs/pages.md", readme)
        self.assertIn("pages.yml", (ROOT / "src" / "features" / "site" / "README.md").read_text(encoding="utf-8"))

    # ---------------- 024: the guard fix, the card draft, the reader record, the live check ----------------

    def test_ac1_024_guard_fix_is_the_only_difference(self):
        old = (ROOT / "changes" / "023-publish-on-github-pages-portfolio-card-a" / "proposed" / "pages.yml").read_text(encoding="utf-8")
        new = (ROOT / "changes" / "024-live-check-portfolio-card-and-the-o1-rea" / "proposed" / "pages.yml").read_text(encoding="utf-8")
        import difflib
        diff = list(difflib.ndiff(old.splitlines(), new.splitlines()))
        added = [l[2:] for l in diff if l.startswith("+ ")]
        removed = [l[2:] for l in diff if l.startswith("- ")]
        # every changed line, in order: the header, the guard fix, and the deploy retry (024 revision)
        self.assertEqual(removed, ["# Publish the page on GitHub Pages (E4 child c, change 023).",
                                   "      url: ${{ steps.deployment.outputs.page_url }}"])
        self.assertEqual(added, ["# Publish the page on GitHub Pages (E4 child c, change 023; guard fix in E4 child d, change 024).",
                                 '          if [ -z "$head" ]; then',
                                 "            echo \"::error::could not read main's head; refusing to deploy\"",
                                 "            exit 1",
                                 "          fi",
                                 "      url: ${{ steps.retry.outputs.page_url || steps.deployment.outputs.page_url }}",
                                 "      # deploy-pages has twice failed to see the artifact uploaded seconds before, then succeeded on a re-run;",
                                 "      # wait and deploy once more in the same job before failing the run (change 024)",
                                 "        continue-on-error: true",
                                 "",
                                 "      - name: Wait before retrying the deploy",
                                 "        if: steps.deployment.outcome == 'failure'",
                                 "        run: sleep 30",
                                 "",
                                 "      - id: retry",
                                 "        if: steps.deployment.outcome == 'failure'",
                                 "        uses: actions/deploy-pages@v5"])

    def test_ac1_024_deploy_retry(self):
        text = (ROOT / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")
        lines = [l.rstrip() for l in text.splitlines() if l.strip() and not l.strip().startswith("#")]
        deploy = "\n".join(lines).split("  deploy:", 1)[1]
        steps = deploy.split("      - ")
        first = next(s for s in steps if s.startswith("id: deployment"))
        wait = next(s for s in steps if s.startswith("name: Wait before retrying the deploy"))
        retry = next(s for s in steps if s.startswith("id: retry"))
        self.assertIn("uses: actions/deploy-pages@v5", first)
        self.assertIn("continue-on-error: true", first)
        for step in (wait, retry):
            self.assertIn("if: steps.deployment.outcome == 'failure'", step)
            self.assertNotIn("continue-on-error", step)          # a failed retry fails the job
        self.assertIn("run: sleep 30", wait)
        self.assertIn("uses: actions/deploy-pages@v5", retry)
        self.assertLess(deploy.index("id: deployment"), deploy.index("Wait before retrying"))
        self.assertLess(deploy.index("Wait before retrying"), deploy.index("id: retry"))
        self.assertIn("      url: ${{ steps.retry.outputs.page_url || steps.deployment.outputs.page_url }}", lines)

    @staticmethod
    def _bash() -> str:
        """bash for the guard's behaviour test: PATH (not the System32 WSL launcher), else Git for Windows'."""
        import shutil
        import subprocess
        found = shutil.which("bash")
        if found and "system32" not in found.lower():
            return found
        exec_path = subprocess.run(["git", "--exec-path"], capture_output=True, text=True).stdout.strip()
        for candidate in (Path(exec_path).parents[2] / "bin" / "bash.exe", Path(exec_path).parents[2] / "usr" / "bin" / "bash.exe"):
            if candidate.exists():
                return str(candidate)
        raise AssertionError("bash not found: install Git for Windows or put bash on PATH (this test never skips)")

    def test_ac1_024_guard_fails_red_on_empty_lookup(self):
        import subprocess
        import tempfile
        text = (ROOT / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")
        block = text.split("        id: head\n        run: |\n", 1)[1]
        script = "\n".join(line[10:] for line in block.splitlines() if line.startswith("          "))
        script = (script.replace("${{ github.repository }}", "neifertg/audit-knowledge-graph")
                        .replace("${{ github.event.workflow_run.head_sha }}", "0" * 40))
        self.assertNotIn("${{", script)
        # a fake git that prints nothing: a shell function, which bash prefers over any git on PATH (on Windows,
        # Git's bash otherwise finds the real git)
        script = "git() { return 0; }\n" + script
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            run = subprocess.run([self._bash(), "-e", "-c", script], capture_output=True, text=True,
                                 env={**os.environ, "GITHUB_OUTPUT": str(out)})
        self.assertNotEqual(run.returncode, 0, "an empty lookup must fail the guard (red)")
        self.assertIn("::error::could not read main's head", run.stdout)

    def test_ac1_024_pages_docs(self):
        pages = (ROOT / "docs" / "pages.md").read_text(encoding="utf-8")
        self.assertIn("re-run **all** jobs", pages)
        self.assertIn("retries the deploy once after 30 seconds", pages)
        self.assertIn("changes/024-live-check-portfolio-card-and-the-o1-rea/proposed/pages.yml", pages)

    def test_ac2_024_portfolio_card_draft(self):
        card = (ROOT / "changes" / "023-publish-on-github-pages-portfolio-card-a" / "proposed" / "portfolio-card.md").read_text(encoding="utf-8")
        self.assertTrue(card.startswith("### Audit Knowledge Graph\n"))
        for part in ("**Planning.**", "**Problem.**", "**What it does.**", "**Why it's trustworthy.**",
                     "<summary>Under the hood</summary>", "(https://neifertg.github.io/audit-knowledge-graph/)",
                     "(https://github.com/neifertg/audit-knowledge-graph)"):
            self.assertIn(part, card, part)
        # no figure that can go stale: URLs and the product name Neo4j carry digits but are not figures
        self.assertIsNone(re.search(r"\d", re.sub(r"https?://\S+|\bNeo4j\b", "", card)), "the card holds no figure")

    def test_ac3_024_reader_record(self):
        from tests.generator.dictionary import denied_in, deny_entries
        folder = ROOT / "research" / "o1-reader-test"
        script = (folder / "script.md").read_text(encoding="utf-8")
        self.assertIn("published, without your name", script)
        self.assertIn("Redaction", script)
        results = (folder / "results.md").read_text(encoding="utf-8")
        self.assertEqual(denied_in(results, deny_entries()), [], "a real name in results.md")
        self.assertIsNone(re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", results), "an email address in results.md")

    def test_ac4_024_live_check_recorded(self):
        section = (ROOT / "docs" / "pages.md").read_text(encoding="utf-8").split("## Live check", 1)[1]
        self.assertRegex(section, r"\b[0-9a-f]{7,40}\b", "the commit")
        self.assertRegex(section, r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}", "the time")
        self.assertIn("byte for byte", section)
        for name in ("index.html", "site.css", "site.js", "site.json", "rounds.json", "scores.json"):
            self.assertIn(name, section, name)

    def test_ac5_ci_environment_reaches_no_test_subprocess(self):
        ci_env = {"NEO4J_URI": "bolt://localhost:7687", "NEO4J_USER": "neo4j", "NEO4J_PASSWORD": "x",
                  "AKG_REQUIRE_NEO4J": "1"}
        with mock.patch.dict(os.environ, ci_env):
            stripped, kept = akg_env(), akg_env(neo4j=True)
        for name in ci_env:
            self.assertNotIn(name, stripped, name)
            self.assertEqual(kept[name], ci_env[name], name)
