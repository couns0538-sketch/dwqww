#!/usr/bin/env bash
# setup_forge_mcp.sh [SERVER_PY] - register the forge-uci MCP server (user scope) for Claude Code, then health-check it.
# Re-runnable: when forge-uci is already registered it only prints the current entry and the health check (it never
# removes or rewrites an existing entry). Default server path = the forge_uci_mcp.py next to this script.
# Needs no install: the server is standard-library Python, run by the read-only nnue venv interpreter with -I -B.
set -u
here=$(cd "$(dirname "$0")" && pwd)
srv=${1:-$(cygpath -w "$here/forge_uci_mcp.py")}
py='C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe'
[ -f "$(cygpath -u "$srv")" ] || { echo "server not found: $srv" >&2; exit 2; }
if claude mcp get forge-uci > /dev/null 2>&1; then
  echo "forge-uci is already registered:"
else
  claude mcp add --scope user forge-uci -- "$py" -I -B "$srv" || exit 1
fi
claude mcp get forge-uci
