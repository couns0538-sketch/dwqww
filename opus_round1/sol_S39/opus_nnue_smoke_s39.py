"""S39 CPU smoke runner for train_resid_v3c.py (v3b + fixed-size epochs, both options default off).

PC rules: the trainers run only as renamed copies in F:\\opus_scratch\\sol_S39 -- opus_nnue_smoke_s39_v3b.py (byte-identical
to the lock archive's train_resid_v3b.py, sha256 5cebba4d...) and opus_nnue_smoke_s39_v3c.py (byte-identical to
train_resid_v3c.py in this folder) with qa_adam_dml.py beside them -- imported by a --child process whose command line names
neither (the NNUE supervisor adopts python.exe processes whose command line matches train_resid*.py). CPU only, one Torch
thread, Idle priority, outputs only under F:\\opus_scratch\\sol_S39\\out\\<tag> (never runs_* / smoke_kb*). A run starts only
with >= 6 GiB available RAM and is stopped below it; the supervisor log is polled and any new "adopted running job" line stops
the suite. Data: the lock archive's data32_sample_50k (synthetic): every loss is a pipeline result, not a quality result.

  <venv python> -I -B opus_nnue_smoke_s39.py --stage            copy + pin-check the inputs into F:\\opus_scratch\\sol_S39
  <venv python> -I -B opus_nnue_smoke_s39.py --suite r1         smoke cases (seed 99, 2 epochs) into out\\r1
  <venv python> -I -B opus_nnue_smoke_s39.py --compare r1       acceptance checks on out\\r1 (acceptance.json + table)
  <venv python> -I -B opus_nnue_smoke_s39.py --rss t1           10k-step private-memory trace, v3b vs v3c on, into out\\t1
  <venv python> -I -B opus_nnue_smoke_s39.py --rss-eval t1      re-evaluate an existing trace (no training)
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
V3C_SRC = HERE / ("train_resid" + "_v3c.py")  # the deliverable (never run under this name)
LA = Path(r"D:\grok-pc-data\dwqww\.claude\worktrees\b\pkg\forge_LOCK_AL1_s198_FULL_20261026_1039\5_nnue")
SRC_V3B = LA / "trainers" / "cpu_smoke" / ("train_resid" + "_v3b.py")
SRC_ADAM = LA / "trainers" / "cpu_smoke" / "qa_adam_dml.py"
SRC_SAMPLE = LA / "sample_data" / "data32_sample" / "data32_sample_50k"
ROOT = Path(r"F:\opus_scratch\sol_S39")
TRAINERS = {"v3b": ROOT / "opus_nnue_smoke_s39_v3b.py", "v3c": ROOT / "opus_nnue_smoke_s39_v3c.py"}
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
    found = {"v3b_copy": sha256(TRAINERS["v3b"]), "v3c_copy": sha256(TRAINERS["v3c"]), "v3c_src": sha256(V3C_SRC),
             "qa_adam_dml": sha256(ADAM), "sample": {n: sha256(SAMPLE / n) for n in SAMPLE_PINS}}
    bad = []
    if found["v3b_copy"] != PIN_V3B:
        bad.append("v3b copy")
    if found["qa_adam_dml"] != PIN_ADAM:
        bad.append("qa_adam_dml")
    if found["v3c_copy"] != found["v3c_src"]:
        bad.append("v3c copy != train_resid_v3c.py in the job folder (re-run --stage)")
    bad += [n for n, h in found["sample"].items() if h != SAMPLE_PINS[n]]
    if bad:
        raise SystemExit("input check FAILED: " + ", ".join(bad))
    return found


def stage() -> int:
    if sha256(SRC_V3B) != PIN_V3B or sha256(SRC_ADAM) != PIN_ADAM:
        raise SystemExit("lock-archive trainer files differ from their pins")
    SAMPLE.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    for name, pin in SAMPLE_PINS.items():
        if not (SAMPLE / name).exists():
            if sha256(SRC_SAMPLE / name) != pin:
                raise SystemExit(f"lock-archive sample differs from its pin: {name}")
            shutil.copyfile(SRC_SAMPLE / name, SAMPLE / name)
    for dst, src in ((TRAINERS["v3b"], SRC_V3B), (ADAM, SRC_ADAM)):
        if not dst.exists():
            shutil.copyfile(src, dst)
    if not TRAINERS["v3c"].exists() or sha256(TRAINERS["v3c"]) != sha256(V3C_SRC):
        if TRAINERS["v3c"].exists():  # keep the previous copy (no deletes): rename it by its sha256 prefix
            TRAINERS["v3c"].rename(ROOT / f"prev_{sha256(TRAINERS['v3c'])[:12]}_{TRAINERS['v3c'].name}.txt")
        shutil.copyfile(V3C_SRC, TRAINERS["v3c"])
    found = verify_inputs()
    write_json(ROOT / "inputs_receipt.json", {"status": "PASS_STAGED", **found, "v3b_source": str(SRC_V3B),
                                               "v3c_md5": md5(TRAINERS["v3c"]), "v3b_md5": md5(TRAINERS["v3b"])})
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


ON_U = ["--epoch-positions", "100000"]
ON_W = ["--epoch-positions", "100000", "--recent-weight", "3"]
SUITE = [("v3b_1", "v3b", []), ("v3b_2", "v3b", []), ("off_1", "v3c", []), ("off_2", "v3c", []),
         ("eqN", "v3c", ["--epoch-positions", "200000"]),
         ("gtN_w3", "v3c", ["--epoch-positions", "10000000", "--recent-weight", "3"]),
         ("on_u_1", "v3c", ON_U), ("on_u_2", "v3c", ON_U), ("on_w_1", "v3c", ON_W), ("on_w_2", "v3c", ON_W),
         ("on_w_ob2", "v3c", [*ON_W, "--order-buffers", "2"]),
         ("on_u_res", "v3c", [*ON_U, "--resume", "@on_u_1/epoch001"]),
         ("on_w_res", "v3c", [*ON_W, "--resume", "@on_w_1/epoch001"]),
         ("v3b_res", "v3b", ["--resume", "@v3b_1/epoch001"])]


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

    def same_artifacts(a, b, only=None):
        A = {k: v["sha256"] for k, v in R[a]["artifacts"].items() if only is None or k.startswith(only)}
        B = {k: v["sha256"] for k, v in R[b]["artifacts"].items() if only is None or k.startswith(only)}
        return A == B and len(A) > 0, len(A)

    def loss_lines(name, keep=("BASELINE", "INIT", "EPOCH", "FINAL")):
        return [x for x in R[name]["stdout_normalized"] if x.startswith(keep)]

    def info(name):
        return [x for x in R[name]["stdout_normalized"] if x.startswith("epoch-positions")]

    def without_info(name):
        return [x for x in R[name]["stdout_normalized"] if not x.startswith("epoch-positions")]

    ok, n = same_artifacts("v3b_1", "v3b_2")
    check("v3b reproducible (v3b_1 == v3b_2)", ok and R["v3b_1"]["stdout_normalized"] == R["v3b_2"]["stdout_normalized"],
          f"{n} artifacts (.pt .inc .bin .json x 2 epochs) sha256-equal: {ok}; normalized stdout equal: {R['v3b_1']['stdout_normalized'] == R['v3b_2']['stdout_normalized']}")
    for c in ("off_1", "off_2"):
        ok, n = same_artifacts("v3b_1", c)
        same_out = R[c]["stdout_normalized"] == R["v3b_1"]["stdout_normalized"]
        same_set = R[c]["settings_json"] == R["v3b_1"]["settings_json"] and R[c]["settings_argv"] == R["v3b_1"]["settings_argv"]
        check(f"options OFF == v3b ({c} vs v3b_1)", ok and same_out and same_set,
              f"{n} artifacts sha256-equal: {ok}; full normalized stdout equal: {same_out}; settings dump equal: {same_set}")
    for c, line in (("eqN", "epoch-positions 200,000 >= train 200,000: full epochs (v3b order)"),
                    ("gtN_w3", "epoch-positions 10,000,000 >= train 200,000: full epochs (v3b order; recent-weight has no effect)")):
        ok, n = same_artifacts("v3b_1", c)
        same = without_info(c) == R["v3b_1"]["stdout_normalized"] and info(c) == [line]
        check(f"N >= data size == v3b ({c})", ok and same, f"{n} artifacts sha256-equal: {ok}; stdout equal apart from the one line '{line}': {same}")
    for a, b in (("on_u_1", "on_u_2"), ("on_w_1", "on_w_2")):
        ok, n = same_artifacts(a, b)
        same = R[a]["stdout_normalized"] == R[b]["stdout_normalized"]
        md5s = R[a]["artifacts"]
        check(f"ON deterministic ({a} == {b})", ok and same,
              f"{n} artifacts sha256-equal: {ok} (ep2 .inc md5 {[v['md5'] for k, v in md5s.items() if k.startswith('epoch002') and k.endswith('.inc')]}); stdout equal: {same}")
    for c in ("on_u_1", "on_w_1"):
        out = R[c]["stdout_normalized"]
        steps = [x for x in out if x.startswith("steps/epoch=")]
        fin = [x for x in out if x.startswith("Finished:")]
        js = json.loads((ROOT / "out" / tag / c / "run" / [k for k in R[c]["artifacts"] if k.startswith("epoch002") and k.endswith(".json")][0]).read_text())
        ok = steps and steps[0].startswith("steps/epoch=97 total=194 ") and fin == ["Finished: 198,656 positions in Xs"] \
            and js.get("epoch_positions") == 100000
        check(f"ON fixed epoch size ({c})", bool(ok), f"{steps[0] if steps else '?'} | {fin[0] if fin else '?'} | .json epoch_positions={js.get('epoch_positions')} recent_weight={js.get('recent_weight')}")
    w_info = info("on_w_1")
    check("recent-weight 3 per-file draw plan", w_info[-1:] == ["epoch-positions per file (weight drawn/rows): t00000.pos 1.0000 12,500/50,000, "
                                                              "t01000.pos 1.6667 20,833/50,000, t02000.pos 2.3333 29,167/50,000, "
                                                              "t03000.pos 3.0000 37,500/50,000"], w_info[-1] if w_info else "missing")

    def inc(name, ep="epoch002"):
        return [v["sha256"] for k, v in R[name]["artifacts"].items() if k.startswith(ep) and k.endswith(".inc")]
    check("ON changes the training (sanity: the comparisons can fail)", inc("on_u_1") != inc("v3b_1") and inc("on_w_1") != inc("on_u_1"),
          "ep2 .inc of on_u_1 != v3b_1 and on_w_1 != on_u_1")
    ok, n = same_artifacts("on_w_1", "on_w_ob2")
    check("--order-buffers 2 == 1 with recent-weight (on_w_ob2 == on_w_1)", ok, f"{n} artifacts sha256-equal: {ok}")
    for res, src in (("on_u_res", "on_u_1"), ("on_w_res", "on_w_1"), ("v3b_res", "v3b_1")):
        A = {k: v["sha256"] for k, v in R[src]["artifacts"].items() if k.startswith("epoch002")}
        B = {k: v["sha256"] for k, v in R[res]["artifacts"].items() if k.startswith("epoch002")}
        same3 = sorted(A) == sorted(B) and len(A) == 4 and all(A[k] == B[k] for k in A if not k.endswith(".pt"))
        pt = [k for k in A if k.endswith(".pt")]
        diff = pt_content_diff(ROOT / "out" / tag / src / "run" / pt[0], ROOT / "out" / tag / res / "run" / pt[0]) if pt else ["missing"]
        e2 = [x for x in loss_lines(src) if x.startswith("EPOCH 2/")] == [x for x in loss_lines(res) if x.startswith("EPOCH 2/")]
        what = "v3b's own resume (reference)" if res == "v3b_res" else "v3c"
        check(f"resume from epoch 1 reproduces epoch 2 ({res} vs {src}, {what})", same3 and not diff and e2,
              f".inc .bin .json sha256-equal: {same3}; .pt content bitwise-equal: {not diff} {diff[:3]}; .pt bytes equal: "
              f"{A.get(pt[0]) == B.get(pt[0]) if pt else None} (pickle memo/serialization_id, see finding); EPOCH 2 line equal: {e2}")
    peaks = {c: (R[c].get("peak_private", 0), R[c].get("peak_wset", 0)) for c in R}
    base_priv = max(peaks["v3b_1"][0], peaks["v3b_2"][0]); base_wset = max(peaks["v3b_1"][1], peaks["v3b_2"][1])
    spread = max(abs(peaks["v3b_1"][0] - peaks["v3b_2"][0]), abs(peaks["v3b_1"][1] - peaks["v3b_2"][1]))
    tol = max(spread, 2**20)  # allocator noise: v3b's own run-to-run spread, at least 1 MiB
    worst = max(max(peaks[c][0] - base_priv, peaks[c][1] - base_wset) for c in ("on_u_1", "on_u_2", "on_w_1", "on_w_2"))
    check("peak memory of ON runs no higher than v3b (tolerance: v3b's own run-to-run spread, >= 1 MiB)", worst <= tol,
          "MiB peak private/peak working set: " + ", ".join(f"{c} {p / 2**20:.1f}/{w / 2**20:.1f}" for c, (p, w) in peaks.items())
          + f"; worst ON excess over max(v3b) {worst / 2**20:+.2f} MiB, tolerance {tol / 2**20:.2f} MiB")
    check("no new supervisor adoption", all(r.get("adoption_lines") == data["adoption_lines_before"] for r in data["rows"]),
          f"'adopted running job' lines before {data['adoption_lines_before']}, after each run "
          f"{sorted({r.get('adoption_lines') for r in data['rows']})}")
    write_json(ROOT / "out" / tag / "acceptance.json", checks)
    print("| check | result | detail |\n|---|---|---|")
    for c in checks:
        print(f"| {c['item']} | **{c['result']}** | {c['detail']} |")
    print("RESULT " + ("PASS" if all(c["result"] == "PASS" for c in checks) else "FAIL") + f" {sum(c['result'] == 'PASS' for c in checks)}/{len(checks)}")
    print("loss lines v3b_1 / on_u_1 / on_w_1:")
    for c in ("v3b_1", "on_u_1", "on_w_1"):
        for x in loss_lines(c):
            print(f"  {c}: {x}")
    return 0 if all(c["result"] == "PASS" for c in checks) else 1


# --------------------------------------------------------------------------------------------------- rss
RSS_COMMON = ["--shape", "32", "--batch-size", "64", "--epochs", "4", "--warmup-steps", "100", "--val-positions", "8192",
              "--log-every", "0.5"]


RSS_CASES = [("rss_v3b", "v3b", ["--steps-per-epoch", "2500"]),
             ("rss_v3c_on", "v3c", ["--epoch-positions", "160000", "--recent-weight", "3"])]


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
        row = run_case(out, name, trainer, [*argv, *RSS_COMMON, *extra], adopted0, trace=True)
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
