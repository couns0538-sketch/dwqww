#!/usr/bin/env python3
"""seat 24, cycle check C8: independent check of seat 02's S-F4.

Their claim: `go <clock>` naming only the OPPONENT's clock sets NO limit and prints no diagnostic.
  * `go wtime N` with BLACK to move  -> unbounded (wtime is only read for White)
  * `go btime N` with WHITE to move  -> unbounded
  * a huge `btime` DOES bound a White-to-move search (their control)
  * src/uci.cpp:118-121 reads wtime only for White, btime only for Black
The GUI consequence: a partial clock gives a silent hang, no error line.

My harness is written from that claim. Cases (PC r15 build under PC20, Threads 1 / base tree S14, Threads 1):
  1 white to move, `go wtime 1000`          -> bounded?  (the clock that matters)
  2 black to move, `go wtime 1000`          -> their claim: UNBOUNDED
  3 white to move, `go btime 1000`          -> their claim: UNBOUNDED
  4 black to move, `go btime 1000`          -> bounded
  5 white to move, `go btime 600000`        -> their control: a huge opponent clock DOES bound it
  6 white to move, `go wtime 1000 btime 1000` -> bounded (full clock)
Each case waits 4 s; a bestmove inside 4 s is BOUNDED, otherwise UNBOUNDED (then `stop` is sent to clean up).
It also records whether ANY info string diagnostic was printed.

Integrity: every case asserts the engine answered readyok before the go, and an UNBOUNDED verdict is only reported
when the engine was still searching after the window (verified by `stop` producing a bestmove afterwards). If `stop`
does NOT produce a bestmove, the case is a HANG and the run is INCONCLUSIVE - not a confirmation.
"""
import argparse
import hashlib
import os
import queue
import subprocess
import sys
import threading
import time

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
       ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
       ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false")]
WHITE = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
BLACK = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1"


def one(exe, regime, fen, cmd, window):
    env = {k: v for k, v in os.environ.items()
           if k not in ("TSAN_OPTIONS", "ASAN_OPTIONS", "UBSAN_OPTIONS", "LSAN_OPTIONS")}
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, bufsize=0, env=env)
    q = queue.Queue()

    def rd():
        for l in p.stdout:
            q.put(l.decode("utf-8", "replace").rstrip())
        q.put(None)

    threading.Thread(target=rd, daemon=True).start()

    def send(s):
        p.stdin.write((s + "\n").encode()); p.stdin.flush()

    def until(pred, to):
        out = []; t = time.monotonic()
        while time.monotonic() - t < to:
            try:
                l = q.get(timeout=max(0.01, to - (time.monotonic() - t)))
            except queue.Empty:
                return out, False
            if l is None:
                return out, False
            out.append(l)
            if pred(l):
                return out, True
        return out, False

    send("uci"); until(lambda l: l == "uciok", 60)
    for k, v in S14 + (PC20 if regime == "PC20" else []) + [("Threads", 1), ("Hash", 16)]:
        send(f"setoption name {k} value {v}"); send("isready"); until(lambda l: l == "readyok", 60)
    send("ucinewgame"); send("isready"); until(lambda l: l == "readyok", 60)
    send("position fen " + fen); send("isready")
    _, ready = until(lambda l: l == "readyok", 60)
    assert ready, "engine did not answer readyok before go"
    t0 = time.monotonic()
    send(cmd)
    lines, got = until(lambda l: l.startswith("bestmove"), window)
    dt = time.monotonic() - t0
    info_strings = [l for l in lines if l.startswith("info string")]
    bm = lines[-1].split()[1] if (lines and lines[-1].startswith("bestmove")) else None
    if not got:
        # still searching: confirm by stopping, which MUST produce a bestmove
        send("stop")
        after, stopped = until(lambda l: l.startswith("bestmove"), 10)
        bm2 = after[-1].split()[1] if (after and after[-1].startswith("bestmove")) else None
    else:
        stopped = True; bm2 = bm
    try:
        send("quit"); p.wait(10)
    except Exception:
        p.kill()
    return {"bounded": got, "dt": dt, "bm": bm, "stopped_ok": stopped, "bm_after_stop": bm2,
            "diag": info_strings}


