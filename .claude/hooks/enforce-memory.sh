#!/usr/bin/env bash
# PostToolUse(Write/Edit/MultiEdit): validate memory files after edits.
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
# shellcheck source=/dev/null
. "$ROOT/.claude/hooks/lib/guardrail-common.sh" 2>/dev/null || exit 0
TMP_INPUT="$(mktemp)"
cat > "$TMP_INPUT"
trap 'rm -f "$TMP_INPUT"' EXIT

python3 - "$ROOT" "$TMP_INPUT" <<'PY'
import json, subprocess, sys
from pathlib import Path
root = Path(sys.argv[1]).resolve()
raw = Path(sys.argv[2]).read_text(encoding="utf-8", errors="ignore")
try:
    data = json.loads(raw) if raw.strip() else {}
except Exception:
    sys.exit(0)
tool = data.get('tool_name') or ''
if tool not in {'Write', 'Edit', 'MultiEdit', 'NotebookEdit'}:
    sys.exit(0)
ti = data.get('tool_input') or {}
value = ti.get('file_path') or ti.get('path') or ti.get('notebook_path')
if not isinstance(value, str):
    sys.exit(0)
p = Path(value).expanduser()
if not p.is_absolute():
    p = root / p
try:
    rel = p.resolve().relative_to(root).as_posix()
except Exception:
    sys.exit(0)
if not (rel.startswith('memory/_daily/') or rel.startswith('memory/topics/')):
    sys.exit(0)
validator = root / 'scripts' / 'validate_memory.py'
if not validator.is_file():
    sys.exit(0)
proc = subprocess.run(['python3', str(validator)], cwd=root, text=True, capture_output=True)
if proc.returncode != 0:
    detail = (proc.stdout + proc.stderr).strip()
    reason = 'memory 파일 변경 후 scripts/validate_memory.py 검증 실패. ' + detail[:1200]
    print(json.dumps({'decision': 'block', 'reason': reason}, ensure_ascii=False))
    sys.exit(2)
PY
exit $?
