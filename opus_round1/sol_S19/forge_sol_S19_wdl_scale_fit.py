"""S19: fit a per-phase sigmoid scale that maps the side-to-move score to the game result (WDL), with CIs.

Model (the v3b trainer's teacher, train_resid_v3b.py targets()): p = sigmoid(clamp(score * k / 400, -40, 40)),
score = side-to-move centipawns, target = the side to move's result (1 win, 0.5 draw, 0 loss). The trainer and the
f006 recipe use one constant k = 2.25 (K_DEFAULT; the recipe leaves --sigmoid-k at its default). This tool fits k
per game phase by minimising log-loss (cross-entropy with the 0 / 0.5 / 1 target) on a fit set, gives a bootstrap
95% interval per phase, and compares held-out log-loss: the constant 2.25, one fitted global k, and the per-phase
table. Phase = the Forge HCE material phase (include/forge/eval.hpp: PhaseValue {0, P 0, N 1, B 1, R 2, Q 4, K 0},
MaxPhase 24), summed over both sides and clamped at 24.

Inputs (read-only):
  .pos files (v3b record format: FPOS header, 32-byte nibble boards, int16 STM score, meta: bit0 black to move,
      bits1-2 WHITE result*2), and
  text files ("FEN | stm_cp | white_result" per line). Text scores are clipped to +-3000 cp, as the converter that
      makes .pos from text does. Text games are rebuilt from line order (a new game starts when the fullmove number
      falls, the piece count rises or the result changes: the rule of build_forge_holdout_gamesplit_reference.py),
      and held-out games are chosen by sha1(game_id + seed) % 10000 < frac * 10000.
Usage:
  python -I -B forge_sol_S19_wdl_scale_fit.py --fit-pos A.pos B.pos --holdout-pos H.pos --out result.json
  python -I -B forge_sol_S19_wdl_scale_fit.py --text sample.txt --holdout-frac 0.3 --out result.json
Deterministic: fixed seeds, fixed Newton iterations, sorted JSON. Needs numpy (the NNUE venv has 1.26.4).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

K_REFERENCE = 2.25          # train_resid_v3b.py K_DEFAULT; the f006 recipe uses the default
PHASE_VALUE = (0, 0, 1, 1, 2, 4, 0)   # by piece type: none, pawn, knight, bishop, rook, queen, king
MAX_PHASE = 24
DEFAULT_EDGES = (0, 4, 8, 12, 16, 20, 25)   # buckets [0,4) [4,8) ... [20,25): phase 24 is in the last one
TEXT_CLIP = 3000
SEED = 20261027


# ------------------------------------------------------------------------------------------------ inputs
def nibble_phase_table() -> np.ndarray:
    """Phase weight of each board nibble code: 0 empty, 1..6 white P N B R Q K, 7..12 black P N B R Q K."""
    table = np.zeros(16, np.int64)
    for code in range(1, 13):
        table[code] = PHASE_VALUE[(code - 1) % 6 + 1]
    return table


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1 << 22), b""):
            digest.update(block)
    return digest.hexdigest()


def read_pos(path: Path, stride: int = 1) -> dict:
    """Read a .pos file through read-only memory maps; stride > 1 keeps every stride-th row (rows 0, stride, ...)."""
    with open(path, "rb") as stream:
        header = stream.read(16)
    if header[:4] != b"FPOS" or int.from_bytes(header[4:8], "little") != 1:
        raise ValueError(f"bad .pos header: {path}")
    n = int.from_bytes(header[8:16], "little")
    if path.stat().st_size != 16 + 35 * n:
        raise ValueError(f".pos size does not match its count: {path}")
    boards_all = np.memmap(path, np.uint8, "r", 16, (n, 32))
    score_all = np.memmap(path, "<i2", "r", 16 + 32 * n, (n,))
    meta_all = np.memmap(path, np.uint8, "r", 16 + 34 * n, (n,))
    table = nibble_phase_table()
    rows = list(range(0, n, 1 << 20))
    phase_parts, score_parts, meta_parts = [], [], []
    for start in rows:  # chunks of 1M rows keep the working set small
        end = min(n, start + (1 << 20))
        first = start + (-start) % stride
        b = np.asarray(boards_all[first:end:stride])
        phase_parts.append(table[b & 15].sum(axis=1) + table[b >> 4].sum(axis=1))
        score_parts.append(np.asarray(score_all[first:end:stride]).astype(np.float64))
        meta_parts.append(np.asarray(meta_all[first:end:stride]))
    del boards_all, score_all, meta_all
    phase = np.concatenate(phase_parts) if phase_parts else np.zeros(0, np.int64)
    score = np.concatenate(score_parts) if score_parts else np.zeros(0)
    meta = np.concatenate(meta_parts) if meta_parts else np.zeros(0, np.uint8)
    if (meta == 255).any():
        raise ValueError(f"bad records in {path}")
    black = (meta & 1).astype(bool)
    white_result = ((meta >> 1) & 3).astype(np.float64) * 0.5
    stm_result = np.where(black, 1.0 - white_result, white_result)
    return {"score": score, "phase": np.minimum(phase, MAX_PHASE), "result": stm_result, "group": None,
            "rows": len(score), "file_rows": n, "stride": stride, "sha256": file_sha256(path), "path": str(path)}


def fen_phase(placement: str) -> int:
    weight = {"n": 1, "b": 1, "r": 2, "q": 4}
    return min(MAX_PHASE, sum(weight.get(ch.lower(), 0) for ch in placement if ch.isalpha()))


def read_text(path: Path) -> dict:
    """FEN | stm_cp | white_result lines; games rebuilt from line order (see the module docstring)."""
    raw = path.read_bytes()
    scores, phases, results, games = [], [], [], []
    game = -1
    prev = None
    bad = 0
    for line in raw.decode("utf-8-sig").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        try:
            fen, score_text, result_text = [part.strip() for part in line.split("|")]
            fields = fen.split()
            fullmove = int(fields[5])
            pieces = sum(ch.isalpha() for ch in fields[0])
            white_result = float(result_text)
            score = int(score_text)
            if white_result not in (0.0, 0.5, 1.0) or fields[1] not in ("w", "b"):
                raise ValueError("bad field")
        except (ValueError, IndexError):
            bad += 1
            continue
        if prev is None or fullmove < prev[0] or pieces > prev[1] or result_text != prev[2]:
            game += 1
        prev = (fullmove, pieces, result_text)
        stm_result = white_result if fields[1] == "w" else 1.0 - white_result
        scores.append(max(-TEXT_CLIP, min(TEXT_CLIP, score)))
        phases.append(fen_phase(fields[0]))
        results.append(stm_result)
        games.append(game)
    return {"score": np.asarray(scores, np.float64), "phase": np.asarray(phases, np.int64),
            "result": np.asarray(results, np.float64), "group": np.asarray(games, np.int64),
            "rows": len(scores), "bad_lines": bad, "games": game + 1,
            "sha256": hashlib.sha256(raw).hexdigest(), "path": str(path)}


def concat(parts: list[dict]) -> dict:
    out = {key: np.concatenate([p[key] for p in parts]) for key in ("score", "phase", "result")}
    if all(p["group"] is not None for p in parts):
        offset, groups = 0, []
        for p in parts:
            groups.append(p["group"] + offset)
            offset += int(p["group"].max()) + 1 if len(p["group"]) else 0
        out["group"] = np.concatenate(groups)
    else:
        out["group"] = None
    out["rows"] = len(out["score"])
    return out


def select(data: dict, mask: np.ndarray) -> dict:
    out = {key: data[key][mask] for key in ("score", "phase", "result")}
    out["group"] = None if data["group"] is None else data["group"][mask]
    out["rows"] = int(mask.sum())
    return out


def game_split(text: dict, path: str, frac: float, seed: str) -> np.ndarray:
    """Held-out mask by game: sha1('<file>#<game>' + seed) % 10000 < frac * 10000."""
    name = Path(path).name
    held = np.zeros(text["rows"], bool)
    for game in np.unique(text["group"]):
        digest = int(hashlib.sha1((f"{name}#{int(game)}" + seed).encode()).hexdigest(), 16)
        if digest % 10000 < frac * 10000:
            held |= text["group"] == game
    return held


# ------------------------------------------------------------------------------------------------- model
def log_loss(score: np.ndarray, result: np.ndarray, k) -> float:
    """Mean cross-entropy of sigmoid(clamp(score*k/400, +-40)) against the 0/0.5/1 target (natural log)."""
    z = np.clip(score * (np.asarray(k, np.float64) / 400.0), -40.0, 40.0)
    softplus = np.log1p(np.exp(-np.abs(z))) + np.maximum(z, 0.0)
    return float(np.mean(softplus - result * z)) if len(score) else float("nan")


def fit_k(score: np.ndarray, result: np.ndarray, start: float = K_REFERENCE) -> tuple[float, int]:
    """Newton's method on the convex 1-D log-loss in k, with backtracking; returns (k, iterations)."""
    x = score / 400.0
    if len(x) == 0 or not np.any(x):
        return start, 0
    k = start
    loss = log_loss(score, result, k)
    for iteration in range(1, 101):
        z = k * x
        inside = np.abs(z) < 40.0
        p = 1.0 / (1.0 + np.exp(-np.clip(z, -40.0, 40.0)))
        grad = float(np.mean((p - result) * x * inside))
        hess = float(np.mean(p * (1.0 - p) * x * x * inside))
        if hess <= 0.0:
            break
        step = grad / hess
        trial = k - step
        new_loss = log_loss(score, result, trial)
        shrink = 0
        while new_loss > loss and shrink < 40:
            step *= 0.5
            trial = k - step
            new_loss = log_loss(score, result, trial)
            shrink += 1
        if new_loss > loss:
            break
        k, loss = trial, new_loss
        if abs(step) < 1e-10:
            return k, iteration
    return k, 100


