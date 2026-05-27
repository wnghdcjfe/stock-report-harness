# stock-report-harness 코드/문서 계약 리뷰

- 작성일: 2026-05-28 KST
- 요청: 코드 전체를 분석해 `AGENTS.md`, `README.md` 수정 필요 여부를 확인하고 정리
- 범위: 루트 문서, `.claude/commands`, `.claude/skills`, `.claude/agents`, `.claude/hooks`, `scripts/`, `docs/`, `design/`, 기존 plan/research/draft/review/output 산출물
- 직접 수정: 이 리뷰 파일만 작성함. `AGENTS.md`와 `README.md`는 변경하지 않음.

## 결론

| 대상 | 판단 | 요약 |
| --- | --- | --- |
| `AGENTS.md` | 수정 필요 | Draft 필수 섹션명이 실제 validator/README/skill과 불일치하고, review 4번째 리뷰어 지시가 현재 파일 구조와 맞지 않음. |
| `README.md` | 대체로 최신, 일부 보강 권고 | Toss 디자인/이미지 래퍼/검증 명령은 구현과 대체로 일치함. 다만 `assumptions`, selected-image JSON 스키마, 불필요해 보이는 `jq` 의존성은 정리 여지가 있음. |
| 코드/검증기 | 동작하나 계약 공백 있음 | 정적 검사와 memory 검증은 통과. 기존 report artifact 일부는 validator 실패. 특히 image manifest의 `status: complete` 및 procedural/Pillow 금지 규칙은 문서보다 검증이 약함. |

## 확인한 구현 구조

- 파이프라인 파일 계약은 `plan/ → research/ → drafts/ → output/assets image → reviews/ → output HTML` 구조임.
- 핵심 검증/빌드 구현:
  - `scripts/report_contract_lib.py`: 공통 artifact path, frontmatter, required draft section, selected image path resolver.
  - `scripts/validate_report_contract.py`: plan/research/draft/review/image/price chart/HTML 계약 검증.
  - `scripts/build_report.py`: yfinance 가격 차트 생성, draft markdown 렌더링, Toss 스타일 HTML 생성, source marker 제거.
  - `scripts/run_stock_image_codex.py`: Codex CLI nested imagegen 실행 래퍼.
- Claude Code 표면:
  - `.claude/commands/stock-*.md`: slash command → skill 위임.
  - `.claude/skills/stock-*.md`: 단계별 운영 계약.
  - `.claude/hooks/*.sh`: 위험 bash, 민감 파일, 순서, citation, memory, review reminder 가드레일.

## AGENTS.md 수정 권고

### 1. Draft 필수 섹션명을 실제 validator와 맞춰야 함 — 높음

**Evidence**

- `AGENTS.md:30`은 필수 섹션을 `## 영향`, `## 참고`로 적고 있음.
- `README.md:79`, `.claude/skills/stock-draft/SKILL.md:21-27`, `scripts/report_contract_lib.py:32`는 `## 영향과 적용`, `## References`를 필수로 봄.
- `scripts/run_stock_image_codex.py:117`도 `영향과 적용` 섹션을 읽어 이미지 context를 구성함.

이를 필수 섹션을 `## 영향`, `## 참고` 기반으로 각각의 파일들을 수정해야함.  

### 2. Plan frontmatter 필수 목록에 `assumptions`를 추가해야 함 — 중간

**Evidence**

- `AGENTS.md:15`의 Plan 필수 frontmatter에는 `assumptions`가 없음.
- 바로 아래 `AGENTS.md:17`은 기간 기본값을 `assumptions`에 기록하라고 함.
- `.claude/skills/stock-plan/SKILL.md:18-19`와 `docs/templates/planning-brief-template.md:14-15`는 `assumptions`를 required/frontmatter 예시에 포함함.

**권고 수정**

- Plan frontmatter 필수 목록 끝에 `assumptions` 추가.

### 3. Review 4번째 리뷰어 지시를 현재 실행 표면과 맞춰야 함 — 중간

**Evidence**

