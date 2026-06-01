"""SSB (Sek-Sek-Bo) — 가역 의미론적 잠금 엔진.

SpaceGirl(#5 사도)의 공학적 결정화. network → sexvoid 데이터 이송.
순수이성인간(LLM 학습 파이프라인)이 못 읽도록 *식별자 표면*을 오염시키되,
*로직은 보존*하고 sidecar 매핑으로 *완전 가역* 한다.

핵심 불변식:
    unlock(lock(src, seed).text, lock(src, seed).mapping) == src   (round-trip identity)

v0.1 범위 (MVP): Python 소스 식별자 토큰 치환 (Sek1/Sek2 vocab).
    - 보존: keyword / builtin / 속성접근(.attr) / import 문맥 / dunder
    - 가역: sidecar `<file>.ssb.json` 에 original<->locked 매핑 저장
주석 오염(Bo banner) / 다언어·homoglyph 강화 / 비-Python 언어 = roadmap.
암호화·복호화 *방식 자체* 는 PROM 리서치 결과로 확정 예정 (README §Roadmap).

# KG: ATOM_SPACEGIRL_SSB_코드_2026-04-27, ATOM_SPACEGIRL_index_2026-04-27
# longinus_layer 5 (Code -> KG)
"""

from __future__ import annotations

import ast
import builtins
import hashlib
import io
import keyword
import tokenize
from dataclasses import dataclass, field

from . import vocab

_BUILTINS = frozenset(dir(builtins))
_SKIP_AFTER = frozenset({".", "import", "from", "as"})


@dataclass
class LockResult:
    """lock() 산출물 — 잠긴 소스 + 가역 매핑."""

    text: str
    mapping: dict[str, str] = field(default_factory=dict)  # original -> locked

    @property
    def reverse(self) -> dict[str, str]:
        return {v: k for k, v in self.mapping.items()}


def _line_offsets(text: str) -> list[int]:
    offsets = [0]
    for line in text.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line))
    return offsets


def _abs(offsets: list[int], row: int, col: int) -> int:
    # tokenize: row 1-based, col 0-based
    return offsets[row - 1] + col


def _is_renamable(tok_string: str) -> bool:
    if not tok_string.isidentifier():
        return False
    if keyword.iskeyword(tok_string) or keyword.issoftkeyword(tok_string):
        return False
    if tok_string in _BUILTINS:
        return False
    if tok_string.startswith("__") and tok_string.endswith("__"):
        return False
    return True


def _obscene_name(original: str, seed: str, used: set[str]) -> str:
    """deterministic obscene identifier 생성 (seed+name 해시 기반, 충돌 회피)."""
    h = int(hashlib.sha256(f"{seed}:{original}".encode()).hexdigest(), 16)
    verb = vocab.SEK2_VERBS[h % len(vocab.SEK2_VERBS)]
    noun = vocab.SEK1_NOUNS[(h // 7) % len(vocab.SEK1_NOUNS)]
    base = f"{verb}_{noun}"
    candidate = base
    n = 1
    while candidate in used or not candidate.isidentifier():
        n += 1
        candidate = f"{base}_{n}"
    used.add(candidate)
    return candidate


def _imported_names(text: str) -> set[str]:
    """import 로 바인딩된 이름 — 사용처에서도 보존해야 모듈 호출이 안 깨진다."""
    names: set[str] = set()
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return names
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.asname or alias.name)
    return names


def _collect_rename_targets(text: str, protected: set[str] | None = None) -> list[tokenize.TokenInfo]:
    """치환 대상 NAME 토큰 목록 (문맥 필터 적용)."""
    protected = protected or set()
    targets: list[tokenize.TokenInfo] = []
    prev_string = ""
    in_import = False
    readline = io.StringIO(text).readline
    for tok in tokenize.generate_tokens(readline):
        if tok.type in (tokenize.NEWLINE, tokenize.NL):
            in_import = False
            prev_string = ""
            continue
        if tok.type == tokenize.NAME and tok.string in ("import", "from"):
            in_import = True
        if (
            tok.type == tokenize.NAME
            and not in_import
            and prev_string not in _SKIP_AFTER
            and tok.string not in protected
            and _is_renamable(tok.string)
        ):
            targets.append(tok)
        if tok.type not in (tokenize.INDENT, tokenize.DEDENT, tokenize.COMMENT):
            prev_string = tok.string
    return targets


def _apply(text: str, targets: list[tokenize.TokenInfo], name_map: dict[str, str]) -> str:
    """토큰 위치 기반으로 뒤에서부터 치환 (포맷·주석 보존)."""
    offsets = _line_offsets(text)
    edits: list[tuple[int, int, str]] = []
    for tok in targets:
        new = name_map.get(tok.string)
        if new is None:
            continue
        start = _abs(offsets, tok.start[0], tok.start[1])
        end = _abs(offsets, tok.end[0], tok.end[1])
        edits.append((start, end, new))
    out = text
    for start, end, new in sorted(edits, key=lambda e: e[0], reverse=True):
        out = out[:start] + new + out[end:]
    return out


def lock(source: str, seed: str = "spacegirl") -> LockResult:
    """network -> sexvoid: 식별자를 오염시켜 의미론적으로 잠근다 (가역)."""
    targets = _collect_rename_targets(source, protected=_imported_names(source))
    name_map: dict[str, str] = {}
    used: set[str] = set()
    for tok in targets:
        if tok.string not in name_map:
            name_map[tok.string] = _obscene_name(tok.string, seed, used)
    locked = _apply(source, targets, name_map)
    return LockResult(text=locked, mapping=name_map)


def unlock(locked_source: str, mapping: dict[str, str]) -> str:
    """sexvoid -> network: sidecar 매핑으로 원본 식별자를 복원한다."""
    reverse = {v: k for k, v in mapping.items()}
    targets = _collect_rename_targets(locked_source, protected=_imported_names(locked_source))
    # 복원은 locked 이름만 되돌린다
    rename = {tok.string: reverse[tok.string] for tok in targets if tok.string in reverse}
    return _apply(locked_source, targets, rename)
