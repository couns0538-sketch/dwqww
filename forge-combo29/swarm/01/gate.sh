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

# 3b. SIGNS THAT A FILE WAS DAMAGED BY SHELL EXPANSION (Trap 9). Three separate times now a heredoc has eaten text:
#     a backticked command inside a double-quoted heredoc gets EXECUTED and replaced by nothing, and its error message
#     is the only trace. These markers are that trace. They are cheap to check and impossible to notice by reading,
#     because the sentence around them still parses.
# A marker inside a fenced code block is QUOTED EVIDENCE (Trap 9 shows the damage verbatim), not damage, so the
# check skips fenced regions. My first version flagged MEASUREMENT_TRAPS.md:172-173, which are deliberately quoted
# error lines - a check that cannot tell an example from the real thing is the same trap one level up.
damaged=$(python3 - <<'PYEOF'
import glob, re, sys
pat = re.compile(r"return: can only .return. from a function|^go nodes: unknown command|command not found$|unexpected EOF while looking for")
hits = []
for f in sorted(set(glob.glob("*.md") + glob.glob("v3net/*.md") + glob.glob("*/*.md"))):
    fenced = False
    for n, line in enumerate(open(f, encoding="utf-8", errors="replace"), 1):
        s = line.rstrip("\n")
        if s.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced and pat.search(s):
            hits.append("%s:%d:%s" % (f, n, s[:120]))
print("\n".join(hits))
PYEOF
)
if [ -n "$damaged" ]; then
  echo "FAIL  shell-expansion damage markers found (Trap 9)"
  echo "$damaged" | head -6 | sed 's/^/      /'
  fail=1
else
  echo "ok    no shell-expansion damage markers in the markdown"
fi

# 4. the four honesty pins, if asked for and if a PC build exists
if [ "${1:-}" = "--with-honesty" ]; then
  if [ -x "$HOME/builds/pc/forge" ]; then
    run "honesty pins (PC build)" python3 honesty/honesty.py "$HOME/builds/pc/forge" /tmp/gate_honesty
  else
    echo "skip  honesty pins (no \$HOME/builds/pc/forge)"
  fi
fi

# 6. SELF-TEST: the checks must FAIL on bad input. A check that has only ever passed is indistinguishable from a
#    check that does nothing - which is exactly how long the findings-table check was decorative (S-F122: it always
#    exited 0, so this gate printed "ok" while the checker reported a problem). So the gate proves its own teeth on
#    every run, against synthetic input it creates and deletes, never against the real files.
selftest() {
  # NOTE ON A BUG I PUT HERE FIRST: I used `trap 'rm -rf "$tmpd"' RETURN` for cleanup. A RETURN trap's own last
  # command sets the function's exit status, and `rm -rf` succeeds - so selftest() ALWAYS returned 0 and passed a
  # deliberately broken checker. The self-test was decorative in exactly the way the check it was written to
  # protect (S-F122). Cleanup is therefore explicit, and each assertion sets rc itself.
  local rc=0 tmpd
  tmpd="$(mktemp -d)"

  # a findings table with a literal pipe inside a cell must be rejected
  printf '| S-F1 | 1 | this | breaks the cell | x | y |\n' > "$tmpd/bad.md"
  FINDINGS_ARTIFACT="$tmpd/art1.txt" python3 check_findings_table.py "$tmpd/bad.md" > "$tmpd/out" 2>&1
  [ $? -ne 0 ] || { echo "  a bad pipe in a row was ACCEPTED"; rc=1; }

  # a well-formed row must be accepted - so the rejection above is for the right reason, not because the checker
  # rejects everything
  printf '| S-F1 | 1 | well formed | evidence.txt | NEW |\n' > "$tmpd/good.md"
  FINDINGS_ARTIFACT="$tmpd/art2.txt" python3 check_findings_table.py "$tmpd/good.md" > "$tmpd/out2" 2>&1
  [ $? -eq 0 ] || { echo "  a well-formed row was REJECTED"; rc=1; }

  # a STATUS stamp in the future must be rejected
  printf '## 2099-01-01T00:00:00Z — a stamp that cannot be true\nbody\n' > "$tmpd/future.md"
  python3 check_status_stamps.py "$tmpd/future.md" > "$tmpd/out3" 2>&1
  [ $? -ne 0 ] || { echo "  a future stamp was ACCEPTED"; rc=1; }

  # and a possible stamp must be accepted
  printf '## 2026-01-01T00:00:00Z — a stamp that could be real\nbody\n' > "$tmpd/past.md"
  python3 check_status_stamps.py "$tmpd/past.md" > "$tmpd/out4" 2>&1
  [ $? -eq 0 ] || { echo "  a valid past stamp was REJECTED"; rc=1; }

  rm -rf "$tmpd"
  return $rc
}
if selftest; then
  echo "ok    self-test: table and stamp checks fail on bad input and pass on good input"
else
  echo "FAIL  self-test: a checker did not behave as claimed, so its 'ok' above means nothing"
  fail=1
fi

# 7. no non-text files, no net files, and no pycache TRACKED BY GIT in the folder.
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
