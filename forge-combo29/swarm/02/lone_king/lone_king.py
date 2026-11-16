#!/usr/bin/env python3
"""S02 — independent check of the lone-king wrong-move defect on the PC build.

Board: `1r6/5b2/2K5/8/8/5n2/5k2/8 w - - 18 183` — White has a bare king against rook, bishop and knight.
The claim to test: the engine scores a move wrongly on this position, and `bestmove` alone cannot reveal it,
because every bare-king move scores the same. So each legal move is scored SEPARATELY with `searchmoves`, at
depths 16, 18 and 20, on both builds.

Why searchmoves is the right instrument here: a bare-king position has all moves transposing to the same
material, so the engine's move ORDERING decides which move `bestmove` reports, and a single `go depth N` cannot
tell you whether a particular move is scored wrongly. Restricting the root to one move forces that move's score.

Integrity rules held to:
  * Threads 1 (seat 04: scores above Threads 1 are not reproducible).
  * OwnBook false, Hash 16, PC20 on the PC build and S14 on the base build (the base cannot take PC20's
    switches — it answers `unknown option`, which aborts).
  * every search the FIRST of a fresh process, so COLD (seat 10).
  * interactive driver, never piped (19-F12).
  * a `mate N` score is replayed with python-chess and must end in checkmate at 2N-1 (N>0) or 2|N| (N<0) plies.
  * every move's legality is checked with python-chess before the run, and the count is printed.

usage: lone_king.py <pc_exe> <base_exe> <outdir>
"""
import json
import os
import re
import subprocess
import sys
import threading
import time

import chess

PC = sys.argv[1] if len(sys.argv) > 1 else "/agent/repos/pc/forge-combo29/build-pc/forge"
BASE = sys.argv[2] if len(sys.argv) > 2 else "/agent/repos/base/forge-combo29/build/forge"
OUT = sys.argv[3] if len(sys.argv) > 3 else "out_lk"

FEN = "1r6/5b2/2K5/8/8/5n2/5k2/8 w - - 18 183"
DEPTHS = [16, 18, 20]

S14 = [
    "setoption name LmrQuietBase value 93", "setoption name LmrQuietDivisor value 205",
    "setoption name LmrNoisyBase value 13", "setoption name LmrNoisyDivisor value 333",
    "setoption name LmrHistoryDivisor value 5643", "setoption name NullMoveBase value 5",
    "setoption name LmpBase value 8", "setoption name HistoryPruneMultiplier value 2220",
    "setoption name HistoryBonusQuadratic value 24", "setoption name HistoryBonusLinear value 54",
    "setoption name HistoryBonusMax value 2212", "setoption name SingularDepth value 6",
    "setoption name IirDepth value 2", "setoption name NonPawnCorrection value true",
]
BASE_SETUP = ["setoption name Threads value 1", "setoption name Hash value 16"] + S14 + [
    "setoption name OwnBook value false"]
PC_SETUP = ["setoption name Threads value 1", "setoption name Hash value 16"] + S14 + [
    "setoption name CuckooRep value true", "setoption name HistRework value 2",
    "setoption name TtPruneV2 value true", "setoption name CorrHistV2 value true",
    "setoption name MateAlphaGuard value true", "setoption name OwnBook value false"]


def legal_moves(fen):
    b = chess.Board(fen)
    if not b.is_valid():
        raise SystemExit("FAIL: the board %r is not valid per python-chess" % fen)
    return [m.uci() for m in b.legal_moves]


def search(exe, setup, move, depth):
    """Score ONE move at the root via searchmoves. Returns the score and the raw line."""
    env = {k: v for k, v in os.environ.items()
           if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS")}
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)
    L = []
    threading.Thread(target=lambda: [L.append(l.rstrip("\n")) for l in p.stdout], daemon=True).start()

    def send(t):
        if p.poll() is None:
            try:
                p.stdin.write(t + "\n")
                p.stdin.flush()
            except Exception:
                pass

    def wait(pref, n0=0, to=180.0):
        dl = time.monotonic() + to
        while time.monotonic() < dl:
            if any(l.startswith(pref) for l in L[n0:]):
                return True
            if p.poll() is not None:
                return any(l.startswith(pref) for l in L[n0:])
            time.sleep(0.001)
        return False

    send("uci")
    if not wait("uciok"):
        raise SystemExit("FAIL: no uciok from %s" % exe)
    for s in setup:
        send(s)
    send("isready")
    if not wait("readyok"):
        raise SystemExit("FAIL: no readyok from %s" % exe)
    for line in L:
        if "unknown option" in line or "invalid value" in line:
            raise SystemExit("FAIL: an option was refused by %s: %r" % (exe, line))
    send("position fen " + FEN)
    send("isready")
    n0 = len(L)
    wait("readyok", n0)
    n0 = len(L)
    send("go depth %d searchmoves %s" % (depth, move))
    if not wait("bestmove", n0, 240):
        raise SystemExit("FAIL: no bestmove for searchmoves %s depth %d" % (move, depth))
    seg = list(L[n0:])
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    at = []
    for line in seg:
        m = re.match(r"info depth (\d+) .*?score (\S+) (-?\d+)", line)
        if m and int(m.group(1)) == depth:
            at.append(line)
    if not at:
        return {"move": move, "depth": depth, "score_kind": None, "score": None,
                "raw": None, "note": "no info line at that depth"}
    m = re.match(r"info depth (\d+) .*?score (\S+) (-?\d+).*?(?: pv (.*))?$", at[-1])
    pv = (m.group(4) or "").split() if m and m.group(4) else []
    bm = [l for l in seg if l.startswith("bestmove")]
    return {"move": move, "depth": depth, "score_kind": m.group(2),
            "score": int(m.group(3)), "pv": pv, "raw": at[-1],
            "bestmove": bm[-1].split()[1] if bm else None}


