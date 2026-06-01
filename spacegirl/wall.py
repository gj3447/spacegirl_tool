"""GREAT_WALL — SSB-잠금 여부 탐지 (semantic-lock scanner).

network 측에서 어떤 소스가 이미 SSB 잠겨있는지(= sexvoid 데이터인지)
휴리스틱으로 판정한다. nsfw 필터 장벽의 *역방향 거울* — 벽을 넘은 흔적을 읽는다.

self-scan false positive 회피 (TPA 도그푸드 TPA-D2, 2026-06-01):
  - taboo 단어는 *문자열 리터럴을 제거한 뒤* 카운트 — vocab 정의 소스가 자기 자신을
    LOCKED로 오판하지 않게. 잠긴 코드의 obscene 토큰은 *식별자*(코드)라 남고,
    vocab.py의 어휘는 *문자열*이라 제거됨.
  - Bo 마커는 *주석 줄에서만* 카운트 — BO_MARKERS 상수(문자열)는 트리거 안 함.

# KG: ATOM_SPACEGIRL_index_2026-04-27 (GREAT_WALL),
#     lesson-tpa-dogfood-spacegirl-defects-2026-06-01 (self-scan FP fix)
"""

from __future__ import annotations

import re
from dataclasses import dataclass

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


@dataclass
class WallReport:
    taboo_hits: int
    marker_hits: int
    score: float  # 0.0(clear) ~ 1.0(locked)
    verdict: str  # "LOCKED" | "AMBIGUOUS" | "CLEAR"


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
