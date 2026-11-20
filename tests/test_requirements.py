"""AC-10: requirements.txt pins exactly, and only approved packages and their dependencies."""
import re
import unittest
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APPROVED = {"anthropic", "scikit-learn", "pandas", "neo4j", "networkx", "pyyaml"}
PIN = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)==([0-9][A-Za-z0-9.+!-]*)$")


def normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def requirement_name(spec: str) -> str | None:
    """Name of a Requires-Dist entry, or None when it applies only to an extra."""
    requirement, _, marker = spec.partition(";")
    if "extra" in marker:
        return None
    match = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)", requirement)
    return normalize(match.group(1)) if match else None


def dependency_closure(roots: set[str]) -> set[str]:
    """Every package reachable from `roots` through installed Requires-Dist metadata."""
    seen: set[str] = set()
    pending = [normalize(r) for r in roots]
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        seen.add(name)
        try:
            requires = metadata.requires(name) or []
        except metadata.PackageNotFoundError:
            continue
        pending.extend(n for n in map(requirement_name, requires) if n and n not in seen)
    return seen


class RequirementsTests(unittest.TestCase):
    def test_ac10_requirements_exactly_pinned_and_approved(self):
        lines = [line.strip() for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()]
        lines = [line for line in lines if line and not line.startswith("#")]
        self.assertTrue(lines, "requirements.txt is empty")

        pinned = []
        for line in lines:
            match = PIN.match(line)
            self.assertIsNotNone(match, f"not an exact pin: {line!r}")
            pinned.append(normalize(match.group(1)))

        allowed = dependency_closure(APPROVED)
        unapproved = sorted(set(pinned) - allowed)
        self.assertEqual(unapproved, [], "pinned packages that are neither approved nor a dependency of one")


if __name__ == "__main__":
    unittest.main()
