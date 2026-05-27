# Image Generation Spec

주식 경제리포트의 hero 이미지 생성 규칙입니다.

## 목적

- 모든 최종 리포트는 문서 상단에 hero 이미지 1장을 가진다.
- 이미지는 장식용이 아니라 **리포트 전체 메시지를 압축한 시각 요약**이어야 한다.
- 제목만 보고 만들지 말고, **리포트 전체 내용**을 기반으로 프롬프트를 만든다.

## 기본 워크플로

1. build 직전에 리포트 전체를 읽고 프롬프트 3종 생성
2. 에이전트가 `image_gen`으로 후보 3장 생성
3. 후보별 점수 JSON 생성
4. 최고점 1장 선택
5. 선택된 1장만 최종 HTML hero 이미지로 렌더

## 필수 산출물

- `output/assets/<slug>-hero-v1.prompt.txt`
- `output/assets/<slug>-hero-v2.prompt.txt`
- `output/assets/<slug>-hero-v3.prompt.txt`
- `output/assets/<slug>-hero-v1.png`
- `output/assets/<slug>-hero-v2.png`
- `output/assets/<slug>-hero-v3.png`
- `output/assets/<slug>-hero-v1.score.json`
- `output/assets/<slug>-hero-v2.score.json`
- `output/assets/<slug>-hero-v3.score.json`
- `output/assets/<slug>-image-review.txt`
- `output/assets/<slug>-image-manifest.json`
- `output/assets/<slug>-selected-image.json`

## 필수 규칙

- 이미지 생성은 에이전트가 직접 `image_gen`으로 수행한다.
- 로컬 스크립트는 프롬프트 생성, 파일 정리, 선택만 담당한다.
- **최종 리포트에는 선택된 이미지 1장이 반드시 있어야 한다.**
- 선택 이미지가 없으면 build를 성공 처리하면 안 된다.

## 프롬프트 작성 규칙

프롬프트는 반드시 아래 정보를 반영한다.

- 리포트 제목
- 부제
- ticker / 기업 맥락
- 요청 기간
- 각 주요 섹션의 핵심 메시지
- 결론의 톤(성장, 부담, 변곡점, 리스크 등)

금지:

- 텍스트, 숫자, 티커, 로고, 워터마크 삽입
- 실제 앱/대시보드 스크린샷처럼 보이는 구성
- 리포트와 무관한 범용 이미지 재사용

## 리뷰 기준

1. 리포트 전체 적합성
2. 기업/섹터/촉매 맥락 적합성
3. 시각적 명확성
4. 프리미엄 프레젠테이션 품질
5. 절제된 구성
