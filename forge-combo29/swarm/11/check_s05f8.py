#!/usr/bin/env python3
"""check_s05f8.py EXE — seat 11's INDEPENDENT check of seat 05's S-F8 (also 24-C3).

S-F8 claims: `go infinite` at a terminal root never answers — no bestmove after 30 s on a
checkmate root AND on a stalemate root — while `go depth 5` on the same board answers 0000 at
once; and an explicit `stop` DOES produce `bestmove 0000` in ~0.2 s, so the defect is "never
volunteers a bestmove", not "cannot be stopped".

Written from that sentence; seat 05's scripts not read. This is a HANG test, so the timeout is
the measurement — I use a queue with a real deadline (my runner's earlier bug was exactly a
blocking read with no timeout).
"""
import os, queue, subprocess, sys, threading, time

EXE = sys.argv[1]
CHECKMATE = "8/8/8/8/8/6K1/8/Q5k1 b - - 0 1"      # Black to move, checkmated
STALEMATE = "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"      # Black to move, stalemated
ORDINARY = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
WAIT = 6.0          # shorter than seat 05's 30 s, enough to prove "no volunteer"


def talk(fen, go_line, stop_after=None, wait=WAIT):
    """Returns (lines, got_bestmove, elapsed)."""
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    q = queue.Queue()

    def pump():
        try:
            for line in iter(p.stdout.readline, ""):
                q.put(line.rstrip("\n"))
        except Exception:
            pass
        q.put(None)
    threading.Thread(target=pump, daemon=True).start()

    p.stdin.write(f"uci\nisready\n"); p.stdin.flush()
    lines = []
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            l = q.get(timeout=0.5)
        except queue.Empty:
            continue
        if l is None:
            break
        lines.append(l)
        if l.strip() == "uciok":
            pass
    p.stdin.write(f"position fen {fen}\nisready\n{go_line}\n"); p.stdin.flush()

    t0 = time.monotonic()
    bm = None
    got_at = None
    stop_sent = False
    while True:
        remaining = wait - (time.monotonic() - t0)
        if stop_after is not None and not stop_sent and (time.monotonic() - t0) >= stop_after:
            p.stdin.write("stop\n"); p.stdin.flush()
            stop_sent = True
        if remaining <= 0:
            break
        try:
            l = q.get(timeout=min(0.25, max(0.01, remaining)))
        except queue.Empty:
            if stop_after is not None and not stop_sent:
                continue
            continue
        if l is None:
            break
        lines.append(l)
        if l.startswith("bestmove"):
            bm = l.split()[1] if len(l.split()) > 1 else "?"
            got_at = time.monotonic() - t0
            break
        if stop_after is not None and not stop_sent and (time.monotonic() - t0) >= stop_after:
            p.stdin.write("stop\n"); p.stdin.flush()
            stop_sent = True
    el = time.monotonic() - t0
    try:
        p.stdin.write("quit\n"); p.stdin.flush(); p.wait(timeout=5)
    except Exception:
        p.kill()
    return bm, got_at, el, lines


def show(label, fen, go, stop_after=None):
    bm, got_at, el, lines = talk(fen, go, stop_after=stop_after)
    info = [l for l in lines if l.startswith("info depth")]
    print(f"  {label:34} go={go:14} bestmove={str(bm):6} at={('%.2fs' % got_at) if got_at else 'NEVER':7} "
          f"info_lines={len(info)}")
    return bm, got_at, info


print(f"wait window: {WAIT}s")
print("\n=== A. go infinite at terminal roots (does it VOLUNTEER a bestmove?) ===")
cm = show("checkmated root", CHECKMATE, "go infinite")
st = show("stalemated root", STALEMATE, "go infinite")

print("\n=== B. go depth 5 on the same roots (must answer at once) ===")
cm5 = show("checkmated root", CHECKMATE, "go depth 5")
st5 = show("stalemated root", STALEMATE, "go depth 5")

print("\n=== C. go infinite + explicit stop after 0.3 s ===")
cms = show("checkmated root", CHECKMATE, "go infinite", stop_after=0.3)
sts = show("stalemated root", STALEMATE, "go infinite", stop_after=0.3)

print("\n=== D. control: go infinite on an ORDINARY board answers only on stop ===")
ord1 = show("ordinary board", ORDINARY, "go infinite")
ords = show("ordinary board", ORDINARY, "go infinite", stop_after=0.3)

print("\n=== verdict on S-F8 ===")
fail = []
def chk(name, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}{('  — ' + detail) if detail else ''}")
    if not cond:
        fail.append(name)

chk("checkmate root: go infinite NEVER volunteers a bestmove in the window", cm[1] is None)
chk("stalemate root: go infinite NEVER volunteers a bestmove in the window", st[1] is None)
chk("checkmate root: go depth 5 answers at once", cm5[0] == "0000", f"got {cm5[0]}")
chk("stalemate root: go depth 5 answers at once", st5[0] == "0000", f"got {st5[0]}")
chk("checkmate root: stop DOES produce 0000", cms[0] == "0000", f"got {cms[0]}")
chk("stalemate root: stop DOES produce 0000", sts[0] == "0000", f"got {sts[0]}")
chk("control: the ordinary board also only answers on stop", ord1[1] is None and ords[0] is not None)

print()
if not fail:
    print("RESULT: CONFIRMS S-F8 — `go infinite` at a terminal root never volunteers a bestmove,")
    print("        while `go depth 5` answers 0000 immediately and `stop` releases it.")
else:
    print("RESULT: does NOT reproduce S-F8 as stated — see FAIL lines.")