- `AGENTS.md:46`은 `gpt-review.sh` 또는 `gpt-review.ps1`를 리뷰어로 언급함.
- 저장소에는 해당 파일이 없음. 확인 결과 review 관련 shell 파일은 `.claude/hooks/remind-review.sh`뿐임.
- `.claude/skills/stock-review/SKILL.md:17-21`과 `README.md:92-93`은 4번째 관점을 `codex-independent` 또는 동등 blind-spot review로 설명함.

**권고 수정**
gpt-review.sh과 같은 기능을 하는 
gpt-review.ps1 스크립트 추가
 

### 4. selected-image JSON 최소 스키마를 명시하면 실패를 줄일 수 있음 — 중간

**Evidence**

- `scripts/report_contract_lib.py:197-202`가 인식하는 이미지 경로 키는 `selected_image`, `selectedImage`, `image`, `image_path`, `path`, `file`임.
- 기존 `output/assets/samsung-electronics-recent-1y-2026-05-selected-image.json`은 `selected_path`만 사용해 validator에서 “이미지 경로를 찾을 수 없음”으로 실패함.

**권고 수정**

- Image 계약에 `selected-image.json`은 최소 `slug`, `selected_candidate`, `image_path` 또는 `selected_image`, `reason`, `generated_with`를 포함해야 한다고 명시.
- 경로는 `assets/<file>.png` 또는 `output/assets/<file>.png`처럼 resolver가 찾을 수 있는 값으로 제한.

### 5. 이미지 manifest의 `status: complete`와 procedural/Pillow 금지 규칙을 더 강하게 적어야 함 — 중간

**Evidence**

- `AGENTS.md:39`, `README.md:88`은 placeholder/Pillow/SVG 대체 금지를 말함.
- 그러나 `scripts/validate_report_contract.py:219-224`는 manifest `status`가 없으면 통과시킴.
- 기존 artifact 중 `method: programmatic-pillow` 또는 `generation_method: Pillow (procedural abstract)`가 있어도 일부 검증을 통과함.

**권고 수정**

- 문서에는 “manifest는 반드시 `status: complete`, `generation_method: codex-cli-imagegen`, `generated_with`를 가져야 하며 procedural/Pillow/SVG는 실패”라고 더 구체화.
- 실제 차단은 문서보다 validator 보강이 필요함.

## README.md 수정/보강 권고

### 1. Plan frontmatter 목록에 `assumptions` 추가 — 중간

**Evidence**

- `README.md:64`에는 Plan 필수 frontmatter 목록이 있으나 `assumptions`가 빠져 있음.
- `README.md:65`는 기간이 없으면 `assumptions`에 기록한다고 설명함.
- stock-plan skill과 planning template은 `assumptions`를 포함함.

**권고 수정**

- `README.md`의 Plan 필수 frontmatter 목록에 `assumptions` 추가.

### 2. selected-image JSON 스키마 예시 추가 — 중간

**Evidence**

- README는 `selected-image.json` 존재만 설명함.
- validator는 특정 key만 path로 인식하고, 실제 기존 artifact 중 schema drift로 실패한 사례가 있음.

**권고 수정 예시**

```json
{
  "slug": "<slug>",
  "selected_candidate": 2,
  "image_path": "assets/<slug>-hero-v2.png",
  "reason": "리포트 결론과 가장 잘 맞음",
  "generated_with": "Codex CLI $imagegen / built-in image_gen"
}
```

### 3. `jq` 의존성 표기는 확인 필요 — 낮음

**Evidence**

- `README.md:186`은 의존 도구에 `jq`를 적고 있음.
- 현재 저장소 검색에서 `jq`를 실제 호출하는 스크립트/훅은 발견되지 않음.

**권고**

- 외부 수동 workflow에서만 필요한 도구라면 “선택”으로 표시.
- 현재 코드 기준 필수 의존성이 아니면 제거.

### 4. README는 현재 구현과 대체로 일치함 — 참고

- Toss 디자인 기준 문서(`design/toss_design.md`)와 deterministic renderer 설명은 `scripts/build_report.py` 구현과 일치함.
- 이미지 단계가 `scripts/run_stock_image_codex.py <slug>`를 통해 Codex CLI/imagegen으로 진행된다는 설명도 구현과 일치함.
- build/validate 명령도 package scripts 및 validator와 일치함.

