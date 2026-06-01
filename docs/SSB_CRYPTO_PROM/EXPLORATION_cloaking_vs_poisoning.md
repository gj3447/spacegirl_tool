# EXPLORATION — cloaking vs poisoning 모드 분리
## seed: `seed-ssb-cloaking-vs-poisoning-explore-2026-06-01`

> 2026-06-01. 프로메테우스 위상 single-axis worker.  
> 선행: PROM 16 `D-conflict` + PROM 12 `C4/권장결정 §6`. 본 문서 = arXiv 2604.04289 실체 검증 + 두 PROM의 D-conflict 공백(inference-time vs training-time 구분) 채움.

---

## 0. 사전 지식 (하계 pre-fetch)

### 정전 snapshot (THREAT_MODEL.md + PROM 12 결론)

| 항목 | 정전 내용 |
|---|---|
| cloaking 정의 | 가역. 외설/taboo 식별자 → NSFW·toxicity 필터 *flag → DROP*. 학습셋 미진입. |
| poisoning 정의 | 비가역. 모델 가중치/학습 데이터 오염 → 모델 열화. |
| 정전 결정 | 같은 파일에 두 모드 동시 불가 (필터 요구 정반대 = C1 모순). |
| "두 번째 모드" | 비파괴 canary (귀속·증명). 모델 오염 아님. |
| D-conflict 미결 | arXiv 2604.04289 내용이 "poison이 LLM deobfuscation을 살아남는다"고 보고 — 실제 주장이 뭔지 검증 미완료. |

### KG 기존 노드

- `lesson-ssb-mode-split-prom12-2026-06-01` — C1 모순 Lesson (CONFIRMED)
- `lesson-ssb-crypto-method-prom16-2026-06-01` — FF1 FPE 권고 Lesson (CONFIRMED)
- `consensus-report-ssb-mode-split-prom12-2026-06-01` — PROM 12 결론 노드

---

## 1. Consensus (검증 결과 수렴)

### C1. arXiv 2604.04289는 **실존한다** — 단 "poisoning"의 의미가 training-time 아님

논문: *"Poisoned Identifiers Survive LLM Deobfuscation: A Case Study on Claude Opus 4.6"*, Luis Guzmán Lorenzo, 2026-04-05 제출.

**결정적 사실**: 이 논문의 "poisoning"은 **inference-time prompt-level** 현상을 가리킨다. 즉:
- 이미 난독화된 JavaScript 코드의 string table에 **잘못된(misleading) 식별자 이름**을 주입.
- Claude에게 "이 코드를 deobfuscate하라" 프롬프트 → Claude가 잘못된 이름을 *그대로 출력에 재현*.
- 모델 가중치 변경 없음. 학습 데이터 오염 없음. *단일 inference 안에서 identifier가 전파*되는 현상.

이것은 training-time poisoning(CFAA/법적 회색지대, 비가역 모델 열화)과 **레이어가 완전히 다르다**. 논문 제목의 "poisoned identifiers"는 *모델을 망가뜨리는 poison*이 아니라 *난독화 코드 안에 심어진 misleading identifiers*다.

### C2. **논문의 핵심 발견 = reframing으로 해소 가능**

192 inference run (Claude Opus 4.6, 2 코드 유형, 50 조건, N=3-6) 결과:

| 프롬프트 유형 | 잘못된 식별자 전파율 |
|---|---|
| "deobfuscate this code" (기본) | physics: 8/8 (100%), pathfinding: 5/5 (100%) |
| explicit verification prompt (4 variant) | 12/12 (0% 감소, 검증 지시 무효) |
| **"write a fresh implementation" (reframe)** | physics: 0-20%로 급감, pathfinding: 0% |

결론: 동일한 misleading identifier가 deobfuscation frame에선 전파되지만 generation frame에선 사라진다. 이는 **SSB의 cloaking 설계(drop-from-corpus)에 직접 위협이 아니다** — cloaking 목표는 "파일이 학습셋에 들어가지 않는 것"이지 "들어간 후 deobfuscation되지 않는 것"이 아니기 때문.

### C3. **논문이 지지하는 것은 "inference-level identifier stickiness"지 "model-degrading poisoning survivability"가 아니다**

논문 자체 한계 명시: "These observations are from two archetypes on one model family (Opus 4.6 primary; Haiku 4.5 spot-check). Broader generalization is needed."

