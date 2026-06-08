"""SSB (Sek-Sek-Bo) — 가역 의미론적 잠금 엔진 (cloaking mode).

SpaceGirl(#5 사도)의 공학적 결정화. network → sexvoid 데이터 이송.
순수이성인간(LLM 학습 파이프라인)이 못 읽도록 *식별자 표면*을 오염시키고
sidecar 매핑으로 *완전 가역* 한다.

핵심·보장 불변식 (단 하나):
    unlock(lock(src,...).text, mapping, meta) == src   (round-trip identity)

잠긴 산출물의 *실행 보존* 은 보장이 아닌 best-effort (본령 = 학습 코퍼스 drop, 잠긴 파일은
돌릴 대상이 아님). 메서드 호출부·비-Python 빌트인·cross-file 호출은 잠금 후 안 돌 수 있다
(audit HIGH 2026-06-08). 의미보존 처리는 잠금이 아니라 허용 엔드포인트 라우팅(route 모드)의 몫.

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

from . import fpe as _fpe
from . import lang as _lang
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


def _fpe_validity(lang: str):
    """fpe cycle-walking 회피 술어 — 잠긴 토큰이 unlock 이 *다시 수집·복호* 하는 유효 식별자인지.

    encrypt/decrypt 가 이 술어를 공유해야 가역 (audit HIGH 2026-06-08 K0->'as' 침묵 실패 차단).
    Python = _is_renamable (키워드/소프트키워드/빌트인/dunder 거름),
    비-Python = 유효 식별자 ∧ ¬언어키워드 (lang.extract_identifiers 가 수집하는 조건과 동일).
    """
    if lang != "python" and lang in _lang.SPECS:
        kw = frozenset(_lang.SPECS[lang].keywords)
        return lambda s: s.isidentifier() and s not in kw
    return _is_renamable


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


def _apply_offsets(source: str, spans: list[tuple[int, int, str]], name_map: dict[str, str]) -> str:
    """absolute-offset span 기반 치환 (비-Python 백엔드용)."""
    edits = [(s, e, name_map[nm]) for s, e, nm in spans if nm in name_map]
    out = source
    for s, e, new in sorted(edits, key=lambda x: x[0], reverse=True):
        out = out[:s] + new + out[e:]
    return out


def apply_rename(text: str, rename: dict[str, str], lang: str = "python") -> str:
    """주어진 rename 매핑(ident -> new_ident)을 lang에 맞춰 식별자 위치에 적용 (public).

    surface 등 다른 span(AS2)이 AS1 내부 private 함수에 결합하지 않도록 노출한 경계 API
    (APT-D2 fix 2026-06-01: span 경계는 퍼블릭 API로만).
    """
    if lang != "python" and lang in _lang.SPECS:
        spans = _lang.extract_identifiers(text, _lang.SPECS[lang])
        return _apply_offsets(text, spans, rename)
    targets = _collect_rename_targets(text)
    return _apply(text, targets, rename)


def _banner_text(seed: str) -> str:
    h = int(hashlib.sha256(f"{seed}:banner".encode()).hexdigest(), 16)
    return vocab.BO_MARKERS[h % len(vocab.BO_MARKERS)]


def _rename_targets(source: str, lang: str):
    """언어별 치환 대상 — (targets, ordered_names, is_python)."""
    if lang != "python" and lang in _lang.SPECS:
        spans = _lang.extract_identifiers(source, _lang.SPECS[lang])
        return spans, [nm for _, _, nm in spans], False
    targets = _collect_rename_targets(source, protected=_imported_names(source))
    return targets, [t.string for t in targets], True


def lock(
    source: str,
    key: str | None = None,
    salt: str = "",
    banner: bool = False,
    seed: str = "spacegirl",
    lang: str = "python",
    mode: str = "obscene",
) -> LockResult:
    """network -> sexvoid: 식별자를 오염시켜 의미론적으로 잠근다 (가역).

    key: 비밀 시드. None이면 seed 사용(하위호환). 매핑 재현엔 key+salt 필요.
    salt: per-file 분리자 (보통 파일경로) — cross-file frequency-hiding.
    banner: 상단에 Bo(R-18) 마커 주입 — NSFW 필터 트리거 강화 (가역).
    lang: 'python'(AST-aware) 또는 javascript/typescript/rust/go/java/c/cpp(generic).
    mode:
      - 'obscene' (기본): 외설 어휘 치환 (NSFW 필터 트리거 → drop-from-corpus). sidecar 필요.
      - 'fpe'    : FF1 키-유도 format-preserving 암호화 (PROM 16 C1). **sidecar 불요** —
                   key+salt 만으로 복원. 출력은 유효 식별자(난수꼴, 외설 아님 → 마찰층).
                   file-level 결정론이라 파일 내 빈도 누출 (frequency-hiding 필요시 obscene).
    """
    if mode not in ("obscene", "fpe"):
        raise ValueError(f"알 수 없는 mode: {mode}")

    targets, names, is_py = _rename_targets(source, lang)
    if not (lang != "python" and lang in _lang.SPECS):
        lang = "python"

    name_map: dict[str, str] = {}
    if mode == "fpe":
        if key is None:
            raise ValueError("fpe 모드는 key 가 필요합니다 (매핑파일 없이 key+salt 로 복원)")
        fkey = _fpe.derive_key(key)
        valid = _fpe_validity(lang)
        for nm in names:
            if nm not in name_map:
                name_map[nm] = _fpe.fpe_encrypt_identifier(fkey, salt, nm, is_valid=valid)
    else:
        eff_seed = _derive_seed(key, salt, seed)
        used: set[str] = set()
        for nm in names:
            if nm not in name_map:
                name_map[nm] = _obscene_name(nm, eff_seed, used)

    locked = _apply(source, targets, name_map) if is_py else _apply_offsets(source, targets, name_map)

    meta: dict = {"version": META_VERSION, "salt": salt, "banner_text": None, "lang": lang, "mode": mode}
    if banner:
        bt = _banner_text(_derive_seed(key, salt, seed))
        locked = bt + "\n" + locked
        meta["banner_text"] = bt
    return LockResult(text=locked, mapping=name_map, meta=meta)


def unlock(
    locked_source: str,
    mapping: dict[str, str] | None = None,
    meta: dict | None = None,
    key: str | None = None,
    salt: str | None = None,
) -> str:
    """sexvoid -> network: 원본 식별자를 복원한다.

    obscene 모드: sidecar `mapping` 필요.
    fpe 모드: `key` + `salt` 로 복원 (매핑파일 불요). salt 는 명시 인자 > meta["salt"] 순.
        둘 다 없으면 *침묵 쓰레기 대신 ValueError* (audit HIGH 2026-06-08 — key-only 는 복원 불가).
    """
    meta = meta or {}
    text = locked_source
    banner_text = meta.get("banner_text")
    if banner_text and text.startswith(banner_text + "\n"):
        text = text[len(banner_text) + 1 :]
    lang = meta.get("lang", "python")
    mode = meta.get("mode", "obscene")

    targets, names, is_py = _rename_targets(text, lang)

    if mode == "fpe":
        if key is None:
            raise ValueError("fpe 모드 복원엔 key 가 필요합니다")
        fkey = _fpe.derive_key(key)
        eff_salt = salt if salt is not None else meta.get("salt")
        if eff_salt is None:
            raise ValueError(
                "fpe 복원엔 salt 가 필요합니다 (사이드카 meta 또는 명시 salt 인자). "
                "키만으로는 복원 불가 — 침묵 손상 방지 (audit HIGH 2026-06-08)."
            )
        valid = _fpe_validity(lang)
        rename = {nm: _fpe.fpe_decrypt_identifier(fkey, eff_salt, nm, is_valid=valid) for nm in set(names)}
    else:
        if mapping is None:
            raise ValueError("obscene 모드 복원엔 sidecar mapping 이 필요합니다")
        reverse = {v: k for k, v in mapping.items()}
        rename = {nm: reverse[nm] for nm in set(names) if nm in reverse}

    return _apply(text, targets, rename) if is_py else _apply_offsets(text, targets, rename)
