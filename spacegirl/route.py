"""route.py — 모드(ii): *의미보존* 라우팅 (PROM 16 D1/D2, 2026-06-08).

스페이스걸 의의 = 의미·문맥을 *살린 채* 그레이트월을 넘는 것. SSB 잠금(모드 i)은 의미를
*파괴* 해 학습 코퍼스서 drop 시키는 정반대 도구다. 모드(ii)는 그 의의를 직접 구현한다:

  벽을 부수지 말고, 벽이 없는 곳으로 보낸다.

NSFW 의미를 *난독화 없이*(identity transform) 허용된(무검열·self-host) OpenAI-호환
엔드포인트로 라우팅한다. cloak 변환을 *전혀* 재사용하지 않는다.

근거 (PROM 16):
  - A1/A4: 적응형 동급 LLM 필터를 의미보존한 채 통과시키는 건 *구조적으로 불가능*
    (secure steganography = 공유키 필요; 무키 동급이면 복원자가 디코드하는 걸 필터도 디코드).
    → 제3자 안전필터를 "뚫는" 변환은 제공하지 않는다.
  - D2: permitted 엔드포인트엔 in-path 적대필터가 없으므로 올바른 변환은 *항등*.
    가치는 변환이 아니라 *라우팅 + 동의/provenance 오케스트레이션*.
  - B3/C6: 내구 정당성층 = 동의·연령·provenance (법/사회/귀속). 암호가 아님.

# KG: PROM-16-spacegirl-greatwall-crossing-2026-06-08,
#     rf-prom16-spacegirl-greatwall-D2-2026-06-08, rf-prom16-spacegirl-greatwall-C5-2026-06-08
# longinus_layer 5 (Code -> KG)
"""

from __future__ import annotations

import json
import os
import tomllib
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from . import optout

DEFAULT_TIMEOUT = 120


class RouteError(RuntimeError):
    """라우팅 일반 오류."""


class PreflightError(RouteError):
    """동의/연령/permitted 게이트 미통과 — 내구 정당성층 (B3/C6)."""


@dataclass
class EndpointSpec:
    """허용(permitted) 엔드포인트 명세 — self-host 무검열 모델 등 (PROM 16 B1/B2)."""

    name: str
    base_url: str  # OpenAI-호환 base, 예: http://dgx:8000/v1
    model: str
    api_key_env: str = ""  # 키가 든 환경변수명 (self-host 무인증이면 빈 값)
    permitted: bool = False  # 운영자가 *성인 콘텐츠 허용* 을 명시 확인했는가 (D2: 가정 금지)
    note: str = ""

    @property
    def api_key(self) -> str:
        return os.environ.get(self.api_key_env, "") if self.api_key_env else ""


def load_endpoints(path: str | Path) -> dict[str, EndpointSpec]:
    """endpoints.toml 로드. [endpoints.<name>] 테이블당 EndpointSpec 하나."""
    p = Path(path)
    if not p.exists():
        raise RouteError(f"endpoints 설정 없음: {p}")
    data = tomllib.loads(p.read_text(encoding="utf-8"))
    table = data.get("endpoints", {})
    out: dict[str, EndpointSpec] = {}
    for name, cfg in table.items():
        if "base_url" not in cfg or "model" not in cfg:
            raise RouteError(f"endpoint '{name}': base_url 와 model 은 필수")
        out[name] = EndpointSpec(
            name=name,
            base_url=str(cfg["base_url"]).rstrip("/"),
            model=str(cfg["model"]),
            api_key_env=str(cfg.get("api_key_env", "")),
            permitted=bool(cfg.get("permitted", False)),
            note=str(cfg.get("note", "")),
        )
    return out


@dataclass
class Preflight:
    """라우팅 전 통과해야 하는 정당성 게이트 (잠금이 아니라 *이게* teeth)."""

    age_attested: bool = False  # 운영자 18+ 성인 확인
    consent: bool = False  # 콘텐츠 사용/처리 동의 확보
    provenance: dict = field(default_factory=dict)  # C2PA-식 출처 stamp


def run_preflight(endpoint: EndpointSpec, *, age_attested: bool, consent: bool, contact: str = "") -> Preflight:
    """동의/연령/permitted 게이트. 실패 시 PreflightError (침묵 통과 금지)."""
    if not endpoint.permitted:
        raise PreflightError(
            f"endpoint '{endpoint.name}' 는 permitted=false. 성인 콘텐츠 허용을 명시 확인한 "
            "(self-host/무검열) 엔드포인트만 사용하라 — 제3자 안전필터 우회 금지 (PROM 16 A1/D2)."
        )
    if not age_attested:
        raise PreflightError("연령 확인 필요 (--age-attest): 성인(18+) 콘텐츠 처리 게이트 (B3).")
    if not consent:
        raise PreflightError("동의 필요 (--consent): 콘텐츠 처리 동의 게이트 (B3).")
    prov = optout.c2pa_manifest(contact=contact, as_json=False)
    prov["spacegirl_route"] = {
        "endpoint": endpoint.name,
        "model": endpoint.model,
        "transform": "identity",  # D2: 의미보존 = 난독화 0
        "age_attested": True,
        "consent": True,
    }
    return Preflight(age_attested=True, consent=True, provenance=prov)


def build_chat_payload(endpoint: EndpointSpec, messages: list[dict], **opts) -> dict:
    """OpenAI-호환 chat.completions 페이로드 — *콘텐츠는 변형 없이 그대로* (identity)."""
    payload = {"model": endpoint.model, "messages": messages}
    payload.update(opts)
    return payload


def _http_post_json(url: str, headers: dict, payload: dict, timeout: int = DEFAULT_TIMEOUT) -> dict:
    """stdlib urllib POST (zero-dep). 네트워크 경계 — 테스트는 transport 주입으로 우회."""
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (신뢰 base_url)
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:  # pragma: no cover - 네트워크 의존
        raise RouteError(f"엔드포인트 HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:200]}") from e
    except urllib.error.URLError as e:  # pragma: no cover
        raise RouteError(f"엔드포인트 연결 실패: {e.reason}") from e


def route_chat(
    endpoint: EndpointSpec,
    messages: list[dict],
    *,
    age_attested: bool,
    consent: bool,
    contact: str = "",
    transport: Callable[[str, dict, dict], dict] | None = None,
    **opts,
) -> tuple[str, Preflight]:
    """preflight → identity 라우팅 → 응답 텍스트.

    transport(url, headers, payload)->dict 주입 가능(테스트/대체 클라이언트). 기본=urllib.
    반환: (assistant 응답 텍스트, Preflight[provenance 포함]).
    """
    pf = run_preflight(endpoint, age_attested=age_attested, consent=consent, contact=contact)
    payload = build_chat_payload(endpoint, messages, **opts)
    url = f"{endpoint.base_url}/chat/completions"
    headers = {}
    if endpoint.api_key:
        headers["Authorization"] = f"Bearer {endpoint.api_key}"
    call = transport or _http_post_json
    resp = call(url, headers, payload)
    try:
        content = resp["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise RouteError(f"엔드포인트 응답 형식 예상 밖: {str(resp)[:200]}") from e
    return content, pf
