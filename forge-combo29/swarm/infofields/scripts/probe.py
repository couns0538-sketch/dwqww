"""Probe battery for the info-line field audit.

Each probe writes one JSON object into ../evidence/. Every probe states the
settings it ran under, because a number without its build and settings is not a
result (brief rule 7).
"""

import json
import os
import sys
import time

import chess

import uci

ENGINE = os.environ.get("FORGE_BIN", "/agent/repos/work-infofields/build/forge")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evidence")
os.makedirs(OUT, exist_ok=True)

SETTINGS = {
    "build": "g++ / -DFORGE_MARCH=x86-64-v4 / Release / NDEBUG",
    "base_commit": "6b98f217",
    "threads": 1,
    "hash_mb": 32,
    "own_book": False,
    "pins": {"bench11": 312866, "bench13": 862329, "bench16": 3024920, "perft5": 4865609},
}


def new_engine(**options):
    e = uci.Engine(ENGINE)
    e.handshake()
    e.setoption("OwnBook", "false")
    for k, v in options.items():
        e.setoption(k.replace("_", " "), v)
    return e


def depth_lines(lines):
    return [l for l in lines if l.startswith("info depth")]


def parse_all(lines):
    out = []
    for l in lines:
        f, pv = uci.parse_info(l)
        if f is None:
            continue
        if "depth" not in f:
            continue
        f = dict(f)
        f["pv_moves"] = pv
        f["_line"] = l
        out.append(f)
    return out


def dump(name, payload):
    path = os.path.join(OUT, name + ".json")
    with open(path, "w") as fh:
        json.dump(payload, fh, indent=1, sort_keys=True)
    print("wrote", os.path.basename(path))


def probe_depth_bail():
    """depth on a drawn root: the line claims a depth nothing searched."""
    e = new_engine()
    results = []
    fen = "8/8/8/4k3/8/8/8/4K3 w - - 0 1"
    e.position(fen)
    lines, bm = e.search("depth 10")
    results.append({"case": "drawn root (bare kings, insufficient material)",
                    "fen": fen, "go": "depth 10", "lines": lines, "bestmove": bm})

    fen2 = "7k/5Q2/6K1/8/8/8/8/8 w - - 0 1"  # stalemate? validated below
    assert not chess.Board(fen2).is_stalemate()
    e.position(fen2)
    lines2, bm2 = e.search("depth 6")
    results.append({"case": "stalemate root", "fen": fen2, "go": "depth 6",
                    "lines": lines2, "bestmove": bm2,
                    "python_chess_stalemate": chess.Board(fen2).is_stalemate()})
    e.quit()
    dump("depth_bail", {"settings": SETTINGS, "cases": results})


def probe_depth_abort():
    """depth vs the abort revision line.

    The abort branch can publish a pv from an *unfinished* iteration under that
    iteration's depth. Detect it by comparing an aborted run's ladder against a
    cold-table reference ladder at the same depths.
    """
    e = new_engine()
    fen = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
    chess.Board(fen)

    e.position(fen)
    ref_lines, ref_bm = e.search("depth 12")
    ref = {int(d["depth"]): d for d in parse_all(ref_lines)}

    aborted = []
    for stop_after in (0.25, 0.45, 0.70, 1.0, 1.4):
        e.send("setoption name Hash value 32")  # forces a cold table (known trap)
        e.send("isready")
        e.read_until(lambda l: l.strip() == "readyok")
        e.position(fen)
        lines, bm = e.search("depth 40", stop_after=stop_after)
        rows = []
        for d in parse_all(lines):
            k = int(d["depth"])
            r = ref.get(k)
            rows.append({
                "depth": k, "nodes": int(d["nodes"]), "time": int(d["time"]),
                "score": d["score"], "pv": d["pv_moves"],
                "ref_nodes": int(r["nodes"]) if r else None,
                "ref_pv": r["pv_moves"] if r else None,
                "depth_seen_twice": sum(1 for x in parse_all(lines) if x["depth"] == d["depth"]) > 1,
            })
        aborted.append({"stop_after_s": stop_after, "rows": rows, "bestmove": bm,
                        "raw_tail": lines[-3:]})
    e.quit()
    dump("depth_abort", {"settings": SETTINGS, "fen": fen,
                         "reference_depth_12": {str(k): {"nodes": int(v["nodes"]),
                                                          "pv": v["pv_moves"]} for k, v in ref.items()},
                         "aborted": aborted})


