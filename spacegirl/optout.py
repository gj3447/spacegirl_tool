"""Out-of-band opt-out — Do-Not-Train 신호 생성 (SSB 진짜 teeth).

PROM 12/16 결정: 내구 보호는 기술 cloak이 아니라 *법·provenance·consent* 층에 산다
(EU AI Act Art.4(3), ai.txt/robots, C2PA, Bartz v. Anthropic $1.5B = sabotage보다
opt-out/licensing 보상). 본 모듈은 그 *machine-readable 거부 신호*를 만든다.

생성물: robots.txt(AI 크롤러 Disallow) / ai.txt(opt-out DSL) / NOTRAIN 소스 헤더.

# KG: lesson-ssb-mode-split-prom12-2026-06-01 (C5 out-of-band opt-out = teeth)
"""

from __future__ import annotations

# 알려진 AI 학습 크롤러 user-agent (2025-2026). 망라 아님 — 갱신 대상.
AI_CRAWLERS: list[str] = [
    "GPTBot",
    "OAI-SearchBot",
    "ChatGPT-User",
    "ClaudeBot",
    "Claude-Web",
    "anthropic-ai",
    "Google-Extended",
    "Applebot-Extended",
    "CCBot",
    "Bytespider",
    "Amazonbot",
    "PerplexityBot",
    "Meta-ExternalAgent",
    "FacebookBot",
    "Diffbot",
    "ImagesiftBot",
    "cohere-ai",
    "Timpibot",
]


def robots_txt(crawlers: list[str] | None = None) -> str:
    """AI 학습 크롤러를 Disallow 하는 robots.txt 블록."""
    crawlers = crawlers or AI_CRAWLERS
    lines = ["# spacegirl_tool — AI training opt-out (do-not-train)"]
    for ua in crawlers:
        lines.append(f"User-agent: {ua}")
        lines.append("Disallow: /")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def ai_txt(contact: str = "", policy_url: str = "") -> str:
    """ai.txt 스타일 opt-out 선언 (TDM rights reservation 정신)."""
    lines = [
        "# ai.txt — Text & Data Mining rights reservation (spacegirl_tool)",
        "# 본 저작물은 AI 학습 사용을 거부합니다 (opt-out / do-not-train).",
        "User-Agent: *",
        "Disallow: /",
        "Content-Usage: ai=n; tdm=n; train-ai=n; train-genai=n",
    ]
    if contact:
        lines.append(f"Contact: {contact}")
    if policy_url:
        lines.append(f"Policy: {policy_url}")
    return "\n".join(lines) + "\n"


def notrain_header(lang: str = "python", contact: str = "") -> str:
    """소스 파일 상단에 박는 do-not-train 헤더 주석."""
    body = [
        "DO-NOT-TRAIN / AI 학습 거부 (spacegirl_tool opt-out)",
        "This file reserves text-and-data-mining rights. No AI training.",
        "Content-Usage: ai=n; train-ai=n",
    ]
    if contact:
        body.append(f"Contact: {contact}")
    if lang in ("c", "cpp", "java", "js", "ts", "go", "rust"):
        inner = "\n".join(f" * {b}" for b in body)
        return f"/*\n{inner}\n */\n"
    inner = "\n".join(f"# {b}" for b in body)
    return inner + "\n"
