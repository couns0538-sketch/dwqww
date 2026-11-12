#!/usr/bin/env bash
# regress_safe_load.sh <new folder under _work> - JOB E (2026-11-12): after the switch to h512/train/ckpt_io.py, do the
# tools that read checkpoints still give the results recorded before the switch? Writes only into the new folder.
#   1. test_ckpt_io.py: a file that carries a command is refused and the command does not run
#   2. average_ckpts.py on the two inputs of A12: the exported net must be byte-identical to _work/runs/avg/A12.fnn3
#   3. trainer selfcheck on the FB2 checkpoint: integer scorer result as in results/step1/selfcheck_trainer.json
#   4. parity_h512.py on candidate 3 with its float checkpoint: float-against-integer numbers as in
#      results/phase2/parity_candidate3.json, 0 mismatches
#   5. trainer start from the FB2 checkpoint (plan pilot_P2), stopped after step 5000, then resumed to step 10000:
#      the CKPT 1, step 5000 and step 10000 lines must equal results/step5/pilot_P2_log.txt (loss, data position)
set -u
D=/d/forge_jobs_20261111/h512E; source "$D/h512/train/env_h512.sh"; cd "$D"
O="$D/_work/$1"
if [ -e "$O" ]; then echo "refusing: $O exists"; exit 2; fi
mkdir -p "$O"
fail=0
ok() { echo "PASS $1"; }
no() { echo "FAIL $1"; fail=$((fail+1)); }

# syntax check without writing .pyc files
"$PY" -I -B -c "import ast, sys; [ast.parse(open(p, encoding='utf-8').read(), p) for p in sys.argv[1:]]" h512/train/ckpt_io.py h512/train/train_h512_gpu.py h512/train/fable_nnue_train.py h512/tools/average_ckpts.py h512/tools/parity_h512.py h512/tools/test_ckpt_io.py && ok "0. the edited files compile" || no "0. compile"

"$PY" -I -B h512/tools/test_ckpt_io.py --scratch "$O/ckpt_io" > "$O/1_test_ckpt_io.txt" 2>&1 && ok "1. $(tail -n 1 "$O/1_test_ckpt_io.txt")" || no "1. test_ckpt_io (see $O/1_test_ckpt_io.txt)"

"$PY" -I -B h512/tools/average_ckpts.py --pts _work/runs/main/stage_S1.pt _work/runs/main/stage_S2.pt --out-pt "$O/A12.pt" --out-net "$O/A12.fnn3" > "$O/2_average.txt" 2>&1
if cmp -s "$O/A12.fnn3" _work/runs/avg/A12.fnn3; then ok "2. averaged net byte-identical to A12.fnn3 ($(md5sum < "$O/A12.fnn3" | cut -c1-32))"; else no "2. averaged net differs (see $O/2_average.txt)"; fi

"$PY" -I -B h512/train/train_h512_gpu.py selfcheck --pos F:/opus_scratch/fable/data/holdout/fb2_holdout_200k.pos --rows 200000 \
    --ckpt F:/opus_scratch/fable/fb2/train_j1b/ckpt.pt --net F:/opus_scratch/fable/fb2/train_j1b/best.fnn3 --net-out "$O/reexport.fnn3" --out "$O/3_selfcheck.json" > "$O/3_selfcheck.txt" 2>&1
"$PY" -I -B - "$O/3_selfcheck.json" h512/results/step1/selfcheck_trainer.json > "$O/3_compare.txt" 2>&1 <<'EOF'
import json, sys
new, old = (json.load(open(p)) for p in sys.argv[1:3])
keys = ["features_mismatches", "features_rows", "int_scorer_gpu", "int_scorer_numpy", "fakequant_float_vs_int_cp", "pure_float_vs_int_cp", "phase_rows_equal", "coverage"]
bad = [k for k in keys if new.get(k) != old.get(k)]
print("selfcheck keys compared:", len(keys), "different:", bad, "int_scorer_gpu", new.get("int_scorer_gpu"))
sys.exit(1 if bad else 0)
EOF
[ $? -eq 0 ] && ok "3. $(tail -n 1 "$O/3_compare.txt" | cut -c1-200)" || no "3. selfcheck (see $O/3_compare.txt, $O/3_selfcheck.txt)"

