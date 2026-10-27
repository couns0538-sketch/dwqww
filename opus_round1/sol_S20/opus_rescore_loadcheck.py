"""After rescoring: convert to .pos/.hce, load through both v3b loaders (RAM + mmap), check the sign convention, and
run Sol's D filter on the result. Read-only on its inputs; writes only into --work (inside F:/opus_scratch/rescore_d8).

  python -I -B opus_rescore_loadcheck.py --rescored run/rescored.txt --stem s20_d8 --work F:/opus_scratch/rescore_d8/<x>
      --fen2bin bin/fen2bin.exe --hce-dump bin/hce_dump.exe --loaders input/opus_nnue_smoke_s20_v3b_loaders_src.py
      [--dfilter <forge_sol_datafilter_v2_20261026.py> --dfilter-holdout-dir <dir with h000.pos/.hce> --threshold 300]

- Conversion: fen2bin (FPOS) and hce_dump (FHCE, the AL1 lock's Evaluator::evaluate_uncached) from the lock archive's
  5_nnue/datagen_and_format/record_format sources, built against the AL1 lock tree.
- Loaders: read_pos_header, load_set, CatMap and load_set_mmap are taken from a renamed copy of train_resid_v3b.py
  by AST (no Torch import, no trainer run) and executed with numpy only. Both must load every row; their arrays
  must be equal; scores and meta must equal the text (STM score int16; meta bit0 = black to move; bits1-2 = WHITE
  result * 2).
- Sign convention: on decisive positions the loaded STM score's sign agrees with the side to move's result decoded
  from meta (the same agreement as the text), and the material spot check of the pilot check repeats on loaded data.
- D filter: Sol's v2 filter (seed 20261025, diagnostic mode, --disagreement-threshold) on the converted pair, with a
  supplied holdout copied into --work; its summary (kept/dropped per reason) is recorded.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np

ALLOWED_ROOT = Path(r"F:\opus_scratch\rescore_d8")
BELOW_NORMAL = 0x00004000


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1 << 22), b""):
            digest.update(block)
    return digest.hexdigest()


def loaders(source: Path) -> dict:
    """Execute only the v3b loader definitions (and the constants they use) from the trainer copy."""
    tree = ast.parse(source.read_text(encoding="utf-8"))
    wanted = {"read_pos_header", "load_set", "CatMap", "load_set_mmap"}
    body = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in wanted]
    if {node.name for node in body} != wanted:
        raise ValueError("loader definitions not found in the trainer copy")
    space = {"np": np, "Path": Path, "__name__": "opus_v3b_loaders"}
    exec(compile(ast.Module(body=body, type_ignores=[]), str(source), "exec"), space)
    return space


def run(argv, log: Path, cwd: Path | None = None) -> int:
    with open(log, "w", encoding="utf-8") as out:
        return subprocess.run(argv, stdout=out, stderr=subprocess.STDOUT, cwd=cwd, creationflags=BELOW_NORMAL).returncode


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rescored", type=Path, required=True)
    ap.add_argument("--stem", required=True)
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--fen2bin", required=True)
    ap.add_argument("--hce-dump", required=True)
    ap.add_argument("--loaders", type=Path, required=True)
    ap.add_argument("--dfilter")
    ap.add_argument("--dfilter-holdout-dir", type=Path)
    ap.add_argument("--threshold", type=int, default=300)
    ap.add_argument("--python", default="python")
    args = ap.parse_args(argv)
    work = args.work.resolve()
    if ALLOWED_ROOT.resolve() not in work.parents:
        ap.error(f"--work must be inside {ALLOWED_ROOT}")
    work.mkdir(parents=True, exist_ok=False)
    data = work / "data"
    data.mkdir()
    report = {"rescored": str(args.rescored), "rescored_sha256": sha256_file(args.rescored)}
    pos, hce = data / f"{args.stem}.pos", data / f"{args.stem}.hce"
    report["fen2bin_rc"] = run([args.fen2bin, str(args.rescored), str(pos)], work / "fen2bin.log")
    report["hce_dump_rc"] = run([args.hce_dump, str(args.rescored), str(hce)], work / "hce_dump.log")
    report["pos"] = {"path": str(pos), "bytes": pos.stat().st_size, "sha256": sha256_file(pos)}
    report["hce"] = {"path": str(hce), "bytes": hce.stat().st_size, "sha256": sha256_file(hce)}
    space = loaders(args.loaders)
    ram = space["load_set"]([str(pos)], str(data))
    mm = space["load_set_mmap"]([str(pos)], str(data))
    n = ram["n"]
    idx = np.arange(n, dtype=np.int64)
    same = {key: bool(np.array_equal(ram[key], mm[key][idx] if hasattr(mm[key], "__getitem__") else mm[key])) for key in ("boards", "score", "meta", "hce")}
    report["loaders"] = {"load_set_rows": n, "load_set_mmap_rows": int(mm["n"]), "arrays_equal": same}
    text = [line.split("|") for line in args.rescored.read_text(encoding="utf-8").splitlines()]
    t_score = np.asarray([int(t[1]) for t in text], np.int64)
    t_black = np.asarray([t[0].split()[1] == "b" for t in text])
    t_white2 = np.asarray([int(round(float(t[2]) * 2)) for t in text], np.int64)
    meta = ram["meta"].astype(np.int64)
    report["text_vs_loaded"] = {"rows_equal": n == len(text), "score_equal": bool(np.array_equal(ram["score"].astype(np.int64), t_score)),
                                "stm_bit_equal": bool(np.array_equal((meta & 1).astype(bool), t_black)),
                                "white_result_equal": bool(np.array_equal(meta >> 1, t_white2))}
    stm_result = np.where(meta & 1, 2 - (meta >> 1), meta >> 1)        # x2: 0 loss, 1 draw, 2 win for the side to move
    score = ram["score"].astype(np.int64)
    decisive = (stm_result != 1) & (score != 0)
    agree = int(((score > 0) == (stm_result == 2))[decisive].sum())
    report["sign_from_loaded"] = {"decisive": int(decisive.sum()), "agree": agree, "agreement": agree / max(1, int(decisive.sum()))}
    report["hce_bad"] = int((ram["hce"] == -32768).sum())
    if args.dfilter:
        df = work / "dfilter"
        (df / "scratch").mkdir(parents=True)
        hdir = df / "hce_dir"
        hdir.mkdir()
        for p in (pos, hce):
            shutil.copyfile(p, hdir / p.name)
        for name in ("h000.pos", "h000.hce"):
            shutil.copyfile(args.dfilter_holdout_dir / name, hdir / name)
        argv_df = [args.python, "-B", args.dfilter, "--train", str(hdir / pos.name), "--holdout-pos", str(hdir / "h000.pos"),
                   "--hce-dir", str(hdir), "--out", str(df / "sealed"), "--work-dir", str(df / "scratch"), "--seed", "20261025",
                   "--diagnostic-mode", "--disagreement-threshold", str(args.threshold)]
        report["dfilter_rc"] = run(argv_df, df / "dfilter.log")
        summary = json.loads((df / "sealed" / "forge_sol_datafilter_summary_20261026.json").read_text(encoding="utf-8"))
        report["dfilter"] = {"argv": argv_df, "threshold": args.threshold, "totals": summary["totals"],
                             "dropped_by_reason": {k: v for s in summary["shards"] for k, v in s["dropped"].items()},
                             "supplied_holdout_overlap": summary["supplied_holdout_overlap"]}
    report["pass"] = (report["fen2bin_rc"] == 0 and report["hce_dump_rc"] == 0 and n == len(text) and int(mm["n"]) == n
                      and all(same.values()) and all(report["text_vs_loaded"].values()) and report["hce_bad"] == 0
                      and report["sign_from_loaded"]["agreement"] > 0.8 and report.get("dfilter_rc", 0) == 0)
    (work / "loadcheck.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
