---
slug: {SLUG}
topic: {분석 주제}
request: {사용자 요청 원문}
output_type: report
audience: beginner | intermediate | advanced
ticker: {YFINANCE_SYMBOL_OR_TBD}
period_start: {YYYY-MM-DD}
period_end: {YYYY-MM-DD}
chart_required: true
price_data_source: yfinance
price_data_interval: 1d
created_at: {YYYY-MM-DD}
assumptions:
  - {Planner 가정}
---

# Planning Brief — {분석 주제}

## 요청 해석

- 대상: {개별주/ETF/섹터/테마}
- 기간: {period_start} ~ {period_end}
- 산출물: 검증 가능한 경제 리포트 HTML
- 독자 수준: {beginner/intermediate/advanced}

## 이해 목표

1. {이해 목표 1}
2. {이해 목표 2}
3. {이해 목표 3}

## 리서치 범위

- 공식 IR/공시 자료: {확인 대상}
- 가격 데이터: yfinance, interval=1d, 요청 기간 전체 일봉 종가
- 뉴스/수급: {뉴스 및 수급 데이터}
- 비교 대상: {벤치마크/섹터}

## 데이터 확인 항목

- [ ] ticker 확인
- [ ] 기간 및 가격 데이터 확인
- [ ] 뉴스/이벤트 분류
- [ ] 수급 동향 확인
- [ ] 리스크 요인·불확실성 확인

## 리포트 구조

1. 개요 — {핵심 요약}
2. 배경 — {왜 중요한가}
3. 메커니즘 — {가격/수급/뉴스가 연결되는 방식}
4. 영향과 적용 — {확인할 변수와 리스크}
5. 핵심 정리 — {초보자가 기억할 점}

## 차트 요구

- price-chart 필요 여부: {true/false}
- ticker: {YFINANCE_SYMBOL}
- 기간: {period_start} ~ {period_end}
- field: Close
- interval: 1d
- currency: {USD/KRW/...}

## Hero 이미지 방향

- 시각 방향 메모: {분석 톤과 결론을 반영한 장면}
- 금지 및 주의: 텍스트, 숫자, 티커, 로고, 워터마크, UI 스크린샷

## 리뷰 기준

- fact-checker: plan/research/draft의 ticker·기간 일치, 근거 출처 누락 여부 확인
- report-designer: 5단계 흐름과 차트 가독성 확인
- content-editor: 문장 명료성, 중복 제거, 투자 권유 표현 배제
- Codex: plan 계약, 파일 계약, blind spot 확인

## 완료/차단 조건

- ticker/기간 확정
- research 요구 충족
- 요청 기간 가격 데이터 확보
- 뉴스 데이터 확보
- selected hero 이미지 확보

## 2026-05-26 추가 데이터 요구사항

- 관련 종목 뉴스: 종목별 최신 뉴스 최소 100건 수집·분류·분석
- 최신 뉴스 5건: 100건 중 최신순 상위 5건을 draft/HTML에 별도 요약 블록으로 표시하고 제목을 클릭 가능한 링크로 연결
- 뉴스 링크: 항목별 원문 URL을 원자료 JSON에 저장하고, URL 미제공 시 제공사 뉴스 탭/검색 fallback임을 명시
- 한국 상장 종목 수급: 가능하면 토스증권 투자자별 매매 동향 참고
- 최종 HTML 본문: `[S1][S2]` 형태의 인라인 참조 표식은 노출하지 않고 References 섹션으로만 정리
