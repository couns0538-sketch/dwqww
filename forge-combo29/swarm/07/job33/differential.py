#!/usr/bin/env python3
"""differential.py BASE_EXE PC_EXE OUTDIR

Finds where the PC build behaves DIFFERENTLY from the base tree, because those are the only
differences that can change what the owner does — a PC answer that matches base is either "no change"
or "the same bug", and neither is decision-relevant.

For each case the two builds are driven identically (Threads 1, Hash 16, OwnBook false, one fresh
process per case, never sending anything while a `go` is running) and these are compared:

    bestmove, legal-in-position, number of depth lines, last nodes, score, and whether the run
    reported anything invalid.

Differences are then CLASSIFIED:
  * expected : matches one of the FORGE_FIX_* switches file 5 lists, or a search change from the four
               new options. I only claim "expected" where I can name the switch or option.
  * unexplained : everything else. These are what matter.

The case set deliberately includes things file 3 and file 5 say were CHANGED on the PC (drawn root,
go-parse, bare-king endings) as well as things they do not mention, so a difference that shows up in
an unmentioned area is visible.
"""
import os
import queue
import re
import subprocess
import sys
import threading

import chess

# Position/move cases. Each is (name, position command, go command, note)
CASES = [
    # --- things file 3 / file 5 say the PC REPAIRED: a difference here is expected ---
    ("drawn_root_repetition", "position startpos moves e2e4 e7e5 e1e2 e8e7 e2e1 e7e8 "
                              "e1e2 e8e7 e2e1 e7e8", "go depth 8", "FORGE_FIX_ROOT_DRAWN"),
    ("drawn_root_halfmove", "position fen 8/8/8/4k3/8/8/4K3/R7 w - - 100 80", "go depth 6",
     "FORGE_FIX_ROOT_DRAWN"),
    ("bare_king_vs_king", "position fen 8/8/8/4k3/8/8/4K3/8 w - - 0 1", "go depth 10",
     "FORGE_FIX_BARE_KING_*"),
    ("bare_king_and_rook", "position fen 8/8/8/4k3/8/8/4K3/R7 w - - 0 1", "go depth 10",
     "FORGE_FIX_BARE_KING_*"),
    ("go_keyword_as_value", "position startpos", "go depth nodes", "FORGE_FIX_GO_PARSE"),
    ("go_trailing_keyword", "position startpos", "go nodes 100000 depth", "FORGE_FIX_GO_PARSE"),
    # --- things NOT listed as changed: a difference here is UNEXPLAINED and worth reporting ---
    ("plain_depth8", "position startpos", "go depth 8", "unlisted"),
    ("plain_depth12", "position startpos", "go depth 12", "unlisted"),
    ("middlegame_depth10", "position fen r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
     "go depth 10", "unlisted"),
    ("endgame_depth12", "position fen 8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", "go depth 12",
     "unlisted"),
    ("mate_in_one", "position fen 7k/6Q1/6K1/8/8/8/8/8 b - - 0 1", "go depth 5", "unlisted"),
    ("stalemate_root", "position fen 7k/5Q2/6K1/8/8/8/8/8 b - - 0 1", "go depth 5", "unlisted"),
    ("nodes_budget", "position startpos", "go nodes 50000", "unlisted"),
    ("nodes_tiny", "position startpos", "go nodes 30", "unlisted"),
    ("multipv2", "setoption name MultiPV value 2\nposition startpos", "go depth 8", "unlisted"),
    ("searchmoves_legal", "position startpos", "go depth 8 searchmoves e2e4", "unlisted"),
    ("searchmoves_none_legal", "position startpos", "go depth 8 searchmoves e2e5",
     "07-F1 -- the PC must still show it"),
    ("fifty_move_99", "position fen 8/8/8/4k3/8/8/4K3/R7 w - - 99 80", "go depth 8", "unlisted"),
    ("check_evasion", "position fen 4k3/8/8/8/8/8/4r3/4K3 w - - 0 1", "go depth 8", "unlisted"),
    ("promotion_race", "position fen 8/P6k/8/8/8/8/8/K7 w - - 0 1", "go depth 10", "unlisted"),
]


class Reader:
    def __init__(s, st):
        s.q = queue.Queue()
        threading.Thread(target=s._pump, args=(st,), daemon=True).start()

    def _pump(s, st):
        for l in st:
            s.q.put(l)
        s.q.put(None)

    def get(s, t=240):
        try:
            return s.q.get(timeout=t)
        except queue.Empty:
            return None


