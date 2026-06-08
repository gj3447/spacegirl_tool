"""FF1 FPE 검증 — NIST SP 800-38G 공식 테스트벡터 + round-trip 불변식.

NIST 벡터는 구현 정확성의 *empirical falsifier* (PROM 16 C1 grounding).
벡터 출처: NIST SP 800-38G, Appendix sample data (AES-128).
"""

from __future__ import annotations

import pytest

cryptography = pytest.importorskip("cryptography")

from spacegirl import fpe  # noqa: E402

KEY = bytes.fromhex("2B7E151628AED2A6ABF7158809CF4F3C")


def _to_numerals(s: str, alphabet: str) -> list[int]:
    idx = {c: i for i, c in enumerate(alphabet)}
    return [idx[c] for c in s]


def _from_numerals(nums: list[int], alphabet: str) -> str:
    return "".join(alphabet[i] for i in nums)


# ── NIST SP 800-38G FF1 sample vectors ────────────────────────────────────
def test_nist_sample1_radix10_empty_tweak():
    pt = _to_numerals("0123456789", "0123456789")
    ct = fpe.encrypt_numerals(KEY, b"", pt, 10)
    assert _from_numerals(ct, "0123456789") == "2433477484"
    assert fpe.decrypt_numerals(KEY, b"", ct, 10) == pt


def test_nist_sample2_radix10_with_tweak():
    tweak = bytes.fromhex("39383736353433323130")
    pt = _to_numerals("0123456789", "0123456789")
    ct = fpe.encrypt_numerals(KEY, tweak, pt, 10)
    assert _from_numerals(ct, "0123456789") == "6124200773"
    assert fpe.decrypt_numerals(KEY, tweak, ct, 10) == pt


def test_nist_sample3_radix36():
    alpha = "0123456789abcdefghijklmnopqrstuvwxyz"
    tweak = bytes.fromhex("3737373770717273373737")
    pt = _to_numerals("0123456789abcdefghi", alpha)
    ct = fpe.encrypt_numerals(KEY, tweak, pt, 36)
    assert _from_numerals(ct, alpha) == "a9tv40mll9kdu509eum"
    assert fpe.decrypt_numerals(KEY, tweak, ct, 36) == pt


# ── identifier-level FPE: round-trip + validity ───────────────────────────
@pytest.mark.parametrize(
    "ident",
    ["x", "ab", "foo", "calculate_total", "HTTPServer", "_private", "v2", "a1b2c3", "data_loader42"],
)
def test_identifier_roundtrip_and_validity(ident):
    key = fpe.derive_key("hunter2")
    locked = fpe.fpe_encrypt_identifier(key, "src/app.py", ident)
    assert locked.isidentifier(), f"{ident!r} -> {locked!r} not a valid identifier"
    assert fpe.fpe_decrypt_identifier(key, "src/app.py", locked) == ident


def test_identifier_keyed_and_salted():
    k1 = fpe.derive_key("key-A")
    k2 = fpe.derive_key("key-B")
    a = fpe.fpe_encrypt_identifier(k1, "f.py", "compute")
    b = fpe.fpe_encrypt_identifier(k2, "f.py", "compute")
    c = fpe.fpe_encrypt_identifier(k1, "g.py", "compute")
    assert a != b  # 다른 키 → 다른 결과
    assert a != c  # 다른 salt → 다른 결과 (frequency-hiding across files)


def test_identifier_sidecar_free():
    """매핑 파일 없이 키+salt 만으로 복원 가능해야 한다 (FPE 모드 본령)."""
    key = fpe.derive_key("secret")
    originals = ["handler", "request", "response", "x", "y"]
    locked = [fpe.fpe_encrypt_identifier(key, "mod.py", o) for o in originals]
    # mapping dict 없이 키만으로 복원
    restored = [fpe.fpe_decrypt_identifier(key, "mod.py", L) for L in locked]
    assert restored == originals


def test_text_payload_roundtrip():
    key = fpe.derive_key("pw")
    msg = "secret_message_in_a_string"
    enc = fpe.fpe_encrypt_text(key, "x", msg)
    assert enc != msg
    assert fpe.fpe_decrypt_text(key, "x", enc) == msg


def test_derive_key_deterministic_and_distinct():
    assert fpe.derive_key("a") == fpe.derive_key("a")
    assert fpe.derive_key("a") != fpe.derive_key("b")
    assert len(fpe.derive_key("a")) == 16


def test_identifier_is_valid_avoids_keywords_roundtrip():
    """is_valid 술어를 주면 cycle-walking 이 키워드/dunder 출력을 회피하고 가역 유지 (audit HIGH)."""
    import keyword as kwmod

    def ok(s: str) -> bool:
        return (
            s.isidentifier()
            and not kwmod.iskeyword(s)
            and not kwmod.issoftkeyword(s)
            and not (s.startswith("__") and s.endswith("__"))
        )

    key = fpe.derive_key("k")
    # 이전에 키워드/빌트인으로 충돌하던 2글자 식별자들 포함
    for ident in ["K0", "f9", "xy", "ab", "io", "cC", "eq", "Ub", "hV", "EP"]:
        locked = fpe.fpe_encrypt_identifier(key, "s", ident, is_valid=ok)
        assert ok(locked), f"{ident!r} -> {locked!r} not avoided"
        assert fpe.fpe_decrypt_identifier(key, "s", locked, is_valid=ok) == ident
