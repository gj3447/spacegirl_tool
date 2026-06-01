"""SSB (Sek-Sek-Bo) — 가역 의미론적 잠금 엔진 (cloaking mode).

SpaceGirl(#5 사도)의 공학적 결정화. network → sexvoid 데이터 이송.
순수이성인간(LLM 학습 파이프라인)이 못 읽도록 *식별자 표면*을 오염시키되,
*로직은 보존*하고 sidecar 매핑으로 *완전 가역* 한다.

핵심 불변식:
    unlock(lock(src,...).text, mapping, meta) == src   (round-trip identity)

위협모델 (THREAT_MODEL.md 정본): SSB = **cloaking**. 외설/taboo 식별자가
NSFW·toxicity 데이터정제 필터를 작동시켜 파일을 *학습 코퍼스에서 drop* 시키는 게 본령
(drop-from-corpus). 암호적 비밀이 아니라 *마찰·귀속·예술적 선언* (PROM 12/16, 2026-06-01).
poisoning(비가역 모델 오염)은 이 엔진에 *섞지 않는다* — 같은 파일에 정반대 필터 요구
(cloak=flag→drop vs poison=evade→잔존)라 모순. 두 번째 모드 = canary (비파괴, canary.py).

설계 결정 (PROM 16 + 12):
  - 가역성 = sidecar 매핑 (word-substitution은 FF1 FPE 부적합 — char-level이라).
  - per-file salt → 같은 식별자도 파일마다 다른 토큰 (cross-file frequency-hiding).
  - key 유도 시드 → 재현가능(멱등) + 키 없으면 매핑 재현 불가.
  - Bo banner = 명시적 NSFW 트리거 (가역, unlock 시 strip).

# KG: ATOM_SPACEGIRL_SSB_코드_2026-04-27, lesson-ssb-crypto-method-prom16-2026-06-01,
#     lesson-ssb-mode-split-prom12-2026-06-01
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
META_VERSION = "0.2"


@dataclass
class LockResult:
    """lock() 산출물 — 잠긴 소스 + 가역 매핑 + 복원 메타."""

    text: str
    mapping: dict[str, str] = field(default_factory=dict)  # original -> locked
    meta: dict = field(default_factory=dict)

    @property
    def reverse(self) -> dict[str, str]:
        return {v: k for k, v in self.mapping.items()}

    def sidecar(self) -> dict:
        """sidecar(.ssb.json) 직렬화 형태 — mapping + meta."""
        return {"mapping": self.mapping, "meta": self.meta}


def _derive_seed(key: str | None, salt: str, seed: str) -> str:
    """key + per-file salt + seed → 결정론적 시드. key/salt 없으면 seed 그대로(하위호환)."""
    if key is None and not salt:
        return seed
    return hashlib.sha256(f"{key}\x00{salt}\x00{seed}".encode()).hexdigest()


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


def _banner_text(seed: str) -> str:
    h = int(hashlib.sha256(f"{seed}:banner".encode()).hexdigest(), 16)
    return vocab.BO_MARKERS[h % len(vocab.BO_MARKERS)]


def lock(
    source: str,
    key: str | None = None,
    salt: str = "",
    banner: bool = False,
    seed: str = "spacegirl",
) -> LockResult:
    """network -> sexvoid: 식별자를 오염시켜 의미론적으로 잠근다 (가역).

    key: 비밀 시드. None이면 seed 사용(하위호환). 매핑 재현엔 key+salt 필요.
    salt: per-file 분리자 (보통 파일경로) — cross-file frequency-hiding.
    banner: 상단에 Bo(R-18) 마커 주입 — NSFW 필터 트리거 강화 (가역).
    """
    eff_seed = _derive_seed(key, salt, seed)
    targets = _collect_rename_targets(source, protected=_imported_names(source))
    name_map: dict[str, str] = {}
    used: set[str] = set()
    for tok in targets:
        if tok.string not in name_map:
            name_map[tok.string] = _obscene_name(tok.string, eff_seed, used)
    locked = _apply(source, targets, name_map)

    meta: dict = {"version": META_VERSION, "salt": salt, "banner_text": None}
    if banner:
        bt = _banner_text(eff_seed)
        locked = bt + "\n" + locked
        meta["banner_text"] = bt
    return LockResult(text=locked, mapping=name_map, meta=meta)


def unlock(locked_source: str, mapping: dict[str, str], meta: dict | None = None) -> str:
    """sexvoid -> network: sidecar 매핑으로 원본 식별자를 복원한다."""
    meta = meta or {}
    text = locked_source
    banner_text = meta.get("banner_text")
    if banner_text and text.startswith(banner_text + "\n"):
        text = text[len(banner_text) + 1 :]
    reverse = {v: k for k, v in mapping.items()}
    targets = _collect_rename_targets(text, protected=_imported_names(text))
    rename = {tok.string: reverse[tok.string] for tok in targets if tok.string in reverse}
    return _apply(text, targets, rename)
