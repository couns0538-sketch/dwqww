"""R11 one command: data -> holdout gate -> train -> export -> parity -> bench -> package.

Every stage skips work whose done marker exists, so the command can be rerun at any time (also after a crash or after
R11 was stopped by its PID); each stage logs one PASS/FAIL/WAIT line to <root>/logs/pipeline.log and the run ends with
exactly one "R11 PIPELINE PASS", "R11 PIPELINE WAIT" or "R11 PIPELINE FAIL" line.

Usage (python -I -B; Idle, I/O very low, memory low on 3 cores is set by the script itself):
  r11_pipeline.py --config <cfg.json> run --profile smoke|full [--skip-data] [--name <run name>]
  r11_pipeline.py --config <cfg.json> run --ckpt <file.ckpt> --l1 N [--name <net stem>]   (an existing checkpoint)
  r11_pipeline.py --config <cfg.json> run --net <file.nnue> --l1 N                         (an existing net)
  r11_pipeline.py --config <cfg.json> status
  r11_pipeline.py --config <cfg.json> selftest <new scratch dir>
Exit codes: 0 PASS, 1 FAIL, 3 WAIT (GPU busy with production, disk floor, data incomplete for a full run: rerun later).
Training needs the holdout proof on the real data (CR R2 M3): when HOLDOUT_TEST.json is missing or stale the
pipeline runs opus_r11/tests/test_r11_holdout_real.py itself first. Training yields to production (CR R2 H1).
Packages: smoke runs go to <root>/smoke_packages (not gate candidates); full runs, checkpoints and nets that pass the
check go to <root>/gate_ready. Nothing is ever queued: QA queues after Code Review.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "tests"))
import r11_common as C  # noqa: E402
import r11_check as K  # noqa: E402
import r11_data as D  # noqa: E402
import r11_package as P  # noqa: E402
import r11_train as T  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
EXIT_PASS, EXIT_FAIL, EXIT_WAIT = 0, 1, 3


def ensure_holdout_proof(cfg: dict, log: C.Log) -> None:
    """The train gate; when the record is missing or stale, run the real-data holdout test, then gate again."""
    try:
        T.holdout_gate(cfg, log)
        return
    except C.StageFailed as e:
        log.info(f"holdout gate: {e}; running the holdout test on the real data now")
    import test_r11_holdout_real as HT
    cfg_path = os.path.join(cfg["root"], "run", "pipeline_config.json")
    C.write_json(cfg_path, cfg)
    HT.FAILS.clear()
    rc = HT.main(["--config", cfg_path])
    if rc != 0:
        raise C.StageFailed(f"the holdout test FAILED on the real data ({HT.FAILS}); nothing is trained")
    T.holdout_gate(cfg, log)


def check_and_package(cfg: dict, net: str, l1: int, log: C.Log, gov: C.Governor, provenance: dict, kind: str) -> dict:
    stem = os.path.splitext(os.path.basename(net))[0]
    out = os.path.join(cfg["root"], "checks", stem)
    chk = K.run_check(cfg, net, out, l1, log.sub("check"), gov)
    if not chk["pass"]:
        return {"pass": False, "check": out}
    C.write_json(os.path.join(out, "provenance.json"), provenance)
    pk = P.package(cfg, out, log.sub("package"), provenance, kind=kind)
    return {"pass": bool(pk.get("packaged")), "check": out, "package": pk.get("dir")}


def cmd_run(cfg: dict, a, log: C.Log, gov: C.Governor) -> int:
    t0 = time.time()
    if a.net or a.ckpt:
        if not a.l1:
            raise C.StageFailed("--l1 is required with --net / --ckpt")
        build = K.build_engine(cfg, log.sub("check"))
        if a.ckpt:
            stem = a.name or os.path.splitext(os.path.basename(a.ckpt))[0].replace("=", "")
            net = os.path.join(cfg["root"], "nets", f"{stem}.nnue")
            K.export_net(cfg, a.ckpt, net, a.l1, log.sub("export"), gov, build)
            prov = {"source": "external checkpoint", "checkpoint": C.winpath(a.ckpt), "exported_by": "r11 export_net"}
        else:
            net = a.net
            prov = {"source": "external net", "net": C.winpath(net)}
        res = check_and_package(cfg, net, a.l1, log, gov, prov, "gate_ready")
    else:
        if not a.skip_data:
            man = D.run(cfg, log.sub("data"), gov)
            if a.profile == "full" and not man.get("complete"):
                log.wait("data: not every shard is converted (disk floor?); a full training run waits for complete data")
                print("R11 PIPELINE WAIT (data incomplete)")
                return EXIT_WAIT
        ensure_holdout_proof(cfg, log.sub("holdout"))
        tr = T.run_train(cfg, a.profile, log.sub("train"), gov, a.name)
        if not tr.get("finished"):
            why = "a production trainer holds the GPU" if tr.get("waiting_for_gpu") else "training not finished"
            log.wait(f"train: {why}; rerun to continue (resumes from the newest checkpoint)")
            print(f"R11 PIPELINE WAIT ({why})")
            return EXIT_WAIT
        pick = tr.get("best") or tr.get("last")
        if not pick:
            raise C.StageFailed("training finished without a checkpoint")
        prof = cfg["train"]["profiles"][a.profile]
        run_name = os.path.basename(tr["run_dir"].rstrip("/"))
        net = os.path.join(cfg["root"], "nets", f"{run_name}_e{pick['epoch']}_best.nnue")
        build = K.build_engine(cfg, log.sub("check"))
        K.export_net(cfg, pick["path"], net, prof["l1"], log.sub("export"), gov, build)
        hold = C.read_json(os.path.join(cfg["data"]["dir"], "HOLDOUT_TEST.json"), {})
        prov = {"source": "r11 training run", "run_dir": tr["run_dir"], "profile": a.profile, "checkpoint": pick["path"],
                "epoch": pick["epoch"], "val_loss": pick.get("val_loss"),
                "data_manifest_sha256": C.sha256_file(os.path.join(cfg["data"]["dir"], "MANIFEST.json")),
                "holdout_test": {k: hold.get(k) for k in ("at", "pass", "holdout", "leak_hits", "registry_sha256")}}
        kind = prof.get("package", "gate_ready" if a.profile == "full" else "smoke")
        cfg_check = cfg
        if prof.get("on_bench_depths"):  # a weak smoke net searches huge trees at d16-d22 (hours): bench it shallower
            cfg_check = json.loads(json.dumps(cfg))
            cfg_check["check"]["on_bench_depths"] = [int(d) for d in prof["on_bench_depths"]]
        res = check_and_package(cfg_check, net, prof["l1"], log, gov, prov, kind)
    secs = round(time.time() - t0)
    if res["pass"]:
        log.ok(f"pipeline: {res.get('package')} ({secs} s)")
        print(f"R11 PIPELINE PASS {res.get('package')}")
        return EXIT_PASS
    log.fail(f"pipeline: the check did not pass ({res['check']})")
    print(f"R11 PIPELINE FAIL (check {res['check']})")
    return EXIT_FAIL


def cmd_status(cfg: dict) -> int:
    d = cfg["data"]
    man = C.read_json(os.path.join(d["dir"], "MANIFEST.json"), {})
    hold = C.read_json(os.path.join(d["dir"], "HOLDOUT_TEST.json"), {})
    out = {"data": man.get("totals"), "data_complete": man.get("complete"),
           "holdout_test": {k: hold.get(k) for k in ("pass", "at", "leak_hits", "dedup_sample_rows")},
           "runs": {}, "gate_ready": [], "smoke_packages": []}
    rd = cfg["train"]["runs_dir"]
    if os.path.isdir(rd):
        for r in sorted(os.listdir(rd)):
            ix = T.read_index(os.path.join(rd, r))
            last = T.newest(ix)
            out["runs"][r] = {"best": (ix.get("best") or {}).get("val_loss"), "next_epoch": (last or {}).get("next_epoch")}
    for kind in ("gate_ready", "smoke_packages"):
        pd = os.path.join(cfg["root"], kind)
        if os.path.isdir(pd):
            out[kind] = [x for x in sorted(os.listdir(pd)) if os.path.isfile(os.path.join(pd, x, "PACKAGE_DONE"))]
    out["production_trainers"] = [h["pattern"] for h in C.production_processes(cfg["train"]["production_patterns"])]
    out["free"] = {"ram_gb": round(C.memory_gb()[0], 1), "d_gb": round(C.disk_free_gb(d["dir"]), 1)}
    print(json.dumps(out, indent=1))
    return EXIT_PASS


def cmd_selftest(cfg: dict, scratch: str, log: C.Log) -> int:
    if os.path.exists(scratch):
        print(f"{scratch} exists; give a new folder")
        return EXIT_FAIL
    os.makedirs(scratch)
    writer = D.resolve_writer(cfg, log)
    py = sys.executable
    tests = os.path.join(REPO, "opus_r11", "tests")
    rc1 = subprocess.call([py, "-I", "-B", os.path.join(tests, "test_r11_tools.py"), os.path.join(scratch, "tools")])
    rc2 = subprocess.call([py, "-I", "-B", os.path.join(tests, "test_r11_data.py"), writer, os.path.join(scratch, "data")])
    ok = rc1 == 0 and rc2 == 0
    print("R11 PIPELINE SELFTEST " + ("PASS" if ok else "FAIL") + f" (tools {rc1}, data {rc2})")
    return EXIT_PASS if ok else EXIT_FAIL


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--profile", help="a profile of train.profiles in the config (smoke, full, ...)")
    r.add_argument("--skip-data", action="store_true")
    r.add_argument("--name")
    r.add_argument("--ckpt")
    r.add_argument("--net")
    r.add_argument("--l1", type=int)
    sub.add_parser("status")
    s = sub.add_parser("selftest")
    s.add_argument("scratch")
    a = ap.parse_args(argv)
    cfg = C.read_json(a.config)
    C.set_idle_background(C.affinity_from_cfg(cfg))
    C.write_pid_file(cfg["root"], "pipeline")
    log = C.Log(os.path.join(cfg["root"], "logs", "pipeline.log"), "pipeline")
    gov = C.Governor(cfg["root"], C.limits_from(cfg), log)
    try:
        if a.cmd == "status":
            return cmd_status(cfg)
        if a.cmd == "selftest":
            return cmd_selftest(cfg, a.scratch, log)
        if not (a.profile or a.ckpt or a.net):
            raise C.StageFailed("run needs --profile, --ckpt or --net")
        if a.profile and a.profile not in cfg["train"]["profiles"]:
            raise C.StageFailed(f"unknown profile {a.profile}; the config has {sorted(cfg['train']['profiles'])}")
        return cmd_run(cfg, a, log, gov)
    except C.StageFailed as e:
        if str(e).startswith("disk:"):  # a resource condition, not a defect: rerun when space is back
            log.wait(str(e))
            print(f"R11 PIPELINE WAIT ({e})")
            return EXIT_WAIT
        log.fail(str(e))
        print(f"R11 PIPELINE FAIL ({e})")
        return EXIT_FAIL


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
