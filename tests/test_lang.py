"""다언어 백엔드 — round-trip identity + 문자열/주석/멤버접근 보존."""

from __future__ import annotations

import textwrap

import pytest

from spacegirl import lang, ssb, surface

JS = textwrap.dedent(
    '''
    // compute average — keep this comment intact
    function average(numbers) {
      const total = numbers.reduce((acc, n) => acc + n, 0);
      const label = "average value";  // string "numbers" must survive
      return Math.floor(total / numbers.length);
    }
    '''
).strip()

RUST = textwrap.dedent(
    '''
    /* block comment with average keyword inside */
    fn double_values(values: &[i32]) -> Vec<i32> {
        let label = "values list";
        values.iter().map(|x| x * 2).collect()
    }
    '''
).strip()

GO = textwrap.dedent(
    '''
    package main
    func Sum(nums []int) int {
        total := 0
        for _, n := range nums {
            total += n
        }
        return total
    }
    '''
).strip()


@pytest.mark.parametrize("src,lang_name", [(JS, "javascript"), (RUST, "rust"), (GO, "go")])
def test_roundtrip(src, lang_name):
    r = ssb.lock(src, key="k", salt="f", lang=lang_name)
    assert ssb.unlock(r.text, r.mapping, r.meta) == src
    assert r.meta["lang"] == lang_name


def test_strings_and_comments_preserved_js():
    r = ssb.lock(JS, lang="javascript")
    # 주석 텍스트와 문자열 리터럴은 오염되지 않음
    assert "keep this comment intact" in r.text
    assert '"average value"' in r.text  # 문자열 리터럴 내부 단어 보존
    # 멤버 접근(.reduce/.length)의 멤버명은 보존 (전역 Math는 멤버 아니라 치환됨)
    assert ".reduce(" in r.text and ".length" in r.text


def test_keywords_not_renamed_rust():
    r = ssb.lock(RUST, lang="rust")
    assert r.text.startswith("/* block comment")  # 주석 보존
    for kw in ("fn", "let"):  # rust 샘플은 implicit return (return 키워드 없음)
        assert r.text.count(kw) >= 1


def test_identifier_def_obfuscated_js():
    r = ssb.lock(JS, key="k", salt="f", lang="javascript")
    # 함수 정의 줄에서 함수명이 오염됨 (문자열 리터럴의 "average"는 별개로 보존)
    def_line = [ln for ln in r.text.split("\n") if ln.startswith("function ")][0]
    assert "average" not in def_line
    assert "average" in r.mapping


def test_lang_for_path():
    assert lang.lang_for_path("foo.js") == "javascript"
    assert lang.lang_for_path("foo.rs") == "rust"
    assert lang.lang_for_path("foo.py") == "python"
    assert lang.lang_for_path("foo.unknown") == "python"


def test_surface_roundtrip_nonpython():
    r = ssb.lock(JS, key="k", salt="f", lang="javascript")
    s = surface.apply_surface(r)
    assert surface.has_homoglyphs(s.text) > 0
    assert ssb.unlock(s.text, s.mapping, s.meta) == JS


# TPA-D3 fix: template literal ${...} 내부 식별자도 치환
def test_js_template_literal_identifiers_cloaked():
    src = "const greet = (name) => `Hello ${name}, total ${name.length}`;\n"
    r = ssb.lock(src, key="k", salt="f", lang="javascript")
    # 정적 텍스트 "Hello"는 보존, ${} 안 name 은 오염
    assert "Hello " in r.text
    assert "${name}" not in r.text  # template 내부 식별자 치환됨
    assert ".length" in r.text  # 멤버명은 보존
    assert ssb.unlock(r.text, r.mapping, r.meta) == src


# TPA-D2 fix: 도구가 자기 소스를 LOCKED로 오판하지 않음 (self-scan FP)
def test_wall_does_not_flag_tool_own_source():
    from pathlib import Path

    from spacegirl import wall

    pkg = Path(ssb.__file__).parent
    for mod in ("vocab.py", "ssb.py", "wall.py", "lang.py"):
        rep = wall.scan((pkg / mod).read_text(encoding="utf-8"))
        assert rep.verdict != "LOCKED", f"{mod} false-positive: {rep}"
