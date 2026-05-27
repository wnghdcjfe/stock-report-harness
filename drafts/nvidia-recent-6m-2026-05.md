---
slug: nvidia-recent-6m-2026-05
title: 엔비디아 최근 6개월 동향
subtitle: 블랙웰 수요, 루빈 로드맵, 중국 변수, 그리고 너무 높아진 기대가 함께 만든 6개월
ticker: NVDA
currency: USD
level: beginner
prerequisites: []
duration_minutes: 12
created_at: 2026-05-26
period_start: 2025-11-21
period_end: 2026-05-26
research_source: research/nvidia-recent-6m-2026-05.md
hero_prompt_file: assets/nvidia-recent-6m-2026-05-image-review.txt
---

# 엔비디아 최근 6개월 동향

> 2025-11-21부터 2026-05-26까지 엔비디아는 실적이 세 분기 연속 커졌지만, 주가는 실적 숫자만이 아니라 차세대 칩 로드맵과 중국 규제, 그리고 높아진 기대치까지 함께 반영했다.

---

## 개요

최근 6개월 엔비디아 주가는 Barchart 기준 +20.38% 올랐다. 같은 구간 저점은 2026-03-30의 164.27달러, 고점은 2026-05-14의 236.54달러, 2026-05-26 종가는 215.33달러였다.

::stat-card
label: 6개월 주가
title: NVDA 6개월 수익률
value: +20.38%
tone: up
compare: 2025-11-21 ~ 2026-05-26
::

이 움직임을 한 문장으로 줄이면 이렇다. **엔비디아는 실적이 계속 좋아졌고, 시장은 그 다음 칩까지 미리 가격에 넣었지만, 기대가 너무 높아질수록 발표 직후 반응은 오히려 차가워질 수 있었다.**

---

## 배경

이 6개월 동안 엔비디아를 이해하려면 세 가지 배경이 필요하다.

- 첫째, **블랙웰 수요 강세**다. 2025년 11월 엔비디아는 FY26 3분기 매출 570억 달러, 데이터센터 매출 512억 달러를 발표했고, 젠슨 황은 블랙웰 판매가 매우 강하고 클라우드 GPU가 매진 상태라고 설명했다.
- 둘째, **로드맵의 연장**이다. 2026년 1월 엔비디아는 CES에서 루빈 플랫폼을 공개했다. 시장은 “지금 잘 파는 회사”가 아니라 “다음 세대도 계속 주도할 회사”로 엔비디아를 보기 시작했다.
- 셋째, **중국 변수**다. H200의 중국 판매는 미국 수출 규제와 중국 승인이라는 두 개의 문을 모두 통과해야 했고, 이 과정이 2026년 2월과 3월 주가 해석의 중요한 변수였다.


---


```price-chart
title: ???? ?? 6?? ?? ??
aria_label: ????? 2025-11-21?? 2026-05-26?? ?? ?? ?? ?? ?? ?? ??
field: Close
interval: 1d
currency: USD
```

## 메커니즘

### 1. 숫자는 분명히 강했다

최근 3번의 핵심 실적 발표만 이어 보면 엔비디아의 성장 속도는 매우 가파르다.

- FY26 3분기 매출: 570억 달러
- FY26 4분기 매출: 681억 달러
- FY27 1분기 매출: 816억 달러

데이터센터 매출도 512억 달러 → 623억 달러 → 752억 달러로 커졌다. 즉, 최근 6개월 엔비디아 스토리의 중심은 여전히 게임이 아니라 **AI 데이터센터**였다.

```chart
{
  "type": "bar",
  "summaryCards": [
    {"label": "Q3 FY26", "value": "$57.0B", "tone": "up"},
    {"label": "Q4 FY26", "value": "$68.1B", "tone": "up"},
    {"label": "Q1 FY27", "value": "$81.6B", "tone": "up"}
  ],
  "data": {
    "labels": ["Q3 FY26", "Q4 FY26", "Q1 FY27"],
    "datasets": [
      {
        "label": "매출(십억달러)",
        "data": [57.0, 68.1, 81.6],
        "backgroundColor": ["#7AA6D8", "#4E87C2", "#185FA5"],
        "borderRadius": 6,
        "borderSkipped": false,
        "barThickness": 56
      },
      {
        "label": "데이터센터 매출(십억달러)",
        "data": [51.2, 62.3, 75.2],
        "backgroundColor": ["#B7DCCF", "#63B69B", "#1D9E75"],
        "borderRadius": 6,
        "borderSkipped": false,
        "barThickness": 56
      }
    ]
  },
  "options": {
    "responsive": true,
    "maintainAspectRatio": false,
    "plugins": {"legend": {"display": true}},
    "scales": {
      "y": {"grid": {"color": "rgba(115,114,108,0.12)"}},
      "x": {"grid": {"display": false}}
    }
  },
  "ariaLabel": "엔비디아의 최근 세 분기 매출과 데이터센터 매출 비교 차트. 전체 매출과 데이터센터 매출이 모두 꾸준히 증가했다."
}
```

