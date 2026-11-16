#!/usr/bin/env python3
"""audit_19f12.py EXE -- checks EVERY harness pattern I used against seat 19's finding 19-F12
("if you pipe quit or close stdin while a search runs, this build answers a FABRICATED bestmove with 0 nodes").

Patterns tested on the same FEN (startpos and a middlegame FEN), `go depth 12`:
  P1 PIPED-QUIT   : whole script as one stdin string ending in `quit` (the pattern 19-F12 describes)
  P2 QUIT-IMMEDIATE: live process, go then quit at once
  P3 QUIT-AFTER-2S: live process, go, wait 2 s, quit
  P4 READ-TO-BESTMOVE (my harnesses): live process, read stdout until `bestmove`, then quit
Every pattern is run and the result printed, so the difference is visible in one table.
"""
import re
import subprocess
import sys
import time

EXE = sys.argv[1]
S14 = ["setoption name Threads value 1", "setoption name Hash value 16"]
CASES = [("startpos", ""), ("middlegame", "r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8")]
GO = "go depth 12"


def prep(fen):
    cmds = ["uci", "isready"]
    for o in S14:
        cmds += [o, "isready"]
    cmds += ["ucinewgame", "isready"]
    cmds.append(f"position fen {fen}" if fen else "position startpos")
    cmds += ["isready"]
    return cmds


def summarise(lines):
    pv = [l for l in lines if re.search(r"\binfo\b.*\bpv\b", l)]
    bm = [l for l in lines if l.startswith("bestmove")]
    last = pv[-1] if pv else "(no info/pv line)"
    nodes = "-"
    if pv:
        m = re.search(r"\bnodes (\d+)", pv[-1])
        nodes = m.group(1) if m else "?"
    return dict(n_info=len(pv), nodes=nodes, best=bm[0] if bm else "(none bestmove)",
                last=last, all_lines=lines)


def p1_piped_quit(fen):
    script = "\n".join(prep(fen) + [GO, "quit"]) + "\n"
    p = subprocess.run([EXE], input=script, capture_output=True, text=True, timeout=120)
    return summarise(p.stdout.splitlines())


def p2_quit_immediate(fen):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, bufsize=1)
    for c in prep(fen):
        p.stdin.write(c + "\n")
    p.stdin.write(GO + "\n")
    p.stdin.write("quit\n")
    p.stdin.flush()
    out = p.stdout.read().splitlines()
    p.wait(timeout=30)
    return summarise(out)


def p3_quit_after(fen, delay=2.0):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, bufsize=1)
    for c in prep(fen):
        p.stdin.write(c + "\n")
    p.stdin.flush()
    p.stdin.write(GO + "\n")
    p.stdin.flush()
    time.sleep(delay)
    p.stdin.write("quit\n")
    p.stdin.flush()
    out = p.stdout.read().splitlines()
    p.wait(timeout=30)
    return summarise(out)


def p4_read_to_bestmove(fen):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, bufsize=1)
    out = []

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    for c in prep(fen):
        send(c)
    send(GO)
    while True:
        line = p.stdout.readline()
        if line == "":
            break
        line = line.rstrip("\n")
        out.append(line)
        if line.startswith("bestmove"):
            break
    send("quit")
    try:
        p.wait(timeout=15)
    except subprocess.TimeoutExpired:
        p.kill()
    rest = p.stdout.read()
    if rest:
        out += rest.splitlines()
    return summarise(out)


print(f"exe: {EXE}")
print(f"go: {GO}, S14, Threads 1, Hash 16")
print()
for name, fen in CASES:
    print(f"########## {name} ({fen or 'startpos'})")
    for label, fn in (("P1 PIPED-QUIT", p1_piped_quit), ("P2 QUIT-IMMEDIATE", p2_quit_immediate),
                      ("P3 QUIT-AFTER-2S", p3_quit_after), ("P4 READ-TO-BESTMOVE", p4_read_to_bestmove)):
        try:
            r = fn(fen)
            print(f"  {label:20s} info_lines={r['n_info']:3d} nodes={r['nodes']:>8s} {r['best']}")
            print(f"  {'':20s} last: {r['last'][:110]}")
        except Exception as e:
            print(f"  {label:20s} EXCEPTION {e}")
    print()
