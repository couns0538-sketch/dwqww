#!/usr/bin/env bash
# cpu1_w3.sh - Opus 30-h job, window 3: when CPU 1 is free (no python / fastchess pinned to exactly CPU 1 = V16's match
# has ended), on CPU 1 in this order: (1) abba.py A/A with the identical command in both arms (bug-hunt item 8),
# (2) tools/final_checks_o30.sh as a pre-run (the final run follows after the last document changes), (3) 120 more
# games of run 5 (the best sanity result so far) with opening seed 31 into D:\o30\nets\o30_gpu_kb8short_r5\sanity2.
# Exit codes are taken on their own lines (BH-2). Nothing starts after 21:15 except what is running.
set -u
busy() {
    powershell -NoProfile -Command "Get-Process python,fastchess -ErrorAction SilentlyContinue | Where-Object { [int64]\$_.ProcessorAffinity -eq 2 } | Measure-Object | Select-Object -ExpandProperty Count"
}
until [ "$(busy | tr -d '\r')" = "0" ]; do sleep 30; done
echo "$(date '+%F %T') CPU 1 free"
tag=$(date +%H%M)
bash /d/o30/speed/aa/run_aa_identical.sh "aa_identical_$tag" 0x2 > "/d/o30/logs/aa_identical_$tag.out" 2>&1
rc=$?
echo "$(date '+%F %T') A/A identical exit $rc: $(grep -E 'geometric mean' "/d/o30/logs/aa_identical_$tag.out" | cut -c1-120)"
O30_MASK=0x2 bash /d/o30/wt/opus_30h/tools/final_checks_o30.sh > "/d/o30/logs/final_checks_w3pre_$tag.out" 2>&1
rc=$?
echo "$(date '+%F %T') final checks pre-run exit $rc: $(tail -1 "/d/o30/logs/final_checks_w3pre_$tag.out")"
[ "$(date +%H%M)" -ge 2115 ] && { echo "$(date '+%T') 21:15 reached: no extra games"; exit 0; }
bash /d/o30/wt/opus_30h/a/play_w3.sh o30_gpu_kb8short_r5 sanity2 120 1 1 31
rc=$?
echo "$(date '+%F %T') r5 extra games exit $rc"
