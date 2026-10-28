"""S-A4 CPU smoke: an H512 net from trainer_v3c_clip.py (opus_round1/sol_SA2, `--shape 512 --weight-clip`), trained twice.

Reuses opus_round1/sol_SA2/opus_nnue_smoke_sa2.py (staging with pins, renamed copies, --child processes at Idle priority,
>= 6 GiB RAM floor, supervisor-log watch) with its own scratch root F:\\opus_scratch\\sol_SA4: the trainer runs only as
F:\\opus_scratch\\sol_SA4\\opus_nnue_smoke_sa4_clip.py (byte-identical to trainer_v3c_clip.py), CPU, one Torch thread,
outputs only under F:\\opus_scratch\\sol_SA4\\out\\<tag>. Data: the lock archive's data32_sample_50k (synthetic): the net is
a pipeline artifact for engine support, parity and NPS, not a playing-strength net.

  <venv python> -I -B opus_nnue_smoke_sa4.py --stage
  <venv python> -I -B opus_nnue_smoke_sa4.py --suite r1      (h512_1, h512_2: seed 99, H512, 2 epochs, --weight-clip)
  <venv python> -I -B opus_nnue_smoke_sa4.py --compare r1
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SA2_RUNNER = HERE.parent / "sol_SA2" / "opus_nnue_smoke_sa2.py"


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module


base = load_module(SA2_RUNNER)
ROOT = Path(r"F:\opus_scratch\sol_SA4")
base.ROOT = ROOT
base.TRAINERS = {"v3c": ROOT / "opus_nnue_smoke_sa4_v3c.py", "clip": ROOT / "opus_nnue_smoke_sa4_clip.py"}
base.ADAM = ROOT / "qa_adam_dml.py"
base.SAMPLE = ROOT / "inputs" / "data32_sample_50k"
base.TMP = ROOT / "tmp"
H512 = ["--shape", "512", "--weight-clip"]
NETS = ROOT / "nets"
LR0 = ["--lr", "0", "--epochs", "1", "--steps-per-epoch", "2", "--weight-clip"]
SUITES = {  # tag prefix "w": warm-start suite (widened lock nets at lr 0), otherwise the H512 smoke suite
    "r": [("h512_1", "clip", H512), ("h512_2", "clip", H512)],
    "w": [("lock256_lr0", "clip", ["--shape", "256", "--init-weights", str(NETS / "lock_h256_copy.pt"), *LR0]),
          ("warm_zero_lr0", "clip", ["--shape", "512", "--init-weights", str(NETS / "h512_widened_lock_zero.pt"), *LR0]),
          ("warm_split_lr0", "clip", ["--shape", "512", "--init-weights", str(NETS / "h512_widened_lock_split.pt"), *LR0])]}
CLIP_UNITS = 21704


def compare_warm(tag: str) -> int:
    """lr 0 warm starts: the widened H512 nets have the lock's holdout loss and export unchanged."""
    data = json.loads((ROOT / "out" / tag / "results.json").read_text(encoding="utf-8"))
    R = {r["name"]: r for r in data["rows"]}
    checks = []

    def check(item, ok, detail):
        checks.append({"item": item, "result": "PASS" if ok else "FAIL", "detail": detail})

    def lines(name, prefix):
        return [x for x in R[name]["stdout_normalized"] if x.startswith(prefix)]

    def numbers(line):
        return re.findall(r"(mse_[\w.]+=[0-9.]+)", line.split("(")[0] if line.startswith("INIT") else line.split("|")[0])

    init = {n: lines(n, "INIT warm-start net") for n in R}
    final = {n: lines(n, "FINAL FULL HOLDOUT") for n in R}
    ref_i, ref_f = numbers(init["lock256_lr0"][0]), numbers(final["lock256_lr0"][0])
    for n in ("warm_zero_lr0", "warm_split_lr0"):
        same = numbers(init[n][0]) == ref_i and numbers(final[n][0]) == ref_f
        check(f"{n}: holdout loss == the lock's (function-preserving widening)", same,
              f"INIT {numbers(init[n][0])} vs lock {ref_i}; FINAL {numbers(final[n][0])} vs lock {ref_f}")
    for n, src in (("lock256_lr0", "lock_h256_copy.inc"), ("warm_zero_lr0", "h512_widened_lock_zero.inc"),
                   ("warm_split_lr0", "h512_widened_lock_split.inc")):
        inc = sorted((ROOT / "out" / tag / n / "run").glob("*.inc"))[0]
        a, b = base.read_inc(inc), base.read_inc(NETS / src)
        same = all(a[k] == b[k] for k in a)
        check(f"{n}: lr-0 export == {src} (warm-start pipeline is exact)", same, f"{inc.name}: arrays equal {same}")
    check("supervisor: no new 'adopted running job' line", data["adoption_lines_after"] == data["adoption_lines_before"],
          f"before {data['adoption_lines_before']} after {data['adoption_lines_after']}")
    ok = all(c["result"] == "PASS" for c in checks)
    base.write_json(ROOT / "out" / tag / "acceptance.json", {"tag": tag, "pass": ok, "checks": checks})
    print("| check | result | detail |\n|---|---|---|")
    for c in checks:
        print(f"| {c['item']} | {c['result']} | {c['detail']} |")
    print("ACCEPTANCE PASS" if ok else "ACCEPTANCE FAIL")
    return 0 if ok else 1


