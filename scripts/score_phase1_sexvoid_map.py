#!/usr/bin/env python3
"""Local scorer for LakatosTree node sg-phase1-sexvoid-map.

Metrics (preregistered):
  - pytest_fail_count : direction lower, baseline 1 → progressive if 0
  - scan_tree_api_present : novel higher, threshold 0.5 → 1.0 if API exists

Prints a single JSON line for humans; exit code = fail count (capped).
Does NOT embed a Lakatos verdict (engine judges).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    # 1) pytest fail count
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--tb=no"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    # pytest exit: 0 ok, 1 failed tests, 2 interrupted, 3 internal, 4 usage, 5 no tests
    fail_count = 0 if proc.returncode == 0 else (1 if proc.returncode == 1 else proc.returncode)

    # 2) novel: scan_tree API present + basic behavior
    novel = 0.0
    try:
        sys.path.insert(0, str(ROOT))
        from spacegirl import wall  # noqa: WPS433

        assert hasattr(wall, "scan_tree")
        assert hasattr(wall, "catalog_erased")
        # smoke: empty-ish clear source
        rep = wall.scan("def ok():\n    return 1\n")
        assert rep.verdict == "CLEAR"
        novel = 1.0
    except Exception as e:  # noqa: BLE001
        novel = 0.0
        err = str(e)
    else:
        err = ""

    out = {
        "metric": "pytest_fail_count",
        "value": float(fail_count),
        "novel_metric": "scan_tree_api_present",
        "novel_measured": novel,
        "pytest_returncode": proc.returncode,
        "error": err,
        "tree": "LakatosTree_SpaceGirl_SSB_20260722",
        "tag": "sg-phase1-sexvoid-map",
    }
    print(json.dumps(out, ensure_ascii=False))
    return 0 if fail_count == 0 and novel >= 0.5 else 1


if __name__ == "__main__":
    raise SystemExit(main())
