"""S-A3 CPU smoke runner for train_resid_v3d.py (S50's v3c + lr schedule options, defaults = v3b's schedule).

Cases: v3b x2, S50's v3c off, v3d defaults x2 and with the defaults spelled out, cosine with --lr-schedule-epochs = --epochs and
= 3 x --epochs, linear x2, wsd x2, resumes from epoch 1 (wsd, long cosine), an "extend" chain (stop at epoch 1 of a 2-epoch
horizon, then resume with --epochs 2), and wsd together with --epoch-positions --recent-weight --init-weights (x2).

PC rules: the trainers run only as renamed copies in F:\\opus_scratch\\sol_SA3 -- opus_nnue_smoke_sa3_v3b.py (the lock archive's
train_resid_v3b.py, sha256 5cebba4d...), opus_nnue_smoke_sa3_v3c.py (opus-sol-S50's train_resid_v3c.py, sha256 ddff28bb...) and
opus_nnue_smoke_sa3_v3d.py (byte-identical to train_resid_v3d.py in this folder) with qa_adam_dml.py beside them -- imported by a
--child process whose command line names none of them (the NNUE supervisor adopts python.exe processes whose command line
matches train_resid*.py). CPU only, one Torch thread, Idle priority, outputs only under F:\\opus_scratch\\sol_SA3\\out\\<tag>
(never runs_* / smoke_kb*). A run starts only with >= 6 GiB available RAM and is stopped below it; the supervisor log is polled
and any new "adopted running job" line stops the suite. Data: the lock archive's data32_sample_50k (synthetic): every loss is a
pipeline result, not a quality result.

  <venv python> -I -B opus_nnue_smoke_sa3.py --stage            copy + pin-check the inputs into F:\\opus_scratch\\sol_SA3
  <venv python> -I -B opus_nnue_smoke_sa3.py --suite r1         smoke cases (seed 99, 2 epochs) into out\\r1
  <venv python> -I -B opus_nnue_smoke_sa3.py --compare r1       acceptance checks on out\\r1 (acceptance.json + table)
  <venv python> -I -B opus_nnue_smoke_sa3.py --rss t1           10k-step private-memory trace, v3b vs v3d wsd, into out\\t1
  <venv python> -I -B opus_nnue_smoke_sa3.py --rss-eval t1      re-evaluate an existing trace (no training)
"""
from __future__ import annotations

import argparse
import ctypes
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

HERE = Path(__file__).resolve().parent
V3C_SRC = HERE.parent / "sol_S50" / ("train_resid" + "_v3c.py")  # opus-sol-S50's v3c (never run under this name)
V3D_SRC = HERE / ("train_resid" + "_v3d.py")  # the deliverable (never run under this name)
PIN_V3C = "ddff28bb6801421793e1767cec8271fe3406a263b0c0dfec03ac0cd97dcadef8"  # md5 e7fefe77 (opus-sol-S50)
LA = Path(r"D:\grok-pc-data\dwqww\.claude\worktrees\b\pkg\forge_LOCK_AL1_s198_FULL_20261026_1039\5_nnue")
SRC_V3B = LA / "trainers" / "cpu_smoke" / ("train_resid" + "_v3b.py")
SRC_ADAM = LA / "trainers" / "cpu_smoke" / "qa_adam_dml.py"
SRC_SAMPLE = LA / "sample_data" / "data32_sample" / "data32_sample_50k"
ROOT = Path(r"F:\opus_scratch\sol_SA3")
TRAINERS = {"v3b": ROOT / "opus_nnue_smoke_sa3_v3b.py", "v3c": ROOT / "opus_nnue_smoke_sa3_v3c.py",
            "v3d": ROOT / "opus_nnue_smoke_sa3_v3d.py"}
