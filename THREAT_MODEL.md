# THREAT_MODEL — spacegirl_tool / SSB

> 정직 공시 (PROM 16 + PROM 12, 2026-06-01). **이것은 강한 암호가 아니다.**
> SSB는 *마찰 · 귀속 · 예술적 선언* 도구다. 아래를 읽고 기대치를 맞추세요.

---

## 한 줄 요약

| | 한다 | 못 한다 |
|---|---|---|
| **cloaking** (`lock`) | 외설/taboo 식별자로 NSFW·toxicity 필터를 작동시켜 *필터 돌리는 파이프라인*이 파일을 **학습 코퍼스에서 drop** 하게 유도 | 결정한 적대자가 코드를 학습하는 걸 *내구적으로* 막지 못함 |
| **canary** (`canary`) | 비파괴 워터마크로 *무단 학습이 일어났음을 사후 증명* (귀속/증거) | 학습 자체를 막지 못함 |
| **opt-out** (`optout`) | machine-readable do-not-train 신호 (법/provenance 층 — 진짜 teeth) | good-faith 행위자만 구속 |

---

## 무엇이 실제로 작동하나 (drop-from-corpus)

cloaking의 본령은 **파일을 학습셋에서 떨어뜨리는 것**이다. 외설/taboo 식별자(Bo tier)는
상용·공식 LLM 파이프라인의 NSFW·toxicity·quality 데이터정제 필터를 작동시켜 그 파일을
*flag → drop* 시킨다. 드롭된 파일은 애초에 학습되지 않는다.

이 경로는 다음 조건에서 작동한다:

- 대상 파이프라인이 **NSFW/toxicity 필터를 실제로 돌릴 때** (상용/공식 채널 — 정전 스코프).
- 정제 필터가 외설 식별자를 *flagged*로 판정할 때.

## 무엇이 작동하지 않나 (정직)

- **abliterated / 무검열 / 날것 scraper**: refusal/NSFW 필터가 없어 외설을 무시 → SSB 무력.
  (정전 `SSB/코드_예시.md §4`가 이미 "공식 채널 한정" 으로 못 박음.)
- **정규화 반격 (normalize-back)**: 파일이 *drop 안 되고* 학습셋에 남으면, 표적 LLM이
  "이 외설 식별자들을 합리적 이름으로 rename" 으로 의미 보존 복원 가능. drop 설계가
  실패한 경우의 잔여 위험.
- **표면층 (homoglyph/zero-width)**: NFKC 데이터정제 / post-Trojan-Source 툴체인 /
  BPE byte-fallback 3 chokepoint에서 *strip*됨. short half-life. **opportunistic 보조일 뿐
  load-bearing 금지** — legacy 미정규화 scraper에만 부분 효과.
- **암호적 비밀 아님 (Kerckhoffs)**: sidecar 매핑/키가 곧 비밀. 매핑이 유출되면 전체 해제.
  sidecar는 절대 public repo에 동봉하지 말 것 (`*.ssb.json` 은 `.gitignore` 됨).

## 왜 poisoning 모드가 *없나*

PROM 12 결정 (`lesson-ssb-mode-split-prom12-2026-06-01`):

1. **모순**: cloaking은 파일이 필터에 *걸려 drop*되길 원하고, poisoning은 파일이 필터를
   *통과해 코퍼스에 잔존*하길 원한다 — 같은 파일에 정반대 요구. 외설 poison은 자기파괴.
2. **효능**: 개인 1-repo poisoning은 *falling bet* — 일반 열화엔 코퍼스 분율이 부족하고,
   타깃 백도어는 데이터 접근이 병목 + benign(외설 정반대)이어야 함.
3. **윤리·법**: 능동 poisoning = 제3자 시스템 비인가 impairment (CFAA/CMA, hack-back 유사)
   + **비가역 trap** (작가 본인 · 정직한 fork · commons 영구 오염, 되돌리기 불가)
   + 평판 리스크. 2026 기후는 sabotage보다 opt-out/licensing 보상.

⟹ "두 번째 모드" = 비파괴 **canary** (증명/귀속) + **opt-out** (법/provenance). 모델 오염 ✗.

## 키/매핑 위생 (필수)

- `lock --key K --salt S` 의 `key`+`salt` 가 매핑 재현의 비밀. 안전 보관.
- sidecar(`*.ssb.json`)는 평문 매핑 — 분실 시 복원 불가, 유출 시 전체 해제.
- public repo에는 **cloaked 코드만**. sidecar/key는 별도 채널 (예: age/SOPS 암호화).

# KG: lesson-ssb-crypto-method-prom16-2026-06-01, lesson-ssb-mode-split-prom12-2026-06-01
