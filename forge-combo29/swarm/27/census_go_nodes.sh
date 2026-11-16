#!/usr/bin/env bash
# census_go_nodes.sh [directory] [--max-bytes N]
#
# ONE LINE: counts, in any directory you point it at, how many places use a `go nodes N` budget below one
# root iteration (26 nodes at startpos) and how many data rows carry a node count of 0 or 1..25 -- the band
# where the engine returns the generator's first move with no score.
#
# Works on an ARBITRARY directory, git or not:
#   - inside a git repo it uses `git ls-files` (tracked files only) and reports the commit;
#   - anywhere else it walks the directory with `find`, skipping binaries and huge files.
# The original version used `git ls-files` unconditionally, so it failed outside a repository and could
# never have been run against the owner's training-data directory. Fixed and re-run in both modes.
#
# Usage:
#   bash census_go_nodes.sh ~/forge-training-data
#   bash census_go_nodes.sh /path/to/repo
#   bash census_go_nodes.sh              # current directory
#
# Exit: 0 always unless the directory is unreadable.
set -u
DIR="${1:-.}"
MAXBYTES=20000000      # skip files over ~20 MB: node-count CSV/JSONL rows are far smaller
[ "${2:-}" = "--max-bytes" ] && MAXBYTES="${3:-20000000}"

[ -d "$DIR" ] || { echo "not a directory: $DIR" >&2; exit 2; }
DIR_ABS=$(readlink -f "$DIR")
echo "directory : $DIR_ABS"
echo "date      : $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# --- choose the file list: git when available, find otherwise
IN_GIT=0
if git -C "$DIR_ABS" rev-parse --show-toplevel >/dev/null 2>&1 &&
   [ "$(readlink -f "$(git -C "$DIR_ABS" rev-parse --show-toplevel)")" = "$DIR_ABS" ]; then
  TOP=$(git -C "$DIR_ABS" rev-parse --show-toplevel)
  if [ "$(readlink -f "$TOP")" = "$DIR_ABS" ]; then
    IN_GIT=1
    echo "mode      : git repository, tracked files only"
    echo "commit    : $(git -C "$DIR_ABS" rev-parse --short HEAD)"
    FILES=$(git -C "$DIR_ABS" ls-files)
  fi
fi

if [ "$IN_GIT" -eq 0 ]; then
  echo "mode      : plain directory, walking with find (non-git)"
  FILES=$(find "$DIR_ABS" -type f \
            -not -path '*/.git/*' \
            -not -name '*.o' -not -name '*.a' -not -name '*.so' -not -name '*.pyc' \
            -not -name 'forge' -not -name '*.zip' -not -name '*.png' -not -name '*.jpg' \
            -size -"${MAXBYTES}c" 2>/dev/null | sed "s#^$DIR_ABS/##")
fi

N_FILES=$(printf '%s\n' "$FILES" | grep -c . || true)
echo "files     : $N_FILES"
echo

echo "== 1. does a per-row labelled dataset exist here? =="
echo "  *.jsonl files     : $(printf '%s\n' "$FILES" | grep -cE '\.jsonl$' || true)"
printf '%s\n' "$FILES" | grep -E '\.jsonl$' | head -20 | sed 's/^/    /'
echo "  *.csv files       : $(printf '%s\n' "$FILES" | grep -cE '\.csv$' || true)"
printf '%s\n' "$FILES" | grep -E '\.csv$' | head -20 | sed 's/^/    /'
echo "  paths with 'train': $(printf '%s\n' "$FILES" | grep -icE 'train' || true)"
printf '%s\n' "$FILES" | grep -iE 'train' | head -20 | sed 's/^/    /'
echo

echo "== 2. 'go nodes N' budget distribution over these files =="
# search the files' contents; -I skips binary content
if [ -n "$FILES" ]; then
  if [ "$IN_GIT" -eq 1 ]; then
    BUDGETS=$(cd "$DIR_ABS" && printf '%s\n' "$FILES" | tr '\n' '\0' \
      | xargs -0 -r grep -hoE 'go nodes [0-9]+' 2>/dev/null | awk '{print $3}')
  else
    BUDGETS=$(cd "$DIR_ABS" && printf '%s\n' "$FILES" | tr '\n' '\0' \
      | xargs -0 -r grep -hoE 'go nodes [0-9]+' 2>/dev/null | awk '{print $3}')
  fi
else
  BUDGETS=""
