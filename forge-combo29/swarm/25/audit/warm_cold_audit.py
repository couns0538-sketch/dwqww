#!/usr/bin/env python3
"""warm_cold_audit.py EXE : seat 10's rule, verified on THIS build, against MY harness patterns.

Seat 10 reports: two identical searches in one process give 56,720 then 4,951 then 4,516; three separate
processes give 56,720 each; `ucinewgame` restores cold exactly but `Clear Hash` gives 40,569.

I verify three things and print them, because a table is only allowed to be called COLD if this passes:
  A  three fresh processes          -> must agree with each other
  B  one process, search / ucinewgame / search / ucinewgame / search -> must equal A
  C  one process, search / Clear Hash / search -> compare (this is the pattern I must NOT use as a baseline)
"""
import re
import subprocess
import sys

EXE = sys.argv[1]
POS = "position fen rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 2 4"


def nodes_of(line):
    m = re.search(r"nodes (\d+)", line)
    return int(m.group(1)) if m else None


def fresh_process():
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("setoption name Hash value 16\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(POS + "\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("go depth 12\n"); p.stdin.flush()
    last = None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        line = line.rstrip("\n")
        if line.startswith("info depth"):
            last = line
        if line.startswith("bestmove"):
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=5)
    except subprocess.TimeoutExpired:
        p.kill()
    return nodes_of(last or "")


def one_process(reset_cmd, reps=3):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("setoption name Hash value 16\nisready\n"); p.stdin.flush(); until("readyok")
    out = []
    for i in range(reps):
        if reset_cmd:
            p.stdin.write(reset_cmd + "\n")
        p.stdin.write("isready\n"); p.stdin.flush(); until("readyok")
        p.stdin.write(POS + "\nisready\n"); p.stdin.flush(); until("readyok")
        p.stdin.write("go depth 12\n"); p.stdin.flush()
        last = None
        while True:
            line = p.stdout.readline()
            if not line:
                break
            line = line.rstrip("\n")
            if line.startswith("info depth"):
                last = line
            if line.startswith("bestmove"):
                break
        out.append(nodes_of(last or ""))
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=5)
    except subprocess.TimeoutExpired:
        p.kill()
    return out


a = [fresh_process() for _ in range(3)]
print("A three fresh processes          :", a)
b = one_process("ucinewgame")
print("B one process, ucinewgame before :", b)
c = one_process("setoption name Clear Hash")
print("C one process, Clear Hash before :", c)

ok_a = len(set(a)) == 1
ok_b = set(b) == set(a) if ok_a else False
print()
print(f"A agrees with itself            : {ok_a}")
print(f"B (ucinewgame) equals A          : {ok_b}")
print(f"C (Clear Hash) equals A          : {set(c) == set(a)}")
print()
if ok_a and ok_b:
    print("VERDICT: ucinewgame is a cold reset on this build, so my harnesses that send ucinewgame")
    print("         before every search are COLD and their node counts are comparable.")
else:
    print("VERDICT: ucinewgame is NOT a reliable cold reset here — any table of mine that relied on it")
    print("         must be re-labelled WARM.")
