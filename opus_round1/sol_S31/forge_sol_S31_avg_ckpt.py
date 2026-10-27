"""S31: checkpoint averaging for Forge H256 residual nets (float average -> .inc), parity and holdout scoring.

  python -I -B forge_sol_S31_avg_ckpt.py avg   --inputs a.inc b.inc ... --out avg.inc
  python -I -B forge_sol_S31_avg_ckpt.py avg   --bins a.bin b.bin ... --template a.inc --out avg.inc
  python -I -B forge_sol_S31_avg_ckpt.py avg   --pts a.pt b.pt ... --template a.inc --out avg.inc   (needs torch)
  python -I -B forge_sol_S31_avg_ckpt.py score --nets x.inc y.inc ... --pos holdout.pos --hce-dir D --out score.json
  python -I -B forge_sol_S31_avg_ckpt.py subset --pos a.pos b.pos --hce-dir D --stride 16 --out-stem dir/name

avg: the nets are averaged in float64 and quantized like the trainer's export_forge (x 4096, round half away from
  zero, int16). From .inc inputs the average is of the dequantized weights (int/4096); from .bin inputs (the trainer's
  float32 export: W1^T (768*H), B1, W2, B2) it is of the float weights. The text is written exactly as export_forge
  writes it (the header lines of the template/first input, 24 values per line), so averaging ONE file reproduces that
  file byte for byte (same md5), and a single .bin reproduces its own .inc.
score: the trainer's holdout metric without Torch: pred = sigmoid(net_logit + hce * 2.25/400), MSE against the
  blended target b*sigmoid(clamp(score * 2.25/400, +-40)) + (1-b)*stm_result for b = 1.0 (teacher), 0.6, 0.8, and
  the HCE-alone baseline; float64 sums. The forward is the engine's (checked against forge::nnue in S21 and by the
  parity step here). Every result records the holdout files' md5.
subset: a deterministic every-stride-th-row copy of .pos/.hce files (rows 0, stride, ... of their concatenation), so
  every arm is scored on one holdout file pair with one md5.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import numpy as np

SCALE = 4096.0
HIDDEN = 256
K = 2.25
CHUNK = 4000


# --------------------------------------------------------------------------------------------- .inc I/O
def parse_inc(path: Path) -> dict:
    text = path.read_text(encoding="ascii")
    head = text[:text.index("static const std::int16_t NnueW1[")]

    def arr(name):
        m = re.search(r"static const std::int16_t " + name + r"\[(\d+)\] = \{\n(.*?)\n\};", text, re.S)
        values = np.array([int(x) for x in m.group(2).replace("\n", " ").split(",") if x.strip()], np.int64)
        if len(values) != int(m.group(1)):
            raise ValueError(f"{path}: {name} length")
        return values

    w1, b1, w2 = arr("NnueW1"), arr("NnueB1"), arr("NnueW2")
    b2 = int(re.search(r"static const std::int16_t NnueB2 = (-?\d+);", text).group(1))
    if len(b1) != HIDDEN or len(w1) != 768 * HIDDEN or len(w2) != 2 * HIDDEN:
        raise ValueError(f"{path}: not an H256 Forge-768 net")
    residual = bool(int(re.search(r"#define FORGE_NNUE_RESIDUAL\s+(\d)", head).group(1)))
    return {"head": head, "w1": w1, "b1": b1, "w2": w2, "b2": b2, "residual": residual}


def render_inc(head: str, w1, b1, w2, b2) -> bytes:
    lines = head.rstrip("\n").split("\n")
    for name, v in (("NnueW1", w1), ("NnueB1", b1), ("NnueW2", w2)):
        if np.abs(v).max() > 32767:
            raise ValueError(f"{name} exceeds int16")
        lines.append(f"static const std::int16_t {name}[{len(v)}] = {{")
        lines.extend("  " + ", ".join(map(str, v[i:i + 24])) + "," for i in range(0, len(v), 24))
        lines.append("};")
    lines.append(f"static const std::int16_t NnueB2 = {int(b2)};")
    return ("\n".join(lines) + "\n").encode("ascii")


def quantize(values: np.ndarray) -> np.ndarray:
    """export_forge: v * 4096, round half away from zero."""
    scaled = values.astype(np.float64) * SCALE
    return (np.sign(scaled) * np.floor(np.abs(scaled) + 0.5)).astype(np.int64)


def read_bin(path: Path) -> list[np.ndarray]:
    raw = np.frombuffer(path.read_bytes(), "<f4").astype(np.float64)
    sizes = (768 * HIDDEN, HIDDEN, 2 * HIDDEN, 1)
    if len(raw) != sum(sizes):
        raise ValueError(f"{path}: unexpected .bin size")
    out, offset = [], 0
    for size in sizes:
        out.append(raw[offset:offset + size])
        offset += size
    return out


RUN_KEYS = ("hidden", "residual", "features", "epochs", "steps_per_epoch")


def read_pt(path: Path) -> tuple[list[np.ndarray], dict]:
    """A trainer checkpoint (.pt = config + model state + optimizer state): the model's float32 weights in .bin
    order (W1^T as 768 x H row-major, B1, W2, B2) and the run identity from its config."""
    import torch
    obj = torch.load(str(path), map_location="cpu", weights_only=True)
    cfg, model = obj.get("config", {}), obj["model"]
    if int(cfg.get("hidden", HIDDEN)) != HIDDEN:
        raise ValueError(f"{path}: hidden {cfg.get('hidden')} is not {HIDDEN}")
    parts = [model["ft.weight"].double().numpy().T.reshape(-1), model["ft.bias"].double().numpy().reshape(-1),
             model["out.weight"].double().numpy().reshape(-1), model["out.bias"].double().numpy().reshape(-1)]
    return parts, {k: cfg.get(k) for k in RUN_KEYS}


def average_pts(paths: list[Path], template: Path) -> bytes:
    """Average any number of .pt checkpoints of ONE run (their configs must agree)."""
    loaded = [read_pt(p) for p in paths]
    runs = {json.dumps(run, sort_keys=True) for _, run in loaded}
    if len(runs) != 1:
        raise ValueError("the .pt files come from different runs: " + "; ".join(sorted(runs)))
    mean = [np.mean([parts[i] for parts, _ in loaded], axis=0) for i in range(4)]
    return render_inc(parse_inc(template)["head"], quantize(mean[0]), quantize(mean[1]), quantize(mean[2]), quantize(mean[3])[0])


def average_incs(paths: list[Path]) -> bytes:
    nets = [parse_inc(p) for p in paths]
    mean = lambda key: np.mean([n[key] / SCALE for n in nets], axis=0)
    b2 = quantize(np.array([np.mean([n["b2"] / SCALE for n in nets])]))[0]
    return render_inc(nets[0]["head"], quantize(mean("w1")), quantize(mean("b1")), quantize(mean("w2")), b2)


def average_bins(paths: list[Path], template: Path) -> bytes:
    parts = [read_bin(p) for p in paths]
    mean = [np.mean([p[i] for p in parts], axis=0) for i in range(4)]
    return render_inc(parse_inc(template)["head"], quantize(mean[0]), quantize(mean[1]), quantize(mean[2]), quantize(mean[3])[0])


# --------------------------------------------------------------------------------------------- forward
def read_pos(pos: Path, hce_dir: Path) -> dict:
    with open(pos, "rb") as stream:
        header = stream.read(16)
    if header[:4] != b"FPOS":
        raise ValueError(f"bad .pos {pos}")
    n = int.from_bytes(header[8:16], "little")
    boards = np.array(np.memmap(pos, np.uint8, "r", 16, (n, 32)))   # copied: no map stays open (Windows file locks)
    score = np.asarray(np.memmap(pos, "<i2", "r", 16 + 32 * n, (n,))).astype(np.float64)
    meta = np.asarray(np.memmap(pos, np.uint8, "r", 16 + 34 * n, (n,))).astype(np.int64)
    hce_path = hce_dir / (pos.stem + ".hce")
    hce = np.asarray(np.memmap(hce_path, "<i2", "r", 16, (n,))).astype(np.float64)
    return {"boards": boards, "score": score, "meta": meta, "hce": hce, "n": n,
            "pos_md5": hashlib.md5(pos.read_bytes()).hexdigest(), "hce_md5": hashlib.md5(hce_path.read_bytes()).hexdigest()}


def accumulators(w1p: np.ndarray, b1: np.ndarray, codes: np.ndarray, persp: np.ndarray) -> np.ndarray:
    sq = np.arange(64)[None, :]
    c = codes - 1
    color = np.floor_divide(c, 6)
    typ = c - color * 6
    bl = persp[:, None]
    f = np.where(codes > 0, ((color != bl).astype(np.int64) * 6 + typ) * 64 + np.where(bl == 1, sq ^ 56, sq), 768)
    return w1p[f].sum(axis=1) + b1[None, :]


def net_logit(net: dict, boards: np.ndarray, stm: np.ndarray) -> np.ndarray:
    codes = np.empty((len(boards), 64), np.int64)
    codes[:, 0::2] = boards & 15
    codes[:, 1::2] = boards >> 4
    w1p = np.vstack([net["w1"].reshape(768, HIDDEN), np.zeros((1, HIDDEN), np.int64)])
    a_s = np.clip(accumulators(w1p, net["b1"], codes, stm) / SCALE, 0.0, 1.0) ** 2
    a_o = np.clip(accumulators(w1p, net["b1"], codes, 1 - stm) / SCALE, 0.0, 1.0) ** 2
    return (a_s @ net["w2"][:HIDDEN] + a_o @ net["w2"][HIDDEN:] + net["b2"]) / SCALE


def score_net(net: dict | None, data: dict, blends=(1.0, 0.6, 0.8)) -> dict:
    sums = {b: 0.0 for b in blends}
    n = data["n"]
    for start in range(0, n, CHUNK):
        end = min(n, start + CHUNK)
        meta = data["meta"][start:end]
        stm = meta & 1
        white = (meta >> 1) * 0.5
        stm_res = np.where(stm == 0, white, 1.0 - white)
        hce_logit = data["hce"][start:end] * (K / 400.0)
        logit = hce_logit if net is None else net_logit(net, np.asarray(data["boards"][start:end]), stm) + hce_logit
        pred = 1.0 / (1.0 + np.exp(-logit))
        teacher = 1.0 / (1.0 + np.exp(-np.clip(data["score"][start:end] * (K / 400.0), -40.0, 40.0)))
        for b in blends:
            target = b * teacher + (1.0 - b) * stm_res
            sums[b] += float(np.sum((pred - target) ** 2))
    return {f"mse_b{b}": sums[b] / n for b in blends}


def write_subset(pos_files: list[Path], hce_dir: Path, stride: int, stem: Path) -> dict:
    boards, score, meta, hce = [], [], [], []
    offset = 0
    for pos in pos_files:
        with open(pos, "rb") as stream:
            n = int.from_bytes(stream.read(16)[8:16], "little")
        first = (-offset) % stride
        boards.append(np.asarray(np.memmap(pos, np.uint8, "r", 16, (n, 32))[first::stride]))
        score.append(np.asarray(np.memmap(pos, "<i2", "r", 16 + 32 * n, (n,))[first::stride]))
        meta.append(np.asarray(np.memmap(pos, np.uint8, "r", 16 + 34 * n, (n,))[first::stride]))
        hce.append(np.asarray(np.memmap(hce_dir / (pos.stem + ".hce"), "<i2", "r", 16, (n,))[first::stride]))
        offset += n
    b, s, m, h = (np.concatenate(x) for x in (boards, score, meta, hce))
    rows = len(s)
    header = lambda magic: magic + (1).to_bytes(4, "little") + rows.to_bytes(8, "little")
    pos_out, hce_out = stem.with_suffix(".pos"), stem.with_suffix(".hce")
    pos_out.write_bytes(header(b"FPOS") + b.tobytes() + s.astype("<i2").tobytes() + m.tobytes())
    hce_out.write_bytes(header(b"FHCE") + h.astype("<i2").tobytes())
    return {"rows": rows, "stride": stride, "sources": [str(p) for p in pos_files],
            "pos_md5": hashlib.md5(pos_out.read_bytes()).hexdigest(), "hce_md5": hashlib.md5(hce_out.read_bytes()).hexdigest()}


PIECE_CODE = {"P": 1, "N": 2, "B": 3, "R": 4, "Q": 5, "K": 6, "p": 7, "n": 8, "b": 9, "r": 10, "q": 11, "k": 12}


def fen_codes(path: Path) -> tuple[np.ndarray, np.ndarray]:
    boards, stm = [], []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        fields = line.split("|")[0].split()
        codes = [0] * 64
        for r, rank in enumerate(fields[0].split("/")):
            f = 0
            for ch in rank:
                if ch.isdigit():
                    f += int(ch)
                else:
                    codes[(7 - r) * 8 + f] = PIECE_CODE[ch]
                    f += 1
        boards.append(bytes(codes[2 * i] | (codes[2 * i + 1] << 4) for i in range(32)))
        stm.append(0 if fields[1] == "w" else 1)
    return np.frombuffer(b"".join(boards), np.uint8).reshape(-1, 32), np.asarray(stm, np.int64)


def parity(inc: Path, fens: Path, lock_tree: Path, harness: Path, work: Path) -> dict:
    """Build the archive's nnue_check.cpp with this .inc (a copy of the lock's nnue.cpp next to it) and compare its
    network cp with this tool's forward, truncated toward zero like the engine."""
    import os
    import shutil
    import subprocess
    work.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(inc, work / "nnue_weights.inc")
    shutil.copyfile(lock_tree / "src" / "nnue.cpp", work / "nnue.cpp")
    src = lock_tree / "src"
    cmd = [r"C:\msys64\ucrt64\bin\g++.exe", "-std=c++20", "-O2", "-DNDEBUG", "-DFORGE_NNUE_HIDDEN=256", "-ffp-contract=off",
           "-fno-fast-math", "-march=znver5", "-static", "-I" + str(lock_tree / "include"), str(harness), str(work / "nnue.cpp"),
           str(src / "bitboard.cpp"), str(src / "board.cpp"), str(src / "eval.cpp"), str(src / "eval_params.cpp"), "-o", str(work / "nnue_check.exe")]
    env = dict(os.environ, PATH=r"C:\msys64\ucrt64\bin;" + os.environ["PATH"])
    build = subprocess.run(cmd, capture_output=True, text=True, env=env, creationflags=0x00004000)
    if build.returncode != 0:
        raise SystemExit(build.stderr[-2000:])
    run = subprocess.run([str(work / "nnue_check.exe"), str(fens)], capture_output=True, text=True, creationflags=0x00004000)
    engine = np.array([int(line.split()[0]) for line in run.stdout.splitlines() if line.strip() and line != "BAD"])
    boards, stm = fen_codes(fens)
    raw = np.clip(net_logit(parse_inc(inc), boards, stm) * 400.0 / K, -30000, 30000)
    mine = np.trunc(raw).astype(np.int64)
    if len(engine) != len(mine):
        return {"net": inc.name, "positions": int(len(mine)), "engine_lines": int(len(engine)), "exact": 0,
                "boundary": 0, "max_abs_diff": None, "stderr": run.stderr.strip()}
    exact = int((mine == engine).sum())
    # The engine sums in float32, this forward in float64: a value within 1e-3 of an integer can truncate to the
    # neighbouring integer. Such 1 cp differences are counted apart; anything else is a real mismatch.
    diff = np.abs(mine - engine)
    near = np.abs(raw - np.round(raw)) < 1e-3
    boundary = int(((diff == 1) & near).sum())
    return {"net": inc.name, "positions": int(len(mine)), "engine_lines": int(len(engine)), "exact": exact,
            "boundary": boundary, "max_abs_diff": int(diff.max()), "stderr": run.stderr.strip()}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("parity")
    p.add_argument("--nets", nargs="+", type=Path, required=True)
    p.add_argument("--fens", type=Path, required=True)
    p.add_argument("--lock-tree", type=Path, required=True)
    p.add_argument("--harness", type=Path, required=True)
    p.add_argument("--work", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = sub.add_parser("avg")
    a.add_argument("--inputs", nargs="*", type=Path, default=[])
    a.add_argument("--bins", nargs="*", type=Path, default=[])
    a.add_argument("--pts", nargs="*", type=Path, default=[], help="trainer .pt checkpoints of one run")
    a.add_argument("--template", type=Path)
    a.add_argument("--out", type=Path, required=True)
    s = sub.add_parser("score")
    s.add_argument("--nets", nargs="+", type=Path, required=True)
    s.add_argument("--pos", type=Path, required=True)
    s.add_argument("--hce-dir", type=Path, required=True)
    s.add_argument("--out", type=Path, required=True)
    t = sub.add_parser("subset")
    t.add_argument("--pos", nargs="+", type=Path, required=True)
    t.add_argument("--hce-dir", type=Path, required=True)
    t.add_argument("--stride", type=int, required=True)
    t.add_argument("--out-stem", type=Path, required=True)
    args = ap.parse_args(argv)
    if args.cmd == "parity":
        if args.out.exists():
            ap.error("--out must be a new file")
        rows = [parity(n, args.fens, args.lock_tree, args.harness, args.work / n.stem) for n in args.nets]
        for r in rows:
            print(f"{r['net']:44s} {r['exact']}/{r['positions']} exact, {r['boundary']} at a float32/float64 truncation "
                  f"boundary (1 cp), max |diff| {r['max_abs_diff']} cp", flush=True)
        ok = all(r["exact"] + r["boundary"] == r["positions"] == r["engine_lines"] for r in rows)
        args.out.write_text(json.dumps({"fens": str(args.fens), "fens_md5": hashlib.md5(args.fens.read_bytes()).hexdigest(),
                                        "nets": rows, "pass": ok}, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        return 0 if ok else 1
    if args.cmd == "avg":
        if args.out.exists():
            ap.error("--out must be a new file")
        given = [bool(args.inputs), bool(args.bins), bool(args.pts)]
        if sum(given) != 1 or ((args.bins or args.pts) and not args.template):
            ap.error("give --inputs, or --bins / --pts with --template")
        if args.inputs:
            data = average_incs(args.inputs)
        elif args.bins:
            data = average_bins(args.bins, args.template)
        else:
            data = average_pts(args.pts, args.template)
        args.out.write_bytes(data)
        print(f"{args.out.name}: md5 {hashlib.md5(data).hexdigest()} from {len(args.inputs or args.bins or args.pts)} input(s)")
        return 0
    if args.cmd == "subset":
        if args.out_stem.with_suffix(".pos").exists():
            ap.error("output exists")
        print(json.dumps(write_subset(args.pos, args.hce_dir, args.stride, args.out_stem), indent=2))
        return 0
    if args.out.exists():
        ap.error("--out must be a new file")
    data = read_pos(args.pos, args.hce_dir)
    result = {"holdout": {"pos": str(args.pos), "rows": data["n"], "pos_md5": data["pos_md5"], "hce_md5": data["hce_md5"]},
              "hce_baseline": score_net(None, data), "nets": []}
    for path in args.nets:
        net = parse_inc(path)
        row = {"net": path.name, "md5": hashlib.md5(path.read_bytes()).hexdigest(), **score_net(net, data)}
        result["nets"].append(row)
        print(f"{path.name:40s} md5 {row['md5'][:8]} teacher {row['mse_b1.0']:.7f} b0.6 {row['mse_b0.6']:.7f} b0.8 {row['mse_b0.8']:.7f}", flush=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
