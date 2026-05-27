---
description: plan/research/draft/image 산출물을 4-way review로 검증합니다.
argument-hint: "<slug>"
---

사용자가 stock-report-harness review 단계를 요청했습니다.

**slug**: $ARGUMENTS

`.claude/skills/stock-review/SKILL.md`를 읽고 그대로 수행하세요.
리뷰 파일 작성 후 반드시 `python3 scripts/validate_report_contract.py <slug>`를 실행해
계약 오류가 없는지 확인하세요.
`reviews/<slug>.md` status가 pass일 때만 다음 단계 `/stock-build <slug>`를 안내하세요.
