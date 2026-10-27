"""S18 remaining four arms (t200/t300/t400/t500) as CPU smoke on the PC.

Windows port of the design of Sol's v4 S18 controller (forge_sol_S18_train_selected_v4_20261027.py,
sha256 643e71ea...): same filter argv, same f006 trainer recipe (2 epochs), same separate postscore of
the preselected final epoch-2 checkpoint on all 50,000 holdout rows. The Linux-only parts (taskset,
RLIMIT_AS, /proc RSS, subreaper, memfd Torch load) are replaced by a Windows guard: BelowNormal priority,
one Torch thread, a free-RAM floor (stop below 6 GiB available), a per-arm memory cap, a disk floor, a
time limit and a supervisor-log check. Sol's trainer, filter and tools are used unchanged; the trainer
runs as a byte-identical copy named opus_nnue_smoke_s18_v3b.py (the PC's NNUE supervisor adopts any
process whose command line matches train_resid*.py).

Run with the read-only NNUE venv python, one mode at a time:
  --stage             copy the pinned inputs to F:\\opus_scratch\\sol_s18\\s18_inputs and pin-check them
  --data TAG          regenerate the five arms' shards with Sol's unchanged v2 filter (LF launcher) into
                      s18_data_TAG and compare them with Sol's archived shards and the arms index
  --train TAG         train t200..t500 from s18_data_<--data-tag> into s18_r4_TAG and postscore each arm
  --compare A B       compare two train runs, t200 with Sol's frozen v3 reference, write the loss table
The controller never imports Torch; training and postscore run in a --child process.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import re
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path

LA = Path(r"D:\grok-pc-data\dwqww\.claude\worktrees\b\pkg\forge_LOCK_AL1_s198_FULL_20261026_1039")
SRC_TRAINER = LA / "5_nnue/trainers/cpu_smoke/train_resid_v3b.py"
SRC_ADAM = LA / "5_nnue/trainers/cpu_smoke/qa_adam_dml.py"
SRC_SAMPLE = LA / "5_nnue/sample_data/data32_sample/data32_sample_50k"
VENV_PY = Path(r"C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe")
ROOT = Path(r"F:\opus_scratch\sol_s18")
SOL = ROOT / "sol_src"
INPUTS = ROOT / "s18_inputs"
SAMPLE = INPUTS / "data32_sample_50k"
TRAINER = INPUTS / "trainer" / "opus_nnue_smoke_s18_v3b.py"
ADAM = INPUTS / "trainer" / "qa_adam_dml.py"
FILTER = SOL / "instrument" / "forge_sol_datafilter_v2_20261026.py"
FILTER_BASE = SOL / "instrument" / "forge_sol_datafilter_20261025.py"
INDEX = SOL / "forge_sol_S18_training_arms_index_20261026.json"
POSTSCORE_PREREG = SOL / "pinned" / "forge_sol_S18_postscore_preregistration_20261026.json"
T200_REFERENCE = SOL / "prereg" / "forge_sol_S18_v4_t200_reference_binding_20261027.json"
LAUNCHER = Path(__file__).resolve().with_name("opus_s18_lf_launcher.py")
SUPERVISOR_LOG = Path(r"F:\forge_nnue_train\supervisor.log")
SOL_ARM_DIRS = {
    "none": SOL / "orig_ckpt/x/reused_S16/none",
    "t200": SOL / "orig_ckpt/x/data_cases/t200_first/sealed",
    "t300": SOL / "orig_ckpt/x/reused_S16/t300_first",
    "t400": SOL / "orig_ckpt/x/data_cases/t400_first/sealed",
    "t500": SOL / "orig_ckpt/x/data_cases/t500_first/sealed",
}
ARMS = {"none": None, "t200": 200, "t300": 300, "t400": 400, "t500": 500}
TRAIN_ARMS = ["t200", "t300", "t400", "t500"]
SHARDS = ["t00000", "t01000", "t02000", "t03000"]
FILTER_SEED = 20261025

PINS = {
    SRC_TRAINER: "5cebba4d44133630e247d9ab4c0085fa6301dde8db1dfe1389452ac19d92313f",
    SRC_ADAM: "799faa89bc7b8dbd8c9a8747dd6658085eb0a69b84800af191db5ca7fd660cba",
    FILTER: "5dd0c009566bc5a8c8e06300a8541c5d130d458ca75266a432d1477d1d156332",
    FILTER_BASE: "6ccf78c864c44155cea22044fe05d0584bec5241acdc5ebb2b71e23886007ab3",
    INDEX: "fb5d2575d2d9aabaaff6143f9137e786af5351785a558b6ef46e53ba08944ff0",
    POSTSCORE_PREREG: "aa8fed66b82399b62f77cf792f25d2582771aefabed39ab08c0e5e63ab771d7e",
    T200_REFERENCE: "311d97f70a5b3f162b88c77a12f7aba8513991df15f6af3a3bb76d47833ad0f2",
}
SAMPLE_PINS = {
    "h000.pos": "92c40ae25c3b650db9f5db235786133afed3e9a8f6691e7860dff6bdc5aa11b3",
    "h000.hce": "212e51e6c108f3ff6b879b0f247277925f9483102e34230b5024e5fb7ef2cc44",
    "t00000.pos": "7a8727fa19f857f5b3ac1c79219b06ca1aefdb971f72167b775d1a1dfa2794c8",
    "t00000.hce": "b5dd1729246a630d8e079882913311858b7ad063d026245b5b60a8141097f637",
    "t01000.pos": "0252d5f924c67aea939d55229ebd514c3fb6c767619f6a27075993b89f846b9a",
    "t01000.hce": "fcb63b0ce7e68f05445bb6376e0a6d61abbc8ee12979ba533872524d194270ea",
    "t02000.pos": "9630ea73c53159375e7e821c01b0a39e4d598d4acebb29d384ed4cf70cd9e693",
    "t02000.hce": "78e4c77c5efb34029d85aaa1ccc43b877079e76c47507aff6416d3a7e384ba55",
    "t03000.pos": "7753665ec40e98a4b58db3a61ea74116245aaa4ced1355345bf460041306fe98",
    "t03000.hce": "77a6a237a771f275c2def1fca2c5d50f4854d78a8f560c1e2dc5f6c0edc79f8d",
}
HOLDOUT_MD5 = {"h000.pos": "b263af9969f8ace979e25db061eb37ef", "h000.hce": "f248959bc791424407a37af5ac60752a"}

# Guard limits (QA: small, RAM-capped, stop if free RAM < 6 GB).
FREE_RAM_FLOOR = 6 * 1024**3          # available physical memory, checked before and during each arm
MEMORY_CAP = 3 * 1024**3              # child tree: max(working set, private bytes) summed over the tree
DISK_FLOOR = 6_979_321_856 + 64 * 1024**2   # Sol's floor + his 64 MiB launch allowance, measured on F:
HARD_SECONDS = 1800                   # per arm (Sol: 300 work / 360 hard on an idle Linux core)
START_HEADROOM = 1024**3              # an arm starts only with >= 7 GiB available (floor + 1 GiB) ...
START_WAIT_SECONDS = 1800             # ... waiting up to 30 min for it; otherwise the run stops (NOT_STARTED_GUARD)
POLL_SECONDS = 0.25
SUPERVISOR_CHECK_SECONDS = 30.0


def fingerprint(path: Path) -> dict:
    sha, md5, size = hashlib.sha256(), hashlib.md5(), 0
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            sha.update(block); md5.update(block); size += len(block)
    return {"sha256": sha.hexdigest(), "md5": md5.hexdigest(), "bytes": size}


def sha256(path: Path) -> str:
    return fingerprint(path)["sha256"]


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def make_read_only(path: Path) -> None:
    os.chmod(path, stat.S_IREAD)


def below_normal_self() -> None:
    """Run the controller itself at BelowNormal priority (the PC rule)."""
    import ctypes
    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x00004000)


def free_ram() -> int:
    import psutil
    return int(psutil.virtual_memory().available)


def free_disk() -> int:
    return shutil.disk_usage(ROOT).free


def verify_pins() -> dict:
    values = {}
    for path, expected in PINS.items():
        got = sha256(path)
        values[str(path)] = got
        if got != expected:
            raise ValueError(f"pinned input changed: {path} {got} != {expected}")
    return values


def verify_staged() -> dict:
    found = {}
    for name, expected in SAMPLE_PINS.items():
        meta = fingerprint(SAMPLE / name)
        if meta["sha256"] != expected:
            raise ValueError(f"staged sample file differs: {name}")
        if name in HOLDOUT_MD5 and meta["md5"] != HOLDOUT_MD5[name]:
            raise ValueError(f"staged holdout md5 differs: {name}")
        found[name] = meta
    for copy, source in ((TRAINER, SRC_TRAINER), (ADAM, SRC_ADAM)):
        meta = fingerprint(copy)
        if meta["sha256"] != PINS[source]:
            raise ValueError(f"staged copy differs from its pin: {copy.name}")
        found[copy.name] = meta
    return found


# --------------------------------------------------------------------------------------------------- stage
def stage() -> int:
    verify_pins()
    for name, expected in SAMPLE_PINS.items():
        if sha256(SRC_SAMPLE / name) != expected:
            raise ValueError(f"lock-archive sample file differs from Sol's pin: {name}")
    if INPUTS.exists():
        print("inputs already staged; verifying only")
    else:
        SAMPLE.mkdir(parents=True)
        TRAINER.parent.mkdir(parents=True)
        for name in SAMPLE_PINS:
            shutil.copyfile(SRC_SAMPLE / name, SAMPLE / name)
            make_read_only(SAMPLE / name)
        shutil.copyfile(SRC_TRAINER, TRAINER); make_read_only(TRAINER)
        shutil.copyfile(SRC_ADAM, ADAM); make_read_only(ADAM)
    found = verify_staged()
    write_json(ROOT / "s18_inputs_receipt.json", {"status": "PASS_STAGED_INPUTS", "files": found,
                                                  "pins": verify_pins(), "trainer_copy_of": str(SRC_TRAINER)})
    for name, meta in sorted(found.items()):
        print(f"{name:32s} {meta['bytes']:>9d} {meta['sha256']}")
    print("RESULT PASS_STAGED_INPUTS files=%d" % len(found))
    return 0


# ---------------------------------------------------------------------------------------------------- data
def filter_argv(arm: str, armdir: Path) -> list[str]:
    argv = [str(VENV_PY), "-B", str(LAUNCHER), str(FILTER),
            "--train", *[str(SAMPLE / f"{s}.pos") for s in SHARDS],
            "--holdout-pos", str(SAMPLE / "h000.pos"), "--hce-dir", str(SAMPLE),
            "--out", str(armdir / "sealed"), "--work-dir", str(armdir / "scratch"),
            "--seed", str(FILTER_SEED), "--diagnostic-mode"]
    if ARMS[arm] is not None:
        argv += ["--disagreement-threshold", str(ARMS[arm])]
    return argv


def child_env(extra: dict | None = None) -> dict:
    env = os.environ.copy()
    for key in ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP"):
        env.pop(key, None)
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1",
               OPENBLAS_NUM_THREADS="1", NUMEXPR_NUM_THREADS="1", CUDA_VISIBLE_DEVICES="")
    env.update(extra or {})
    return env


SUMMARY_NAME = "forge_sol_datafilter_summary_20261026.json"
MANIFEST_NAME = "forge_sol_datafilter_manifest_20261026.md5"


def posix_order_manifest(text: str) -> str:
    """The manifest as Sol's Linux run wrote it: lines sorted by file name, case-sensitively.
    Sol's filter sorts with sorted(out.iterdir()); WindowsPath sorts case-insensitively, so on the PC
    'forge_sol_datafilter_summary...' comes before 'forge_sol_S16_removals...' (same lines, other order)."""
    return "".join(sorted(text.splitlines(keepends=True), key=lambda line: line.split("  ", 1)[1]))


def check_data(tag: str) -> int:
    """Check one data run against Sol's archived shards and the arms index (read-only)."""
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    out = ROOT / f"s18_data_{tag}"
    result = {"status": "FAIL_S18_DATA_CHECK", "tag": tag, "arms": {}}
    for arm in ARMS:
        sealed = out / arm / "sealed"
        produced = {p.name: fingerprint(p) for p in sorted(sealed.iterdir()) if p.is_file()}
        reference = {p.name: fingerprint(p) for p in sorted(SOL_ARM_DIRS[arm].iterdir()) if p.is_file()}
        mismatched = sorted(n for n in set(produced) | set(reference)
                            if produced.get(n, {}).get("sha256") != reference.get(n, {}).get("sha256"))
        manifest = (sealed / MANIFEST_NAME).read_bytes().decode("utf-8")
        sol_manifest = (SOL_ARM_DIRS[arm] / MANIFEST_NAME).read_bytes().decode("utf-8")
        listed = dict(line.split("  ", 1)[::-1] for line in manifest.splitlines())
        summary = json.loads((sealed / SUMMARY_NAME).read_text(encoding="utf-8"))
        entry = index["arms"][arm]
        checks = {
            "shards_summary_removals_byte_identical_to_sol": [n for n in mismatched if n != MANIFEST_NAME] == [],
            "manifest_same_lines_as_sol": sorted(manifest.splitlines()) == sorted(sol_manifest.splitlines()),
            "manifest_posix_order_sha256_matches_index":
                hashlib.sha256(posix_order_manifest(manifest).encode("utf-8")).hexdigest() == entry["output_manifest_sha256"],
            "manifest_md5_lines_match_files": listed == {n: m["md5"] for n, m in produced.items() if n != MANIFEST_NAME},
            "summary_sha256_matches_index": produced[SUMMARY_NAME]["sha256"] == entry["summary_sha256"],
            "kept_matches_index": summary["totals"]["kept"] == entry["kept"],
            "dropped_matches_index": summary["totals"]["dropped"] == entry["dropped"],
            "holdout_overlap_0": summary["supplied_holdout_overlap"] == 0,
            "holdout_md5": summary["input_md5"]["h000.pos"] == HOLDOUT_MD5["h000.pos"],
        }
        result["arms"][arm] = {"kept": summary["totals"]["kept"], "dropped": summary["totals"]["dropped"],
                               "produced": produced, "mismatched_vs_sol": mismatched,
                               "manifest_byte_identical_to_sol": manifest == sol_manifest, "checks": checks,
                               "status": "PASS" if all(checks.values()) else "FAIL"}
        print(f"{arm}: kept {summary['totals']['kept']:>6d} dropped {summary['totals']['dropped']:>6d} "
              f"files differing from Sol {mismatched} -> {result['arms'][arm]['status']}", flush=True)
    if all(a["status"] == "PASS" for a in result["arms"].values()):
        result["status"] = "PASS_S18_DATA_MATCHES_SOL"
    write_json(out / "s18_data_check.json", result)
    print(f"RESULT {result['status']}")
    return 0 if result["status"].startswith("PASS") else 1


