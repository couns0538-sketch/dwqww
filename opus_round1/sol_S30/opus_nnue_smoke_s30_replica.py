"""S30 part 2: tiny CPU replicas of the residual NNUE recipe on the data32 sample: 4 data sizes x 3 epoch counts,
fixed seeds, run twice; FINAL losses are parsed and fitted against data size and epochs.

CPU smoke only (QA rule): a byte-identical copy of the v3b trainer named opus_nnue_smoke_s30_v3b.py (never
train_resid*), one Torch thread, BelowNormal priority, output only under F:\\opus_scratch\\sol_S30\\replicas\\<tag>,
stop before a run if available RAM < 6 GiB, and stop at once if the NNUE supervisor's log shows a new
"adopted running job" line. The data32 sample's results are synthetic: every number is a pipeline result.

  <venv python> -I -B opus_nnue_smoke_s30_replica.py --tag r1   (then --tag r2, then --compare r1 r2)

Recipe (scaled down from f006): --shape 64 --residual --device cpu --epochs E --batch-size 512 --lr 0.000707
--warmup-steps 20 --blend-end 0.6 --seed 25 --val-positions 0 --final-full-val --max-train N; train = data32
t00000..t03000 (file prefixes), holdout = h000 (50,000 positions). N in {4000, 8000, 16000, 32000} (2-16 % of the
200k sample), E in {2, 4, 8}.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

LA = Path(r"D:\grok-pc-data\dwqww\.claude\worktrees\b\pkg\forge_LOCK_AL1_s198_FULL_20261026_1039")
SRC_TRAINER = LA / "5_nnue/trainers/cpu_smoke/train_resid_v3b.py"
SRC_ADAM = LA / "5_nnue/trainers/cpu_smoke/qa_adam_dml.py"
SRC_SAMPLE = LA / "5_nnue/sample_data/data32_sample/data32_sample_50k"
ROOT = Path(r"F:\opus_scratch\sol_S30")
INPUTS = ROOT / "inputs"
TRAINER = INPUTS / "trainer" / "opus_nnue_smoke_s30_v3b.py"
ADAM = INPUTS / "trainer" / "qa_adam_dml.py"
SAMPLE = INPUTS / "data32_sample_50k"
SUPERVISOR_LOG = Path(r"F:\forge_nnue_train\supervisor.log")
TRAINER_SHA = "5cebba4d44133630e247d9ab4c0085fa6301dde8db1dfe1389452ac19d92313f"
SIZES = (4000, 8000, 16000, 32000)
EPOCHS = (2, 4, 8)
FREE_RAM_FLOOR = 6 * 1024**3
FINAL = re.compile(r"^FINAL FULL HOLDOUT n=([\d,]+): net mse_teacher=(\S+) mse_b0\.6=(\S+) mse_b0\.8=(\S+) \| HCE (\S+)/(\S+)/b0\.8 (\S+)")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stage() -> None:
    if not TRAINER.exists():
        TRAINER.parent.mkdir(parents=True)
        shutil.copyfile(SRC_TRAINER, TRAINER)
        shutil.copyfile(SRC_ADAM, ADAM)
        SAMPLE.mkdir(parents=True)
        for name in ("t00000", "t01000", "t02000", "t03000", "h000"):
            for ext in (".pos", ".hce"):
                shutil.copyfile(SRC_SAMPLE / (name + ext), SAMPLE / (name + ext))
    if sha256(TRAINER) != TRAINER_SHA:
        raise SystemExit("trainer copy differs from the pinned v3b trainer")


def adoptions_since(t0: float) -> list[str]:
    if not SUPERVISOR_LOG.exists():
        return []
    with open(SUPERVISOR_LOG, "rb") as stream:
        stream.seek(0, os.SEEK_END)
        stream.seek(max(0, stream.tell() - 65536))
        tail = stream.read().decode("utf-8", "replace").splitlines()
    since = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(t0 - 1))
    return [line for line in tail if "adopted running job" in line and line[:19] >= since]


def free_ram() -> int:
    import psutil
    return int(psutil.virtual_memory().available)


def argv_for(n: int, epochs: int, run: Path) -> list[str]:
    train = [str(SAMPLE / f"{s}.pos") for s in ("t00000", "t01000", "t02000", "t03000")]
    return ["--train", *train, "--holdout", str(SAMPLE / "h000.pos"), "--hce-dir", str(SAMPLE), "--device", "cpu",
            "--shape", "64", "--residual", "--epochs", str(epochs), "--batch-size", "512", "--lr", "0.000707",
            "--warmup-steps", "20", "--blend-end", "0.6", "--seed", "25", "--val-positions", "0", "--final-full-val",
            "--max-train", str(n), "--run-dir", str(run)]


def child(run: Path, argv: list[str]) -> int:
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    spec = importlib.util.spec_from_file_location("opus_nnue_smoke_s30_v3b", TRAINER)
    trainer = importlib.util.module_from_spec(spec)
    sys.modules["opus_nnue_smoke_s30_v3b"] = trainer
    spec.loader.exec_module(trainer)
    sys.argv = [str(TRAINER), *argv]
    return trainer.main()


def run_tag(tag: str) -> int:
    stage()
    out = ROOT / "replicas" / tag
    out.mkdir(parents=True)
    rows = []
    env = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1",
               TMP=str(out), TEMP=str(out))
    for n in SIZES:
        for epochs in EPOCHS:
            name = f"n{n}_e{epochs}"
            if free_ram() < FREE_RAM_FLOOR:
                rows.append({"cfg": name, "status": "NOT_STARTED_FREE_RAM"})
                break
            run = out / name
            t0 = time.time()
            with open(out / f"{name}.stdout", "xb") as so:
                proc = subprocess.Popen([sys.executable, "-I", "-B", str(Path(__file__).resolve()), "--child", str(run), "--",
                                         *argv_for(n, epochs, run)], stdout=so, stderr=subprocess.STDOUT, env=env,
                                        creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS)
                adopted = []
                while proc.poll() is None:
                    time.sleep(1.0)
                    adopted = adoptions_since(t0)
                    if adopted:
                        proc.kill()
                        break
                rc = proc.wait()
            text = (out / f"{name}.stdout").read_text(encoding="utf-8", errors="replace")
            final = [FINAL.match(line) for line in text.splitlines() if line.startswith("FINAL FULL HOLDOUT")]
            row = {"cfg": name, "n": n, "epochs": epochs, "rc": rc, "seconds": round(time.time() - t0, 1), "adopted": adopted}
            if final and final[0]:
                m = final[0]
                row.update(teacher=float(m[2]), b06=float(m[3]), b08=float(m[4]), hce_teacher=float(m[5]), hce_b06=float(m[6]))
                artifacts = sorted(p for p in run.iterdir() if p.suffix in (".pt", ".inc", ".bin", ".json"))
                row["artifacts_sha256"] = {p.name: sha256(p) for p in artifacts}
            row["status"] = "PASS" if rc == 0 and final and not adopted else "FAIL"
            rows.append(row)
            print(f"{name}: {row['status']} rc {rc} {row['seconds']} s b0.6 {row.get('b06')} teacher {row.get('teacher')}", flush=True)
            if adopted:
                break
    (out / "replicas.json").write_text(json.dumps({"tag": tag, "rows": rows, "trainer_sha256": TRAINER_SHA}, indent=2, sort_keys=True) + "\n",
                                       encoding="utf-8", newline="\n")
    return 0 if all(r.get("status") == "PASS" for r in rows) and len(rows) == len(SIZES) * len(EPOCHS) else 1


def compare(a: str, b: str) -> int:
    ra = json.loads((ROOT / "replicas" / a / "replicas.json").read_text(encoding="utf-8"))["rows"]
    rb = json.loads((ROOT / "replicas" / b / "replicas.json").read_text(encoding="utf-8"))["rows"]
    same = all(x.get("artifacts_sha256") == y.get("artifacts_sha256") and x.get("b06") == y.get("b06") for x, y in zip(ra, rb))
    print(f"| N positions | epochs | b0.6 | teacher | HCE b0.6 |\n|---:|---:|---:|---:|---:|")
    for r in ra:
        print(f"| {r['n']} | {r['epochs']} | {r.get('b06')} | {r.get('teacher')} | {r.get('hce_b06')} |")
    print(f"REPRODUCIBLE {a} vs {b}: {same}")
    return 0 if same else 1


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "--child":
        return child(Path(argv[1]), argv[3:])
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tag")
    ap.add_argument("--compare", nargs=2)
    args = ap.parse_args(argv)
    if args.compare:
        return compare(*args.compare)
    if not args.tag or not re.fullmatch(r"r\d+", args.tag):
        ap.error("--tag r1, r2, ...")
    return run_tag(args.tag)


if __name__ == "__main__":
    raise SystemExit(main())
