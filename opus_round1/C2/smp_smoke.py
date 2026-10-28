#!/usr/bin/env python3
"""UCI smoke test for CorrHistPlus at a given thread count (used by .github/workflows/opus-c2-smp.yml).

For every CorrHistPlus value (default 0,1,2,4,7) in ONE engine process per value:
  - go depth D on every position (fresh `ucinewgame` before every second position), then
  - go movetime 300, go infinite + stop after 0.3 s, and a ponder/ponderhit/stop round;
every search must end with exactly one bestmove, the bestmove must be legal (checked by the engine
itself: `position fen <fen> moves <bestmove>` must not print "illegal move") and the engine must not
crash or hang (timeouts). With --threads 1 every depth search is run twice in separate processes
and the node counts must be identical (Threads=1 determinism).
usage: smp_smoke.py <forge_exe> --threads N [--depth D] [--values 0,1,2,4,7] [--timeout S]
Prints one line per check and exits 1 on any failure.
"""
import argparse
import queue
import subprocess
import sys
import threading
import time

FENS = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
    "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
    "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
    "n1n5/PPPk4/8/8/8/8/4Kppp/5N1N b - - 0 1",
    "8/8/8/4k3/8/8/4P3/4K3 w - - 0 1",
]


class Engine:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  text=True, bufsize=1)
        self.q = queue.Queue()
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self):
        for line in self.p.stdout:
            self.q.put(line.rstrip("\n"))
        self.q.put(None)

    def send(self, text):
        self.p.stdin.write(text + "\n")
        self.p.stdin.flush()

    def wait_for(self, prefix, timeout):
        """Lines up to and including the first line starting with prefix; None on timeout or exit."""
        lines = []
        deadline = time.time() + timeout
        while True:
            left = deadline - time.time()
            if left <= 0:
                return None
            try:
                line = self.q.get(timeout=left)
            except queue.Empty:
                return None
            if line is None:
                return None
            lines.append(line)
            if line.startswith(prefix):
                return lines

    def close(self):
        try:
            self.send("quit")
            self.p.wait(timeout=30)
        except Exception:
            self.p.kill()
        return self.p.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("--threads", type=int, required=True)
    ap.add_argument("--depth", type=int, default=10)
    ap.add_argument("--values", default="0,1,2,4,7")
    ap.add_argument("--timeout", type=float, default=300.0)
    args = ap.parse_args()
    failures = 0

    def check(ok, what):
        nonlocal failures
        print(("PASS " if ok else "FAIL ") + what, flush=True)
        if not ok:
            failures += 1

    def run_value(value, record_nodes):
        """One engine process: all checks for one CorrHistPlus value; returns the depth-search node counts."""
        e = Engine(args.exe)
        tag = f"threads={args.threads} CorrHistPlus={value}"
        e.send("uci")
        check(e.wait_for("uciok", 60) is not None, f"{tag}: uciok")
        for opt in (f"Threads value {args.threads}", "Hash value 16", "OwnBook value false", f"CorrHistPlus value {value}"):
            e.send("setoption name " + opt)
        e.send("isready")
        lines = e.wait_for("readyok", 60)
        check(lines is not None and not any("invalid" in l for l in lines), f"{tag}: options accepted")
        nodes = []

        def legal(fen, move):
            e.send(f"position fen {fen} moves {move}")
            e.send("isready")
            out = e.wait_for("readyok", 60)
            return out is not None and not any("illegal move" in l for l in out)

        def one_search(fen, go, label, stop_after=None, ponderhit_after=None):
            e.send(f"position fen {fen}")
            e.send(go)
            if ponderhit_after is not None:
                time.sleep(ponderhit_after)
                e.send("ponderhit")
            if stop_after is not None:
                time.sleep(stop_after)
                e.send("stop")
            out = e.wait_for("bestmove", args.timeout)
            if out is None:
                check(False, f"{tag}: {label}: bestmove within {args.timeout:.0f} s (hang or crash)")
                return None
            best = out[-1].split()[1]
            ok = best != "0000" and legal(fen, best)
            check(ok, f"{tag}: {label}: legal bestmove {best}")
            n = [int(l.split(" nodes ")[1].split()[0]) for l in out if l.startswith("info depth") and " nodes " in l]
            return n[-1] if n else None

        for i, fen in enumerate(FENS):
            if i % 2 == 0:
                e.send("ucinewgame")
            nodes.append(one_search(fen, f"go depth {args.depth}", f"go depth {args.depth} pos {i}"))
        one_search(FENS[1], "go movetime 300", "go movetime 300")
        one_search(FENS[2], "go infinite", "go infinite + stop", stop_after=0.3)
        one_search(FENS[4], "go ponder wtime 2000 btime 2000", "go ponder + ponderhit", ponderhit_after=0.2)
        e.send("isready")
        check(e.wait_for("readyok", 60) is not None, f"{tag}: isready after the searches")
        rc = e.close()
        check(rc == 0, f"{tag}: clean exit (code {rc})")
        return nodes

    for value in [int(v) for v in args.values.split(",")]:
        first = run_value(value, True)
        if args.threads == 1:
            second = run_value(value, True)
            check(first == second and None not in first,
                  f"threads=1 CorrHistPlus={value}: depth-{args.depth} node counts identical across two processes")
    print(f"SUMMARY failures={failures}", flush=True)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