ADAM = ROOT / "qa_adam_dml.py"
SAMPLE = ROOT / "inputs" / "data32_sample_50k"
TMP = ROOT / "tmp"
SUPERVISOR_LOG = Path(r"F:\forge_nnue_train\supervisor.log")
SHARDS = ("t00000", "t01000", "t02000", "t03000")
PIN_V3B = "5cebba4d44133630e247d9ab4c0085fa6301dde8db1dfe1389452ac19d92313f"  # md5 b6758004 (CHANGES_v3b.md)
PIN_ADAM = "799faa89bc7b8dbd8c9a8747dd6658085eb0a69b84800af191db5ca7fd660cba"
SAMPLE_PINS = {  # = opus-sol-S18's pins of the same lock-archive sample
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
RAM_FLOOR = 6 * 1024**3
IDLE_PRIORITY_CLASS = 0x00000040
PROGRESS = re.compile(r"^ep(\d+) step ([\d,]+)/([\d,]+) ")
TIMING = [(re.compile(r"\((\d+)s\)$"), "(Xs)"), (re.compile(r"\((\d+)s load\)$"), "(Xs load)"),
          (re.compile(r" done in \d+s "), " done in Xs "), (re.compile(r" in \d+s$"), " in Xs")]


# ------------------------------------------------------------------------------------------------ helpers
def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def md5(path: Path) -> str:
    return hashlib.md5(Path(path).read_bytes()).hexdigest()


def write_json(path: Path, value) -> None:
    Path(path).write_text(json.dumps(value, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


class _PMC(ctypes.Structure):
    _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong)] + [(f, ctypes.c_size_t) for f in (
        "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage",
        "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage", "PrivateUsage")]


class _MSX(ctypes.Structure):
    _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong)] + [(f, ctypes.c_ulonglong) for f in (
        "ullTotalPhys", "ullAvailPhys", "ullTotalPageFile", "ullAvailPageFile", "ullTotalVirtual", "ullAvailVirtual",
        "ullAvailExtendedVirtual")]


def mem_counters() -> dict:
    """This process: private bytes, working set and their peaks (PeakPagefileUsage = peak private commit)."""
    k32, psapi = ctypes.WinDLL("kernel32"), ctypes.WinDLL("psapi")
    psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong]
    k32.GetCurrentProcess.restype = ctypes.c_void_p
    pmc = _PMC(); pmc.cb = ctypes.sizeof(_PMC)
    psapi.GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb)
    return {"private": pmc.PrivateUsage, "wset": pmc.WorkingSetSize, "peak_wset": pmc.PeakWorkingSetSize,
            "peak_private": pmc.PeakPagefileUsage}


def avail_ram() -> int:
    ms = _MSX(); ms.dwLength = ctypes.sizeof(_MSX)
    ctypes.WinDLL("kernel32").GlobalMemoryStatusEx(ctypes.byref(ms))
    return int(ms.ullAvailPhys)


def adoption_lines() -> list[str]:
    if not SUPERVISOR_LOG.exists():
        return []
    text = SUPERVISOR_LOG.read_bytes().decode("utf-8", "replace")
    return [line for line in text.splitlines() if "adopted running job" in line]


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module


def normalize(stdout: str) -> list[str]:
    """Trainer stdout without MEM lines and with the wall-clock fields replaced (everything else must match exactly)."""
    out = []
    for line in stdout.splitlines():
        if line.startswith("MEM "):
            continue
        for pattern, repl in TIMING:
            line = pattern.sub(repl, line)
        out.append(line)
    return out


# ------------------------------------------------------------------------------------------------- stage
def verify_inputs() -> dict:
    found = {"v3b_copy": sha256(TRAINERS["v3b"]), "v3c_copy": sha256(TRAINERS["v3c"]), "v3d_copy": sha256(TRAINERS["v3d"]),
             "v3d_src": sha256(V3D_SRC), "qa_adam_dml": sha256(ADAM), "sample": {n: sha256(SAMPLE / n) for n in SAMPLE_PINS}}
    bad = []
    if found["v3b_copy"] != PIN_V3B:
        bad.append("v3b copy")
    if found["v3c_copy"] != PIN_V3C:
        bad.append("v3c copy (opus-sol-S50)")
    if found["qa_adam_dml"] != PIN_ADAM:
        bad.append("qa_adam_dml")
    if found["v3d_copy"] != found["v3d_src"]:
        bad.append("v3d copy != train_resid_v3d.py in the job folder (re-run --stage)")
    bad += [n for n, h in found["sample"].items() if h != SAMPLE_PINS[n]]
    if bad:
        raise SystemExit("input check FAILED: " + ", ".join(bad))
    return found