초보자 관점에서 여기서 중요한 포인트는 하나다. **엔비디아의 성장은 단순히 칩을 많이 판다는 뜻이 아니라, AI 인프라 예산이 실제 매출로 전환되고 있다는 뜻**이다.

### 2. 시장은 현재보다 다음 세대를 더 크게 봤다

2026년 1월 CES에서 공개된 루빈 플랫폼은 단순 신제품 발표가 아니었다. 베라 CPU, 루빈 GPU, NVLink 6 등 여러 칩을 묶은 차세대 시스템 로드맵이 시장에 제시됐다. 3월에는 젠슨 황이 블랙웰과 루빈의 매출 기회가 2027년 말까지 1조 달러를 넘을 수 있다고 말했다.

이 대목이 중요한 이유는, 주가가 “이번 분기 실적”만 따라 움직이지 않았기 때문이다. 시장은 **블랙웰의 현재 수요 + 루빈의 미래 수요**를 합쳐서 엔비디아를 평가했다.

### 3. 그런데 강한 숫자만으로는 항상 부족했다

2026년 5월 20일 엔비디아는 다시 기록적인 실적을 발표했다. 매출은 816억 달러였고, 다음 분기 가이던스는 910억 달러 ±2%였다. 동시에 자사주 매입 한도를 800억 달러 늘리고, 분기 배당도 0.01달러에서 0.25달러로 올렸다.

그런데 로이터는 실적 발표 직후 시간외 주가가 1.6% 하락했다고 전했다. 이유는 단순하다. 시장은 이미 “좋은 실적”을 어느 정도 기본값으로 보고 있었고, 이제는 **성장이 언제까지 이어질지**, **경쟁이 더 세지지 않을지**를 보기 시작했기 때문이다.

즉, 엔비디아는 최근 6개월 동안 **좋은 회사라서 오른 종목**이면서 동시에 **좋은 회사라서 기대치가 너무 높아진 종목**이기도 했다.

### 4. 중국 변수는 사라지지 않았다

2월 24일에는 미국 상무부 당국자가 중국 고객에게 H200이 아직 판매되지 않았다고 말했다. 하지만 3월 17일 로이터는 엔비디아가 베이징 승인을 받아 중국향 H200 판매 재개 길을 열었다고 보도했다.

여기서 볼 점은 두 가지다.

- 중국은 엔비디아에게 여전히 큰 시장이었다.
- 하지만 그 시장은 자유롭게 열려 있는 시장이 아니라 규제와 외교 변수에 따라 열리고 닫히는 시장이었다.

그래서 최근 6개월 엔비디아를 볼 때는 “수요가 강하다”와 “모든 시장에 다 팔 수 있다”를 같은 말로 보면 안 된다.

---

## 영향과 적용

이 사례는 반도체 주식을 볼 때 무엇을 함께 봐야 하는지를 잘 보여준다.

- **실적 속도**: 매출과 데이터센터 매출이 얼마나 빨리 커지는가
- **로드맵 길이**: 블랙웰 다음에 무엇이 있는가
- **규제 변수**: 특히 중국처럼 큰 시장에서 판매 제약이 있는가
- **기대치 관리**: 숫자가 좋아도 시장 기대보다 덜 놀라우면 주가가 쉬어갈 수 있는가
- **참여자 흐름**: 개인은 급락 때 매수하는지, 기관은 섹터 전체를 사는지

개인과 기관의 해석도 분리해서 볼 필요가 있다. 미국 주식은 한국 주식처럼 외국인·기관·개인 수급 표가 일상적으로 함께 붙지 않는 경우가 많아서, 이 리포트에서는 외국인이라는 단일 항목보다 개인·기관·해외 투자자 흐름을 나눠 보는 편이 더 현실적이다.

- 개인투자자는 2025년 1월 28일 딥시크 충격 때 엔비디아를 기록적으로 순매수한 사례가 있었다. 다만 이 사례는 이번 6개월 구간 이전 사례다.
- 기관투자자는 2026년 1분기 기준 반도체·AI 인프라 섹터 전반을 적극적으로 매수했다.

