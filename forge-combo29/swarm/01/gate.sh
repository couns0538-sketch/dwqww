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

# 3c. NO PER-NODE FIGURE NORMALISED BY THE REQUESTED BUDGET (the rule in NODE_COUNT_NORMALISATION_RULE.md).
#     The request is not a quantity, and if the same request divides both sides of a comparison it cancels into a raw
#     time ratio reported under a per-node label. This greps the scripts for the shape of the mistake so the rule
#     cannot quietly come back the next time I write a throughput harness.
baddiv=$(grep -nE "(1e5|100000\.0?|100_000)\s*/\s*(requested|budget|node_budget|request)\b" v3net/*.py *.py 2>/dev/null || true)
if [ -n "$baddiv" ]; then
  echo "FAIL  a per-node figure divides by the REQUESTED budget, not the reported count"
  echo "$baddiv" | head -4 | sed 's/^/      /'
  echo "      see NODE_COUNT_NORMALISATION_RULE.md: divide by the count on the last info line"
  fail=1
else
  echo "ok    no per-node figure divides by a requested budget"
fi

# 3d. PUBLISHED FIGURES MUST DIVIDE (the general rule in NODE_COUNT_NORMALISATION_RULE.md, S-F126).
#     If a line shows two numbers and then a ratio, a reader WILL divide them. This scans the v3 result files for a
#     line of the form "A -> B = Rx" where B/A disagrees with R, i.e. the two numbers are not the ones the ratio came
#     from. That is how my ABBA line read "54.0 -> 46.6 = 0.91x" (46.6/54.0 = 0.863).
divcheck=$(python3 - <<'PYEOF'
import glob, re
bad = []
pat = re.compile(r"([0-9]+\.[0-9]+)\s*(?:ms/100k)?\s*->\s*([0-9]+\.[0-9]+)\s*(?:ms/100k)?\s*=\s*\*?\*?([0-9]+\.[0-9]+)x")
for f in glob.glob("v3net/*.txt"):
    for n, line in enumerate(open(f, encoding="utf-8", errors="replace"), 1):
        for m in pat.finditer(line):
            a, b, r = float(m.group(1)), float(m.group(2)), float(m.group(3))
            if a <= 0:
                continue
            if abs(b / a - r) > 0.01 and abs(a / b - r) > 0.01:
                bad.append("%s:%d: %.1f -> %.1f claims %.2fx, but %.1f/%.1f = %.3f" % (f, n, a, b, r, b, a, b / a))
print("\n".join(bad))
PYEOF
)

if [ -n "$divcheck" ]; then
  echo "FAIL  a published figure does not divide to its stated ratio (S-F126)"
  echo "$divcheck" | head -4 | sed 's/^/      /'
  echo "      see NODE_COUNT_NORMALISATION_RULE.md: label the statistic, or show the numbers it came from"
  fail=1
else
  echo "ok    every 'A -> B = Rx' line divides to its stated ratio"
fi

# 3e. NO STRANDED FORMAT ESCAPES IN THE MARKDOWN. This is the boundary the divides-rule cannot cover: an escape that
#     was meant for a format string but landed in plain text renders as a literal "%" pair, and every arithmetic check
#     passes because the numbers are untouched. Cheap to detect, and it closed a real gap - two finding rows shipped
#     with one and the gate said clean. Quoted examples are still allowed inside a fenced block or a backticked span,
#     so the rule this very check documents can be written down without tripping it.
escapes=$(python3 - <<'PYEOF'
import glob, re
bad = []
for f in sorted(set(glob.glob("*.md") + glob.glob("*/*.md"))):
    fenced = False
    for n, line in enumerate(open(f, encoding="utf-8", errors="replace"), 1):
        s = line.rstrip("\n")
        if s.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        # strip inline code spans, where a quoted escape is deliberate documentation
        prose = re.sub(r"`[^`]*`", "", s)
        if "%%" in prose:
            bad.append("%s:%d: %s" % (f, n, s[:100]))
print("\n".join(bad))
PYEOF
)

if [ -n "$escapes" ]; then
  echo "FAIL  a stranded format escape renders as literal text (%% in prose)"
  echo "$escapes" | head -4 | sed 's/^/      /'
  echo "      fix the text; this is the boundary the divides-rule cannot see (NODE_COUNT_NORMALISATION_RULE.md)"
  fail=1
