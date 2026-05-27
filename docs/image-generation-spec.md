# Image Generation Spec

주식 경제리포트의 hero 이미지 생성 규칙입니다.

## 목적

- 모든 최종 리포트는 문서 상단에 hero 이미지 1장을 가진다.
- 이미지는 장식용이 아니라 **리포트 전체 메시지를 압축한 시각 요약**이어야 한다.
- 제목만 보고 만들지 말고, **리포트 전체 내용**을 기반으로 프롬프트를 만든다.

## 기본 워크플로

1. build 직전에 리포트 전체를 읽고 프롬프트 3종 생성
2. `python3 scripts/run_stock_image_codex.py <slug>`가 Codex CLI를 열고 `imagegen` skill / built-in `image_gen`으로 후보 3장 생성
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

`image-manifest.json`은 최소 아래 provenance 필드를 포함한다.

```json
{
  "slug": "<slug>",
  "status": "complete",
  "generation_method": "codex-cli-imagegen",
  "generated_with": "Codex CLI $imagegen / built-in image_gen"
}
```

`selected-image.json`은 최소 아래 필드를 포함한다. 이미지 경로는 `assets/<file>.png` 또는
`output/assets/<file>.png`처럼 검증기가 실제 파일로 해석할 수 있어야 한다.

```json
{
  "slug": "<slug>",
  "selected_candidate": 2,
  "image_path": "assets/<slug>-hero-v2.png",
  "reason": "리포트 결론과 가장 잘 맞음",
  "generated_with": "Codex CLI $imagegen / built-in image_gen"
}
```

## 필수 규칙

- 이미지 생성은 Codex CLI 세션이 `$imagegen` skill / built-in `image_gen`으로 수행한다.
- 로컬 스크립트는 프롬프트 준비, Codex CLI 호출, 파일 정리, 계약 검증만 담당한다.
- Pillow/SVG/빈 이미지 같은 절차적 placeholder를 실제 hero 이미지로 대체하지 않는다.
- `status: complete`라도 `generation_method`, `generated_with`, 선택 이미지 메타데이터에 procedural/Pillow/SVG/placeholder 흔적이 있으면 build 검증 실패로 본다.
- **최종 리포트에는 선택된 이미지 1장이 반드시 있어야 한다.**
- 선택 이미지가 없으면 build를 성공 처리하면 안 된다.

## 실행 명령

```bash
python3 scripts/run_stock_image_codex.py <slug>
```

디버깅 시에는 실제 생성 없이 Codex CLI 프롬프트만 확인할 수 있다.

```bash
python3 scripts/run_stock_image_codex.py <slug> --dry-run
```

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
