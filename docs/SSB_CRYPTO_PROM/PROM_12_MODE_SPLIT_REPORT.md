# PROM 12 — OQ1 결정: cloaking vs poisoning 모드 분리

> `/prom 12` (3 axis × 4 sub-axis). 2026-06-01.
> 결정 질문: **SSB를 cloaking(가역, drop-from-corpus 트리거) 과 poisoning(비가역, 학습셋 오염→모델 열화) 두 모드로 분리할 것인가, 어떻게?**
> 매트릭스: axis = {모드아키텍처(A) / poisoning효능·기법(B) / 윤리·법·역효과(C)} × sub-axis = {학술(1)/도구·사례(2)/함정(3)/2026트렌드(4)}.
> 선행: `PROM_16_REPORT.md` OQ1 + 씨앗 `seed-ssb-cloaking-vs-poisoning-explore-2026-06-01`.

---

## 결론 (한 줄)

**cloaking을 단일 default로 유지. poisoning을 같은 변환의 mode-flag로 박지 말 것 (필터 요구가 정반대 = 모순). "두 번째 모드"가 필요하면 비가역 모델 오염이 아니라 비파괴 canary/watermark(+ out-of-band opt-out)로 간다.**

---

## 1. Consensus (12셀 강수렴)

### C1. **결정적 모순: cloaking과 poisoning은 같은 파일에 *정반대* 필터 요구** (A1·A3 동의, HIGH — 이게 핵심)
- **cloaking**: 외설 식별자 → NSFW·toxicity 필터가 파일을 *flag → DROP* → 학습셋 미진입. *드롭된 파일은 오염 불가*.
- **poisoning**: 모델을 망치려면 파일이 필터를 *EVADE → 코퍼스 잔존 → 학습됨* 해야. 즉 *외설의 정반대(benign-looking)* 여야.
- ⟹ **외설로 둘 다 못 한다**. 외설 poison은 *자기파괴* — 외설 코드를 드롭하는 바로 그 필터가 poison을 제거. 두 모드는 분리 가능한 게 아니라 *artifact 수준에서 모순*. poison은 별도 codepath(benign 표면)여야지 외설 cloak 위의 flag가 될 수 없음.

### C2. **모드는 분리하되 — 산업 정전 = Glaze(default)/Nightshade(opt-in) 별도 도구** (A1·A2·A4 동의, HIGH)
- 같은 UChicago 연구실이 Glaze(방어, 가역, 항상-on)와 Nightshade(공격, poison)를 *별개 도구*로 출시 — 위협모델·consent 윤리·법적 blast radius가 달라서. 방어 도구에 파괴 payload 섞으면 *방어 용례의 깨끗한 법적 지위가 오염됨*.
- 권고: cloaking = safe default. poison = (만든다면) *별도 subcommand/바이너리, off-by-default, 명시 opt-in, 비가역·법적 경고*.

### C3. **개인 1-repo poisoning은 *falling bet* — 효능 천장 낮음** (B1·B3·B4 동의, MEDIUM-HIGH)
- *일반 열화*: 큰 코퍼스 분율 필요 → 1-repo는 rounding error. + 외설 poison은 필터에 제거(자기파괴).
- *타깃 백도어*: ~250 docs near-constant(Anthropic 2025)로 sample-count는 OK *그러나* 진짜 병목은 **데이터 접근**(실제로 스크랩되고 dedup/quality 필터 생존). 그리고 백도어는 *benign-looking*(외설 정반대)이어야 + 효과는 narrow trigger지 일반 steering 아님.
- 방어(dedup/perplexity/anomaly/spectral)가 개인보다 빠르게 강화 중.

### C4. **D-conflict(arXiv 2604.04289) 해소: 약한 단일 케이스, reframing이 무력화** (B2 동의, MEDIUM)
- "poisoned identifiers survive LLM deobfuscation"는 N=3-6 단일모델 case study고, **"write from scratch" reframing이 전파를 100%→20%(physics)/0%(pathfinding)로 떨굼**. 코퍼스-스케일 모델 열화 연구가 아님. → 견고한 일반 poison 근거 아님. 유일하게 cleaning 생존하는 건 *semantic in-distribution*(mislabeled docstring↔code)이지 외설 토큰 아님.