else
  echo "ok    no stranded format escapes in the markdown"
fi

# 3f. NO EXTREMUM PAIRED WITH A REFERENCE FROM ANOTHER ROW (S-C44 / S-F126 generalised).
#     In a clock trace, every spend must face a clock, and the harness must ASSERT that rather than leave it to a
#     summary sentence. This checks the committed forfeit artifact: every trace entry must carry clock_before, spent
#     and overrun, and no entry may overrun without the run being marked forfeited. It is the machine version of
#     "substitute the pair back into the arithmetic".
tracecheck=$(python3 - <<'PYEOF'
import glob, json
bad = []
for f in sorted(glob.glob("clockfloor/*.json")):
    try:
        d = json.load(open(f))
    except Exception:
        continue
    for r in d.get("rows", []):
        tr = r.get("trace")
        if not tr:
            # A row WITHOUT a trace can still support "did it forfeit" - that is a fact about the run. What it cannot
            # support is any claim pairing a spend with a clock. Only flag it when the row carries an extremum that
            # would need a row to belong to.
            if "max_spend" in r or "lowest" in r:
                bad.append("%s (%s start %s): records an extremum but no per-move trace to tie it to"
                           % (f, r.get("pos") or "row", r.get("start")))
            continue
        for e in tr:
            if not {"clock_before", "spent", "overrun"} <= set(e):
                bad.append("%s: trace entry missing clock_before/spent/overrun" % f)
                break
print("\n".join(bad[:6]))
PYEOF
)

if [ -n "$tracecheck" ]; then
  echo "FAIL  a clock trace cannot tie an extremum to its own row"
  echo "$tracecheck" | head -4 | sed 's/^/      /'
  echo "      see NODE_COUNT_NORMALISATION_RULE.md - the reference must belong to the same row"
  fail=1
else
  echo "ok    every clock trace ties each spend to the clock it faced"
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

  # EVERY injection asserts that it LANDED before its result is trusted (S-F132). printf converts %%, so an
  # injection built with it can silently write clean input and the check then passes correctly - which reads as
  # "the check is broken". Each grep below is the proof that the bad input arrived.
  printf '| S-F1 | 1 | this | breaks the cell | x | y |\n' > "$tmpd/bad.md"
  grep -q '| S-F1 | 1 | this | breaks the cell' "$tmpd/bad.md" || { echo "  INJECTION FAILED: bad row not written"; rc=1; }
  FINDINGS_ARTIFACT="$tmpd/art1.txt" python3 check_findings_table.py "$tmpd/bad.md" > "$tmpd/out" 2>&1
  [ $? -ne 0 ] || { echo "  a bad pipe in a row was ACCEPTED"; rc=1; }

  # a well-formed row must be accepted - so the rejection above is for the right reason, not because the checker
  # rejects everything
  printf '| S-F1 | 1 | well formed | evidence.txt | NEW |\n' > "$tmpd/good.md"
  grep -q 'well formed' "$tmpd/good.md" || { echo "  INJECTION FAILED: good row not written"; rc=1; }
  FINDINGS_ARTIFACT="$tmpd/art2.txt" python3 check_findings_table.py "$tmpd/good.md" > "$tmpd/out2" 2>&1
  [ $? -eq 0 ] || { echo "  a well-formed row was REJECTED"; rc=1; }

  # a STATUS stamp in the future must be rejected
  printf '## 2099-01-01T00:00:00Z — a stamp that cannot be true\nbody\n' > "$tmpd/future.md"
  grep -q '^## 2099-' "$tmpd/future.md" || { echo "  INJECTION FAILED: future stamp not written"; rc=1; }
  python3 check_status_stamps.py "$tmpd/future.md" > "$tmpd/out3" 2>&1
  [ $? -ne 0 ] || { echo "  a future stamp was ACCEPTED"; rc=1; }

  # and a possible stamp must be accepted
  printf '## 2026-01-01T00:00:00Z — a stamp that could be real\nbody\n' > "$tmpd/past.md"
  grep -q '^## 2026-' "$tmpd/past.md" || { echo "  INJECTION FAILED: past stamp not written"; rc=1; }
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
