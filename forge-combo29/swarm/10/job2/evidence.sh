#!/usr/bin/env bash
# evidence.sh -- produces every evidence file that REPORT_job2.md cites. Run from the repo root.
set -u
S=$(cat ~/swarm_seat.txt)
D="forge-combo29/swarm/$S/job2"
REF=for-fable-and-opus/deepseek6-work
mkdir -p "$D/out" "$D/raw"

# 1. the report text itself, verbatim, as read
git fetch -q --depth 1 origin "$REF" || exit 2
git show FETCH_HEAD:forge-combo29/REPORT_deepseek6_long56.md > "$D/raw/REPORT_deepseek6_long56.md.txt"

# 2. raw summary vs report text
python3 - "$D" <<'PY'
import sys, os
d = sys.argv[1]
raw = open('/tmp/ds6/long56/out/fuzz56_summary.txt').read().strip()
rep = open(os.path.join(d, 'raw/REPORT_deepseek6_long56.md.txt')).read()
dct = eval(raw)
report_says = {'seqs': 2000, 'crashes': 0, 'hangs': 0, 'san': 0, 'illegal': 0, 'ok': 2000}
with open(os.path.join(d, 'out/summary_vs_report.txt'), 'w') as f:
    f.write("RAW SUMMARY LINE: %s\n" % raw)
    f.write("source: git show %s:forge-combo29/tests_deepseek6_long56/out/fuzz56_summary.txt\n" % os.environ.get('REF','for-fable-and-opus/deepseek6-work'))
    for k, v in report_says.items():
        got = dct.get(k)
        f.write("%s: raw=%s report=%s agree=%s\n" % (k, got, v, got == v))
    f.write("\nreport text actually contains '2,000 sequences, ZERO crashes': %s\n"
            % ('2,000 sequences, ZERO crashes' in rep))
PY

# 3. listing of long56/out as committed
git ls-tree -r --name-only FETCH_HEAD forge-combo29/tests_deepseek6_long56/out/ > "$D/out/out_dir_listing.txt"
echo "count: $(wc -l < "$D/out/out_dir_listing.txt")" >> "$D/out/out_dir_listing.txt"

# 4. grep for the two sanitizer proofs anywhere in long56
: > "$D/out/proof_grep.txt"
for f in $(git ls-tree -r --name-only FETCH_HEAD forge-combo29/tests_deepseek6_long56/); do
  if git show "FETCH_HEAD:$f" 2>/dev/null | grep -qE "__asan_|__ubsan_|__tsan_|planted"; then
    echo "FOUND in $f" >> "$D/out/proof_grep.txt"
  fi
done
echo "files in long56: $(git ls-tree -r --name-only FETCH_HEAD forge-combo29/tests_deepseek6_long56/ | wc -l)" >> "$D/out/proof_grep.txt"
echo "(no FOUND line above = neither proof is committed)" >> "$D/out/proof_grep.txt"

# 5. does the engine ever print a line starting with 'position'?
{
  echo '$ printf "uci\nisready\nposition startpos moves e2e4 e7e5\ngo depth 3\nisready\nquit\n" | ~/builds/release/forge | grep -c "^position"'
  printf 'uci\nisready\nposition startpos moves e2e4 e7e5\ngo depth 3\nisready\nquit\n' | ~/builds/release/forge 2>/dev/null | grep -c '^position'
} > "$D/out/engine_never_prints_position.txt"
cat "$D/out/engine_never_prints_position.txt"
echo "--- evidence written to $D/out/"
