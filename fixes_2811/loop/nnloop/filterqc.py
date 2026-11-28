"""Filter and quality-check one round of data.

Input: raw files from datagen (.binpack from the official generator, .plain from self-play).
Output: filtered.binpack (what the trainer reads), raw.binpack (untouched archive), qc.json.

A filtered position is not deleted. Its score is set to VALUE_NONE (32002), which the nnue-pytorch
loader skips. Keeping the record keeps the move chains intact, so the binpack stays small.
Positions in check and positions whose best move is a capture are skipped by the loader itself
(its `filtered` option), so they are not handled here.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

from .common import VALUE_NONE, atomic_write_json, child_env, log, run_logged, tail_text

SCORE_EDGES = [50, 100, 200, 400, 800, 1600]


def tools_convert(cfg: dict, src: Path, dst: Path, log_path: Path, validate: bool = False) -> None:
    """Convert between .plain and .binpack with the official tools-branch converter."""
    tmp = dst.with_name("tmp_" + dst.name)
    tmp.unlink(missing_ok=True)
    line = f"convert {src} {tmp}" + (" validate" if validate else "")
    rc = run_logged([cfg["sf_tools"]["cmd"]], log_path, cwd=str(dst.parent), env=child_env(cfg),
                    stdin_text=line + "\nquit\n")
    if rc != 0 or not tmp.exists() or tmp.stat().st_size == 0:
        raise RuntimeError(f"convert {src.name} -> {dst.name} failed (exit {rc}); "
                           f"log tail:\n{tail_text(log_path, 1500)}")
    os.replace(tmp, dst)


def filter_round(cfg: dict, raw_dir: Path, out_dir: Path) -> dict:
    f = cfg["filter"]
    out_dir.mkdir(parents=True, exist_ok=True)
    work = out_dir / "work"
    work.mkdir(exist_ok=True)
    clog = out_dir / "convert.log"
    t0 = time.time()

    # 1. everything to .plain
    plains: list[Path] = []
    raw_binpacks = sorted(raw_dir.glob("*.binpack"))
    raw_plains = sorted(raw_dir.glob("*.plain"))
    for bp in raw_binpacks:
        pl = work / (bp.stem + ".plain")
        if not pl.exists():
            tools_convert(cfg, bp, pl, clog)
        plains.append(pl)
    plains.extend(raw_plains)
    if not plains:
        raise RuntimeError(f"no raw data in {raw_dir}")

    max_abs = int(f.get("max_abs_score", 3000))
    min_ply = int(f.get("min_ply", 0))
    max_ply = int(f.get("max_ply", 10**9))
    dedup = bool(f.get("dedup", True))
    conflict = int(f.get("conflict_score", 0))
    max_r50 = int(f.get("max_halfmove_clock", 1000))
    min_pieces = int(f.get("min_pieces", 0))

    seen: set[int] = set()
    n = kept = 0
    why = {"score_limit": 0, "ply": 0, "duplicate": 0, "score_result_conflict": 0, "rule50": 0,
           "few_pieces": 0, "already_none": 0}
    res_kept = {-1: 0, 0: 0, 1: 0}
    score_hist = [0] * (len(SCORE_EDGES) + 1)
    ply_hist: dict[int, int] = {}
    pc_hist: dict[int, int] = {}
    sum_abs = 0
    sum_sq = 0
    sum_s = sum_r = sum_rr = sum_sr = 0
    games = 0
    last_ply = 10**9

    merged = work / "filtered.plain"
    with open(merged, "w", encoding="ascii", newline="\n") as out:
        for pl in plains:
            fen = move = ""
            score = ply = result = 0
            with open(pl, "r", encoding="ascii", errors="replace") as fh:
                for line in fh:
                    c = line[:1]
                    if c == "f":
                        fen = line[4:].rstrip("\r\n")
                    elif c == "m":
                        move = line[5:].rstrip("\r\n")
                    elif c == "s":
                        score = int(float(line[6:]))
                    elif c == "p":
                        ply = int(line[4:])
                    elif c == "r":
                        result = int(line[7:])
                    elif c == "e":
                        n += 1
                        if ply < last_ply:
                            games += 1
                        last_ply = ply
                        parts = fen.split(" ")
                        reason = None
                        if score == VALUE_NONE:
                            reason = "already_none"
                        elif abs(score) > max_abs:
                            reason = "score_limit"
                        elif ply < min_ply or ply > max_ply:
                            reason = "ply"
                        elif conflict and result != 0 and abs(score) >= conflict and (score > 0) != (result > 0):
                            reason = "score_result_conflict"
                        elif len(parts) > 4 and parts[4].isdigit() and int(parts[4]) > max_r50:
                            reason = "rule50"
                        else:
                            pieces = sum(ch.isalpha() for ch in parts[0])
                            if pieces < min_pieces:
                                reason = "few_pieces"
                            elif dedup:
                                key = hash(" ".join(parts[:4]))
                                if key in seen:
                                    reason = "duplicate"
                                else:
                                    seen.add(key)
                        if reason is None:
                            kept += 1
                            res_kept[result] = res_kept.get(result, 0) + 1
                            a = abs(score)
                            sum_abs += a
                            sum_sq += a * a
                            sum_s += score
                            sum_r += result
                            sum_rr += result * result
                            sum_sr += score * result
                            b = 0
                            while b < len(SCORE_EDGES) and a >= SCORE_EDGES[b]:
                                b += 1
                            score_hist[b] += 1
                            ply_hist[ply // 20 * 20] = ply_hist.get(ply // 20 * 20, 0) + 1
                            pc_hist[pieces] = pc_hist.get(pieces, 0) + 1
                            out_score = score
                        else:
                            why[reason] += 1
                            out_score = VALUE_NONE
                        out.write(f"fen {fen}\nmove {move}\nscore {out_score}\nply {ply}\nresult {result}\ne\n")
    del seen
    if n == 0:
        raise RuntimeError("filter: no records found in raw data")

    # 2. what the trainer reads: a binpack (official trainer) or the text file itself (other trainers)
    if f.get("output", "binpack") == "plain":
        filtered = out_dir / "filtered.plain"
        os.replace(merged, filtered)
    else:
        filtered = out_dir / "filtered.binpack"
        tools_convert(cfg, merged, filtered, clog, validate=True)

    # 3. archive the untouched raw data as binpack and drop the bulky text
    raw_archive = []
    if raw_plains:
        cat = work / "raw_selfplay.plain"
        with open(cat, "wb") as o:
            for pl in raw_plains:
                with open(pl, "rb") as i:
                    while True:
                        block = i.read(1 << 22)
                        if not block:
                            break
                        o.write(block)
        arch = out_dir / "raw_selfplay.binpack"
        tools_convert(cfg, cat, arch, clog)
        raw_archive.append(str(arch))
        cat.unlink(missing_ok=True)
        for pl in raw_plains:
            pl.unlink(missing_ok=True)
    raw_archive.extend(str(p) for p in raw_binpacks)
    for p in work.glob("*.plain"):
        p.unlink(missing_ok=True)
    try:
        work.rmdir()
    except OSError:
        pass

    mean_abs = sum_abs / kept if kept else 0.0
    rms = (sum_sq / kept) ** 0.5 if kept else 0.0
    # Pearson correlation of score and game result (both from the side to move): a label-quality figure
    corr = None
    if kept > 1:
        var_s = sum_sq / kept - (sum_s / kept) ** 2
        var_r = sum_rr / kept - (sum_r / kept) ** 2
        if var_s > 0 and var_r > 0:
            corr = round((sum_sr / kept - (sum_s / kept) * (sum_r / kept)) / (var_s * var_r) ** 0.5, 4)
    qc = {
        "records": n, "kept": kept, "kept_pct": round(100.0 * kept / n, 2), "games": games,
        "marked_skip": why,
        "result_side_to_move": {"loss": res_kept.get(-1, 0), "draw": res_kept.get(0, 0), "win": res_kept.get(1, 0)},
        "draw_pct": round(100.0 * res_kept.get(0, 0) / kept, 2) if kept else 0.0,
        "abs_score_mean": round(mean_abs, 1), "abs_score_rms": round(rms, 1), "score_result_corr": corr,
        "abs_score_hist": {(f"<{SCORE_EDGES[0]}" if i == 0 else f">={SCORE_EDGES[i - 1]}"): c
                           for i, c in enumerate(score_hist)},
        "ply_hist": {str(k): v for k, v in sorted(ply_hist.items())},
        "piece_count_hist": {str(k): v for k, v in sorted(pc_hist.items())},
        "filtered": str(filtered), "filtered_bytes": filtered.stat().st_size,
        "raw_archive": raw_archive, "seconds": round(time.time() - t0, 1),
        "rules": {"max_abs_score": max_abs, "min_ply": min_ply, "max_ply": max_ply, "dedup": dedup,
                  "conflict_score": conflict, "max_halfmove_clock": max_r50, "min_pieces": min_pieces},
    }
    atomic_write_json(out_dir / "qc.json", qc)
    log(f"filter: {n} records, {kept} kept ({qc['kept_pct']}%), marked {why}, draws {qc['draw_pct']}%, "
        f"mean |score| {qc['abs_score_mean']}, {filtered.stat().st_size / 2**20:.1f} MB {filtered.suffix}")
    return qc
