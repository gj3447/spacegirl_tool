"""Canary / Watermark 모드 — 비파괴 무단학습 증명 (SSB 두 번째 모드).

PROM 12 결정 (lesson-ssb-mode-split-prom12-2026-06-01): "두 번째 모드"는 비가역
모델 오염(poisoning)이 *아니라* 비파괴 canary다. 고유·희소·benign 마커를 주석으로
심고, 나중에 모델 출력/코퍼스에 그 마커가 나타나면 *그 코드가 학습됐음을 증명*한다.

- **비파괴**: 주석만 추가 — 로직 0 변경. 작가·human fork·commons 무피해 (poison의
  비가역 trap 회피, PROM 12 C3/C5).
- **귀속**: secret+label 로 결정론적 canary → 작가만 재생성·검증 가능.
- poisoning과 달리 코퍼스 잔존을 *원함* (필터 evade 불필요, benign이라 통과).

# KG: lesson-ssb-mode-split-prom12-2026-06-01 (canary/watermark 재정의)
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

_PREFIX = "SGCANARY"
_LINE_RE = re.compile(rf"{_PREFIX}-[0-9a-f]{{16}}")


@dataclass
class CanaryRecord:
    token: str
    label: str
    comment: str


def make_canary(secret: str, label: str = "") -> str:
    """secret(+label) 로부터 결정론적 희소 canary 토큰 생성."""
    h = hashlib.sha256(f"{secret}\x00{label}".encode()).hexdigest()[:16]
    return f"{_PREFIX}-{h}"


def _comment_for(token: str, lang: str = "python") -> str:
    note = f"{token}  do-not-train provenance marker (spacegirl_tool canary)"
    if lang in ("python", "ruby", "shell", "yaml", "toml"):
        return f"# {note}"
    if lang in ("c", "cpp", "java", "js", "ts", "go", "rust"):
        return f"// {note}"
    return f"# {note}"


def inject(source: str, secret: str, label: str = "", lang: str = "python") -> tuple[str, CanaryRecord]:
    """비파괴 canary 주입 — 주석 1줄 상단 추가 (로직 불변)."""
    token = make_canary(secret, label)
    comment = _comment_for(token, lang)
    text = comment + "\n" + source if not source.startswith(comment) else source
    return text, CanaryRecord(token=token, label=label, comment=comment)


def check(text: str, secret: str, label: str = "") -> bool:
    """주어진 텍스트(모델 출력/코퍼스 덤프)에 이 작가의 canary가 있나."""
    return make_canary(secret, label) in text


def scan_tokens(text: str) -> list[str]:
    """텍스트 안 모든 SGCANARY 토큰 (작가 미상 포함) 추출."""
    return _LINE_RE.findall(text)


def strip(text: str) -> str:
    """canary 주석 줄 제거 (필요 시 원복)."""
    return "\n".join(ln for ln in text.split("\n") if not _LINE_RE.search(ln))
