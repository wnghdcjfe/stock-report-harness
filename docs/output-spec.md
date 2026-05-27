# Output Spec

최종 HTML 출력 규격과 build 단계의 동적 생성 규칙입니다.

## 파일 구조

최종 결과물:

- `output/<slug>.html`
- `output/assets/<slug>-image-manifest.json`
- `output/assets/<slug>-selected-image.json`
- `output/assets/<slug>-price-chart-v1.json` 등 yfinance 원본 가격 데이터 파일

## 필수 frontmatter

```yaml
---
slug: {SLUG}
title: {경제리포트 제목}
subtitle: {부제}
ticker: {yfinance 심볼}
period_start: YYYY-MM-DD
period_end: YYYY-MM-DD
level: beginner | intermediate | advanced
duration_minutes: 12
created_at: YYYY-MM-DD
research_source: research/{SLUG}.md
hero_prompt_file: assets/{SLUG}-image-review.txt
---
```

- `ticker`는 yfinance 심볼이어야 한다. 예: `NVDA`, `005930.KS`
- `period_start`, `period_end`는 사용자의 자연어 요청 기간과 정확히 일치해야 한다.
- 가격 차트 시각화는 최근 1년까지만 허용한다.

## 섹션 구조

필수 섹션:

1. `## 개요`
2. `## 배경`
3. `## 메커니즘`
4. 관련 종목 뉴스 100건이 있는 경우 `## 최신 뉴스 5건 요약`
5. `## 영향과 적용`
6. `## 핵심 정리`
7. `## References`

면책은 별도 섹션으로 draft에 있어도 되지만 최종 HTML에서는 문서 하단 footer note로 렌더한다.

## 마크다운 → HTML 변환

| 마크다운 | HTML |
|---|---|
| `# 제목` | `<h1>` |
| `## 섹션` | `<section><h2>` |
| `### 서브` | `<h3>` |
| `::stat-card ... ::` | `.stat-card` |
| `> 인용` | `.callout` |
| ` ```chart {json} ``` ` | Chart.js `<canvas>` |
| ` ```price-chart ... ``` ` | build 단계에서 yfinance → Chart.js JSON 생성 |

## price-chart 블록

draft에서는 가격 차트를 직접 샘플링해서 쓰지 말고 아래 블록을 사용한다.

```markdown
```price-chart
title: 엔비디아 최근 6개월 일별 종가
aria_label: 엔비디아의 요청 기간 전체 일별 종가 추이 차트
field: Close
interval: 1d
currency: USD
```
```

동작 규칙:

- build가 `ticker`, `period_start`, `period_end` frontmatter를 읽는다.
- `yfinance`에서 요청 기간 전체의 실제 일별 데이터를 가져온다.
- build가 Chart.js line chart JSON으로 확장한다.
- x축 labels는 실제 거래일 `YYYY-MM-DD`여야 한다.
- 생성된 원본 데이터는 `output/assets/<slug>-price-chart-v{N}.json` 으로 저장한다.

## Hero image 규칙

- build 전에 전체 리포트 기반 프롬프트 3종을 생성한다.
- 에이전트가 `image_gen`으로 3장을 생성한다.
- 선택 결과는 `output/assets/<slug>-selected-image.json` 으로 남긴다.
- **최종 리포트에는 hero 이미지 1장이 반드시 포함되어야 한다.**
- 선택 이미지가 없거나 파일이 없으면 build 실패.

## 최신 뉴스 5건 요약 렌더링

- 입력: `output/assets/<slug>-*-latest100.json` 또는 이에 준하는 100건 뉴스 원자료.
- 정렬: `published_at_utc`, `createdAt`, `updatedAt`, `date` 중 파싱 가능한 최신 시간을 기준으로 내림차순 정렬 후 상위 5건.
- HTML 구조: `<section id="latest-news-5"><h2>최신 뉴스 5건 요약</h2><ol class="latest-news-list">...</ol></section>`.
- 각 항목: 날짜·매체·제목 링크·요약·가격/수급 해석을 포함한다.
- 링크: 항목별 원문 URL이 있으면 `<a href="..." target="_blank" rel="noopener noreferrer">제목</a>`로 렌더한다.
- fallback: 항목별 URL이 없으면 제공사 뉴스 탭 또는 제목 검색 URL을 쓰되, 화면 또는 데이터에 `원문 URL 미제공`을 표시한다. 존재하지 않는 원문 URL을 추측해 만들면 안 된다.
- 최종 HTML 본문에는 `[S1]` 같은 인라인 참조 표식은 노출하지 않는다.

## build 검증

build 단계에서 아래 항목을 검증한다.

1. `# 제목` 정확히 1개
2. 필수 섹션 존재
3. 본문 footnote 표기 금지, 출처는 References로만 모음
4. `level`, `duration_minutes`, `period_start`, `period_end` 존재
5. 모든 차트에 `ariaLabel` 존재
6. 가격 차트는 yfinance 기반이고 요청 기간과 일치
7. 가격 차트는 최근 1년 이내 요청만 허용
8. 선택된 hero 이미지 1개 존재
9. 뉴스 100건 원자료가 있으면 최신 뉴스 5건 요약과 클릭 가능한 링크 존재