N="$D/_work/nets/h512_cand_W2_seen10000023552"
"$PY" -I -B h512/tools/parity_h512.py --net "$(cygpath -m "$N.fnn3")" --ckpt "$(cygpath -m "${N}_float.pt")" --fens D:/forge_jobs_20261111/fairD/_work/data/fens_12k_v2.txt \
    --select-pos D:/forge_jobs_20261111/h512E/_work/data/select_2m.pos --tool D:/forge_jobs_20261111/h512E/_work/plain/forge_nnue_v3_tool_combo29.exe \
    --diag D:/forge_jobs_20261111/h512E/_work/builds/h512_v3_diag_56ae5025294a/forge_fair_h512_v3_diag.exe --work "$(cygpath -m "$O/parity")" --out "$(cygpath -m "$O/4_parity_c3.json")" > "$O/4_parity.txt" 2>&1
"$PY" -I -B - "$O/4_parity_c3.json" h512/results/phase2/parity_candidate3.json > "$O/4_compare.txt" 2>&1 <<'EOF'
import json, sys
new, old = (json.load(open(p)) for p in sys.argv[1:3])
keys = ["PASS", "positions", "net_md5", "float_vs_int", "gpu_int"]
bad = [k for k in keys if new.get(k) != old.get(k)]
t = new.get("tool", {})
print("parity keys compared:", len(keys), "different:", bad, "PASS", new.get("PASS"), "tool cp mismatches", t.get("cp_mismatches"),
      "fake-quantised float max cp", new.get("float_vs_int", {}).get("fake_quantised_float", {}).get("max_cp"))
sys.exit(1 if bad or not new.get("PASS") else 0)
EOF
[ $? -eq 0 ] && ok "4. $(tail -n 1 "$O/4_compare.txt" | cut -c1-220)" || no "4. parity (see $O/4_compare.txt, $O/4_parity.txt)"

R="$O/trainer"
"$PY" -I -B h512/train/train_h512_gpu.py train --plan h512/train/plans/pilot_P2.json --run-dir "$R" --max-pres 45000000 --log-every 5000 > "$O/5_first.txt" 2>&1
"$PY" -I -B h512/train/train_h512_gpu.py train --plan h512/train/plans/pilot_P2.json --run-dir "$R" --resume --max-pres 86000000 --log-every 5000 > "$O/5_resumed.txt" 2>&1
# The GPU trainer is not bit-reproducible from run to run (true before this change: results/step2 resume logs).
# Measured 2026-11-12, seven runs of these first 45M presentations (4 with the old loader, 3 with the new):
# CKPT 1 selection loss 0.014739..0.014756, step-5000 loss 0.007650..0.007674, data position identical in all.
# So: the data position (seen, idxsum) must be identical, the losses within 5e-5 of the original log.
"$PY" -I -B - "$R/log.txt" h512/results/step5/pilot_P2_log.txt > "$O/5_compare.txt" 2>&1 <<'EOF'
import re, sys
def read(path):
    out = {}
    for line in open(path, encoding="utf-8", errors="replace"):
        m = re.search(r" CKPT 1 seen (\d+) .*?mse_b0\.6 ([0-9.]+)", line)
        if m and "ckpt1" not in out:
            out["ckpt1"] = (int(m.group(1)), None, float(m.group(2)))
        m = re.search(r" step (5000|10000) .*? seen (\d+) loss ([0-9.]+) .*idxsum (\d+)", line)
        if m and "step" + m.group(1) not in out:
            out["step" + m.group(1)] = (int(m.group(2)), int(m.group(4)), float(m.group(3)))
    return out
new, old = read(sys.argv[1]), read(sys.argv[2])
bad = 0
for key in ("ckpt1", "step5000", "step10000"):
    if key not in new or key not in old:
        print(key, "missing"); bad += 1; continue
    same_pos = new[key][:2] == old[key][:2]
    close = abs(new[key][2] - old[key][2]) <= 5e-5
    print(f"{key}: data position {'identical' if same_pos else 'DIFFERENT'} (seen {new[key][0]}, idxsum {new[key][1]}); "
          f"loss {new[key][2]:.6f} against {old[key][2]:.6f} in the original log ({'within' if close else 'OUTSIDE'} 5e-5)")
    bad += 0 if (same_pos and close) else 1
sys.exit(1 if bad else 0)
EOF
rc=$?; while read -r line; do if [ $rc -eq 0 ]; then ok "5. $line"; else echo "     $line"; fi; done < "$O/5_compare.txt"
[ $rc -eq 0 ] || no "5. trainer start and resume against the original pilot log (see $O/5_compare.txt)"
grep -q "resumed\|resume" "$R/log.txt" && ok "5. the second run resumed from latest.pt: $(grep -m1 -i 'resum' "$R/log.txt" | cut -c21-140)" || no "5. no resume line in $R/log.txt"
echo "RESULT $([ $fail -eq 0 ] && echo PASS || echo FAIL): $fail failed"
exit $fail
