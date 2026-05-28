---
name: stock-image
description: 주식 리포트 히어로 이미지를 생성하고 선택한다. plan, research, draft가 존재한 뒤 /stock-image <slug>로 사용하며, 프롬프트 3개, PNG 후보 3장, 스코어 JSON, image-manifest.json, image-review.txt, selected-image.json을 생성한다.
---

# 주식 이미지 스킬

리포트 slug에 필요한 히어로 이미지 에셋 세트를 생성한다.
이미지 래스터 생성은 Codex CLI 세션의 `imagegen` 스킬이 담당한다.
외부 Claude 파이프라인은 파일 계약을 관리·검증하며, 로컬 절차적 플레이스홀더 이미지를 대체물로 사용하지 않는다.

## 선행 조건

- `plan/<slug>.md`, `research/<slug>.md`, `drafts/<slug>.md`가 존재해야 한다.
- 프롬프트 작성 전 세 파일을 모두 읽는다. 제목만으로 프롬프트를 작성하지 않는다.

## 절차

1. Codex CLI 이미지 실행기를 실행한다:
   ```bash
   python3 scripts/run_stock_image_codex.py <slug>
   ```
   이 래퍼는:
   - `plan/<slug>.md`, `research/<slug>.md`, `drafts/<slug>.md`를 읽고
   - 프롬프트 3개를 준비하고
   - 이 리포지토리에서 `codex exec`을 열고
   - 내부 Codex 세션에 `$imagegen` / 내장 `image_gen` 사용을 지시하고
   - Codex 종료 후 필수 PNG/JSON 출력을 검증한다
2. 필수 프롬프트 출력:
   - `output/assets/<slug>-hero-v1.prompt.txt`
   - `output/assets/<slug>-hero-v2.prompt.txt`
   - `output/assets/<slug>-hero-v3.prompt.txt`
3. Codex `imagegen`이 생성하는 필수 PNG 후보:
   - `output/assets/<slug>-hero-v1.png`
   - `output/assets/<slug>-hero-v2.png`
   - `output/assets/<slug>-hero-v3.png`
4. 필수 스코어 JSON:
   - `output/assets/<slug>-hero-v1.score.json` 등
   - 리포트 적합성, 기업/섹터 적합성, 명확성, 프리미엄 품질, 절제도 점수를 포함한다.
5. 다음 파일을 작성한다:
   - `output/assets/<slug>-image-review.txt`
   - `output/assets/<slug>-image-manifest.json`
   - `output/assets/<slug>-selected-image.json`
   - 매니페스트 JSON에 `status: complete`, `generation_method: codex-cli-imagegen`, `generated_with`를 포함한다.
   - 선택 이미지 JSON에 최소 `slug`, `selected_candidate`, `image_path` 또는 `selected_image`, `reason`, `generated_with`를 포함한다.
6. 최종 빌드용 히어로 이미지 1장을 선택한다.

디버깅 전용으로, 이미지를 생성하지 않고 명령/프롬프트만 확인하려면:
`python3 scripts/run_stock_image_codex.py <slug> --dry-run`.

## 이미지 규칙

- 텍스트, 숫자, 티커 심볼, 로고, 워터마크, UI 스크린샷, 가짜 대시보드 화면을 포함하지 않는다.
- 추상적/에디토리얼 비주얼을 사용한다: 웨이퍼, 메모리 스택, 시장 라인, 매크로/섹터 메타포, 스튜디오 조명.
- 이미지가 리포트의 실제 톤과 일치해야 한다. 리스크 중심 리포트에 일반적인 상승 이미지를 사용하지 않는다.
- 절차적/Pillow/SVG/빈 플레이스홀더 이미지를 Codex `imagegen` 대체물로 만들지 않는다.
- 절차적/Pillow/SVG/플레이스홀더 출력을 `status: complete`로 표시하지 않는다.
- 직접 LLM/OpenAI API 키를 호출하지 않는다. Codex CLI만 사용한다.

## 차단 규칙

Codex CLI 또는 이미지 생성이 불가하면, 래퍼가 프롬프트 3개와 `status: blocked` 매니페스트만 작성한다. 이미지 단계를 완료로 표시하지 않으며 `/stock-build` 통과를 허용하지 않는다.

## 완료 보고

선택된 이미지 경로, 매니페스트 경로, 다음 명령어를 보고한다: `/stock-review <slug>`.

`stock-goal`에서 호출된 경우 이 보고는 내부 체크포인트일 뿐이다. 멈추거나 사용자를 기다리지 않고 즉시 `/stock-review <slug>`로 진행한다.
