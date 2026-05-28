---
name: stock-draft
description: plan/<slug>.md와 research/<slug>.md를 기반으로 교육적 한국어 주식 리포트 초안을 작성한다. /stock-draft <slug>로 사용하며, 필수 섹션, price-chart 블록, References, 출처 표식을 포함하고 투자 조언을 금지한다.
---

# 주식 초안 스킬

plan과 research를 기반으로 `drafts/<slug>.md`를 작성한다.

## 선행 조건

- `plan/<slug>.md`와 `research/<slug>.md`가 존재해야 한다.
- research를 사실 경계로 사용한다. research에 출처가 없는 새로운 주장을 추가하지 않는다.

## 절차

1. plan과 research를 읽고 `ticker`, `period_start`, `period_end`가 일치하는지 검증한다.
2. `drafts/<slug>.md`에 최소 다음 프론트매터를 포함해 작성한다:
   `slug`, `title`, `subtitle`, `ticker`, `period_start`, `period_end`, `level`, `duration_minutes`, `created_at`, `plan_source`, `research_source`.
3. H1을 정확히 하나 포함한다.
4. 필수 섹션:
   - `## 개요`
   - `## 배경`
   - `## 메커니즘`
   - `## 최신 뉴스 5건 요약` (100건 뉴스 데이터가 있을 때)
   - `## 영향과 적용`
   - `## References`
   - 투자 판단 면책/주의 문구
5. 가격 차트는 펜스드 `price-chart` 블록으로만 선언한다. 본문에 가격 배열을 붙여넣지 않는다.
6. 리뷰/빌드 검증을 위해 `[S1]`, `[N1]` 등 출처 표식을 초안에 유지한다.
7. 가격 이외의 차트를 추가할 때는 펜스드 `chart` 블록에 유효한 JSON과 `ariaLabel`을 포함한다.
8. 미국 또는 해외 주식은 사용자가 명시적으로 요청하지 않는 한 한국식 `수급과 투자자 구도` 섹션을 별도로 추가하지 않는다. 한국 상장 주식은 개인·외국인·기관 수급을 가능한 경우 포함한다.
9. 개요 가격 차트 논의에서 요청 기간 내 가장 큰 급등과 급락을 식별하고, 해당 날짜 전후의 역사적 사건을 웹/출처에서 조회해 출처 표식과 함께 차트 옆에 요약한다. 출처 없이 인과관계를 추론하지 않는다.

## 스타일과 안전

- 한국어, 교육적, plan에서 달리 지정하지 않는 한 초급자 친화적.
- 불확실성과 리스크를 명시하되 매매 지시를 하지 않는다.
- "사세요/팔아야/보장/확실" 같은 투자 조언 표현을 피한다.
- 간결한 단락으로 메커니즘을 설명한다: 무엇이 일어났고, 왜 중요하며, 무엇을 지켜봐야 하는지.

## 완료 보고

`drafts/<slug>.md`, H1 제목, 필수 섹션 존재 여부, 다음 명령어를 보고한다: `/stock-image <slug>`.

`stock-goal`에서 호출된 경우 이 보고는 내부 체크포인트일 뿐이다. 멈추거나 사용자를 기다리지 않고 즉시 `/stock-image <slug>`로 진행한다.
