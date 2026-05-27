#!/usr/bin/env bash
# PreToolUse(Write/Edit/MultiEdit/Bash): enforce stock report artifact order.
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
# shellcheck source=/dev/null
. "$ROOT/.claude/hooks/lib/guardrail-common.sh" 2>/dev/null || exit 0
TMP_INPUT="$(mktemp)"
cat > "$TMP_INPUT"
trap 'rm -f "$TMP_INPUT"' EXIT

python3 - "$ROOT" "$TMP_INPUT" <<'PY'
import json, re, sys
from pathlib import Path
root = Path(sys.argv[1]).resolve()
raw = Path(sys.argv[2]).read_text(encoding="utf-8", errors="ignore")
try:
    data = json.loads(raw) if raw.strip() else {}
except Exception:
    data = {}

def relpath(value: str) -> str:
    p = Path(value).expanduser()
    if not p.is_absolute():
        p = root / p
    try:
        return p.resolve().relative_to(root).as_posix()
    except Exception:
        return p.resolve().as_posix()

plan_slugs = sorted((p.stem for p in (root / 'plan').glob('*.md')), key=len, reverse=True)
asset_suffixes = [
    '-price-chart-v1.json', '-price-chart-v2.json', '-price-chart-v3.json',
    '-google-news-latest100.json', '-google-news-analysis100.json',
    '-toss-news-latest100.json', '-toss-news-analysis100.json', '-toss-transaction-status.json',
    '-holders-yfinance.json', '-yfinance-raw.json', '-news-latest100.json', '-news-analysis100.json',
    '-hero-v1.prompt.txt', '-hero-v2.prompt.txt', '-hero-v3.prompt.txt',
    '-hero-v1.png', '-hero-v2.png', '-hero-v3.png',
    '-hero-v1.score.json', '-hero-v2.score.json', '-hero-v3.score.json',
    '-image-review.txt', '-image-manifest.json', '-selected-image.json',
]
image_suffix_markers = ('-hero-v', '-image-review.txt', '-image-manifest.json', '-selected-image.json')
research_asset_markers = ('latest100.json', 'analysis100.json', 'transaction-status.json', 'holders-yfinance.json', 'yfinance-raw.json', 'price-chart-v')

def infer_slug_from_asset(name: str) -> str | None:
    for slug in plan_slugs:
        if name == slug or name.startswith(slug + '-'):
            return slug
    for suffix in sorted(asset_suffixes, key=len, reverse=True):
        if name.endswith(suffix):
            return name[:-len(suffix)]
    return None

def review_is_pass(slug: str) -> bool:
    path = root / 'reviews' / f'{slug}.md'
    if not path.is_file():
        return False
    text = path.read_text(encoding='utf-8', errors='ignore')[:2000]
    return bool(re.search(r'^status:\s*pass\s*$', text, re.M)) and 'review_type: separate-session-4way' in text and 'review_execution: separate_subagent_sessions' in text

def selected_image_exists(slug: str) -> bool:
    def has_prohibited_generation_marker(value) -> bool:
        terms = ('pillow', 'procedural', 'programmatic', 'svg', 'placeholder', 'blank')
        if isinstance(value, str):
            lowered = value.lower()
            return any(term in lowered for term in terms)
        if isinstance(value, dict):
            return any(has_prohibited_generation_marker(child) for child in value.values())
        if isinstance(value, list):
            return any(has_prohibited_generation_marker(child) for child in value)
        return False

    manifest = root / 'output' / 'assets' / f'{slug}-image-manifest.json'
    if not manifest.is_file():
        return False
    try:
        manifest_payload = json.loads(manifest.read_text(encoding='utf-8'))
    except Exception:
        return False
    if not isinstance(manifest_payload, dict):
        return False
    if manifest_payload.get('status') != 'complete':
        return False
    if manifest_payload.get('generation_method') != 'codex-cli-imagegen':
        return False
    if not str(manifest_payload.get('generated_with') or '').strip():
        return False
    if has_prohibited_generation_marker(manifest_payload):
        return False
    selected = root / 'output' / 'assets' / f'{slug}-selected-image.json'
    if not selected.is_file():
        return False
    try:
        payload = json.loads(selected.read_text(encoding='utf-8'))
    except Exception:
        return False
    if not isinstance(payload, dict) or has_prohibited_generation_marker(payload):
        return False
    image = (
        payload.get('image_path') or payload.get('selected_image') or payload.get('selectedImage')
        or payload.get('image') or payload.get('path') or payload.get('file')
        or payload.get('selected_path') or payload.get('selected_file')
    )
    if isinstance(image, str):
        p = Path(image)
        if not p.is_absolute():
            candidates = [root / p, root / 'output' / p, root / 'output' / 'assets' / p]
            if image.startswith('assets/'):
                candidates.append(root / 'output' / p)
            return any(candidate.is_file() for candidate in candidates)
        return p.is_file()
    return False

