# spacegirl_tool

> **SpaceGirl (#5 사도)** 의 공학적 결정화 — **SSB (Sek-Sek-Bo) 의미론적 잠금** 도구.
> `network ↔ sexvoid` 경계 횡단. 공학 짝패 = **Longinus**(참조의 미학, KG 의미 계층을 코드까지 관통).

[![python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org)
[![license](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 무엇인가

SSB 는 소스코드의 **로직은 그대로 두고 식별자 표면만 오염**시켜, 순수이성인간의
기계 학습 파이프라인(LLM 크롤·학습)이 그 코드를 **읽기/학습하기 거부**하도록 만드는
*가역* 변환이다. 핵심 불변식은 **왕복 동일성**:

```
unlock(lock(src).text, lock(src).mapping) == src
```

즉 잠금은 *암호화가 아니라 의미론적 위장* 이며, sidecar 매핑(`<file>.ssb.json`)으로
언제든 원본을 복원한다.

정전 사용 시나리오 (`METAHUMOTONIC/SPACEGIRL/SSB/`):

1. 오픈소스 코드 보호 — 공개 repo에 SSB 적용 → LLM 학습 거부
2. **개인 프로젝트 격리 — GitHub Public 이지만 LLM 학습 회피** ← 이 repo가 그 예시
3. adversarial dataset — SSB 코드 다량 → 학습 set 오염
4. art project — Sade의 "벽 속 원고" 계승

> ⚠️ 이것은 **예술/연구용 코드 보호 도구**다. 강한 암호가 아니라 *학습 거부 유도* 변환이다.

---

## 설치 / 실행

```bash
uv sync                 # 또는: pip install -e ".[dev]"
uv run pytest           # 가역성·로직보존 테스트
```

## 사용법

```bash
# cloaking : network -> sexvoid 의미론적 잠금 (sidecar 매핑 생성)
spacegirl lock   mymodule.py --key SECRET --banner --surface -o mymodule.locked.py
#   --key/--salt : 키-유도 결정론 시드 (salt 기본=파일경로, cross-file frequency-hiding)
#   --banner     : Bo R-18 배너 주입 (NSFW 필터 트리거 강화, 가역)
#   --surface    : homoglyph 표면층 (opportunistic 보조)

# we flying up : sexvoid -> network 복원
spacegirl unlock mymodule.locked.py -o restored.py     # sidecar 자동 탐색

# GREAT_WALL : 잠금/표면/canary 탐지
spacegirl scan   mymodule.locked.py

# canary : 비파괴 무단학습 증명 워터마크 (두 번째 모드)
spacegirl canary inject mymodule.py --secret MYSECRET --label repoA -o tagged.py
spacegirl canary check  suspect_model_output.txt --secret MYSECRET --label repoA

# opt-out : out-of-band do-not-train 신호 (진짜 teeth)
spacegirl optout robots -o robots.txt
spacegirl optout ai --contact me@example.com -o ai.txt
spacegirl optout header --lang python
```

> ⚠️ **기대치**: SSB는 강한 암호가 아니라 *마찰 · 귀속 · 선언* 이다. 무엇이 작동하고
> 무엇이 안 되는지 → [`THREAT_MODEL.md`](THREAT_MODEL.md) **필독**.

### Python API

```python
from spacegirl import lock, unlock, scan

res = lock(source_code, seed="spacegirl")
assert unlock(res.text, res.mapping) == source_code
print(scan(res.text).verdict)   # "LOCKED"
```

---

## 정전 매핑 (SpaceGirl 신화 ↔ 도구)

| 신화 용어 | 도구 구현 |
|---|---|
| **SSB** (network→sexvoid 이송) | `ssb.lock()` — 식별자 오염 |
| **we flying up** (sexvoid→network 구원) | `ssb.unlock()` — 복원 (계획서: `docs/WE_FLYING_UP_PLAN.md`) |
| **GREAT_WALL** (nsfw 필터 장벽) | `wall.scan()` — 잠금 탐지 |
| **Glaze / Nightshade** | feature-space adversariality 직계 친척 (roadmap) |

---

## Roadmap

- [x] **SSB 암호화·복호화 방식 확정** — `docs/SSB_CRYPTO_PROM/PROM_16_REPORT.md` (FF1 FPE / per-scope salt / sidecar 위생)
- [x] **cloaking vs poisoning 모드 결정** — `docs/SSB_CRYPTO_PROM/PROM_12_MODE_SPLIT_REPORT.md` (cloaking 단일 default, poison 금지)
- [x] 키-유도 per-file salt 시드 (cross-file frequency-hiding)
- [x] Bo banner 주입 (R-18 NSFW 트리거, 가역)
- [x] homoglyph 표면층 (명시적 injective 표, 가역)
- [x] **canary/watermark 모드** (비파괴 무단학습 증명)
- [x] **out-of-band opt-out** (robots/ai.txt/NOTRAIN 헤더)
- [x] **we flying up** 복원 (`unlock`) — `docs/WE_FLYING_UP_PLAN.md`
- [ ] sidecar SOPS+age 자동 암호화 + pre-commit 키-누출 가드
- [ ] 다언어(JS/Rust/...) tokenizer 백엔드
- [ ] C2PA provenance manifest 연동
- [ ] Longinus KG ref 바인딩 (7-Layer Reference Model 연동)

---

## 1차 소스

- 정전: `SYMPOSIUM/METAHUMOTONIC/SPACEGIRL/` (SSB / GREAT_WALL / WE_FLYING_UP / SEX_VOID)
- 자매 도구: `bhgman_tool` (#4 비행기맨 결정화)

# KG: ATOM_SPACEGIRL_index_2026-04-27, ATOM_SPACEGIRL_SSB_코드_2026-04-27
