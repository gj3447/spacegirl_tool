# SpaceGirl / SSB 연구 지도

| 주체 | 관계 | 대상 | 공개 근거 | 상태 |
|---|---|---|---|---|
| `lock` | 변환한다 | 소스 식별자 표면과 sidecar 매핑 | [README](../README.md) | SOURCE_DOCUMENT |
| `unlock` | 복원한다 | lock 결과의 원문 | [README](../README.md) | SOURCE_DOCUMENT |
| 위협 모델 | 제한한다 | 실행 보존·학습 회피에 관한 주장 | [THREAT_MODEL](../THREAT_MODEL.md) | SOURCE_DOCUMENT |
| `scan`·canary·opt-out | 보조한다 | 잠금 탐지·귀속·선언 | [README](../README.md) | SOURCE_DOCUMENT |
| key+salt | 결정한다 | per-file 변환 시드와 매핑 재현 | [README](../README.md#) | SOURCE_DOCUMENT |
| 기본 salt | 사용한다 | 파일 경로 | [README](../README.md#) | SOURCE_DOCUMENT |
| `*.ssb.json` | 보존한다 | 평문 sidecar mapping | [THREAT_MODEL](../THREAT_MODEL.md#) | SOURCE_DOCUMENT |
| `unlock` | 의존한다 | 보유한 sidecar | [WE_FLYING_UP 계획](WE_FLYING_UP_PLAN.md#1-) | SOURCE_DOCUMENT |
| Phase 1 | 구현한다 | 재귀 scan·tier·reversible·erased catalog | [WE_FLYING_UP 계획](WE_FLYING_UP_PLAN.md#1-) | SOURCE_DOCUMENT |
| Phase 2 | 계획한다 | sidecar 없는/부분 복원 | [WE_FLYING_UP 계획](WE_FLYING_UP_PLAN.md#2-) | SOURCE_DOCUMENT |
| poisoning | 채택하지 않는다 | 코퍼스 오염 모드 | [THREAT_MODEL](../THREAT_MODEL.md#) | SOURCE_DOCUMENT |
| PROM 12 decision | 유지한다 | cloaking single default와 non-destructive canary/opt-out | [PROM 12](SSB_CRYPTO_PROM/PROM_12_MODE_SPLIT_REPORT.md) | SOURCE_DOCUMENT |
| PROM 16 design | 구분한다 | reversible mapping의 보관 위험과 기술적 한계 | [PROM 16](SSB_CRYPTO_PROM/PROM_16_REPORT.md) | SOURCE_DOCUMENT |
| public repo | 제외한다 | sidecar와 key | [THREAT_MODEL](../THREAT_MODEL.md#) | SOURCE_DOCUMENT |

공개 계약의 핵심은 가역성이다. 강한 암호화, 모델 학습 차단, 잠긴 코드의 실행 보존은 이 표가 보장하지 않는다.

## 열린 질문

- 제안: 변환 전후의 언어별 실행 한계와 sidecar 유실 시의 실패 사례를 공개 fixture로 계속 측정할 수 있는가.
