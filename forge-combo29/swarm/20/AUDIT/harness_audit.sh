#!/usr/bin/env bash
# harness_audit.sh — seat 20: audit EVERY harness I used for the pipelined-quit trap that seat 19 reported (19-F12).
#
# The trap: writing `go ...` and `quit` (or closing stdin) before the engine has printed `bestmove` makes this
# build answer a FABRICATED bestmove with 0 nodes. Any result recorded from such a harness is invalid.
#
# Classification per script:
#   WAITS-FOR-BESTMOVE  — writes go, then reads stdout until a bestmove line, THEN quits  -> valid
#   PIPELINED-QUIT      — go and quit are both written/closing before bestmove            -> INVALID for searches
#   NO-SEARCH           — never sends `go` (eval / uci / argv tests)                      -> unaffected
set -u
D="$(cd "$(dirname "$0")/.." && pwd)"        # forge-combo29/swarm/20
OUT="$D/AUDIT"
mkdir -p "$OUT"
date -u +"audit start %Y-%m-%dT%H:%M:%SZ" > "$OUT/stamps.txt"
{
echo "== every script of mine that drives the engine, and how it handles quit"
echo
for f in $(find "$D" -name '*.py' -o -name '*.sh' | grep -v '/out' | grep -v 'AUDIT' | sort); do
  rel=${f#$D/}
  has_go=$(grep -cE '"go |go \$|echo "go |echo \$go|f"go |go depth|go nodes|go movetime|go infinite' "$f" 2>/dev/null || true)
  waits=$(grep -cE 'wait_best|waitspin|startswith\("bestmove"\)|startswith\(.bestmove.\)|bestmove" for x' "$f" 2>/dev/null || true)
  # a pipelined quit: a heredoc/printf/echo-block containing both a go line and a quit line, or quit written
  # immediately after go with no read in between
  piped=$(grep -cE 'printf .*go .*\\n.*quit|echo quit' "$f" 2>/dev/null || true)
  echo "--- $rel"
  echo "    mentions go: $has_go   waits-for-bestmove constructs: $waits   quit-ish: $piped"
  if [ "$has_go" -eq 0 ]; then
    echo "    CLASS: NO-SEARCH (unaffected by 19-F12)"
  elif [ "$waits" -gt 0 ]; then
    echo "    CLASS: WAITS-FOR-BESTMOVE (needs manual confirmation that the wait precedes the quit)"
  else
    echo "    CLASS: *** PIPELINED-QUIT RISK — INSPECT ***"
  fi
done
echo
echo "== the shell-level pipelines inside my scripts ('|' into the engine) — each needs a look:"
grep -rn --include='*.sh' --include='*.py' -E '\| *(timeout [0-9]+ )?("\$|\./|\$EXE|/agent/repos)' "$D" 2>/dev/null | grep -v AUDIT | head -40
} | tee "$OUT/harness_audit.txt"
date -u +"audit done %Y-%m-%dT%H:%M:%SZ" >> "$OUT/stamps.txt"