def bucket_index(phase: np.ndarray, edges: tuple[int, ...]) -> np.ndarray:
    return np.searchsorted(np.asarray(edges[1:-1]), phase, side="right")


def bootstrap_k(data: dict, mask: np.ndarray, samples: int, rng: np.random.Generator, start: float) -> list[float]:
    """Percentile 95% interval of the fitted k: resample games when the data has game ids, else rows."""
    score, result = data["score"][mask], data["result"][mask]
    groups = None if data["group"] is None else data["group"][mask]
    values = []
    if groups is not None:
        unique, inverse = np.unique(groups, return_inverse=True)
        members = [np.flatnonzero(inverse == g) for g in range(len(unique))]
        for _ in range(samples):
            pick = rng.integers(0, len(unique), len(unique))
            rows = np.concatenate([members[g] for g in pick])
            values.append(fit_k(score[rows], result[rows], start)[0])
    else:
        n = len(score)
        for _ in range(samples):
            rows = rng.integers(0, n, n)
            values.append(fit_k(score[rows], result[rows], start)[0])
    values = np.sort(np.asarray(values))
    return [float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))]


def run(fit: dict, held: dict, edges: tuple[int, ...], samples: int, min_rows: int, seed: int) -> dict:
    """Per phase bucket: the fitted k with its bootstrap 95% CI. The delivered table uses a bucket's fitted k only
    when the bucket has at least min_rows fit rows AND its CI excludes the reference 2.25; otherwise it keeps 2.25
    (the current constant stays unless the fit set clearly says otherwise). Held-out log-loss is reported for the
    reference, one global fitted k, every bucket fitted ("always fit"), and the delivered table."""
    rng = np.random.default_rng(seed)
    global_k, global_iterations = fit_k(fit["score"], fit["result"])
    global_ci = bootstrap_k(fit, np.ones(fit["rows"], bool), samples, rng, global_k)
    fit_bucket, held_bucket = bucket_index(fit["phase"], edges), bucket_index(held["phase"], edges)
    table = []
    k_table_held = np.full(held["rows"], K_REFERENCE)
    k_always_held = np.full(held["rows"], global_k)
    for b in range(len(edges) - 1):
        mask = fit_bucket == b
        rows = int(mask.sum())
        entry = {"phase_from": edges[b], "phase_to_exclusive": edges[b + 1], "fit_rows": rows,
                 "holdout_rows": int((held_bucket == b).sum())}
        if rows >= min_rows:
            k, iterations = fit_k(fit["score"][mask], fit["result"][mask], global_k)
            entry.update(fitted_k=k, newton_iterations=iterations, k_ci95=bootstrap_k(fit, mask, samples, rng, k))
        else:
            entry.update(fitted_k=None, newton_iterations=0, k_ci95=None)
        entry["ci_excludes_reference"] = (entry["k_ci95"] is not None
                                          and not entry["k_ci95"][0] <= K_REFERENCE <= entry["k_ci95"][1])
        if entry["ci_excludes_reference"]:
            entry.update(k=entry["fitted_k"], source="fitted (CI excludes 2.25)")
        elif entry["fitted_k"] is None:
            entry.update(k=K_REFERENCE, source=f"reference 2.25 (fewer than {min_rows} fit rows)")
        else:
            entry.update(k=K_REFERENCE, source="reference 2.25 (CI includes 2.25)")
        hm = held_bucket == b
        k_table_held[hm] = entry["k"]
        k_always_held[hm] = global_k if entry["fitted_k"] is None else entry["fitted_k"]
        entry["holdout_logloss_reference"] = log_loss(held["score"][hm], held["result"][hm], K_REFERENCE) if hm.any() else None
        entry["holdout_logloss_table"] = log_loss(held["score"][hm], held["result"][hm], entry["k"]) if hm.any() else None
        table.append(entry)
    holdout = {
        "rows": held["rows"],
        "logloss_reference_k2.25": log_loss(held["score"], held["result"], K_REFERENCE),
        "logloss_global_k": log_loss(held["score"], held["result"], global_k),
        "logloss_always_fit": log_loss(held["score"], held["result"], k_always_held),
        "logloss_per_phase_table": log_loss(held["score"], held["result"], k_table_held),
    }
    holdout["table_minus_reference"] = holdout["logloss_per_phase_table"] - holdout["logloss_reference_k2.25"]
    holdout["always_fit_minus_reference"] = holdout["logloss_always_fit"] - holdout["logloss_reference_k2.25"]
    holdout["table_at_least_as_good_as_reference"] = holdout["table_minus_reference"] <= 0.0
    fit_summary = {"rows": fit["rows"], "logloss_reference_k2.25": log_loss(fit["score"], fit["result"], K_REFERENCE),
                   "logloss_global_k": log_loss(fit["score"], fit["result"], global_k)}
    return {"reference_k": K_REFERENCE, "global_k": global_k, "global_k_ci95": global_ci,
            "global_newton_iterations": global_iterations, "phase_table": table, "fit": fit_summary,
            "holdout": holdout, "bootstrap_samples": samples, "bootstrap_unit": "game" if fit["group"] is not None else "row",
            "min_rows_per_phase": min_rows, "seed": seed, "phase_edges": list(edges)}