def stage() -> int:
    if sha256(SRC_V3B) != PIN_V3B or sha256(SRC_ADAM) != PIN_ADAM or sha256(V3C_SRC) != PIN_V3C:
        raise SystemExit("lock-archive trainer files or the opus-sol-S50 v3c differ from their pins")
    SAMPLE.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    for name, pin in SAMPLE_PINS.items():
        if not (SAMPLE / name).exists():
            if sha256(SRC_SAMPLE / name) != pin:
                raise SystemExit(f"lock-archive sample differs from its pin: {name}")
            shutil.copyfile(SRC_SAMPLE / name, SAMPLE / name)
    for dst, src in ((TRAINERS["v3b"], SRC_V3B), (ADAM, SRC_ADAM), (TRAINERS["v3c"], V3C_SRC)):
        if not dst.exists():
            shutil.copyfile(src, dst)
    if not TRAINERS["v3d"].exists() or sha256(TRAINERS["v3d"]) != sha256(V3D_SRC):
        if TRAINERS["v3d"].exists():  # keep the previous copy (no deletes): rename it by its sha256 prefix
            TRAINERS["v3d"].rename(ROOT / f"prev_{sha256(TRAINERS['v3d'])[:12]}_{TRAINERS['v3d'].name}.txt")
        shutil.copyfile(V3D_SRC, TRAINERS["v3d"])
    found = verify_inputs()
    write_json(ROOT / "inputs_receipt.json", {"status": "PASS_STAGED", **found, "v3b_source": str(SRC_V3B), "v3c_source": str(V3C_SRC),
                                               "v3d_md5": md5(TRAINERS["v3d"]), "v3c_md5": md5(TRAINERS["v3c"]),
                                               "v3b_md5": md5(TRAINERS["v3b"])})
    print(json.dumps(found, indent=1))
    print("RESULT PASS_STAGED")
    return 0


# ------------------------------------------------------------------------------------------------- child
class StampedStdout:
    """Passes the trainer's stdout through; at every progress line ("epN step S/T ...") records this process's memory."""
    def __init__(self, inner, trace):
        self.inner, self.trace, self.part = inner, trace, ""

    def write(self, s):
        self.inner.write(s)
        self.part += s
        while "\n" in self.part:
            line, self.part = self.part.split("\n", 1)
            m = PROGRESS.match(line)
            if m:
                self.trace.append({"step": int(m[2].replace(",", "")), "t": time.time(), **mem_counters()})
        return len(s)

    def flush(self):
        self.inner.flush()


def child(case_dir: Path) -> int:
    case = json.loads((case_dir / "case.json").read_text(encoding="utf-8"))
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    trainer = load_module(Path(case["trainer"]))
    sys.argv = [case["trainer"], *case["argv"]]
    trace = []
    if case.get("trace"):
        sys.stdout = StampedStdout(sys.stdout, trace)
    t0 = time.time()
    rc = trainer.main()
    sys.stdout.flush()
    write_json(case_dir / "child_result.json", {"rc": rc, "seconds": round(time.time() - t0, 2), "mem_end": mem_counters(),
                                                 "trace": trace, "torch": torch.__version__, "threads": torch.get_num_threads()})
    return int(rc or 0)


# ------------------------------------------------------------------------------------------------ parent
def child_env() -> dict:
    env = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1",
               TMP=str(TMP), TEMP=str(TMP))
    return env


def run_case(out: Path, name: str, trainer: str, argv: list[str], adopted0: int, trace: bool = False) -> dict:
    case_dir = out / name
    case_dir.mkdir(parents=True)
    run_dir = case_dir / "run"
    full_argv = [*argv, "--run-dir", str(run_dir)]
    write_json(case_dir / "case.json", {"name": name, "trainer": str(TRAINERS[trainer]), "argv": full_argv, "trace": trace})
    row = {"name": name, "trainer": trainer, "argv": full_argv}
    if avail_ram() < RAM_FLOOR:
        row["status"] = "NOT_STARTED_RAM"
        return row
    t0 = time.time(); min_avail = avail_ram(); stop = None
    with open(case_dir / "stdout.txt", "xb") as so, open(case_dir / "stderr.txt", "xb") as se:
        proc = subprocess.Popen([sys.executable, "-I", "-B", str(Path(__file__).resolve()), "--child", str(case_dir)],
                                stdout=so, stderr=se, env=child_env(), cwd=str(ROOT), creationflags=IDLE_PRIORITY_CLASS)
        polls = 0
        while proc.poll() is None:
            time.sleep(0.5); polls += 1
            min_avail = min(min_avail, avail_ram())
            if min_avail < RAM_FLOOR:
                stop = "RAM_FLOOR"
            elif polls % 4 == 0 and len(adoption_lines()) != adopted0:
                stop = "SUPERVISOR_ADOPTION"
            if stop:
                proc.terminate()  # this job's own child only
                break
        rc = proc.wait()
    row.update(rc=rc, seconds=round(time.time() - t0, 1), min_avail_gib=round(min_avail / 2**30, 2),
               adoption_lines=len(adoption_lines()))
    stdout = (case_dir / "stdout.txt").read_text(encoding="utf-8", errors="replace")
    row["stdout_normalized"] = normalize(stdout)
    if (case_dir / "child_result.json").exists():
        res = json.loads((case_dir / "child_result.json").read_text(encoding="utf-8"))
        row["peak_private"] = res["mem_end"]["peak_private"]; row["peak_wset"] = res["mem_end"]["peak_wset"]
        row["torch_threads"] = res["threads"]
    files = sorted(run_dir.iterdir()) if run_dir.exists() else []
    row["artifacts"] = {p.name: {"sha256": sha256(p), "md5": md5(p), "bytes": p.stat().st_size}
                        for p in files if not p.name.startswith("settings_")}
    settings = [p for p in files if p.name.startswith("settings_")]
    if settings:  # the trainer path and this case's run dir differ between cases by design
        head, body = settings[0].read_text(encoding="utf-8").split("\n", 1)
        row["settings_argv"] = head.replace(str(TRAINERS[trainer]), "<trainer>").replace(str(run_dir), "<run>")
        row["settings_json"] = body.replace(json.dumps(str(run_dir))[1:-1], "<run>")
    row["status"] = stop or ("PASS" if rc == 0 else "FAIL")
    print(f"{name:10s} {trainer} {row['status']} rc={rc} {row['seconds']} s min_avail={row['min_avail_gib']} GiB "
          f"peak_private={row.get('peak_private', 0) / 2**20:.1f} MiB", flush=True)
    return row


