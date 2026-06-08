"""FF1 format-preserving encryption — SSB 가역성 메커니즘 축의 *sidecar-free* 백엔드.

PROM 16 권고 (C1·정정노트 line 70): SSB 의 가역 변환은 두 축으로 분리된다.
  - *무엇으로* (외설 어휘 = NSFW 트리거 → drop-from-corpus). word-level. ssb._obscene_name.
  - *어떻게 되돌리나* (가역성 메커니즘). char-level. **본 모듈**.

FF1 (NIST SP 800-38G) 은 *키+salt 로 가역 + 매핑파일 불필요 + 출력이 여전히 유효한 식별자/문자열*
을 동시에 만족한다. 외설 단어 치환과 달리 매핑 파일이 필요 없다 — 키+salt 만으로 unlock.
**salt 는 load-bearing**: 없으면 복원 불가하므로 호출부(ssb/cli)가 salt 를 명시 보관/전달해야 하며,
salt 부재 시 *침묵 쓰레기 대신 명시 에러* 를 내야 한다 (audit HIGH 2026-06-08).
대가: 결정론(동일이름→동일토큰)이라 파일 내 빈도 누출. frequency-hiding 이 필요하면
sidecar(obscene) 모드를 쓴다 (PROM 16 §2 det-vs-randomized tension).

**FF3/FF3-1 사용 금지** (Beyne 공격, NIST 2026-02 철회). FF1 만.
AES-128 을 round PRF 로 쓴다 (cryptography optional extra: `pip install spacegirl_tool[crypto]`).

핵심 불변식:
    decrypt(K, T, encrypt(K, T, X)) == X            (numeral / text / identifier 모두)
    encrypt 결과 식별자는 항상 유효한 식별자 (cycle-walking 으로 first-char digit 회피)

# KG: seed-ssb-ff1-fpe-engine-2026-06-01, lesson-ssb-crypto-method-prom16-2026-06-01
# longinus_layer 5 (Code -> KG)
"""

from __future__ import annotations

import hashlib
import hmac
import math
from collections.abc import Callable

try:  # AES via cryptography (optional [crypto] extra)
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    _HAVE_CRYPTO = True
except ImportError:  # pragma: no cover - exercised only without the extra
    _HAVE_CRYPTO = False


class FPEUnavailable(RuntimeError):
    """cryptography 가 없을 때 FPE 호출 시."""


def _require_crypto() -> None:
    if not _HAVE_CRYPTO:
        raise FPEUnavailable(
            "FF1 FPE 모드는 'cryptography' 가 필요합니다 — pip install 'spacegirl_tool[crypto]'"
        )


# ──────────────────────────────────────────────────────────────────────────
# AES primitives
# ──────────────────────────────────────────────────────────────────────────
def _aes_ecb_encrypt(key: bytes, block: bytes) -> bytes:
    enc = Cipher(algorithms.AES(key), modes.ECB()).encryptor()
    return enc.update(block) + enc.finalize()


def _prf(key: bytes, data: bytes) -> bytes:
    """NIST SP 800-38G PRF — AES-CBC-MAC (IV=0), data 는 16의 배수."""
    assert len(data) % 16 == 0
    y = b"\x00" * 16
    for i in range(0, len(data), 16):
        x = bytes(a ^ b for a, b in zip(y, data[i : i + 16]))
        y = _aes_ecb_encrypt(key, x)
    return y


# ──────────────────────────────────────────────────────────────────────────
# numeral-string helpers (base `radix`, most-significant first)
# ──────────────────────────────────────────────────────────────────────────
def _num(numerals: list[int], radix: int) -> int:
    x = 0
    for d in numerals:
        x = x * radix + d
    return x


def _num_bytes(b: bytes) -> int:
    return int.from_bytes(b, "big")


def _str_radix(x: int, m: int, radix: int) -> list[int]:
    out = [0] * m
    for i in range(m - 1, -1, -1):
        out[i] = x % radix
        x //= radix
    return out


