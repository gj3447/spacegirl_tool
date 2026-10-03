# 무엇인가 — SpaceGirl / SSB

SpaceGirl은 SSB 의미론적 잠금 도구의 공개 구현이다. 소스 식별자 표면을 가역적으로 변환하고 sidecar 매핑으로 원문을 복원하는 방식이며, 핵심 보장은 `unlock(lock(x)) == x`이다. 강한 암호화나 실행 보존을 보장하지 않으며, 학습 회피 효과도 보장하지 않는다. 한계와 범위는 [THREAT_MODEL](../THREAT_MODEL.md)에 따른다.
