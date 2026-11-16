#!/usr/bin/env python3
"""deepseek5 job5: measure the go/position lines (10 reps each), per-rep raw rows + measured class."""
import chess
import json
import os
import subprocess
import sys
import time

ENGINE = os.environ.get("DS5ENGINE", "/tmp/ds13_base/build/forge")

import queue as _q
import threading as _th

class Eng:
    def __init__(self, wrapper=None, env=None):
        full_env = dict(os.environ)
        if env:
            full_env.update(env)
        cmd = [wrapper, ENGINE] if wrapper else [ENGINE]
        self.p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, bufsize=1, env=full_env)
        self.q = _q.Queue()
        _th.Thread(target=self._reader, daemon=True).start()
        self.send("uci")
        self.expect("uciok", 30)
        self.send("setoption name Threads value 1")
        self.send("setoption name Hash value 16")
        self.send("setoption name OwnBook value false")
        self.send("isready")
        self.expect("readyok", 30)

    def _reader(self):
        for line in self.p.stdout:
            self.q.put(line)
        self.q.put(None)

    def send(self, s):
        self.p.stdin.write(s + "\n")
        self.p.stdin.flush()

    def rl(self, timeout=None):
        return self.q.get(timeout=timeout) if timeout is not None else self.q.get()

    def expect(self, prefix, timeout):
        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout:
            try:
                line = self.q.get(timeout=0.1)
            except _q.Empty:
                continue
            if line is None:
                raise RuntimeError("engine died")
            if line.startswith(prefix):
                return line
        raise _q.Empty

    def newgame(self):
        self.send("ucinewgame")
        self.send("isready")
        self.expect("readyok", 30)

def collect(e, deadline):
    best = None; last_depth = None; last_nodes = None; info = []; perft_total = None
    t0 = time.monotonic_ns()
    while True:
        left = deadline - (time.monotonic_ns() - t0) / 1e9
        if left <= 0:
            break
        try:
            line = e.rl(timeout=left)
        except _q.Empty:
            break
        if line is None:
            break
        if line.startswith("bestmove"):
            best = line.split()[1] if len(line.split()) > 1 else ""
            return {"best": best, "depth": last_depth, "nodes": last_nodes,
                    "info": info, "perft": perft_total, "ms": (time.monotonic_ns() - t0) / 1e6}
        if line.startswith("info string"):
            info.append(line.strip())
        elif line.startswith("info") and " depth " in line:
            t = line.split()
            try:
                last_depth = int(t[t.index("depth") + 1])
                last_nodes = int(t[t.index("nodes") + 1])
            except (ValueError, IndexError):
                pass
        elif line.startswith("info") and " nodes " in line:
            t = line.split()
            try:
                last_nodes = int(t[t.index("nodes") + 1])
            except (ValueError, IndexError):
                pass
        elif line.startswith("nodes ") or line == "nodes\n":
            try:
                perft_total = int(line.split()[1])
            except (ValueError, IndexError, IndexError):
                pass
        if (time.monotonic_ns() - t0) / 1e9 > deadline:
            return {"best": None, "depth": last_depth, "nodes": last_nodes,
                    "info": info, "perft": perft_total, "ms": None}
    return {"best": None, "depth": last_depth, "nodes": last_nodes,
            "info": info, "perft": perft_total, "ms": None}

def measure(e, line, board, deadline=1.5, stop_wait=1.0):
    e.send(line)
    r = collect(e, deadline)
    stop_ms = None
    if r["best"] is None:
        e.send("stop")
        r2 = collect(e, stop_wait)
        stop_ms = r2["ms"]
        r = {"best": r2["best"], "depth": r2["depth"], "nodes": r2["nodes"],
             "info": r["info"] + r2["info"], "perft": r["perft"] or r2["perft"], "ms": None,
             "stop_ms": stop_ms}
    legal = "n/a"
    if r["best"] and r["best"] not in ("(none)", "0000", "none"):
        try:
            legal = "yes" if chess.Move.from_uci(r["best"]) in board.legal_moves else "no"
        except Exception:
            legal = "no"
    elif r["best"]:
        legal = "none-move"
    e.send("isready")
    try:
        e.expect("readyok", 2.0)
        alive = True
    except _q.Empty:
        alive = False
    cls = classify(r, line)
    return {"ms": r["ms"], "stop_ms": stop_ms, "best": r["best"], "legal": legal,
            "depth": r["depth"], "nodes": r["nodes"], "perft": r["perft"],
            "info_strings": r["info"], "class": cls, "alive": alive}

def classify(r, line):
    got = r["best"] is not None
    if not got:
        if any(("must be" in s) for s in r["info"]):
            return "REFUSED"
        if r["perft"] is not None:
            return "OTHER:perft-no-bestmove"
        return "OTHER:no-bestmove"
    if r["ms"] is None:
        return "RUNS"
    eff = r["ms"]
    depth = r["depth"]
    if eff < 300 and (depth is None or depth <= 1):
        return "AT_ONCE"
    if eff < 600 and depth is not None and depth >= 9:
        return "CLOCK"
    if depth is None or depth <= 1:
        return "OTHER:delayed-answer"
    return "LIMIT"