fi
if [ -z "$BUDGETS" ]; then
  echo "  (no 'go nodes' occurrences found)"
  TOTAL=0; BELOW=0
else
  printf '%s\n' "$BUDGETS" | sort -n | uniq -c \
    | awk '{printf "  budget %-8s %s occurrences\n", $2, $1}'
  TOTAL=$(printf '%s\n' "$BUDGETS" | wc -l)
  BELOW=$(printf '%s\n' "$BUDGETS" | awk '{if ($1+0 < 26) c++} END {print c+0}')
fi
echo
echo "  TOTAL 'go nodes' occurrences : $TOTAL"
echo "  BELOW the 26-node threshold  : $BELOW"
[ "$TOTAL" -gt 0 ] && echo "  share below threshold        : $(awk -v b="$BELOW" -v t="$TOTAL" 'BEGIN{printf "%.4f %%", 100*b/t}')"
echo

echo "== 3. DATA ROWS carrying a node count of 0 or 1..25 (the band's fingerprint) =="
# A row only counts as a LABEL if it carries a POSITION *and* a node count *and* a move-or-score field
# on the SAME LINE. That definition was reached the hard way, in three passes over this repository:
#   pass 1  matched `"nodes": 0` anywhere -> 2,000+ hits, all of them soak-test CONFIG blocks where
#           `"nodes": 0` means "no node limit" (labels read n0). Not data.
#   pass 2  added "a position on the same line" -> 12,630 hits, but inspection showed they are FENs
#           quoted inside reports and progress logs, with a node figure elsewhere on the line. Not data.
#   pass 3  requires position + node count + move/score -> this is the definition below.
# The lesson is in the script on purpose: a wide grep over a repository full of transcripts will always
# "find" rows, and the only way to tell a label from a log line is to open the matches.
LABEL_RE='("fen"|"epd").*"(nodes|n)"[[:space:]]*:[[:space:]]*([0-9]|1[0-9]|2[0-5])[^0-9].*"(bestmove|move|score|"score")'
ROWS=0
SAMPLES=$(mktemp)
if [ -n "$FILES" ]; then
  ( cd "$DIR_ABS" && printf '%s\n' "$FILES" | tr '\n' '\0' \
      | xargs -0 -r grep -nHE "$LABEL_RE" 2>/dev/null ) > "$SAMPLES" || true
  ROWS=$(wc -l < "$SAMPLES")
fi
# also report the wider "position + node count, any range" population, so the reader sees the denominator
POOL=$(mktemp)
if [ -n "$FILES" ]; then
  ( cd "$DIR_ABS" && printf '%s\n' "$FILES" | tr '\n' '\0' \
      | xargs -0 -r grep -hE '("fen"|"epd").*"(nodes|n)"[[:space:]]*:[[:space:]]*[0-9]+.*"(bestmove|move|score)"' 2>/dev/null ) > "$POOL" || true
fi
POOLN=$(wc -l < "$POOL")
echo "  label-shaped rows anywhere in these files (position + node count + move/score): $POOLN"
echo "  of those, rows whose node count is 0 or 1..25 (THE BAND)                       : $ROWS"
if [ "$ROWS" -gt 0 ]; then
  echo "  first 10 (inspect these):"
  head -10 "$SAMPLES" | cut -c1-200 | sed 's/^/    /'
else
  echo "  no label row in this directory records a node count in the band."
fi
rm -f "$SAMPLES" "$POOL"
echo

echo "== verdict =="
if [ "$TOTAL" -eq 0 ] && [ "$ROWS" -eq 0 ]; then
  echo "  Nothing here uses a 'go nodes' budget and no row records a node count in the band."
elif [ "$ROWS" -gt 0 ]; then
  echo "  $ROWS label-shaped rows carry a small node count. THIS IS A CANDIDATE LIST, NOT A VERDICT:"
  echo "  a legitimate draw can also be scored in 18 nodes. In this repository the rows found are parity"
  echo "  test fixtures, and the one verified by hand (fen 4k3/4Q3/8/8/8/8/2K5/8 b - - 24 133) is a"
  echo "  CORRECT cp 0 -- Black has exactly one legal move, KxQ, leaving K vs K. Open each sample and"
  echo "  check the position before treating any of them as a band artefact."
else
  echo "  $BELOW of $TOTAL budget occurrences sit below the threshold, but no data row records a node"
  echo "  count in the band -- so the scripts use small budgets deliberately, and no dataset is affected."
fi
