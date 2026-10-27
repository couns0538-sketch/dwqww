#!/usr/bin/env python3
"""S42 higher-variance opening book study: candidate book builder + opening statistics (Opus 5.5, 2026-10-27).

PROPOSAL + STATS ONLY. Nothing here plays games, touches a gate, or changes a live book. Every eval comes from OUR
engine (the AL1 lock exe) at a fixed depth, Threads=1, Hash=16, Idle priority, a fresh `ucinewgame` before every
position (python-chess `game=object()`), so a fixed seed reproduces the same files byte for byte.

Subcommands
  build    Candidate book v2: walk the current book's lines in a seeded order; at each line deviate once with a
           seeded random legal move, either replacing the line's last book move or one ply after its exit; skip
           checks, game-over, any current-book exit and repeats; score the new exit at the fixed depth and keep it
           when lo <= |eval| <= hi (White POV, cp). Stops at --target accepted positions (or --max-candidates).
           Writes forge_sol_S42_book_v2_<DATE>.epd (6-field FENs, fastchess format=epd), a metadata CSV, every
           scored candidate (.csv.gz), build_summary.json (deterministic) and run_info.json (timings).
  sample   Seeded sample of the current book's exits, scored at the same depth (eval histogram of the current book).
  gate     A gate PGN (read-only copy): pairs by Round, the book exit of each pair (moves commented {book}), the
           candidate's pair score, the pentanomial (checked against the RESULT's printed counts), and every exit
           scored at the same depth -> per-game CSV for the power model, per-bucket pair table.
Exit codes: 0 ok, 1 failed check, 2 usage. Needs python-chess + the engine exe (the PC's read-only NNUE venv).
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import os
import platform
import random
import sys
import time
from pathlib import Path

import chess
import chess.engine
import chess.pgn

DATE = "20261027"
TOOL = "forge_sol_S42_book_v2_" + DATE
BUCKETS = ((0, 20), (20, 40), (40, 60), (60, 120), (120, 200), (200, 10**9))


class Fail(Exception):
    pass


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def new_dir(p):
    p = Path(p)
    if p.exists() and any(p.iterdir()):
        raise Fail(f"{p} exists and is not empty (outputs are never overwritten)")
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_x(path, data):
    with open(path, "xb") as f:
        f.write(data if isinstance(data, bytes) else data.encode("utf-8"))


def epd4(board):
    return " ".join(board.fen().split()[:4])


def bucket(v):
    a = abs(v)
    for lo, hi in BUCKETS:
        if lo <= a < hi:
            return f"{lo}-{hi if hi < 10**9 else 'inf'}"
    return "inf"


class Engine:
    """Our engine at a fixed depth; White-POV centipawns (mate -> +-30000 minus plies)."""

    def __init__(self, exe, depth):
        kw = {"creationflags": 0x40} if os.name == "nt" else {}  # IDLE_PRIORITY_CLASS
        cmd = [sys.executable, "-I", "-B", str(exe)] if str(exe).endswith(".py") else [str(exe)]  # .py = test engine
        self.e = chess.engine.SimpleEngine.popen_uci(cmd, **kw)
        self.e.configure({"Threads": 1, "Hash": 16})
        self.depth = depth; self.calls = 0; self.id = dict(self.e.id)

    def score(self, board):
        info = self.e.analyse(board, chess.engine.Limit(depth=self.depth), game=object())  # ucinewgame every time
        self.calls += 1
        s = info["score"].white()
        return int(s.score(mate_score=30000)), int(info.get("nodes", -1)), int(info.get("depth", -1))

    def close(self):
        self.e.quit()


def read_book(path):
    """All mainlines of the current PGN book (python-chess), in file order."""
    lines = []
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        while True:
            g = chess.pgn.read_game(f)
            if g is None:
                break
            lines.append(list(g.mainline_moves()))
    return lines


def exits_of(lines):
    out = []
    for mv in lines:
        b = chess.Board()
        for m in mv:
            b.push(m)
        out.append(b)
    return out


# ------------------------------------------------------------------------------------------------ build
def build(a):
    out = new_dir(a.out); t0 = time.monotonic()
    lines = read_book(a.book); exits = exits_of(lines)
    book_ids = {epd4(b) for b in exits}
    eng = Engine(a.engine, a.depth)
    rng = random.Random(a.seed)
    order = list(range(len(lines))); rng.shuffle(order)
    cand_rows = []; acc = []; seen = set(); skipped = {"check_or_game_over": 0, "current_book_exit": 0, "repeat_candidate": 0, "no_legal_deviation": 0}
    try:
        for li in order:
            if len(acc) >= a.target or len(cand_rows) >= a.max_candidates:
                break
            mv = lines[li]
            dev = rng.choice((len(mv) - 1, len(mv)))   # replace the last book move, or deviate right after the exit
            b = chess.Board()
            for m in mv[:dev]:
                b.push(m)
            legal = sorted(b.legal_moves, key=lambda m: m.uci())
            if dev < len(mv):
                legal = [m for m in legal if m != mv[dev]]
            if not legal:
                skipped["no_legal_deviation"] += 1; continue
            m = legal[rng.randrange(len(legal))]
            san = b.san(m); b.push(m)
            if b.is_check() or b.is_game_over():
                skipped["check_or_game_over"] += 1; continue
            ident = epd4(b)
            if ident in book_ids:
                skipped["current_book_exit"] += 1; continue
            if ident in seen:
                skipped["repeat_candidate"] += 1; continue
            seen.add(ident)
            ev, nodes, depth = eng.score(b)
            ok = a.lo <= abs(ev) <= a.hi
            row = {"line": li + 1, "deviation_ply": dev + 1, "deviation_uci": m.uci(), "deviation_san": san, "fen": b.fen(),
                   "eval_white_cp": ev, "nodes": nodes, "depth": depth, "pieces": len(b.piece_map()), "accepted": int(ok)}
            cand_rows.append(row)
            if ok:
                acc.append(row)
    finally:
        eng.close()
    if len(acc) < a.target:
        print(f"warning: only {len(acc)} of {a.target} accepted within {len(cand_rows)} scored candidates", file=sys.stderr)
    # outputs (deterministic content)
    epd = "".join(r["fen"] + "\n" for r in acc)
    book_name = f"forge_sol_S42_book_v2_{DATE}.epd"
    write_x(out / book_name, epd)
    meta = io.StringIO(); w = csv.writer(meta, lineterminator="\n")
    cols = ["idx", "fen", "eval_white_cp", "favored", "nodes", "depth", "pieces", "source_line", "deviation_ply", "deviation_uci", "deviation_san"]
    w.writerow(cols)
    for i, r in enumerate(acc):
        w.writerow([i + 1, r["fen"], r["eval_white_cp"], "white" if r["eval_white_cp"] > 0 else "black", r["nodes"], r["depth"],
                    r["pieces"], r["line"], r["deviation_ply"], r["deviation_uci"], r["deviation_san"]])
    write_x(out / f"forge_sol_S42_book_v2_meta_{DATE}.csv", meta.getvalue())
    cz = io.StringIO(); w = csv.writer(cz, lineterminator="\n")
    ccols = ["line", "deviation_ply", "deviation_uci", "deviation_san", "fen", "eval_white_cp", "nodes", "depth", "pieces", "accepted"]
    w.writerow(ccols)
    for r in cand_rows:
        w.writerow([r[k] for k in ccols])
    gz = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=gz, mtime=0) as z:
        z.write(cz.getvalue().encode())
    write_x(out / f"forge_sol_S42_candidates_{DATE}.csv.gz", gz.getvalue())
    # checks: no duplicate with the current book's exits, no repeat inside the new book
    new_ids = [epd4(chess.Board(r["fen"])) for r in acc]
    hist_all = {}; hist_acc = {}
    for r in cand_rows:
        hist_all[bucket(r["eval_white_cp"])] = hist_all.get(bucket(r["eval_white_cp"]), 0) + 1
    summary = {"tool": TOOL, "tool_sha256": sha256(__file__), "mode": "build",
               "parameters": {"book": Path(a.book).name, "book_sha256": sha256(a.book), "engine_sha256": sha256(a.engine),
                              "engine_id": eng.id, "depth": a.depth, "band_abs_cp": [a.lo, a.hi], "target": a.target, "seed": a.seed,
                              "max_candidates": a.max_candidates, "uci": "Threads=1 Hash=16, ucinewgame before every position"},
               "current_book_lines": len(lines), "current_book_unique_exits": len(book_ids),
               "lines_visited": sum(skipped.values()) + len(cand_rows), "skipped": skipped, "scored": len(cand_rows), "accepted": len(acc),
               "acceptance_rate": round(len(acc) / max(1, len(cand_rows)), 4),
               "duplicates_with_current_book_exits": sum(i in book_ids for i in new_ids),
               "repeats_inside_new_book": len(new_ids) - len(set(new_ids)),
               "favored": {"white": sum(r["eval_white_cp"] > 0 for r in acc), "black": sum(r["eval_white_cp"] < 0 for r in acc)},
               "deviation_ply": {str(k): sum(r["deviation_ply"] == k for r in acc) for k in sorted({r["deviation_ply"] for r in acc})},
               "eval_histogram_scored_candidates": dict(sorted(hist_all.items())),
               "accepted_abs_eval": {"min": min((abs(r["eval_white_cp"]) for r in acc), default=None),
                                     "max": max((abs(r["eval_white_cp"]) for r in acc), default=None),
                                     "mean": round(sum(abs(r["eval_white_cp"]) for r in acc) / max(1, len(acc)), 2)},
               "outputs": {}}
    for p in sorted(out.iterdir()):
        summary["outputs"][p.name] = sha256(p)
    write_x(out / "build_summary.json", json.dumps(summary, indent=1) + "\n")
    write_x(out / "run_info.json", json.dumps({"argv": sys.argv, "seconds": round(time.monotonic() - t0, 1), "engine_calls": eng.calls,
                                                 "python": sys.version.split()[0], "chess": chess.__version__, "platform": platform.platform()}, indent=1) + "\n")
    print(json.dumps({k: summary[k] for k in ("scored", "accepted", "acceptance_rate", "skipped", "favored", "duplicates_with_current_book_exits",
                                              "repeats_inside_new_book")}, indent=1))
    print(f"{book_name} sha256 {summary['outputs'][book_name]}")
    return 0 if summary["duplicates_with_current_book_exits"] == 0 and summary["repeats_inside_new_book"] == 0 else 1


# ------------------------------------------------------------------------------------------------ sample (current book)
def sample(a):
    out = new_dir(a.out); t0 = time.monotonic()
    lines = read_book(a.book); exits = exits_of(lines)
    rng = random.Random(a.seed); idx = sorted(rng.sample(range(len(lines)), min(a.n, len(lines))))
    eng = Engine(a.engine, a.depth); rows = []
    try:
        for i in idx:
            ev, nodes, depth = eng.score(exits[i])
            rows.append([i + 1, exits[i].fen(), ev, nodes, depth])
    finally:
        eng.close()
    s = io.StringIO(); w = csv.writer(s, lineterminator="\n"); w.writerow(["line", "fen", "eval_white_cp", "nodes", "depth"]); w.writerows(rows)
    name = f"forge_sol_S42_current_book_sample_{DATE}.csv"
    write_x(out / name, s.getvalue())
    hist = {}
    for r in rows:
        hist[bucket(r[2])] = hist.get(bucket(r[2]), 0) + 1
    summ = {"tool": TOOL, "mode": "sample", "book": Path(a.book).name, "book_sha256": sha256(a.book), "engine_sha256": sha256(a.engine),
            "depth": a.depth, "seed": a.seed, "n": len(rows), "abs_eval_histogram": dict(sorted(hist.items())),
            "share_in_60_120": round(sum(60 <= abs(r[2]) <= 120 for r in rows) / max(1, len(rows)), 4), "csv_sha256": sha256(out / name)}
    write_x(out / "sample_summary.json", json.dumps(summ, indent=1) + "\n")
    write_x(out / "run_info.json", json.dumps({"argv": sys.argv, "seconds": round(time.monotonic() - t0, 1)}, indent=1) + "\n")
    print(json.dumps(summ, indent=1))
    return 0


# ------------------------------------------------------------------------------------------------ gate PGN
def gate(a):
    out = new_dir(a.out); t0 = time.monotonic()
    games = []
    with open(a.pgn, encoding="utf-8-sig", errors="replace") as f:
        while True:
            g = chess.pgn.read_game(f)
            if g is None:
                break
            b = g.board(); book = 0
            for node in g.mainline():
                if node.comment.strip() != "book":
                    break
                b.push(node.move); book += 1
            games.append({"round": int(g.headers["Round"]), "white": g.headers["White"], "black": g.headers["Black"],
                          "result": g.headers["Result"], "book_plies": book, "exit": b.fen(), "board": b,
                          "termination": g.headers.get("Termination", "")})
    by_round = {}
    for gm in games:
        by_round.setdefault(gm["round"], []).append(gm)
    pts = {"1-0": (1.0, 0.0), "0-1": (0.0, 1.0), "1/2-1/2": (0.5, 0.5)}
    pairs = []; problems = []
    for r in sorted(by_round):
        g2 = by_round[r]
        if len(g2) != 2:
            problems.append(f"round {r}: {len(g2)} games"); continue
        if epd4(g2[0]["board"]) != epd4(g2[1]["board"]):
            problems.append(f"round {r}: different exits"); continue
        sc = 0.0; rows = []
        for gm in g2:
            if gm["result"] not in pts:
                problems.append(f"round {r}: result {gm['result']}"); break
            cw = gm["white"] == a.cand
            if not cw and gm["black"] != a.cand:
                raise Fail(f"candidate {a.cand} not in round {r}")
            p = pts[gm["result"]][0 if cw else 1]; sc += p
            rows.append((cw, p))
        pairs.append({"round": r, "exit": g2[0]["exit"], "board": g2[0]["board"], "pair_points": sc, "games": rows,
                      "book_plies": g2[0]["book_plies"]})
    ptnml = [0] * 5
    for p in pairs:
        ptnml[int(round(p["pair_points"] * 2))] += 1
    if a.expect_ptnml:
        exp = [int(x) for x in a.expect_ptnml.split(",")]
        if ptnml != exp:
            raise Fail(f"pentanomial from the PGN {ptnml} != the RESULT's printed {exp}")
    eng = Engine(a.engine, a.depth)
    try:
        for p in pairs:
            p["eval"], p["nodes"], p["depth"] = eng.score(p["board"])
    finally:
        eng.close()
    s = io.StringIO(); w = csv.writer(s, lineterminator="\n")
    w.writerow(["round", "exit_fen", "book_plies", "eval_white_cp", "cand_is_white", "cand_points"])
    for p in pairs:
        for cw, pt in p["games"]:
            w.writerow([p["round"], p["exit"], p["book_plies"], p["eval"], int(cw), pt])
    name = f"forge_sol_S42_gate_games_{Path(a.pgn).stem}_{DATE}.csv"
    write_x(out / name, s.getvalue())
    table = {}
    for p in pairs:
        k = bucket(p["eval"]); t = table.setdefault(k, {"pairs": 0, "ptnml": [0] * 5, "decisive_games": 0})
        t["pairs"] += 1; t["ptnml"][int(round(p["pair_points"] * 2))] += 1
        t["decisive_games"] += sum(pt != 0.5 for _, pt in p["games"])
    for t in table.values():
        t["share_1_1_pairs"] = round(t["ptnml"][2] / t["pairs"], 4); t["decisive_game_rate"] = round(t["decisive_games"] / (2 * t["pairs"]), 4)
        t["cand_score"] = round(sum(i * c for i, c in enumerate(t["ptnml"])) / (4 * t["pairs"]), 4)
    summ = {"tool": TOOL, "mode": "gate", "pgn": Path(a.pgn).name, "pgn_sha256": sha256(a.pgn), "candidate": a.cand,
            "engine_sha256": sha256(a.engine), "depth": a.depth, "games": len(games), "pairs": len(pairs), "problems": problems,
            "ptnml_from_pgn": ptnml, "ptnml_expected": a.expect_ptnml, "share_1_1_pairs": round(ptnml[2] / max(1, len(pairs)), 4),
            "by_abs_exit_eval": dict(sorted(table.items(), key=lambda kv: float(kv[0].split("-")[0]))), "csv_sha256": sha256(out / name),
            "terminations": sorted({gm["termination"] for gm in games})}
    write_x(out / "gate_summary.json", json.dumps(summ, indent=1) + "\n")
    write_x(out / "run_info.json", json.dumps({"argv": sys.argv, "seconds": round(time.monotonic() - t0, 1)}, indent=1) + "\n")
    print(json.dumps({k: summ[k] for k in ("games", "pairs", "problems", "ptnml_from_pgn", "share_1_1_pairs", "by_abs_exit_eval")}, indent=1))
    return 0 if not problems else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0]); sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build"); b.add_argument("--book", required=True); b.add_argument("--engine", required=True)
    b.add_argument("--depth", type=int, default=12); b.add_argument("--lo", type=int, default=60); b.add_argument("--hi", type=int, default=120)
    b.add_argument("--target", type=int, default=1000); b.add_argument("--max-candidates", type=int, default=10000)
    b.add_argument("--seed", type=int, default=20261027); b.add_argument("--out", required=True)
    s = sub.add_parser("sample"); s.add_argument("--book", required=True); s.add_argument("--engine", required=True)
    s.add_argument("--depth", type=int, default=12); s.add_argument("--n", type=int, default=2000); s.add_argument("--seed", type=int, default=20261027)
    s.add_argument("--out", required=True)
    g = sub.add_parser("gate"); g.add_argument("--pgn", required=True); g.add_argument("--cand", required=True)
    g.add_argument("--engine", required=True); g.add_argument("--depth", type=int, default=12)
    g.add_argument("--expect-ptnml"); g.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    try:
        return {"build": build, "sample": sample, "gate": gate}[a.cmd](a)
    except Fail as exc:
        print(f"FAILED: {exc}", file=sys.stderr); return 1


if __name__ == "__main__":
    raise SystemExit(main())