def fmt(x):
    return "NONE" if x is None else f"{x:.2f}"

def row(lid, rep, r):
    return (f"{lid}|{rep}|{fmt(r['ms'])}|{fmt(r['stop_ms'])}|{r['best']}|{r['legal']}|"
            f"{r['depth']}|{r['nodes']}|{'; '.join(r['info_strings'])}|{r['class']}|alive={r['alive']}")

def startpos_black():
    b = chess.Board(); b.push_uci("e2e4"); return b

def board_of(fen):
    def fn():
        b = chess.Board()
        b.set_fen(fen.split(" moves ")[0])
        if " moves " in fen:
            for mv in fen.split(" moves ")[1].split():
                b.push_uci(mv)
        return b
    return fn

def main():
    which = sys.argv[1]
    out_path = sys.argv[2]
    rows = []
    if which == "H":
        e = Eng()
        cases = [("H1", "go depth 5", startpos_black()),
                 ("H2", "go infinite", startpos_black()),
                 ("H3", "go wtime 2000 btime 2000", startpos_black())]
        for cid, ln, bd in cases:
            e.newgame(); e.send("position startpos moves e2e4")
            r = measure(e, ln, bd)
            rows.append(row(cid, 1, r)); print(rows[-1], flush=True)
        open(out_path, "w").write("\n".join(rows) + "\n")
        return
    if which == "H4":
        e = Eng(wrapper="/tmp/glmflash/ds5_swallow_once.py")
        e.newgame(); e.send("position startpos moves e2e4")
        r = measure(e, "go depth 5", startpos_black())
        rows.append(row("H4", 1, r)); print(rows[-1], flush=True)
        open(out_path, "w").write("\n".join(rows) + "\n")
        return
    if which == "H5":
        e = Eng(wrapper="/tmp/glmflash/ds5_delay_wrapper.py", env={"DS5DELAY": "0.400"})
        e.newgame(); e.send("position startpos moves e2e4")
        r = measure(e, "go depth 1", startpos_black())
        rows.append(row("H5", 1, r)); print(rows[-1], flush=True)
        open(out_path, "w").write("\n".join(rows) + "\n")
        return
    e = Eng()
    if which == "A":
        go_lines = [
            "go wtime 2000 btime 2000", "go depth btime 2000 wtime 2000", "go nodes 0",
            "go wtime btime 50", "go infinite", "go btime abc", "go winc btime 2000 wtime 2000",
            "go depth 5", "go movetime -1", "go nodes btime 2000 wtime 2000", "go",
            "go wtime 0 btime 0", "go movestogo btime 2000 wtime 2000", "go depth 0", "go btime",
            "go searchmoves e7e5 wtime 2000 btime 2000", "go depth -3", "go wtime btime 2000 wtime 2000",
            "go movetime abc", "go binc btime 2000 wtime 2000", "go softnodes 2000", "go wtime -50 btime -50",
            "go mate btime 2000 wtime 2000", "go depth abc", "go movestogo 0 wtime 2000 btime 2000",
            "go wtime abc", "go movetime btime 2000 wtime 2000", "go nodes 5000", "go wtime abc btime 2000",
            "go nodes -1", "go movetime 99999999999999999999 wtime 2000 btime 2000"]
        for i, ln in enumerate(go_lines, 1):
            bd = startpos_black()
            for rep in range(1, 11):
                e.newgame(); e.send("position startpos moves e2e4")
                r = measure(e, ln, bd)
                rows.append(row(f"A{i:02d}", rep, r))
            print(rows[-1], flush=True)
    elif which == "B":
        go_special = {
            1: "ponder", 28: "perft5", 29: "perft99", 30: "perft-1", 31: "perftabc",
        }
        go_lines = [
            None, "go mate 1", "go mate 3", "go depth 5 nodes 100", "go movetime 50 depth 30",
            "go wtime 2000 btime 2000 movestogo 1", "go wtime 1 btime 1 winc 0 binc 0",
            "GO DEPTH 5", "go  depth   5  ", "go\tdepth\t5", "go depth 5 depth 2", "go searchmoves zzzz",
            "go searchmoves", "go nodes 1", "go nodes 18446744073709551616", "go depth 2147483648",
            "go wtime 2000 btime 2000 winc -100 binc -100", "go movestogo -1 wtime 2000 btime 2000",
            "go movetime 1", "go wtime 2000 btime 2000 searchmoves e7e5 d7d5", "go depth 5 infinite",
            "go wtime 2000", "go btime 2000", "go binc 1000", "go movetime 0",
            "go searchmoves e7e5 e7e5 depth 4", "go infinite depth 3",
            "go perft 5", "go perft 99", "go perft -1", "go perft abc"]
        for i, ln in enumerate(go_lines, 1):
            bd = startpos_black()
            for rep in range(1, 11):
                e.newgame(); e.send("position startpos moves e2e4")
                if i == 1:
                    e.send("go ponder wtime 2000 btime 2000")
                    time.sleep(0.3)
                    e.send("ponderhit")
                    r = collect_and_classify_ponderhit(e, bd)
                elif ln is None:
                    r = measure(e, "go depth 5", bd)  # unreachable; safety
                else:
                    r = measure(e, ln, bd)
                rows.append(row(f"B{i:02d}", rep, r))
            print(rows[-1], flush=True)
    elif which == "C":
        fens = ["6k1/5ppp/8/8/8/1q6/8/R2Q2K1 w - - 0 1 moves d1e2 b3c4 e2d1 c4b3 d1e2 b3c4 e2d1 c4b3",
                "6k1/5ppp/8/8/8/1q6/8/R2Q2K1 w - - 100 80",
                "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1",
                "7k/6Q1/6K1/8/8/8/8/8 b - - 0 1",
                "8/8/8/4k3/8/8/8/4K3 w - - 0 1"]
        for i, f in enumerate(fens, 1):
            bd = board_of(f)()
            for rep in range(1, 11):
                e.newgame(); e.send(f"position fen {f}")
                r = measure(e, "go depth 6", bd)
                rows.append(row(f"C{i}", rep, r))
            print(rows[-1], flush=True)
    elif which == "P":
        pdefs = [("P1", "position startpos moves e2e4 e7e5 e2e4"),
                 ("P2", "position fen 8/8/8/8/8/8/8/8 w - - 0 1"),
                 ("P3", "position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq"),
                 ("P4", "position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1 moves"),
                 ("P5", "position fen 4k3/8/8/8/8/8/8/4K2r b - - 0 1"),
                 ("P6", "position foo"),
                 ("P7", "position fen rnbqkbnr/ppppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")]
        for pid, pl in pdefs:
            for rep in range(1, 11):
                e.newgame()
                e.send(pl)
                r1 = collect(e, 1.0)   # perft 1
                e.send("go perft 1")
                r2 = collect(e, 1.0)
                e.send("isready")
                alive = wait_readyok(e)
                # then the measured go
                bd = last_valid_board(pid)
                r3 = measure(e, "go depth 3", bd)
                rec = {"perft1_count": r2["perft"], "perft1_info": r2["info"] + r1["info"],
                       "pos_info": r1["info"]}
                rows.append(row(pid, rep, r3) + f"|perft1={r2['perft']}|{' ; '.join(rec['perft1_info'])[:200]}")
            print(rows[-1][:160], flush=True)
        for pid, reps in (("P8", 300), ("P9", 3000)):
            mv = " ".join(["g1f3 g8f6 f3g1 f6g8"] * reps)
            pl = "position startpos moves " + mv
            bd = chess.Board()
            for rep in range(1, 11):
                e.newgame()
                t0 = time.monotonic_ns()
                e.send(pl)
                setup_ms = (time.monotonic_ns() - t0) / 1e6
                e.send("go perft 1")
                r1 = collect(e, 5.0)
                r3 = measure(e, "go depth 4", bd)
                rows.append(row(pid, rep, r3) + f"|perft1={r1['perft']}|setup_ms={setup_ms:.1f}")
            print(rows[-1][:160], flush=True)
    open(out_path, "w").write("\n".join(rows) + "\n")

