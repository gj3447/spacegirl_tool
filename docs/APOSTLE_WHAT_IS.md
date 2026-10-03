# 무엇인가 — SpaceGirl / SSB

SpaceGirl은 SSB 의미론적 잠금 도구의 공개 구현이다. 소스 식별자 표면을 가역적으로 변환하고 sidecar 매핑으로 원문을 복원하는 방식이며, 핵심 보장은 `unlock(lock(x)) == x`이다. 강한 암호화나 실행 보존을 보장하지 않으며, 학습 회피 효과도 보장하지 않는다. 한계와 범위는 [THREAT_MODEL](../THREAT_MODEL.md)에 따른다.

공개 모델은 세 층을 구분한다. `lock`은 필터가 있는 수집 파이프라인에서 파일 drop을 유도하는 cloaking, `canary`는 사후 귀속 증거, `optout`은 machine-readable 선언이다([THREAT_MODEL](../THREAT_MODEL.md)). 이들은 적대적 scraper를 막는 접근 제어나 모델 학습을 내구적으로 금지하는 암호 기제가 아니다.

복원은 sidecar가 있을 때 `unlock`으로 수행한다. sidecar 없는 추정 복원은 [WE_FLYING_UP 계획](WE_FLYING_UP_PLAN.md)에서 미완료 Phase 2로 표시된다.