def required_for_path(path: str):
    path = path.replace('\\', '/')
    slug = None
    phase = None
    req = []
    if path.startswith('plan/') and path.endswith('.md'):
        return None, None, []
    if path.startswith('research/') and path.endswith('.md'):
        slug = Path(path).stem; phase = 'research'; req = [('plan', root/'plan'/f'{slug}.md')]
    elif path.startswith('drafts/') and path.endswith('.md'):
        slug = Path(path).stem; phase = 'draft'; req = [('plan', root/'plan'/f'{slug}.md'), ('research', root/'research'/f'{slug}.md')]
    elif path.startswith('reviews/') and path.endswith('.md'):
        slug = Path(path).stem; phase = 'review'; req = [('plan', root/'plan'/f'{slug}.md'), ('research', root/'research'/f'{slug}.md'), ('draft', root/'drafts'/f'{slug}.md')]
    elif path.startswith('output/assets/'):
        name = Path(path).name
        slug = infer_slug_from_asset(name)
        if not slug:
            return None, None, []
        if any(marker in name for marker in image_suffix_markers):
            phase = 'image'
            req = [('plan', root/'plan'/f'{slug}.md'), ('research', root/'research'/f'{slug}.md'), ('draft', root/'drafts'/f'{slug}.md')]
        elif any(marker in name for marker in research_asset_markers):
            phase = 'research-asset'
            req = [('plan', root/'plan'/f'{slug}.md')]
        else:
            phase = 'output-asset'
            req = [('plan', root/'plan'/f'{slug}.md')]
    elif path.startswith('output/') and path.endswith('.html'):
        slug = Path(path).stem; phase = 'build'; req = [('plan', root/'plan'/f'{slug}.md'), ('research', root/'research'/f'{slug}.md'), ('draft', root/'drafts'/f'{slug}.md'), ('review', root/'reviews'/f'{slug}.md')]
    return slug, phase, req

tool = data.get('tool_name') or ''
ti = data.get('tool_input') or {}
paths = []
if tool in {'Write', 'Edit', 'MultiEdit', 'NotebookEdit'}:
    for key in ('file_path', 'path', 'notebook_path'):
        value = ti.get(key)
        if isinstance(value, str) and value.strip():
            paths.append(relpath(value.strip()))
elif tool == 'Bash':
    cmd = ti.get('command') if isinstance(ti.get('command'), str) else ''
    # Guard explicit build command as a last gate before HTML generation.
    m = re.search(r'python3?\s+scripts/build_report\.py\s+([A-Za-z0-9._-]+)', cmd)
    if m:
        paths.append(f'output/{m.group(1)}.html')

problems = []
for path in paths:
    slug, phase, req = required_for_path(path)
    if not slug:
        continue
    missing = [name for name, req_path in req if not req_path.is_file()]
    if missing:
        problems.append(f'{path}: 선행 산출물 누락({", ".join(missing)})')
        continue
    if phase == 'review' and not selected_image_exists(slug):
        problems.append(f'{path}: review 전 selected hero image 누락(output/assets/{slug}-selected-image.json)')
    if phase == 'build':
        if not selected_image_exists(slug):
            problems.append(f'{path}: build 전 selected hero image 누락(output/assets/{slug}-selected-image.json)')
        if not review_is_pass(slug):
            problems.append(f'{path}: build 전 pass 상태의 separate-session-4way review 필요(reviews/{slug}.md)')

if problems:
    reason = '파이프라인 순서(/plan → /research → /draft → /image → /review → /build)를 위반해 차단합니다. ' + '; '.join(problems[:6])
    print(json.dumps({'decision': 'block', 'reason': reason}, ensure_ascii=False))
    sys.exit(2)
PY
exit $?
