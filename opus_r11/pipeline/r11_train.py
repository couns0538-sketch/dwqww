"""R11 train stage: nnue-pytorch (R6 AMD Triton clone) on the R11 binpacks with auto-resume and checkpoint rotation.

The trainer runs in its own process through tools/nnue_pytorch_amd/r11/r11_train_entry.py (keeps the newest
`keep_last` checkpoints + the best by validation loss, exact resume, hold event Local\\Forge_R11_Hold, RAM floors,
production policy; there are no STOP/PAUSE files: stop R11 by its own PID, it resumes from the newest checkpoint).
This driver:
  - picks the run folder <train.runs_dir>/<run name>, the datasets (data/train_files.txt) and the validation files
    (data/holdout_files.txt);
  - waits before starting until free RAM >= limits floor + profile.need_ram_gb, and with gpu_policy "wait" until no
    production trainer is running (process check fails closed);
  - resumes from the newest checkpoint of the run's own index; a finished run is not started again;
  - handles the entry's exit codes: 0 finished/stopped, 75 RAM (wait, resume), 76 production appeared (wait until it
    ends, resume), 97 hard RAM floor (wait, resume), anything else FAIL; at most `max_restarts` restarts.
Profiles (config train.profiles): "smoke" (L1 256, batch 4096, 1 loader worker: the size the PC rules allow next to the
live trainer; gpu_policy share) and "full" (the owner's L1 1024 recipe; gpu_policy wait).
Usage: r11_train.py --config <cfg.json> --profile smoke|full [--name <run name>]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r11_common as C  # noqa: E402

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ENTRY = os.path.join(REPO, "tools", "nnue_pytorch_amd", "r11", "r11_train_entry.py")


def run_name(profile_name: str, prof: dict) -> str:
    return f"r11_{profile_name}_k32h3_l{prof['l1']}_bs{prof['batch_size']}_e{prof['max_epochs']}x{prof['epoch_size']}_s{prof.get('seed', 1)}"


def read_index(run_dir: str) -> dict:
    return C.read_json(os.path.join(run_dir, "checkpoints", "r11_ckpt_index.json"), {"entries": [], "best": None})


def newest(ix: dict) -> dict | None:
    live = [x for x in ix.get("entries", []) if os.path.isfile(x["path"])]
    return sorted(live, key=lambda x: (x["next_epoch"], x["step"], x["saved"]))[-1] if live else None


def trainer_cmd(cfg: dict, prof: dict, run_dir: str, resume: str | None) -> tuple[list[str], dict]:
    t = cfg["trainer"]
    d = cfg["data"]
    train_files = [ln.strip() for ln in open(os.path.join(d["dir"], "train_files.txt"), encoding="utf-8") if ln.strip()]
    hold_files = [ln.strip() for ln in open(os.path.join(d["dir"], "holdout_files.txt"), encoding="utf-8") if ln.strip()]
    if prof.get("max_train_files"):
        train_files = train_files[: int(prof["max_train_files"])]
    if not train_files or not hold_files:
        raise C.StageFailed("no train or holdout binpacks yet (run the data stage first)")
    policy = {"wait": "yield", "share": "share", "ignore": "ignore"}[prof.get("gpu_policy", "wait")]
    cmd = [t["python"], "-B", ENTRY, "--r11-clone", t["clone"], "--r11-run-dir", C.winpath(run_dir),
           "--r11-keep-last", str(prof.get("keep_last", 2)), "--r11-policy", policy,
           "--r11-share-duty", str(prof.get("share_duty", 1.0)),
           "--r11-min-free-ram-gb", str(cfg["limits"]["min_free_ram_gb"] + 1.0),
           "--r11-hard-ram-gb", str(cfg["limits"]["min_free_ram_gb"]),
           "--r11-patterns", ";".join(cfg["train"]["production_patterns"]),
           "--r11-affinity", hex(C.affinity_from_cfg(cfg)), "--"]
    cmd += train_files
    for h in hold_files:
        cmd += ["--validation-datasets", h]
    cmd += ["--validation-size", str(prof["validation_size"]), "--check-val-every-n-epoch", "1",
            "--default-root-dir", C.winpath(os.path.join(run_dir, "npt")),
            "--features", "K32H3^", "--l1", str(prof["l1"]), "--batch-size", str(prof["batch_size"]),
            "--num-workers", str(prof["num_workers"]), "--threads", str(prof["threads"]),
            "--epoch-size", str(prof["epoch_size"]), "--max-epochs", str(prof["max_epochs"]),
            "--network-save-period", "1", "--save-top-k", "-1", "--save-last-network", "False",
            "--async-checkpoint-save", "False", "--swa-start-epoch", "-1", "--seed", str(prof.get("seed", 1)),
            "--lr", str(prof["lr"]), "--start-lambda", str(prof["start_lambda"]), "--end-lambda", str(prof["end_lambda"]),
            "--no-filtered", "--no-wld-filtered", "--accelerator", prof.get("accelerator", "cuda")]
    if prof.get("gamma") is not None:
        cmd += ["--gamma", str(prof["gamma"])]
    if resume:
        cmd += ["--resume-from-checkpoint", C.winpath(resume)]
    env = dict(os.environ)
    tmp = os.path.join(cfg["root"], "tmp")
    os.makedirs(tmp, exist_ok=True)
    scripts = os.path.join(os.path.dirname(t["python"]))
    env.update({"PATH": scripts + os.pathsep + env.get("PATH", ""),  # Triton finds the ROCm SDK through the venv
                "NNUE_DATA_LOADER_LIB": t["loader_lib"], "PYTHONPATH": t["clone"], "TMP": tmp, "TEMP": tmp,
                "OMP_NUM_THREADS": str(prof["threads"]), "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
                "TORCHINDUCTOR_COMPILE_THREADS": "1",
                "TRITON_CACHE_DIR": os.path.join(cfg["root"], "cache", "triton"),
                "TORCHINDUCTOR_CACHE_DIR": os.path.join(cfg["root"], "cache", "inductor")})
    if not prof.get("compile", False):
        env["TORCHDYNAMO_DISABLE"] = "1"
    if prof.get("accelerator") == "cpu":
        env["NNUE_FT_BACKEND"] = "torch"
        env["CUDA_VISIBLE_DEVICES"] = ""
        env["HIP_VISIBLE_DEVICES"] = ""
    return cmd, env


def run_train(cfg: dict, profile_name: str, log: C.Log, gov: C.Governor, name: str | None = None) -> dict:
    prof = dict(cfg["train"]["profiles"][profile_name])
    run_dir = os.path.join(cfg["train"]["runs_dir"], name or run_name(profile_name, prof))
    C.assert_writable_path(run_dir)
    os.makedirs(run_dir, exist_ok=True)
    C.write_json(os.path.join(run_dir, "r11_profile.json"), {"profile": profile_name, **prof})
    patterns = cfg["train"]["production_patterns"]
    restarts = 0
    while True:
        ix = read_index(run_dir)
        last = newest(ix)
        if last and last["complete"] and last["next_epoch"] >= prof["max_epochs"]:
            log.ok(f"train {os.path.basename(run_dir)}: finished ({prof['max_epochs']} epochs); best "
                   f"{(ix.get('best') or {}).get('path')} val {(ix.get('best') or {}).get('val_loss')}")
            return {"run_dir": C.winpath(run_dir), "finished": True, "best": ix.get("best"), "last": last}
        # production policy
        if prof.get("gpu_policy", "wait") == "wait":
            t0 = time.time()
            while True:
                hits = C.production_processes(patterns)
                if not hits:
                    break
                if time.time() - t0 < 1 or int(time.time() - t0) % 600 < cfg["limits"]["poll_seconds"]:
                    log.wait(f"train {profile_name}: production trainer running ({hits[0]['pattern']}, pid "
                             f"{hits[0]['pid']}); full-size training waits (gpu_policy wait)")
                if prof.get("max_wait_s") is not None and time.time() - t0 > prof["max_wait_s"]:
                    return {"run_dir": C.winpath(run_dir), "finished": False, "waiting_for_gpu": True}
                time.sleep(cfg["limits"]["poll_seconds"])
        if not gov.wait_ok(f"train {profile_name}", need_ram_gb=prof["need_ram_gb"], disk_path=run_dir,
                           need_disk_gb=prof.get("need_disk_gb", 2.0)):
            return {"run_dir": C.winpath(run_dir), "finished": False, "stopped": True}
        resume = last["path"] if last else None
        cmd, env = trainer_cmd(cfg, prof, run_dir, resume)
        logf = os.path.join(run_dir, f"trainer_{time.strftime('%Y%m%d_%H%M%S')}.log")
        log.info(f"train {profile_name}: start ({'resume from ' + os.path.basename(resume) if resume else 'fresh'}), "
                 f"log {logf}")
        t0 = time.time()
        with open(logf, "w", encoding="utf-8", newline="\n") as lf:
            rc = subprocess.call(cmd, stdout=lf, stderr=subprocess.STDOUT, env=env, cwd=cfg["trainer"]["clone"])
        log.info(f"train {profile_name}: trainer exit {rc} after {time.time() - t0:.0f} s")
        if rc == 0:
            ix = read_index(run_dir)
            last = newest(ix)
            if last and last["complete"] and last["next_epoch"] >= prof["max_epochs"]:
                continue  # the loop top reports "finished"
            raise C.StageFailed(f"trainer exited 0 without finishing; see {logf}")
        if rc in (75, 76, 97):
            restarts += 1
            if restarts > int(prof.get("max_restarts", 20)):
                raise C.StageFailed(f"too many restarts ({restarts}); last exit {rc}; see {logf}")
            log.info(f"train {profile_name}: exit {rc} ({ {75: 'RAM floor', 76: 'production trainer appeared', 97: 'hard RAM floor'}[rc] }); "
                     "waiting, then resuming from the newest checkpoint")
            time.sleep(cfg["limits"]["poll_seconds"])
            continue
        tail = open(logf, encoding="utf-8", errors="replace").read()[-1500:]
        raise C.StageFailed(f"trainer failed with exit {rc}; see {logf}\n{tail}")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    ap.add_argument("--profile", required=True)
    ap.add_argument("--name")
    a = ap.parse_args(argv)
    cfg = C.read_json(a.config)
    C.set_idle_background(C.affinity_from_cfg(cfg))
    C.write_pid_file(cfg["root"], "train")
    log = C.Log(os.path.join(cfg["root"], "logs", "pipeline.log"), "train")
    gov = C.Governor(cfg["root"], C.Limits(**cfg.get("limits", {})), log)
    try:
        res = run_train(cfg, a.profile, log, gov, a.name)
        print(json.dumps(res, indent=1))
        return 0 if res.get("finished") else 3
    except C.StageFailed as e:
        log.fail(str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
