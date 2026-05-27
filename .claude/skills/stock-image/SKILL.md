---
name: stock-image
description: Generate and select stock-report-harness hero images. Use for /stock-image <slug> after plan, research, and draft exist; creates three prompt files, three PNG candidates, score JSON files, image-manifest.json, image-review.txt, and selected-image.json.
---

# Stock Image Skill

Create the required hero image asset set for a report slug.

## Preconditions

- `plan/<slug>.md`, `research/<slug>.md`, and `drafts/<slug>.md` must exist.
- Read all three files before writing prompts; title-only prompts are not acceptable.

## Procedure

1. Extract the report message:
   - title/subtitle
   - ticker/company/sector context
   - period
   - core catalysts and risks
   - conclusion tone
2. Write three distinct premium editorial prompts:
   - `output/assets/<slug>-hero-v1.prompt.txt`
   - `output/assets/<slug>-hero-v2.prompt.txt`
   - `output/assets/<slug>-hero-v3.prompt.txt`
3. Generate three PNG candidates using the available `image_gen`/`imagegen` image tool when available:
   - `output/assets/<slug>-hero-v1.png`
   - `output/assets/<slug>-hero-v2.png`
   - `output/assets/<slug>-hero-v3.png`
4. Score each candidate as JSON:
   - `output/assets/<slug>-hero-v1.score.json` etc.
   - Include scores for report fit, company/sector fit, clarity, premium quality, and restraint.
5. Write:
   - `output/assets/<slug>-image-review.txt`
   - `output/assets/<slug>-image-manifest.json`
   - `output/assets/<slug>-selected-image.json`
6. Select exactly one hero image for final build.

## Image Rules

- No visible text, numbers, ticker symbols, logos, watermarks, UI screenshots, or fake dashboard screens.
- Use abstract/editorial visuals: wafers, memory stacks, market lines, macro/sector metaphors, studio lighting.
- The image must match the report’s actual tone; do not use generic bullish imagery for risk-heavy reports.

## Blocking Rule

If image generation is unavailable, still write the three prompt files and manifest with `status: blocked`, but do not mark the image stage complete and do not allow `/stock-build` to pass.

## Completion Report

Report the selected image path, manifest path, and next command: `/stock-review <slug>`.
