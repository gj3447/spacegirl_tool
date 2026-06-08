"""다언어 식별자 토크나이저 백엔드.

Python은 `ssb` 가 `tokenize`+`ast`(최고 충실도)로 처리하고, 그 외 언어는 본 모듈의
*문자열·주석 인식 char-walker* 가 식별자 span을 추출한다. 로직 보존 + sidecar 가역은
Python 경로와 동일 (offset 치환).

지원: javascript / typescript / rust / go / java / c / cpp.
가역성 불변식은 언어 무관 (sidecar 매핑). 단 *cross-module 실행* 보장은 안 함
(같은 파일 내 일관 치환만 — 정전 정신: 표면 오염, 의미 보존).

# KG: lesson-ssb-crypto-method-prom16-2026-06-01 (anti-counter-attack 다언어 mixing)
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Unicode-aware: 키릴 homoglyph 가 섞인 식별자(surface 층)도 매치해야 unlock 가역.
# 시작=letter/underscore/$ (digit 제외), 이어짐=word char/$.
_IDENT_RE = re.compile(r"[^\W\d][\w$]*|\$[\w$]*", re.UNICODE)
# 식별자 앞이 이 문자면 멤버/경로 접근 → 치환 제외 (.x  ::x  ->x)
_SKIP_PREV = frozenset({".", ":", ">"})


@dataclass(frozen=True)
class LangSpec:
    name: str
    keywords: frozenset[str]
    line_comment: tuple[str, ...] = ()
    block_comment: tuple[tuple[str, str], ...] = ()
    string_delims: tuple[str, ...] = ('"', "'")
    raw_string_delims: tuple[str, ...] = ()  # e.g. ` for JS template


_C_FAMILY_BLOCK = (("/*", "*/"),)
_C_FAMILY_LINE = ("//",)

_JS_KW = frozenset(
    "break case catch class const continue debugger default delete do else export extends "
    "finally for function if import in instanceof new return super switch this throw try typeof "
    "var void while with yield let static async await of as from get set null true false undefined".split()
)
_TS_KW = _JS_KW | frozenset(
    "interface type enum implements public private protected readonly abstract namespace declare "
    "is keyof infer never unknown any number string boolean object".split()
)
_RUST_KW = frozenset(
    "as break const continue crate dyn else enum extern false fn for if impl in let loop match mod "
    "move mut pub ref return self Self static struct super trait true type unsafe use where while "
    "async await macro_rules".split()
)
_GO_KW = frozenset(
    "break case chan const continue default defer else fallthrough for func go goto if import "
    "interface map package range return select struct switch type var nil true false iota".split()
)
_JAVA_KW = frozenset(
    "abstract assert boolean break byte case catch char class const continue default do double else "
    "enum extends final finally float for goto if implements import instanceof int interface long "
    "native new package private protected public return short static strictfp super switch "
    "synchronized this throw throws transient try void volatile while true false null var record".split()
)
_C_KW = frozenset(
    "auto break case char const continue default do double else enum extern float for goto if int "
    "long register return short signed sizeof static struct switch typedef union unsigned void "
    "volatile while inline restrict _Bool bool true false NULL".split()
)
_CPP_KW = _C_KW | frozenset(
    "class namespace template typename public private protected virtual override final new delete "
    "this nullptr using friend operator explicit constexpr noexcept mutable throw try catch "
    "dynamic_cast static_cast const_cast reinterpret_cast".split()
)

SPECS: dict[str, LangSpec] = {
    "javascript": LangSpec("javascript", _JS_KW, _C_FAMILY_LINE, _C_FAMILY_BLOCK, ('"', "'"), ("`",)),
    "typescript": LangSpec("typescript", _TS_KW, _C_FAMILY_LINE, _C_FAMILY_BLOCK, ('"', "'"), ("`",)),
    "rust": LangSpec("rust", _RUST_KW, _C_FAMILY_LINE, _C_FAMILY_BLOCK, ('"',)),
    "go": LangSpec("go", _GO_KW, _C_FAMILY_LINE, _C_FAMILY_BLOCK, ('"', "'"), ("`",)),
    "java": LangSpec("java", _JAVA_KW, _C_FAMILY_LINE, _C_FAMILY_BLOCK, ('"', "'")),
    "c": LangSpec("c", _C_KW, _C_FAMILY_LINE, _C_FAMILY_BLOCK, ('"', "'")),
    "cpp": LangSpec("cpp", _CPP_KW, _C_FAMILY_LINE, _C_FAMILY_BLOCK, ('"', "'")),
}

# 확장자 → lang
EXT_MAP: dict[str, str] = {
    ".py": "python", ".js": "javascript", ".mjs": "javascript", ".cjs": "javascript",
    ".ts": "typescript", ".tsx": "typescript", ".jsx": "javascript",
    ".rs": "rust", ".go": "go", ".java": "java",
    ".c": "c", ".h": "c", ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp", ".hpp": "cpp",
}


def lang_for_path(path: str) -> str:
    for ext, lang in EXT_MAP.items():
        if path.endswith(ext):
            return lang
    return "python"


def _last_significant(text: str, i: int) -> str:
    j = i - 1
    while j >= 0 and text[j] in " \t":
        j -= 1
    return text[j] if j >= 0 else ""


def extract_identifiers(source: str, spec: LangSpec) -> list[tuple[int, int, str]]:
    """문자열·주석을 건너뛰고 (start, end, name) 식별자 span 목록 반환 (absolute offset)."""
    out: list[tuple[int, int, str]] = []
    i, n = 0, len(source)
    line_c = sorted(spec.line_comment, key=len, reverse=True)
    block_c = spec.block_comment
    strings = spec.string_delims + spec.raw_string_delims
    raw = spec.raw_string_delims
    while i < n:
        ch = source[i]
        # line comment
        matched = False
        for lc in line_c:
            if source.startswith(lc, i):
                nl = source.find("\n", i)
                i = n if nl == -1 else nl
                matched = True
                break
        if matched:
            continue
        # block comment
        for op, cl in block_c:
            if source.startswith(op, i):
                end = source.find(cl, i + len(op))
                i = n if end == -1 else end + len(cl)
                matched = True
                break
        if matched:
            continue
        # template literal (backtick) — 리터럴은 건너뛰되 ${...} 내부 식별자는 추출
        if ch == "`" and "`" in raw:
            i += 1
            while i < n and source[i] != "`":
                if source[i] == "\\":
                    i += 2
                    continue
                if source.startswith("${", i):
                    depth, j = 1, i + 2
                    while j < n and depth > 0:
                        if source[j] == "{":
                            depth += 1
                        elif source[j] == "}":
                            depth -= 1
                        j += 1
                    expr = source[i + 2 : j - 1]
                    for s, e, nm in extract_identifiers(expr, spec):
                        out.append((i + 2 + s, i + 2 + e, nm))
                    i = j
                    continue
                i += 1
            i += 1  # 닫는 backtick
            continue
        # string literal (escape-aware)
        if ch in strings:
            i += 1
            while i < n:
                if source[i] == "\\":
                    i += 2
                    continue
                if source[i] == ch:
                    i += 1
                    break
                i += 1
            continue
        # identifier
        if ch.isalpha() or ch in "_$":
            m = _IDENT_RE.match(source, i)
            if m:
                name = m.group(0)
                start, end = m.start(), m.end()
                if name not in spec.keywords and _last_significant(source, start) not in _SKIP_PREV:
                    out.append((start, end, name))
                i = end
                continue
        i += 1
    return out
