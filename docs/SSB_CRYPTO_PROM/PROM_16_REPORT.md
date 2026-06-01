# PROM 16 — SSB 암호화·복호화 방식 설계

> `/prom 16` (4 axis × 4 sub-axis = 16 cell). 2026-06-01.
> 문제: **로직 보존 코드의 식별자 의미론적 잠금(anti-LLM-training)을 어떻게 가역 변환으로 구현할 것인가.**
> 산출: spacegirl_tool SSB 엔진의 암호화/복호화 방식 권고.
> 매트릭스: axis = {변환방식론(A) / 복원·키관리(B) / 토크나이저·표면attack(C) / 적대강건성(D)} × sub-axis = {학술(1) / 도구(2) / 함정(3) / 2026트렌드(4)}.

---

## 0. 사전 지식 (KG pre-fetch)

KG에 SSB-crypto 관련 ResearchFinding 없음 (기존 "SSB" 노드는 물리학 electroweak SSB — 무관). 신규 도메인. v0.1 엔진 = 식별자 토큰 치환 + sidecar 매핑 (round-trip identity 6 pytest PASS) — 본 PROM이 그 *방식 자체*를 평가/대체 권고.

---

## 1. Consensus (16셀 중 강수렴)

### C1. **변환 방식 = 키-유도 FPE(FF1)가 이론적 sweet spot** (A1·A2·B1·B4 동의, HIGH)
세 후보 — (1) sidecar 매핑 / (2) 키-유도 결정론 변환 / (3) 진짜 암호화(AES) — 중,
**NIST SP 800-38G FF1 (format-preserving encryption)** 이 *키만으로 가역 + sidecar 불필요 + 출력이 여전히 유효한 식별자(컴파일됨)* 를 동시 만족.
- AES(3)는 ciphertext가 식별자가 아니라 base64 blob → 코드 깨짐. *문자열/주석 payload 에만* 한정 사용.
- **FF3/FF3-1 사용 금지**: Beyne 공격으로 NIST가 2026-02 FF3 철회. **FF1만** 사용.
- 단 FPE는 *작은 도메인(짧은 식별자)에서 약함* — 1-3자 이름은 패딩/도메인 확장 필요.

### C2. **매핑/키 = 유일한 비밀. 소유자-facing 파국을 설계 기준으로** (A1·A2·B2·B3·B4 동의, HIGH)
- sidecar 매핑은 *그 자체가 평문 키* — 유실 = 영구 복원불가 / 유출 = 즉시 전체 해제.
- 따라서 **모든 엔트로피는 소유자 보유 키에**. sidecar를 쓰면 **SOPS+age로 암호화**하고 평문맵+키는 `.gitignore` (암호화된 `.enc`만 커밋). 공개 repo엔 cloaked 코드만, 키는 절대 동봉 금지.
- **default = 결정론(seed 유도, 멱등·재현가능 CI 친화)** + **per-scope salt** (아래 C3) + age/passkey BYOK 복구 + *비밀 아닌 self-describing 헤더*(KDF id, salt, key fingerprint). 토큰 단위 revoke 필요할 때만 randomized-stored-map.

### C3. **순수 결정론은 빈도/구조 누출 → per-scope salt로 randomize + AST 정합성** (A3·B1 동의, HIGH)
동일이름→동일토큰(global deterministic)은 빈도분석·call-graph 구조로 재식별됨 (deterministic encryption frequency leak / source de-anonymization, Horlboge PoPETs 2024: k-anonymous source code는 계산불가). → occurrence별 per-scope salt로 frequency-hiding. 변환은 **scope-aware + cross-file consistent + import/attribute 보존 bijection**이어야 파싱·복원 둘 다 성립. 목표 = *비용 상승(억지)*, 암호적 비밀 아님 (Kerckhoffs).

### C4. **표면 attack(homoglyph/zero-width)은 보조일 뿐 — load-bearing 금지** (C1·C2·C3·C4 동의, HIGH)
- 가역 안전한 것만: insertion-class(zero-width/bidi/tag) = 고정 allowlist strip으로 무손실 역산 / homoglyph = *명시적 injective 표* (NFKC 아님 — NFKC는 lossy·detection-only, Cyrillic/Greek homoglyph 못 되돌림).
- 그러나 표면 cloak은 *poison이 아니라 strip됨* — 3개 chokepoint(NFKC 데이터정제 / post-Trojan-Source 툴체인 GCC -Wbidi-chars·CodeQL / BPE byte-fallback)에서 학습 전 제거. **half-life 짧음**. 표면은 legacy 미정규화 scraper용 opportunistic 층으로만.

