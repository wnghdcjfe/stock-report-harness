---
name: stock-research
description: 주식 리포트 slug에 대한 출처 기반 리서치를 수행한다. /stock-plan 이후 /stock-research <slug>로 사용하며, yfinance 일봉 가격, 최신 뉴스 100건, 한국 주식의 토스 증권 뉴스/매매 동향 확인, research/<slug>.md 출력을 포함한다.
---

# 주식 리서치 스킬

`plan/<slug>.md`를 기반으로 `research/<slug>.md`와 `output/assets/` 원자료 파일을 생성한다.

## 선행 조건

- `plan/<slug>.md`가 존재해야 한다. 없으면 중단하고 `/stock-plan <요청>`을 먼저 실행하라고 안내한다.
- plan 프론트매터에서 `ticker`, `period_start`, `period_end`, `price_data_source`, `price_data_interval`을 읽고 유지한다.

## 절차

1. 티커와 기간을 plan 대비 검증한다.
2. `yfinance`로 요청 기간 전체의 실제 일봉 가격 데이터를 수집한다.
   - 원본/정규화 데이터를 `output/assets/<slug>-price-chart-v1.json` 또는 명확히 명명된 파일로 저장한다.
   - `YYYY-MM-DD` 레이블을 오름차순으로 사용한다.
3. 출처 기반 맥락을 수집한다:
   - 1차 출처 우선: 기업 IR, 공식 뉴스룸, 공시, 거래소/중앙은행 데이터.
   - 이벤트와 리스크는 공신력 있는 매체를 사용한다.
   - 한국 상장 주식은 토스 증권 주식 뉴스와 투자자 매매 동향을 가능한 경우 확인한다.
4. 주식/ETF/섹터 요청 시 가능하면 최신 관련 뉴스 100건 이상을 수집·분류한다.
   - 최신 뉴스 원본 JSON을 `output/assets/<slug>-*-latest100.json`으로 저장한다.
   - 분류/분석 JSON을 `output/assets/<slug>-*-analysis100.json`으로 저장한다.
   - 기사 URL을 조작하지 않는다. API에 개별 URL이 없으면 제공자/검색 폴백을 유지하고 `url_is_fallback: true`로 표시한다.
5. `research/<slug>.md`에 최소 다음 프론트매터를 포함해 작성한다:
   `slug`, `title`, `created_at`, `period_start`, `period_end`, `ticker`, `price_data_source`, `price_data_interval`, `plan_source`, `sources`.
6. 본문 필수 항목:
   - 결론 요약
   - 주가 데이터 메모
   - 핵심 이벤트/메커니즘
   - 뉴스 100건 표 또는 수집 한계와 근거
   - 수급/투자자별 매매 동향 (가능한 경우)
   - 리스크/불확실성
   - References/출처 표식 (`[S1]` 등)

## 제약 조건

- 임의·샘플링 가격 데이터를 사용하지 않는다.
- 존재하지 않는 기사 URL을 조작하지 않는다.
- 사실과 추론을 분리한다.
- 외부 접근이 차단되면 증거를 지어내지 말고 정확한 누락 데이터를 명시한 `blocked`/한계 섹션을 작성한다.

## 완료 보고

`research/<slug>.md`, 주요 원자료 JSON 파일, 가격 데이터 행 수, 뉴스 건수, 다음 명령어를 보고한다: `/stock-draft <slug>`.

`stock-goal`에서 호출된 경우 이 보고는 내부 체크포인트일 뿐이다. 멈추거나 사용자를 기다리지 않고 즉시 `/stock-draft <slug>`로 진행한다.
