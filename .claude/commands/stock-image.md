---
description: 리포트 기반 hero 이미지 후보 3개를 만들고 1개를 선택합니다.
argument-hint: "<slug>"
---

사용자가 stock-report-harness image 단계를 요청했습니다.

**slug**: $ARGUMENTS

`.claude/skills/stock-image/SKILL.md`를 읽고 그대로 수행하세요.
이 단계는 직접 이미지 생성 도구를 호출하지 말고 Codex CLI를 열어 `imagegen` skill로 생성하게 합니다.
완료 후 선택된 hero 이미지와 다음 단계 `/stock-review <slug>`를 알려주세요.
