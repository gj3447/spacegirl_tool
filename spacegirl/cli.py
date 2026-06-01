"""spacegirl CLI — SSB cloaking + canary + opt-out.

    spacegirl lock   <file> [--key K] [--salt S] [--banner] [--surface] [-o OUT]
    spacegirl unlock <file> [--map M] [-o OUT]
    spacegirl scan   <file>
    spacegirl canary inject <file> --secret S [--label L] [-o OUT]
    spacegirl canary check  <file> --secret S [--label L]
    spacegirl optout robots|ai|header [--contact C] [--policy URL] [-o OUT]

lock 은 <out>.ssb.json sidecar(mapping+meta)에 가역 정보를 남긴다.
--salt 미지정 시 입력 파일경로를 salt로 써서 cross-file frequency-hiding.

# KG: ATOM_SPACEGIRL_index_2026-04-27, lesson-ssb-mode-split-prom12-2026-06-01
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import canary as canary_mod
from . import lang as lang_mod
from . import optout as optout_mod
from . import ssb, surface, wall


def _sidecar_path(p: Path) -> Path:
    return p.with_suffix(p.suffix + ".ssb.json")


def _cmd_lock(args: argparse.Namespace) -> int:
    src = Path(args.file).read_text(encoding="utf-8")
    salt = args.salt if args.salt is not None else str(args.file)
    lang = args.lang or lang_mod.lang_for_path(str(args.file))
    result = ssb.lock(src, key=args.key, salt=salt, banner=args.banner, lang=lang)
    if args.surface:
        result = surface.apply_surface(result)
    out = Path(args.out) if args.out else Path(args.file)
    out.write_text(result.text, encoding="utf-8")
    sc = _sidecar_path(out)
    sc.write_text(json.dumps(result.sidecar(), ensure_ascii=False, indent=2), encoding="utf-8")
    layers = ["rename"] + (["banner"] if args.banner else []) + (["surface"] if args.surface else [])
    print(f"locked[{lang}] -> {out}  ({len(result.mapping)} ids, layers: {'+'.join(layers)})  map -> {sc}")
    return 0


def _cmd_unlock(args: argparse.Namespace) -> int:
    src = Path(args.file).read_text(encoding="utf-8")
    map_path = Path(args.map) if args.map else _sidecar_path(Path(args.file))
    raw = json.loads(map_path.read_text(encoding="utf-8"))
    # 하위호환: 평문 dict(mapping) 또는 {mapping, meta}
    mapping = raw.get("mapping", raw) if isinstance(raw, dict) and "mapping" in raw else raw
    meta = raw.get("meta", {}) if isinstance(raw, dict) else {}
    restored = ssb.unlock(src, mapping, meta)
    out = Path(args.out) if args.out else Path(args.file)
    out.write_text(restored, encoding="utf-8")
    print(f"unlocked -> {out}  ({len(mapping)} ids restored)")
    return 0


def _cmd_scan(args: argparse.Namespace) -> int:
    src = Path(args.file).read_text(encoding="utf-8")
    rep = wall.scan(src)
    hg = surface.has_homoglyphs(src)
    cans = canary_mod.scan_tokens(src)
    print(
        f"{rep.verdict}  score={rep.score}  taboo={rep.taboo_hits}  "
        f"markers={rep.marker_hits}  homoglyphs={hg}  canaries={len(cans)}"
    )
    return 0 if rep.verdict != "LOCKED" else 2


def _cmd_canary(args: argparse.Namespace) -> int:
    if args.canary_cmd == "inject":
        src = Path(args.file).read_text(encoding="utf-8")
        text, rec = canary_mod.inject(src, args.secret, args.label or "", args.lang)
        out = Path(args.out) if args.out else Path(args.file)
        out.write_text(text, encoding="utf-8")
        print(f"canary -> {out}  token={rec.token}")
        return 0
    # check
    text = Path(args.file).read_text(encoding="utf-8")
    hit = canary_mod.check(text, args.secret, args.label or "")
    token = canary_mod.make_canary(args.secret, args.label or "")
    print(f"{'MATCH' if hit else 'NO-MATCH'}  token={token}")
    return 0 if hit else 1


def _cmd_optout(args: argparse.Namespace) -> int:
    if args.kind == "robots":
        text = optout_mod.robots_txt()
    elif args.kind == "ai":
        text = optout_mod.ai_txt(contact=args.contact or "", policy_url=args.policy or "")
    elif args.kind == "c2pa":
        text = optout_mod.c2pa_manifest(contact=args.contact or "")
    else:  # header
        text = optout_mod.notrain_header(lang=args.lang, contact=args.contact or "")
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.kind} -> {args.out}")
    else:
        sys.stdout.write(text)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="spacegirl", description="SpaceGirl SSB semantic-lock tool")
    sub = p.add_subparsers(dest="cmd", required=True)

    pl = sub.add_parser("lock", help="network -> sexvoid 의미론적 잠금")
    pl.add_argument("file")
    pl.add_argument("--key", default=None, help="비밀 시드 (매핑 재현엔 key+salt 필요)")
    pl.add_argument("--salt", default=None, help="per-file 분리자 (기본=파일경로)")
    pl.add_argument("--banner", action="store_true", help="Bo R-18 배너 주입 (NSFW 트리거)")
    pl.add_argument("--surface", action="store_true", help="homoglyph 표면층 (opportunistic)")
    pl.add_argument("--lang", default=None, help="언어 (기본=확장자 자동감지): python/javascript/typescript/rust/go/java/c/cpp")
    pl.add_argument("-o", "--out")
    pl.set_defaults(func=_cmd_lock)

    pu = sub.add_parser("unlock", help="sexvoid -> network 복원")
    pu.add_argument("file")
    pu.add_argument("--map", help="sidecar (기본 <file>.ssb.json)")
    pu.add_argument("-o", "--out")
    pu.set_defaults(func=_cmd_unlock)

    ps = sub.add_parser("scan", help="GREAT_WALL — 잠금/표면/canary 탐지")
    ps.add_argument("file")
    ps.set_defaults(func=_cmd_scan)

    pc = sub.add_parser("canary", help="비파괴 무단학습 증명 워터마크")
    csub = pc.add_subparsers(dest="canary_cmd", required=True)
    ci = csub.add_parser("inject")
    ci.add_argument("file")
    ci.add_argument("--secret", required=True)
    ci.add_argument("--label", default="")
    ci.add_argument("--lang", default="python")
    ci.add_argument("-o", "--out")
    cc = csub.add_parser("check")
    cc.add_argument("file")
    cc.add_argument("--secret", required=True)
    cc.add_argument("--label", default="")
    pc.set_defaults(func=_cmd_canary)

    po = sub.add_parser("optout", help="out-of-band do-not-train 신호")
    po.add_argument("kind", choices=["robots", "ai", "header", "c2pa"])
    po.add_argument("--contact", default="")
    po.add_argument("--policy", default="")
    po.add_argument("--lang", default="python")
    po.add_argument("-o", "--out")
    po.set_defaults(func=_cmd_optout)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv if argv is not None else sys.argv[1:])
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
