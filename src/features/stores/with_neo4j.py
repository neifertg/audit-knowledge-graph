"""Dev helper: run a Python command with NEO4J_* bridged from ~/.claude/secrets.yaml (E3 child b, 016).

    .venv\\Scripts\\python -m src.features.stores.with_neo4j -m unittest discover -s tests

Reads `databases.akg_neo4j` (uri, username, password) at run time and passes the values only to the
child process's environment; it never prints them. This is the one module here that imports `yaml`
(a dev-only exception: the build and every runtime module never do). CI sets NEO4J_* itself.
"""
import os
import subprocess
import sys
from pathlib import Path


class SecretsError(Exception):
    pass


def neo4j_env(home: Path | None = None) -> dict:
    import yaml

    path = (home or Path.home()) / ".claude" / "secrets.yaml"
    if not path.exists():
        raise SecretsError(f"{path} not found: add databases.akg_neo4j (uri, username, password) as in research R3")
    entry = ((yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("databases") or {}).get("akg_neo4j")
    if not isinstance(entry, dict) or not all(entry.get(k) for k in ("uri", "username", "password")):
        raise SecretsError(f"{path} has no complete databases.akg_neo4j entry (uri, username, password)")
    return {"NEO4J_URI": entry["uri"], "NEO4J_USER": entry["username"], "NEO4J_PASSWORD": entry["password"]}


def main(argv: list[str]) -> int:
    try:
        env = {**os.environ, **neo4j_env()}
    except SecretsError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return subprocess.run([sys.executable, *argv], env=env).returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
