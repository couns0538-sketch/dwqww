"""S21: check the study's Python forward against the engine's own NNUE (forge::nnue::refresh/evaluate).

For each .inc: copies it as nnue_weights.inc next to a copy of the lock's src/nnue.cpp in a scratch dir, builds the
lock archive's nnue_check.cpp harness with the PC compiler flags (MSYS2 ucrt64 g++), runs it on "FEN | ..." lines and
compares its network cp with the Python forward of forge_sol_S21_int16range.py, truncated toward zero as the engine
does (engine STM cp = truncate(clamp(logit * 400 / 2.25, -30000, 30000))). Read-only on its inputs.

  python -I -B forge_sol_S21_engine_parity.py --nets a.inc ... --fens sample.txt --lock-tree <AL1 source tree>
      --harness <5_nnue/tools/nnue_check.cpp> --work F:/opus_scratch/sol_s21/engine_parity --out parity.json
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("s21", HERE / "forge_sol_S21_int16range.py")
s21 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s21)
GPP = r"C:\msys64\ucrt64\bin\g++.exe"
FLAGS = ["-std=c++20", "-O2", "-DNDEBUG", "-DFORGE_NNUE_HIDDEN=256", "-ffp-contract=off", "-fno-fast-math", "-march=znver5", "-static"]
BELOW_NORMAL = 0x00004000


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--nets", nargs="+", type=Path, required=True)
    ap.add_argument("--fens", type=Path, required=True)
    ap.add_argument("--lock-tree", type=Path, required=True)
    ap.add_argument("--harness", type=Path, required=True)
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    if args.out.exists():
        ap.error("--out must be a new file")
    codes, stm = s21.read_fen_text([args.fens])
    env = dict(os.environ, PATH=r"C:\msys64\ucrt64\bin;" + os.environ["PATH"])
    rows = []
    for inc in args.nets:
        work = args.work / inc.stem
        work.mkdir(parents=True, exist_ok=False)
        shutil.copyfile(inc, work / "nnue_weights.inc")
        shutil.copyfile(args.lock_tree / "src" / "nnue.cpp", work / "nnue.cpp")
        exe = work / "nnue_check.exe"
        src = args.lock_tree / "src"
        cmd = [GPP, *FLAGS, "-I" + str(args.lock_tree / "include"), str(args.harness), str(work / "nnue.cpp"),
               str(src / "bitboard.cpp"), str(src / "board.cpp"), str(src / "eval.cpp"), str(src / "eval_params.cpp"), "-o", str(exe)]
        build = subprocess.run(cmd, capture_output=True, text=True, env=env, creationflags=BELOW_NORMAL)
        if build.returncode != 0:
            raise SystemExit(build.stderr[-2000:])
        run = subprocess.run([str(exe), str(args.fens)], capture_output=True, text=True, creationflags=BELOW_NORMAL)
        engine_net = np.array([int(line.split()[0]) for line in run.stdout.splitlines() if line.strip() and line != "BAD"])
        net = s21.read_inc(inc)
        py = s21.network_cp(net, s21.accumulators(net, codes, stm), s21.accumulators(net, codes, 1 - stm))
        py_trunc = np.trunc(np.clip(py, -30000, 30000)).astype(np.int64)
        diff = py_trunc - engine_net
        rows.append({"net": inc.name, "md5": net["md5"], "positions": int(len(engine_net)), "harness_stderr": run.stderr.strip(),
                     "exact": int((diff == 0).sum()), "max_abs_diff_cp": int(np.abs(diff).max()),
                     "max_abs_untruncated_diff": float(np.abs(py - engine_net).max())})
        print(f"{inc.name}: {rows[-1]['exact']}/{rows[-1]['positions']} exact, max |diff| {rows[-1]['max_abs_diff_cp']} cp", flush=True)
    result = {"tool": "forge_sol_S21_engine_parity", "fens": str(args.fens), "lock_tree": str(args.lock_tree), "nets": rows,
              "pass": all(r["max_abs_diff_cp"] <= 1 and r["positions"] == len(codes) for r in rows)}
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