def base_argv(extra=()) -> list[str]:
    return ["--train", *[str(SAMPLE / f"{s}.pos") for s in SHARDS], "--holdout", str(SAMPLE / "h000.pos"),
            "--hce-dir", str(SAMPLE), "--device", "cpu", "--residual", "--init-check", "--final-full-val",
            "--log-every", "1e9", "--shape", "64", "--epochs", "2", "--lr", "7.07e-4", "--blend-end", "0.6", "--seed", "99",
            "--batch-size", "1024", "--warmup-steps", "20", "--val-positions", "16384", *extra]


ON_W = ["--epoch-positions", "100000", "--recent-weight", "3"]
WSD = ["--lr-schedule", "wsd"]
COS_H6 = ["--lr-schedule-epochs", "6"]
EXT = ["--lr-schedule", "wsd", "--lr-schedule-epochs", "2", "--blend-start", "0.6"]  # constant blend 0.6 (blend-end default 0.6)
SUITE = [("v3b_1", "v3b", []), ("v3b_2", "v3b", []), ("v3c_off", "v3c", []),
         ("off_1", "v3d", []), ("off_2", "v3d", []),
         ("cos_explicit", "v3d", ["--lr-schedule", "cosine", "--lr-schedule-epochs", "0", "--lr-decay-frac", "0.2"]),
         ("cos_h2", "v3d", ["--lr-schedule-epochs", "2"]),
         ("lin_1", "v3d", ["--lr-schedule", "linear"]), ("lin_2", "v3d", ["--lr-schedule", "linear"]),
         ("wsd_1", "v3d", WSD), ("wsd_2", "v3d", WSD),
         ("cos_h6_1", "v3d", COS_H6), ("cos_h6_2", "v3d", COS_H6),
         ("wsd_res", "v3d", [*WSD, "--resume", "@wsd_1/epoch001"]),
         ("cos_h6_res", "v3d", [*COS_H6, "--resume", "@cos_h6_1/epoch001"]),
         ("ext_full", "v3d", EXT), ("ext_part", "v3d", [*EXT, "--epochs", "1"]),
         ("ext_cont", "v3d", [*EXT, "--resume", "@ext_part/epoch001"]),
         ("wsd_on_init_1", "v3d", [*WSD, *ON_W, "--init-weights", "@v3b_1/epoch002"]),
         ("wsd_on_init_2", "v3d", [*WSD, *ON_W, "--init-weights", "@v3b_1/epoch002"])]


