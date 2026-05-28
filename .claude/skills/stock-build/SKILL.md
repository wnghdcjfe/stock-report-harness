---
name: stock-build
description: 최종 주식 리포트 HTML을 빌드한다. 리뷰 pass와 선택된 히어로 이미지가 존재한 뒤에만 /stock-build <slug>로 사용하며, 계약 검증, yfinance 가격 차트 JSON 생성, output/<slug>.html 렌더링, 인라인 출처 표식 제거, 하단 투자 면책 문구 추가를 수행한다.
---

# 주식 빌드 스킬

승인된 산출물로부터 새로운 주장을 추가하지 않고 `output/<slug>.html`을 생성한다.
빌드 구현은 결정적이다: HTML을 직접 작성하지 않고 `python3 scripts/build_report.py <slug>`를 사용한다.

## 선행 조건

필수 파일이 존재해야 한다:

- `plan/<slug>.md`
- `research/<slug>.md`
- `drafts/<slug>.md`
- `reviews/<slug>.md` (`status: pass`)
- `output/assets/<slug>-image-manifest.json` (`status: complete`, `generation_method: codex-cli-imagegen`, `generated_with` 포함)
- `output/assets/<slug>-selected-image.json`
- selected-image JSON이 참조하는 선택된 히어로 PNG

하나라도 없거나 리뷰가 pass가 아니면 중단하고 필요한 `/stock-*` 단계로 안내한다.

## 절차

1. 빌드 전 계약 게이트를 실행한다:
   `python3 scripts/validate_report_contract.py <slug>`
   - 실패하면 오류가 지목하는 상위 단계로 안내하고 빌드하지 않는다.
2. 결정적 빌더를 실행한다:
   `python3 scripts/build_report.py <slug>`
   - 빌더가 plan, research, draft, review 간 프론트매터 일관성을 검증한다.
   - 빌더가 요청 기간 전체의 실제 yfinance 일봉 데이터로 `output/assets/<slug>-price-chart-v1.json`을 생성/갱신한다.
   - 빌더가 Markdown/프론트매터를 `design/toss_design.md`의 토스 디자인 시스템으로 `output/<slug>.html`에 렌더링하고 인라인 출처 표식을 제거한다 (`sample/skhynix.html`을 참조 구성으로 사용).
3. 엄격한 빌드 후 게이트를 확인하거나 명시적으로 실행한다:
   `python3 scripts/validate_report_contract.py <slug> --require-html --require-price-chart`
4. 생성된 HTML은 반드시:
   - 토스 스타일 모바일 셸 사용: `max-width: 560px`, 고정 앱바, 티커 히어로 카드, Pretendard, 토스 블루 강조색, 회색 8px 섹션 구분선, 한국 주식 색상 규칙 (상승=빨강, 하락=파랑)
   - 선택된 히어로 이미지를 상단 근처에 한 번, 조용한 토스 카드로 스타일링해 리포트 에셋 계약을 충족
   - `price-chart` 블록을 토스 라인 스타일링과 우측 Y축의 접근성 Chart.js 호환 차트로 렌더링
   - draft/research에 급등/급락 이벤트 메타데이터가 있으면 가격 차트에서 해당 날짜를 강조하고 차트 근처에 짧은 이벤트 카드를 렌더링
   - 펜스드 `chart` JSON이 있으면 차트로 렌더링
   - 최종 본문에서 인라인 `[S1]`, `[N1]` 표식을 제거
   - References 섹션은 출처 상세와 함께 유지
   - 하단에 교육 정보 전용, 투자 조언이 아님을 명시하는 면책 문구 포함
   - 긴 뉴스 링크가 콘텐츠 열을 넘치지 않도록 처리 (기사 링크, 목록 항목, 참조 URL에 `overflow-wrap: anywhere` / `word-break: break-word`)
5. `validate_report_contract.py`가 최종 검사를 시행한다:
   - HTML 파일이 존재하고 비어있지 않은지
   - 선택된 이미지 경로가 유효한지
   - 가격 차트 JSON이 존재하고 티커/기간이 일치하는지
   - References 외부에 인라인 출처 표식이 남아있지 않은지
   - draft/research 범위를 넘는 새 주장이 추가되지 않았는지
6. 빌드 성공 후 로컬 프리뷰 서버를 시작하고 리포트 직접 URL을 표시한다:
   - 권장 명령: `node server.js <slug>`
   - 포트 3000이 사용 중이면 알 수 없는 프로세스를 종료하지 않는다. 기존 서버가 응답하면 `http://localhost:3000/<slug>.html`을 보고하고, 아니면 `PORT=<빈포트> node server.js <slug>`를 사용해 해당 URL을 보고한다.
   - 콘솔/보고에 `http://localhost:3000/<slug>.html` 같은 직접 링크를 반드시 포함한다.

## 제약 조건

- 리뷰 pass 없이 빌드하지 않는다.
- 선택된 히어로 이미지 없이 빌드하지 않는다.
- 절차적/Pillow/SVG/플레이스홀더 히어로 출처로 빌드하지 않는다.
- 가짜 가격이나 플레이스홀더 차트를 사용하지 않는다.
- 빌드 중 새로운 시장 주장을 추가하지 않는다. research/draft를 먼저 수정한다.

## 완료 보고

최종 HTML 경로, 가격 차트 JSON 경로, 선택된 히어로 경로, 프리뷰 URL, 검증 증거를 보고한다.
