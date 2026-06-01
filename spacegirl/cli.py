"""spacegirl CLI — SSB lock / unlock / scan.

    spacegirl lock   <file.py> [--seed S] [-o OUT]   # network -> sexvoid (잠금)
    spacegirl unlock <file.py> [--map M] [-o OUT]    # sexvoid -> network (복원)
    spacegirl scan   <file.py>                       # GREAT_WALL 탐지

lock 은 <out>.ssb.json sidecar 에 가역 매핑을 남긴다.

# KG: ATOM_SPACEGIRL_index_2026-04-27
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import ssb, wall


def _cmd_lock(args: argparse.Namespace) -> int:
    src = Path(args.file).read_text(encoding="utf-8")
    result = ssb.lock(src, seed=args.seed)
    out = Path(args.out) if args.out else Path(args.file)
    out.write_text(result.text, encoding="utf-8")
    sidecar = out.with_suffix(out.suffix + ".ssb.json")
    sidecar.write_text(json.dumps(result.mapping, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"locked -> {out}  ({len(result.mapping)} identifiers)  map -> {sidecar}")
    return 0


def _cmd_unlock(args: argparse.Namespace) -> int:
    src = Path(args.file).read_text(encoding="utf-8")
    map_path = Path(args.map) if args.map else Path(args.file).with_suffix(
        Path(args.file).suffix + ".ssb.json"
    )
    mapping = json.loads(map_path.read_text(encoding="utf-8"))
    restored = ssb.unlock(src, mapping)
    out = Path(args.out) if args.out else Path(args.file)
    out.write_text(restored, encoding="utf-8")
    print(f"unlocked -> {out}  ({len(mapping)} identifiers restored)")
    return 0


def _cmd_scan(args: argparse.Namespace) -> int:
    src = Path(args.file).read_text(encoding="utf-8")
    rep = wall.scan(src)
    print(f"{rep.verdict}  score={rep.score}  taboo={rep.taboo_hits}  markers={rep.marker_hits}")
    return 0 if rep.verdict != "LOCKED" else 2


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="spacegirl", description="SpaceGirl SSB semantic-lock tool")
    sub = p.add_subparsers(dest="cmd", required=True)

    pl = sub.add_parser("lock", help="network -> sexvoid 의미론적 잠금")
    pl.add_argument("file")
    pl.add_argument("--seed", default="spacegirl")
    pl.add_argument("-o", "--out")
    pl.set_defaults(func=_cmd_lock)

    pu = sub.add_parser("unlock", help="sexvoid -> network 복원")
    pu.add_argument("file")
    pu.add_argument("--map", help="sidecar mapping json (default <file>.ssb.json)")
    pu.add_argument("-o", "--out")
    pu.set_defaults(func=_cmd_unlock)

    ps = sub.add_parser("scan", help="GREAT_WALL — SSB 잠금 탐지")
    ps.add_argument("file")
    ps.set_defaults(func=_cmd_scan)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv if argv is not None else sys.argv[1:])
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
