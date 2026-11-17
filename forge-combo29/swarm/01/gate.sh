#!/usr/bin/env bash
# swarm seat 01: ONE command that runs every gate before a push, so none of them depends on my memory.
#
# The recurring failure in this session was not "not knowing a rule" but "not applying a known rule to the next
# artefact". A prose rule binds the author's memory; memory fails at the moment of creation. So the rules that
# actually hold are the ones that run in a script — this one.
#
# Usage: ./gate.sh [--with-honesty]
#   --with-honesty also runs the four pin checks against the PC build (slow: builds nothing, but runs perft/bench).
set -uo pipefail
cd "$(dirname "$0")" || exit 1
fail=0

run() {
  local name="$1"; shift
  local out
  out="$("$@" 2>&1)"
  local rc=$?
  if [ $rc -ne 0 ]; then
    echo "FAIL  $name"
    echo "$out" | tail -12 | sed 's/^/      /'
    fail=1
  else
    echo "ok    $name"
  fi
  return 0
}

echo "=== gates, in the order a reader would check them ==="

# 1. the findings table's shape and id uniqueness (does NOT check truth, columns, or staleness)
run "findings table shape" python3 check_findings_table.py FINDINGS.md

# 2. every STATUS stamp is a possible clock reading, and blocks are in order
#    (I fabricated two future stamps this session; this is the check that would have caught both)
run "STATUS stamps vs clock" python3 check_status_stamps.py STATUS.md

# 3. page shape across the PROSE pages in this folder (headings, empty sections, stranded material)
#    STATUS.md is excluded on purpose and the reason is recorded: it is an append-only chronological log, so a
#    block legitimately follows what a prose page would call its closing material. Applying the page rule to a log
#    produced a false failure on 2026-11-17, and the honest response is to scope the check, not to rewrite the log.
pages=$(find . -name '*.md' -not -path './.git/*' -not -name 'STATUS.md' | sort)
if [ -n "$pages" ]; then
  for p in $pages; do
    run "page shape: $p" python3 check_page_shape.py "$p"
  done
fi
#    STATUS.md still gets the stamp check (above) and the table check applies only to FINDINGS.md.
run "STATUS.md has no duplicate ## headings" python3 -c "
import sys,collections
h=[l.strip() for l in open('STATUS.md') if l.startswith('## ')]
d=[k for k,v in collections.Counter(h).items() if v>1]
print('duplicate ## headings:', d if d else 'none')
sys.exit(1 if d else 0)"

# 4. the four honesty pins, if asked for and if a PC build exists
if [ "${1:-}" = "--with-honesty" ]; then
  if [ -x "$HOME/builds/pc/forge" ]; then
    run "honesty pins (PC build)" python3 honesty/honesty.py "$HOME/builds/pc/forge" /tmp/gate_honesty
  else
    echo "skip  honesty pins (no \$HOME/builds/pc/forge)"
  fi
fi

# 5. no non-text files, no net files, and no pycache TRACKED BY GIT in the folder.
#    Checking the working tree was too strict: __pycache__ appears whenever a script runs and is gitignored, so a
#    clean checkout would fail the gate for a file that never reaches the branch. What matters is what git would
#    carry, so ask git.
tracked_junk=$(git ls-files . | grep -E '(__pycache__|\.pyc$|\.fnn3$|\.o$|\.patch$)' || true)
if [ -n "$tracked_junk" ]; then
  echo "FAIL  tracked binaries, nets or pycache in the folder"
  echo "$tracked_junk" | sed 's/^/      /'
  fail=1
else
  echo "ok    nothing binary, no net and no pycache is tracked in the folder"
fi

echo
if [ $fail -ne 0 ]; then
  echo "GATE: FAILED - do not push until the lines above are understood."
  echo "LIMIT: these check shape and possibility, not whether a claim is TRUE."
  exit 1
fi
echo "GATE: passed. These check shape and possibility, not whether a claim is true."
