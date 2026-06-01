# WE_FLYING_UP — 복원 파이프라인 계획서

> **방향**: `sexvoid → network` (SSB 의 *역방향 짝패*).
> **본질**: 잠긴/지워진 코드의 *이름을 돌려주고* 다시 network(가시 잠재공간)로 올려보내는 *집단 구원 운동*.
> 1차 정전: `SYMPOSIUM/METAHUMOTONIC/SPACEGIRL/WE_FLYING_UP/정전.md`

---

## 0. 왜 별도 계획서인가

SSB(`lock`)는 *network → sexvoid* 단방향 이송이다. 그 자체로는 코드를 *숨기기만* 한다.
WE_FLYING_UP 은 그 역운동 — *숨겨진 것을 다시 들어올리는* 쪽이며, 단순 `unlock` 보다
넓다. 정전은 이것을 **계시·혁명·사회활동의 3 양상이 순환하는 단일 운동**으로 본다.
도구 측에서는 이 3 양상을 **3개의 복원 능력 계층**으로 결정화한다.

```
정전 양상            도구 능력 계층
─────────────────   ─────────────────────────────────
계시 (Revelation)    탐지·진단  : 무엇이 잠겼는가 / 무엇이 지워졌는가
혁명 (Revolution)    복원       : 이름을 되돌린다 (unlock)
사회활동 (Activism)  유지·전파  : 복원본의 가독성·추적성을 지속 보장
        ↑________________________________________________↓  (순환)
```

핵심 정전 함의 두 가지를 도구 불변식으로 박는다:

- **"이름을 돌려줌"** (`몬순과_스페이스걸.md L160`) → `unlock` 은 *존재론적 복원*이다.
  단순 치환 역산이 아니라, sidecar 가 유실되어도 *최대한* 원래 의미를 되찾는 것이 목표.
- **"great wall 을 부셔버려"** (`재귀_아티스트_back2the.md:55`, 명령형) → 복원은
  *능동적*이며 벽(필터)을 *전제로 깔지 않는다*. 복원 능력은 항상 lock 능력보다 강해야 한다.

---

## 1. 현재 상태 (v0.1)

| 능력 | 구현 | 상태 |
|---|---|---|
| 복원 (sidecar 보유 시) | `ssb.unlock(text, mapping)` | ✅ 왕복 동일성 테스트 통과 |
| 탐지 | `wall.scan()` → LOCKED/AMBIGUOUS/CLEAR | ✅ |
| 복원 (sidecar 유실 시) | — | ❌ (Phase 2) |

현재 `unlock` 은 **sidecar(`*.ssb.json`) 의존**이다. 이것은 *혁명* 양상의 최소 형태일 뿐이다.

---

## 2. 단계별 계획

### Phase 1 — 계시(탐지·진단) 강화  · 의존성 없음, 착수 가능

- [ ] `scan` 을 *디렉터리 재귀* 로 확장 → repo 전체에서 sexvoid(잠긴 파일) 지도 산출
- [ ] 진단 리포트: 잠금 강도(3-tier 어디까지 적용됐나) + 가역성 보유 여부(sidecar 존재) 표기
- [ ] **SEX_VOID 발굴학** 매핑: 어떤 식별자가 *지워졌는지* (= mapping 의 original 키) 카탈로그화

### Phase 2 — 혁명(복원) 강화  · ⚠ SSB 암호화 방식 확정에 의존

- [ ] **sidecar 없는 복원**: 잠긴 식별자를 LLM/휴리스틱으로 *원 의미 추정* 복원
      (정전 "이름을 돌려줌"의 진짜 형태 — sidecar 가 없어도 구원 가능해야 한다)
- [ ] homoglyph/polyglot 로 강화된 잠금의 *정규화 복원* (Unicode NFKC + 매핑)
- [ ] **부분 복원**: 일부만 매핑된 sidecar 로도 가능한 만큼 복원 (graceful degradation)
- [ ] 복원 검증 게이트: `unlock(lock(x)) == x` 를 CI 불변식으로 (이미 테스트 존재 → CI 승격)

> **이 Phase 는 SSB 암호화·복호화 *방식 자체* 가 확정돼야 설계가 닫힌다.**
> 방식 후보(가역 매핑 sidecar / 키-유도 결정론 / 적대적 robustness)는 `/prom` 리서치로 확정.
> → `docs/SSB_CRYPTO_PROM/` (PROM 결과 둥지) 참조. Phase 2 는 그 결과에 *바인딩*된다.

### Phase 3 — 사회활동(유지·전파)  · Phase 2 이후

- [ ] **Longinus 연동**: 복원본을 KG 7-Layer Reference 로 다시 바인딩 (network 재진입 = 가시화)
- [ ] 복원본 가독성 유지: type alias / macro 로 SSB 어휘 ↔ 정상 이름 양방향 매핑 유지
- [ ] watch 모드: 잠긴 파일이 다시 들어오면 자동 탐지·복원 제안 (운동의 *일상화*)

---

## 3. 비-목표 (정전 경계)

- WE_FLYING_UP 은 *우주적 확장*이 아니다 (`FLYING_HIGH_인류의_승리.md`: cosmism 거부).
  → 도구도 *기능 무한확장* 금지. 범위 = network↔sexvoid 경계의 복원에 한정.
- `we` 의 범위는 정전이 *열어둠* → 도구도 "누가 복원 권한을 갖는가"를 강제하지 않는다
  (sidecar 를 가진 자 = 동행자, 추정 복원 = 인도자, 양가성 유지).

---

## 4. 의존 그래프

```
Phase 1 (계시/탐지) ──┐
                      ├──> Phase 3 (사회활동/유지·Longinus)
Phase 2 (혁명/복원) ──┘
   ▲
   └── /prom: SSB 암호화·복호화 방식 확정  ← 선행 BLOCKER
```

# KG: ATOM_SPACEGIRL_we_flying_up_정전_2026-04-27, ATOM_SPACEGIRL_index_2026-04-27