def run(exe, pre_lines, go):
    """pre_lines may include setoption/position lines. Returns a record dict."""
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1)
    r = Reader(p.stdout)
    bad = []

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def drain():
        while True:
            l = r.get()
            if l is None:
                raise RuntimeError("no readyok")
            low = l.lower()
            if "unknown option" in low or "invalid value" in low or "error" in low:
                bad.append(l.strip())
            if l.strip() == "readyok":
                return

    send("uci")
    while True:
        l = r.get(60)
        if l is None or l.strip() == "uciok":
            break
    for opt in ["Hash value 16", "Threads value 1", "OwnBook value false"]:
        send("setoption name " + opt); send("isready"); drain()
    send("ucinewgame"); send("isready"); drain()

    position_line = None
    for line in pre_lines:
        if line.startswith("setoption"):
            send(line); send("isready"); drain()
        elif line.startswith("position"):
            position_line = line
            send(line); send("isready"); drain()
    if position_line is None:
        raise SystemExit("FAIL no position line in case")

    send(go)
    depth_lines, best, score, nodes = [], None, None, None
    while True:
        l = r.get(300)
        if l is None:
            best = "ABSENT"
            break
        low = l.lower()
        if "unknown option" in low or "invalid value" in low or "error" in low:
            bad.append(l.strip())
        if l.startswith("info depth"):
            depth_lines.append(l.strip())
            m = re.search(r" nodes (\d+) ", l + " ")
            if m:
                nodes = int(m.group(1))
            m = re.search(r"score (cp|mate) (-?\d+)", l)
            if m:
                score = f"{m.group(1)} {m.group(2)}"
        if l.startswith("bestmove"):
            best = l.split()[1]
            break
    send("quit")
    try:
        p.wait(timeout=30)
    except subprocess.TimeoutExpired:
        p.kill()

    # legality of the answer, from the position line
    legal_ok = None
    fen = None
    m = re.search(r"position fen (.+)", position_line)
    if m:
        fen = m.group(1).strip()
    elif position_line.startswith("position startpos"):
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        suffix = position_line[len("position startpos"):].strip()
        if suffix.startswith("moves"):
            moves = suffix.split()[1:]
            b = chess.Board()
            for mv in moves:
                b.push(chess.Move.from_uci(mv))
            fen = b.fen()
    if fen and best not in (None, "ABSENT"):
        try:
            b = chess.Board(fen)
            legal = [x.uci() for x in b.legal_moves]
            legal_ok = (best == "0000" and not legal) or (best in legal)
        except ValueError:
            legal_ok = None
    return {"bestmove": best, "legal": legal_ok, "depth_lines": len(depth_lines),
            "nodes": nodes, "score": score, "bad": bad}


def main():
    base_exe, pc_exe, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(outdir, exist_ok=True)
    rows = []
    print(f"{'case':26s} {'BASE (best/score/nodes)':44s} {'PC (best/score/nodes)':44s} verdict")
    for name, pre, go, note in CASES:
        pre_lines = pre.split("\n")
        b = run(base_exe, pre_lines, go)
        p = run(pc_exe, pre_lines, go)
        same_move = b["bestmove"] == p["bestmove"]
        same_score = b["score"] == p["score"]
        same_nodes = b["nodes"] == p["nodes"]
        identical = same_move and same_score and same_nodes and b["depth_lines"] == p["depth_lines"]
        verdict = "SAME" if identical else "DIFFERS"
        rows.append({"case": name, "go": go, "note": note, "base": b, "pc": p,
                     "differs": not identical, "same_move": same_move,
                     "same_score": same_score, "same_nodes": same_nodes})
        bl = f"{b['bestmove']}/{b['score']}/{b['nodes']}/{b['depth_lines']}d"
        pl = f"{p['bestmove']}/{p['score']}/{p['nodes']}/{p['depth_lines']}d"
        print(f"{name:26s} {bl:44s} {pl:44s} {verdict}", flush=True)
        if b["bad"] or p["bad"]:
            print(f"    BAD LINES base={b['bad'][:2]} pc={p['bad'][:2]}")

    import json
    json.dump(rows, open(os.path.join(outdir, "differential.json"), "w"), indent=1)
    differs = [r for r in rows if r["differs"]]
    print()
    print(f"cases differing: {len(differs)} of {len(rows)}")
    explained = [r for r in differs if r["note"] not in ("unlisted",)]
    unexplained = [r for r in differs if r["note"] == "unlisted"]
    print(f"  with a named PC switch in the note (expected): {len(explained)}")
    print(f"  NOT explained by a named switch:                {len(unexplained)}")
    for r in unexplained:
        print(f"    UNEXPLAINED {r['case']}: base {r['base']['bestmove']}/{r['base']['score']}/"
              f"{r['base']['nodes']}  pc {r['pc']['bestmove']}/{r['pc']['score']}/{r['pc']['nodes']}")
    # any illegal answer is a fault regardless of explanation
    illegal = [(r["case"], "base") for r in rows if r["base"]["legal"] is False] + \
              [(r["case"], "pc") for r in rows if r["pc"]["legal"] is False]
    print()
    if illegal:
        print("ILLEGAL ANSWERS (a fault on that build): " + str(illegal[:8]))
    else:
        print("no illegal answer on either build in any case")


if __name__ == "__main__":
    main()