### C5. **윤리·법: poisoning = 공격적 비인가 손상(hack-back 유사), 비가역 trap, 평판 리스크** (C1·C2·C3·C4 동의, MEDIUM-HIGH)
- 능동 poisoning = 제3자 시스템 *비인가 impairment* (CFAA/UK CMA 노출, proportionality·verifiability 테스트 실패). 방어(Glaze=자기 자산 보호)와 *구조적으로 다름*.
- **비가역 trap**: poison된 repo는 *되돌릴 수 없음* — 작가 본인 + 정직한 human fork/dependent/commons까지 영구 오염. 스크래퍼와 사람을 구분 못 함.
- 평판: Nightshade/Nepenthes는 "virus/malware" 프레이밍 + OSS 백래시 받음(소송은 없었지만 부재≠면책).
- 2026 기후: EU AI Act opt-out + Bartz v. Anthropic $1.5B 합의 = **sabotage보다 opt-out/licensing 보상**.

---

## 2. Divergence

- **B1·B2 (효능 real) ↔ B3·B4·A3 (self-defeating·falling)**: 타깃 백도어는 *원리상* real(250 docs, mislabeled docstring cleaning 생존)이나 *외설 토큰으로는 불가*(필터 제거) + *1-repo 접근 병목*. 해소 = SSB poison으로 ship할 가치 없음. (외설 cloak과 benign 백도어는 다른 codepath.)

## 3. Open Questions (남김)

- **OQ1-a**: 비파괴 *canary/watermark* (CoProtector식 가역 watermark backdoor = 무단학습 *증명*용, 귀속/법적 증거, 모델 안 망침)를 "두 번째 모드"로 넣을지. ← poison의 deterrence 가치는 취하되 비가역성·법적 노출 없음. 유력 후보.
- **OQ1-b**: out-of-band opt-out(ai.txt/robots/C2PA)을 spacegirl_tool에 넣을지 별도 둘지 (PROM16 OQ3 = WE_FLYING_UP Phase 3와 동일 갈래).

## 4. 권장 결정 (OQ1 답)

| # | 결정 | 근거 |
|---|---|---|
| 1 | **cloaking = 단일 shipped default** (가역, drop-from-corpus, 외설=NSFW 트리거) | C1·C2·C5 |
| 2 | **poisoning을 같은 변환의 mode-flag로 박지 않음** (필터 요구 정반대 = 모순, mode-confusion) | C1 |
| 3 | "두 번째 모드"는 **비파괴 canary/watermark**(무단학습 증명·귀속) 로 — 비가역 모델 오염 아님 | C5·OQ1-a |
| 4 | 진짜 poison 모드는 (원한다면) **별도 opt-in 바이너리 + 비가역·법적 경고 + first-party 한정**, 단 개인 효능 낮음·법/평판 비용 큼 명시 | C2·C3·C5 |
| 5 | deterrence의 실제 teeth = **out-of-band opt-out/provenance**(ai.txt/C2PA) | C5 |
| 6 | EXPLORATION 씨앗 `seed-ssb-cloaking-vs-poisoning` → **RESOLVED (분리하되 poison은 비파괴 canary로 재정의)** | 전체 |

---

## 주요 1차 소스

- Glaze vs Nightshade (UChicago SAND Lab, 별개 도구): nightshade.cs.uchicago.edu/whatis.html
- Anthropic/UK-AISI/Turing 2025 *250 docs backdoor any size*: anthropic.com/research/small-samples-poison; arXiv:2510.07192
- *Stronger Data Poisoning Attacks Break Data Sanitization Defenses*, arXiv:1811.00741 (poison은 필터 evade 필요 — cloaking과 정반대)
- CoProtector (code watermark backdoor), arXiv:2110.12925
- *Poisoned Identifiers Survive LLM Deobfuscation*, arXiv:2604.04289 (D-conflict, reframing이 무력화)
- LightShed (USENIX Sec 2025), Honig ICLR 2025, Bartz v. Anthropic $1.5B, EU AI Act Art.4(3)/AIPREF

# KG: lesson-ssb-mode-split-prom12-2026-06-01, consensus-report-ssb-mode-split-prom12-2026-06-01
