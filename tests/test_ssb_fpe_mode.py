"""ssb FPE 모드 검증 — sidecar-free round-trip + 코드 유효성 + 모드 직교성."""

from __future__ import annotations

import ast

import pytest

pytest.importorskip("cryptography")

from spacegirl import ssb  # noqa: E402

PY = """\
import math

def calculate_total(items, tax_rate):
    subtotal = sum(item.price for item in items)
    return subtotal * (1 + tax_rate)

class OrderProcessor:
    def process(self, order):
        return calculate_total(order, 0.1)
"""

JS = """\
function calculateTotal(items, taxRate) {
  const subtotal = items.reduce((acc, it) => acc + it.price, 0);
  return subtotal * (1 + taxRate);  // tax applied
}
"""


def test_fpe_python_sidecar_free_roundtrip():
    r = ssb.lock(PY, key="my-secret", salt="app.py", mode="fpe")
    assert r.meta["mode"] == "fpe"
    # 매핑 없이 key 만으로 복원
    restored = ssb.unlock(r.text, mapping=None, meta=r.meta, key="my-secret")
    assert restored == PY


def test_fpe_locked_is_valid_python():
    r = ssb.lock(PY, key="k", salt="x", mode="fpe")
    ast.parse(r.text)  # 잠긴 코드도 파싱 가능해야 (식별자 유효)


def test_fpe_generic_js_roundtrip():
    r = ssb.lock(JS, key="k", salt="m.js", lang="javascript", mode="fpe")
    restored = ssb.unlock(r.text, meta=r.meta, key="k")
    assert restored == JS


def test_fpe_wrong_key_does_not_restore():
    r = ssb.lock(PY, key="right", salt="a.py", mode="fpe")
    bad = ssb.unlock(r.text, meta=r.meta, key="wrong")
    assert bad != PY


def test_fpe_requires_key():
    with pytest.raises(ValueError):
        ssb.lock(PY, mode="fpe")  # key 없음


def test_obscene_mode_still_default_and_sidecar_based():
    r = ssb.lock(PY, key="k", salt="a.py")
    assert r.meta["mode"] == "obscene"
    assert r.mapping  # 매핑 존재
    assert ssb.unlock(r.text, r.mapping, r.meta) == PY


def test_fpe_changes_identifiers():
    r = ssb.lock(PY, key="k", salt="a.py", mode="fpe")
    assert "calculate_total" not in r.text
    assert "OrderProcessor" not in r.text
    # import 된 이름은 보존 (실행 안 깨짐)
    assert "math" in r.text


# ── audit HIGH 회귀 (2026-06-08) ──────────────────────────────────────────
def test_fpe_no_keyword_collision_roundtrip():
    """잠긴 식별자가 키워드/빌트인이 되어 round-trip 이 침묵 실패하면 안 된다.

    이전엔 짧은 식별자 ~0.2% 가 키워드(as/in/if...)로 암호화돼 (a) 코드가 비-파싱이 되고
    (b) unlock 이 그 토큰을 건너뛰어 복원 실패했다 (audit HIGH, K0->'as').
    """
    import keyword as kwmod

    names = [a + b for a in "abcdefgh" for b in "ABCDEFGH"]  # 64개 2글자 식별자
    src = "\n".join(f"def {n}(z): return z" for n in names) + "\n"
    r = ssb.lock(src, key="k", salt="s", mode="fpe")
    ast.parse(r.text)  # 잠긴 코드도 유효 파이썬
    for tok in r.mapping.values():
        assert not kwmod.iskeyword(tok) and not kwmod.issoftkeyword(tok), f"{tok!r} is keyword"
        assert not (tok.startswith("__") and tok.endswith("__")), f"{tok!r} is dunder"
    assert ssb.unlock(r.text, meta=r.meta, key="k") == src


def test_fpe_unlock_requires_salt_no_silent_corruption():
    """사이드카(=salt) 없이 fpe 복원 시 침묵 쓰레기 대신 명시 에러 (audit HIGH)."""
    r = ssb.lock(PY, key="k", salt="app.py", mode="fpe")
    meta_no_salt = {kk: vv for kk, vv in r.meta.items() if kk != "salt"}
    with pytest.raises(ValueError):
        ssb.unlock(r.text, meta=meta_no_salt, key="k")
    # 명시 salt 를 주면 정상 복원 (key+salt 가 비밀)
    assert ssb.unlock(r.text, meta=meta_no_salt, key="k", salt="app.py") == PY


def test_fpe_explicit_salt_overrides_meta():
    r = ssb.lock(PY, key="k", salt="real.py", mode="fpe")
    # 틀린 salt → 복원 실패 / 맞는 salt → 성공 (salt 가 load-bearing 임을 입증)
    assert ssb.unlock(r.text, meta=r.meta, key="k", salt="wrong.py") != PY
    assert ssb.unlock(r.text, meta=r.meta, key="k", salt="real.py") == PY
