#!/usr/bin/env bash
# job2 part A: static audit of deepseek6 long56 committed files
# Every command is printed, every output is kept. Run from a clean dir.
set -u
W=${1:?workdir}   # ~/work/ds6
F=forge-combo29/tests_deepseek6_long56
cd "$W/$F" || exit 1
echo "## date:"; date -u
echo
echo "## 1. the report's headline claim vs its own summary file"
echo '$ grep -n "2,000\|ok 2000\|ZERO" REPORT_deepseek6_long56.md'
grep -n "2,000\|ok 2000\|ZERO" REPORT_deepseek6_long56.md 2>/dev/null || \
  { echo "(report not in this extraction; read from git below)"; }
echo
echo '$ cat out/fuzz56_summary.txt'
cat out/fuzz56_summary.txt
echo
echo '$ ls -la out/'
ls -la out/
echo
echo "## 2. per-sequence records (the report says they are in out/)"
echo '$ find . -name "*seq*" -o -name "*.jsonl" -o -name "records*" | sort'
find . -name "*seq*" -o -name "*.jsonl" -o -name "records*" | sort
echo
echo "## 3. sanitizer proof files (.meta with nm __asan_, planted-fault run)"
echo '$ grep -rl "__asan_\|AddressSanitizer" . | sort'
grep -rl "__asan_\|AddressSanitizer" . 2>/dev/null | sort || true
echo '$ find . -name "*.meta" | sort'
find . -name "*.meta" | sort
echo
echo "## 4. is the sequence file committed / regenerable from the branch alone?"
echo '$ ls /tmp/uci56_seqs.txt  (before my own regeneration)'
ls -la /tmp/uci56_seqs.txt 2>&1
echo '$ grep -n "/tmp/" make_uci56.py fuzzuci56.py'
grep -n "/tmp/" make_uci56.py fuzzuci56.py
echo
echo "## 5. the checker: which lines of fuzzuci56.py actually do the legality check"
echo '$ grep -n "chess.Board\|lastpos\|best\b\|pos_line\|ValueError" fuzzuci56.py'
grep -n "chess.Board\|lastpos\|best\b\|pos_line\|ValueError" fuzzuci56.py
echo
echo "## 6. stamps and claim"
echo '$ cat CLAIM.txt; echo ---; cat stamps.txt; echo ---; cat PREDICTION.md'
cat CLAIM.txt; echo ---; cat stamps.txt; echo ---; cat PREDICTION.md
echo
echo "## 7. last command (report section 12) checked against reality"
echo '$ git log --oneline -1 -- '"$F"
echo "(see git section of the evidence file)"
date -u
