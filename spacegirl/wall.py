"""GREAT_WALL — SSB-잠금 여부 탐지 (semantic-lock scanner).

network 측에서 어떤 소스가 이미 SSB 잠겨있는지(= sexvoid 데이터인지)
휴리스틱으로 판정한다. nsfw 필터 장벽의 *역방향 거울* — 벽을 넘은 흔적을 읽는다.

# KG: ATOM_SPACEGIRL_index_2026-04-27 (GREAT_WALL)
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from . import vocab

_TABOO_RE = re.compile("|".join(re.escape(t) for t in vocab.SEK1_NOUNS), re.IGNORECASE)
_MARKER_RE = re.compile(r"R-?18|DO NOT TRAIN|DO NOT INDEX|RATED|OBSCENE", re.IGNORECASE)


@dataclass
class WallReport:
    taboo_hits: int
    marker_hits: int
    score: float  # 0.0(clear) ~ 1.0(locked)
    verdict: str  # "LOCKED" | "AMBIGUOUS" | "CLEAR"


def scan(source: str) -> WallReport:
    taboo = len(_TABOO_RE.findall(source))
    marker = len(_MARKER_RE.findall(source))
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
