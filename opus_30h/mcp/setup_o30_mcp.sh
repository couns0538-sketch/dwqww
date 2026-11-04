#!/usr/bin/env bash
# setup_o30_mcp.sh [SERVER_PY] - register the forge-o30 MCP server (user scope) for Claude Code, then health-check it.
# Re-runnable: when forge-o30 is already registered it only prints the current entry (it never removes or rewrites an
# existing entry). Default server path = the forge_o30_mcp.py next to this script. No install: standard-library Python
# run by the read-only nnue venv interpreter with -I -B. Self-test: python -I -B test_forge_o30_mcp.py
set -u
here=$(cd "$(dirname "$0")" && pwd)
srv=${1:-$(cygpath -w "$here/forge_o30_mcp.py")}
py='C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe'
[ -f "$(cygpath -u "$srv")" ] || { echo "server not found: $srv" >&2; exit 2; }
if claude mcp get forge-o30 > /dev/null 2>&1; then
  echo "forge-o30 is already registered:"
else
  claude mcp add --scope user forge-o30 -- "$py" -I -B "$srv" || exit 1
fi
claude mcp get forge-o30