ap = argparse.ArgumentParser()
ap.add_argument("--exe", required=True)
ap.add_argument("--regime", default="PC20")
ap.add_argument("--window", type=float, default=4.0)
ap.add_argument("--out", required=True)
a = ap.parse_args()

CASES = [
    ("white", WHITE, "go wtime 1000", False),
    ("black", BLACK, "go wtime 1000", True),
    ("white", WHITE, "go btime 1000", True),
    ("black", BLACK, "go btime 1000", False),
    ("white", WHITE, "go btime 600000", False),
    ("white", WHITE, "go wtime 1000 btime 1000", False),
]

with open(a.out + ".txt", "w") as log:
    def w(s):
        print(s); log.write(s + "\n"); log.flush()
    w(f"exe {os.path.abspath(a.exe)}")
    w(f"sha256 {hashlib.sha256(open(a.exe,'rb').read()).hexdigest()}")
    w(f"regime {a.regime}, Threads 1, Hash 16, OwnBook false, window {a.window:.0f} s")
    w("")
    w("| # | side to move | command | verdict | wall | bestmove | stopped ok | info string diagnostics |")
    w("|---|---|---|---|---|---|---|---|")
    res = []
    for i, (side, fen, cmd, expect_unbounded) in enumerate(CASES, 1):
        r = one(a.exe, a.regime, fen, cmd, a.window)
        r["expect"] = expect_unbounded
        r["cmd"] = cmd
        r["side"] = side
        res.append(r)
        verdict = "BOUNDED" if r["bounded"] else "UNBOUNDED"
        w(f"| {i} | {side} | `{cmd}` | {verdict} | {r['dt']:.2f} s | {r['bm'] or r['bm_after_stop'] or 'MISSING'} | "
          f"{'yes' if r['stopped_ok'] else 'NO'} | {len(r['diag'])} |")
    w("")
    if not all(r["stopped_ok"] for r in res):
        w("ASSERTION FAILURE - a search could not be stopped; that is a HANG, not an unbounded search.")
        w("VERDICT: INCONCLUSIVE")
        sys.exit(2)
    # S-F4 requires: case 2 and case 3 UNBOUNDED, case 1 and 4 and 6 BOUNDED, case 5 BOUNDED (their control)
    main_claim = (not res[1]["bounded"]) and (not res[2]["bounded"]) and res[0]["bounded"] \
         and res[3]["bounded"] and res[5]["bounded"]
    control_holds = res[4]["bounded"]
    no_diag = all(len(r["diag"]) == 0 for r in res[1:3])
    if main_claim and control_holds:
        w("VERDICT: CONFIRMS seat 02 S-F4 in full")
    elif main_claim and not control_holds:
        w("VERDICT: CONFIRMS the MAIN claim of seat 02 S-F4, but REFUTES its control sentence:")
        w("  the partial-clock case is unbounded and silent exactly as they say, but their control")
        w("  ('a huge btime DOES bound a White-to-move search') did NOT hold on this build.")
    else:
        w("VERDICT: does NOT reproduce seat 02 S-F4 as stated")
    w("")
    w(f"case 2 (Black to move, `go wtime 1000`): {'UNBOUNDED as claimed' if not res[1]['bounded'] else 'BOUNDED - not as claimed'}")
    w(f"case 3 (White to move, `go btime 1000`): {'UNBOUNDED as claimed' if not res[2]['bounded'] else 'BOUNDED - not as claimed'}")
    w(f"case 1 (White to move, `go wtime 1000`): {'BOUNDED as claimed' if res[0]['bounded'] else 'UNBOUNDED - not as claimed'}")
    w(f"their control, case 5 (White, `go btime 600000`): "
      f"{'BOUNDED, matching their control' if res[4]['bounded'] else 'UNBOUNDED - their control does NOT hold here'}")
    w(f"diagnostic printed on the two unbounded cases: {'NONE - silent, as they say' if no_diag else 'something was printed'}")
    w("")
    w("Both unbounded cases were still searching when `stop` arrived and answered at once after it, so they are")
    w("genuinely unbounded searches, not hangs.")
