"""sidecar 암호화 검증 — native 백엔드 round-trip + 변조/오류 감지."""

from __future__ import annotations

import json

import pytest

pytest.importorskip("cryptography")

from spacegirl import sidecar_crypto as sc  # noqa: E402

SAMPLE = json.dumps({"mapping": {"foo": "bar", "x": "y"}, "meta": {"lang": "python"}})


def test_native_roundtrip():
    env = sc.encrypt_native(SAMPLE, "correct horse battery staple")
    assert sc.MAGIC in env
    assert "foo" not in env  # 평문 누출 없음
    assert sc.decrypt_native(env, "correct horse battery staple") == SAMPLE


def test_wrong_passphrase_fails():
    env = sc.encrypt_native(SAMPLE, "right-key")
    with pytest.raises(sc.SidecarCryptoError):
        sc.decrypt_native(env, "wrong-key")


def test_tamper_detected():
    env = sc.encrypt_native(SAMPLE, "k")
    d = json.loads(env)
    import base64

    ct = bytearray(base64.b64decode(d["ciphertext"]))
    ct[0] ^= 0x01
    d["ciphertext"] = base64.b64encode(bytes(ct)).decode()
    with pytest.raises(sc.SidecarCryptoError):
        sc.decrypt_native(json.dumps(d), "k")


def test_dispatch_roundtrip():
    env = sc.encrypt_sidecar(SAMPLE, "pw", backend="native")
    assert sc.decrypt_sidecar(env, "pw") == SAMPLE


def test_fingerprint_stable_and_non_reversible():
    env1 = json.loads(sc.encrypt_native(SAMPLE, "same"))
    env2 = json.loads(sc.encrypt_native(SAMPLE, "same"))
    assert env1["fingerprint"] == env2["fingerprint"]  # 같은 키 식별
    assert env1["salt"] != env2["salt"]  # 매번 새 salt
    assert "same" not in env1["fingerprint"]
