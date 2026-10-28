"""S-A2 CPU smoke runner for trainer_v3c_clip.py (v3c + --weight-clip, default off).

PC rules: the trainers run only as renamed copies in F:\\opus_scratch\\sol_SA2 -- opus_nnue_smoke_sa2_v3c.py (byte-identical
to the S50 v3c, opus-sol-S50 ff98828a, sha256 ddff28bb...) and opus_nnue_smoke_sa2_clip.py (byte-identical to
trainer_v3c_clip.py in this folder) with qa_adam_dml.py beside them -- imported by a --child process whose command line names
neither. CPU only, one Torch thread, Idle priority, outputs only under F:\\opus_scratch\\sol_SA2\\out\\<tag> (never runs_* /
smoke_kb*). A run starts only with >= 6 GiB available RAM and is stopped below it; the supervisor log is polled and any new
"adopted running job" line stops the suite. Data: the lock archive's data32_sample_50k (synthetic): every loss is a pipeline
result, not a quality result.

  <venv python> -I -B opus_nnue_smoke_sa2.py --stage          copy + pin-check the inputs into F:\\opus_scratch\\sol_SA2
  <venv python> -I -B opus_nnue_smoke_sa2.py --suite r1       smoke cases (seed 99, H64, 2 epochs) into out\\r1
  <venv python> -I -B opus_nnue_smoke_sa2.py --compare r1     acceptance checks on out\\r1 (acceptance.json + table)
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
CLIP_SRC = HERE / "trainer_v3c_clip.py"
S50 = Path(r"F:\opus_scratch\worktrees\opus_sol_s50\opus_round1\sol_S50")
SRC_V3C = S50 / ("train_resid" + "_v3c.py")  # read only; never run under this name
LA = Path(r"D:\grok-pc-data\dwqww\.claude\worktrees\b\pkg\forge_LOCK_AL1_s198_FULL_20261026_1039\5_nnue")
SRC_ADAM = LA / "trainers" / "cpu_smoke" / "qa_adam_dml.py"
SRC_SAMPLE = LA / "sample_data" / "data32_sample" / "data32_sample_50k"
ROOT = Path(r"F:\opus_scratch\sol_SA2")
TRAINERS = {"v3c": ROOT / "opus_nnue_smoke_sa2_v3c.py", "clip": ROOT / "opus_nnue_smoke_sa2_clip.py"}
ADAM = ROOT / "qa_adam_dml.py"
SAMPLE = ROOT / "inputs" / "data32_sample_50k"
TMP = ROOT / "tmp"
SUPERVISOR_LOG = Path(r"F:\forge_nnue_train\supervisor.log")
SHARDS = ("t00000", "t01000", "t02000", "t03000")
PIN_V3C = "ddff28bb6801421793e1767cec8271fe3406a263b0c0dfec03ac0cd97dcadef8"  # opus-sol-S50 ff98828a, md5 e7fefe77
PIN_ADAM = "799faa89bc7b8dbd8c9a8747dd6658085eb0a69b84800af191db5ca7fd660cba"
SAMPLE_PINS = {  # = opus-sol-S18/S50 pins of the same lock-archive sample
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
TIMING = [(re.compile(r"\((\d+)s\)$"), "(Xs)"), (re.compile(r"\((\d+)s load\)$"), "(Xs load)"),
          (re.compile(r" done in \d+s "), " done in Xs "), (re.compile(r" in \d+s$"), " in Xs")]


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def md5(path: Path) -> str:
    return hashlib.md5(Path(path).read_bytes()).hexdigest()


def write_json(path: Path, value) -> None:
    Path(path).write_text(json.dumps(value, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


class _MSX(ctypes.Structure):
    _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong)] + [(f, ctypes.c_ulonglong) for f in (
        "ullTotalPhys", "ullAvailPhys", "ullTotalPageFile", "ullAvailPageFile", "ullTotalVirtual", "ullAvailVirtual",
        "ullAvailExtendedVirtual")]


def avail_ram() -> int:
    ms = _MSX(); ms.dwLength = ctypes.sizeof(_MSX)
    ctypes.WinDLL("kernel32").GlobalMemoryStatusEx(ctypes.byref(ms))
    return int(ms.ullAvailPhys)


def adoption_lines() -> list[str]:
    if not SUPERVISOR_LOG.exists():
        return []
    return [x for x in SUPERVISOR_LOG.read_bytes().decode("utf-8", "replace").splitlines() if "adopted running job" in x]


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module


def normalize(stdout: str) -> list[str]:
    """Trainer stdout without MEM lines and with the wall-clock fields replaced."""
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
    found = {"v3c_copy": sha256(TRAINERS["v3c"]), "clip_copy": sha256(TRAINERS["clip"]), "clip_src": sha256(CLIP_SRC),
             "qa_adam_dml": sha256(ADAM), "sample": {n: sha256(SAMPLE / n) for n in SAMPLE_PINS}}
    bad = []
    if found["v3c_copy"] != PIN_V3C:
        bad.append("v3c copy")
    if found["qa_adam_dml"] != PIN_ADAM:
        bad.append("qa_adam_dml")
    if found["clip_copy"] != found["clip_src"]:
        bad.append("clip copy != trainer_v3c_clip.py in the job folder (re-run --stage)")
    bad += [n for n, h in found["sample"].items() if h != SAMPLE_PINS[n]]
    if bad:
        raise SystemExit("input check FAILED: " + ", ".join(bad))
    return found


def stage() -> int:
    if sha256(SRC_V3C) != PIN_V3C or sha256(SRC_ADAM) != PIN_ADAM:
        raise SystemExit("source trainer files differ from their pins")
    SAMPLE.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    for name, pin in SAMPLE_PINS.items():
        if not (SAMPLE / name).exists():
            if sha256(SRC_SAMPLE / name) != pin:
                raise SystemExit(f"lock-archive sample differs from its pin: {name}")
            shutil.copyfile(SRC_SAMPLE / name, SAMPLE / name)
    for dst, src in ((TRAINERS["v3c"], SRC_V3C), (ADAM, SRC_ADAM)):
        if not dst.exists():
            shutil.copyfile(src, dst)
    if not TRAINERS["clip"].exists() or sha256(TRAINERS["clip"]) != sha256(CLIP_SRC):
        if TRAINERS["clip"].exists():  # keep the previous copy (no deletes): rename it by its sha256 prefix
            TRAINERS["clip"].rename(ROOT / f"prev_{sha256(TRAINERS['clip'])[:12]}_{TRAINERS['clip'].name}.txt")
        shutil.copyfile(CLIP_SRC, TRAINERS["clip"])
    found = verify_inputs()
    write_json(ROOT / "inputs_receipt.json", {"status": "PASS_STAGED", **found, "v3c_source": str(SRC_V3C),
                                               "clip_md5": md5(TRAINERS["clip"]), "v3c_md5": md5(TRAINERS["v3c"])})
    print(json.dumps(found, indent=1))
    print("RESULT PASS_STAGED")
    return 0


# ------------------------------------------------------------------------------------------------- child
def child(case_dir: Path) -> int:
    case = json.loads((case_dir / "case.json").read_text(encoding="utf-8"))
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    trainer = load_module(Path(case["trainer"]))
    sys.argv = [case["trainer"], *case["argv"]]
    t0 = time.time()
    rc = trainer.main()
    sys.stdout.flush()
    write_json(case_dir / "child_result.json", {"rc": rc, "seconds": round(time.time() - t0, 2), "torch": torch.__version__,
                                                 "threads": torch.get_num_threads()})
    return int(rc or 0)


# ------------------------------------------------------------------------------------------------ parent
def child_env() -> dict:
    return dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1",
                TMP=str(TMP), TEMP=str(TMP))


def run_case(out: Path, name: str, trainer: str, argv: list[str], adopted0: int) -> dict:
    case_dir = out / name
    case_dir.mkdir(parents=True)
    run_dir = case_dir / "run"
    full_argv = [*argv, "--run-dir", str(run_dir)]
    write_json(case_dir / "case.json", {"name": name, "trainer": str(TRAINERS[trainer]), "argv": full_argv})
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
    files = sorted(run_dir.iterdir()) if run_dir.exists() else []
    row["artifacts"] = {p.name: {"sha256": sha256(p), "md5": md5(p), "bytes": p.stat().st_size}
                        for p in files if not p.name.startswith("settings_")}
    settings = [p for p in files if p.name.startswith("settings_")]
    if settings:  # the trainer path and this case's run dir differ between cases by design
        head, body = settings[0].read_text(encoding="utf-8").split("\n", 1)
        row["settings_argv"] = head.replace(str(TRAINERS[trainer]), "<trainer>").replace(str(run_dir), "<run>")
        row["settings_json"] = body.replace(json.dumps(str(run_dir))[1:-1], "<run>")
    row["status"] = stop or ("PASS" if rc == 0 else "FAIL")
    print(f"{name:10s} {trainer} {row['status']} rc={rc} {row['seconds']} s min_avail={row['min_avail_gib']} GiB", flush=True)
    return row


def base_argv(extra=()) -> list[str]:
    return ["--train", *[str(SAMPLE / f"{s}.pos") for s in SHARDS], "--holdout", str(SAMPLE / "h000.pos"),
            "--hce-dir", str(SAMPLE), "--device", "cpu", "--residual", "--init-check", "--final-full-val",
            "--log-every", "1e9", "--shape", "64", "--epochs", "2", "--lr", "7.07e-4", "--blend-end", "0.6", "--seed", "99",
            "--batch-size", "1024", "--warmup-steps", "20", "--val-positions", "16384", *extra]


TIGHT = ["--weight-clip", "0.05"]  # K = floor(0.05 * 4096) = 204: binds on this smoke
SUITE = [("v3c_1", "v3c", []), ("off_1", "clip", []), ("off_2", "clip", []),
         ("on_1", "clip", ["--weight-clip"]), ("on_2", "clip", ["--weight-clip"]),
         ("tight_1", "clip", TIGHT), ("tight_2", "clip", TIGHT),
         ("tight_res", "clip", [*TIGHT, "--resume", "@tight_1/epoch001"]),
         ("tight_warm", "clip", [*TIGHT, "--init-weights", "@v3c_1/epoch002", "--epochs", "1"])]


def resolve(out: Path, argv: list[str]) -> list[str]:
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
    print(f"supervisor 'adopted running job' lines before: {adopted0}", flush=True)
    rows = []
    for name, trainer, extra in SUITE:
        row = run_case(out, name, trainer, resolve(out, base_argv(extra)), adopted0)
        rows.append(row)
        if row["status"] != "PASS":
            break
    print(f"supervisor 'adopted running job' lines after: {len(adoption_lines())}", flush=True)
    write_json(out / "results.json", {"tag": tag, "inputs": inputs, "adoption_lines_before": adopted0,
                                      "adoption_lines_after": len(adoption_lines()), "rows": rows})
    return 0 if all(r["status"] == "PASS" for r in rows) and len(rows) == len(SUITE) else 1


# ----------------------------------------------------------------------------------------------- compare
def read_inc(path: Path) -> dict:
    text = path.read_text(encoding="ascii")
    arrays = {}
    for name in ("NnueW1", "NnueB1", "NnueW2"):
        m = re.search(name + r"\[(\d+)\]\s*=\s*\{([^}]*)\}", text, re.S)
        arrays[name] = [int(x) for x in m.group(2).replace("\n", " ").split(",") if x.strip()]
    arrays["NnueB2"] = [int(re.search(r"NnueB2\s*=\s*(-?\d+)", text).group(1))]
    return arrays


def compare(tag: str) -> int:
    import torch
    sys.path.insert(0, str(HERE))
    data = json.loads((ROOT / "out" / tag / "results.json").read_text(encoding="utf-8"))
    R = {r["name"]: r for r in data["rows"]}
    checks = []

    def check(item, ok, detail):
        checks.append({"item": item, "result": "PASS" if ok else "FAIL", "detail": detail})

    def arts(name, only=None, ext=None):
        return {k: v["sha256"] for k, v in R[name]["artifacts"].items()
                if (only is None or k.startswith(only)) and (ext is None or k.endswith(ext))}

    def run_of(name):
        return ROOT / "out" / tag / name / "run"

    def pt_content(name, stem):
        p = sorted(run_of(name).glob(stem + "-*.pt"))[0]
        return torch.load(p, map_location="cpu", weights_only=True)

    # 1. off == v3c, byte for byte
    for c in ("off_1", "off_2"):
        a, b = arts("v3c_1"), arts(c)
        same = a == b and len(a) == 8
        same_out = R[c]["stdout_normalized"] == R["v3c_1"]["stdout_normalized"]
        same_set = R[c]["settings_json"] == R["v3c_1"]["settings_json"] and R[c]["settings_argv"] == R["v3c_1"]["settings_argv"]
        check(f"clip off == v3c byte-identical ({c} vs v3c_1)", same and same_out and same_set,
              f"{len(a)} artifacts (.pt .inc .bin .json x 2 epochs) sha256-equal: {same}; normalized stdout equal: {same_out}; "
              f"settings dump equal: {same_set}")
    # 2. deterministic ON
    for x, y in (("on_1", "on_2"), ("tight_1", "tight_2")):
        same = arts(x) == arts(y) and len(arts(x)) == 8 and R[x]["stdout_normalized"] == R[y]["stdout_normalized"]
        check(f"clip on deterministic ({x} == {y})", same, f"8 artifacts sha256-equal and normalized stdout equal: {same}")
    # 3. every export of every clip-on run within its bound, nothing at the int16 rail, INT16 CHECK line per epoch
    import numpy as np
    for name, units in (("on_1", 21704), ("on_2", 21704), ("tight_1", 204), ("tight_2", 204), ("tight_res", 204), ("tight_warm", 204)):
        incs = sorted(run_of(name).glob("*.inc"))
        lines = [x for x in R[name]["stdout_normalized"] if x.startswith("INT16 CHECK")]
        worst, rail, at_bound = 0, 0, {}
        for inc in incs:
            arr = read_inc(inc)
            for k, v in arr.items():
                v = np.abs(np.asarray(v, np.int64))
                worst = max(worst, int(v.max()))
                rail += int((v >= 32767).sum())
                at_bound[k] = at_bound.get(k, 0) + int((v == units).sum())
        ok = incs and worst <= units and rail == 0 and len(lines) == len(incs)
        check(f"no exported weight saturates ({name}, bound {units})", bool(ok),
              f"{len(incs)} .inc: max|q| {worst} <= {units}; values at the int16 rail: {rail}; values at the clip bound: {at_bound}; "
              f"INT16 CHECK lines: {len(lines)}" + (f" | {lines[-1]}" if lines else ""))
    # 4. the default bound does not bind on this smoke: weights equal the off run; only the config records the clip
    same_w = arts("on_1", ext=".inc") == arts("off_1", ext=".inc") and arts("on_1", ext=".bin") == arts("off_1", ext=".bin")
    pt_on, pt_off = pt_content("on_1", "epoch002"), pt_content("off_1", "epoch002")
    model_same = all(torch.equal(pt_on["model"][k], pt_off["model"][k]) for k in pt_off["model"])
    extra_keys = sorted(set(pt_on["config"]) - set(pt_off["config"]))
    check("default bound (K 21704) not binding here: .inc/.bin == off, config adds only weight_clip_units",
          same_w and model_same and extra_keys == ["weight_clip_units"] and pt_on["config"]["weight_clip_units"] == 21704,
          f".inc/.bin sha256 equal to off_1: {same_w}; .pt model tensors equal: {model_same}; extra config keys {extra_keys}")
    # 5. the tight bound binds (the comparison can fail) and the parameters sit inside it
    pt_t = pt_content("tight_1", "epoch002")
    bound = 204 / 4096
    inside = all(float(t.abs().max()) <= bound for t in pt_t["model"].values())
    pinned = {k: int((t.abs() == bound).sum()) for k, t in pt_t["model"].items()}
    check("tight bound (K 204) binds and holds in the checkpoint", inside and pinned["ft.weight"] > 0 and arts("tight_1", ext=".inc") != arts("off_1", ext=".inc"),
          f"all |param| <= 204/4096: {inside}; params exactly at the bound: {pinned}; .inc differs from off: "
          f"{arts('tight_1', ext='.inc') != arts('off_1', ext='.inc')}")
    # 6. resume reproduces the clipped run's epoch 2
    a, b = arts("tight_1", only="epoch002"), arts("tight_res", only="epoch002")
    same3 = sorted(a) == sorted(b) and all(a[k] == b[k] for k in a if not k.endswith(".pt"))
    pa, pb = pt_content("tight_1", "epoch002"), pt_content("tight_res", "epoch002")
    same_pt = all(torch.equal(pa["model"][k], pb["model"][k]) for k in pa["model"]) and pa["config"] == pb["config"]
    check("resume with the clip reproduces epoch 2 (tight_res vs tight_1)", same3 and same_pt,
          f".inc .bin .json sha256-equal: {same3}; .pt model + config equal: {same_pt}")
    # 7. warm start from an unclipped net: the first step clips it
    lines = [x for x in R["tight_warm"]["stdout_normalized"] if x.startswith(("init-weights", "INIT", "INT16 CHECK"))]
    check("warm start (unclipped v3c net) + clip: export within the bound", R["tight_warm"]["status"] == "PASS" and any("INT16 CHECK" in x for x in lines),
          " | ".join(lines)[:600])
    check("supervisor: no new 'adopted running job' line", data["adoption_lines_after"] == data["adoption_lines_before"],
          f"before {data['adoption_lines_before']} after {data['adoption_lines_after']}")
    ok = all(c["result"] == "PASS" for c in checks)
    write_json(ROOT / "out" / tag / "acceptance.json", {"tag": tag, "pass": ok, "checks": checks})
    print("| check | result | detail |\n|---|---|---|")
    for c in checks:
        print(f"| {c['item']} | {c['result']} | {c['detail']} |")
    print("ACCEPTANCE PASS" if ok else "ACCEPTANCE FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--stage", action="store_true")
    g.add_argument("--suite")
    g.add_argument("--compare")
    g.add_argument("--child", type=Path)
    a = ap.parse_args()
    if a.stage:
        return stage()
    if a.suite:
        return suite(a.suite)
    if a.compare:
        return compare(a.compare)
    return child(a.child)


if __name__ == "__main__":
    sys.exit(main())
