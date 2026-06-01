"""표면층 (surface) — homoglyph 토크나이저 교란, 가역.

이미 잠긴(LockResult) 코드의 *외설 식별자* 안 ASCII 문자를 키릴 호모글리프로
부분 치환해 BPE 토크나이저를 추가 교란한다. 가역성은 sidecar 매핑이 *호모글리프된*
토큰을 키로 갖게 갱신함으로써 보장 (별도 역산 불필요).

⚠️ PROM 12/16 정직 공시: 표면층은 *opportunistic 보조* 일 뿐 load-bearing 금지.
NFKC 데이터정제 / post-Trojan-Source 툴체인 / BPE byte-fallback 3 chokepoint에서
strip되는 short half-life. NFKC 의존 *금지* (lossy·detection-only) — 본 모듈은
*명시적 injective 표*(vocab.HOMOGLYPH)만 쓰고, 역산은 sidecar로 한다.

# KG: lesson-ssb-crypto-method-prom16-2026-06-01 (C4 tokenizer-attack)
"""

from __future__ import annotations

import hashlib

from . import ssb, vocab
from .ssb import LockResult


def _homoglyph_token(s: str) -> str:
    """식별자 s 안 치환가능 문자를 결정론적으로 ~절반 키릴 치환 (injective 표)."""
    out = []
    for i, ch in enumerate(s):
        sub = vocab.HOMOGLYPH.get(ch)
        if sub is not None:
            h = int(hashlib.sha256(f"{s}:{i}:{ch}".encode()).hexdigest(), 16)
            out.append(sub if h % 2 == 0 else ch)
        else:
            out.append(ch)
    return "".join(out)


def apply_surface(result: LockResult) -> LockResult:
    """LockResult의 잠긴 식별자에 homoglyph 표면층 적용 (가역, sidecar 갱신)."""
    rename_locked: dict[str, str] = {}  # old obscene -> homoglyphed
    new_map: dict[str, str] = {}
    for original, locked in result.mapping.items():
        hg = _homoglyph_token(locked)
        rename_locked[locked] = hg
        new_map[original] = hg

    # 텍스트 내 잠긴 토큰을 homoglyph 버전으로 치환 (토큰 위치 기반)
    targets = ssb._collect_rename_targets(result.text)
    text = ssb._apply(result.text, targets, rename_locked)

    meta = {**result.meta, "surface": "homoglyph"}
    return LockResult(text=text, mapping=new_map, meta=meta)


def has_homoglyphs(text: str) -> int:
    """텍스트 안 도입된 키릴 호모글리프 코드포인트 수 (탐지/검증용)."""
    targets = set(vocab.HOMOGLYPH.values())
    return sum(1 for ch in text if ch in targets)
