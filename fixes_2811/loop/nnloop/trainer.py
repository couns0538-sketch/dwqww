"""Training backends.

nnue_pytorch: runs the official trainer (train.py) and exporter (serialize.py).
command:      runs your own commands (config train.train_cmd / train.export_cmd), for engines whose
              nets the official trainer cannot write.

Both return the same dictionary: net file, model file for continuing, losses, timing.
"""
from __future__ import annotations

import csv
import math
import os
import subprocess
import time
from pathlib import Path

from .common import child_env, log, now, python_exe, run_logged, tail_text


def _find_last_ckpt(out_dir: Path) -> Path | None:
    cands = list(out_dir.glob("training_logs/version_*/checkpoints/last.ckpt"))
    return max(cands, key=lambda p: p.stat().st_mtime) if cands else None


def _read_metrics(out_dir: Path) -> dict:
    train, val, lr = [], [], None
    files = sorted(out_dir.glob("training_logs/version_*/metrics.csv"), key=lambda p: p.stat().st_mtime)
    for mf in files:
        with open(mf, "r", encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                v = row.get("train_loss_epoch")
                if v:
                    train.append(float(v))
                for key in ("val_loss", "val_loss_epoch"):
                    v = row.get(key)
                    if v:
                        val.append(float(v))
                        break
                if row.get("lr"):
                    lr = float(row["lr"])
    return {"train_loss_epochs": train, "val_loss_epochs": val, "last_lr": lr}


def _run_trainer(cmd: list[str], cwd: str, env: dict, log_path: Path, marker: Path, grace_s: int = 120) -> int:
    """Run train.py; if it has written its 'finished' marker but does not exit, stop it after a grace time."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "ab") as lf:
        lf.write(f"\n===== {now()} :: {' '.join(cmd)}\n".encode("utf-8", "replace"))
        lf.flush()
        p = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=lf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
        seen_at = None
        while True:
            try:
                return p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
            if marker.exists():
                seen_at = seen_at or time.time()
                if time.time() - seen_at > grace_s:
                    log(f"trainer wrote {marker.name} but did not exit within {grace_s} s; stopping it")
                    p.kill()
                    p.wait()
                    return 0


def plan_epochs(t: dict, kept_positions: int) -> int:
    if not t.get("auto_epochs", False):
        return int(t["max_epochs"])
    want = kept_positions * float(t.get("passes", 4.0)) / int(t["epoch_size"])
    return int(min(int(t["max_epochs"]), max(int(t.get("min_epochs", 2)), math.ceil(want))))


def _serialize(cfg: dict, src: Path, dst: Path, log_path: Path) -> None:
    t = cfg["train"]
    tmp = dst.with_name("tmp_" + dst.name)
    tmp.unlink(missing_ok=True)
    cmd = [python_exe(cfg), "serialize.py", str(src), str(tmp)] + list(t.get("serialize_args", []))
    rc = run_logged(cmd, log_path, cwd=t["nnue_pytorch_dir"], env=child_env(cfg, t.get("env", {})))
    if rc != 0 or not tmp.exists() or tmp.stat().st_size == 0:
        raise RuntimeError(f"serialize {src.name} -> {dst.name} failed (exit {rc}):\n{tail_text(log_path, 2000)}")
    os.replace(tmp, dst)


def eval_loss(cfg: dict, model_pt: str, dataset: str, out_dir: Path) -> float | None:
    """Loss of a model on a hold-out set.

    The trainer's own validation needs a second loader stream, which crashes in the natively built
    Windows loader (access violation in create_sparse_batch_stream). So the hold-out set is read by a
    separate one-epoch run with a learning rate of 1e-12, which reports the loss without learning.
    """
    t = cfg["train"]
    out_dir.mkdir(parents=True, exist_ok=True)
    cached = out_dir / "loss.txt"
    if cached.exists():
        try:
            return float(cached.read_text().strip())
        except ValueError:
            pass
    size = int(t["validation_size"])
    cmd = [python_exe(cfg), "train.py", str(dataset), "--resume-from-model", str(model_pt),
           "--default-root-dir", str(out_dir), "--accelerator", str(t.get("accelerator", "auto")),
           "--batch-size", str(int(t["batch_size"])), "--num-workers", "1", "--threads", "2",
           "--epoch-size", str(size), "--max-epochs", "1", "--network-save-period", "0",
           "--save-last-network", "False", "--lr", "1e-12"] + [str(a) for a in t.get("extra_args", [])]
    marker = out_dir / "training_finished"
    marker.unlink(missing_ok=True)
    rc = _run_trainer(cmd, t["nnue_pytorch_dir"], child_env(cfg, t.get("env", {})), out_dir / "eval.log", marker)
    tl = _read_metrics(out_dir)["train_loss_epochs"]
    if rc != 0 or not tl:
        log(f"hold-out loss run failed (exit {rc}); continuing without it")
        return None
    cached.write_text(repr(tl[-1]))
    return tl[-1]


def train_nnue_pytorch(cfg: dict, datasets: list[str], val_set: str | None, init_model: str | None,
                       out_dir: Path, epochs: int, lr: float, tag: str = "cand", init_net: str | None = None) -> dict:
    t = cfg["train"]
    out_dir.mkdir(parents=True, exist_ok=True)
    marker = out_dir / "training_finished"
    tlog = out_dir / "train.log"
    t0 = time.time()
    if not marker.exists():
        cmd = [python_exe(cfg), "train.py", *datasets,
               "--default-root-dir", str(out_dir),
               "--accelerator", str(t.get("accelerator", "auto")),
               "--batch-size", str(int(t["batch_size"])),
               "--num-workers", str(int(t["num_workers"])),
               "--threads", str(int(t.get("threads", 2))),
               "--epoch-size", str(int(t["epoch_size"])),
               "--max-epochs", str(int(epochs)),
               "--network-save-period", "0",
               "--lr", repr(float(lr)), "--gamma", repr(float(t.get("gamma", 0.992))),
               "--max-time", str(t.get("max_time", "00:02:00:00"))]
        resume = _find_last_ckpt(out_dir)
        if resume is not None:
            log(f"train: resuming interrupted training from {resume}")
            cmd += ["--resume-from-checkpoint", str(resume)]
        elif init_model:
            cmd += ["--resume-from-model", str(init_model)]
        cmd += [str(a) for a in t.get("extra_args", [])]
        log(f"train: {epochs} epochs x {t['epoch_size']} positions, batch {t['batch_size']}, lr {lr}, "
            f"init {'checkpoint' if resume else (init_model or 'scratch')}, {len(datasets)} dataset file(s)")
        rc = _run_trainer(cmd, t["nnue_pytorch_dir"], child_env(cfg, t.get("env", {})), tlog, marker)
        if rc != 0 or not marker.exists():
            raise RuntimeError(f"training failed (exit {rc}); log tail:\n{tail_text(tlog, 3000)}")
    ckpt = _find_last_ckpt(out_dir)
    if ckpt is None:
        raise RuntimeError(f"training finished but no last.ckpt under {out_dir}")
    train_seconds = time.time() - t0
    net = out_dir / f"{tag}.nnue"
    model = out_dir / f"{tag}.pt"
    slog = out_dir / "serialize.log"
    if not net.exists():
        _serialize(cfg, ckpt, net, slog)
    if not model.exists():
        _serialize(cfg, ckpt, model, slog)
    m = _read_metrics(out_dir)
    tl = m["train_loss_epochs"]
    vl = []
    if val_set and int(t.get("validation_size", 0)) > 0:
        v = eval_loss(cfg, str(model), val_set, out_dir / "val_eval")
        if v is not None:
            vl = [v]
    samples = len(tl) * int(t["epoch_size"])
    return {
        "backend": "nnue_pytorch", "net": str(net), "model": str(model), "ckpt": str(ckpt),
        "epochs_run": len(tl), "epochs_planned": int(epochs), "samples": samples,
        "train_loss_first": tl[0] if tl else None, "train_loss_last": tl[-1] if tl else None,
        "val_loss_first": vl[0] if vl else None, "val_loss_last": vl[-1] if vl else None,
        "train_loss_epochs": [round(x, 6) for x in tl], "val_loss_epochs": [round(x, 6) for x in vl],
        "lr": lr, "last_lr": m["last_lr"], "init": init_model or "scratch",
        "seconds": round(train_seconds, 1),
        "pos_per_s": round(samples / train_seconds, 0) if train_seconds > 5 and samples else None,
        "net_bytes": net.stat().st_size,
    }


def train_command(cfg: dict, datasets: list[str], val_set: str | None, init_model: str | None,
                  out_dir: Path, epochs: int, lr: float, tag: str = "cand", init_net: str | None = None) -> dict:
    """Generic backend: your own trainer and exporter, described by command templates in the config.

    Placeholders: {datasets} {val} {init} {init_net} {out_dir} {epochs} {lr} {batch_size} {net} {model} {python}
    {init} is the model file of the current best net ("" if there is none), {init_net} its net file.
    The train command must leave a model file at {model}; the export command must write {net}.
    Lines 'LOSS <number>' and 'VAL <number>' in the output are recorded as training / hold-out loss.
    """
    t = cfg["train"]
    out_dir.mkdir(parents=True, exist_ok=True)
    net = out_dir / (tag + t.get("net_suffix", ".net"))
    model = out_dir / (tag + t.get("model_suffix", ".pt"))
    fields = {"datasets": " ".join(f'"{d}"' for d in datasets), "val": val_set or "", "init": init_model or "",
              "init_net": init_net or "", "out_dir": str(out_dir), "epochs": epochs, "lr": lr, "net": str(net), "model": str(model),
              "python": python_exe(cfg),
              "batch_size": int(t.get("batch_size", 4096))}   # [train] batch_size (2026-11-14), default as always
    tlog = out_dir / "train.log"
    t0 = time.time()
    # A hung training would stall the loop unseen (the watchdog sees only the process); killed, the stage fails and
    # is tried again. 180 min: the loop's trainings take about 25, the longest experiment 61 (2026-11-17).
    limit = float(t.get("max_minutes", 180)) * 60
    if not model.exists():
        rc = run_logged(t["train_cmd"].format(**fields), tlog, cwd=t.get("cwd") or None, env=child_env(cfg, t.get("env", {})),
                        timeout=limit)
        if rc != 0 or not model.exists():
            raise RuntimeError(f"train command failed (exit {rc}):\n{tail_text(tlog, 3000)}")
    if not net.exists():
        rc = run_logged(t["export_cmd"].format(**fields), tlog, cwd=t.get("cwd") or None, env=child_env(cfg, t.get("env", {})),
                        timeout=limit)
        if rc != 0 or not net.exists():
            raise RuntimeError(f"export command failed (exit {rc}):\n{tail_text(tlog, 3000)}")
    # A line 'VAL_MIX60 <number>' (the king-bucket trainer forge_train_v3.py, 2026-11-15) is the hold-out loss at the
    # 0.6 score/result mix of forge_train.py's VAL lines. When it is there it is the one recorded, so the hold-out
    # column of the round table stays one scale across both kinds of net; that trainer's own 'VAL' (its training
    # mix) is kept beside it.
    losses, vals, vals60 = [], [], []
    for line in tail_text(tlog, 200000).splitlines():
        for key, dst in (("LOSS ", losses), ("VAL ", vals), ("VAL_MIX60 ", vals60)):
            if line.startswith(key):
                try:
                    dst.append(float(line.split()[1]))
                except (ValueError, IndexError):
                    pass
    return {"backend": "command", "net": str(net), "model": str(model), "ckpt": None,
            "epochs_run": len(losses) or epochs, "epochs_planned": epochs, "samples": None,
            "train_loss_first": losses[0] if losses else None, "train_loss_last": losses[-1] if losses else None,
            "val_loss_first": None, "val_loss_last": (vals60 or vals)[-1] if (vals60 or vals) else None,
            "val_loss_trainer_mix": vals[-1] if (vals60 and vals) else None, "lr": lr,
            "init": init_model or init_net or "scratch",
            "seconds": round(time.time() - t0, 1), "pos_per_s": None, "net_bytes": net.stat().st_size}


def train(cfg: dict, *args, **kw) -> dict:
    backend = cfg["train"].get("backend", "nnue_pytorch")
    if backend == "nnue_pytorch":
        return train_nnue_pytorch(cfg, *args, **kw)
    if backend == "command":
        return train_command(cfg, *args, **kw)
    raise ValueError(f"unknown train.backend {backend!r}")
