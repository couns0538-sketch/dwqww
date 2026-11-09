#!/usr/bin/env bash
# final_chain.sh <git short head> <suite tag> - everything for the frozen head, one after the other: macro combinations, clean-room lint, freeze proof, reproduction from the pack, trial_w6 line, whole suite, option churn, two-position warm rows.
# One line per step in out/logs/final_chain_<head>.txt. Each step writes its own result file. Exits by itself.
set -u
J=/d/forge_jobs_20261107/opus1
W='D:\forge_jobs_20261107\opus1'
T=$J/repo/opus_syzygy_gaps/tools
WT="$W\\repo\\opus_syzygy_gaps\\tools"
VPY='C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe'
tag=$1; st=$2
L=$J/out/logs/final_chain_$tag.txt
say() { echo "$(date) $*" >> "$L"; }
say "start head $(git -C "$J/out/src/cand" log -1 --format=%h) dirty $(git -C "$J/out/src/cand" status --short | wc -l)"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$T/macro_combos.ps1" -Src "$W\\out\\src\\cand" > "$J/out/builds/macro_combos_$tag.txt" 2>&1
say "macro combos exit $? $(tail -1 "$J/out/builds/macro_combos_$tag.txt")"
python -I -B D:/o15/wt/opus_r15/tools/cleanroom_lint.py --patch "$J/repo/opus_syzygy_gaps/patches/syzygy_gaps_after_p6.patch" > "$J/out/builds/lint_$tag.txt" 2>&1
say "clean-room lint exit $? $(tail -1 "$J/out/builds/lint_$tag.txt")"
bash "$T/final_freeze.sh" "$tag" > "$J/out/logs/final_freeze_$tag.log" 2>&1
say "freeze exit $? $(tail -1 "$J/out/builds/final_$tag.txt" | cut -c1-80)"
B=$(sha256sum "$J/out/builds/buildB_c${tag}_pc1/forge_buildB_c${tag}_pc1.exe" | cut -c1-64 | tr a-z A-Z)
bash "$T/repro_from_pack.sh" "$tag" "$B" > "$J/out/logs/repro_$tag.log" 2>&1
say "repro exit $?"
bash "$T/after_w6.sh" "$tag" > "$J/out/logs/after_w6_$tag.log" 2>&1
say "after_w6 exit $?"
bash "$T/run_v6.sh" "$st" > "$J/out/logs/run_$st.log" 2>&1
say "suite exit $?"
bash "$T/run_churn.sh" "$st" "cand_${st}_plain" 3000 200 > "$J/out/logs/churn_$st.log" 2>&1
say "churn exit $?"
H="$W\\out\\exp\\hunt"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$T/pinned.ps1" -Exe "$VPY" -ArgLine "-I -B $WT\\gen_warm_pred_fixture.py D:\\syzygy345 $W\\out\\exp\\warm\\f1.clock.tsv $H\\pred2.tsv --per-root 3 --plies 2" -Log "$H\\pred2.log"
bash "$T/run_pred.sh" "h$st" pred1.tsv "${st}_p1" 12 > "$J/out/logs/pred1_$st.log" 2>&1
say "pred 1 exit $?"
bash "$T/run_pred.sh" "h$st" pred2.tsv "${st}_p2" 12 > "$J/out/logs/pred2_$st.log" 2>&1
say "pred 2 exit $?"
say "end"