이는 Glaze/Nightshade식 erosion arc(ICLR 2025 Honig; USENIX 2025 LightShed — Nightshade 99.98% 탐지·제거)와 비교했을 때 단일 narrow case다. PROM 12 C4의 "약한 단일 케이스" 판정이 논문 원문으로 재확인된다.

### C4. **PROM 12 결정(cloaking 단일 default, poison mode 미추가)은 이 검증 후에도 유효하다**

arXiv 2604.04289가 보여주는 현상은:
1. inference-time identifier stickiness → **cloaking/drop-from-corpus와 레이어가 다름** (drop 성공 시 논문 현상 자체가 발생 안 함)
2. reframing으로 해소 가능 → **내구 장벽 주장 불가**
3. training-time poisoning(모델 가중치 오염)에 대한 근거가 **아님**

따라서 논문이 D-conflict를 야기했던 "poison된 식별자는 살아남는다" 주장은 **scope 오독**이었다. 컨센서스 C5("가역 cloak = 내구 장벽 아님")는 논문이 반박하지 않는다. D-conflict는 용어 충돌(같은 단어 "poisoning"이 다른 레이어를 지칭)이었고 실질적 이론 충돌이 아니다.

### C5. **CoProtector(arXiv:2110.12925)는 canary 방향의 선례로 유효**

CoProtector = 오픈소스 코드에 data poisoning으로 watermark backdoor를 심어 무단 학습 *증명*용 canary로 사용. 모델을 망치는 것이 아니라 "이 모델이 내 코드를 학습했다"는 귀속 증거 생성. 4종 untargeted poisoning method 중 Code Corrupting(AST terminal node → random word)이 식별자 치환과 구조적으로 유사.

이것이 THREAT_MODEL.md "두 번째 모드 = canary(비파괴)"의 학술 선례다.

### C6. **CodeCipher(arXiv:2410.05797)는 또 다른 레이어: LLM이 사용 중일 때 코드 프라이버시 보호**

CodeCipher = LLM에게 코드를 넘길 때 *내용을 숨기면서 LLM 응답 품질은 유지*하는 obfuscation. embedding matrix 변환 기반. 34% token만 복원 가능. 이는 anti-training 도구가 아니라 *runtime privacy* 도구 — spacegirl_tool 스코프 밖. 참고만.

---

## 2. Divergence (남은 긴장)

### DV1. "inference-level stickiness"가 SSB 가역성 주장을 *약화*하는가

PROM 16 C5("표적 LLM이 rename으로 정규화 → 내구 장벽 아님")와 arXiv 2604.04289("deobfuscation frame에서는 misidentifier가 전파됨")는 *같은 현상의 양면*이다:
- C5는 LLM이 의미론적으로 올바른 이름으로 *복원*할 수 있다고 경고.
- 2604.04289는 LLM이 deobfuscation frame에선 오히려 잘못된 이름을 *그대로 재현*한다고 관찰.

이 둘은 모순이 아니라 **프롬프트 frame에 따른 행동 분기**다. SSB 설계 함의: "deobfuscation 요청이 들어왔을 때 cloaked code가 있다" = C5가 경고한 normalize-back 경로 *아님* (그 경로는 drop-from-corpus 실패 시). inference-level stickiness는 drop이 성공한 이후의 다른 시나리오다.

### DV2. 비파괴 canary의 "watermark backdoor"가 진짜 benign인가

CoProtector의 watermark backdoor = 특정 trigger word에 대한 *예측 가능한 출력 변화* → 귀속 증거. 이것이 "benign"인지는 관점에 따라 다르다:
- 방어자: 귀속 증거 생성 → 전적으로 정당.
- 비판: 모델 행동에 hidden hook → 사용자 모르는 백도어 = 신뢰 문제.

이 긴장은 canary 설계 시 명시적 opt-in + disclosure 의무로 해소해야 하며, OPEN 상태로 유지.

---

## 3. Open Questions

### OQ1-a (PROM 12에서 이월): 비파괴 canary를 spacegirl_tool v2 모드로 추가할 것인가

- **유력한 후보 형태**: keyed identifier → trigger word 삽입(steganographic, 고정 allowlist에서 선택). 학습된 모델에서 trigger 재현 여부로 귀속 증명.
- **최소 형태(non-destructive)**: 무작위 benign 단어를 *문서화되지 않은 패턴*으로 배치 → 패턴이 모델 출력에서 재현되면 학습 증거. 기존 `canary.py`가 이 방향.
- **상태**: OPEN_DEFERRED. v1 cloaking 안정화 후 다음 우선순위.