def data(tag: str) -> int:
    verify_pins(); verify_staged()
    out = ROOT / f"s18_data_{tag}"
    out.mkdir()
    result = {"status": "FAIL_S18_DATA", "tag": tag, "arms": {}, "filter_sha256": PINS[FILTER]}
    try:
        for arm in ARMS:
            armdir = out / arm
            (armdir / "scratch").mkdir(parents=True)
            argv = filter_argv(arm, armdir)
            start = time.monotonic()
            with open(armdir / "filter.stdout", "xb") as so, open(armdir / "filter.stderr", "xb") as se:
                proc = subprocess.run(argv, stdout=so, stderr=se, env=child_env(),
                                      creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS, timeout=HARD_SECONDS)
            elapsed = time.monotonic() - start
            result["arms"][arm] = {"argv": argv, "returncode": proc.returncode, "elapsed_seconds": round(elapsed, 2)}
            print(f"{arm}: rc {proc.returncode} {elapsed:6.1f}s", flush=True)
            if proc.returncode != 0:
                raise ValueError(f"filter failed for {arm}")
        result["status"] = "FILTER_RUNS_COMPLETE"
    except BaseException as error:  # keep the receipt on any failure
        result["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        write_json(out / "s18_data_runs.json", result)
    return check_data(tag)


# ----------------------------------------------------------------------------------------------- histograms
DESCRIBE = SOL / "orig_ckpt/x/source_and_history/forge_sol_S18_describe_20261026.py"
EVAL_HPP = LA / "1_source/forge_AL1_s198_src/include/forge/eval.hpp"
SOL_HIST = SOL / "hist/completed/validation/forge_sol_pack31_20261025/forge_sol_S18_completed_histograms_20261026/runtime"
PINS[DESCRIBE] = "5ff1e6d7fa15f86404d0ab71cdb24bebc28d1cede651d27d55cc853dd960c5ef"
PINS[EVAL_HPP] = "e6cb2b620f5c7fd87cef7a680aea04c4ba756f106b78d5a8fa7ab3cdd5d0cc35"


def hist(tag: str) -> int:
    """Sol's describe tool, unchanged (LF launcher), on one data run; compared with the arms index and with
    Sol's completed histograms. The tool records the sha256 of the arm's manifest file, whose line order
    differs on Windows (see posix_order_manifest); that one field is normalised to the POSIX-order manifest
    before hashing, and every other byte must match."""
    verify_pins(); verify_staged()
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    out = ROOT / f"s18_hist_{tag}"
    out.mkdir()
    result = {"status": "FAIL_S18_HISTOGRAMS", "tag": tag, "describe_sha256": PINS[DESCRIBE], "arms": {}}
    try:
        for arm in ARMS:
            sealed = ROOT / f"s18_data_{tag}" / arm / "sealed"
            (out / arm).mkdir()
            target = out / arm / f"forge_sol_S18_{arm}_histograms_20261026.json"
            argv = [str(VENV_PY), "-B", str(LAUNCHER), str(DESCRIBE), "--arm", str(sealed), "--sample", str(SAMPLE),
                    "--phase-header", str(EVAL_HPP), "--out", str(target)]
            with open(out / arm / "describe.stdout", "xb") as so, open(out / arm / "describe.stderr", "xb") as se:
                proc = subprocess.run(argv, stdout=so, stderr=se, env=child_env(),
                                      creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS, timeout=HARD_SECONDS)
            produced = json.loads(target.read_text(encoding="utf-8"))
            manifest_text = (sealed / MANIFEST_NAME).read_bytes().decode("utf-8")
            recorded = produced["source_output_manifest"]["sha256"]
            normalised = json.loads(json.dumps(produced))
            normalised["source_output_manifest"]["sha256"] = hashlib.sha256(
                posix_order_manifest(manifest_text).encode("utf-8")).hexdigest()
            normalised_bytes = (json.dumps(normalised, indent=2, sort_keys=True) + "\n").encode("utf-8")
            sol_file = SOL_HIST / arm / f"forge_sol_S18_{arm}_histograms_20261026.json"
            checks = {
                "returncode_0": proc.returncode == 0,
                "output_is_lf": b"\r\n" not in target.read_bytes(),
                "recorded_manifest_sha_is_this_runs_file": recorded == sha256(sealed / MANIFEST_NAME),
                "normalised_sha256_matches_index": hashlib.sha256(normalised_bytes).hexdigest() == index["arms"][arm]["histogram_sha256"],
                "normalised_bytes_equal_sol_completed": normalised_bytes == sol_file.read_bytes(),
                "kept_rows_match_index": produced["kept"]["rows"] == index["arms"][arm]["kept"],
                "all_histograms_reconcile": produced.get("all_histograms_reconcile") is True,
            }
            result["arms"][arm] = {"argv": argv, "returncode": proc.returncode, "output_sha256": sha256(target),
                                   "normalised_sha256": hashlib.sha256(normalised_bytes).hexdigest(), "checks": checks,
                                   "status": "PASS" if all(checks.values()) else "FAIL"}
            print(f"{arm}: rc {proc.returncode} kept {produced['kept']['rows']} -> {result['arms'][arm]['status']} "
                  f"{[k for k, v in checks.items() if not v]}", flush=True)
        if all(a["status"] == "PASS" for a in result["arms"].values()):
            result["status"] = "PASS_S18_HISTOGRAMS_MATCH_SOL"
    finally:
        write_json(out / "s18_hist_result.json", result)
        print(f"RESULT {result['status']}")
    return 0 if result["status"].startswith("PASS") else 1


# --------------------------------------------------------------------------------------------------- train
def trainer_argv(view: Path, train_files: list[Path], run: Path) -> list[str]:
    """Sol's v4 trainer_argv, unchanged: the f006 recipe with 2 epochs."""
    return ["--train", *[str(p) for p in sorted(train_files)], "--holdout", str(view / "h000.pos"), "--hce-dir", str(view),
            "--device", "cpu", "--shape", "256", "--residual", "--epochs", "2", "--batch-size", "8192", "--lr", "0.000707",
            "--warmup-steps", "300", "--blend-end", "0.6", "--seed", "25", "--final-full-val", "--run-dir", str(run)]


def final_checkpoint(run: Path, rows: int) -> Path:
    return run / ("epoch002-step" + format(2 * (rows // 8192), "09d") + ".pt")


def native_final_metric(text: str) -> dict:
    """Sol's v4 native_final_metric: the trainer's own FINAL FULL HOLDOUT line (49,152 rows)."""
    lines = [line for line in text.splitlines() if line.startswith("FINAL FULL HOLDOUT n=")]
    if len(lines) != 1:
        raise ValueError("exactly one native FINAL FULL HOLDOUT line required")
    match = re.fullmatch(r"FINAL FULL HOLDOUT n=([0-9,]+): net mse_teacher=(\S+) mse_b0\.6=(\S+) mse_b0\.8=(\S+) \| HCE (\S+)/(\S+)/b0\.8 (\S+)", lines[0])
    if match is None or int(match[1].replace(",", "")) != 49152:
        raise ValueError("native metric must report 49,152 rows")
    values = [float(match[i]) for i in range(2, 8)]
    return {"line": lines[0], "net_MSE": dict(zip(("1.0", "0.6", "0.8"), values[:3])),
            "HCE_baseline_MSE": dict(zip(("1.0", "0.6", "0.8"), values[3:]))}


def supervisor_adoptions_since(start_wall: float) -> list[str]:
    """Read-only tail of the NNUE supervisor log: 'adopted running job' lines written after start_wall."""
    if not SUPERVISOR_LOG.exists():
        return []
    with open(SUPERVISOR_LOG, "rb") as stream:
        stream.seek(0, os.SEEK_END)
        stream.seek(max(0, stream.tell() - 65536))
        tail = stream.read().decode("utf-8", "replace").splitlines()
    since = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(start_wall - 1))
    return [line for line in tail if "adopted running job" in line and line[:19] >= since]


def tree_memory(proc) -> int:
    """max(working set, private bytes), summed over the child and its descendants."""
    import psutil
    total = 0
    try:
        tree = [proc, *proc.children(recursive=True)]
    except psutil.NoSuchProcess:  # the child exited between poll() and here (run3 crashed on this race)
        return 0
    for p in tree:
        try:
            info = p.memory_info()
            total += max(info.rss, getattr(info, "private", 0))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return total


def kill_tree(proc) -> None:
    """Stop this job's own child process tree (the guard's stop action); nothing else is touched."""
    import psutil
    try:
        children = proc.children(recursive=True)
    except psutil.NoSuchProcess:
        children = []
    for p in children:
        try:
            p.kill()
        except psutil.NoSuchProcess:
            pass
    try:
        proc.kill()
    except psutil.NoSuchProcess:
        pass


def run_guarded(argv: list[str], cwd: Path, env: dict, stdout: Path, stderr: Path) -> dict:
    import psutil
    observed = {"stop_reason": None, "max_tree_memory_bytes": 0, "min_free_ram_bytes": None,
                "min_free_disk_bytes": None, "supervisor_adoptions": []}
    start_wall, start = time.time(), time.monotonic()
    last_supervisor = start
    with open(stdout, "xb") as so, open(stderr, "xb") as se:
        popen = subprocess.Popen(argv, cwd=cwd, env=env, stdout=so, stderr=se,
                                 creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS | subprocess.CREATE_NEW_PROCESS_GROUP)
        proc = psutil.Process(popen.pid)
        try:
            while popen.poll() is None:
                memory, ram, disk = tree_memory(proc), free_ram(), free_disk()
                observed["max_tree_memory_bytes"] = max(observed["max_tree_memory_bytes"], memory)
                observed["min_free_ram_bytes"] = ram if observed["min_free_ram_bytes"] is None else min(observed["min_free_ram_bytes"], ram)
                observed["min_free_disk_bytes"] = disk if observed["min_free_disk_bytes"] is None else min(observed["min_free_disk_bytes"], disk)
                now = time.monotonic()
                if ram < FREE_RAM_FLOOR:
                    observed["stop_reason"] = "FREE_RAM_BELOW_6GiB"
                elif memory > MEMORY_CAP:
                    observed["stop_reason"] = "MEMORY_CAP_3GiB"
                elif disk < DISK_FLOOR:
                    observed["stop_reason"] = "DISK_FLOOR"
                elif now - start > HARD_SECONDS:
                    observed["stop_reason"] = "HARD_TIME_LIMIT"
                elif now - last_supervisor >= SUPERVISOR_CHECK_SECONDS or now - start < 2 * POLL_SECONDS:
                    last_supervisor = now
                    adopted = supervisor_adoptions_since(start_wall)
                    if adopted:
                        observed["supervisor_adoptions"] = adopted
                        observed["stop_reason"] = "SUPERVISOR_ADOPTED"
                if observed["stop_reason"]:
                    kill_tree(proc)
                    break
                time.sleep(POLL_SECONDS)
        finally:
            returncode = popen.wait()
    observed["supervisor_adoptions"] = observed["supervisor_adoptions"] or supervisor_adoptions_since(start_wall)
    if observed["supervisor_adoptions"] and not observed["stop_reason"]:
        observed["stop_reason"] = "SUPERVISOR_ADOPTED"
    observed.update(returncode=returncode, elapsed_seconds=round(time.monotonic() - start, 2))
    return observed


def wait_for_headroom() -> float:
    """Before an arm starts (never during one): wait up to START_WAIT_SECONDS for free RAM to reach the
    floor plus START_HEADROOM, so a ~0.45 GiB arm does not start right at the 6 GiB floor."""
    start = time.monotonic()
    while free_ram() < FREE_RAM_FLOOR + START_HEADROOM and time.monotonic() - start < START_WAIT_SECONDS:
        time.sleep(10)
    return round(time.monotonic() - start, 1)


def stage_view(armout: Path, sealed: Path) -> dict:
    view = armout / "data"
    view.mkdir(parents=True)
    sources = [p for p in sorted(sealed.iterdir()) if p.suffix in (".pos", ".hce")]
    sources += [SAMPLE / "h000.pos", SAMPLE / "h000.hce"]
    inventory = {}
    for source in sources:
        before = fingerprint(source)
        dest = view / source.name
        shutil.copyfile(source, dest)
        make_read_only(dest)
        after = fingerprint(dest)
        if after != before:
            raise ValueError(f"copy changed bytes: {source.name}")
        inventory[source.name] = after
    for name, md5 in HOLDOUT_MD5.items():
        if inventory[name]["md5"] != md5:
            raise ValueError("holdout md5 differs in the staged view")
    return inventory


def train(tag: str, data_tag: str) -> int:
    below_normal_self()
    pins = verify_pins(); staged = verify_staged()
    data_check = json.loads((ROOT / f"s18_data_{data_tag}" / "s18_data_check.json").read_text(encoding="utf-8"))
    if data_check["status"] != "PASS_S18_DATA_MATCHES_SOL":
        raise ValueError("training needs a PASS data check (shards identical to Sol's)")
    out = ROOT / f"s18_r4_{tag}"
    out.mkdir()
    result = {"status": "FAIL_S18_TRAINING", "tag": tag, "data_tag": data_tag, "scope": "PIPELINE_ONLY_SYNTHETIC",
              "training_approved": False, "net_adoption": "NONE", "pins": pins, "staged": staged, "arms": {},
              "guard": {"free_ram_floor_bytes": FREE_RAM_FLOOR, "memory_cap_bytes": MEMORY_CAP,
                        "disk_floor_bytes": DISK_FLOOR, "hard_seconds": HARD_SECONDS, "priority": "BELOW_NORMAL",
                        "torch_threads": 1}}
    try:
        for arm in TRAIN_ARMS:
            waited = wait_for_headroom()
            result.setdefault("pre_arm_wait_seconds", {})[arm] = waited
            ram, disk = free_ram(), free_disk()
            if ram < FREE_RAM_FLOOR + START_HEADROOM or disk < DISK_FLOOR:
                result["arms"][arm] = {"status": "NOT_STARTED_GUARD", "free_ram_bytes": ram, "free_disk_bytes": disk}
                print(f"{arm}: NOT STARTED (free RAM {ram / 2**30:.2f} GiB, free disk {disk / 2**30:.1f} GiB)", flush=True)
                break
            armout = out / arm
            for sub in ("cwd", "tmp", "cache"):
                (armout / sub).mkdir(parents=True)
            sealed = ROOT / f"s18_data_{data_tag}" / arm / "sealed"
            summary = json.loads((sealed / "forge_sol_datafilter_summary_20261026.json").read_text(encoding="utf-8"))
            rows = summary["totals"]["kept"]
            inventory = stage_view(armout, sealed)
            argv = [str(VENV_PY), "-B", str(Path(__file__).resolve()), "--child", "--arm", arm, "--out", str(armout),
                    "--rows", str(rows)]
            env = child_env({"TMP": str(armout / "tmp"), "TEMP": str(armout / "tmp"),
                             "TORCH_HOME": str(armout / "cache" / "torch"), "XDG_CACHE_HOME": str(armout / "cache")})
            print(f"{arm}: start rows {rows} steps {2 * (rows // 8192)} free RAM {ram / 2**30:.2f} GiB", flush=True)
            observed = run_guarded(argv, armout / "cwd", env, armout / "stdout", armout / "stderr")
            entry = {"rows": rows, "steps_per_epoch": rows // 8192, "total_steps": 2 * (rows // 8192),
                     "command": argv, "observer": observed, "view_inventory": inventory}
            child_file = armout / "child_result.json"
            child = json.loads(child_file.read_text(encoding="utf-8")) if child_file.exists() else None
            entry["child"] = child
            passed = (observed["returncode"] == 0 and observed["stop_reason"] is None and child is not None
                      and child.get("work_complete") is True)
            if passed:
                entry["native_FINAL_FULL_metric"] = native_final_metric((armout / "stdout").read_text(encoding="utf-8"))
                run = armout / "trainer-run"
                entry["artifacts"] = {p.name: fingerprint(p) for p in sorted(run.iterdir())
                                      if p.is_file() and not p.name.startswith("settings_")}
                if any(fingerprint(armout / "data" / n) != m for n, m in inventory.items()):
                    raise ValueError("staged view changed during training")
            entry["status"] = "PASS_PIPELINE_ONLY" if passed else "FAIL"
            result["arms"][arm] = entry
            print(f"{arm}: {entry['status']} rc {observed['returncode']} stop {observed['stop_reason']} "
                  f"{observed['elapsed_seconds']}s peak {observed['max_tree_memory_bytes'] / 2**20:.0f} MiB", flush=True)
            if not passed:
                break
        verify_pins(); verify_staged()
        result["inputs_unchanged"] = True
        if [a for a in result["arms"] if result["arms"][a]["status"] == "PASS_PIPELINE_ONLY"] == TRAIN_ARMS:
            result["status"] = "PASS_REMAINING4_SYNTHETIC_PIPELINE"
    except BaseException as error:
        result["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        write_json(out / "s18_training_result.json", result)
        print(f"RESULT {result['status']}")
    return 0 if result["status"].startswith("PASS") else 1


# --------------------------------------------------------------------------------------------------- child
def postscore_final_checkpoint(old, run: Path, training_rows: int, view: Path) -> dict:
    """Sol's v4 postscore, unchanged in method: all 50,000 h000 rows of the preselected final epoch-2
    checkpoint, float64 sums of squared errors, three blends, no optimizer step and no export."""
    import numpy as np
    import torch
    checkpoint = final_checkpoint(run, training_rows); checkpoint_before = fingerprint(checkpoint)
    hold_before = {p.name: fingerprint(p) for p in (view / "h000.pos", view / "h000.hce")}
    rng_before = torch.random.get_rng_state().clone()

    def model_hash(model):
        value = hashlib.sha256()
        for name, tensor in sorted(model.state_dict().items()):
            value.update(name.encode() + b"\0" + str(tensor.dtype).encode() + b"\0" + str(tuple(tensor.shape)).encode() + b"\0")
            value.update(tensor.detach().cpu().contiguous().numpy().tobytes())
        return value.hexdigest()

    try:
        ck = torch.load(checkpoint, map_location="cpu", weights_only=True)
        if (ck["next_epoch"] != 2 or ck["step"] != 2 * (training_rows // 8192) or ck["config"]["hidden"] != 256
                or ck["config"]["residual"] is not True or ck["config"]["qat"] is not True):
            raise ValueError("preselected epoch-2 checkpoint/config mismatch")
        model = old.NNUE(256, qat=True, residual=True).cpu(); model.load_state_dict(ck["model"], strict=True); model.eval()
        torch.random.set_rng_state(rng_before)
        state_before = model_hash(model); data = old.load_set([str(view / "h000.pos")], str(view))
        if data["n"] != 50000:
            raise ValueError("postscore requires all 50,000 h000 rows")
        blends = (1.0, 0.6, 0.8); net_sse = {str(b): 0.0 for b in blends}; hce_sse = {str(b): 0.0 for b in blends}
        count = 0; batches = []
        with torch.no_grad():
            for begin in range(0, 50000, 8192):
                end = min(begin + 8192, 50000)
                codes, stm, wres, score, hce = old.make_batch(data, np.arange(begin, end, dtype=np.int64))
                c = torch.from_numpy(codes.astype(np.int64)); s = torch.from_numpy(stm.astype(np.int64))
                wr = torch.from_numpy(wres.astype(np.float32)); sc = torch.from_numpy(score.astype(np.float32))
                hc = torch.from_numpy(hce.astype(np.float32)) * (2.25 / 400.0)
                logit = model(c, s, hc); pred = torch.sigmoid(logit); baseline = torch.sigmoid(hc)
                if not torch.isfinite(logit).all():
                    raise ValueError("non-finite postscore model logit")
                for blend in blends:
                    target = old.targets(sc, s, wr, 2.25, blend)[2]
                    if not torch.isfinite(target).all():
                        raise ValueError("non-finite postscore target")
                    net_sse[str(blend)] += float((pred.double() - target.double()).square().sum())
                    hce_sse[str(blend)] += float((baseline.double() - target.double()).square().sum())
                count += end - begin; batches.append(end - begin)
        state_after = model_hash(model)
        if (count != 50000 or batches != [8192] * 6 + [848] or state_after != state_before
                or fingerprint(checkpoint) != checkpoint_before
                or any(fingerprint(view / n) != m for n, m in hold_before.items())):
            raise ValueError("postscore count/state/checkpoint/holdout integrity failed")
        result = {"rows": count, "batch_sizes": batches, "dropped_tail_rows": 0,
                  "checkpoint_selection": "FINAL_EPOCH2_PRESELECTED", "checkpoint": checkpoint.name,
                  "checkpoint_sha256": checkpoint_before["sha256"],
                  "net_MSE": {b: v / count for b, v in net_sse.items()},
                  "HCE_baseline_MSE": {b: v / count for b, v in hce_sse.items()},
                  "aggregation": "float64 squared errors summed by rows /50000; original float32 predictions/targets promoted before subtraction",
                  "model_state_sha256": state_before, "state_unchanged": True, "holdout": hold_before,
                  "holdout_unchanged": True, "weight_updates": 0, "exports": 0,
                  "postscore_preregistration_sha256": PINS[POSTSCORE_PREREG]}
    finally:
        torch.random.set_rng_state(rng_before)
    result["Torch_RNG_preserved"] = bool(torch.equal(torch.random.get_rng_state(), rng_before))
    return result


def child(arm: str, armout: Path, rows: int) -> int:
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    report = {"arm": arm, "work_complete": False, "torch": torch.__version__, "torch_threads": torch.get_num_threads(),
              "trainer": str(TRAINER), "trainer_sha256": sha256(TRAINER)}
    try:
        if report["trainer_sha256"] != PINS[SRC_TRAINER]:
            raise ValueError("trainer copy differs from the pinned v3b trainer")
        view = armout / "data"
        train_files = sorted(view.glob("t*_filtered_*.pos"))
        spec = importlib.util.spec_from_file_location("opus_nnue_smoke_s18_v3b", TRAINER)
        trainer = importlib.util.module_from_spec(spec); sys.modules["opus_nnue_smoke_s18_v3b"] = trainer
        spec.loader.exec_module(trainer)
        run = armout / "trainer-run"
        saved = sys.argv
        try:
            sys.argv = [str(TRAINER), *trainer_argv(view, train_files, run)]
            report["trainer_argv"] = sys.argv[1:]
            code = trainer.main()
        finally:
            sys.argv = saved
        report["trainer_returncode"] = code
        if code != 0:
            raise ValueError(f"trainer returned {code}")
        report["separate_post_training_all50000"] = postscore_final_checkpoint(trainer, run, rows, view)
        report["work_complete"] = True
    except BaseException as error:
        report["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        write_json(armout / "child_result.json", report)
    return 0


# ------------------------------------------------------------------------------------------------- compare
def fixed_lexemes(stdout_text: str) -> dict:
    """Sol's fixed loss bytes: baseline lines, each epoch line from 'train_mse=' on, the FINAL line."""
    lines = stdout_text.splitlines()
    epochs = {}
    for line in lines:
        match = re.match(r"EPOCH (\d+)/\d+ done in \S+ (train_mse=.*)$", line)
        if match:
            epochs[match[1]] = match[2]
    return {"baseline_lines": [l for l in lines if l.startswith("BASELINE HCE-alone")],
            "epoch_loss_suffix_by_epoch": epochs,
            "native_final_lines": [l for l in lines if l.startswith("FINAL FULL HOLDOUT n=")]}


def compare(tag_a: str, tag_b: str) -> int:
    runs = {}
    for tag in (tag_a, tag_b):
        runs[tag] = json.loads((ROOT / f"s18_r4_{tag}" / "s18_training_result.json").read_text(encoding="utf-8"))
    reference = json.loads(T200_REFERENCE.read_text(encoding="utf-8"))
    report = {"runs": [tag_a, tag_b], "arms": {}, "status": "FAIL"}
    ok = True
    for arm in TRAIN_ARMS:
        a, b = runs[tag_a]["arms"].get(arm), runs[tag_b]["arms"].get(arm)
        entry = {}
        if not a or not b or a["status"] != "PASS_PIPELINE_ONLY" or b["status"] != "PASS_PIPELINE_ONLY":
            report["arms"][arm] = {"status": "NOT_COMPARABLE"}; ok = False; continue
        lex = {t: fixed_lexemes((ROOT / f"s18_r4_{t}" / arm / "stdout").read_text(encoding="utf-8")) for t in (tag_a, tag_b)}
        entry["artifacts_identical"] = {n: a["artifacts"][n]["sha256"] == b["artifacts"].get(n, {}).get("sha256") for n in a["artifacts"]}
        entry["same_artifact_names"] = set(a["artifacts"]) == set(b["artifacts"])
        entry["fixed_loss_lexemes_identical"] = lex[tag_a] == lex[tag_b]
        pa, pb = a["child"]["separate_post_training_all50000"], b["child"]["separate_post_training_all50000"]
        entry["postscore_identical"] = pa["net_MSE"] == pb["net_MSE"] and pa["HCE_baseline_MSE"] == pb["HCE_baseline_MSE"]
        entry["holdout_md5"] = {n: pa["holdout"][n]["md5"] for n in pa["holdout"]}
        entry["holdout_md5_ok"] = entry["holdout_md5"] == HOLDOUT_MD5
        entry["rows"] = a["rows"]
        entry["reproducible_same_pc"] = (entry["same_artifact_names"] and all(entry["artifacts_identical"].values())
                                         and entry["fixed_loss_lexemes_identical"] and entry["postscore_identical"])
        ok = ok and entry["reproducible_same_pc"] and entry["holdout_md5_ok"]
        if arm == "t200":
            want = {Path(x["path"]).name: x["sha256"] for x in reference["epoch_artifacts"]}
            got = {n: m["sha256"] for n, m in a["artifacts"].items()}
            fixed = reference["fixed_emitted_loss_bytes"]
            entry["vs_sol_v3_reference"] = {
                "artifacts_identical": {n: got.get(n) == s for n, s in want.items()},
                "baseline_lines_identical": lex[tag_a]["baseline_lines"] == fixed["baseline_lines"],
                "epoch_suffixes_identical": lex[tag_a]["epoch_loss_suffix_by_epoch"] == fixed["epoch_loss_suffix_by_epoch"],
                "final_line_identical": lex[tag_a]["native_final_lines"] == fixed["native_final_lines"],
            }
            vs = entry["vs_sol_v3_reference"]
            vs["status"] = ("CONFIRMED" if all(vs["artifacts_identical"].values()) and vs["baseline_lines_identical"]
                            and vs["epoch_suffixes_identical"] and vs["final_line_identical"] else "NOT_CONFIRMED")
        report["arms"][arm] = entry
    report["t300_rows_157666"] = runs[tag_a]["arms"].get("t300", {}).get("rows") == 157666
    ok = ok and report["t300_rows_157666"]
    report["status"] = "PASS_REMAINING4_REPRODUCIBLE_SAME_PC" if ok else "FAIL_OR_NOT_REPRODUCIBLE"
    table = ["| arm | rows kept | steps | net_MSE b1.0 | b0.6 | b0.8 | HCE b1.0 | HCE b0.6 | HCE b0.8 | native FINAL (49,152 rows) b1.0/b0.6/b0.8 |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    for arm in TRAIN_ARMS:
        a = runs[tag_a]["arms"].get(arm)
        if not a or a["status"] != "PASS_PIPELINE_ONLY":
            table.append(f"| {arm} | | | not run | | | | | | |"); continue
        p = a["child"]["separate_post_training_all50000"]; n = a["native_FINAL_FULL_metric"]["net_MSE"]
        table.append(f"| {arm} | {a['rows']:,} | {a['total_steps']} | {p['net_MSE']['1.0']!r} | {p['net_MSE']['0.6']!r} | "
                     f"{p['net_MSE']['0.8']!r} | {p['HCE_baseline_MSE']['1.0']!r} | {p['HCE_baseline_MSE']['0.6']!r} | "
                     f"{p['HCE_baseline_MSE']['0.8']!r} | {n['1.0']:.6f}/{n['0.6']:.6f}/{n['0.8']:.6f} |")
    report["loss_table_markdown"] = "\n".join(table)
    out = ROOT / f"s18_compare_{tag_a}_{tag_b}"
    out.mkdir(exist_ok=False)
    write_json(out / "s18_compare_result.json", report)
    (out / "s18_loss_table.md").write_text(report["loss_table_markdown"] + "\n", encoding="utf-8", newline="\n")
    print(report["loss_table_markdown"])
    for arm, entry in report["arms"].items():
        print(arm, json.dumps({k: v for k, v in entry.items() if k in ("reproducible_same_pc", "holdout_md5_ok", "rows")}),
              entry.get("vs_sol_v3_reference", {}).get("status", ""))
    print(f"RESULT {report['status']}")
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--stage", action="store_true")
    mode.add_argument("--data", metavar="TAG")
    mode.add_argument("--check-data", metavar="TAG")
    mode.add_argument("--hist", metavar="TAG")
    mode.add_argument("--train", metavar="TAG")
    mode.add_argument("--compare", nargs=2, metavar=("TAG_A", "TAG_B"))
    mode.add_argument("--child", action="store_true")
    ap.add_argument("--data-tag", default="run1")
    ap.add_argument("--arm", choices=TRAIN_ARMS)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--rows", type=int)
    args = ap.parse_args(argv)
    for tag in (args.data, args.check_data, args.hist, args.train, args.data_tag):
        if tag is not None and not re.fullmatch(r"run[0-9]+", tag):
            ap.error("tags are run1, run2, ...")
    if args.child:
        return child(args.arm, args.out, args.rows)
    below_normal_self()
    if args.stage:
        return stage()
    if args.data:
        return data(args.data)
    if args.check_data:
        return check_data(args.check_data)
    if args.hist:
        return hist(args.hist)
    if args.train:
        return train(args.train, args.data_tag)
    return compare(*args.compare)


if __name__ == "__main__":
    raise SystemExit(main())
