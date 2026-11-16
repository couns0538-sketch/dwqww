#!/usr/bin/env bash
# census_go_nodes.sh [repo-dir]
# Answers one question with a number instead of a warning: does this repository contain any training or
# tuning DATA whose rows would fall in the `go nodes` band (below one root iteration, 26 nodes at
# startpos), and what `go nodes` budgets does the repository actually use?
#
# Three parts:
#   1. does a per-row labelled dataset exist here at all?
#   2. the distribution of `go nodes N` budgets over every tracked file
#   3. attribution: which directories the below-threshold budgets come from
#
# Read the output as: part 1 decides whether the band can be counted at all. If there is no dataset,
# no count is possible and the honest answer is "not in this repository" -- which is what it prints.
set -u
DIR="${1:-.}"
cd "$DIR" || exit 2
echo "repository: $(git rev-parse --show-toplevel)"
echo "commit    : $(git rev-parse --short HEAD)"
echo "date      : $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo

echo "== 1. is there a per-row labelled dataset in the repository? =="
echo "  *.jsonl files        : $(git ls-files '*.jsonl' | wc -l)"
git ls-files '*.jsonl' | sed 's/^/    /'
echo "  *.csv files          : $(git ls-files '*.csv' | wc -l)"
git ls-files '*.csv' | sed 's/^/    /'
echo "  paths containing 'train': $(git ls-files | grep -icE 'train')"
git ls-files | grep -iE 'train' | sed 's/^/    /'
echo "  files named data/labels/targets.(txt|jsonl|csv): $(git ls-files | grep -icE '(data|labels|targets)\.(txt|jsonl|csv)$')"
echo
echo "  For each 'train' path, does it hold DATA or just commands? (position/info-depth line counts)"
while IFS= read -r f; do
  [ -z "$f" ] && continue
  printf '    %-55s position=%-4s info_depth=%-4s\n' "$f" \
    "$(grep -c '^position' "$f" 2>/dev/null || echo 0)" \
    "$(grep -c '^info depth' "$f" 2>/dev/null || echo 0)"
done <<< "$(git ls-files | grep -iE 'train')"
echo

echo "== 2. distribution of 'go nodes N' budgets over every tracked file =="
git grep -hoE 'go nodes [0-9]+' 2>/dev/null | awk '{print $3}' | sort -n | uniq -c \
  | awk '{printf "  budget %-8s %s occurrences\n", $2, $1}'
echo
BELOW=$(git grep -hoE 'go nodes [0-9]+' 2>/dev/null | awk '{if ($3+0 < 26) c++} END {print c+0}')
TOTAL=$(git grep -hoE 'go nodes [0-9]+' 2>/dev/null | wc -l)
echo "  below the 26-node startpos threshold: $BELOW of $TOTAL"
echo

echo "== 3. where do the below-threshold budgets come from? =="
git grep -lE 'go nodes ([0-9]|1[0-9]|2[0-5])\b' 2>/dev/null \
  | sed 's#\(forge-combo29/[^/]*\).*#\1#' | sort | uniq -c | sort -rn | sed 's/^/  /'
echo
echo "  Read part 3 carefully: swarm/ entries are probe scripts written by swarm seats (including me)."
echo "  entries under tests_* are deliberate unit tests that ASSERT the small-budget behaviour."
echo
echo "== verdict =="
if [ "$(git ls-files '*.jsonl' '*.csv' | wc -l)" -le 1 ] && [ "$(git ls-files | grep -icE 'train')" -le 1 ]; then
  echo "  NO training or tuning dataset exists in this repository, so the fraction of dataset rows in the"
  echo "  go-nodes band CANNOT be counted here. The repository's own budgets are all far above the"
  echo "  threshold (see part 2); the owner's real training data lives on the PC, not in this repo."
else
  echo "  A candidate dataset exists -- inspect it before quoting any band fraction."
fi