# ──────────────────────────────────────────────────────────────────────────
# FF1 (NIST SP 800-38G, Algorithms 7 & 8)
# ──────────────────────────────────────────────────────────────────────────
def _ff1(key: bytes, tweak: bytes, numerals: list[int], radix: int, *, encrypt: bool) -> list[int]:
    _require_crypto()
    n = len(numerals)
    if n < 2:
        raise ValueError("FF1 requires numeral length >= 2")
    if not (radix**n >= 100):
        raise ValueError("FF1 domain too small: radix**len must be >= 100")

    t = len(tweak)
    u = n // 2
    v = n - u
    A = numerals[:u]
    B = numerals[u:]
    b = math.ceil(math.ceil(v * math.log2(radix)) / 8)
    d = 4 * math.ceil(b / 4) + 4

    P = (
        bytes([1, 2, 1])
        + radix.to_bytes(3, "big")
        + bytes([10, u % 256])
        + n.to_bytes(4, "big")
        + t.to_bytes(4, "big")
    )

    rounds = range(10) if encrypt else range(9, -1, -1)
    for i in rounds:
        # In decryption the halves swap roles each round (Algorithm 8).
        if encrypt:
            m = u if i % 2 == 0 else v
            other = B
        else:
            m = u if i % 2 == 0 else v
            other = A

        pad = (-t - b - 1) % 16
        Q = tweak + b"\x00" * pad + bytes([i]) + _num(other, radix).to_bytes(b, "big")
        R = _prf(key, P + Q)
        # S = first d bytes of R || AES(R xor [1]) || AES(R xor [2]) || ...
        S = bytearray(R)
        j = 1
        while len(S) < d:
            block = _num(_str_radix(j, 16, 256), 256)  # j as 16-byte big-endian
            xored = bytes(a ^ c for a, c in zip(R, block.to_bytes(16, "big")))
            S += _aes_ecb_encrypt(key, xored)
            j += 1
        S = bytes(S[:d])
        y = _num_bytes(S)

        if encrypt:
            c = (_num(A, radix) + y) % (radix**m)
            C = _str_radix(c, m, radix)
            A = B
            B = C
        else:
            # invert: B was set from A,B previously — undo
            c = (_num(B, radix) - y) % (radix**m)
            C = _str_radix(c, m, radix)
            B = A
            A = C
    return A + B


def encrypt_numerals(key: bytes, tweak: bytes, numerals: list[int], radix: int) -> list[int]:
    return _ff1(key, tweak, numerals, radix, encrypt=True)


def decrypt_numerals(key: bytes, tweak: bytes, numerals: list[int], radix: int) -> list[int]:
    return _ff1(key, tweak, numerals, radix, encrypt=False)


# ──────────────────────────────────────────────────────────────────────────
# key derivation
# ──────────────────────────────────────────────────────────────────────────
def derive_key(passphrase: str, info: str = "spacegirl-ff1") -> bytes:
    """passphrase → 16-byte AES-128 키 (HKDF-Extract+Expand, SHA-256)."""
    salt = b"spacegirl/ssb/fpe/v1"
    prk = hmac.new(salt, passphrase.encode("utf-8"), hashlib.sha256).digest()
    t = hmac.new(prk, info.encode("utf-8") + b"\x01", hashlib.sha256).digest()
    return t[:16]


def _tweak(salt: str) -> bytes:
    return hashlib.sha256(("ssb-fpe\x00" + salt).encode("utf-8")).digest()[:8]


# ──────────────────────────────────────────────────────────────────────────
# identifier-level FPE (charset bijection + cycle-walking)
# ──────────────────────────────────────────────────────────────────────────
# 인덱스 0..52 = 비-digit (a-z A-Z _), 53..62 = digit. 식별자 첫 글자는 < 53 이어야 유효.
_ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789"
_RADIX = len(_ALPHABET)  # 63
_NONDIGIT = 53  # _ALPHABET[:53] 은 모두 식별자 first-char 허용
_CHAR2IDX = {c: i for i, c in enumerate(_ALPHABET)}


def _keyed_perm(key: bytes, salt: str, size: int) -> list[int]:
    """key+salt 결정론 Fisher-Yates 순열 (길이-1 식별자용, reversible)."""
    perm = list(range(size))
    stream = b""
    counter = 0
    for i in range(size - 1, 0, -1):
        while len(stream) < 4:
            stream += hashlib.sha256(key + salt.encode() + counter.to_bytes(4, "big")).digest()
            counter += 1
        r = int.from_bytes(stream[:4], "big")
        stream = stream[4:]
        j = r % (i + 1)
        perm[i], perm[j] = perm[j], perm[i]
    return perm


