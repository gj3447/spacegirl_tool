#!/usr/bin/env bash
# spacegirl_tool — sidecar/키 누출 가드 (pre-commit hook).
#
# PROM 16 C2: sidecar 매핑/키 = 비밀. public repo 동봉 = 즉시 전체 해제.
# 본 훅은 *.ssb.json sidecar, age/ssh 개인키, SGCANARY secret 누출을 staged diff에서 차단.
#
# 설치: ln -sf ../../bin/pre-commit-guard.sh .git/hooks/pre-commit
#   또는 pre-commit 프레임워크의 local hook 으로 등록.
#
# 우회(의도된 커밋): git commit --no-verify
#
# KG: lesson-ssb-crypto-method-prom16-2026-06-01 (sidecar 위생)

set -euo pipefail

fail=0
staged=$(git diff --cached --name-only --diff-filter=ACM)

block() { echo "BLOCKED(spacegirl-guard): $1"; fail=1; }

while IFS= read -r f; do
  [ -z "$f" ] && continue
  case "$f" in
    *.ssb.json)      block "sidecar 매핑 커밋 시도: $f (cloak 키. .gitignore 확인)";;
    *.age|*.agekey)  block "age 키 커밋 시도: $f";;
    *id_rsa|*id_ed25519|*.pem) block "개인키 커밋 시도: $f";;
  esac
  # 내용 스캔: 실제 개인키 자료 (라인 시작 앵커로 자기-매치 false positive 회피)
  if git show ":$f" 2>/dev/null | grep -qE '^AGE-SECRET-KEY-1|^-----BEGIN (OPENSSH|RSA|EC) PRIVATE KEY-----'; then
    block "파일 내 개인키 자료: $f"
  fi
done <<< "$staged"

if [ "$fail" -ne 0 ]; then
  echo "---"
  echo "의도된 커밋이면: git commit --no-verify"
  exit 1
fi
exit 0
