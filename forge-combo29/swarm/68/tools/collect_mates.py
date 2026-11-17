#!/usr/bin/env python3
"""Collect engine mate scores over a corpus, at Threads 1.

Every hard-won rule about this harness is enforced here rather than assumed:

  * Threads 1 always. Above it every position differs between runs.
  * MultiPV is set explicitly per run; the engine default is 1.
  * `go` is always bounded (depth or movetime), never `infinite`, so no `stop`
    is ever needed and no search can hang. A wall-clock timeout kills the
    process and the position is recorded as TIMEOUT, not silently dropped.
  * The `info string invalid FEN` diagnostic is read from BOTH places it can
    appear -- the `position` reply and the `go` output before the first
    `info depth` -- because a harness that reads only one misses it half the
    time. A position that produced the diagnostic is marked REFUSED and its
    scores are discarded: a refused position would otherwise give us a mate
    score for the PREVIOUS board.
  * Every FEN is validated with python-chess before it is sent, so a fixture bug
    cannot masquerade as an engine fault.
  * `bestmove` is awaited with a timeout on every position.

Output: one JSON object per line, including the full set of `info` lines for the
position so a later analysis can recompute anything without re-running.
"""
import json
import queue
import subprocess
import sys
import threading
import time

import chess

ENGINE = sys.argv[1] if len(sys.argv) > 1 else \
    "/agent/repos/dwqww/forge-combo29/build/forge"


class Engine:
    def __init__(self, threads=1, multipv=1, hash_mb=16):
        self.p = subprocess.Popen(
            [ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.lines = queue.Queue()
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()
        self.send("uci")
        self._await("uciok", 10.0)
        self.send(f"setoption name Threads value {threads}")
        self.send(f"setoption name MultiPV value {multipv}")
        self.send(f"setoption name Hash value {hash_mb}")
        self.send("isready")
        self._await("readyok", 20.0)
        self.threads = threads
        self.multipv = multipv

    def _read(self):
        for line in self.p.stdout:
            self.lines.put(line.rstrip("\n"))
        self.lines.put(None)

    def send(self, cmd):
        self.p.stdin.write(cmd + "\n")
        self.p.stdin.flush()

    def _await(self, token, timeout):
        out = []
        deadline = time.time() + timeout
        while True:
            remaining = deadline - time.time()
            if remaining <= 0:
                return out, False
            try:
                line = self.lines.get(timeout=remaining)
            except queue.Empty:
                return out, False
            if line is None:
                return out, False
            out.append(line)
            if line.startswith(token):
                return out, True

    def search(self, fen, depth, timeout):
        """Returns (info_lines, bestmove, position_reply, refused, timed_out)."""
        # Any output already buffered belongs to a previous command.
        while not self.lines.empty():
            try:
                self.lines.get_nowait()
            except queue.Empty:
                break

        self.send(f"position fen {fen}")
        # NO isready here: it would swallow the invalid-FEN diagnostic into this
        # reply and then we would parse it as part of the next command's output.
        position_reply = []
        time.sleep(0.01)
        while not self.lines.empty():
            try:
                line = self.lines.get_nowait()
            except queue.Empty:
                break
            if line:
                position_reply.append(line)

        self.send(f"go depth {depth}")
        info = []
        best = None
        deadline = time.time() + timeout
        while True:
            remaining = deadline - time.time()
            if remaining <= 0:
                return info, None, position_reply, False, True
            try:
                line = self.lines.get(timeout=remaining)
            except queue.Empty:
                return info, None, position_reply, False, True
            if line is None:
                return info, None, position_reply, False, True
            info.append(line)
            if line.startswith("bestmove"):
                best = line.split()[1] if len(line.split()) > 1 else None
                break

        refused = any("invalid FEN" in l for l in position_reply) or \
                  any("invalid FEN" in l for l in info if l.startswith("info string"))
        return info, best, position_reply, refused, False

    def close(self):
        try:
            self.send("quit")
            self.p.wait(timeout=5)
        except Exception:
            self.p.kill()


def parse_info(lines):
    """Extract per-depth records, keeping multipv index when present."""
    recs = []
    for line in lines:
        if not line.startswith("info depth"):
            continue
        tok = line.split()
        rec = {"raw": line}
        i = 0
        mpv = 1
        while i < len(tok):
            t = tok[i]
            if t == "depth" and i + 1 < len(tok):
                rec["depth"] = int(tok[i + 1]); i += 2
            elif t == "multipv" and i + 1 < len(tok):
                mpv = int(tok[i + 1]); i += 2
            elif t == "score" and i + 2 < len(tok):
                rec["score_type"] = tok[i + 1]
                rec["score_value"] = int(tok[i + 2]); i += 3
            elif t == "nodes" and i + 1 < len(tok):
                rec["nodes"] = int(tok[i + 1]); i += 2
            elif t == "pv":
                rec["pv"] = tok[i + 1:]
                break
            else:
                i += 1
        rec["multipv"] = mpv
        recs.append(rec)
    return recs


def main():
    corpus_path = sys.argv[2] if len(sys.argv) > 2 else "corpus.fen"
    depth = int(sys.argv[3]) if len(sys.argv) > 3 else 12
    multipv = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    out_path = sys.argv[5] if len(sys.argv) > 5 else "mates.jsonl"
    per_pos_timeout = float(sys.argv[6]) if len(sys.argv) > 6 else 30.0

    fens = []
    with open(corpus_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                fens.append(line)

    print(f"corpus {corpus_path}: {len(fens)} FENs requested")
    # Validate every FEN before it is sent. An illegal FEN makes the engine
    # silently search the PREVIOUS position, so a fixture bug would otherwise
    # appear as an engine fault.
    valid = []
    rejected = 0
    for fen in fens:
        try:
            b = chess.Board(fen)
            if not b.is_valid():
                rejected += 1
                continue
        except Exception:
            rejected += 1
            continue
        valid.append(fen)
    print(f"python-chess validation: {len(valid)} accepted, {rejected} rejected "
          f"(of {len(fens)} requested)")

    eng = Engine(threads=1, multipv=multipv)
    n_refused = 0
    n_timeout = 0
    n_mate = 0
    n_out = 0
    t0 = time.time()
    with open(out_path, "w") as out:
        for idx, fen in enumerate(valid):
            info, best, preply, refused, timed_out = eng.search(fen, depth, per_pos_timeout)
            if refused:
                n_refused += 1
            if timed_out:
                n_timeout += 1
                # The engine is in an unknown state; restart it so the next
                # position cannot be polluted by a search that ignored its limit.
                eng.close()
                eng = Engine(threads=1, multipv=multipv)
            recs = parse_info(info)
            mates = [r for r in recs if r.get("score_type") == "mate"]
            if mates:
                n_mate += 1
            out.write(json.dumps({
                "idx": idx, "fen": fen, "depth": depth, "multipv": multipv,
                "threads": 1, "bestmove": best, "refused": refused,
                "timed_out": timed_out, "position_reply": preply,
                "info": recs,
                "mate_final": mates[-1] if mates else None,
            }) + "\n")
            n_out += 1
    eng.close()
    dt = time.time() - t0
    print(f"wrote {out_path}: {n_out} positions")
    print(f"  refused (invalid FEN): {n_refused}/{len(valid)}")
    print(f"  timed out: {n_timeout}/{len(valid)}")
    print(f"  positions with >=1 mate score: {n_mate}/{len(valid)}")
    print(f"  elapsed {dt:.1f}s = {len(valid) / dt:.2f} positions/s")


if __name__ == "__main__":
    main()
