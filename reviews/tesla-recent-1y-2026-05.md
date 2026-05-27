---
slug: tesla-recent-1y-2026-05
status: pass
created_at: 2026-05-27
plan_source: plan/tesla-recent-1y-2026-05.md
research_source: research/tesla-recent-1y-2026-05.md
draft_source: drafts/tesla-recent-1y-2026-05.md
review_type: separate-session-4way
review_execution: separate_subagent_sessions
reviewers: fact-checker, report-designer, content-editor, codex-independent
---

# Review — 테슬라 최근 1년 분석

## Separate Session Evidence

- fact-checker: price/source/date invariant review perspective
- report-designer: structure/chart/hero/readability review perspective
- content-editor: Korean style and financial-advice wording review perspective
- Codex: independent build-contract checklist perspective

## fact-checker: pass

- plan/research/draft ticker는 모두 `TSLA`로 일치한다.
- 기간은 모두 `2025-05-27`~`2026-05-26`로 일치한다.
- 가격 데이터는 yfinance 1일봉으로 `output/assets/tesla-recent-1y-2026-05-price-chart-v1.json`에 저장되었고, row count는 `251`개다.
- 시작 종가 `$362.89`, 종료 종가 `$433.59`, 수익률 `+19.48%`, 최고/최저 종가가 draft와 일치한다.
- Google News RSS 100건 원자료와 분석 파일이 존재한다.
- 미국 주식 수급은 한국식 개인·외국인·기관 일별 순매수 대신 yfinance/Yahoo Finance 보유자·내부자·의견 요약을 대용 지표로 설명했다.

## report-designer: pass

- 개요 → 차트 급등·급락 이벤트 → 배경 → 메커니즘 → 최신 뉴스 5건 → 영향과 적용 → 핵심 정리 흐름이 초보자용 리포트 구조에 맞다.
- `price-chart` 블록, 급등·급락 이벤트 강조, 뉴스 카테고리 bar chart가 모두 있고, 차트에는 접근성 라벨이 있다.
- hero 이미지는 세 후보 중 v2가 선택되었고, EV 제조·AI·로보택시·에너지 옵션이라는 리포트 메시지를 반영한다.

## content-editor: pass

- 한국어 톤은 교육용이며 매수·매도 지시, 수익 보장, 과도한 FOMO 표현을 포함하지 않는다.
- 제목에 포함된 외부 기사 원문 표현은 뉴스 제목으로만 표시되며, 리포트 자체의 투자 권유 문장으로 사용하지 않았다.
- 면책 문구가 draft 말미에 포함되어 있고 최종 HTML footer note로 렌더할 수 있다.

## codex-independent: pass

- 필수 파일 존재: plan, research, draft, selected image JSON, selected PNG.
- Draft H1은 정확히 1개이며 필수 섹션이 모두 있다.
- 최종 build 전 조건은 충족된다.
- 미국 주식 리포트이므로 한국식 개인·외국인·기관 수급 섹션은 제거했고, 필요한 보유자 데이터는 research 원자료에만 남겼다.
- 최신 뉴스 5건 링크는 긴 URL/제목이 화면 밖으로 벗어나지 않도록 HTML CSS 줄바꿈 규칙을 확인했다.

## Build Gate

통과: /stock-build tesla-recent-1y-2026-05 진행 가능
