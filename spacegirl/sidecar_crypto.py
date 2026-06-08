"""sidecar 암호화 — 평문 매핑(`*.ssb.json`)은 *그 자체가 키* 이므로 절대 평문 커밋 금지.

PROM 16 C2 (HIGH): sidecar 매핑 유출 = 즉시 전체 해제. 모든 엔트로피는 소유자 키에.
sidecar 를 쓸 때는 **암호화** 하고 평문맵·키는 `.gitignore`, 암호화된 `.enc` 만 커밋.

두 백엔드:
  1. **native** (기본, 외부 바이너리 불요): scrypt(passphrase) → ChaCha20-Poly1305 AEAD.
     `cryptography` extra 필요.
  2. **sops/age** (있으면 shell-out): `sops --encrypt` / `age -p`. 팀 키관리·KMS 연동용.

self-describing 헤더(non-secret): KDF id / salt / nonce / fingerprint — 비밀 아님(Kerckhoffs).

# KG: seed-ssb-ff1-fpe-engine-2026-06-01 (sidecar SOPS+age 암호화), lesson-ssb-crypto-method-prom16-2026-06-01
# longinus_layer 5
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import subprocess

try:
    from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

    _HAVE_CRYPTO = True
except ImportError:  # pragma: no cover
    _HAVE_CRYPTO = False

MAGIC = "SSB-SIDECAR-ENC"
VERSION = 1
_SCRYPT_N = 2**15
_SCRYPT_R = 8
_SCRYPT_P = 1


class SidecarCryptoError(RuntimeError):
    pass


def _scrypt(passphrase: str, salt: bytes) -> bytes:
    maxmem = 128 * _SCRYPT_R * _SCRYPT_N * (_SCRYPT_P + 2)  # OpenSSL 기본 32MB 캡 회피
    return hashlib.scrypt(
        passphrase.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P, dklen=32, maxmem=maxmem
    )


def _fingerprint(passphrase: str) -> str:
    """비밀 아닌 키 지문 — 같은 키로 잠갔는지 식별만, 역산 불가."""
    return hashlib.sha256(b"ssb-fp\x00" + passphrase.encode("utf-8")).hexdigest()[:12]


# ── native backend (scrypt + ChaCha20-Poly1305) ──────────────────────────
def encrypt_native(plaintext: str, passphrase: str) -> str:
    if not _HAVE_CRYPTO:
        raise SidecarCryptoError("native 암호화는 'cryptography' 필요 — pip install 'spacegirl_tool[crypto]'")
    salt = os.urandom(16)
    nonce = os.urandom(12)
    key = _scrypt(passphrase, salt)
    ct = ChaCha20Poly1305(key).encrypt(nonce, plaintext.encode("utf-8"), MAGIC.encode())
    env = {
        "magic": MAGIC,
        "version": VERSION,
        "kdf": "scrypt",
        "kdf_params": {"n": _SCRYPT_N, "r": _SCRYPT_R, "p": _SCRYPT_P},
        "cipher": "chacha20poly1305",
        "salt": base64.b64encode(salt).decode(),
        "nonce": base64.b64encode(nonce).decode(),
        "fingerprint": _fingerprint(passphrase),
        "ciphertext": base64.b64encode(ct).decode(),
    }
    return json.dumps(env, ensure_ascii=False, indent=2) + "\n"


def decrypt_native(envelope: str, passphrase: str) -> str:
    if not _HAVE_CRYPTO:
        raise SidecarCryptoError("native 복호화는 'cryptography' 필요")
    env = json.loads(envelope)
    if env.get("magic") != MAGIC:
        raise SidecarCryptoError("not a native SSB sidecar envelope")
    salt = base64.b64decode(env["salt"])
    nonce = base64.b64decode(env["nonce"])
    ct = base64.b64decode(env["ciphertext"])
    key = _scrypt(passphrase, salt)
    try:
        pt = ChaCha20Poly1305(key).decrypt(nonce, ct, MAGIC.encode())
    except Exception as e:  # InvalidTag 등
        raise SidecarCryptoError(f"복호화 실패 (틀린 passphrase 또는 변조): {e}") from e
    return pt.decode("utf-8")


# ── sops / age backends (optional shell-out) ──────────────────────────────
def have_sops() -> bool:
    return shutil.which("sops") is not None


def have_age() -> bool:
    return shutil.which("age") is not None


def encrypt_age(plaintext: str, passphrase: str) -> bytes:
    """age -p (passphrase) 암호화. age 바이너리 필요."""
    if not have_age():
        raise SidecarCryptoError("age 바이너리 없음 (https://github.com/FiloSottile/age)")
    # age 의 passphrase 입력은 TTY 우선이라 -p 모드는 비대화형에서 까다롭다.
    # 권장 경로: age recipient 키파일. passphrase 모드는 native 백엔드 사용 권고.
    raise SidecarCryptoError(
        "age passphrase 모드는 비대화형 자동화에 부적합 — native 백엔드 사용 권고. "
        "팀 키관리는 `age -r <recipient>` recipient 모드를 직접 사용하라."
    )


def encrypt_sops(plaintext_json: str) -> str:
    """sops --encrypt (환경의 age/KMS 키 사용). .sops.yaml 설정 필요."""
    if not have_sops():
        raise SidecarCryptoError("sops 바이너리 없음 (https://github.com/getsops/sops)")
    proc = subprocess.run(
        ["sops", "--encrypt", "--input-type", "json", "--output-type", "json", "/dev/stdin"],
        input=plaintext_json.encode("utf-8"),
        capture_output=True,
    )
    if proc.returncode != 0:
        raise SidecarCryptoError(f"sops 실패: {proc.stderr.decode(errors='replace')}")
    return proc.stdout.decode("utf-8")


def decrypt_sops(envelope: str) -> str:
    if not have_sops():
        raise SidecarCryptoError("sops 바이너리 없음")
    proc = subprocess.run(
        ["sops", "--decrypt", "--input-type", "json", "--output-type", "json", "/dev/stdin"],
        input=envelope.encode("utf-8"),
        capture_output=True,
    )
    if proc.returncode != 0:
        raise SidecarCryptoError(f"sops 복호화 실패: {proc.stderr.decode(errors='replace')}")
    return proc.stdout.decode("utf-8")


# ── high-level dispatch ───────────────────────────────────────────────────
def encrypt_sidecar(plaintext: str, passphrase: str, backend: str = "native") -> str:
    """sidecar 평문 → 암호화 봉투. backend: native(기본) | sops."""
    if backend == "native":
        return encrypt_native(plaintext, passphrase)
    if backend == "sops":
        return encrypt_sops(plaintext)
    raise SidecarCryptoError(f"알 수 없는 backend: {backend}")


def decrypt_sidecar(envelope: str, passphrase: str = "") -> str:
    """암호화 봉투 → 평문. native/sops 자동 판별."""
    stripped = envelope.lstrip()
    if stripped.startswith("{"):
        try:
            head = json.loads(envelope)
        except json.JSONDecodeError:
            head = {}
        if head.get("magic") == MAGIC:
            return decrypt_native(envelope, passphrase)
        if "sops" in head:
            return decrypt_sops(envelope)
    raise SidecarCryptoError("인식 못 한 sidecar 봉투 형식")
