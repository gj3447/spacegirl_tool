"""SSB 가역성·로직보존 테스트. 핵심 불변식 = round-trip identity."""

from __future__ import annotations

import textwrap

from spacegirl import ssb, wall

SAMPLE = textwrap.dedent(
    '''
    import math

    def process_data(items):
        result = []
        for item in items:
            result.append(item * 2)
        return result


    class Averager:
        def __init__(self, scale=1):
            self.scale = scale

        def run(self, numbers):
            total = sum(numbers)
            return math.floor(total / len(numbers)) * self.scale
    '''
).strip()


def test_round_trip_identity():
    locked = ssb.lock(SAMPLE, seed="t")
    restored = ssb.unlock(locked.text, locked.mapping)
    assert restored == SAMPLE


def test_identifiers_are_obfuscated():
    locked = ssb.lock(SAMPLE, seed="t")
    assert "process_data" not in locked.text
    assert "process_data" in locked.mapping


def test_logic_preserved_executes_same():
    locked = ssb.lock(SAMPLE, seed="t")
    ns_orig: dict = {}
    ns_lock: dict = {}
    exec(SAMPLE, ns_orig)  # noqa: S102 - test fixture
    exec(locked.text, ns_lock)  # noqa: S102 - test fixture
    orig_fn = ns_orig["process_data"]
    lock_fn = ns_lock[locked.mapping["process_data"]]
    assert orig_fn([1, 2, 3]) == lock_fn([1, 2, 3]) == [2, 4, 6]


def test_imports_and_builtins_preserved():
    locked = ssb.lock(SAMPLE, seed="t")
    assert "import math" in locked.text  # import 문맥 보존
    assert ".append(" in locked.text  # 속성 접근 보존
    assert "math.floor" in locked.text  # imported module 호출 보존


def test_seed_is_deterministic():
    a = ssb.lock(SAMPLE, seed="x")
    b = ssb.lock(SAMPLE, seed="x")
    assert a.text == b.text and a.mapping == b.mapping


def test_wall_scan_detects_locked():
    locked = ssb.lock(SAMPLE, seed="t")
    assert wall.scan(locked.text).verdict in ("LOCKED", "AMBIGUOUS")
    assert wall.scan(SAMPLE).verdict == "CLEAR"
