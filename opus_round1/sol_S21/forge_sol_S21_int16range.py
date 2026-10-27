"""S21: int16 range study of Forge H256 nets + a research-only clipped export with its float-parity loss.

RESEARCH ONLY (crew rework 10:30): no engine patch, no int16 engine path. AL1 inference is float: accumulators hold
B1 + sum(W1[f]) in units of 1/4096 (exact in float, |q| < 2^24); an int32 port of that path is safe (CR's table).
This tool measures what an int16 accumulator would face.

  python -I -B forge_sol_S21_int16range.py study --nets a.inc b.inc ... --pos t0.pos t1.pos ... --out study.json
  (--pos also accepts "FEN | ..." text files instead of .pos files)
  python -I -B forge_sol_S21_int16range.py export --net a.inc --pos ... --mode bound|observed --out a_clipped.inc

study, per net, over every position of the .pos files (both perspectives, all 256 lanes):
  - the accumulator range in int units (min, max, max |acc|, |acc| quantiles from an exact histogram);
  - int16 overflow: values with |acc| > 32767, positions with any overflowing lane, lanes that ever overflow;
  - with int16 WRAPPING arithmetic (two's complement, as SIMD add_epi16): positions whose network output changes;
  - CR's weight-only bounds recomputed from the .inc (max|w1|, the 32-feature bound |b1| + top-32 |w1| + 4*max|w1|,
    the 768-feature bound |b1| + sum |w1| as in Sol's gate), to compare with CR_HOLD_sol_nnueint16_b425207a_overflow_table.txt.
export: W1 and B1 rescaled by a = (32767 - 17) / bound and rounded half away from zero (17 = rounding headroom for the
  <= 33 rounded terms of one accumulator), so that every accumulator fits
  int16: mode "bound" uses the 32-feature worst-case bound (guaranteed for any legal position), mode "observed" uses
  the largest |acc| seen on the positions (not guaranteed). W2/B2 are unchanged; the activation divides by 4096*a.
  The written .inc starts with an #error line, so the AL1 engine cannot be built with it by mistake. The tool states
  the float-parity loss: network cp of the export vs the original net on the positions (mean/max |delta|, sign flips).
Forward (train_resid_v3b.py NNUE / forge::nnue): per perspective acc = B1 + sum W1[f], f = (rel*6 + type)*64 + sq'
(rel = piece colour != perspective, sq' = sq ^ 56 for black); act = clamp(acc / 4096, 0, 1)^2; logit =
(W2[:256] . act_stm + W2[256:] . act_opp + B2) / 4096; network cp = logit * 400 / 2.25. Deterministic (integer
accumulation, float64 outputs, fixed order). Needs numpy.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import numpy as np

SCALE = 4096.0
INT16 = 32767
HIDDEN = 256
CHUNK = 2000
ROUNDING_HEADROOM = 17


def read_inc(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")

    def arr(name):
        m = re.search(name + r"\[(\d+)\]\s*=\s*\{([^}]*)\}", text, re.S)
        values = np.array([int(x) for x in m.group(2).replace("\n", " ").split(",") if x.strip()], np.int64)
        if len(values) != int(m.group(1)):
            raise ValueError(f"{path}: {name} length")
        return values

    w1, b1, w2 = arr("NnueW1"), arr("NnueB1"), arr("NnueW2")
    b2 = int(re.search(r"NnueB2\s*=\s*(-?\d+)", text).group(1))
    residual = re.search(r"#define FORGE_NNUE_RESIDUAL\s+(\d)", text)
    if len(b1) != HIDDEN or len(w1) != 768 * HIDDEN or len(w2) != 2 * HIDDEN:
        raise ValueError(f"{path}: not an H256 Forge-768 net")
    raw = path.read_bytes()
    return {"w1": w1.reshape(768, HIDDEN), "b1": b1, "w2": w2, "b2": b2,
            "residual": bool(int(residual.group(1))) if residual else False,
            "md5": hashlib.md5(raw).hexdigest(), "sha256": hashlib.sha256(raw).hexdigest(), "path": str(path)}


def read_positions(paths: list[Path], limit: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """codes [N,64] (0 empty, 1..6 white PNBRQK, 7..12 black) and stm [N] (0 white, 1 black) from .pos files."""
    codes, stm = [], []
    for path in paths:
        with open(path, "rb") as stream:
            header = stream.read(16)
        if header[:4] != b"FPOS":
            raise ValueError(f"bad .pos {path}")
        n = int.from_bytes(header[8:16], "little")
        boards = np.memmap(path, np.uint8, "r", 16, (n, 32))
        meta = np.memmap(path, np.uint8, "r", 16 + 34 * n, (n,))
        c = np.empty((n, 64), np.int64)
        c[:, 0::2] = boards & 15
        c[:, 1::2] = boards >> 4
        codes.append(c)
        stm.append((np.asarray(meta) & 1).astype(np.int64))
    codes, stm = np.concatenate(codes), np.concatenate(stm)
    if limit:
        codes, stm = codes[:limit], stm[:limit]
    return codes, stm


PIECE_CODE = {"P": 1, "N": 2, "B": 3, "R": 4, "Q": 5, "K": 6, "p": 7, "n": 8, "b": 9, "r": 10, "q": 11, "k": 12}


def read_fen_text(paths: list[Path], limit: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """codes/stm from "FEN | ..." text lines (the fen2bin input format)."""
    codes, stm = [], []
    for path in paths:
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            if not line.strip():
                continue
            fields = line.split("|")[0].split()
            row = np.zeros(64, np.int64)
            for rank_index, rank in enumerate(fields[0].split("/")):
                file = 0
                for ch in rank:
                    if ch.isdigit():
                        file += int(ch)
                    else:
                        row[(7 - rank_index) * 8 + file] = PIECE_CODE[ch]
                        file += 1
            codes.append(row)
            stm.append(0 if fields[1] == "w" else 1)
            if limit and len(codes) >= limit:
                return np.asarray(codes), np.asarray(stm, np.int64)
    return np.asarray(codes), np.asarray(stm, np.int64)


def feature_lists(codes: np.ndarray, persp: np.ndarray) -> np.ndarray:
    """[N,64] feature index per square for the given perspective (768 = empty)."""
    sq = np.arange(64)[None, :]
    c = codes - 1
    color = np.floor_divide(c, 6)
    typ = c - color * 6
    bl = persp[:, None]
    rel = (color != bl).astype(np.int64)
    rsq = np.where(bl == 1, sq ^ 56, sq)
    f = (rel * 6 + typ) * 64 + rsq
    return np.where(codes > 0, f, 768)


def accumulators(net: dict, codes: np.ndarray, persp: np.ndarray, w1=None, b1=None) -> np.ndarray:
    """int64 [N,256] accumulators for one perspective (B1 + sum of W1 rows of the active features)."""
    w1 = net["w1"] if w1 is None else w1
    b1 = net["b1"] if b1 is None else b1
    padded = np.vstack([w1, np.zeros((1, HIDDEN), np.int64)])
    f = feature_lists(codes, persp)
    return padded[f].sum(axis=1) + b1[None, :]


def network_cp(net: dict, acc_stm: np.ndarray, acc_opp: np.ndarray, scale: float = SCALE) -> np.ndarray:
    act_s = np.clip(acc_stm / scale, 0.0, 1.0) ** 2
    act_o = np.clip(acc_opp / scale, 0.0, 1.0) ** 2
    logit = (act_s @ net["w2"][:HIDDEN] + act_o @ net["w2"][HIDDEN:] + net["b2"]) / SCALE
    return logit * 400.0 / 2.25


def wrap16(values: np.ndarray) -> np.ndarray:
    return ((values + 32768) % 65536) - 32768


def bounds(net: dict) -> dict:
    a = np.abs(net["w1"])
    maxw = int(a.max())
    top32 = np.sort(a, axis=0)[-32:, :].sum(axis=0)
    full = a.sum(axis=0)
    b = np.abs(net["b1"])
    return {"max_abs_w1": maxw, "top32_bound": int((b + top32).max() + 4 * maxw),
            "full768_bound": int((b + full).max()), "max_abs_w2": int(np.abs(net["w2"]).max())}


def study_net(net: dict, codes: np.ndarray, stm: np.ndarray) -> dict:
    n = len(codes)
    hist = np.zeros(1 << 13, np.int64)        # |acc| histogram, bins of 64 int units, up to 2^19
    lo, hi = None, None
    over_values = 0
    over_positions = 0
    lanes_over = np.zeros(HIDDEN, bool)
    wrap_changed = 0
    for start in range(0, n, CHUNK):
        c, s = codes[start:start + CHUNK], stm[start:start + CHUNK]
        acc_s, acc_o = accumulators(net, c, s), accumulators(net, c, 1 - s)
        both = np.concatenate([acc_s, acc_o], axis=1)
        lo = int(both.min()) if lo is None else min(lo, int(both.min()))
        hi = int(both.max()) if hi is None else max(hi, int(both.max()))
        absv = np.abs(both)
        np.add.at(hist, np.minimum(absv >> 6, len(hist) - 1).ravel(), 1)
        over = absv > INT16
        over_values += int(over.sum())
        over_positions += int(over.any(axis=1).sum())
        lanes_over |= over[:, :HIDDEN].any(axis=0) | over[:, HIDDEN:].any(axis=0)
        exact = network_cp(net, acc_s, acc_o)
        wrapped = network_cp(net, wrap16(acc_s), wrap16(acc_o))
        wrap_changed += int((np.abs(wrapped - exact) > 1e-9).sum())
    total = int(hist.sum())
    cum = np.cumsum(hist)

    def quantile(q):
        return int((np.searchsorted(cum, q * total) + 1) * 64)

    return {"positions": n, "values": total, "acc_min": lo, "acc_max": hi, "max_abs_acc": max(abs(lo), abs(hi)),
            "abs_acc_q0.99": quantile(0.99), "abs_acc_q0.999": quantile(0.999), "abs_acc_q0.99999": quantile(0.99999),
            "int16_overflow_values": over_values, "int16_overflow_value_share": over_values / total,
            "int16_overflow_positions": over_positions, "int16_overflow_position_share": over_positions / n,
            "lanes_that_ever_overflow": int(lanes_over.sum()),
            "wrapping_int16_positions_with_changed_output": wrap_changed,
            "headroom_factor_int16": INT16 / max(abs(lo), abs(hi))}


def export(net: dict, codes: np.ndarray, stm: np.ndarray, mode: str) -> tuple[dict, dict]:
    if mode == "bound":
        target = bounds(net)["top32_bound"]
    else:
        target = study_net(net, codes, stm)["max_abs_acc"]
    alpha = (INT16 - ROUNDING_HEADROOM) / target   # each of the <= 33 rounded terms (32 W1 rows + B1) adds <= 0.5
    rnd = lambda v: (np.sign(v) * np.floor(np.abs(v * alpha) + 0.5)).astype(np.int64)
    w1c, b1c = rnd(net["w1"].astype(np.float64)), rnd(net["b1"].astype(np.float64))
    scale = SCALE * alpha
    deltas, flips, fits = [], 0, True
    worst = 0
    for start in range(0, len(codes), CHUNK):
        c, s = codes[start:start + CHUNK], stm[start:start + CHUNK]
        base = network_cp(net, accumulators(net, c, s), accumulators(net, c, 1 - s))
        acs, aco = accumulators(net, c, s, w1c, b1c), accumulators(net, c, 1 - s, w1c, b1c)
        worst = max(worst, int(np.abs(acs).max()), int(np.abs(aco).max()))
        clipped = network_cp(net, acs, aco, scale)
        deltas.append(clipped - base)
        flips += int(((np.sign(clipped) != np.sign(base)) & (np.abs(base) >= 1.0)).sum())
    d = np.concatenate(deltas)
    parity = {"mode": mode, "alpha": alpha, "accumulator_scale": scale, "target_bound": target,
              "max_abs_acc_after": worst, "fits_int16_on_positions": worst <= INT16,
              "parity_net_cp": {"mean_abs": float(np.mean(np.abs(d))), "p99_abs": float(np.quantile(np.abs(d), 0.99)),
                                "max_abs": float(np.max(np.abs(d))), "mean": float(np.mean(d)),
                                "sign_flips_abs_ge_1cp": flips}, "positions": len(codes)}
    return {"w1": w1c, "b1": b1c, "w2": net["w2"], "b2": net["b2"], "residual": net["residual"]}, parity


def write_inc(path: Path, net: dict, parity: dict, source: dict) -> None:
    lines = ['#error "S21 research export (W1/B1 rescaled for int16 accumulators): not loadable by the AL1 engine"',
             f"// source {source['path']} md5 {source['md5']}; mode {parity['mode']}; W1/B1 scale {parity['accumulator_scale']:.6f} "
             f"(4096 * {parity['alpha']:.8f}); W2/B2 unchanged (scale 4096)",
             f"// float-parity loss on {parity['positions']} positions: mean |d| {parity['parity_net_cp']['mean_abs']:.4f} cp, "
             f"max |d| {parity['parity_net_cp']['max_abs']:.4f} cp, sign flips {parity['parity_net_cp']['sign_flips_abs_ge_1cp']}",
             f"#define FORGE_NNUE_RESIDUAL {1 if net['residual'] else 0}"]
    for name, values in (("NnueW1", net["w1"].ravel()), ("NnueB1", net["b1"]), ("NnueW2", net["w2"])):
        if np.abs(values).max() > INT16:
            raise ValueError(f"{name} outside int16")
        lines.append(f"static const std::int16_t {name}[{len(values)}] = {{")
        lines.extend("  " + ", ".join(map(str, values[i:i + 24])) + "," for i in range(0, len(values), 24))
        lines.append("};")
    lines.append(f"static const std::int16_t NnueB2 = {int(net['b2'])};")
    path.write_text("\n".join(lines) + "\n", encoding="ascii", newline="\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    st = sub.add_parser("study")
    st.add_argument("--nets", nargs="+", type=Path, required=True)
    st.add_argument("--pos", nargs="+", type=Path, required=True)
    st.add_argument("--limit", type=int, default=0)
    st.add_argument("--out", type=Path, required=True)
    ex = sub.add_parser("export")
    ex.add_argument("--net", type=Path, required=True)
    ex.add_argument("--pos", nargs="+", type=Path, required=True)
    ex.add_argument("--limit", type=int, default=0)
    ex.add_argument("--mode", choices=["bound", "observed"], default="bound")
    ex.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    if args.out.exists():
        ap.error("--out must be a new file")
    texts = [p for p in args.pos if p.suffix != ".pos"]
    codes, stm = read_fen_text(args.pos, args.limit) if texts else read_positions(args.pos, args.limit)
    inputs = [{"path": str(p), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in args.pos]
    if args.cmd == "study":
        rows = []
        for path in args.nets:
            net = read_inc(path)
            row = {"net": path.name, "md5": net["md5"], "sha256": net["sha256"], "residual": net["residual"]}
            row.update(bounds(net))
            row.update(study_net(net, codes, stm))
            rows.append(row)
            print(f"{path.name:44s} md5 {net['md5'][:8]} max|acc| {row['max_abs_acc']:>7d} q0.999 {row['abs_acc_q0.999']:>6d} "
                  f"int16-overflow positions {row['int16_overflow_positions']:>7d}/{row['positions']} "
                  f"({100 * row['int16_overflow_position_share']:.2f}%) top32 bound {row['top32_bound']}", flush=True)
        result = {"tool": "forge_sol_S21_int16range study", "status": "RESEARCH ONLY", "positions": len(codes), "inputs": inputs, "nets": rows}
    else:
        net = read_inc(args.net)
        clipped, parity = export(net, codes, stm, args.mode)
        write_inc(args.out, clipped, parity, net)
        result = {"tool": "forge_sol_S21_int16range export", "status": "RESEARCH ONLY: not loadable by the AL1 engine",
                  "source": {"path": str(args.net), "md5": net["md5"]}, "inputs": inputs, "output": str(args.out),
                  "output_sha256": hashlib.sha256(args.out.read_bytes()).hexdigest(), "parity": parity}
        print(json.dumps(parity, indent=2, sort_keys=True))
    target = args.out if args.cmd == "study" else Path(str(args.out) + ".json")   # export: <out>.inc + <out>.inc.json
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
