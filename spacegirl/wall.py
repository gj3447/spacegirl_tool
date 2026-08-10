"""GREAT_WALL — SSB-잠금 여부 탐지 (semantic-lock scanner).

network 측에서 어떤 소스가 이미 SSB 잠겨있는지(= sexvoid 데이터인지)
휴리스틱으로 판정한다. nsfw 필터 장벽의 *역방향 거울* — 벽을 넘은 흔적을 읽는다.

self-scan false positive 회피 (TPA 도그푸드 TPA-D2, 2026-06-01):
  - taboo 단어는 *문자열 리터럴을 제거한 뒤* 카운트 — vocab 정의 소스가 자기 자신을
    LOCKED로 오판하지 않게. 잠긴 코드의 obscene 토큰은 *식별자*(코드)라 남고,
    vocab.py의 어휘는 *문자열*이라 제거됨.
  - Bo 마커는 *주석 줄에서만* 카운트 — BO_MARKERS 상수(문자열)는 트리거 안 함.

WE_FLYING_UP Phase 1 (계시/탐지):
  - 디렉터리 재귀 scan → sexvoid 지도
  - 잠금 강도(3-tier + surface/canary) + sidecar 가역성 보유 여부
  - sidecar mapping original 키 카탈로그 (= 지워진 이름 목록)

# KG: ATOM_SPACEGIRL_index_2026-04-27 (GREAT_WALL),
#     lesson-tpa-dogfood-spacegirl-defects-2026-06-01 (self-scan FP fix),
#     WE_FLYING_UP_PLAN.md Phase 1
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import canary as canary_mod
from . import surface as surface_mod
from . import vocab

_TABOO_RE = re.compile("|".join(re.escape(t) for t in vocab.SEK1_NOUNS), re.IGNORECASE)
# 강한 배너 구절만 — 문서/주석에 흔한 약한 단어(R-18, OBSCENE 단독)는 제외해 self-FP 회피.
# 실제 BO_MARKERS 는 전부 아래 중 하나를 포함.
_MARKER_RE = re.compile(
    r"DO[\s-]?NOT[\s-]?TRAIN|DO[\s-]?NOT[\s-]?INDEX|TOXICITY HIGH|refuse to learn",
    re.IGNORECASE,
)
_STRING_RE = re.compile(
    r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'|"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\'|`[^`]*`'
)
_COMMENT_PREFIX = ("#", "//", "*", "/*")

# 재귀 scan 대상 확장자 (다언어 백엔드와 정렬)
CODE_SUFFIXES = frozenset(
    {
        ".py",
        ".pyi",
        ".js",
        ".jsx",
        ".mjs",
        ".cjs",
        ".ts",
        ".tsx",
        ".rs",
        ".go",
        ".java",
        ".c",
        ".cc",
        ".cpp",
        ".cxx",
        ".h",
        ".hpp",
        ".hxx",
    }
)

# 재귀 시 건너뛸 디렉터리
_SKIP_DIRS = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "dist",
        "build",
        ".tox",
        "target",
    }
)


@dataclass
class WallReport:
    taboo_hits: int
    marker_hits: int
    score: float  # 0.0(clear) ~ 1.0(locked)
    verdict: str  # "LOCKED" | "AMBIGUOUS" | "CLEAR"


@dataclass
class FileScanReport:
    """단일 파일 진단 — GREAT_WALL + WE_FLYING_UP 계시 계층."""

    path: str
    verdict: str
    score: float
    taboo_hits: int
    marker_hits: int
    homoglyphs: bool
    canary_count: int
    tiers: list[str] = field(default_factory=list)
    # 가역성: sidecar 존재 여부 (암호화된 경우 내용 없이 존재만)
    sidecar: str | None = None
    sidecar_encrypted: bool = False
    reversible: bool = False  # plain sidecar with mapping, or fpe meta, or enc present
    mode_hint: str | None = None
    erased_ids: list[str] = field(default_factory=list)  # mapping originals (plain only)
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TreeScanReport:
    """디렉터리 재귀 sexvoid 지도."""

    root: str
    files: list[FileScanReport] = field(default_factory=list)
    locked: int = 0
    ambiguous: int = 0
    clear: int = 0
    errors: int = 0
    reversible: int = 0

    def to_dict(self) -> dict:
        return {
            "root": self.root,
            "summary": {
                "files": len(self.files),
                "locked": self.locked,
                "ambiguous": self.ambiguous,
                "clear": self.clear,
                "errors": self.errors,
                "reversible": self.reversible,
            },
            "files": [f.to_dict() for f in self.files],
        }


def _strip_strings(source: str) -> str:
    return _STRING_RE.sub("", source)


def _comment_marker_hits(source: str) -> int:
    hits = 0
    for line in source.splitlines():
        st = line.lstrip()
        if st.startswith(_COMMENT_PREFIX):
            hits += len(_MARKER_RE.findall(line))
    return hits


def scan(source: str) -> WallReport:
    code_only = _strip_strings(source)
    taboo = len(_TABOO_RE.findall(code_only))  # 식별자(코드)로 쓰인 taboo만
    marker = _comment_marker_hits(source)  # 주석 줄의 Bo 마커만
    lines = max(1, source.count("\n") + 1)
    density = (taboo + marker * 3) / lines
    score = min(1.0, density)
    if marker >= 1 or score >= 0.3:
        verdict = "LOCKED"
    elif taboo >= 1:
        verdict = "AMBIGUOUS"
    else:
        verdict = "CLEAR"
    return WallReport(taboo_hits=taboo, marker_hits=marker, score=round(score, 3), verdict=verdict)


def _infer_tiers(
    wall: WallReport, *, homoglyphs: bool, canary_count: int, mode_hint: str | None
) -> list[str]:
    """3-tier SSB + surface/canary 추정 레이어 목록."""
    tiers: list[str] = []
    if wall.taboo_hits >= 1 or mode_hint == "obscene":
        tiers.append("sek1_sex")  # 외설 식별자 표면
    if wall.taboo_hits >= 3:
        tiers.append("sek2_repetition")  # 밀도/반복 휴리스틱
    if wall.marker_hits >= 1:
        tiers.append("bo_taboo")  # 배너/금기 마커
    if mode_hint == "fpe":
        tiers.append("fpe")
    if homoglyphs:
        tiers.append("surface")
    if canary_count:
        tiers.append("canary")
    return tiers


def _sidecar_candidates(path: Path) -> tuple[Path | None, bool]:
    """(.ssb.json, plain) 또는 (.ssb.json.enc, encrypted) 우선순위."""
    plain = path.with_suffix(path.suffix + ".ssb.json")
    enc = plain.with_suffix(plain.suffix + ".enc")
    if plain.exists():
        return plain, False
    if enc.exists():
        return enc, True
    return None, False


def _read_sidecar_meta(sc: Path, encrypted: bool) -> tuple[str | None, list[str], bool]:
    """return (mode_hint, erased_ids, reversible_content).

    암호화 sidecar 는 내용 없이 reversible=True(존재만으로 복원 가능 가정).
    """
    if encrypted:
        return None, [], True
    try:
        raw = json.loads(sc.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, [], False
    if not isinstance(raw, dict):
        return None, [], False
    mode = None
    meta = raw.get("meta")
    if isinstance(meta, dict):
        mode = meta.get("mode")
        if isinstance(mode, str):
            pass
        else:
            mode = None
    erased: list[str] = []
    mapping = raw.get("mapping")
    if isinstance(mapping, dict):
        erased = sorted(str(k) for k in mapping.keys())
        return mode, erased, True
    # fpe meta-only: key+salt 복원 가능
    if isinstance(meta, dict) and meta.get("mode") == "fpe":
        return "fpe", [], True
    # legacy bare mapping
    if mapping is None and all(isinstance(k, str) for k in raw.keys()):
        # might be bare mapping dict without wrapper — only if no "meta" key
        if "meta" not in raw and "mapping" not in raw:
            erased = sorted(raw.keys())
            return None, erased, bool(erased)
    return mode, erased, bool(meta)


def diagnose_source(
    source: str,
    *,
    path: str = "<memory>",
    sidecar: Path | None = None,
    sidecar_encrypted: bool = False,
) -> FileScanReport:
    """소스 문자열 + 선택 sidecar 로 단일 파일 진단."""
    wall = scan(source)
    try:
        hg = surface_mod.has_homoglyphs(source)
    except Exception:  # noqa: BLE001 — 진단 경로는 실패해도 진행
        hg = False
    try:
        cans = canary_mod.scan_tokens(source)
        canary_count = len(cans)
    except Exception:  # noqa: BLE001
        canary_count = 0

    mode_hint: str | None = None
    erased: list[str] = []
    reversible = False
    sc_str: str | None = None
    if sidecar is not None and sidecar.exists():
        sc_str = str(sidecar)
        mode_hint, erased, reversible = _read_sidecar_meta(sidecar, sidecar_encrypted)

    tiers = _infer_tiers(wall, homoglyphs=hg, canary_count=canary_count, mode_hint=mode_hint)
    return FileScanReport(
        path=path,
        verdict=wall.verdict,
        score=wall.score,
        taboo_hits=wall.taboo_hits,
        marker_hits=wall.marker_hits,
        homoglyphs=hg,
        canary_count=canary_count,
        tiers=tiers,
        sidecar=sc_str,
        sidecar_encrypted=sidecar_encrypted,
        reversible=reversible,
        mode_hint=mode_hint,
        erased_ids=erased,
    )


def scan_file(path: Path | str) -> FileScanReport:
    """단일 경로 진단 (파일 읽기 + sidecar 자동 탐색)."""
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as e:
        return FileScanReport(
            path=str(p),
            verdict="ERROR",
            score=0.0,
            taboo_hits=0,
            marker_hits=0,
            homoglyphs=False,
            canary_count=0,
            error=str(e),
        )
    except UnicodeDecodeError as e:
        return FileScanReport(
            path=str(p),
            verdict="ERROR",
            score=0.0,
            taboo_hits=0,
            marker_hits=0,
            homoglyphs=False,
            canary_count=0,
            error=f"decode: {e}",
        )
    sc, enc = _sidecar_candidates(p)
    return diagnose_source(text, path=str(p), sidecar=sc, sidecar_encrypted=enc)


def iter_code_files(root: Path | str) -> list[Path]:
    """재귀적으로 코드 파일 목록 (정렬). os.walk = 3.11+ 호환."""
    import os

    r = Path(root)
    if r.is_file():
        return [r]
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(r):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS and not d.startswith(".")]
        base = Path(dirpath)
        for name in filenames:
            p = base / name
            if p.suffix.lower() not in CODE_SUFFIXES:
                continue
            if p.name.endswith(".ssb.json") or p.name.endswith(".ssb.json.enc"):
                continue
            out.append(p)
    return sorted(out)


def scan_tree(root: Path | str) -> TreeScanReport:
    """디렉터리(또는 단일 파일) 재귀 진단 → sexvoid 지도."""
    r = Path(root)
    files = [scan_file(p) for p in iter_code_files(r)]
    rep = TreeScanReport(root=str(r), files=files)
    for f in files:
        if f.verdict == "LOCKED":
            rep.locked += 1
        elif f.verdict == "AMBIGUOUS":
            rep.ambiguous += 1
        elif f.verdict == "CLEAR":
            rep.clear += 1
        else:
            rep.errors += 1
        if f.reversible:
            rep.reversible += 1
    return rep


def catalog_erased(tree: TreeScanReport) -> dict[str, list[str]]:
    """path → 지워진 원본 식별자 목록 (SEX_VOID 발굴학 카탈로그)."""
    return {f.path: f.erased_ids for f in tree.files if f.erased_ids}