def pt_content_diff(pa: Path, pb: Path) -> list[str]:
    """Bitwise content diff of two trainer .pt payloads: dict keys in order, Python types, floats by their IEEE bytes, tensors by
    dtype/shape and raw bytes (so -0.0 != 0.0). [] = same content. (Byte-level .pt identity can still differ through pickle
    memoization of equal strings and torch's derived serialization_id.)"""
    import struct
    import torch

    out = []

    def walk(a, b, path):
        if torch.is_tensor(a) or torch.is_tensor(b):
            if not (torch.is_tensor(a) and torch.is_tensor(b)) or a.dtype != b.dtype or a.shape != b.shape:
                out.append(f"{path}: tensor type/dtype/shape")
            elif a.contiguous().view(-1).numpy().tobytes() != b.contiguous().view(-1).numpy().tobytes():
                out.append(f"{path}: tensor bytes")
        elif isinstance(a, dict) and isinstance(b, dict):
            if list(a) != list(b):
                out.append(f"{path}: keys")
            for key in a:
                if key in b:
                    walk(a[key], b[key], f"{path}/{key}")
        elif isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)) and type(a) is type(b):
            if len(a) != len(b):
                out.append(f"{path}: length")
            for i, (x, y) in enumerate(zip(a, b)):
                walk(x, y, f"{path}[{i}]")
        elif type(a) is not type(b):
            out.append(f"{path}: {type(a).__name__} vs {type(b).__name__}")
        elif isinstance(a, float):
            if struct.pack("<d", a) != struct.pack("<d", b):
                out.append(f"{path}: {a!r} vs {b!r}")
        elif a != b:
            out.append(f"{path}: {a!r} vs {b!r}")

    walk(torch.load(pa, map_location="cpu", weights_only=True), torch.load(pb, map_location="cpu", weights_only=True), "")
    return out


def resolve(out: Path, argv: list[str]) -> list[str]:
    """'@case/epochNNN' -> that case's epoch checkpoint path."""
    res = []
    for x in argv:
        if x.startswith("@"):
            case, stem = x[1:].split("/")
            res.append(str(sorted((out / case / "run").glob(stem + "-*.pt"))[0]))
        else:
            res.append(x)
    return res


def suite(tag: str) -> int:
    inputs = verify_inputs()
    out = ROOT / "out" / tag
    out.mkdir(parents=True)
    adopted0 = len(adoption_lines())
    rows = []
    for name, trainer, extra in SUITE:
        row = run_case(out, name, trainer, resolve(out, base_argv(extra)), adopted0)
        rows.append(row)
        if row["status"] != "PASS":
            break
    write_json(out / "results.json", {"tag": tag, "inputs": inputs, "adoption_lines_before": adopted0, "rows": rows})
    return 0 if all(r["status"] == "PASS" for r in rows) and len(rows) == len(SUITE) else 1