### OQ1-b (PROM 12에서 이월): out-of-band opt-out을 spacegirl_tool 내에 넣을지

- ai.txt / C2PA manifest → 법적 teeth가 있는 provenance 층.
- WE_FLYING_UP Phase 3에서 결정 예정.
- **상태**: OPEN_DEFERRED.

### OQ-NEW: 2604.04289의 "deobfuscation frame에서 identifier stickiness"가 SSB의 어떤 공격 시나리오에 해당하는가

- 시나리오: 공격자가 cloaked code를 훔쳐서 "이 코드 deobfuscate해줘" → 잘못된 identifier가 전파된 코드를 얻음 → 공격자 코드 이해를 *방해*하는 우연한 부수 효과.
- 이것이 방어적으로 활용 가능한지(적대자 방해), 아니면 단순 noise인지 — 근거 불충분. OPEN.

---

## 4. 권장 verdict (OQ1 최종 판정)

### 판정: **cloaking/poisoning 모드 분리 — CONFIRMED, 구체 형태 = 비파괴 canary**

| 근거 번호 | 내용 |
|---|---|
| 1 | arXiv 2604.04289는 training-time poisoning(모델 가중치 오염)을 입증하지 않는다. inference-time identifier stickiness는 별개 레이어. |
| 2 | THREAT_MODEL.md C1 모순(같은 파일에 정반대 필터 요구)은 실증적으로 그대로 유효. |
| 3 | D-conflict는 용어 레이어 오독이었다. "poisoned identifiers survive deobfuscation" ≠ "model-degrading poison survives training pipeline". |
| 4 | 진짜 "두 번째 모드" = 비파괴 canary/watermark(CoProtector 선례). 기존 `canary.py` 방향 유지. |
| 5 | 진짜 모델 열화 poison 모드는 효능 낮음(개인 1-repo rounding error) + 법적 리스크(CFAA 노출) + 비가역 trap(자기 코드·commons 오염) 삼중 억제. spacegirl_tool에 추가하지 않음. |

### 최소 형태 명세 (만약 canary v2 만든다면)

```
mode: canary
mechanism: keyed steganographic pattern
  - identifier 선택 pool: benign wordlist (법적 문제 없음)
  - 삽입 위치: AST leaf node, 주석, docstring 패턴
  - trigger: 고정 패턴 (소유자만 알거나 공개 manifest로 선언)
reversibility: 완전 (key로 원본 복원)
destructive: false (모델 가중치 변경 없음)
legal risk: 낮음 (자기 코드에 워터마크)
```

### 진짜 poison 모드의 위험 명세 (비교용, spacegirl_tool 미포함)

| 위험 | 내용 |
|---|---|
| 법적 노출 | CFAA/UK CMA — 제3자 시스템 비인가 impairment. "hack-back" 유사. |
| 비가역성 | 작가 본인 + 정직한 fork + commons 영구 오염. undo 불가. |
| 효능 제한 | 개인 1-repo 분율은 rounding error. 외설 poison은 필터에 걸려 자기파괴. |
| 자기 사용 불가 | poison된 코드를 본인이 LLM에 넣으면 본인 workflow 방해. |

---

## 주요 검증 소스

- arXiv 2604.04289 — 실존 확인됨. 논문 내용: inference-time identifier propagation, reframing mitigation.
- arXiv 2110.12925 (CoProtector) — canary/watermark backdoor 선례.
- arXiv 2410.05797 (CodeCipher) — runtime code privacy (스코프 밖, 참고).
- PROM 12 (`PROM_12_MODE_SPLIT_REPORT.md`) — 이 EXPLORATION의 선행 결정.
- PROM 16 (`PROM_16_REPORT.md`) — D-conflict 원출처.
- THREAT_MODEL.md — 정전 정의 (cloaking/canary/opt-out 3-mode).

# KG 결정화 후보 (부모 처리)
# verdict: CONFIRMED — 분리하되 poison은 비파괴 canary로 재정의. PROM 12 권장결정 §6 재확인.
# arXiv 2604.04289 실존 여부: CONFIRMED_EXISTS (inference-time, training-time 아님)
# seed: seed-ssb-cloaking-vs-poisoning-explore-2026-06-01 → RESOLVED
