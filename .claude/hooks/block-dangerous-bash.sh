#!/usr/bin/env bash
# PreToolUse(Bash): block irreversible/destructive shell commands.
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
# shellcheck source=/dev/null
. "$ROOT/.claude/hooks/lib/guardrail-common.sh" 2>/dev/null || exit 0
INPUT="$(cat)"
CMD="$(printf '%s' "$INPUT" | extract_bash_command)"
[ -z "$CMD" ] && exit 0

python3 - "$CMD" <<'PY'
import json, re, sys
cmd = sys.argv[1]
checks = [
    (
        "rm -rf root",
        re.compile(r"(?:^|[;&|()\s])rm\s+(?:-[^\s]*[rR][^\s]*[fF][^\s]*|-[^\s]*[fF][^\s]*[rR][^\s]*)(?:\s+--[^\s]+)*\s+(?:/|/\*|['\"]?/['\"]?)(?:\s|$)"),
        "루트 디렉터리를 대상으로 한 rm -rf 계열 명령은 되돌릴 수 없어 차단합니다.",
    ),
    (
        "no-preserve-root",
        re.compile(r"\brm\b[^\n]*--no-preserve-root"),
        "rm --no-preserve-root 옵션은 시스템 파괴 위험이 있어 차단합니다.",
    ),
    (
        "sudo",
        re.compile(r"(?:^|[;&|()\s])sudo(?:\s|$)"),
        "sudo 실행은 권한 상승을 동반하므로 이 프로젝트 훅에서 차단합니다.",
    ),
    (
        "remote script pipe",
        re.compile(r"\b(?:curl|wget)\b[^\n|;]*(?:https?://|www\.)[^\n|;]*\|\s*(?:env\s+)?(?:sh|bash|zsh|ksh|fish|python(?:3)?|ruby|perl|node)\b", re.I),
        "원격 스크립트를 다운로드해 셸/인터프리터로 바로 파이프 실행하는 패턴은 차단합니다. 파일로 저장해 검토한 뒤 실행하세요.",
    ),
    (
        "force push flag",
        re.compile(r"\bgit\s+push\b[^\n]*(?:--force(?:-with-lease|-if-includes)?\b|-f\b)"),
        "강제 push(git push --force/-f/--force-with-lease)는 원격 히스토리를 덮어쓸 수 있어 차단합니다.",
    ),
    (
        "force push refspec",
        re.compile(r"\bgit\s+push\b[^\n]*\s\+[^\s]+"),
        "강제 refspec(git push +branch)은 원격 히스토리를 덮어쓸 수 있어 차단합니다.",
    ),
]
for _name, pattern, reason in checks:
    if pattern.search(cmd):
        print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
        sys.exit(2)
sys.exit(0)
PY
exit $?
