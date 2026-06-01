"""v0.2 — keyed salt / banner / surface / canary / optout 테스트.

핵심 불변식 유지: 모든 잠금 조합에 대해 round-trip identity.
"""

from __future__ import annotations

import textwrap

from spacegirl import canary, optout, ssb, surface

SAMPLE = textwrap.dedent(
    '''
    import math

    def average(numbers):
        total = sum(numbers)
        return math.floor(total / len(numbers))


    class Counter:
        def __init__(self):
            self.count = 0

        def tick(self, by=1):
            self.count = self.count + by
            return self.count
    '''
).strip()


# ---- keyed salt ----

def test_keyed_roundtrip():
    r = ssb.lock(SAMPLE, key="s3cret", salt="path/to/file.py")
    assert ssb.unlock(r.text, r.mapping, r.meta) == SAMPLE


def test_per_file_salt_differs():
    a = ssb.lock(SAMPLE, key="k", salt="a.py")
    b = ssb.lock(SAMPLE, key="k", salt="b.py")
    # 같은 식별자가 파일마다 다른 토큰 (frequency-hiding)
    assert a.mapping["average"] != b.mapping["average"]


def test_key_required_for_reproduction():
    a = ssb.lock(SAMPLE, key="k1", salt="x")
    b = ssb.lock(SAMPLE, key="k2", salt="x")
    assert a.mapping != b.mapping


# ---- banner (Bo NSFW trigger, reversible) ----

def test_banner_injected_and_reversible():
    r = ssb.lock(SAMPLE, banner=True)
    assert r.meta["banner_text"] is not None
    assert r.text.startswith(r.meta["banner_text"])
    assert ssb.unlock(r.text, r.mapping, r.meta) == SAMPLE


def test_banner_trips_wall_scan():
    from spacegirl import wall

    r = ssb.lock(SAMPLE, banner=True)
    assert wall.scan(r.text).verdict == "LOCKED"


# ---- surface (homoglyph, reversible via sidecar) ----

def test_surface_roundtrip():
    r = ssb.lock(SAMPLE, key="k", salt="f")
    s = surface.apply_surface(r)
    assert surface.has_homoglyphs(s.text) > 0
    assert ssb.unlock(s.text, s.mapping, s.meta) == SAMPLE


def test_surface_plus_banner_roundtrip():
    r = ssb.lock(SAMPLE, key="k", salt="f", banner=True)
    s = surface.apply_surface(r)
    assert ssb.unlock(s.text, s.mapping, s.meta) == SAMPLE


# ---- canary (non-destructive watermark) ----

def test_canary_injection_is_non_destructive():
    text, rec = canary.inject(SAMPLE, secret="mysecret", label="repoA")
    # 주석만 추가 — 원본이 그대로 포함
    assert SAMPLE in text
    # 코드 로직 동일하게 실행
    ns: dict = {}
    exec(text, ns)  # noqa: S102
    assert ns["average"]([2, 4, 6]) == 4


def test_canary_check_matches_only_right_secret():
    text, rec = canary.inject(SAMPLE, secret="mysecret", label="repoA")
    assert canary.check(text, "mysecret", "repoA") is True
    assert canary.check(text, "wrong", "repoA") is False
    assert canary.check(SAMPLE, "mysecret", "repoA") is False


def test_canary_strip():
    text, rec = canary.inject(SAMPLE, secret="s")
    assert canary.strip(text).strip() == SAMPLE


# ---- optout (out-of-band do-not-train) ----

def test_robots_blocks_known_ai_crawlers():
    txt = optout.robots_txt()
    assert "GPTBot" in txt and "ClaudeBot" in txt
    assert "Disallow: /" in txt


def test_ai_txt_declares_optout():
    txt = optout.ai_txt(contact="me@example.com")
    assert "train-ai=n" in txt and "me@example.com" in txt


def test_notrain_header_comment_form():
    py = optout.notrain_header(lang="python")
    assert py.startswith("#") and "DO-NOT-TRAIN" in py
    c = optout.notrain_header(lang="rust")
    assert c.startswith("/*")
