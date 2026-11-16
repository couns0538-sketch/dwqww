#!/usr/bin/env python3
"""stand S5: 300 self-play games at go nodes 5000, played to the end with no adjudication.
Protocol (the job-29 lesson applied): before every move the harness sends
    position fen <start position> moves <every move so far>
A game ends at mate, stalemate, insufficient material, halfmove clock 100, an ACTUAL third
occurrence (board.is_repetition(3)), or 300 plies. Every draw the runner claims is one python-chess
agrees with (the endings are computed FROM the board, never from the runner's own bookkeeping)."""
import chess
import os
import queue
import subprocess
import sys
import threading
import time

EXE = os.environ.get("DS5ENGINE", "/tmp/ds5_rt21/build3/forge")
OUT = "/agent/repos/dwqww/forge-combo29/tests_deepseek5_stand5"
os.makedirs(OUT, exist_ok=True)
NODES = 5000
MAX_PLIES = 300

def start_engine():
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    q = queue.Queue()
    def rd():
        try:
            for line in p.stdout:
                q.put(line)
        except Exception:
            pass
        q.put(None)
    threading.Thread(target=rd, daemon=True).start()
    def send(s):
        try:
            p.stdin.write(s + "\n"); p.stdin.flush()
        except Exception:
            pass
    def rl():
        try:
            return q.get(timeout=2.0)
        except queue.Empty:
            return ""
        except Exception:
            return ""
    send("uci")
    t0 = time.monotonic()
    while True:
        l = rl()
        if not l:
            if time.monotonic() - t0 > 30:
                break
            continue
        if l.strip().startswith("uciok"):
            break
    send("setoption name Threads value 1")
    send("setoption name Hash value 16")
    send("setoption name OwnBook value false")
    send("isready")
    while True:
        l = rl()
        if not l or l.strip().startswith("readyok"):
            break
    return p, send, rl

def play(p, send, rl, start_fen):
    board = chess.Board()
    board.set_fen(start_fen)
    moves = []
    send("ucinewgame")
    send("isready")
    while True:
        l = rl()
        if not l or l.strip().startswith("readyok"):
            break
    plies = 0
    while True:
        if board.is_checkmate():
            return ("mate", plies, board.fen(), moves)
        if board.is_stalemate():
            return ("stalemate", plies, board.fen(), moves)
        if board.is_insufficient_material():
            return ("insufficient", plies, board.fen(), moves)
        if board.halfmove_clock >= 100:
            return ("fifty", plies, board.fen(), moves)
        if board.is_repetition(3):
            return ("repetition", plies, board.fen(), moves)
        if plies >= MAX_PLIES:
            return ("cap", plies, board.fen(), moves)
        mv = " ".join(moves)
        if mv:
            send(f"position fen {start_fen} moves {mv}")
        else:
            send(f"position fen {start_fen}")
        send(f"go nodes {NODES}")
        best = None
        t0 = time.monotonic()
        while time.monotonic() - t0 < 60:
            l = rl()
            if not l:
                if p.poll() is not None:
                    return ("engine-exited", plies, board.fen(), moves)
                if time.monotonic() - t0 > 60:
                    break
                continue
            l = l.strip()
            if l.startswith("bestmove"):
                best = l.split()[1]
                break
        if best is None:
            return ("no-bestmove", plies, board.fen(), moves)
        try:
            m = chess.Move.from_uci(best)
        except Exception:
            return ("bad-move", plies, board.fen(), moves)
        if m not in board.legal_moves:
            return ("illegal-move", plies, board.fen(), moves)
        moves.append(best)
        board.push(m)
        plies += 1

def main():
    fens = [ln.strip().split("|")[0] for ln in open("/tmp/glmflash/set_O.epd")][:200]
    for ln in open("/tmp/glmflash/set_G.epd"):
        fens.append(ln.strip().split("|")[0])
    fens = fens[:300]
    print(f"start positions: {len(fens)}")
    p, send, rl = start_engine()
    rows = []
    endings = {}
    for i, fen in enumerate(fens, 1):
        r = play(p, send, rl, fen)
        endings[r[0]] = endings.get(r[0], 0) + 1
        rows.append(f"{i}|{fen}|{r[0]}|{r[1]}|{r[2]}|" + " ".join(r[3]))
        if i % 25 == 0:
            print(f"{i} games done; endings so far {endings}", flush=True)
    try:
        send("quit")
    except Exception:
        pass
    p.wait(timeout=30)
    with open(f"{OUT}/games.rows", "w") as f:
        for r in rows:
            f.write(r + "\n")
    # the replay with python-chess: every move legal, every ending re-derived
    bad_legal = 0
    bad_end = 0
    for r in rows:
        i, fen, ending, plies, final_fen, mvs = r.split("|", 5)
        b = chess.Board()
        b.set_fen(fen)
        ok = True
        for uci in mvs.split():
            m = chess.Move.from_uci(uci)
            if m not in b.legal_moves:
                ok = False
                break
            b.push(m)
        if not ok:
            bad_legal += 1
        # re-derive the ending
        again = None
        if b.is_checkmate(): again = "mate"
        elif b.is_stalemate(): again = "stalemate"
        elif b.is_insufficient_material(): again = "insufficient"
        elif b.halfmove_clock >= 100: again = "fifty"
        elif b.is_repetition(3): again = "repetition"
        elif len(mvs.split()) >= MAX_PLIES: again = "cap"
        if again != ending:
            bad_end += 1
    print("ENDINGS:", dict(sorted(endings.items(), key=lambda kv: -kv[1])))
    print(f"replay: games with an illegal move {bad_legal}; games whose re-derived ending differs {bad_end}")
    with open(f"{OUT}/replay.txt", "w") as f:
        f.write(f"ENDINGS: {dict(sorted(endings.items(), key=lambda kv: -kv[1]))}\n")
        f.write(f"replay: illegal-move games {bad_legal}; ending mismatches {bad_end}\n")

if __name__ == "__main__":
    main()
