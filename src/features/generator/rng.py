"""Independent, reproducible random streams.

Every entity type and relationship file draws from its own stream, derived from the
master seed and the stream's name. Adding draws to one stream never shifts another,
so later children can extend the generator without changing earlier output (AC-11).
"""
import hashlib
import random


def stream(seed: int, name: str) -> random.Random:
    digest = hashlib.sha256(f"{seed}:{name}".encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))