### C5. **핵심 진실: 가역 cloak = 소유자 가역 ⟺ 공격자 가역. 의미 잠금은 내구 장벽이 아니라 마찰/귀속** (D1·D2·D3·D4 강수렴, HIGH)
- Glaze/Nightshade식 가역 feature-space cloak은 *이미지에서도 경험적으로 깨짐* (Honig ICLR 2025; LightShed USENIX 2025 — Nightshade 99.98% 탐지·제거). 코드는 더 나쁨(이산 validity 제약 → imperceptible 예산 없음).
- **표적이 되는 그 LLM이 바로 cloak을 정규화함**: "이 외설 식별자들을 합리적 이름으로 rename" → 의미 보존 복원 (Neural Variable Name Repair). 외설-refusal은 abliterated 모델이 무력화.
- ⟹ SSB의 실제 가치 = **마찰(저노력 scraper 차단) + 귀속 증거(워터마크/canary) + 예술적 선언**. 내구 보호는 *법·라이선스·provenance* 층(C2PA, ai.txt/robots, Do-Not-Train 옵트아웃 레지스트리)에 산다. 2026 컨센서스: 기술 cloaking은 arms race 패배 → 법/provenance로 이주.

### C6. **권고 아키텍처 = 2층 (가역 cloak + out-of-band consent)** (A2·A4·D2·D4 동의, MEDIUM-HIGH)
1. **In-artifact 가역 cloak**: FF1 FPE 식별자(per-scope salt, AST-aware) — 마찰 + 선언. 소유자는 키로 un-cloak.
2. **Out-of-band provenance/consent**: C2PA식 manifest + ai.txt/robots Do-Not-Train 신호 — *진짜 teeth*.
3. (옵션) repo 경계 tarpit/decoy(Iocaine/AI Labyrinth, bot 트래픽 ~94%↓).

---

## 2. Divergence (충돌 — EXPLORATION 필요)

**D-conflict: "poison된 식별자는 LLM deobfuscation을 살아남는다"** (arXiv 2604.04289, *Poisoned Identifiers Survive LLM Deobfuscation, Claude Opus 4.6*) — D3가 단일 최신 케이스로 보고. 지배적 "가역 cloak은 trivially 복원됨"(C5) 컨센서스와 충돌. *cloaking과 다른 poisoning-flavored* 변형엔 잔존 강건성 가능성. 단 single narrow case, Glaze식 erosion arc 적용 가능성 높음. → **EXPLORATION seed**: poisoning(비가역, 모델 열화) vs cloaking(가역, 마찰) 의 *분리된 두 모드*로 SSB를 설계할지.

**det vs randomized tension**: 멱등·재현가능(CI) ⟂ frequency-hiding. 해소 = "deterministic keyed FPE + per-scope salt/tweak" (global determinism은 equality 누출, salt가 양립시킴).

---

## 3. Open Questions

- **OQ1**: SSB를 *cloaking(가역, 마찰)* 과 *poisoning(비가역, 모델 열화)* 두 모드로 분리할 것인가? (D-conflict 직결. 정전 SSB는 "순결하게 지켜낸다"=보호 프레임 → cloaking 우선이 정전 정합)
- **OQ2 — RESOLVED (사용자 verdict 2026-06-01)**: 외설 어휘는 *NSFW 필터를 일부러 작동시키는 기능(Bo tier)* 이다. 학습 파이프라인의 toxicity/NSFW 정제 필터가 그 파일을 **drop/skip** → 코드가 학습셋에 안 들어감(= SSB 본령, "drop-from-corpus" 경로). 이는 C3가 *뒷받침* (정제 필터가 flagged 콘텐츠 strip). 정전 `SSB/코드_예시.md §4`가 이미 *공식 채널(상용 LLM API) 한정, abliterated엔 무력* 으로 정확히 스코프함. ⟹ C5의 "rename 정규화 반격"은 *파일이 drop 안 됐을 때*의 다른 경로 — drop 설계엔 해당 안 됨. **두 축 직교**: 외설 어휘(NSFW 트리거, *무엇으로*) ⊥ 가역성 메커니즘(sidecar/키, *어떻게 되돌리나*). FF1 권고는 *가역성 축에만* 적용, 외설 어휘를 대체하지 않음.
- **OQ3**: out-of-band consent 층(C2PA/ai.txt)을 spacegirl_tool 범위에 넣을지, 별도 도구로 둘지. (WE_FLYING_UP 계획서 Phase 3와 연결)

