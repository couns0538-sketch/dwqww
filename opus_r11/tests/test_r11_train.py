"""R11 end-to-end self-test of the ONE command on synthetic data: data -> holdout proof -> train -> export -> parity ->
bench -> package, on the CPU (no GPU, nothing of production touched; ~5 GB RAM for a few minutes).

  1 yield (CR R2 H1): while a "production" marker process runs, the train stage does not start (waiting_for_gpu);
  2 run 1: r11_pipeline run --profile cpu_test (2 epochs) -> PASS: data converted, holdout test PASS, K32H3^ L1 64
    trained by the unchanged R6 trainer through the R11 entry, the best checkpoint exported (loads in the HalfKA tool),
    fens_12k parity exact, OFF identity, ON bench, WAC, smoke package (not a gate candidate);
  3 run 2: the same run with max_epochs 4 resumes at epoch 2 (exact resume), trains 2 more epochs, rotation keeps the
    newest 2 checkpoints + the best one (logged in rotation.jsonl), the pipeline PASSes again.
It reuses the synthetic positions of test_r11_data.py. Includes the real production patterns: if a production trainer
runs, the test SKIPS (exit 0, "SKIPPED") instead of training next to it.
Usage: test_r11_train.py <scratch dir (new)> [--gpu]   -> prints "R11 TRAIN E2E SELFTEST PASS"
  --gpu: the same run on the AMD GPU through the R6 Triton/ROCm trainer (only when no production trainer runs: the
         pipeline yields otherwise; smoke size: L1 64, batch 1024, 1 loader worker).
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "opus_r11", "pipeline"))
sys.path.insert(0, HERE)
import r11_common as C  # noqa: E402
import r11_pipeline as PL  # noqa: E402
import r11_train as T  # noqa: E402
import test_r11_data as TD  # noqa: E402

FAILS: list[str] = []


def check(cond: bool, what: str) -> None:
    print(("ok   " if cond else "FAIL ") + what, flush=True)
    if not cond:
        FAILS.append(what)


def main() -> int:
    scratch = sys.argv[1]
    if os.path.exists(scratch):
        print(f"{scratch} exists; give a new folder")
        return 2
    real = C.read_json(os.path.join(REPO, "opus_r11", "pipeline", "r11_config.json"))
    if C.production_processes(real["train"]["production_patterns"]):
        print("R11 TRAIN E2E SELFTEST SKIPPED (a production trainer is running; training yields)")
        return 0
    src = os.path.join(scratch, "src")
    for name, n in (("h_001", 3000), ("t_001", 6000), ("t_002", 6000), ("t_003", 6000)):
        b, s, m = TD.random_rows(n)
        h = TD.RNG.integers(-1500, 1500, n).astype(np.int16)
        TD.write_fpos(os.path.join(src, "s", f"{name}.pos"), b, s, m, h)
    marker = f"R11E2EPROD{os.getpid()}"
    cfg = copy.deepcopy(real)
    cfg["root"] = os.path.join(scratch, "root")
    cfg["limits"].update({"max_cpu_percent": 100.0, "poll_seconds": 2.0, "disk_floor_gb": {"C:": 5.0, "D:": 40.0}})
    cfg["data"] = {
        "dir": os.path.join(cfg["root"], "data"), "writer_exe": "auto",
        "sources": [{"name": "s", "pos_glob": os.path.join(src, "s", "*_[0-9][0-9][0-9].pos"),
                     "ready": {"info_suffix": ".info", "min_age_s": 0},
                     "hce": {"dir": os.path.join(src, "s"), "strip": ".pos", "suffix": ".hce"}}],
        "holdout": ["s:h_001"], "dedup_mem_gb": 0.5, "chunk_rows": 2000, "ply": 40, "verify": "all",
        "keys_cache": False, "disk_margin_gb": 0.0, "convert_order": ["holdout", "s"]}
    cfg["train"]["runs_dir"] = os.path.join(cfg["root"], "runs")
    cfg["train"]["production_patterns"] = real["train"]["production_patterns"] + [marker]
    accel = "cuda" if "--gpu" in sys.argv[2:] else "cpu"
    cfg["train"]["profiles"] = {"cpu_test": {
        "accelerator": accel, "gpu_policy": "yield", "l1": 64, "batch_size": 1024, "num_workers": 1, "threads": 1,
        "epoch_size": 20480, "max_epochs": 2, "validation_size": 4096, "lr": 0.000875, "start_lambda": 1.0,
        "end_lambda": 1.0, "seed": 1, "need_ram_gb": 6.0, "need_disk_gb": 0.5, "compile": False, "keep_last": 2,
        "max_restarts": 3}}
    cfg_path = os.path.join(scratch, "cfg.json")
    C.write_json(cfg_path, cfg)

    # 1 the gate: no passing holdout record -> the train stage refuses to start (CR R2 M3)
    log = C.Log(os.path.join(cfg["root"], "logs", "pipeline.log"), "train")
    gov = C.Governor(cfg["root"], C.limits_from(cfg), log)
    try:
        T.run_train(cfg, "cpu_test", log, gov, "gate_probe")
        check(False, "the gate must refuse training without a passing holdout test")
    except C.StageFailed as e:
        check("holdout" in str(e), "train stage refuses to start without a passing holdout test (CR R2 M3)")

    # 2 run 1 through the ONE command (2 epochs)
    rc = PL.main(["--config", cfg_path, "run", "--profile", "cpu_test", "--name", "e2e"])
    check(rc == 0, f"r11_pipeline run --profile cpu_test (2 epochs) -> exit {rc}")
    hold = C.read_json(os.path.join(cfg["data"]["dir"], "HOLDOUT_TEST.json"), {})
    check(bool(hold.get("pass")) and hold.get("leak_hits") == 0, "the pipeline ran the holdout test itself: PASS, 0 leak hits")
    run_dir = os.path.join(cfg["train"]["runs_dir"], "e2e")
    ix = T.read_index(run_dir)
    last = T.newest(ix)
    check(bool(last) and last["next_epoch"] == 2 and last["complete"], f"run 1 finished 2 epochs (newest {last})")
    smoke = os.path.join(cfg["root"], "smoke_packages")
    pk1 = sorted(os.listdir(smoke)) if os.path.isdir(smoke) else []
    check(len(pk1) == 1 and os.path.isfile(os.path.join(smoke, pk1[0], "PACKAGE_DONE")) and
          os.path.isfile(os.path.join(smoke, pk1[0], "GATE_EXE.txt")), f"smoke package written: {pk1}")
    if pk1:
        chk = C.read_json(os.path.join(smoke, pk1[0], "check.json"))
        check(chk["parity"]["exact"] == chk["parity"]["fens_count"] == 12000,
              f"trained net parity {chk['parity']['exact']}/{chk['parity']['fens_count']} exact vs nnue-pytorch")
        check(chk["off"]["ok"] and chk["on"]["ok"], "OFF identity and ON bench pass for the trained net")
        readme = open(os.path.join(smoke, pk1[0], "README.md"), encoding="utf-8").read()
        check("NOT a gate candidate" in readme, "the smoke package says it is not a gate candidate")
    gate_dir = os.path.join(cfg["root"], "gate_ready")
    check(not os.path.isdir(gate_dir) or not os.listdir(gate_dir), "no gate-ready folder for a smoke run")

    # 2b yield (CR R2 H1): while a "production" marker process runs, the train stage starts nothing
    dummy = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(20)", marker])
    try:
        time.sleep(1.0)
        cfg_y = copy.deepcopy(cfg)
        cfg_y["train"]["profiles"]["cpu_test"]["max_wait_s"] = 4
        res = T.run_train(cfg_y, "cpu_test", log, gov, "yield_probe")
    finally:
        dummy.wait(timeout=60)
    probe = os.path.join(cfg["train"]["runs_dir"], "yield_probe")
    started = [x for x in os.listdir(probe) if x.startswith("trainer_")] if os.path.isdir(probe) else []
    check(res.get("waiting_for_gpu") is True and not started,
          f"a running production trainer -> the train stage yields and starts no trainer ({res}, logs {started})")

    # 3 run 2: 4 epochs -> exact resume at epoch 2, rotation newest 2 + best
    cfg2 = copy.deepcopy(cfg)
    cfg2["train"]["profiles"]["cpu_test"]["max_epochs"] = 4
    cfg2_path = os.path.join(scratch, "cfg4.json")
    C.write_json(cfg2_path, cfg2)
    rc = PL.main(["--config", cfg2_path, "run", "--profile", "cpu_test", "--name", "e2e", "--skip-data"])
    check(rc == 0, f"rerun with max_epochs 4 -> exit {rc}")
    events = [json.loads(x) for x in open(os.path.join(run_dir, "r11_events.jsonl"), encoding="utf-8")]
    resumed = [e for e in events if e["event"] == "resumed"]
    check(bool(resumed) and resumed[-1]["epoch"] == 2, f"run 2 resumed at epoch 2 (exact resume): {resumed[-1:]}")
    ix = T.read_index(run_dir)
    live = sorted(os.path.basename(x["path"]) for x in ix["entries"] if os.path.isfile(x["path"]))
    newest2 = sorted(ix["entries"], key=lambda x: (x["next_epoch"], x["step"]))[-2:]
    best = ix.get("best") or {}
    expect = sorted({os.path.basename(x["path"]) for x in newest2} | ({os.path.basename(best["path"])} if best else set()))
    check(live == expect and 2 <= len(live) <= 3, f"rotation keeps the newest 2 + the best: {live}")
    rot = os.path.join(run_dir, "checkpoints", "rotation.jsonl")
    check(os.path.isfile(rot) and sum(1 for _ in open(rot, encoding="utf-8")) >= 1, "removed checkpoints are logged in rotation.jsonl")
    files = [x for x in os.listdir(os.path.join(run_dir, "checkpoints")) if x.endswith(".ckpt")]
    check(sorted(files) == live, f"no other checkpoint file on disk: {sorted(files)}")

    print(f"\n{len(FAILS)} failed checks")
    print("R11 TRAIN E2E SELFTEST " + ("PASS" if not FAILS else "FAIL"))
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())