# ----------------------------------------------------------------------------------------------- compare
def compare(tag: str) -> int:
    data = json.loads((ROOT / "out" / tag / "results.json").read_text(encoding="utf-8"))
    R = {r["name"]: r for r in data["rows"]}
    checks = []

    def check(item, ok, detail):
        checks.append({"item": item, "result": "PASS" if ok else "FAIL", "detail": detail})

    def run_of(name):
        return ROOT / "out" / tag / name / "run"

    def arts(name, only=None, exts=(".pt", ".inc", ".bin", ".json")):
        return {k: v["sha256"] for k, v in R[name]["artifacts"].items()
                if (only is None or k.startswith(only)) and k.endswith(exts)}

    def same(a, b, only=None, exts=(".pt", ".inc", ".bin", ".json")):
        A, B = arts(a, only, exts), arts(b, only, exts)
        return A == B and len(A) > 0, len(A)

    def out(name):
        return R[name]["stdout_normalized"]

    def line_of(name, prefix):
        hits = [x for x in out(name) if x.startswith(prefix)]
        return hits[0] if hits else ""

    def loss_lines(name):
        return [x for x in out(name) if x.startswith(("BASELINE", "INIT", "EPOCH", "FINAL"))]

    def json_of(name, ep):
        key = [k for k in R[name]["artifacts"] if k.startswith(ep) and k.endswith(".json")][0]
        return json.loads((run_of(name) / key).read_text(encoding="utf-8"))

    def inc(name, ep="epoch002"):
        return [v["md5"] for k, v in R[name]["artifacts"].items() if k.startswith(ep) and k.endswith(".inc")]

    ok, n = same("v3b_1", "v3b_2")
    check("v3b reproducible (v3b_1 == v3b_2)", ok and out("v3b_1") == out("v3b_2"), f"{n} artifacts sha256-equal: {ok}; stdout equal: {out('v3b_1') == out('v3b_2')}")
    for c, ref in (("v3c_off", "v3b_1"), ("off_1", "v3b_1"), ("off_2", "v3b_1"), ("off_1", "v3c_off"), ("cos_explicit", "v3b_1")):
        ok, n = same(ref, c)
        so = out(c) == out(ref)
        ss = R[c]["settings_json"] == R[ref]["settings_json"]
        what = {"v3c_off": "opus-sol-S50 v3c, options off", "cos_explicit": "v3d with the three defaults spelled out"}.get(c, "v3d defaults")
        check(f"defaults identical: {c} ({what}) vs {ref}", ok and so and ss,
              f"{n} artifacts (.pt .inc .bin .json x 2 epochs) sha256-equal: {ok}; normalized stdout equal: {so}; settings dump equal: {ss} "
              f"(ep2 .inc md5 {inc(c)})")
    ok, n = same("v3b_1", "cos_h2", exts=(".inc", ".bin"))
    ll = loss_lines("cos_h2") == loss_lines("v3b_1")
    js = json_of("cos_h2", "epoch002")
    sline = line_of("cos_h2", "lr schedule:")
    check("--lr-schedule-epochs = --epochs gives v3b's weights and loss (cos_h2)",
          ok and n == 4 and ll and js.get("lr_schedule") == "cosine" and js.get("lr_schedule_steps") == 390
          and sline == "lr schedule: cosine over 390 steps (2 epochs x 195), warmup 20, floor 0.01 x lr",
          f"{n} .inc/.bin sha256-equal to v3b: {ok}; BASELINE/INIT/EPOCH/FINAL lines equal: {ll}; .json lr_schedule={js.get('lr_schedule')} "
          f"lr_schedule_steps={js.get('lr_schedule_steps')}; '{sline}'")
    for a, b in (("lin_1", "lin_2"), ("wsd_1", "wsd_2"), ("cos_h6_1", "cos_h6_2"), ("wsd_on_init_1", "wsd_on_init_2")):
        ok, n = same(a, b)
        so = out(a) == out(b)
        check(f"deterministic ({a} == {b})", ok and n == 8 and so, f"{n} artifacts sha256-equal: {ok} (ep2 .inc md5 {inc(a)}); stdout equal: {so}")
    incs = {c: inc(c) for c in ("v3b_1", "lin_1", "wsd_1", "cos_h6_1")}
    check("each schedule trains differently (sanity: the comparisons can fail)", len({tuple(v) for v in incs.values()}) == 4,
          "ep2 .inc md5: " + ", ".join(f"{c} {v[0][:8] if v else '?'}" for c, v in incs.items()))
    expect = {
        "lin_1": ("linear", 390, None, "lr schedule: linear over 390 steps (2 epochs x 195), warmup 20, floor 0.01 x lr"),
        "wsd_1": ("wsd", 390, 312, "lr schedule: wsd over 390 steps (2 epochs x 195), lr 0.000707 until step 312, then linear decay, "
                                   "warmup 20, floor 0.01 x lr"),
        "cos_h6_1": ("cosine", 1170, None, "lr schedule: cosine over 1,170 steps (6 epochs x 195), warmup 20, floor 0.01 x lr; the run "
                                           "stops at step 390 of the horizon"),
    }
    for c, (kind, steps, d0, text) in expect.items():
        js = json_of(c, "epoch002")
        st = json.loads(R[c]["settings_json"])
        rec_json = js.get("lr_schedule") == kind and js.get("lr_schedule_steps") == steps and js.get("lr_decay_start_step") == d0 \
            and (js.get("lr_decay_frac") == (0.2 if d0 else None))
        rec_set = st.get("lr_schedule") == kind and "lr_schedule_epochs" in st and "lr_decay_frac" in st
        rec_out = line_of(c, "lr schedule:") == text and line_of(c, "steps/epoch=").startswith(f"steps/epoch=195 total=390 batch=1024 lr=0.000707 {kind} blend")
        check(f"schedule recorded ({c}: .json config, settings dump, stdout)", rec_json and rec_set and rec_out,
              f".json lr_schedule={js.get('lr_schedule')} lr_schedule_steps={js.get('lr_schedule_steps')} lr_decay_frac={js.get('lr_decay_frac')} "
              f"lr_decay_start_step={js.get('lr_decay_start_step')}: {rec_json}; settings lr_schedule={st.get('lr_schedule')} "
              f"lr_schedule_epochs={st.get('lr_schedule_epochs')} lr_decay_frac={st.get('lr_decay_frac')}: {rec_set}; stdout lines: {rec_out}")
    for res, src in (("wsd_res", "wsd_1"), ("cos_h6_res", "cos_h6_1")):
        same3, n3 = same(src, res, only="epoch002", exts=(".inc", ".bin", ".json"))
        pt = [k for k in R[src]["artifacts"] if k.startswith("epoch002") and k.endswith(".pt")]
        diff = pt_content_diff(run_of(src) / pt[0], run_of(res) / pt[0]) if pt else ["missing"]
        e2 = line_of(src, "EPOCH 2/2") == line_of(res, "EPOCH 2/2")
        check(f"resume from epoch 1 reproduces epoch 2 ({res} vs {src})", same3 and n3 == 3 and not diff and e2,
              f"epoch-2 .inc .bin .json sha256-equal: {same3}; .pt content bitwise-equal: {not diff} {diff[:3]}; EPOCH 2 line equal: {e2}")
    ok1, n1 = same("ext_full", "ext_part", only="epoch001", exts=(".inc", ".bin"))
    ok2, n2 = same("ext_full", "ext_cont", only="epoch002", exts=(".inc", ".bin", ".json"))
    pt = [k for k in R["ext_full"]["artifacts"] if k.startswith("epoch002") and k.endswith(".pt")]
    diff = pt_content_diff(run_of("ext_full") / pt[0], run_of("ext_cont") / pt[0]) if pt else ["missing"]
    stop = line_of("ext_part", "lr schedule:").endswith("; the run stops at step 195 of the horizon")
    check("extend: stop at epoch 1 of a 2-epoch horizon, resume with --epochs 2 = the uninterrupted run (constant blend)",
          ok1 and n1 == 2 and ok2 and n2 == 3 and not diff and stop,
          f"ext_part epoch-1 .inc/.bin = ext_full's: {ok1}; ext_cont epoch-2 .inc/.bin/.json = ext_full's: {ok2}, .pt content: {not diff}; "
          f"ext_part says it stops at step 195 of the horizon: {stop}")
    js = json_of("wsd_on_init_1", "epoch002")
    o = out("wsd_on_init_1")
    wl = line_of("wsd_on_init_1", "lr schedule:")
    ok = ("INIT CHECK OK (warm start == checkpoint val)" in o and line_of("wsd_on_init_1", "steps/epoch=").startswith("steps/epoch=97 total=194 ")
          and wl == "lr schedule: wsd over 194 steps (2 epochs x 97), lr 0.000707 until step 155, then linear decay, warmup 20, floor 0.01 x lr"
          and js.get("epoch_positions") == 100000 and js.get("recent_weight") == 3.0 and bool(js.get("init_weights_md5"))
          and js.get("lr_schedule") == "wsd" and js.get("lr_schedule_steps") == 194 and js.get("lr_decay_start_step") == 155)
    check("works with --epoch-positions/--recent-weight and --init-weights (wsd_on_init_1)", ok,
          f"INIT CHECK OK; {line_of('wsd_on_init_1', 'steps/epoch=')}; '{wl}'; .json epoch_positions={js.get('epoch_positions')} "
          f"recent_weight={js.get('recent_weight')} init_weights_md5={js.get('init_weights_md5')} lr_schedule={js.get('lr_schedule')} "
          f"lr_schedule_steps={js.get('lr_schedule_steps')} lr_decay_start_step={js.get('lr_decay_start_step')}")
    check("no new supervisor adoption", all(r.get("adoption_lines") == data["adoption_lines_before"] for r in data["rows"]),
          f"'adopted running job' lines before {data['adoption_lines_before']}, after each run "
          f"{sorted({r.get('adoption_lines') for r in data['rows']})}")
    write_json(ROOT / "out" / tag / "acceptance.json", checks)
    print("| check | result | detail |\n|---|---|---|")
    for c in checks:
        print(f"| {c['item']} | **{c['result']}** | {c['detail']} |")
    print("RESULT " + ("PASS" if all(c["result"] == "PASS" for c in checks) else "FAIL") + f" {sum(c['result'] == 'PASS' for c in checks)}/{len(checks)}")
    print("loss lines v3b_1 / lin_1 / wsd_1 / cos_h6_1 / wsd_on_init_1:")
    for c in ("v3b_1", "lin_1", "wsd_1", "cos_h6_1", "wsd_on_init_1"):
        for x in loss_lines(c):
            print(f"  {c}: {x}")
    return 0 if all(c["result"] == "PASS" for c in checks) else 1


