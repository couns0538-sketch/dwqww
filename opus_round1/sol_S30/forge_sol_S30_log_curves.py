"""S30 part 1: read the NNUE training history (run logs) read-only and build loss tables, epoch curves and the seed
spread, citing file:line for every number.

  python -I -B forge_sol_S30_log_curves.py --runs F:/forge_nnue_train/runs --out F:/opus_scratch/sol_S30/out

Reads <runs>/*.log (and *.resumeN.log, *.cmd.txt); skips *.guard.log, *.chain.log and *.export_*.log. Parses:
  "EPOCH n/N done in ... train_mse=... | HOLDOUT n=V mse_teacher=T (HCE ...) mse_b0.6=B6 (HCE ...) mse_b0.8=B8"
  "FINAL FULL HOLDOUT n=V: net mse_teacher=T mse_b0.6=B6 mse_b0.8=B8 | HCE t/b6/b0.8 b8"
  "train: P positions from F files", "steps/epoch=S total=... batch=B lr=L cosine blend X->Y", "resumed ..."
and the recipe from the run's cmd.txt (--shape --epochs --lr --blend-end --seed --batch-size --warmup-steps
--val-positions, the trainer script name, the number of --train files). Writes (all new files; the output dir must
not be inside the runs folder):
  final_table.csv   one row per run with a FINAL FULL HOLDOUT line (file:line), recipe, data size
  epoch_curves.csv  every EPOCH line (file:line)
  seed_spread.csv   runs grouped by recipe without the seed: count, mean, min, max, sd of the FINAL losses
  summary.json      the same, plus input file hashes and the parse counts
Deterministic: files sorted by name, fixed formatting.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import statistics
from pathlib import Path

EPOCH = re.compile(r"^EPOCH (\d+)/(\d+) done in (\S+)s train_mse=(\S+) \| HOLDOUT n=([\d,]+) mse_teacher=(\S+) \(HCE (\S+), [^)]*\) "
                   r"mse_b0\.6=(\S+) \(HCE (\S+), [^)]*\) mse_b0\.8=(\S+)")
FINAL = re.compile(r"^FINAL FULL HOLDOUT n=([\d,]+): net mse_teacher=(\S+) mse_b0\.6=(\S+) mse_b0\.8=(\S+) \| HCE (\S+)/(\S+)/b0\.8 (\S+)")
TRAIN = re.compile(r"^train: ([\d,]+) positions from (\d+) files")
STEPS = re.compile(r"^steps/epoch=([\d,]+) total=([\d,]+) batch=(\d+) lr=(\S+) cosine blend (\S+)->(\S+)")
RECIPE_FLAGS = ("--shape", "--epochs", "--lr", "--blend-end", "--seed", "--batch-size", "--warmup-steps", "--val-positions",
                "--adam-impl", "--blend-start", "--min-lr-frac", "--sigmoid-k")
SKIP = (".guard.log", ".chain.log")


def num(text: str) -> float:
    return float(text.replace(",", ""))


def run_name(path: Path) -> str:
    name = path.name
    name = re.sub(r"\.resume\d+\.log$", "", name)
    return re.sub(r"\.log$", "", name)


def read_lines(path: Path) -> list[str]:
    return path.read_bytes().decode("utf-8", "replace").replace("\x00", "").replace("\r", "").split("\n")


def parse_cmd(path: Path) -> dict:
    if not path.exists():
        return {}
    text = path.read_bytes().decode("utf-8", "replace").replace("\r", "")
    tokens = text.split()
    recipe = {}
    for flag in RECIPE_FLAGS:
        if flag in tokens:
            i = tokens.index(flag)
            if i + 1 < len(tokens) and not tokens[i + 1].startswith("--"):
                recipe[flag[2:]] = tokens[i + 1]
    if "--train" in tokens:
        i = tokens.index("--train") + 1
        n = 0
        while i < len(tokens) and not tokens[i].startswith("--"):
            n += 1
            i += 1
        recipe["train_files_cmd"] = n
    for token in tokens:
        if token.endswith(".py") and "train" in token.lower():
            recipe["trainer"] = Path(token).name
            break
    recipe["residual"] = "--residual" in tokens
    recipe["final_full_val"] = "--final-full-val" in tokens
    return recipe


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    runs, out = args.runs.resolve(), args.out.resolve()
    if out == runs or runs in out.parents:
        ap.error("--out must not be inside the runs folder")
    out.mkdir(parents=True, exist_ok=False)
    logs = sorted(p for p in runs.glob("*.log") if not p.name.endswith(SKIP) and ".export_" not in p.name)
    finals, epochs, meta, hashes = [], [], {}, {}
    for log in logs:
        name = run_name(log)
        hashes[log.name] = hashlib.sha256(log.read_bytes()).hexdigest()
        info = meta.setdefault(name, {"run": name, **parse_cmd(runs / f"{name}.cmd.txt")})
        for number, line in enumerate(read_lines(log), 1):
            where = f"{log.name}:{number}"
            m = EPOCH.match(line)
            if m:
                epochs.append({"run": name, "where": where, "epoch": int(m[1]), "epochs": int(m[2]), "seconds": num(m[3]),
                               "train_mse": num(m[4]), "holdout_n": int(num(m[5])), "teacher": num(m[6]), "hce_teacher": num(m[7]),
                               "b06": num(m[8]), "hce_b06": num(m[9]), "b08": num(m[10])})
                continue
            m = FINAL.match(line)
            if m:
                finals.append({"run": name, "where": where, "holdout_n": int(num(m[1])), "teacher": num(m[2]), "b06": num(m[3]),
                               "b08": num(m[4]), "hce_teacher": num(m[5]), "hce_b06": num(m[6]), "hce_b08": num(m[7])})
                continue
            m = TRAIN.match(line)
            if m and "train_positions" not in info:
                info.update(train_positions=int(num(m[1])), train_files=int(m[2]), train_where=where)
                continue
            m = STEPS.match(line)
            if m and "steps_per_epoch" not in info:
                info.update(steps_per_epoch=int(num(m[1])), total_steps=int(num(m[2])), batch=int(m[3]), lr_log=m[4],
                            blend=f"{m[5]}->{m[6]}", steps_where=where)
    rows = []
    for f in finals:
        info = meta[f["run"]]
        rows.append({**f, **{k: info.get(k) for k in ("shape", "epochs", "lr", "blend-end", "seed", "batch-size", "warmup-steps",
                                                     "val-positions", "trainer", "train_positions", "train_files", "train_where")}})
    key_fields = ("shape", "epochs", "lr", "blend-end", "batch-size", "warmup-steps", "train_positions")
    groups = {}
    for r in rows:
        groups.setdefault(tuple(r.get(k) for k in key_fields), []).append(r)
    spread = []
    for key, members in sorted(groups.items(), key=lambda kv: [str(x) for x in kv[0]]):
        entry = dict(zip(key_fields, key))
        entry["runs"] = len(members)
        entry["members"] = " ".join(f"{m['run']}@{m['where'].split(':')[1]}" for m in members)
        for metric in ("teacher", "b06"):
            values = [m[metric] for m in members]
            entry[f"{metric}_mean"] = statistics.fmean(values)
            entry[f"{metric}_min"], entry[f"{metric}_max"] = min(values), max(values)
            entry[f"{metric}_sd"] = statistics.stdev(values) if len(values) > 1 else None
        spread.append(entry)

    def write_csv(path, items):
        fields = sorted({k for item in items for k in item})
        with open(path, "w", newline="", encoding="utf-8") as stream:
            w = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
            w.writeheader()
            for item in items:
                w.writerow(item)

    write_csv(out / "final_table.csv", rows)
    write_csv(out / "epoch_curves.csv", epochs)
    write_csv(out / "seed_spread.csv", spread)
    summary = {"tool": "forge_sol_S30_log_curves", "runs_dir": str(runs), "logs_read": len(logs), "final_lines": len(finals),
               "epoch_lines": len(epochs), "runs_with_final": len({r["run"] for r in rows}), "log_sha256": hashes,
               "final_table": rows, "seed_spread": spread}
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(f"logs {len(logs)}, FINAL lines {len(finals)}, EPOCH lines {len(epochs)}, recipe groups {len(spread)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
