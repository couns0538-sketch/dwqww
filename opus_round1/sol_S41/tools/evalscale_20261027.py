#!/usr/bin/env python3
"""S41 evalscale: compare the static-evaluation scale of Forge networks on a fixed position set.

Subcommands (all read-only on their inputs; outputs must be new files / a new work directory):

  sample  --wac WAC300.epd --selfplay forge_selfplay_NNN.txt --n 9700 --out positions.txt
          Fixed position set: every WAC300 position, then N self-play positions read at evenly spaced byte offsets
          of one closed self-play text file ("FEN | score | result" lines; the first full line after each offset).
          Deterministic for a given file; only ~N short reads, the big file is never read whole.
  dump    --lock-tree <AL1 source tree> --harness evalscale_dump.cpp --positions positions.txt --work <new dir>
          --net NAME=path/to/net.inc [--net ...]
          Builds evalscale_dump once per network (the network as nnue_weights.inc next to a copy of src/nnue.cpp,
          the lock recipe's compiler flags, Idle priority, one compiler process at a time) and writes
          <work>/<NAME>.dump (index stm in_check hce net total) plus <work>/dump_manifest.json.
  analyze --ref NAME --dump NAME=path.dump [--dump ...] --out-json stats.json --out-md EVALSCALE.md
          |eval| quantiles, robust slope fits of every network against the reference, and the NetScale value
          (percent) that maps each network's static evaluation back to the reference scale.

Statistics (positions: valid FEN, not in check -- the search never uses a static evaluation in check --, and
|eval| <= WINDOW cp on both sides; slopes are cand = s * ref):
  lad(x, y)      least-absolute-deviation slope through the origin = weighted median of y/x, weights |x|.
  sym(x, y)      sqrt(lad(x, y) / lad(y, x)): symmetric robust scale (no regression-dilution direction).
  theil_sen      median of pairwise slopes (with intercept; all pairs or a fixed-seed sample of pairs).
  huber          Huber IRLS through the origin (k = 1.345 * MAD scale), a robust cross-check.
  ols            least squares through the origin (not robust; for reference only).
  q-ratio        q_p(|cand|) / q_p(|ref|) for p in QUANTILES (spread comparison, unpaired).
The same network on both sides gives every slope and ratio exactly 1.0 (identical arrays; tested).
Proposed NetScale = round(100 / sym): the engine option scales the NNUE-mode static evaluation by NetScale/100
(integer, truncated toward zero, as src/search.cpp does), so the mapped network has sym slope ~1 vs the reference.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

WINDOW = 2000            # cp; positions with a larger |static eval| on either side are decisive, not margin territory
QUANTILES = (0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99)
SUB_WINDOWS = ((0, 300), (300, WINDOW))
BOOT = 1000
SEED = 20261027
THEIL_SEN_MAX_PAIRS = 2_000_000
GPP = r"C:\msys64\ucrt64\bin\g++.exe"
# The PC lock recipe (2_build/BUILD.md): g++ 15.2 ucrt64, -O3 -DNDEBUG, znver5, static, no FMA contraction.
FLAGS = ["-std=c++20", "-O3", "-DNDEBUG", "-DFORGE_NNUE_HIDDEN=256", "-ffp-contract=off", "-fno-fast-math",
         "-march=znver5", "-static"]
IDLE_PRIORITY_CLASS = 0x00000040
PROTECTED = ("forge_push", "selfplay_out", "forge_nnue_train", os.path.join("Administrator", "grok-pc"))


# ----------------------------------------------------------------------------------------------- helpers

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def md5_file(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def refuse_protected(path: Path, what: str) -> None:
    norm = str(Path(path).resolve())
    for p in PROTECTED:
        if p.lower() in norm.lower():
            raise SystemExit(f"refusing to write {what} under a protected PC data directory: {norm}")


def epd_to_fen(line: str) -> str | None:
    """'pieces side castling ep [ops...]' -> FEN with halfmove 0 and fullmove 1."""
    parts = line.split()
    if len(parts) < 4:
        return None
    return " ".join(parts[:4]) + " 0 1"


# ----------------------------------------------------------------------------------------------- sample

def sample_selfplay(path: Path, n: int) -> list[tuple[int, str]]:
    """n positions at evenly spaced byte offsets: offset_k = k * (size // n); take the first complete line after
    the offset (or the first line for k = 0). Returns (offset_of_line, fen)."""
    size = path.stat().st_size
    if n <= 0 or size < n * 64:
        raise SystemExit(f"self-play file too small for {n} samples: {size} bytes")
    stride = size // n
    out: list[tuple[int, str]] = []
    with open(path, "rb") as f:
        for k in range(n):
            off = k * stride
            f.seek(off)
            if off:
                f.readline()                      # finish the partial line
            start = f.tell()
            line = f.readline().decode("utf-8", "strict").strip()
            if not line:
                raise SystemExit(f"empty line at offset {start}")
            fen = line.split("|")[0].strip()
            if len(fen.split()) != 6:
                raise SystemExit(f"not a 6-field FEN at offset {start}: {line[:80]!r}")
            out.append((start, fen))
    return out


def cmd_sample(a: argparse.Namespace) -> int:
    out = Path(a.out)
    if out.exists():
        raise SystemExit("--out must be a new file")
    refuse_protected(out, "--out")
    lines: list[str] = []
    wac = Path(a.wac)
    for raw in wac.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        fen = epd_to_fen(raw)
        ident = raw.split('id "')[1].split('"')[0] if 'id "' in raw else f"wac{len(lines) + 1}"
        lines.append(f"{fen} | wac:{ident}")
    n_wac = len(lines)
    sp = Path(a.selfplay)
    tag = sp.stem.replace("forge_selfplay_", "sp")
    for off, fen in sample_selfplay(sp, a.n):
        lines.append(f"{fen} | {tag}@{off}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    info = {"tool": "evalscale_20261027 sample", "wac": str(wac), "wac_sha256": sha256_file(wac), "wac_positions": n_wac,
            "selfplay": str(sp), "selfplay_bytes": sp.stat().st_size, "selfplay_mtime": sp.stat().st_mtime,
            "selfplay_md5_sidecar": (sp.with_suffix(sp.suffix + ".md5").read_text(encoding="utf-8").strip()
                                     if sp.with_suffix(sp.suffix + ".md5").exists() else None),
            "selfplay_positions": a.n, "stride_bytes": sp.stat().st_size // a.n,
            "positions": len(lines), "out": str(out), "out_sha256": sha256_file(out)}
    out.with_suffix(out.suffix + ".json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(info, indent=2))
    return 0


# ----------------------------------------------------------------------------------------------- dump

def build_harness(lock_tree: Path, harness: Path, net: Path, work: Path) -> Path:
    work.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(net, work / "nnue_weights.inc")
    shutil.copyfile(lock_tree / "src" / "nnue.cpp", work / "nnue.cpp")
    exe = work / "evalscale_dump.exe"
    src = lock_tree / "src"
    cmd = [GPP, *FLAGS, "-I" + str(lock_tree / "include"), str(harness), str(work / "nnue.cpp"),
           str(src / "bitboard.cpp"), str(src / "board.cpp"), str(src / "eval.cpp"), str(src / "eval_params.cpp"),
           "-o", str(exe)]
    env = dict(os.environ, PATH=r"C:\msys64\ucrt64\bin;" + os.environ.get("PATH", ""))
    flags = IDLE_PRIORITY_CLASS if os.name == "nt" else 0
    r = subprocess.run(cmd, capture_output=True, text=True, env=env, creationflags=flags)
    (work / "build.log").write_text(" ".join(cmd) + "\n" + r.stdout + r.stderr, encoding="utf-8")
    if r.returncode != 0:
        raise SystemExit(f"build failed for {net}:\n{r.stderr[-3000:]}")
    return exe


def cmd_dump(a: argparse.Namespace) -> int:
    work = Path(a.work)
    if work.exists():
        raise SystemExit("--work must be a new directory")
    refuse_protected(work, "--work")
    work.mkdir(parents=True)
    lock_tree, harness, positions = Path(a.lock_tree), Path(a.harness), Path(a.positions)
    manifest = {"tool": "evalscale_20261027 dump", "lock_tree": str(lock_tree), "harness": str(harness),
                "harness_sha256": sha256_file(harness), "positions": str(positions),
                "positions_sha256": sha256_file(positions), "flags": FLAGS, "nets": []}
    flags = IDLE_PRIORITY_CLASS if os.name == "nt" else 0
    for spec in a.net:
        name, path = spec.split("=", 1)
        net = Path(path)
        exe = build_harness(lock_tree, harness, net, work / f"build_{name}")
        r = subprocess.run([str(exe), str(positions)], capture_output=True, text=True, creationflags=flags)
        if r.returncode != 0:
            raise SystemExit(f"dump failed for {name}: {r.stderr[-2000:]}")
        dump = work / f"{name}.dump"
        dump.write_text(r.stdout, encoding="utf-8", newline="\n")
        manifest["nets"].append({"name": name, "net": str(net), "net_md5": md5_file(net), "net_sha256": sha256_file(net),
                                 "exe_sha256": sha256_file(exe), "harness_stderr": r.stderr.strip(),
                                 "dump": str(dump), "dump_sha256": sha256_file(dump),
                                 "lines": r.stdout.count("\n"), "bad": r.stdout.count(" BAD")})
        print(f"{name}: {manifest['nets'][-1]['lines']} lines, {manifest['nets'][-1]['bad']} BAD, "
              f"net md5 {manifest['nets'][-1]['net_md5'][:8]} ({r.stderr.strip()})", flush=True)
    (work / "dump_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    return 0


# ----------------------------------------------------------------------------------------------- statistics

def read_dump(path: Path) -> dict[str, np.ndarray]:
    idx, chk, hce, net, tot, valid = [], [], [], [], [], []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if not parts:
            continue
        idx.append(int(parts[0]))
        if parts[1] == "BAD":
            valid.append(False); chk.append(0); hce.append(0); net.append(0); tot.append(0)
            continue
        valid.append(True)
        chk.append(int(parts[2])); hce.append(int(parts[3])); net.append(int(parts[4])); tot.append(int(parts[5]))
    i = np.array(idx, dtype=np.int64)
    if not np.array_equal(i, np.arange(len(i))):
        raise SystemExit(f"{path}: indices are not 0..n-1")
    return {"valid": np.array(valid), "in_check": np.array(chk, dtype=bool), "hce": np.array(hce, dtype=np.float64),
            "net": np.array(net, dtype=np.float64), "total": np.array(tot, dtype=np.float64)}


def weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    """Lower weighted median: smallest v with cumulative weight >= half the total."""
    order = np.argsort(values, kind="mergesort")
    v, w = values[order], weights[order]
    cum = np.cumsum(w)
    k = int(np.searchsorted(cum, 0.5 * cum[-1], side="left"))
    return float(v[k])


def lad(x: np.ndarray, y: np.ndarray) -> float:
    """argmin_b sum |y - b x| (through the origin) = weighted median of y/x with weights |x| (x != 0)."""
    m = x != 0
    if not m.any():
        raise ValueError("lad: all x are zero")
    return weighted_median(y[m] / x[m], np.abs(x[m]))


def sym(x: np.ndarray, y: np.ndarray) -> float:
    return math.sqrt(lad(x, y) / lad(y, x))


def ols(x: np.ndarray, y: np.ndarray) -> float:
    return float(np.dot(x, y) / np.dot(x, x))


def huber(x: np.ndarray, y: np.ndarray, k: float = 1.345, iters: int = 50) -> float:
    b = ols(x, y)
    for _ in range(iters):
        r = y - b * x
        mad = float(np.median(np.abs(r - np.median(r))))
        scale = 1.4826 * mad
        if scale == 0.0:
            return b
        u = np.abs(r) / (k * scale)
        w = np.where(u <= 1.0, 1.0, 1.0 / np.maximum(u, 1e-300))
        nb = float(np.dot(w * x, y) / np.dot(w * x, x))
        if nb == b:
            break
        b = nb
    return b


def theil_sen(x: np.ndarray, y: np.ndarray, max_pairs: int = THEIL_SEN_MAX_PAIRS, seed: int = SEED) -> tuple[float, int]:
    n = len(x)
    total_pairs = n * (n - 1) // 2
    if total_pairs <= max_pairs:
        i, j = np.triu_indices(n, k=1)
    else:
        rng = np.random.default_rng(seed)
        i = rng.integers(0, n, size=max_pairs)
        j = rng.integers(0, n, size=max_pairs)
        keep = i != j
        i, j = i[keep], j[keep]
    dx = x[j] - x[i]
    m = dx != 0
    slopes = (y[j] - y[i])[m] / dx[m]
    return float(np.median(slopes)), int(m.sum())


def q_ratios(x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    qx = np.quantile(np.abs(x), QUANTILES)
    qy = np.quantile(np.abs(y), QUANTILES)
    return {f"q{int(round(p * 100)):02d}": (float(b / a) if a != 0 else float("nan")) for p, a, b in zip(QUANTILES, qx, qy)}


def bootstrap_sym(x: np.ndarray, y: np.ndarray, reps: int = BOOT, seed: int = SEED) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    n = len(x)
    vals = np.empty(reps)
    for r in range(reps):
        s = rng.integers(0, n, size=n)
        vals[r] = sym(x[s], y[s])
    lo, hi = np.quantile(vals, [0.025, 0.975])
    return float(lo), float(hi)


def scale_engine(values: np.ndarray, percent: int) -> np.ndarray:
    """The engine's NetScale arithmetic (src/search.cpp, forge::net_scale::apply): truncation toward zero."""
    if percent == 100:
        return values.copy()
    return np.trunc(values * percent / 100.0)


def residual_scale_for_unit_slope(hce: np.ndarray, net: np.ndarray, ref_total: np.ndarray) -> float:
    """Diagnostic only: the factor r (percent) with sym(ref_total, hce + r * net) == 1, by bisection on [0, 300]%."""
    def f(r: float) -> float:
        return sym(ref_total, hce + r * net) - 1.0
    lo, hi = 0.0, 3.0
    flo, fhi = f(lo), f(hi)
    if flo > 0 or fhi < 0:
        return float("nan")
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if f(mid) <= 0:
            lo = mid
        else:
            hi = mid
    return 100.0 * 0.5 * (lo + hi)


def compare(ref: dict[str, np.ndarray], cand: dict[str, np.ndarray], boot: bool = True) -> dict:
    base = ref["valid"] & cand["valid"] & ~ref["in_check"] & ~cand["in_check"]
    x_all, y_all = ref["total"], cand["total"]
    w = base & (np.abs(x_all) <= WINDOW) & (np.abs(y_all) <= WINDOW)
    x, y = x_all[w], y_all[w]
    ts, ts_pairs = theil_sen(x, y)
    s = sym(x, y)
    res = {
        "positions_valid_not_in_check": int(base.sum()),
        "positions_in_window": int(w.sum()),
        "sym": s,
        "lad_cand_on_ref": lad(x, y),
        "lad_ref_on_cand": lad(y, x),
        "theil_sen": ts, "theil_sen_pairs": ts_pairs,
        "huber": huber(x, y),
        "ols": ols(x, y),
        "pearson": float(np.corrcoef(x, y)[0, 1]) if np.std(x) > 0 and np.std(y) > 0 else float("nan"),
        "q_ratio_total": q_ratios(x, y),
        "mean_abs_ref": float(np.mean(np.abs(x))), "mean_abs_cand": float(np.mean(np.abs(y))),
        "netscale_percent": int(round(100.0 / s)),
    }
    for lo, hi in SUB_WINDOWS:
        m = (np.abs(x) > lo) & (np.abs(x) <= hi) if lo else (np.abs(x) <= hi)
        res[f"sym_ref_abs_{lo}_{hi}"] = sym(x[m], y[m]) if m.sum() > 10 else float("nan")
        res[f"n_ref_abs_{lo}_{hi}"] = int(m.sum())
    nm = base & (np.abs(ref["net"]) <= WINDOW) & (np.abs(cand["net"]) <= WINDOW)
    res["net_only"] = {"positions": int(nm.sum()),
                       "q_ratio_net": q_ratios(ref["net"][nm], cand["net"][nm]),
                       "mean_abs_net_ref": float(np.mean(np.abs(ref["net"][nm]))),
                       "mean_abs_net_cand": float(np.mean(np.abs(cand["net"][nm]))),
                       "share_net_of_total_ref": float(np.mean(np.abs(ref["net"][w])) / max(np.mean(np.abs(x)), 1e-9)),
                       "share_net_of_total_cand": float(np.mean(np.abs(cand["net"][w])) / max(np.mean(np.abs(y)), 1e-9))}
    res["residual_only_scale_percent_diag"] = residual_scale_for_unit_slope(cand["hce"][w], cand["net"][w], x)
    # Mapped with the proposed NetScale, engine arithmetic: should come back to sym ~ 1 against the reference.
    p = res["netscale_percent"]
    ym = scale_engine(y, p)
    res["mapped"] = {"percent": p, "sym": sym(x, ym), "q_ratio_total": q_ratios(x, ym)}
    if boot:
        res["sym_ci95"] = bootstrap_sym(x, y)
    return res


def quantile_table(d: dict[str, np.ndarray]) -> dict[str, float]:
    m = d["valid"] & ~d["in_check"] & (np.abs(d["total"]) <= WINDOW)
    q = np.quantile(np.abs(d["total"][m]), QUANTILES)
    out = {f"q{int(round(p * 100)):02d}": float(v) for p, v in zip(QUANTILES, q)}
    out["n"] = int(m.sum())
    out["mean_abs"] = float(np.mean(np.abs(d["total"][m])))
    out["beyond_window"] = int((d["valid"] & ~d["in_check"] & (np.abs(d["total"]) > WINDOW)).sum())
    return out


def cmd_analyze(a: argparse.Namespace) -> int:
    for p in (a.out_json, a.out_md):
        if Path(p).exists():
            raise SystemExit(f"{p} exists; outputs must be new files")
        refuse_protected(Path(p), "output")
    dumps = {}
    for spec in a.dump:
        name, path = spec.split("=", 1)
        dumps[name] = read_dump(Path(path))
    n = {len(v["valid"]) for v in dumps.values()}
    if len(n) != 1:
        raise SystemExit(f"dumps have different lengths: {n}")
    if a.ref not in dumps:
        raise SystemExit(f"--ref {a.ref} is not among the dumps")
    ref = dumps[a.ref]
    stats = {"tool": "evalscale_20261027 analyze", "ref": a.ref, "window_cp": WINDOW, "quantiles": list(QUANTILES),
             "bootstrap": BOOT, "seed": SEED, "positions": int(next(iter(n))),
             "abs_eval_quantiles": {k: quantile_table(v) for k, v in dumps.items()}, "vs_ref": {}}
    for name, d in dumps.items():
        stats["vs_ref"][name] = compare(ref, d, boot=not a.no_bootstrap)
    if a.second_ref:
        stats["second_ref"] = a.second_ref
        stats["vs_second_ref"] = {name: compare(dumps[a.second_ref], d, boot=False) for name, d in dumps.items()}
    Path(a.out_json).write_text(json.dumps(stats, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    Path(a.out_md).write_text(render_md(stats), encoding="utf-8", newline="\n")
    print(render_md(stats))
    return 0


def render_md(st: dict) -> str:
    ref = st["ref"]
    L = [f"## |static eval| quantiles (cp; valid, not in check, |eval| <= {st['window_cp']}; {st['positions']} positions in the set)", "",
         "| net | n | " + " | ".join(f"q{int(round(p * 100)):02d}" for p in st["quantiles"]) + " | mean | beyond window |",
         "|---|---:|" + "---:|" * len(st["quantiles"]) + "---:|---:|"]
    for name, q in st["abs_eval_quantiles"].items():
        L.append(f"| {name} | {q['n']} | " + " | ".join(f"{q[f'q{int(round(p * 100)):02d}']:.0f}" for p in st["quantiles"])
                 + f" | {q['mean_abs']:.1f} | {q['beyond_window']} |")
    L += ["", f"## Robust slope of each net's static eval against `{ref}` (cand = s * ref)", "",
          "| net | n | sym (primary) | 95% CI | LAD c|r | LAD r|c | Theil-Sen | Huber | OLS | Pearson | q50 ratio | q90 ratio | NetScale | sym after NetScale |",
          "|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for name, r in st["vs_ref"].items():
        ci = r.get("sym_ci95")
        cis = f"{ci[0]:.4f}-{ci[1]:.4f}" if ci else "-"
        L.append(f"| {name} | {r['positions_in_window']} | {r['sym']:.4f} | {cis} | {r['lad_cand_on_ref']:.4f} | "
                 f"{r['lad_ref_on_cand']:.4f} | {r['theil_sen']:.4f} | {r['huber']:.4f} | {r['ols']:.4f} | {r['pearson']:.4f} | "
                 f"{r['q_ratio_total']['q50']:.4f} | {r['q_ratio_total']['q90']:.4f} | {r['netscale_percent']} | {r['mapped']['sym']:.4f} |")
    L += ["", "## Where the scale difference sits (vs the reference)", "",
          "| net | sym |ref| <= 300 | sym 300 < |ref| <= 2000 | mean |net| ref / cand | net share of |total| ref / cand | net-only q50 ratio | residual-only scale for sym 1 (diagnostic, %) |",
          "|---|---:|---:|---|---|---:|---:|"]
    for name, r in st["vs_ref"].items():
        no = r["net_only"]
        L.append(f"| {name} | {r['sym_ref_abs_0_300']:.4f} | {r['sym_ref_abs_300_2000']:.4f} | "
                 f"{no['mean_abs_net_ref']:.1f} / {no['mean_abs_net_cand']:.1f} | {no['share_net_of_total_ref']:.3f} / {no['share_net_of_total_cand']:.3f} | "
                 f"{no['q_ratio_net']['q50']:.4f} | {r['residual_only_scale_percent_diag']:.1f} |")
    if "vs_second_ref" in st:
        L += ["", f"## Same, against `{st['second_ref']}` (no bootstrap)", "",
              "| net | sym | Theil-Sen | q50 ratio | q90 ratio | NetScale |", "|---|---:|---:|---:|---:|---:|"]
        for name, r in st["vs_second_ref"].items():
            L.append(f"| {name} | {r['sym']:.4f} | {r['theil_sen']:.4f} | {r['q_ratio_total']['q50']:.4f} | "
                     f"{r['q_ratio_total']['q90']:.4f} | {r['netscale_percent']} |")
    return "\n".join(L) + "\n"


# ----------------------------------------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sample")
    s.add_argument("--wac", required=True)
    s.add_argument("--selfplay", required=True)
    s.add_argument("--n", type=int, default=9700)
    s.add_argument("--out", required=True)
    d = sub.add_parser("dump")
    d.add_argument("--lock-tree", required=True)
    d.add_argument("--harness", required=True)
    d.add_argument("--positions", required=True)
    d.add_argument("--work", required=True)
    d.add_argument("--net", action="append", required=True, help="NAME=path/to/net.inc (repeat)")
    z = sub.add_parser("analyze")
    z.add_argument("--ref", required=True)
    z.add_argument("--second-ref")
    z.add_argument("--dump", action="append", required=True, help="NAME=path.dump (repeat)")
    z.add_argument("--out-json", required=True)
    z.add_argument("--out-md", required=True)
    z.add_argument("--no-bootstrap", action="store_true")
    a = ap.parse_args(argv)
    return {"sample": cmd_sample, "dump": cmd_dump, "analyze": cmd_analyze}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