def fpe_encrypt_identifier(
    key: bytes, salt: str, ident: str, is_valid: Callable[[str], bool] | None = None
) -> str:
    """식별자를 키-유도 FPE 로 잠근다 — 출력도 *유효·복호가능* 식별자, sidecar 불요.

    is_valid: 잠긴 출력이 unlock 이 *다시 수집·복호* 하는 유효 토큰인지 판정 (예: ssb._is_renamable).
      None 이면 ``str.isidentifier`` (digit-first 만 회피). cycle-walking 이 ¬is_valid 출력을 건너뛴다.
      **encrypt/decrypt 가 동일 is_valid 를 써야 가역** — 안 그러면 잠긴 토큰이 키워드/빌트인이 돼
      unlock 이 건너뛰고 round-trip 이 침묵 실패한다 (audit HIGH 2026-06-08, 예: K0->'as').
    """
    _require_crypto()
    if not ident or any(c not in _CHAR2IDX for c in ident):
        return ident  # 비-ASCII/빈 문자열은 손대지 않음 (정전: 표면 오염 한정)
    ok = is_valid if is_valid is not None else str.isidentifier
    tw = _tweak(salt)
    if len(ident) == 1:
        if _CHAR2IDX[ident] >= _NONDIGIT:  # 단일 digit 은 가역 식별자화 불가 → 무변환
            return ident
        perm = _keyed_perm(key, salt, _NONDIGIT)
        idx = _CHAR2IDX[ident]
        for _ in range(_NONDIGIT):  # perm cycle-walk (동일 is_valid 미러)
            idx = perm[idx]
            if ok(_ALPHABET[idx]):
                return _ALPHABET[idx]
        return _ALPHABET[idx]  # pragma: no cover - cycle 내 유효 원소 1개뿐 (x 자신)
    nums = [_CHAR2IDX[c] for c in ident]
    # cycle-walking: 출력이 유효·복호가능 식별자일 때까지 (digit-first ∧ 키워드/빌트인/dunder 회피)
    for _ in range(64):
        nums = encrypt_numerals(key, tw, nums, _RADIX)
        cand = "".join(_ALPHABET[i] for i in nums)
        if ok(cand):
            return cand
    return "".join(_ALPHABET[i] for i in nums)  # pragma: no cover - 64회 미수렴 ≈0


def fpe_decrypt_identifier(
    key: bytes, salt: str, locked: str, is_valid: Callable[[str], bool] | None = None
) -> str:
    """fpe_encrypt_identifier 의 역 — *동일* is_valid 로 cycle-walking 미러."""
    _require_crypto()
    if not locked or any(c not in _CHAR2IDX for c in locked):
        return locked
    ok = is_valid if is_valid is not None else str.isidentifier
    tw = _tweak(salt)
    if len(locked) == 1:
        if _CHAR2IDX[locked] >= _NONDIGIT:
            return locked
        perm = _keyed_perm(key, salt, _NONDIGIT)
        inv = {p: i for i, p in enumerate(perm)}
        idx = _CHAR2IDX[locked]
        for _ in range(_NONDIGIT):
            idx = inv[idx]
            if ok(_ALPHABET[idx]):
                return _ALPHABET[idx]
        return _ALPHABET[idx]  # pragma: no cover
    nums = [_CHAR2IDX[c] for c in locked]
    for _ in range(64):
        nums = decrypt_numerals(key, tw, nums, _RADIX)
        cand = "".join(_ALPHABET[i] for i in nums)
        if ok(cand):
            return cand
    return "".join(_ALPHABET[i] for i in nums)  # pragma: no cover


# ──────────────────────────────────────────────────────────────────────────
# text-payload FPE (문자열/주석 내용 — PROM C1 보조 용도)
# ──────────────────────────────────────────────────────────────────────────
def fpe_encrypt_text(key: bytes, salt: str, text: str, charset: str | None = None) -> str:
    """문자열/주석 payload 의 가역 암호화 (charset 내 문자만, 길이 보존)."""
    _require_crypto()
    cs = charset or _ALPHABET
    c2i = {c: i for i, c in enumerate(cs)}
    radix = len(cs)
    nums = [c2i[c] for c in text if c in c2i]
    if len(nums) < 2:
        return text
    enc = encrypt_numerals(key, _tweak(salt), nums, radix)
    it = iter(enc)
    return "".join(cs[next(it)] if c in c2i else c for c in text)


def fpe_decrypt_text(key: bytes, salt: str, text: str, charset: str | None = None) -> str:
    _require_crypto()
    cs = charset or _ALPHABET
    c2i = {c: i for i, c in enumerate(cs)}
    radix = len(cs)
    nums = [c2i[c] for c in text if c in c2i]
    if len(nums) < 2:
        return text
    dec = decrypt_numerals(key, _tweak(salt), nums, radix)
    it = iter(dec)
    return "".join(cs[next(it)] if c in c2i else c for c in text)
