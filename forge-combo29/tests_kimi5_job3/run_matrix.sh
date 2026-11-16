#!/bin/bash
# kimi5 job3 matrix: control pair (off x2 d12), all configs d12+d8 fresh, 8 switches d12 repeat x2.
cd "$(dirname "$0")"
E=/tmp/k5cb/forge
F=first200.fens
run() { python3 k5_j3.py "$E" "$F" "$1" "$2" "$3" 200; }

lane1() {
  run off 12 fresh && mv k5_j3_off_d12_fresh.json k5_j3_off_d12_fresh_runA.json && mv k5_j3_off_d12_fresh_input.log k5_j3_off_d12_fresh_runA_input.log
  run thr 12 fresh
  run nsv 12 fresh
  run acr 12 fresh
  run off 8 fresh
  run thr 8 fresh
  run nsv 8 fresh
  run acr 8 fresh
  run lmrs 12 repeat && mv k5_j3_lmrs_d12_repeat.json k5_j3_lmrs_d12_repeat_r1.json && mv k5_j3_lmrs_d12_repeat_input.log k5_j3_lmrs_d12_repeat_r1_input.log
  run lmrs 12 repeat && mv k5_j3_lmrs_d12_repeat.json k5_j3_lmrs_d12_repeat_r2.json && mv k5_j3_lmrs_d12_repeat_input.log k5_j3_lmrs_d12_repeat_r2_input.log
  run thr 12 repeat && mv k5_j3_thr_d12_repeat.json k5_j3_thr_d12_repeat_r1.json && mv k5_j3_thr_d12_repeat_input.log k5_j3_thr_d12_repeat_r1_input.log
  run thr 12 repeat && mv k5_j3_thr_d12_repeat.json k5_j3_thr_d12_repeat_r2.json && mv k5_j3_thr_d12_repeat_input.log k5_j3_thr_d12_repeat_r2_input.log
}
lane2() {
  run off 12 fresh && mv k5_j3_off_d12_fresh.json k5_j3_off_d12_fresh_runB.json && mv k5_j3_off_d12_fresh_input.log k5_j3_off_d12_fresh_runB_input.log
  run ntv 12 fresh
  run ch4 12 fresh
  run hd 12 fresh
  run ntv 8 fresh
  run ch4 8 fresh
  run hd 8 fresh
  run ntv 12 repeat && mv k5_j3_ntv_d12_repeat.json k5_j3_ntv_d12_repeat_r1.json && mv k5_j3_ntv_d12_repeat_input.log k5_j3_ntv_d12_repeat_r1_input.log
  run ntv 12 repeat && mv k5_j3_ntv_d12_repeat.json k5_j3_ntv_d12_repeat_r2.json && mv k5_j3_ntv_d12_repeat_input.log k5_j3_ntv_d12_repeat_r2_input.log
  run nsv 12 repeat && mv k5_j3_nsv_d12_repeat.json k5_j3_nsv_d12_repeat_r1.json && mv k5_j3_nsv_d12_repeat_input.log k5_j3_nsv_d12_repeat_r1_input.log
  run nsv 12 repeat && mv k5_j3_nsv_d12_repeat.json k5_j3_nsv_d12_repeat_r2.json && mv k5_j3_nsv_d12_repeat_input.log k5_j3_nsv_d12_repeat_r2_input.log
}
lane3() {
  run lmrs 12 fresh
  run smp 12 fresh
  run six 12 fresh
  run lmrs 8 fresh
  run smp 8 fresh
  run six 8 fresh
  run ch4 12 repeat && mv k5_j3_ch4_d12_repeat.json k5_j3_ch4_d12_repeat_r1.json && mv k5_j3_ch4_d12_repeat_input.log k5_j3_ch4_d12_repeat_r1_input.log
  run ch4 12 repeat && mv k5_j3_ch4_d12_repeat.json k5_j3_ch4_d12_repeat_r2.json && mv k5_j3_ch4_d12_repeat_input.log k5_j3_ch4_d12_repeat_r2_input.log
  run acr 12 repeat && mv k5_j3_acr_d12_repeat.json k5_j3_acr_d12_repeat_r1.json && mv k5_j3_acr_d12_repeat_input.log k5_j3_acr_d12_repeat_r1_input.log
  run acr 12 repeat && mv k5_j3_acr_d12_repeat.json k5_j3_acr_d12_repeat_r2.json && mv k5_j3_acr_d12_repeat_input.log k5_j3_acr_d12_repeat_r2_input.log
}
lane4() {
  run hd 16 fresh
  run hd 12 repeat && mv k5_j3_hd_d12_repeat.json k5_j3_hd_d12_repeat_r1.json && mv k5_j3_hd_d12_repeat_input.log k5_j3_hd_d12_repeat_r1_input.log
  run hd 12 repeat && mv k5_j3_hd_d12_repeat.json k5_j3_hd_d12_repeat_r2.json && mv k5_j3_hd_d12_repeat_input.log k5_j3_hd_d12_repeat_r2_input.log
  run smp 12 repeat && mv k5_j3_smp_d12_repeat.json k5_j3_smp_d12_repeat_r1.json && mv k5_j3_smp_d12_repeat_input.log k5_j3_smp_d12_repeat_r1_input.log
  run smp 12 repeat && mv k5_j3_smp_d12_repeat.json k5_j3_smp_d12_repeat_r2.json && mv k5_j3_smp_d12_repeat_input.log k5_j3_smp_d12_repeat_r2_input.log
}
lane1 > lane1.log 2>&1 & lane2 > lane2.log 2>&1 & lane3 > lane3.log 2>&1 & lane4 > lane4.log 2>&1 &
wait
echo MATRIX_DONE
