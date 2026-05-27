#!/usr/bin/env bash
# PostToolUse records touched drafts; Stop blocks if touched drafts lack fresh 4-way review.
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
# shellcheck source=/dev/null
. "$ROOT/.claude/hooks/lib/guardrail-common.sh" 2>/dev/null || exit 0
STATE_DIR="$ROOT/.claude/state"
STATE_FILE="$STATE_DIR/touched-drafts.txt"
mkdir -p "$STATE_DIR"
TMP_INPUT="$(mktemp)"
cat > "$TMP_INPUT"
trap 'rm -f "$TMP_INPUT"' EXIT

python3 - "$ROOT" "$STATE_FILE" "$TMP_INPUT" <<'PY'
import json, os, re, sys
from pathlib import Path
root = Path(sys.argv[1]).resolve()
state_file = Path(sys.argv[2])
raw = Path(sys.argv[3]).read_text(encoding="utf-8", errors="ignore")
try:
    data = json.loads(raw) if raw.strip() else {}
except Exception:
    data = {}

event = data.get('hook_event_name') or data.get('hookEventName') or ''
tool = data.get('tool_name') or ''
ti = data.get('tool_input') or {}

def relpath(value: str) -> str:
    p = Path(value).expanduser()
    if not p.is_absolute():
        p = root / p
    try:
        return p.resolve().relative_to(root).as_posix()
    except Exception:
        return p.resolve().as_posix()

# Record touched draft paths after edits/writes.
if tool in {'Write', 'Edit', 'MultiEdit', 'NotebookEdit'}:
    value = ti.get('file_path') or ti.get('path') or ti.get('notebook_path')
    if isinstance(value, str):
        rp = relpath(value)
        if rp.startswith('drafts/') and rp.endswith('.md'):
            existing = []
            if state_file.is_file():
                existing = [line.strip() for line in state_file.read_text(encoding='utf-8').splitlines() if line.strip()]
            if rp not in existing:
                existing.append(rp)
                state_file.write_text('\n'.join(existing) + '\n', encoding='utf-8')
    sys.exit(0)

# Stop hook: Claude Code often omits tool_name. Treat non-tool invocation as Stop audit.
if tool:
    sys.exit(0)

if not state_file.is_file():
    sys.exit(0)
paths = [line.strip() for line in state_file.read_text(encoding='utf-8').splitlines() if line.strip()]
if not paths:
    sys.exit(0)

problems = []
for rp in paths:
    draft = root / rp
    if not draft.is_file():
        continue
    slug = draft.stem
    review = root / 'reviews' / f'{slug}.md'
    if not review.is_file():
        problems.append(f'{rp}: reviews/{slug}.md 없음')
        continue
    text = review.read_text(encoding='utf-8', errors='ignore')[:2500]
    ok = (
        re.search(r'^status:\s*pass\s*$', text, re.M) and
        'review_type: separate-session-4way' in text and
        'review_execution: separate_subagent_sessions' in text
    )
    if not ok:
        problems.append(f'{rp}: separate-session-4way pass review 아님')
        continue
    if review.stat().st_mtime < draft.stat().st_mtime:
        problems.append(f'{rp}: draft가 review보다 최신임')

if problems:
    reason = 'draft 변경 후 4-way 리뷰 흔적이 부족해 세션 종료를 차단합니다. /stock-review <slug>를 실행하고 pass review를 남기세요. ' + '; '.join(problems[:6])
    print(json.dumps({'decision': 'block', 'reason': reason}, ensure_ascii=False))
    sys.exit(2)

# Reviews are fresh; clear state to avoid repeated reminders.
try:
    state_file.unlink()
except FileNotFoundError:
    pass
PY
exit $?
