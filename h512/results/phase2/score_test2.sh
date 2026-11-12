#!/usr/bin/env bash
# score_test2.sh <name>=<net file> [<name>=<net file> ...] - JOB E phase 2: score test set 2 ONCE.
# Run a single time, after all training of phase 2 has ended and every candidate is frozen. It scores each given net
# (the frozen candidates and FB2's best net) and combo29's evaluator (s198 + HCE, which also gives HCE alone) on
# _work/data/final_test2_2m.pos. The trainer's scorer refuses this file without --final-test-unlock and appends every
# access to _work/data/FINAL_TEST_ACCESS.log. The script refuses to run twice.
set -u
D=/d/forge_jobs_20261111/h512E; source "$D/h512/train/env_h512.sh"
W=D:/forge_jobs_20261111/h512E
O="$D/h512/results/phase2/test2"
[ -e "$O" ] && { echo "refused: test set 2 was already scored ($O exists)"; exit 2; }
mkdir -p "$O"
T="$W/_work/data/final_test2_2m.pos"
echo "$(date '+%F %T') test set 2 scoring session start" >> "$O/SESSION.log"
for pair in "$@"; do
  name="${pair%%=*}"; net="${pair#*=}"
  "$PY" -I -B "$D/h512/train/train_h512_gpu.py" score --net "$net" --pos "$T" --final-test-unlock --name "$name" --out "$W/h512/results/phase2/test2/$name.json" > /dev/null
  echo "$(date '+%F %T') scored $name $net md5 $(md5sum "$net" | cut -c1-32)" >> "$O/SESSION.log"
done
"$PY" -I -B F:/opus_scratch/fable/s31tool/forge_sol_S31_avg_ckpt.py score --nets "$W/forge-combo29/src/nnue_weights.inc" --pos "$T" --hce-dir "$W/_work/data" --out "$W/h512/results/phase2/test2/s198_hce.json" > "$O/s198_hce.log" 2>&1
echo "$(date '+%F %T') scored s198 + HCE and HCE alone" >> "$O/SESSION.log"
cp "$D/_work/data/FINAL_TEST_ACCESS.log" "$O/FINAL_TEST_ACCESS.log"
"$PY" -I -B - "$O" <<'PY'
import glob, json, os, sys
o = sys.argv[1]
rows = []
for p in sorted(glob.glob(os.path.join(o, "*.json"))):
    d = json.load(open(p, encoding="utf-8"))
    if "hce_baseline" in d:
        rows.append(("HCE alone", d["hce_baseline"]["mse_b0.6"], d["hce_baseline"]["mse_b0.8"], d["hce_baseline"]["mse_b1.0"]))
        n = d["nets"][0]
        rows.append(("s198 + HCE", n["mse_b0.6"], n["mse_b0.8"], n["mse_b1.0"]))
    else:
        rows.append((d["name"], d["mse_b0.6"], d["mse_b0.8"], d["mse_b1.0"]))
for r in sorted(rows, key=lambda r: r[1]):
    print(f"{r[0]:28s} b0.6 {r[1]:.6f}  b0.8 {r[2]:.6f}  b1.0 {r[3]:.6f}")
PY
