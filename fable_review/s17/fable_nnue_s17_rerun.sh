#!/usr/bin/env bash
# Re-run Opus S17 step 4b-6 (real window split + leak audit) from the exported job folder; read-only inputs.
set -u
S=/f/opus_scratch/fable_review/s17; J=$S/job/opus_round1/sol_S17
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe   # 3.10 + numpy (audit); the split uses the system python 3.14 as Opus did
SYSPY=C:/Python314/python.exe
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 TMP=$S/tmp TEMP=$S/tmp
mkdir -p "$S/real_inputs" "$S/real_split1/work" "$S/tmp"
echo "# S17 re-run $(date)"
echo "## step 4b: real window (last 200k rows of 010)"
( cd "$J" && nice -n 19 "$SYSPY" -I -B real_window_build.py D:/grok-pc-data/forge_push/nnue_data/pos D:/grok-pc-data/forge_push/nnue_data/hce D:/grok-pc-data/selfplay_out forge_selfplay_010 200000 "$S/real_inputs" forge_selfplay_010_last200k ) || { echo "window build failed"; exit 1; }
echo "## copy 011 / 012 inputs (read-only sources)"
for n in 011 012; do
  cp -n /d/grok-pc-data/selfplay_out/forge_selfplay_$n.txt "$S/real_inputs/"
  cp -n /d/grok-pc-data/forge_push/nnue_data/pos/forge_selfplay_$n.pos "$S/real_inputs/"
  cp -n /d/grok-pc-data/forge_push/nnue_data/hce/forge_selfplay_$n.hce "$S/real_inputs/"
done
( cd "$S/real_inputs" && md5sum *.txt *.pos *.hce )
cp "$J/results/real_split_config.json" "$S/real_split1/config.json"
echo "## step 5: split (diagnostic mode, seed 20261026, 1000 bp)"
date
( cd "$J" && timeout 1500 nice -n 19 "$SYSPY" -I -B gamesplit_v2/forge_sol_S17_gamesplit_v2_20261027.py --config "$S/real_split1/config.json" --diagnostic-mode ); echo "split exit $?"
date
echo "## step 6: leak audit"
( cd "$J" && nice -n 19 "$PY" -I -B audit_split_leak.py "$S/real_split1/config.json" "$S/real_split1/split_out" "$S/real_split1/audit" ); echo "audit exit $?"
echo "## compare with the committed results"
( cd "$S/real_split1/split_out" && sha256sum * ) > "$S/rerun_SHA256SUMS"
"$SYSPY" -I -B - <<'PYEOF'
import json, re
S = 'F:/opus_scratch/fable_review/s17'
J = S + '/job/opus_round1/sol_S17'
ref = {l.split()[1]: l.split()[0] for l in open(J + '/results/real_split_outputs_SHA256SUMS') if l.strip()}
new = {l.split()[1]: l.split()[0] for l in open(S + '/rerun_SHA256SUMS') if l.strip()}
same = [f for f in ref if new.get(f) == ref[f]]
diff = [f for f in ref if f in new and new[f] != ref[f]]
missing = [f for f in ref if f not in new]
print(f"output files: {len(ref)} committed hashes; identical {len(same)}; different {diff}; missing {missing}")
import glob
sfile = glob.glob(S + '/real_split1/split_out/*summary*.json')
if sfile:
    d = json.load(open(sfile[0])); r = json.load(open(J + '/results/forge_sol_S17_summary_20261026.json'))
    keys = ['groups', 'assigned_validation_groups', 'dropped_rows', 'dropped_reasons', 'cross_split_defined_groups', 'cross_split_position_overlap', 'rows', 'status']
    for k in keys:
        print(f"{k}: rerun {d.get(k)} | opus {r.get(k)} | {'same' if d.get(k) == r.get(k) else 'DIFFERENT'}")
PYEOF
echo "# done $(date)"