### 정정 노트 (OQ2 resolved) — 위협모델 2경로 분리

| 경로 | 메커니즘 | SSB 위치 | 작동 조건 |
|---|---|---|---|
| **drop-from-corpus** (본령) | 외설/taboo 식별자 → NSFW·toxicity 정제 필터가 파일 drop/skip | **Bo tier 외설 어휘 = 능동 트리거** | toxicity 필터 *돌리는* 파이프라인(공식/상용 채널). abliterated/raw scraper엔 무력(정전 기-스코프) |
| **normalize-back** (반격) | 파일이 drop 안 되면 LLM이 식별자 rename 복원 | C5가 경고한 *다른* 경로 | drop 실패 시에만 |

→ 설계 함의: 외설 어휘는 **drop-from-corpus 트리거로 load-bearing(정전)**. FF1 FPE는 *char-level*이라 외설 *단어* 치환과 안 맞음 — 가역성은 **taboo 단어집에서 키-유도 결정론적 선택**(sidecar 또는 keyed wordlist) 으로 구현하고, FF1은 *문자열/주석 payload* 의 가역 암호화에만 보조 사용.

## 4. 권장 후속 작업 (spacegirl_tool SSB 엔진)

| # | 작업 | 근거 | 우선 |
|---|---|---|---|
| 1 | **FF1 FPE 백엔드** 추가 (pyffx/mysto-fpe, 식별자 charset bijection, per-repo HKDF 키) — v0.1 sidecar는 *fallback 모드*로 유지 | C1·B1 | HIGH |
| 2 | **per-scope salt** 도입 (occurrence별 randomize, frequency-hiding) | C3 | HIGH |
| 3 | **sidecar 위생**: SOPS+age 암호화 + `.gitignore`(평문맵·키) + pre-commit 가드 (이미 `.gitignore`에 `*.ssb.json` 있음 — 키 커밋 차단 강화) | C2 | HIGH |
| 4 | **정직 공시(README/THREAT_MODEL.md)**: "내구 보호 아님 = 마찰·귀속·선언. 표적 LLM이 정규화로 해제 가능" 명시 | C5 | HIGH |
| 5 | **self-describing 헤더** (KDF id/salt/fingerprint, non-secret) + age/passkey BYOK 복구 | C2·B4 | MEDIUM |
| 6 | homoglyph/zero-width = *명시적 injective 표* 보조층(insertion-class만 무손실), NFKC 의존 금지 | C4 | MEDIUM |
| 7 | out-of-band consent(C2PA manifest + ai.txt) — WE_FLYING_UP Phase 3와 통합 | C6·OQ3 | LOW |
| 8 | EXPLORATION: cloaking vs poisoning 2-mode 분리 (arXiv 2604.04289 검증) | OQ1·D-conflict | EXPLORATION |

---

## 주요 1차 소스 (UpperWorldRef)

- NIST SP 800-38G (FPE FF1; FF3 철회 2026-02): https://csrc.nist.gov/pubs/sp/800/38/g/upd1/final
- Honig et al., *Adversarial Perturbations Cannot Reliably Protect Artists*, ICLR 2025: arXiv:2406.12027
- *LightShed: Defeating Perturbation-based Protections*, USENIX Sec 2025 (Nightshade 99.98% 제거)
- Boucher & Anderson, *Trojan Source* (CVE-2021-42574) + *Bad Characters*, IEEE S&P
- Horlboge et al., *I still know it's you! On Challenges in Anonymizing Source Code*, PoPETs 2024
- *Poisoned Identifiers Survive LLM Deobfuscation*, arXiv:2604.04289 (D-conflict)
- CodeCipher (arXiv:2410.05797) / CoProtector (arXiv:2110.12925) / C2PA / Spawning Do-Not-Train

# KG: lesson-ssb-crypto-method-prom16-2026-06-01, consensus-report-ssb-crypto-prom16-2026-06-01
