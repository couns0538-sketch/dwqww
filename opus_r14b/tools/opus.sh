#!/usr/bin/env bash
# opus.sh COMMAND [args] - Opus R14-B: one entry point for the tools in this folder (skill forge-opus-tools).
#   status [--ci]                       what runs, worktrees, CPUs 2-3, RAM / disks, npt keeper (read-only, ~10 s)
#   lint [PATH...]                      doc_lint over PATH (default: the R14-B branch folders and the skills)
#   abba --out NEW --a CMD --b CMD ...  palindromic A/B timing of two commands (all abba.py options)
#   engine REF NEW_DIR [--quick]        fresh export + lock-recipe build + bench / perft pins of an engine ref
#   bisect GOOD BAD NEW_DIR [--depth D] first commit that changed bench nodes (builds each candidate; --test CMD)
#   time [--since T] [BRANCH...]        commits, spans, pauses per branch (default: last 24 h, the R14-B branches)
#   load [MASK] [SECONDS]               who uses the CPUs of MASK (default 0xC = CPUs 2-3, 5 s)
#   gpu [--hours H | --from T --to T]   GPU utilisation from the keeper's HWiNFO log (read-only; --by-hour)
#   test NEW_DIR                        the tools' own tests (26 checks)
set -u
here=$(cd "$(dirname "$0")" && pwd)
PY=${PY:-/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe}
repo=$(git -C "$here" rev-parse --show-toplevel 2>/dev/null || echo /d/grok-pc-data/dwqww)
wt=/d/grok-pc-data/dwqww/.claude/worktrees
cmd=${1:-help}; [ $# -gt 0 ] && shift
case "$cmd" in
  status) exec bash "$here/opus_status.sh" "$@" ;;
  lint)
    if [ $# -eq 0 ]; then
      set --
      for d in "$wt"/o14b-*/opus_r14b "$wt"/o14b-*/skills /d/grok-pc-data/dwqww/.claude/skills; do [ -d "$d" ] && set -- "$@" "$d"; done
    fi
    exec "$PY" -I -B "$here/doc_lint.py" "$@" ;;
  abba) exec "$PY" -I -B "$here/abba.py" "$@" ;;
  engine) exec bash "$here/engine_fresh_check.sh" "$@" ;;
  bisect) exec bash "$here/engine_bisect.sh" "$@" ;;
  time)  # options (--since / --until / --gap VALUE) first, then branches
    opts=()
    while [ $# -gt 1 ] && [[ "$1" == --* ]]; do opts+=("$1" "$2"); shift 2; done
    [[ " ${opts[*]-} " == *" --since "* ]] || opts+=(--since "24 hours ago")
    [ $# -eq 0 ] && set -- origin/opus-r14b-status origin/opus-r14b-fast-loader origin/opus-r14b-relabel
    exec "$PY" -I -B "$here/commit_span.py" --repo "$repo" ${opts[@]+"${opts[@]}"} "$@" ;;
  load) exec powershell -NoProfile -File "$(cygpath -w "$here/cpu_users.ps1")" -Mask "${1:-0xC}" -Seconds "${2:-5}" ;;
  gpu) exec "$PY" -I -B "$here/gpu_util_stats.py" "$@" ;;
  test) exec bash "$here/test_tools.sh" "$@" ;;
  help|-h|--help) sed -n 2,11p "$0" | sed 's/^# \{0,1\}//' ;;
  *) echo "opus.sh: unknown command '$cmd'"; sed -n 2,11p "$0" | sed 's/^# \{0,1\}//'; exit 2 ;;
esac
