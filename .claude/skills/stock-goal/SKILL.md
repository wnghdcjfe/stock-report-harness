---
name: stock-goal
description: "종단 간 주식 리포트 파이프라인. '삼성전자 30일 분석' 같은 자연어 요청 하나로 plan → research → draft → image → review → build 전체를 자동 실행해 output/<slug>.html을 생성한다."
---

# 주식 목표 스킬

자연어 요청 하나로 stock-report-harness 전체 파이프라인을 순차 실행해 최종 HTML 리포트를 생성한다.

## 파이프라인

```
plan → research → draft → image → review → build
```

각 단계는 해당 `/stock-*` 스킬의 계약을 그대로 따른다.
실패 시 해당 단계에서 멈추고 사용자에게 상태를 보고한다.

## 핵심 규칙: 단일 턴 연속 실행

이 스킬의 가장 중요한 규칙이다. 반드시 지켜야 한다.

1. **전체 파이프라인을 하나의 응답(턴)에서 끝까지 실행한다.**
   plan을 만들고 멈추지 않는다. research를 끝내고 멈추지 않는다.
   draft를 쓰고 멈추지 않는다. 6단계 전부를 이 턴에서 완료한다.

2. **`Skill` 도구를 사용해 하위 `/stock-*` 스킬을 호출하지 않는다.**
   각 하위 스킬의 SKILL.md를 직접 읽고 그 Procedure를 이 턴 안에서 인라인으로 실행한다.
   `Skill` 호출은 턴 경계를 만들어 중단을 유발하므로 금지한다.

3. **단계 완료 메시지를 사용자에게 출력하지 않는다.**
   "plan이 완료되었습니다", "다음 단계는...", "research 결과:" 같은
   중간 보고를 사용자에게 보내면 턴이 끝나므로 금지한다.
   진행 상황은 내부적으로만 추적한다.

4. **사용자에게 질문하지 않는다.** AskUserQuestion을 호출하지 않는다.
   "진행할까요?", "확인해주세요" 같은 확인을 구하지 않는다.

5. **다음 경우에만 이 턴을 종료한다:**
   - 최종 build가 성공해 `output/<slug>.html`이 생성되고 프리뷰 URL을 보고할 때
   - 가격 데이터 조회 불가, 외부 도구 부재 등 실제 `blocked` 조건이 발생했을 때
   - review/fix 루프가 최대 3회에 도달했을 때

6. **단계 사이에 텍스트를 출력하지 않는다.**
   도구 호출(Read, Write, Bash 등)만 연속으로 실행한다.
   사용자에게 보이는 텍스트 출력은 최종 완료 보고 한 번뿐이다.

## 절차

### 1단계: 기획

1. 요청을 파싱한다 (종목/ETF/섹터, 기간, 대상 독자).
2. `/stock-plan` 스킬 계약(`.claude/skills/stock-plan/SKILL.md`)에 따라 `plan/<slug>.md`를 작성한다.
3. slug를 확정하고 이후 모든 단계에서 동일 slug를 사용한다.
4. **멈추지 않고 즉시 2단계로 진행한다.**

### 2단계: 리서치

1. `plan/<slug>.md`가 존재하는지 확인한다.
2. `/stock-research` 스킬 계약에 따라 실행한다.
   - yfinance 일봉 가격 데이터 수집
   - 뉴스 최소 100건 수집·분류
   - `research/<slug>.md` 및 `output/assets/` 원자료 생성
3. 가격 데이터가 조회 불가하면 `blocked`로 보고하고 멈춘다.
4. **멈추지 않고 즉시 3단계로 진행한다.**

### 3단계: 초안

1. `plan/<slug>.md`와 `research/<slug>.md`가 존재하는지 확인한다.
2. `/stock-draft` 스킬 계약에 따라 `drafts/<slug>.md`를 작성한다.
   - 필수 섹션: 개요, 배경, 메커니즘, 영향과 적용, References
   - price-chart 블록 선언, 투자 권유 금지
3. **멈추지 않고 즉시 4단계로 진행한다.**

### 4단계: 이미지

1. plan, research, draft가 모두 존재하는지 확인한다.
2. `/stock-image` 스킬 계약에 따라 Codex CLI를 열어 `imagegen` skill로 히어로 이미지 3장을 생성한다.
   - 프롬프트 3개 → PNG 3장 → 스코어링 → 1장 선택
   - `output/assets/<slug>-selected-image.json` 생성
3. Codex CLI 또는 이미지 생성 도구가 없으면 프롬프트와 blocked 매니페스트만 남기고 `blocked`로 보고한다.
4. **멈추지 않고 즉시 5단계로 진행한다.**

### 5단계: 리뷰

1. plan, research, draft, selected image가 모두 존재하는지 확인한다.
2. `/stock-review` 스킬 계약에 따라 4-way 리뷰를 실행한다.
   - fact-checker, report-designer, content-editor, codex-independent
3. `reviews/<slug>.md`에 결과를 기록한다.
4. `needs_fix`이면 해당 단계로 돌아가 수정 후 재리뷰한다 (최대 3회).
5. `blocked`이면 사용자에게 보고하고 멈춘다.
6. **멈추지 않고 즉시 6단계로 진행한다.**

### 6단계: 빌드

1. review `status: pass`인지 확인한다.
2. `/stock-build` 스킬 계약에 따라 `output/<slug>.html`을 생성한다.
   - yfinance 실데이터 차트, 히어로 이미지 삽입, 인라인 마커 제거, footer 면책 문구
3. 로컬 프리뷰 서버를 시작하고 URL을 보고한다.
4. **이제 완료 보고를 출력하고 턴을 종료한다.**

## 실행 규칙

- 각 단계는 반드시 선행 산출물이 존재해야 시작한다.
- 단계 간 `slug`, `ticker`, `period_start`, `period_end`가 일관되어야 한다.
- review에서 `needs_fix`가 나오면 fix → re-review 루프를 최대 3회 시도한다.
- 동일 차단 이슈가 3회 반복되면 `blocked`로 전환하고 멈춘다.

## 제약 조건

- AGENTS.md의 모든 계약과 금지 사항을 준수한다.
- 임의 가격 데이터, 조작한 URL, 투자 권유 표현을 사용하지 않는다.
- 각 `/stock-*` 스킬의 산출물 경로와 포맷 계약을 그대로 따른다.

## 완료 보고

최종 build 성공 후 단 한 번만 출력한다:
- 생성된 전체 산출물 목록 (plan, research, draft, images, review, html)
- 최종 HTML 경로: `output/<slug>.html`
- 프리뷰 URL
- 파이프라인 중 발생한 이슈 요약 (있는 경우)
