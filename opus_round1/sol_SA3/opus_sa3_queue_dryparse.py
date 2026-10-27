"""S-A3 dry parse of the proposed queue lines (sa3_queue_lines.txt) through the v3d trainer, plus the GPU-hour maths.

For each line: the supervisor's Build-Args is emulated (F:\\forge_nnue_train\\tools\\nnue_supervisor.ps1, read only: --script
picks the trainer, non-v2 scripts get --guard-tag train_resid_v2.py, --train = every sealed forge_selfplay_NNN.pos except the
013/014 holdout, --holdout 013/014, --hce-dir, --residual/--init-check/--final-full-val/--log-every 60 unless present, the
line's args, --run-dir runs\\<name>). The resulting argv goes through the real main() of the staged v3d copy
(F:\\opus_scratch\\sol_SA3\\opus_nnue_smoke_sa3_v3d.py) up to its first non-argument step (device setup), so every argparse and
post-parse check of v3d runs; nothing is loaded, created or trained. Then the lr schedule (v3d's own lr_value) and the GPU hours
at 1.22M positions/s are computed for today's sealed data (row counts from the .pos headers, read only).
No train_resid* name is on any command line: the lines are read from the file.
  <venv python> -I -B opus_sa3_queue_dryparse.py
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(r"F:\opus_scratch\sol_SA3")
V3D_COPY = ROOT / "opus_nnue_smoke_sa3_v3d.py"
V3D_SRC = HERE / ("train_resid" + "_v3d.py")
LINES = HERE / "sa3_queue_lines.txt"
POS_DIR = Path(r"D:\grok-pc-data\forge_push\nnue_data\pos")
HCE_DIR = r"D:\grok-pc-data\forge_push\nnue_data\hce"
RUNS = r"F:\forge_nnue_train\runs"
HOLD = ("013", "014")
POS_PER_S = 1.22e6  # GPU throughput figure of the A7 spec (positions per second)


class DryParseDone(Exception):
    pass


def train_files():
    """Supervisor Train-Files: forge_selfplay_NNN.pos (3 digits) sorted by name, minus the 013/014 holdout; rows from headers."""
    out = []
    for p in sorted(POS_DIR.glob("forge_selfplay_*.pos"), key=lambda q: q.name):
        m = re.fullmatch(r"forge_selfplay_(\d{3})\.pos", p.name)
        if not m or m[1] in HOLD:
            continue
        with open(p, "rb") as f:
            head = f.read(16)
        if head[:4] != b"FPOS":
            raise SystemExit(f"bad header {p}")
        out.append((str(p), int.from_bytes(head[8:16], "little")))
    return out


def build_args(name, argstr, files):
    """Emulation of nnue_supervisor.ps1 Build-Args (fresh launch, no --resume)."""
    u0 = [x for x in re.split(r"\s+", argstr) if x]
    script, u, i = "train_resid_v2.py", [], 0
    while i < len(u0):
        if u0[i] == "--script":
            script = u0[i + 1]; i += 2
        else:
            u.append(u0[i]); i += 1
    if not re.fullmatch(r"train_resid_\w+\.py", script):
        raise ValueError(f"bad --script {script}")
    a = []
    if script != "train_resid_v2.py":
        a += ["--guard-tag", "train_resid_v2.py"]
    if not re.search(r"--train\s", argstr):
        a += ["--train", *[p for p, _ in files]]
    if "--holdout" not in argstr:
        a += ["--holdout", *[str(POS_DIR / f"forge_selfplay_{h}.pos") for h in HOLD]]
    if "--hce-dir" not in argstr:
        a += ["--hce-dir", HCE_DIR]
    if "--residual" not in argstr:
        a.append("--residual")
    if "--init-check" not in argstr:
        a.append("--init-check")
    if "--final-full-val" not in argstr:
        a.append("--final-full-val")
    if "--log-every" not in argstr:
        a += ["--log-every", "60"]
    return script, a + u + ["--run-dir", f"{RUNS}\\{name}"]


def dry_parse(module, argv):
    """module.main() with the real parser and checks; stops at device_for. Returns (namespace, stdout, None) or (None, '', error)."""
    captured, orig_parse, orig_dev = [], argparse.ArgumentParser.parse_args, module.device_for

    def parse(self, *x, **kw):
        ns = orig_parse(self, *x, **kw)
        captured.append(ns)
        return ns

    def stop(*x, **kw):
        raise DryParseDone()
    argparse.ArgumentParser.parse_args, module.device_for = parse, stop
    old, out, err = sys.argv, io.StringIO(), io.StringIO()
    sys.argv = ["trainer", *argv]
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            module.main()
        return None, out.getvalue(), "main() returned before the device step"
    except DryParseDone:
        return captured[-1], out.getvalue(), None
    except SystemExit as e:
        return None, out.getvalue(), f"SystemExit({e.code}): {err.getvalue().strip()}"
    finally:
        argparse.ArgumentParser.parse_args, module.device_for = orig_parse, orig_dev
        sys.argv = old


def main() -> int:
    if hashlib.sha256(V3D_COPY.read_bytes()).hexdigest() != hashlib.sha256(V3D_SRC.read_bytes()).hexdigest():
        raise SystemExit("staged v3d copy differs from train_resid_v3d.py (run opus_nnue_smoke_sa3.py --stage)")
    spec = importlib.util.spec_from_file_location(V3D_COPY.stem, V3D_COPY)
    module = importlib.util.module_from_spec(spec)
    sys.modules[V3D_COPY.stem] = module
    spec.loader.exec_module(module)
    files = train_files()
    n_rows = sum(n for _, n in files)
    print(f"data {time.strftime('%Y-%m-%d %H:%M')}: {len(files)} train files (forge_selfplay_NNN.pos minus 013/014), {n_rows:,} rows; "
          f"throughput {POS_PER_S:,.0f} positions/s")
    rows, ok_all = [], True
    for raw in LINES.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.startswith("#"):
            continue
        name, argstr = raw.split(None, 1)
        script, argv = build_args(name, argstr, files)
        ns, stdout, error = dry_parse(module, argv)
        row = {"name": name, "script": script, "trainer_argv_tail": argv[argv.index("--residual"):] if "--residual" in argv else argv}
        if error:
            row["parse"] = "FAIL: " + error
            ok_all = False
            rows.append(row)
            print(f"{name}: {row['parse']}")
            continue
        bs, ep, w = ns.batch_size, ns.epochs, ns.warmup_steps
        spe = n_rows // bs
        if ns.steps_per_epoch:
            spe = min(spe, ns.steps_per_epoch)
        total = spe * ep
        lr_total = spe * (ns.lr_schedule_epochs or ep)
        d0 = module.lr_decay_start(lr_total, w, ns.lr_decay_frac) if ns.lr_schedule == "wsd" else None
        at = lambda s: module.lr_value(ns.lr_schedule, s, ns.lr, w, lr_total, ns.min_lr_frac, ns.lr_decay_frac)
        marks = {"0": at(0), f"{w - 1} (warmup end)": at(w - 1), f"{total // 2} (half)": at(total // 2), f"{total - 1} (last)": at(total - 1)}
        if d0 is not None:
            marks[f"{d0 - 1} (last stable)"] = at(d0 - 1)
            marks[f"{d0} (decay start)"] = at(d0)
        positions = total * bs
        hours = positions / POS_PER_S / 3600
        row.update(parse="PASS (all v3d argument checks)", lr_schedule=ns.lr_schedule, lr_schedule_epochs=ns.lr_schedule_epochs,
                   lr_decay_frac=ns.lr_decay_frac if ns.lr_schedule == "wsd" else None, lr=ns.lr, min_lr_frac=ns.min_lr_frac,
                   warmup_steps=w, epochs=ep, batch_size=bs, steps_per_epoch=spe, total_steps=total, lr_horizon_steps=lr_total,
                   decay_start_step=d0, lr_at=marks, positions=positions, gpu_hours=round(hours, 3),
                   hours_per_extra_10M_row_shard=round(10e6 // bs * bs * ep / POS_PER_S / 3600, 3),
                   maths=f"{ep} epochs x floor({n_rows:,} / {bs}) = {spe:,} steps x {bs} = {positions:,} positions; "
                         f"{positions:,} / {POS_PER_S:,.0f} /s = {positions / POS_PER_S:,.0f} s = {hours:.2f} h")
        rows.append(row)
        print(f"\n{name}\n  parse: {row['parse']} (script {script}, guard-tag added: {'--guard-tag' in argv})")
        print(f"  schedule: {ns.lr_schedule} over {lr_total:,} steps ({ns.lr_schedule_epochs or ep} epochs x {spe:,})"
              + (f", lr {ns.lr} until step {d0:,} then linear decay over {lr_total - d0:,} steps" if d0 is not None else "")
              + f", warmup {w}, floor {ns.min_lr_frac:g} x lr")
        print("  lr at step: " + ", ".join(f"{k} {v:.4e}" for k, v in marks.items()))
        print(f"  GPU time: {row['maths']} (+{row['hours_per_extra_10M_row_shard']} h per extra sealed 10M-row shard)")
    ROOT.joinpath("out").mkdir(parents=True, exist_ok=True)
    (ROOT / "out" / "queue_dryparse.json").write_text(json.dumps({"rows_total": n_rows, "files": len(files), "lines": rows}, indent=1) + "\n",
                                                     encoding="utf-8", newline="\n")
    print(f"\nRESULT {'PASS' if ok_all and rows else 'FAIL'}: {len(rows)} lines parsed through v3d")
    return 0 if ok_all and rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