즉, 최근 엔비디아는 **한 종목의 개별 스토리**이면서 동시에 **AI 인프라 섹터 전체의 대표 종목**으로 읽혀 왔다.

---

## 한 줄 정리

- 최근 6개월 엔비디아는 **실적 가속**과 **차세대 로드맵** 덕분에 강한 주가 흐름을 만들었다.
- 하지만 **중국 규제 변수**와 **너무 높아진 기대치** 때문에 좋은 발표 뒤에도 단기 조정이 나올 수 있었다.
- 그래서 엔비디아를 볼 때는 현재 분기 숫자만이 아니라 **다음 칩, 다음 고객, 다음 규제**까지 같이 봐야 한다.

---

## References

- NVIDIA Investor Relations — NVIDIA Announces Financial Results for Third Quarter Fiscal 2026 (2025-11-19) — https://investor.nvidia.com/news/press-release-details/2025/NVIDIA-Announces-Financial-Results-for-Third-Quarter-Fiscal-2026/ — Tier A
- NVIDIA Investor Relations — NVIDIA Announces Financial Results for Fourth Quarter and Fiscal 2026 (2026-02-25) — https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Announces-Financial-Results-for-Fourth-Quarter-and-Fiscal-2026/ — Tier A
- NVIDIA Investor Relations — NVIDIA Announces Financial Results for First Quarter Fiscal 2027 (2026-05-20) — https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Announces-Financial-Results-for-First-Quarter-Fiscal-2027/default.aspx — Tier A
- NVIDIA Investor Relations — NVIDIA Kicks Off the Next Generation of AI With Rubin — Six New Chips, One Incredible AI Supercomputer (2026-01-05) — https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Kicks-Off-the-Next-Generation-of-AI-With-Rubin--Six-New-Chips-One-Incredible-AI-Supercomputer/default.aspx — Tier A
- Reuters via Investing.com — Nvidia CEO Huang sees strong demand for Blackwell chips (2025-11-07) — https://www.investing.com/news/stock-market-news/nvidia-ceo-huang-sees-strong-demand-for-blackwell-chips-4344292 — Tier B
- Reuters via Investing.com — China has not yet received any Nvidia H200 chips, US official says (2026-02-24) — https://www.investing.com/news/stock-market-news/china-has-not-yet-received-any-nvidia-h200-chips-us-official-said-4522567 — Tier B
- Reuters via Investing.com — Nvidia gets Beijing’s nod for H200 chip sales, adapts Groq chip for China, sources say (2026-03-17) — https://www.investing.com/news/stock-market-news/chinese-authorities-approve-nvidias-h200-ai-chip-sales-source-says-4567348 — Tier B
- Reuters via Investing.com — Nvidia sales opportunity for Blackwell, Rubin chips more than $1 trillion by 2027 (2026-03-17) — https://www.investing.com/news/stock-market-news/nvidia-sales-opportunity-for-blackwell-rubin-chips-more-than-1-trillion-by-2027-4566514 — Tier B
- Reuters via Investing.com — Nvidia bets on new data center chips for growth as sales outlook tops estimates (2026-05-20) — https://www.investing.com/news/stock-market-news/nvidia-forecasts-quarterly-revenue-above-estimates-announces-80-billion-share-buyback-4702363 — Tier B
- Barchart — NVDA Performance Report for Nvidia Corp Stock (accessed 2026-05-26) — https://www.barchart.com/stocks/quotes/NVDA/performance — Tier B
- Reuters via Investing.com — Retail investors bought record amount of Nvidia stock in DeepSeek rout (2025-01-28) — https://www.investing.com/news/stock-market-news/retail-investors-bought-record-amount-of-nvidia-stock-in-deepseek-rout-3833728 — Tier B
- Reuters via Investing.com — Institutional investors boosted holdings of AI infrastructure plays during first quarter (2026-05-15) — https://www.investing.com/news/stock-market-news/institutional-investors-boosted-holdings-of-ai-infrastructure-plays-during-first-quarter-4693317 — Tier B

---

## 투자 판단 면책

이 리포트는 교육 및 정보 제공 목적을 위해 작성되었습니다.
특정 종목의 매수·매도를 권유하지 않으며 투자 자문이 아닙니다.
모든 투자 판단과 그 결과에 대한 책임은 투자자 본인에게 있습니다.
리포트 내용은 2026-05-26 기준 공개 정보를 바탕으로 정리되었으며,
이후 변경된 사실이 반영되지 않았을 수 있습니다.