# --------------------------------------------------------------------------------------------------- rss
RSS_COMMON = ["--shape", "32", "--batch-size", "64", "--epochs", "4", "--warmup-steps", "100", "--val-positions", "8192",
              "--log-every", "0.5"]


RSS_CASES = [("rss_v3b", "v3b", ["--steps-per-epoch", "2500"]),
             ("rss_v3d_wsd", "v3d", ["--steps-per-epoch", "2500", "--lr-schedule", "wsd"])]


def fit_slope(pts):
    n = len(pts); mx = sum(s for s, _ in pts) / n; my = sum(p for _, p in pts) / n
    return sum((s - mx) * (p - my) for s, p in pts) / sum((s - mx) ** 2 for s, _ in pts)


def rss_summary(out: Path) -> int:
    """Private-memory trace per case (sampled at every progress line, i.e. every ~0.5 s, with the step number).
    Pass: the run finished all 10,000 steps (trainer's own Finished line) and |least-squares slope| < 100 B/step over steps
    >= 1000 (preregistered; v3b's DirectML leak was ~24 KB/step). Also reported: the window after the first epoch's
    eval/save (steps >= 2600) and the one-time steps between samples."""
    rows = json.loads((out / "results.json").read_text(encoding="utf-8"))["rows"]
    summary = []
    for row in rows:
        name = row["name"]
        trace = json.loads((out / name / "child_result.json").read_text(encoding="utf-8"))["trace"]
        stdout = (out / name / "stdout.txt").read_text(encoding="utf-8")
        done = "steps/epoch=2,500 total=10,000 " in stdout and "Finished: 640,000 positions in " in stdout
        pts = [(t["step"], t["private"]) for t in trace if t["step"] >= 1000]
        late = [(t["step"], t["private"]) for t in trace if t["step"] >= 2600]
        jumps = [f"{a['step']}->{b['step']}: {(b['private'] - a['private']) / 2**10:+.0f} KiB" for a, b in zip(trace, trace[1:])
                 if b["private"] != a["private"]]
        summary.append({"case": name, "finished_10000_steps": done, "samples": len(trace), "samples_from_step_1000": len(pts),
                        "first_sample_step": trace[0]["step"], "last_sample_step": trace[-1]["step"],
                        "slope_bytes_per_step_from_1000": round(fit_slope(pts), 2) if len(pts) >= 5 else None,
                        "slope_bytes_per_step_from_2600": round(fit_slope(late), 3) if len(late) >= 5 else None,
                        "private_range_from_2600_kib": round((max(p for _, p in late) - min(p for _, p in late)) / 2**10, 1) if late else None,
                        "private_first_mib": round(trace[0]["private"] / 2**20, 2), "private_last_mib": round(trace[-1]["private"] / 2**20, 2),
                        "changes_between_samples": jumps,
                        "peak_private_mib": round(row["peak_private"] / 2**20, 2), "peak_wset_mib": round(row["peak_wset"] / 2**20, 2)})
        print(json.dumps(summary[-1]), flush=True)
    write_json(out / "rss_summary.json", summary)
    ok = len(summary) == 2 and all(s["finished_10000_steps"] and s["slope_bytes_per_step_from_1000"] is not None
                                   and abs(s["slope_bytes_per_step_from_1000"]) < 100 for s in summary)
    print(f"RESULT {'PASS' if ok else 'FAIL'} (flat = all 10,000 steps run and |slope| < 100 B/step over steps >= 1000; "
          "v3b's DirectML leak was ~24 KB/step)")
    return 0 if ok else 1


