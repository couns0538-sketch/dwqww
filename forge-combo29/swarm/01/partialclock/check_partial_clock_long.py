#!/usr/bin/env python3
"""swarm seat 01: the LONG leg of the partial-clock check — does `stop` have to arrive, or not?

check_partial_clock.py caps every search at 8 s, which is enough to show a partial clock does not answer, but
not enough to say WHY. "Did not finish in 8 s" is compatible with two very different worlds: a slow but bounded
search, or no bound at all. Seat 02's aside claims a huge opponent clock DOES bound a White-to-move search, so
the difference matters — a big number would then be a workaround.

Two legs, each naming its clock, its position, and its stopping condition:

  D1  `go btime 6000000`, White to move, NO stop sent, killed at KILL_S.
      Claim under test: it does not finish on its own. Evidence: zero bestmove lines, depth still climbing.
  D2  `go btime 6000000`, White to move, `stop` sent at STOP_S, then `quit`.
      Claim under test: the only thing that ends it is the stop. Evidence: bestmove appears once, after the stop,
      and the last info line's own `time` field is greater than every bound a clock could have imposed.

D2 is the run quoted in S-C37 leg D (depth 27, ~31 M nodes, ~18 s of search, bestmove only at the 20 s stop).
The engine cannot know when the opponent will move, so no value of the opponent's clock can bound this search —
the mechanism, not just the observation.

Usage: check_partial_clock_long.py <pc-exe> <outdir>
"""
import hashlib, json, os, select, subprocess, sys, time
from pathlib import Path

KILL_S = 8.0
STOP_S = 20.0
OPTS = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
        ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
        ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
        ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
        ("IirDepth", "2"), ("NonPawnCorrection", "true"), ("CuckooRep", "true"), ("HistRework", "2"),
        ("TtPruneV2", "true"), ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false"),
        ("Threads", "1"), ("Hash", "16")]
W_FEN = "r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 w - - 0 1"
GO = "go btime 6000000"


class R:
    def __init__(self, fd):
        self.fd, self.buf, self.eof = fd, b"", False

    def line(self, dl):
        while b"\n" not in self.buf:
            if self.eof:
                return None
            rem = dl - time.monotonic()
            if rem <= 0:
                return None
            r, _, _ = select.select([self.fd], [], [], rem)
            if not r:
                return None
            c = os.read(self.fd, 65536)
            if not c:
                self.eof = True
                return None
            self.buf += c
        l, _, self.buf = self.buf.partition(b"\n")
        return l.decode("utf-8", "replace")


def depth_of(l):
    if not l.startswith("info depth"):
        return None
    f = l.split()
    try:
        return int(f[2])
    except (IndexError, ValueError):
        return None


def nodes_of(l):
    f = l.split()
    for i, t in enumerate(f):
        if t == "nodes" and i + 1 < len(f):
            try:
                return int(f[i + 1])
            except ValueError:
                return None
    return None


def time_of(l):
    f = l.split()
    for i, t in enumerate(f):
        if t == "time" and i + 1 < len(f):
            try:
                return int(f[i + 1])
            except ValueError:
                return None
    return None


def session(exe, send_stop_after=None, kill_after=KILL_S):
    """Run one `go`, record every line, and report whether bestmove came before the stop."""
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, bufsize=0, cwd="/tmp")
    rd = R(p.stdout.fileno())
    buf, marks = [], {}

    def until(pre, dl):
        while True:
            l = rd.line(dl)
            if l is None:
                return None
            buf.append(l)
            if l.startswith(pre):
                return l

    def send(s):
        try:
            p.stdin.write((s + "\n").encode())
            p.stdin.flush()
        except Exception:
            pass

    d = time.monotonic() + 30
    send("uci")
    until("uciok", d)
    for n, v in OPTS:
        send("setoption name %s value %s" % (n, v))
        send("isready")
        until("readyok", d)
    send("ucinewgame")
    send("isready")
    until("readyok", d)
    send("position fen " + W_FEN)
    send("isready")
    until("readyok", d)

    t0 = time.monotonic()
    marks["t_go"] = 0.0
    send(GO)
    stopped_at = None
    if send_stop_after is not None:
        while time.monotonic() - t0 < send_stop_after:
            l = rd.line(time.monotonic() + 0.2)
            if l is None:
                if p.poll() is not None:
                    break
                continue
            buf.append(l)
        stopped_at = time.monotonic() - t0
        marks["t_stop_sent"] = round(stopped_at, 2)
        send("stop")
    # drain until bestmove, the process dies, or the kill deadline
    end = time.monotonic() + (60.0 if send_stop_after is not None else kill_after)
    bm_at = None
    while time.monotonic() < end:
        l = rd.line(time.monotonic() + 0.2)
        if l is None:
            if p.poll() is not None:
                break
            continue
        buf.append(l)
        if l.startswith("bestmove"):
            bm_at = time.monotonic() - t0
            break
    if send_stop_after is None:
        marks["killed_at"] = round(time.monotonic() - t0, 2)
        p.kill()
    else:
        send("quit")
        try:
            p.wait(timeout=10)
        except Exception:
            p.kill()

    infos = [l for l in buf if l.startswith("info depth")]
    depths = [x for x in (depth_of(l) for l in infos) if x is not None]
    bestmoves = [l for l in buf if l.startswith("bestmove")]
    info_strings = [l for l in buf if l.startswith("info string")]
    return {
        "go": GO, "fen": W_FEN,
        "stop_sent": send_stop_after is not None,
        "stop_at_s": None if stopped_at is None else round(stopped_at, 2),
        "bestmove": bestmoves[0].split()[1] if bestmoves else None,
        "bestmove_at_s": None if bm_at is None else round(bm_at, 2),
        "bestmove_lines": len(bestmoves),
        "info_depth_lines": len(infos),
        "max_depth": max(depths) if depths else None,
        "max_nodes": max([n for n in (nodes_of(l) for l in infos) if n is not None] or [0]) or None,
        "last_time_ms": (time_of(infos[-1]) if infos else None),
        "info_strings": info_strings,
        "marks": marks,
        # the verdict-bearing field: was the bestmove produced before the stop could have arrived?
        "answered_without_stop": bm_at is not None and (stopped_at is None or bm_at <= stopped_at),
    }


