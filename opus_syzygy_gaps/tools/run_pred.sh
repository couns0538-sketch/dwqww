#!/usr/bin/env bash
# run_pred.sh <claims exe tag> <rows file under out/exp/hunt> <label> [depth] - a root stored at clock 0 is read at an inner node of a later search (R3 finding 6): claim harness in two-position warm mode,
# all switches on and a control without SyzygyRule50 bit 1. Rows from gen_warm_pred_fixture.py. Output out/exp/hunt/pred_<label>_{on,ctl}_d<depth>.out
set -u
J=/d/forge_jobs_20261107/opus1
W='D:\forge_jobs_20261107\opus1'
T=$J/repo/opus_syzygy_gaps/tools
H=$J/out/exp/hunt; HW="$W\\out\\exp\\hunt"
exe=tb_claims_$1; rows=$2; label=$3; depth=${4:-12}
pin() { powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$T/pinned.ps1" "$@"; }
export TB_CLAIMS_WARM=2
for r in "SyzygyTbBounds=7 SyzygyRootExact=3 SyzygyRule50=3|on" "SyzygyTbBounds=7 SyzygyRootExact=3 SyzygyRule50=2|ctl"; do
  o=${r%|*}; n=${r#*|}
  pin -Exe "$W\\out\\exe\\$exe.exe" -ArgLine "D:\\syzygy345 $HW\\$rows 4 $depth 0 0 $o" -OutFile "$HW\\pred_${label}_${n}_d$depth.out" -ErrFile "$HW\\pred_${label}_${n}_d$depth.err"
  echo "== $label $n [$o] depth $depth exit $?"
  grep -vE 'wrong 0 ' "$H/pred_${label}_${n}_d$depth.out" | cut -c1-110
done
