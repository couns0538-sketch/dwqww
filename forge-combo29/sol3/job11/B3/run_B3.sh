#!/usr/bin/env bash
set -euo pipefail
work=/workspace/work/sol3-job11
job=forge-combo29/sol3/job11
out="$job/B3"
test "$(rg -c 'B2 .* exit 0$' "$job/stamps.txt")" -eq 4
mkdir "$out"
cp "$work/"{expand_prefilter.py,repetition_oracle.patch.txt,driver_rep.py,run_B3.sh} "$out/"
diff -u --label a/driver_verify.py --label b/driver_rep.py forge-combo29/sol3/job8/step2/driver_verify.py "$out/driver_rep.py" > "$out/driver_rep.patch.txt" || test "$?" -eq 1
cp -a "$work/tree_14" "$work/tree_B3"
patch -d "$work/tree_B3" -p1 -F0 --batch --forward < "$out/repetition_oracle.patch.txt" > "$out/patch_apply.txt" 2>&1
if rg -in 'offset|fuzz|reject|failed' "$out/patch_apply.txt"; then exit 1; fi
diff -qr "$work/tree_oracle" "$work/tree_B3" > "$out/reproducibility.txt"
gcc_line=$(c++ -dM -E -march=x86-64-v4 -x c++ /dev/null | rg '^#define __AVX512F__ 1$')
printf '%s\n%s\n' 'c++ -dM -E -march=x86-64-v4 -x c++ /dev/null' "$gcc_line" > "$out/avx512_macro.txt"
date -u '+%FT%TZ B3 froze differential scan and prefilter oracle before build' >> "$job/stamps.txt"
git add --sparse -- "$out" "$job/stamps.txt"
git -c core.whitespace=-blank-at-eol,-blank-at-eof diff --cached --check
git commit -qm 'sol3 job 11 B3 freeze old and new repetition oracle'
bash /workspace/work/sol3-job3/push-checkpoint.sh
status=0
bash /workspace/work/sol3-job3/build_one.sh "$work/tree_B3" "$work/build_B3" "$out/build.txt" || status=$?
if ((status == 0)); then
  bash "$job/partA/run_warm.sh" "$work/build_B3/forge" "$out/driver_rep.py" "$out" --audit "$out/observed" || status=$?
fi
if ((status == 0)); then
  PYTHONPATH="$work" python3 -B "$job/partA/warm_readback.py" "$job/B1" "$out" equal > "$out/readback.json" 2> "$out/readback.stderr.txt" || status=$?
  PYTHONPATH="$work" python3 -B "$job/partA/sum_counts.py" rep "$out" > "$out/totals.json" 2> "$out/totals.stderr.txt" || status=$?
fi
date -u "+%FT%TZ B3 checked old/new scans and prefilter outcomes on warm workload exit $status" >> "$job/stamps.txt"
git add --sparse -- "$out" "$job/stamps.txt"
git -c core.whitespace=-blank-at-eol,-blank-at-eof diff --cached --check
git commit -qm 'sol3 job 11 B3 checkpoint repetition oracle and path totals'
bash /workspace/work/sol3-job3/push-checkpoint.sh
if test -f "$out/observed.engine_status.json"; then cat "$out/observed.engine_status.json"; fi
if test -f "$out/totals.json"; then cat "$out/totals.json" "$out/totals.stderr.txt"; fi
test "$status" -eq 0