def rss(tag: str) -> int:
    inputs = verify_inputs()
    out = ROOT / "out" / tag
    out.mkdir(parents=True)
    adopted0 = len(adoption_lines())
    rows = []
    for name, trainer, extra in RSS_CASES:
        argv = base_argv()
        for opt in ("--shape", "--batch-size", "--epochs", "--warmup-steps", "--val-positions", "--log-every"):
            i = argv.index(opt); del argv[i:i + 2]
        row = run_case(out, name, trainer, resolve(out, [*argv, *RSS_COMMON, *extra]), adopted0, trace=True)
        rows.append(row)
        if row["status"] != "PASS":
            break
    write_json(out / "results.json", {"tag": tag, "inputs": inputs, "adoption_lines_before": adopted0, "rows": rows})
    if len(rows) != len(RSS_CASES) or any(r["status"] != "PASS" for r in rows):
        print("RESULT FAIL (a trace run did not finish)")
        return 1
    return rss_summary(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--stage", action="store_true")
    g.add_argument("--suite")
    g.add_argument("--compare")
    g.add_argument("--rss")
    g.add_argument("--rss-eval")
    g.add_argument("--child")
    a = ap.parse_args()
    if a.child:
        return child(Path(a.child))
    if a.stage:
        return stage()
    if a.suite:
        return suite(a.suite)
    if a.compare:
        return compare(a.compare)
    if a.rss_eval:
        return rss_summary(ROOT / "out" / a.rss_eval)
    return rss(a.rss)


if __name__ == "__main__":
    raise SystemExit(main())
