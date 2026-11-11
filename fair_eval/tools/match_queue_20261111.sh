#!/usr/bin/env bash
# match_queue_20261111.sh - JOB D follow-up (own code): the three matches of 2026-11-11 in one detached queue.
# Waits for the last timing queue to finish (timing needs a quiet machine), then runs, one after another:
#   1. halfka_1024  - the stand-alone 1024 net on the correctly profiled combo29 build, 300 games
#   2. v2kb8_U8_fast - soup U8 on the correctly profiled combo29 v2 build, 2000 games
#   3. int8          - INT8/VNNI with its own profile, 1100 games
# each against the original lock exe (tools/run_match.sh). Not the crew gate; no lock claim.
set -u
R=/d/forge_jobs_20261111/fairD
B=$R/_work/builds; N=D:/forge_jobs_20261111/fairD/_work/nets; M=$R/_work/match
mkdir -p "$M"
echo "queue pid $$ started $(date '+%F %T')" >> "$M/queue.log"
until grep -q "^done" "$R/_work/abba_final/final.log"; do sleep 5; done
echo "timing queue finished, matches start $(date '+%F %T')" >> "$M/queue.log"
run() { echo "== $1 start $(date '+%F %T')" >> "$M/queue.log"; bash "$R/fair_eval/tools/run_match.sh" "$@" >> "$M/queue.log" 2>&1; echo "== $1 end $(date '+%F %T') exit $?" >> "$M/queue.log"; }
run halfka_1024 "$M" 300 "$B/halfka_1024_8e8613998566/forge_fair_halfka_1024.exe" "option.EvalFileHalfKA=$N/npt_k32h3_l1024_bs16k_e8x152m5_g072_lam10_w4_s6_final.nnue"
run v2kb8_U8_fast "$M" 2000 "$B/v2kb8_U8_fast_8321c11aa8d0/forge_fair_v2kb8_U8_fast.exe" "option.EvalFileV2=$N/o30_gpu_soupU8r3r5r10r12r14.nnue2"
run int8 "$M" 1100 "$B/int8_6ffe14d0ceb8/forge_fair_int8.exe" "option.NnueInt8Vnni=1"
echo "QUEUE DONE $(date '+%F %T')" >> "$M/queue.log"
