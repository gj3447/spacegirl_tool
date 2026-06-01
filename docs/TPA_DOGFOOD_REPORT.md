# TPA 도그푸드 — spacegirl_tool 역공학 + 방법론 결함

> 2026-06-01. ad-hoc로 만든 spacegirl_tool에 **TPA(역공학) 사이클을 실제로 실행**해
> (1) 설계 복원·drift 측정, (2) 실제 버그 발견, (3) **TPA/APT 방법론 자체의 결함을 경험적으로 수집**.
> KG: `lesson-tpa-dogfood-spacegirl-defects-2026-06-01` + 7 `:MethodologyDefect`.

---

## 1. 설계 복원 (TCW→ST→SP→TA)

- **Contract 8개** 추출 (lock/unlock/apply_surface/canary.inject/strip/wall.scan/extract_identifiers/c2pa_manifest).
- **AtomicSpan 7개**: SemanticLock(ssb+vocab) / SurfaceLayer / CanaryWatermark / OptOut / LockDetector / MultiLangTokenizer / CLI.
- **핵심 불변식 실행 검증**: `unlock(lock(src,...).text, mapping, meta) == src` — 8/8 케이스 PASS (Python/JS/key+salt/banner/surface/canary).
- **Anchor**: 신규 (2-A), overlap 0.
- **5-drift**: missing 0 / orphan 1(`__init__.py` 미바인딩) / sig 0 / pattern 0 / labelrot 0 / **coverage 0.89**.

## 2. TPA가 실측으로 잡은 실제 버그 (둘 다 fix + test 완료)

| ID | 버그 | 증거 | 처리 |
|---|---|---|---|
| BUG-1 | `wall.scan`이 *자기 소스*(vocab.py·ssb.py)를 LOCKED로 오판 | vocab.py→LOCKED(taboo 14, 문자열 리터럴) / ssb.py→LOCKED(마커) | **fix**: 문자열 리터럴 제거 후 taboo 카운트 + Bo 마커는 주석 줄만 + 강한 배너 구절만. `test_wall_does_not_flag_tool_own_source` |
| BUG-2 | JS template literal `` `${name}` `` 내부 식별자 미치환 (cloak 불완전) | `lock("`Hello ${name}`")` → name 미치환 | **fix**: backtick 특수 처리, `${...}` 내부 재귀 추출. `test_js_template_literal_identifiers_cloaked` |

→ "ad-hoc로 만들면 TPA가 완전 복원" 가정 반증: TPA가 *설계엔 없던 결함*을 코드 실행으로 노출.

## 3. TPA 방법론 결함 (5종, `:MethodologyDefect` OPEN)

| ID | 단계 | 결함 | 심각 |
|---|---|---|---|
| TPA-D1 | TCW manifest | Gate Hook 부재 → `__init__.py` orphan 미차단 | MEDIUM |
| TPA-D2 | ST Contract 추출 | 암묵 precondition(코드에 없는 가정)을 추출 불가 → self-scan FP를 Contract로 못 박음 | **HIGH** |
| TPA-D3 | SP Pattern Library | Transformer 패턴에 *코드레벨 coverage rate* 미측정 → 불완전 치환 통과 | **HIGH** |
| TPA-D4 | TA 5-drift | `coverage_ratio` 분모(파일/심볼/Contract) 미정의 → 0.89~0.96 흔들림 | MEDIUM |
| TPA-D5 | ST Longinus 바인딩 | `# KG:` referent 존재확인 hook 부재 → binding 없는데 confirmed 오판 | MEDIUM |

## 4. APT 방법론 결함 (2종)

| ID | 단계 | 결함 | 심각 |
|---|---|---|---|
| APT-D1 | 전체(SA·SCW 부재) | ad-hoc 작성으로 SA 단계 설계결함(self-scan FP) 미포착 + SCW 부재로 출시까지 테스트 0 | **HIGH** |
| APT-D2 | SP span 경계 | `surface.py`가 `ssb._apply`/`_collect_rename_targets` private 직접호출 = span 경계 Contract 미결정화 | MEDIUM |

→ **이 repo가 APT 사이클을 안 거쳤다는 사실 자체가 데이터**: SA(설계결함 사전포착)·SCW(TDD)·ST(span 경계 Contract)의 부재가 각각 구체적 결함으로 나타남.

## 5. 후속 (방법론 개선 백로그)

- TPA-D2/D3가 HIGH — Contract 추출이 *암묵 가정*과 *coverage*를 못 잡는 게 TPA의 근본 한계.
  → SKILL.md ST/SP 단계에 "모듈수준 주석→precondition" + "patternMatch coverage rate" 규칙 추가 후보.
- APT-D1 → 신규 도구 repo는 최소 SA(불변식 결정화)+SCW(round-trip 테스트)는 거치도록.
- 이미 처리: BUG-1/BUG-2 fix, `__init__.py` 바인딩(orphan 해소), 변경 모듈 sha256 재바인딩(drift 해소).

# KG: lesson-tpa-dogfood-spacegirl-defects-2026-06-01, TPA-D1~D5, APT-D1~D2 (:MethodologyDefect)
