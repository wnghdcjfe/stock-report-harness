#!/usr/bin/env bash
# UserPromptSubmit: inject relevant memory topics for the requested domain.
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT" 2>/dev/null || exit 0
if [ ! -f scripts/memory_context.py ]; then
  exit 0
fi
python3 scripts/memory_context.py