def probe_seldepth():
    """seldepth: >= depth, and genuinely the deepest ply incl. qsearch."""
    e = new_engine()
    out = []
    fens = [
        ("startpos", None),
        ("mate in 1 (Ra8#)", "6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1"),
        ("tactical kiwipete", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"),
        ("quiet rook ending", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"),
    ]
    for name, fen in fens:
        if fen:
            chess.Board(fen)
        e.position(fen)
        lines, bm = e.search("depth 14")
        rows = [{"depth": int(d["depth"]), "seldepth": int(d["seldepth"]),
                 "nodes": int(d["nodes"]), "pv_len": len(d["pv_moves"])}
                for d in parse_all(lines)]
        out.append({"case": name, "fen": fen, "rows": rows, "bestmove": bm})

    # bail: seldepth is fabricated as max(0, depth)
    e.position("8/8/8/4k3/8/8/8/4K3 w - - 0 1")
    lines, bm = e.search("depth 8")
    out.append({"case": "drawn root bail (0 nodes)",
                "rows": [{"depth": int(d["depth"]), "seldepth": int(d["seldepth"]),
                          "nodes": int(d["nodes"])} for d in parse_all(lines)],
                "bestmove": bm})
    e.quit()
    dump("seldepth", {"settings": SETTINGS, "cases": out})


def probe_multipv():
    """multipv: 1-based, contiguous, present on every line when MultiPV > 1."""
    out = []
    for n in (1, 2, 3, 4):
        e = new_engine(MultiPV=n)
        e.position()
        lines, bm = e.search("depth 8")
        rows = []
        for d in parse_all(lines):
            rows.append({"depth": int(d["depth"]),
                         "multipv": int(d["multipv"]) if "multipv" in d else None,
                         "nodes": int(d["nodes"]), "hashfull": int(d["hashfull"]),
                         "pv0": d["pv_moves"][0] if d["pv_moves"] else None})
        out.append({"setting": n, "rows": rows, "bestmove": bm})
        e.quit()

    # MultiPV > 1 on a bailed root
    e = new_engine(MultiPV=3)
    e.position("8/8/8/4k3/8/8/8/4K3 w - - 0 1")
    lines, bm = e.search("depth 5")
    bail = {"setting": 3, "case": "drawn root bail", "lines": lines, "bestmove": bm}
    e.quit()

    # MultiPV > 1 on the book path. One `go` only: sending a second `go` while
    # the first search is live would make the reader attribute the first
    # search's output to the second, which is how a control fabricates a result.
    e = uci.Engine(ENGINE)
    e.handshake()
    e.setoption("OwnBook", "true")
    e.setoption("MultiPV", "3")
    e.position()
    lines, bm = e.search("movetime 200")
    book = {"setting": 3, "case": "book path", "lines": lines, "bestmove": bm}
    e.quit()
    dump("multipv", {"settings": SETTINGS, "by_setting": out, "bail": bail, "book": book})


def probe_score_relativity():
    """score must be side-to-move relative."""
    e = new_engine()
    out = []

    # A board where White is a clean rook up, searched from both sides to move.
    pairs = [
        ("rook up, White to move", "4k3/8/8/8/8/8/8/4K2R w - - 0 1"),
        ("same board, Black to move", "4k3/8/8/8/8/8/8/4K2R b - - 0 1"),
    ]
    for name, fen in pairs:
        chess.Board(fen)
        e.position(fen)
        lines, bm = e.search("depth 12")
        last = parse_all(lines)[-1]
        out.append({"case": name, "fen": fen, "score": last["score"],
                    "line": last["_line"], "bestmove": bm})

    # Mirror: colours swapped so the engine's own POV should negate exactly.
    base = "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 6 6"
    mirrored = chess.Board(base).mirror().fen(en_passant="fen")
    for name, fen in (("base", base), ("mirrored", mirrored)):
        chess.Board(fen)
        e.position(fen)
        lines, bm = e.search("depth 10")
        last = parse_all(lines)[-1]
        out.append({"case": name, "fen": fen, "score": last["score"],
                    "line": last["_line"], "bestmove": bm})

    # Mate scores from both sides: a position White mates in, and its mirror
    # where Black mates. Both fixtures are validated, and a refused FEN would
    # manufacture a pass, so the wire is checked for a refusal too.
    e = new_engine()
    mate_white = "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1"
    mate_black = chess.Board(mate_white).mirror().fen(en_passant="fen")
    for name, fen in (("White mates, White to move", mate_white),
                      ("Black mates, Black to move (mirror)", mate_black)):
        chess.Board(fen)
        e.position(fen)
        lines, bm = e.search("depth 10")
        parsed = parse_all(lines)
        out.append({"case": name, "fen": fen,
                    "score": parsed[-1]["score"] if parsed else None,
                    "lines": lines, "bestmove": bm,
                    "refused": any(l.startswith("info string invalid FEN") for l in lines)})

    # A genuine checkmate root: mate 0 is the only mate score allowed to be 0.
    e.position("6k1/6Q1/6K1/8/8/8/8/8 b - - 0 1")
    lines, bm = e.search("depth 4")
    out.append({"case": "checkmate root, mated side to move",
                "fen": "6k1/6Q1/6K1/8/8/8/8/8 b - - 0 1",
                "lines": lines, "bestmove": bm,
                "python_chess_checkmate": chess.Board("6k1/6Q1/6K1/8/8/8/8/8 b - - 0 1").is_checkmate()})

    # Mate in N with N > 1, from the delivering side: the number must be plies/2
    # rounded as UCI specifies (moves, not plies, from the side to move).
    for name, fen, expected in (
            ("mate in 1", "6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1", 1),
            ("mate in 2", "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1", 2),):
        chess.Board(fen)
        e.position(fen)
        lines, bm = e.search("depth 8")
        parsed = parse_all(lines)
        out.append({"case": name, "fen": fen, "score": parsed[-1]["score"],
                    "expected_mate_in": expected, "line": parsed[-1]["_line"],
                    "bestmove": bm})
    e.quit()
    dump("score_relativity", {"settings": SETTINGS, "cases": out})


def probe_nodes():
    """nodes: monotone within a search; final line vs the bench node total."""
    out = {}

    # (a) monotonicity at MultiPV 1
    e = new_engine()
    e.position()
    lines, bm = e.search("depth 16")
    seq = [int(d["nodes"]) for d in parse_all(lines)]
    out["multipv1_sequence"] = seq
    out["multipv1_monotone"] = all(b >= a for a, b in zip(seq, seq[1:]))
    e.quit()

    # (b) monotonicity at MultiPV 3 -- the candidate violation
    e = new_engine(MultiPV=3)
    e.position()
    lines, bm = e.search("depth 10")
    rows = [(int(d["depth"]), int(d["multipv"]), int(d["nodes"])) for d in parse_all(lines)]
    out["multipv3_rows"] = rows
    viol = []
    for i in range(1, len(rows)):
        if rows[i][2] < rows[i - 1][2]:
            viol.append({"prev": rows[i - 1], "cur": rows[i]})
    out["multipv3_monotone"] = not viol
    out["multipv3_violations"] = viol
    out["multipv3_raw"] = lines
    e.quit()

    # (c) final line vs bench total, Threads 1, per bench FEN
    bench_fens = [
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
        "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
        "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
        "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
    ]
    e = new_engine()
    per = []
    total = 0
    for fen in bench_fens:
        e.position(fen)
        lines, bm = e.search("depth 11")
        parsed = parse_all(lines)
        n = int(parsed[-1]["nodes"])
        total += n
        per.append({"fen": fen, "nodes": n, "line": parsed[-1]["_line"]})
    out["bench_depth_11_per_fen"] = per
    out["bench_depth_11_sum"] = total
    out["bench_pin"] = 312866
    e.quit()
    dump("nodes", {"settings": SETTINGS, **out})


def probe_nps():
    """nps must be nodes/time, and must not be a 0 sentinel that reads as a rate."""
    e = new_engine()
    bad = []
    zero_time = []
    total = 0
    for fen in (None, "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"):
        e.position(fen)
        lines, bm = e.search("depth 14")
        for d in parse_all(lines):
            total += 1
            n, t, p = int(d["nodes"]), int(d["time"]), int(d["nps"])
            if t == 0:
                zero_time.append({"nodes": n, "time": t, "nps": p, "line": d["_line"]})
                continue
            expect = n * 1000 // t
            if p != expect:
                bad.append({"nodes": n, "time": t, "nps": p, "expected": expect,
                            "line": d["_line"]})
    e.quit()
    dump("nps", {"settings": SETTINGS, "lines_checked": total,
                 "mismatches": bad, "zero_time_lines": zero_time,
                 "zero_time_count": len(zero_time),
                 "zero_time_max_nodes": max([z["nodes"] for z in zero_time], default=0)})


def probe_hashfull():
    """hashfull: per-mille, 0..1000, and one table per search."""
    e = new_engine()
    e.position()
    lines, bm = e.search("depth 20")
    vals = [int(d["hashfull"]) for d in parse_all(lines)]
    out = {"multipv1_series": vals, "min": min(vals), "max": max(vals),
           "in_range": all(0 <= v <= 1000 for v in vals),
           "monotone": all(b >= a for a, b in zip(vals, vals[1:]))}
    e.quit()

    # MultiPV: hashfull per line comes from different tables.
    e = new_engine(MultiPV=3)
    e.position()
    lines, bm = e.search("depth 18")
    rows = [(int(d["depth"]), int(d["multipv"]), int(d["hashfull"])) for d in parse_all(lines)]
    out["multipv3_rows"] = rows
    out["multipv3_last_depth"] = [r for r in rows if r[0] == max(x[0] for x in rows)]
    out["multipv3_raw_tail"] = lines[-4:]
    e.quit()
    dump("hashfull", {"settings": SETTINGS, **out})


def probe_time():
    """time: milliseconds since when? ordinary vs ponder."""
    out = {}

    # ordinary, go depth: origin is worker entry, budget origin is the same.
    e = new_engine()
    e.position()
    t0 = time.monotonic()
    lines, bm = e.search("depth 18")
    wall = time.monotonic() - t0
    parsed = parse_all(lines)
    out["depth18"] = {"wall_s": round(wall, 3), "last_time_ms": int(parsed[-1]["time"]),
                      "last_line": parsed[-1]["_line"],
                      "series": [int(d["time"]) for d in parsed],
                      "monotone": all(b >= a for a, b in
                                      zip([int(d["time"]) for d in parsed],
                                          [int(d["time"]) for d in parsed][1:]))}

    # ordinary, movetime: time should track the movetime budget.
    e.position()
    t0 = time.monotonic()
    lines, bm = e.search("movetime 1200")
    wall = time.monotonic() - t0
    parsed = parse_all(lines)
    out["movetime1200"] = {"wall_s": round(wall, 3),
                           "last_time_ms": int(parsed[-1]["time"]),
                           "last_line": parsed[-1]["_line"],
                           "budget_ms": 1190}
    e.quit()

    # ponder: budget counts from ponderhit, `time` counts from `go`.
    e = new_engine()
    e.position()
    t_go = time.monotonic()
    e.send("go ponder wtime 600000 btime 600000")
    time.sleep(2.0)
    during = []
    # snapshot what was printed so far without touching the search
    while True:
        try:
            during.append(e.lines.get(timeout=0.02))
        except Exception:
            break
    t_hit = time.monotonic()
    e.send("ponderhit")
    rest = e.read_until(lambda l: l.startswith("bestmove"), timeout=120)
    t_end = time.monotonic()
    parsed_rest = parse_all(rest)

    # The engine's own budget clock is elapsed_ms(); observe the stop moment.
    out["ponder"] = {
        "ponder_wait_s": round(t_hit - t_go, 3),
        "wall_from_hit_s": round(t_end - t_hit, 3),
        "last_line_during_ponder": during[-1] if during else None,
        "last_time_during_ponder_ms": int(parse_all([during[-1]])[-1]["time"]) if during else None,
        "first_line_after_hit": parsed_rest[0]["_line"] if parsed_rest else None,
        "first_time_after_hit_ms": int(parsed_rest[0]["time"]) if parsed_rest else None,
        "last_time_ms": int(parsed_rest[-1]["time"]) if parsed_rest else None,
        "budget_ms": 600000,
    }
    e.quit()
    dump("time", {"settings": SETTINGS, **out})


def probe_pv():
    """pv[0] == bestmove on a searching path, and pv is a legal line."""
    cases = [
        (None, "startpos"),
        ("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", "kiwipete"),
        ("8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", "rook ending"),
        ("r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9", "italian"),
        ("6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1", "black to move"),
        ("2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1", "attacking"),
    ]
    e = new_engine()
    out = []
    for fen, name in cases:
        if fen:
            chess.Board(fen)
        e.position(fen)
        lines, bm = e.search("depth 14")
        parsed = parse_all(lines)
        best = bm.split()[1]
        last = parsed[-1] if parsed else None
        rec = {"case": name, "fen": fen, "bestmove": best,
               "last_pv0": last["pv_moves"][0] if last and last["pv_moves"] else None,
               "last_line": last["_line"] if last else None}
        if last and last["pv_moves"]:
            board = chess.Board(fen if fen else chess.STARTING_FEN)
            ok, detail = True, "ok"
            for i, tok in enumerate(last["pv_moves"]):
                mv = chess.Move.from_uci(tok)
                if mv not in board.legal_moves:
                    ok, detail = False, "illegal at index %d: %s" % (i, tok)
                    break
                board.push(mv)
            rec["pv_legal"] = ok
            rec["pv_detail"] = detail
            rec["pv_match_bestmove"] = (last["pv_moves"][0] == best)
        out.append(rec)
    e.quit()
    dump("pv", {"settings": SETTINGS, "cases": out})


PROBES = {
    "depth_bail": probe_depth_bail,
    "depth_abort": probe_depth_abort,
    "seldepth": probe_seldepth,
    "multipv": probe_multipv,
    "score": probe_score_relativity,
    "nodes": probe_nodes,
    "nps": probe_nps,
    "hashfull": probe_hashfull,
    "time": probe_time,
    "pv": probe_pv,
}

if __name__ == "__main__":
    names = sys.argv[1:] or list(PROBES)
    for n in names:
        print("==", n)
        PROBES[n]()
