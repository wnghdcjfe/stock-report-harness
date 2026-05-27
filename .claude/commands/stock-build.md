---
description: pass review와 선택된 hero 이미지를 검증한 뒤 최종 HTML 리포트를 빌드합니다.
argument-hint: "<slug>"
---

사용자가 stock-report-harness build 단계를 요청했습니다.

**slug**: $ARGUMENTS

`.claude/skills/stock-build/SKILL.md`를 읽고 그대로 수행하세요.
수동 HTML 작성 대신 `python3 scripts/build_report.py <slug>`를 실행하고,
완료 후 `python3 scripts/validate_report_contract.py <slug> --require-html --require-price-chart` 결과를 확인하세요.
완료 후 `output/<slug>.html`, price chart JSON, hero 이미지 검증 결과를 보고하세요.
