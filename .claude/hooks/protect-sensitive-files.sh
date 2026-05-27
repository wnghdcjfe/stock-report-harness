#!/usr/bin/env bash
# PreToolUse(Write/Edit/MultiEdit/Bash): prevent modifications to protected paths.
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
# shellcheck source=/dev/null
. "$ROOT/.claude/hooks/lib/guardrail-common.sh" 2>/dev/null || exit 0
TMP_INPUT="$(mktemp)"
cat > "$TMP_INPUT"
trap 'rm -f "$TMP_INPUT"' EXIT

python3 - "$ROOT" "$TMP_INPUT" <<'PY'
import json, os, re, shlex, sys
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

def is_protected(path: str) -> bool:
    path = path.replace('\\', '/')
    return (
        path == '.env' or path.startswith('.env.') or path.startswith('.env/') or
        path == '.git' or path.startswith('.git/') or
        path == '.github/workflows' or path.startswith('.github/workflows/') or
        path in {'docs/finance-style-guide.md', 'docs/output-spec.md'}
    )

tool = data.get('tool_name') or ''
ti = data.get('tool_input') or {}
violations = []

if tool in {'Write', 'Edit', 'MultiEdit', 'NotebookEdit'}:
    for key in ('file_path', 'path', 'notebook_path'):
        value = ti.get(key)
        if isinstance(value, str) and value.strip():
            rp = relpath(value.strip())
            if is_protected(rp):
                violations.append(rp)

elif tool == 'Bash':
    cmd = ti.get('command') if isinstance(ti.get('command'), str) else ''
    # Only block Bash when it both mentions a protected path and appears to mutate files.
    mutating = re.search(r"(^|[;&|]\s*)(cat\s*>|printf\b|echo\b|tee\b|sed\s+-i\b|perl\s+-pi\b|python\b|python3\b|node\b|rm\b|mv\b|cp\b|install\b|touch\b|truncate\b|chmod\b|chown\b|git\s+checkout\b|git\s+restore\b|git\s+reset\b)", cmd)
    redir = re.search(r"(^|[^<>])>{1,2}\s*[^&]", cmd)
    if mutating or redir:
        protected_literals = [
            '.env', '.git', '.github/workflows',
            'docs/finance-style-guide.md', 'docs/output-spec.md',
        ]
        for literal in protected_literals:
            if re.search(r"(?<![\w./-])" + re.escape(literal) + r"(?:/|\b)", cmd):
                violations.append(literal)

if violations:
    uniq = []
    for v in violations:
        if v not in uniq:
            uniq.append(v)
    reason = '보호 경로 수정 시도를 차단합니다: ' + ', '.join(uniq) + '. 보호 대상: .env*, .git/, .github/workflows/, docs/finance-style-guide.md, docs/output-spec.md.'
    print(json.dumps({'decision': 'block', 'reason': reason}, ensure_ascii=False))
    sys.exit(2)
PY
exit $?
