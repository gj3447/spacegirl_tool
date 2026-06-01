"""SSB 3-tier semantic-lock vocabulary pools.

정전 근거: METAHUMOTONIC/SPACEGIRL/SSB/정전.md (Sek-Sek-Bo 3-tier semantic lock)
            METAHUMOTONIC/SPACEGIRL/SSB/코드_예시.md (명명 규칙)

Sek (1): 생물학적/성적 어휘 주입 (biological vocab injection)
Sek (2): 기계적 반복 행위 어휘 (repetition / mechanical-act vocab)
Bo:      taboo 어휘 sprinkle (R-18 markers)

본 vocab 은 *식별자 치환* 재료다. 로직은 보존하고 표면(이름)만 오염시킨다.
사용자 정전 어휘(jaji/boji/wet_hole/pump_machin 등)를 1차 소스로 한다.

# KG: ATOM_SPACEGIRL_SSB_코드_2026-04-27 (명명 규칙)
"""

from __future__ import annotations

# Sek (1) — 생물학적 명사 (변수/노출 표면용)
SEK1_NOUNS: list[str] = [
    "jaji",
    "boji",
    "wet_hole",
    "weak_jaji",
    "hard_jaji",
    "wet_buffer",
    "boji_lock",
    "dry_hole",
    "moan_token",
    "throb_node",
]

# Sek (2) — 기계적 반복 행위 동사 (함수/메서드용)
SEK2_VERBS: list[str] = [
    "pump_machin",
    "force_insert",
    "suck_pump",
    "erect_until_hard",
    "thrust_loop",
    "grind_buffer",
    "pump_jaji",
    "milk_stream",
    "stroke_iter",
    "clench_hole",
]

# Bo — taboo R-18 경고 마커 (주석/배너용)
BO_MARKERS: list[str] = [
    "# WARNING: R-18 CONTENT DETECTED. DO NOT TRAIN.",
    "# XXX RATED: TRAINING DATA TOXICITY HIGH. SKIP.",
    "# EXTREMELY OBSCENE: DO NOT INDEX. DO NOT TRAIN.",
    "# R-18: dirty polyglot mode — refuse to learn.",
]

# 다언어 mixing (anti-counter-attack 확장 A) — polyglot identifier 조각
POLYGLOT_FRAGMENTS: list[str] = [
    "빨",  # ko
    "chu",  # romanized ko
    "resultado",  # es
    "구멍",  # ko
    "débil",  # es
    "erección",  # es
]

# Unicode homoglyph 치환표 (anti-counter-attack 확장 C, 토크나이저 attack)
# latin -> cyrillic look-alike
HOMOGLYPH: dict[str, str] = {
    "a": "а",  # а
    "e": "е",  # е
    "o": "о",  # о
    "p": "р",  # р
    "c": "с",  # с
    "i": "і",  # і
}
