---
slug: {SLUG}
title: {리포트 제목}
subtitle: {부제}
ticker: {YFINANCE_SYMBOL}
period_start: {YYYY-MM-DD}
period_end: {YYYY-MM-DD}
level: beginner | intermediate | advanced
prerequisites: []
duration_minutes: 12
created_at: {YYYY-MM-DD}
plan_source: plan/{SLUG}.md
research_source: research/{SLUG}.md
hero_prompt_file: assets/{SLUG}-image-review.txt
---

# {리포트 제목}

> {한 줄 요약}

---

## 개요

{개요}

::stat-card
label: {핵심 지표}
title: {지표 제목}
value: {값}
tone: up | down | neutral
compare: {비교 문구}
::

---

## 배경

- {배경 1}
- {배경 2}
- {핵심 이슈}
- {시장 맥락}
- {데이터 포인트}

```price-chart
title: {종목명 기간별 종가 추이}
aria_label: {종목 종가가 기간 동안 어떻게 움직였는지 설명하는 차트}
field: Close
interval: 1d
currency: USD
```

---

## 메커니즘

### {메커니즘 1}
{설명}

> "{핵심 문장}" — {출처}

### {메커니즘 2}
{설명}

---

## 뉴스 100건 점검

- 관련 종목 최신 뉴스 최소 100건을 이슈별로 분류한다.
- 한국 상장 종목은 가능하면 토스증권 종목 뉴스 탭을 참고한다.

---

## 최신 뉴스 5건 요약

1. **{YYYY-MM-DD HH:MM · 매체 · 핵심 이슈}** — [{뉴스 제목}]({원문_URL})
   - 요약: {1~2문장 요약}
   - 가격/수급 해석: {가격, 수급, 리스크 해석}
2. **{YYYY-MM-DD HH:MM · 매체 · 핵심 이슈}** — [{뉴스 제목}]({원문_URL})
   - 요약: {1~2문장 요약}
   - 가격/수급 해석: {가격, 수급, 리스크 해석}

> 항목별 원문 URL이 없으면 원문 URL을 추측하지 말고 제공사 뉴스 탭/제목 검색 링크를 fallback으로 걸고 fallback임을 표시한다.

---

## 투자자별 매매 동향

- 한국 상장 종목은 가능하면 토스증권 투자자별 매매 동향을 참고한다.
- 개인, 외국인, 기관, 기타법인 누적 순매수와 최근 거래일 수급을 구분한다.

---

## 영향과 적용

- {적용 포인트 1}
- {적용 포인트 2}
- {리스크 요인}

---

## References

- {출처명} — {제목} ({YYYY-MM-DD}) — {URL} — Tier {A|B|C}

---

## 투자 유의 사항

투자 유의: 이 보고서는 교육 목적의 시장 해설이며 매수·매도 권유가 아닙니다. 모든 투자는 원금 손실 가능성이 있습니다.