def pv_mate_check(fen, pv, score, kind=None):
    """Verify a mate score by replaying the PV. `kind` is the engine's own score kind ("mate" or "cp") —
    the engine reports mate DISTANCE (e.g. -8 = mated in 8), not a large cp value, so the kind is the only
    reliable discriminator. My first version tested |score| >= 10000 and therefore never fired."""
    if kind != "mate" or score is None:
        return None
    b = chess.Board(fen)
    played = 0
    for tok in pv:
        try:
            mv = chess.Move.from_uci(tok)
        except Exception:
            return "pv does not parse"
        if mv not in b.legal_moves:
            return "pv illegal at ply %d" % played
        b.push(mv)
        played += 1
    want = (2 * score - 1) if score > 0 else (2 * abs(score))
    if b.is_checkmate() and played == want:
        return "OK"
    if played < want:
        return "TRUNCATED %d/%d" % (played, want)
    return "WRONG: %s after %d plies, wanted mate after %d" % (
        "mate" if b.is_checkmate() else "not mate", played, want)


def main():
    os.makedirs(OUT, exist_ok=True)
    moves = legal_moves(FEN)
    b = chess.Board(FEN)
    info = {"fen": FEN, "legal_moves": moves, "n_legal": len(moves),
            "white_pieces": sum(1 for p in b.piece_map().values() if p.color == chess.WHITE),
            "black_pieces": sum(1 for p in b.piece_map().values() if p.color == chess.BLACK),
            "halfmove": b.halfmove_clock, "fullmove": b.fullmove_number,
            "pc_exe": PC, "base_exe": BASE,
            "pc_sha256": subprocess.run(["sha256sum", PC], capture_output=True,
                                        text=True).stdout.split()[0],
            "base_sha256": subprocess.run(["sha256sum", BASE], capture_output=True,
                                          text=True).stdout.split()[0],
            "threads": 1, "depths": DEPTHS,
            "pc_settings": "PC20", "base_settings": "S14 (+Threads 1, Hash 16, OwnBook false)",
            "instrument": "go depth D searchmoves <one move>",
            "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    print("board %s" % FEN)
    print("white pieces %d, black pieces %d, halfmove %d"
          % (info["white_pieces"], info["black_pieces"], info["halfmove"]))
    print("legal moves (%d): %s" % (len(moves), " ".join(moves)))
    print()

    results = {}
    for label, exe, setup in (("pc", PC, PC_SETUP), ("base", BASE, BASE_SETUP)):
        results[label] = []
        print("== %s" % label)
        for d in DEPTHS:
            for mv in moves:
                r = search(exe, setup, mv, d)
                r["pv_check"] = pv_mate_check(FEN, r.get("pv", []), r.get("score"), r.get("score_kind"))
                results[label].append(r)
                print("   depth %-2d searchmoves %-5s -> %s %s%s"
                      % (d, mv, r["score_kind"], r["score"],
                         ("  [" + r["pv_check"] + "]") if r["pv_check"] else ""), flush=True)
        print()

    # score agreement between the two builds, per depth
    print("### scores by move, both builds (PC r15 + PC20 vs base + S14), Threads 1")
    print()
    hdr = "| move | " + " | ".join("PC d%d" % d for d in DEPTHS) + " | " + \
          " | ".join("base d%d" % d for d in DEPTHS) + " |"
    print(hdr)
    print("|---|" + "---|" * (2 * len(DEPTHS)))
    for mv in moves:
        cells = []
        for label in ("pc", "base"):
            for d in DEPTHS:
                r = [x for x in results[label] if x["move"] == mv and x["depth"] == d]
                if r and r[0]["score"] is not None:
                    cells.append("%s%d" % ("m" if r[0]["score_kind"] == "mate" else "", r[0]["score"]))
                else:
                    cells.append("-")
        print("| `%s` | %s |" % (mv, " | ".join(cells)))

    # how many moves share the same score at each depth (the ordering ambiguity)
    print()
    print("### how many DISTINCT scores the legal moves get at each depth")
    print()
    print("| build | depth | moves | distinct scores | all equal? |")
    print("|---|---|---|---|---|")
    for label in ("pc", "base"):
        for d in DEPTHS:
            scores = [x["score"] for x in results[label] if x["depth"] == d and x["score"] is not None]
            print("| %s | %d | %d | %d | %s |"
                  % (label, d, len(scores), len(set(scores)),
                     "**YES**" if len(set(scores)) == 1 and len(scores) > 1 else "no"))

    json.dump({"info": info, "results": results},
              open(os.path.join(OUT, "lone_king.json"), "w"), indent=1)
    print()
    print("raw: lone_king.json")


if __name__ == "__main__":
    main()