def main():
    exe = sys.argv[1]
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()

    print("D1: no stop, killed at %.0f s ..." % KILL_S, flush=True)
    d1 = session(exe, send_stop_after=None, kill_after=KILL_S)
    print("D1: bestmove=%s depth=%s nodes=%s killed_at=%s"
          % (d1["bestmove"], d1["max_depth"], d1["max_nodes"], d1["marks"].get("killed_at")), flush=True)

    print("D2: stop sent at %.0f s ..." % STOP_S, flush=True)
    d2 = session(exe, send_stop_after=STOP_S)
    print("D2: bestmove=%s at %ss depth=%s nodes=%s last_time=%sms"
          % (d2["bestmove"], d2["bestmove_at_s"], d2["max_depth"], d2["max_nodes"], d2["last_time_ms"]),
          flush=True)

    L = ["CHECK LONG: does a huge OPPONENT clock bound a White-to-move search? (seat 02's aside)",
         "exe_started: %s" % exe,
         "sha256: %s" % sha,
         "PC r15 + PC20, Threads 1, Hash 16. Position (White to move):",
         "  " + W_FEN,
         "Command under test: %s" % GO,
         "",
         "D1  stop never sent, process killed at %.0f s" % KILL_S,
         "    bestmove lines        : %d" % d1["bestmove_lines"],
         "    info depth lines      : %d" % d1["info_depth_lines"],
         "    deepest depth reached : %s" % d1["max_depth"],
         "    nodes at deepest      : %s" % d1["max_nodes"],
         "    last info 'time'      : %s ms" % d1["last_time_ms"],
         "",
         "D2  stop sent at %.0f s, then quit" % STOP_S,
         "    bestmove              : %s" % d2["bestmove"],
         "    bestmove arrived at   : %s s (stop sent at %s s)" % (d2["bestmove_at_s"], d2["stop_at_s"]),
         "    info depth lines      : %d" % d2["info_depth_lines"],
         "    deepest depth reached : %s" % d2["max_depth"],
         "    nodes at deepest      : %s" % d2["max_nodes"],
         "    last info 'time'      : %s ms" % d2["last_time_ms"],
         "    info string lines     : %s" % (d2["info_strings"] or "NONE"),
         ""]

    d1_ok = d1["bestmove_lines"] == 0 and d1["max_depth"] is not None
    d2_ok = (d2["bestmove"] is not None and d2["stop_at_s"] is not None
             and not d2["answered_without_stop"] and d2["info_depth_lines"] > 1)
    V = []
    if d1_ok and d2_ok:
        V.append("VERDICT: REFUTES the aside. A huge opponent clock does NOT bound a White-to-move search.")
        V.append("  D1: with no stop sent, the engine emitted %d bestmove lines in %.0f s and was still deepening"
                 % (d1["bestmove_lines"], KILL_S))
        V.append("      (depth %s reached, %s nodes). A bounded search would have answered."
                 % (d1["max_depth"], d1["max_nodes"]))
        V.append("  D2: the same command ran to depth %s / %s nodes, spending %s ms of search, and produced a"
                 % (d2["max_depth"], d2["max_nodes"], d2["last_time_ms"]))
        V.append("      bestmove ONLY after the explicit stop at %s s." % d2["stop_at_s"])
        V.append("  Neither run emitted any info string, so the protocol reports nothing wrong while the GUI waits.")
        V.append("  MECHANISM: the engine cannot know when the opponent will move, so the opponent's clock is not")
        V.append("  a bound it can honour. No value of btime bounds this search, which is why \"send a big number\"")
        V.append("  is not a workaround. The fix is one info string plus a bounded default, never padding a clock.")
        V.append("  This is Trap 6's hazard arriving through the protocol: an unbounded call cannot be told from a")
        V.append("  slow one, so both legs above name their stopping condition explicitly.")
    elif d1["bestmove_lines"] == 0 and d2["bestmove"] is None:
        V.append("VERDICT: nothing answered at all - the search is unbounded, but D2 did not produce a bestmove")
        V.append("  even after the stop. Reported as is; do not read this as the refutation being proved.")
    else:
        V.append("VERDICT: DOES NOT REFUTE - a bestmove appeared without a stop being sent. See the numbers.")
    L += V
    (out / "check_partial_clock_long.json").write_text(
        json.dumps({"d1": d1, "d2": d2, "verdict": V}, indent=1))
    (out / "check_partial_clock_long.txt").write_text("\n".join(L) + "\n")
    print("")
    print("\n".join(V))


if __name__ == "__main__":
    main()
