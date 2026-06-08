"""spacegirl — SpaceGirl(#5 사도) SSB 의미론적 잠금 도구.

network <-> sexvoid 경계 횡단. 공학 짝패 = Longinus(참조의 미학, 경계 관통).

모드 (PROM 12/16 2026-06-01):
  - cloaking  : ssb.lock/unlock — 가역 식별자 오염 (drop-from-corpus 트리거). default.
  - surface   : surface.apply_surface — homoglyph 보조층 (opportunistic).
  - canary    : canary.inject/check — 비파괴 무단학습 증명 (두 번째 모드).
  - opt-out   : optout — out-of-band do-not-train 신호 (teeth).

# KG: ATOM_SPACEGIRL_index_2026-04-27, lesson-ssb-mode-split-prom12-2026-06-01
"""

from __future__ import annotations

from . import canary, optout, surface
from .ssb import LockResult, lock, unlock
from .wall import WallReport, scan

__all__ = [
    "lock",
    "unlock",
    "scan",
    "LockResult",
    "WallReport",
    "surface",
    "canary",
    "optout",
]
__version__ = "0.4.0"