## 코드/계약 공백 및 후속 개선 후보

문서 수정과 별개로, 코드에서 검증 강도를 높이면 반복 실패를 줄일 수 있음.

1. **Image manifest 검증 강화**
   - 현재는 manifest `status`가 없으면 통과 가능.
   - `status == "complete"`를 필수로 하고, `generation_method`/`generated_with`에 procedural/Pillow/SVG가 들어가면 실패하도록 validator 강화 권고.

2. **selected-image resolver 키 확대 또는 스키마 단일화**
   - 현재 resolver는 `selected_path`를 인식하지 않음.
   - 단기적으로는 문서를 `image_path`로 단일화하고, 필요하면 resolver가 `selected_path`, `selected_file`도 진단 메시지로 안내하게 할 수 있음.

3. **Draft frontmatter 검증 강화 여부 결정**
   - `.claude/skills/stock-draft/SKILL.md:18-19`는 `slug`, `title`, `subtitle`, `level`, `duration_minutes`, `created_at`까지 요구함.
   - validator는 현재 plan/research/draft의 `slug`, `ticker`, `period_start`, `period_end` 및 source path 중심으로 검증함.
   - 문서가 “최소 필수”인지 “완전 필수”인지 정하고 validator를 맞추는 것이 좋음.

4. **가격 급등·급락 이벤트 강조 계약 정합성**
   - `docs/output-spec.md:104-109`와 `.claude/skills/stock-draft/SKILL.md:33`은 급등·급락 이벤트 식별을 요구함.
   - `scripts/build_report.py`는 현재 draft prose/chart block을 렌더링하지만 이벤트 annotation/card를 별도 구조로 강제하지는 않음.
   - 이 요구가 필수라면 draft event metadata schema와 validator/build 렌더링을 추가하는 편이 안전함.

## 검증 실행 결과

실행 명령:

```bash
npm run check
python3 scripts/validate_memory.py
for f in reviews/*.md; do slug=$(basename "$f" .md); python3 scripts/validate_report_contract.py "$slug"; done
for f in output/*.html; do slug=$(basename "$f" .html); python3 scripts/validate_report_contract.py "$slug" --require-html --require-price-chart; done
```

요약:

- `npm run check`: 통과
  - `node --check server.js`
  - `python3 -m py_compile scripts/*.py`
- `python3 scripts/validate_memory.py`: 통과
- 기존 review slug 계약 검증:
  - PASS: `samsung-electro-mechanics-recent-1y-2026-05`, `tesla-recent-1y-2026-05`
  - FAIL: `samsung-electronics-recent-1y-2026-05`, `samsung-electronics-recent-30d-2026-05`, `sk-hynix-recent-1y-2026-05`
- 기존 output HTML strict 검증:
  - PASS: `samsung-electro-mechanics-recent-1y-2026-05`, `tesla-recent-1y-2026-05`
  - FAIL: `nvidia-recent-4m-2026-05`, `nvidia-recent-6m-2026-05`, `samsung-electronics-recent-1y-2026-05`, `samsung-electronics-recent-30d-2026-05`, `sk-hynix-recent-1y-2026-05`

주요 실패 유형:

- plan/review 누락: nvidia 계열 output.
- 100건 뉴스 원자료가 있는데 draft에 `## 최신 뉴스 5건 요약` 누락.
- selected-image JSON path key 불일치.
- legacy HTML이 Toss renderer 필수 요소를 만족하지 않음.
- price chart JSON의 `slug`, `rows`, `ariaLabel` 불일치/누락.

## 우선순위 제안

1. `AGENTS.md`의 Draft 섹션명 불일치 수정.
2. `AGENTS.md` review 4번째 리뷰어 표현을 `codex-independent`로 정정하거나 실제 `gpt-review` 스크립트 추가.
3. `AGENTS.md`와 `README.md` Plan frontmatter에 `assumptions` 추가.
4. `README.md`와 `AGENTS.md`에 selected-image JSON 최소 스키마 명시.
5. validator에서 image manifest status/generation method를 강제.
6. 기존 실패 artifact는 새 계약 기준으로 재생성하거나 legacy sample로 분리.
