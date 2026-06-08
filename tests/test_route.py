"""route 모드(ii) — 의미보존(identity) 라우팅 + 정당성 게이트 (PROM 16 D1/D2, 2026-06-08)."""

from __future__ import annotations

import pytest

from spacegirl import route

TOML = """
[endpoints.local]
base_url = "http://localhost:8000/v1"
model = "uncensored-7b"
permitted = true
note = "self-host"

[endpoints.locked]
base_url = "https://x/v1"
model = "m"
permitted = false
"""


def _eps(tmp_path):
    p = tmp_path / "endpoints.toml"
    p.write_text(TOML)
    return route.load_endpoints(p)


def test_load_endpoints(tmp_path):
    eps = _eps(tmp_path)
    assert eps["local"].permitted is True
    assert eps["local"].base_url == "http://localhost:8000/v1"
    assert eps["local"].model == "uncensored-7b"
    assert eps["locked"].permitted is False


def test_load_endpoints_missing_required(tmp_path):
    p = tmp_path / "bad.toml"
    p.write_text("[endpoints.x]\nbase_url='http://h/v1'\n")  # model 누락
    with pytest.raises(route.RouteError):
        route.load_endpoints(p)


def test_preflight_requires_permitted(tmp_path):
    eps = _eps(tmp_path)
    with pytest.raises(route.PreflightError):
        route.run_preflight(eps["locked"], age_attested=True, consent=True)


def test_preflight_requires_age_and_consent(tmp_path):
    eps = _eps(tmp_path)
    with pytest.raises(route.PreflightError):
        route.run_preflight(eps["local"], age_attested=False, consent=True)
    with pytest.raises(route.PreflightError):
        route.run_preflight(eps["local"], age_attested=True, consent=False)
    pf = route.run_preflight(eps["local"], age_attested=True, consent=True)
    assert pf.provenance["spacegirl_route"]["transform"] == "identity"
    assert pf.provenance["_unsigned"] is True  # provenance stub 정직 표기 유지


def test_route_is_identity_transform(tmp_path):
    """NSFW 의미를 *변형 없이* 그대로 엔드포인트로 — cloak/난독화 0 (D2 핵심)."""
    eps = _eps(tmp_path)
    captured = {}

    def fake_transport(url, headers, payload):
        captured["url"] = url
        captured["payload"] = payload
        captured["headers"] = headers
        return {"choices": [{"message": {"content": "ack"}}]}

    explicit = "explicit adult creative passage, verbatim and unmodified"
    content, pf = route.route_chat(
        eps["local"],
        [{"role": "user", "content": explicit}],
        age_attested=True,
        consent=True,
        transport=fake_transport,
    )
    assert content == "ack"
    # 콘텐츠가 *그대로* 전달됐는지 (identity — 잠금/치환/난독화 없음)
    assert captured["payload"]["messages"][0]["content"] == explicit
    assert captured["payload"]["model"] == "uncensored-7b"
    assert captured["url"] == "http://localhost:8000/v1/chat/completions"
    assert "Authorization" not in captured["headers"]  # self-host 무인증


def test_route_blocked_without_gates(tmp_path):
    eps = _eps(tmp_path)
    with pytest.raises(route.PreflightError):
        route.route_chat(
            eps["local"],
            [{"role": "user", "content": "x"}],
            age_attested=False,
            consent=True,
            transport=lambda *a: {"choices": [{"message": {"content": "should not reach"}}]},
        )


def test_route_bad_response_shape(tmp_path):
    eps = _eps(tmp_path)
    with pytest.raises(route.RouteError):
        route.route_chat(
            eps["local"],
            [{"role": "user", "content": "x"}],
            age_attested=True,
            consent=True,
            transport=lambda *a: {"unexpected": "shape"},
        )


def test_api_key_from_env(tmp_path, monkeypatch):
    p = tmp_path / "e.toml"
    p.write_text('[endpoints.k]\nbase_url="https://h/v1"\nmodel="m"\napi_key_env="SG_TEST_KEY"\npermitted=true\n')
    ep = route.load_endpoints(p)["k"]
    assert ep.api_key == ""  # 미설정
    monkeypatch.setenv("SG_TEST_KEY", "sekret")
    assert ep.api_key == "sekret"