def collect_and_classify_ponderhit(e, bd):
    r = collect(e, 1.5)
    stop_ms = None
    if r["best"] is None:
        e.send("stop")
        r2 = collect(e, 1.0)
        stop_ms = r2["ms"]
        r = {"best": r2["best"], "depth": r2["depth"], "nodes": r2["nodes"],
             "info": r["info"] + r2["info"], "perft": None, "ms": None}
    legal = "n/a"
    if r["best"]:
        try:
            legal = "yes" if chess.Move.from_uci(r["best"]) in bd.legal_moves else "no"
        except Exception:
            legal = "no"
    eff = r["ms"] if r["ms"] is not None else stop_ms
    cls = "AT_ONCE" if (eff is not None and eff < 300) else ("CLOCK" if eff is not None and eff < 600 and r["depth"] and r["depth"] >= 9 else ("RUNS" if r["ms"] is None else "LIMIT"))
    e.send("isready")
    alive = wait_readyok(e)
    return {"ms": r["ms"], "stop_ms": stop_ms, "best": r["best"], "legal": legal,
            "depth": r["depth"], "nodes": r["nodes"], "perft": None,
            "info_strings": r["info"], "class": cls, "alive": alive}

def wait_readyok(e):
    t0 = time.monotonic()
    while time.monotonic() - t0 < 1.0:
        l = e.rl()
        if l == "":
            return False
        if l.startswith("readyok"):
            return True
    return False

_LAST_VALID = {"P1": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1",
               "P2": None, "P3": None, "P4": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
               "P5": "4k3/8/8/8/8/8/8/4K2r b - - 0 1", "P6": None, "P7": None}

def last_valid_board(pid):
    fen = _LAST_VALID.get(pid)
    if fen is None:
        return chess.Board()  # the initial board the engine holds
    b = chess.Board(); b.set_fen(fen); return b

if __name__ == "__main__":
    main()
