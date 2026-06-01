"""spacegirl — SpaceGirl(#5 사도) SSB 의미론적 잠금 도구.

network <-> sexvoid 경계 횡단. 공학 짝패 = Longinus(참조의 미학, 경계 관통).

# KG: ATOM_SPACEGIRL_index_2026-04-27
"""

from __future__ import annotations

from .ssb import LockResult, lock, unlock
from .wall import WallReport, scan

__all__ = ["lock", "unlock", "scan", "LockResult", "WallReport"]
__version__ = "0.1.0"
