---
name: stock-review
description: 주식 리포트 4-way 리뷰 게이트를 실행한다. plan, research, draft, 선택된 히어로 이미지가 존재한 뒤 /stock-review <slug>로 사용하며, reviews/<slug>.md에 pass, needs_fix, blocked 결과와 별도 세션 리뷰어 메타데이터를 기록한다.
---

# 주식 리뷰 스킬

빌드 전 리뷰 게이트로서 `reviews/<slug>.md`를 생성한다.

## 선행 조건

- 필수 파일: `plan/<slug>.md`, `research/<slug>.md`, `drafts/<slug>.md`.
- 필수 이미지 파일: `output/assets/<slug>-selected-image.json`과 선택된 PNG.

## 절차

1. 가급적 별도 Task/서브에이전트 세션에서 4가지 리뷰 관점을 실행한다:
   - `fact-checker`: 티커, 날짜, 숫자, 출처, 가격 데이터, 뉴스 링크.
   - `report-designer`: 흐름, 차트/히어로 적합성, 가독성, 섹션 완전성, `design/toss_design.md` 준수. `output/<slug>.html`이 있으면 빌드된 HTML을 검사하고, 없으면 최종 HTML 시각 검증은 stock-build 검증기로 미룬다고 기록한다.
   - `content-editor`: 한국어 스타일, 명확성, 중복, 투자 조언 부재.
   - `codex-independent` 또는 동등: plan/research/draft/빌드 요건의 사각지대 리뷰.
2. 불변 조건을 검증한다:
   - plan/research/draft 티커와 기간이 일치하는지.
   - 초안에 H1이 정확히 하나이고 필수 섹션이 있는지.
   - 초안이 내장 가격 배열 대신 `price-chart` 블록을 사용하는지.
   - References가 존재하고 사실 주장에 출처 표식이 있는지.
   - 선택된 히어로 이미지가 존재하는지.
   - HTML이 있으면 토스 모바일 셸/디자인 요건을 따르는지 (`main.shell` 560px, 고정 앱바, 토스 블루, 8px 구분선, 히어로 이미지 카드, 토스 차트 렌더러, 하단 면책 문구).
   - 금지된 투자 조언 표현이 없는지.
3. `reviews/<slug>.md` 프론트매터를 작성한다:
   `slug`, `status`, `created_at` 또는 `reviewed_at`, `plan_source`, `research_source`, `draft_source`, `review_type: separate-session-4way`, `review_execution: separate_subagent_sessions`, `reviewers`.
4. 상태를 설정한다:
   - `pass`: 빌드를 진행할 수 있을 때만.
   - `needs_fix`: 생성 단계에서 수정 가능한 이슈가 있을 때.
   - `blocked`: 동일한 차단 이슈가 반복되거나 외부 데이터/권한 한계일 때만.
5. 리뷰 작성 후 계약 검증기를 실행한다:
   `python3 scripts/validate_report_contract.py <slug>`
   - 검증 실패 시 blocked 기준에 해당하지 않으면 `status`를 `needs_fix`로 변경한다.
   - 검증기 오류를 리뷰 수정 목록에 포함한다.

## 피드백 루프

`needs_fix`이면 수정할 상위 단계와 파일을 정확히 나열한다. 리뷰 상태가 `pass`가 될 때까지 빌드하지 않는다.

## 완료 보고

리뷰 상태, 주요 이슈(있는 경우), 다음 명령어를 보고한다: 상태가 `pass`일 때만 `/stock-build <slug>`.

`stock-goal`에서 호출되고 상태가 `pass`이면 이 보고는 내부 체크포인트일 뿐이다. 멈추거나 사용자를 기다리지 않고 즉시 `/stock-build <slug>`로 진행한다.
