# 어떻게 쓰는가 — SpaceGirl / SSB

설치·`lock`·`unlock`·`scan`·canary·opt-out의 공개 사용 예시는 [README](../README.md)에 있다. 실제 파일에는 sidecar와 키 취급이 수반되므로, 먼저 위협 모델과 복원 경로를 확인한다. 잠긴 산출물이 원래처럼 실행된다고 가정하지 않으며, 도구가 접근 권한이나 모델 학습 차단을 부여하지 않는다.

1. 작은 복사본에서 `lock`과 `unlock` 왕복을 먼저 확인한다([README](../README.md)).
2. plain sidecar와 key/salt를 공개 코드와 분리해 보관한다. 유실하면 현재 구현은 복원할 수 없고, 유출되면 mapping이 드러난다. 공개 repo에 plain `*.ssb.json`을 넣지 않는 경계는 [THREAT_MODEL](../THREAT_MODEL.md)에 명시돼 있다.
3. `scan` 결과는 잠금 탐지이며, 차단 성공의 측정값은 아니다.
4. canary와 opt-out은 각각 귀속 증거와 선의의 행위자용 신호다. poisoning은 공개 위협 모델이 명시적으로 채택하지 않는다([THREAT_MODEL](../THREAT_MODEL.md)).

sidecar가 없는 복원을 기대하는 작업은 아직 Phase 2 계획이다. 현재 `scan`의 catalog·tier 결과를 원문 복구 성공으로 해석하지 않는다([WE_FLYING_UP plan](WE_FLYING_UP_PLAN.md)).