def compare(tag: str) -> int:
    data = json.loads((ROOT / "out" / tag / "results.json").read_text(encoding="utf-8"))
    R = {r["name"]: r for r in data["rows"]}
    checks = []

    def check(item, ok, detail):
        checks.append({"item": item, "result": "PASS" if ok else "FAIL", "detail": detail})

    def arts(name):
        return {k: v["sha256"] for k, v in R[name]["artifacts"].items()}

    a, b = arts("h512_1"), arts("h512_2")
    same = a == b and len(a) == 8 and R["h512_1"]["stdout_normalized"] == R["h512_2"]["stdout_normalized"]
    check("H512 smoke deterministic (h512_1 == h512_2)", same, f"{len(a)} artifacts sha256-equal and normalized stdout equal: {same}")
    import numpy as np
    for name in ("h512_1",):
        run = ROOT / "out" / tag / name / "run"
        for inc in sorted(run.glob("*.inc")):
            text = inc.read_text(encoding="ascii")
            shape_ok = "forge::nnue::HiddenSize == 512" in text and "NnueW1[393216]" in text and "NnueB1[512]" in text \
                and "NnueW2[1024]" in text and "#define FORGE_NNUE_RESIDUAL 1" in text
            arr = base.read_inc(inc)
            worst = max(int(np.abs(np.asarray(v, np.int64)).max()) for v in arr.values())
            rail = sum(int((np.abs(np.asarray(v, np.int64)) >= 32767).sum()) for v in arr.values())
            check(f"{inc.name}: H512 export shape and no saturation", shape_ok and worst <= CLIP_UNITS and rail == 0,
                  f"shape/residual lines ok: {shape_ok}; max|q| {worst} <= {CLIP_UNITS}; values at the int16 rail {rail}")
    lines = [x for x in R["h512_1"]["stdout_normalized"] if x.startswith(("INT16 CHECK", "EPOCH", "FINAL", "BASELINE", "INIT"))]
    check("trainer log: INIT CHECK OK, two epochs with INT16 CHECK lines",
          sum(x.startswith("INT16 CHECK") for x in lines) == 2 and sum(x.startswith("EPOCH") for x in lines) == 2
          and any(x.startswith("INIT CHECK OK") for x in lines), " | ".join(lines)[:1500])
    check("supervisor: no new 'adopted running job' line", data["adoption_lines_after"] == data["adoption_lines_before"],
          f"before {data['adoption_lines_before']} after {data['adoption_lines_after']}")
    ok = all(c["result"] == "PASS" for c in checks)
    base.write_json(ROOT / "out" / tag / "acceptance.json", {"tag": tag, "pass": ok, "checks": checks})
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
    a = ap.parse_args()
    if a.stage:
        return base.stage()
    if a.suite:
        base.SUITE = SUITES["w" if a.suite.startswith("w") else "r"]
        return base.suite(a.suite)
    return compare_warm(a.compare) if a.compare.startswith("w") else compare(a.compare)


if __name__ == "__main__":
    sys.exit(main())