def markdown(result: dict) -> str:
    lines = ["| phase | fit rows | holdout rows | fitted k | 95% CI | table k | holdout logloss k=2.25 | holdout logloss table |",
             "|---|---:|---:|---:|---|---:|---:|---:|"]
    for e in result["phase_table"]:
        fitted = "n/a" if e["fitted_k"] is None else f"{e['fitted_k']:.4f}"
        ci = "n/a" if e["k_ci95"] is None else f"[{e['k_ci95'][0]:.4f}, {e['k_ci95'][1]:.4f}]"
        ref = "n/a" if e["holdout_logloss_reference"] is None else f"{e['holdout_logloss_reference']:.6f}"
        tab = "n/a" if e["holdout_logloss_table"] is None else f"{e['holdout_logloss_table']:.6f}"
        lines.append(f"| {e['phase_from']}-{e['phase_to_exclusive'] - 1} | {e['fit_rows']:,} | {e['holdout_rows']:,} | "
                     f"{fitted} | {ci} | {e['k']:.4f} | {ref} | {tab} |")
    h = result["holdout"]
    lines.append("")
    lines.append(f"global fitted k {result['global_k']:.4f} (95% CI [{result['global_k_ci95'][0]:.4f}, {result['global_k_ci95'][1]:.4f}], "
                 f"bootstrap by {result['bootstrap_unit']}, {result['bootstrap_samples']} samples)")
    lines.append(f"holdout log-loss ({h['rows']:,} rows): k=2.25 {h['logloss_reference_k2.25']:.6f}; global k {h['logloss_global_k']:.6f}; "
                 f"every phase fitted {h['logloss_always_fit']:.6f} ({h['always_fit_minus_reference']:+.6f}); "
                 f"delivered table {h['logloss_per_phase_table']:.6f} ({h['table_minus_reference']:+.6f})")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fit-pos", nargs="*", default=[], type=Path)
    ap.add_argument("--holdout-pos", nargs="*", default=[], type=Path)
    ap.add_argument("--text", nargs="*", default=[], type=Path, help="text files, split into fit/holdout by game")
    ap.add_argument("--holdout-frac", type=float, default=0.3)
    ap.add_argument("--split-seed", default="s19")
    ap.add_argument("--edges", default=",".join(map(str, DEFAULT_EDGES)))
    ap.add_argument("--bootstrap", type=int, default=200)
    ap.add_argument("--min-rows", type=int, default=200)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--stride", type=int, default=1, help=".pos inputs: keep every stride-th row (rows 0, stride, ...)")
    ap.add_argument("--label", default="")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    edges = tuple(int(x) for x in args.edges.split(","))
    if edges[0] != 0 or edges[-1] <= MAX_PHASE or list(edges) != sorted(set(edges)):
        ap.error("--edges must start at 0, increase, and end above 24")
    if args.out.exists():
        ap.error("--out must be a new file")
    inputs = []
    if args.text:
        if args.fit_pos or args.holdout_pos:
            ap.error("use either --text or --fit-pos/--holdout-pos")
        fits, helds = [], []
        for path in args.text:
            text = read_text(path)
            held = game_split(text, str(path), args.holdout_frac, args.split_seed)
            fits.append(select(text, ~held)); helds.append(select(text, held))
            inputs.append({"path": str(path), "sha256": text["sha256"], "rows": text["rows"], "games": text["games"],
                           "bad_lines": text["bad_lines"], "holdout_rows": int(held.sum()),
                           "holdout_games": int(len(np.unique(text["group"][held])))})
        fit, held = concat(fits), concat(helds)
        split = {"kind": "by game", "frac": args.holdout_frac, "seed": args.split_seed}
    else:
        if not args.fit_pos or not args.holdout_pos:
            ap.error("--fit-pos and --holdout-pos are both required")
        fit_parts = [read_pos(p, args.stride) for p in args.fit_pos]
        held_parts = [read_pos(p, args.stride) for p in args.holdout_pos]
        for part, role in [(p, "fit") for p in fit_parts] + [(p, "holdout") for p in held_parts]:
            inputs.append({"path": part["path"], "sha256": part["sha256"], "rows": part["rows"],
                           "file_rows": part["file_rows"], "stride": part["stride"], "role": role})
        fit, held = concat(fit_parts), concat(held_parts)
        split = {"kind": "given files"}
    result = run(fit, held, edges, args.bootstrap, args.min_rows, args.seed)
    result.update(label=args.label, inputs=inputs, split=split, tool="forge_sol_S19_wdl_scale_fit",
                  status="UNPROVEN: fitted on the inputs listed; not a claim about engine strength or the full data")
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    md = markdown(result)
    args.out.with_suffix(".md").write_text(md, encoding="utf-8", newline="\n")
    print(md, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
