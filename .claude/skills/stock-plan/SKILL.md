---
name: stock-plan
description: 자연어 주식/ETF/섹터 요청으로부터 stock-report-harness 기획 브리프를 생성한다. "삼성전자 30일 분석" 같은 /stock-plan 요청에 사용하며, 리서치·초안·이미지·리뷰·빌드 전에 plan/<slug>.md를 작성한다.
---

# 주식 기획 스킬

`plan/<slug>.md`를 생성한다. 이후 모든 단계의 단일 진실 공급원이다.

## 절차

1. 요청을 파싱한다.
   - 주제, 대상 독자, 티커/대체 지표, 차트 필요 여부, 요청 기간을 식별한다.
   - 기간이 명시되지 않으면 최근 6개월을 사용하고 `assumptions`에 기록한다.
   - 종료일이 명시되지 않으면 현재 날짜를 사용한다.
   - yfinance 심볼 규칙: 미국 티커는 그대로, 한국 코스피/코스닥은 `.KS`/`.KQ`를 붙인다.
2. 영문 소문자 kebab-case로 안정적인 `slug`를 생성한다. 주제·기간·연월을 포함한다 (예: `samsung-electronics-recent-30d-2026-05`).
3. `plan/<slug>.md`에 필수 프론트매터를 작성한다:
   `slug`, `topic`, `request`, `output_type`, `audience`, `ticker`, `period_start`, `period_end`, `chart_required`, `price_data_source`, `price_data_interval`, `created_at`, `assumptions`.
4. 본문 필수 항목:
   - 요청 해석
   - 이해 목표
   - 리서치 범위
   - 데이터 확인 항목
   - 리포트 구조
   - 차트 요구
   - Hero 이미지 방향
   - 리뷰 기준
   - 완료/차단 조건
5. 사용자가 여러 단계를 명시적으로 요청하지 않은 이상, 이 스킬에서 리서치/초안/빌드로 진행하지 않는다. `stock-goal`은 명시적 다단계 요청으로 간주한다. 다단계 요청이면 plan을 먼저 완료한 뒤 다음 `/stock-*` 단계를 호출한다.

## 제약 조건

- 알 수 없는 티커를 지어내지 않는다. 합리적 조회 후에도 불확실하면 `ticker: TBD`로 설정하고 차단 사항으로 추가한다.
- 한국어 요청에는 기본적으로 한국어로 작성한다.
- 투자 권유, 수익 보장, 매매 지시를 포함하지 않는다.
- 폴더 계약 준수: 기획 산출물은 반드시 `plan/` 아래에 저장한다.

## 완료 보고

생성된 plan 경로, 확정 티커, 기간, slug, 다음 명령어를 보고한다:
`/stock-research <slug>`.

`stock-goal`에서 호출된 경우 이 보고는 내부 체크포인트일 뿐이다. 멈추거나 사용자를 기다리지 않고 즉시 `/stock-research <slug>`로 진행한다.
