"""E3 child e (019): the CI workflow, the README and CI doc, and the CI environment in test subprocesses.

The workflow is read as text: pyyaml is approved only for one-off secrets scripts.
"""
import os
import re
import unittest
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

    def test_ac5_ci_environment_reaches_no_test_subprocess(self):
        ci_env = {"NEO4J_URI": "bolt://localhost:7687", "NEO4J_USER": "neo4j", "NEO4J_PASSWORD": "x",
                  "AKG_REQUIRE_NEO4J": "1"}
        with mock.patch.dict(os.environ, ci_env):
            stripped, kept = akg_env(), akg_env(neo4j=True)
        for name in ci_env:
            self.assertNotIn(name, stripped, name)
            self.assertEqual(kept[name], ci_env[name], name)
