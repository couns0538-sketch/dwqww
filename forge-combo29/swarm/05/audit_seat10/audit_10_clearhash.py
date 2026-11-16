#!/usr/bin/env python3
"""audit_10_clearhash.py EXE -- seat 10's warning, applied to my results.

(1) Reproduce seat 10's three numbers on THEIR claim shape: startpos, go depth 12, one process, no command
    between two identical searches -> node count should fall on the repeats; three separate processes -> equal.
(2) Confirm what my own harnesses do: which of my node-count claims came from ONE search per fresh process
    (cold) and which from repeats inside one process (warm, and therefore must not be quoted as a baseline).
No `Clear Hash` appears anywhere in my folder (grepped), so that part needs no test from me.
"""
import re
import subprocess
import sys
import time

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-rel/forge"
GO = "go depth 12"


def one_process_repeats(n=3, between=None):
    """ONE process, n identical searches, nothing between them (or `between` sent between searches)"""
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, bufsize=1)
    out = []

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def until(tok, limit=120):
        got = []
        t0 = time.time()
        while time.time() - t0 < limit:
            line = p.stdout.readline()
            if line == "":
                return got
            line = line.rstrip("\n")
            got.append(line)
            if line.startswith(tok):
                return got
        return got

    send("uci")
    until("uciok")
    send("setoption name Threads value 1")
    send("isready"); until("readyok")
    send("setoption name Hash value 16")
    send("isready"); until("readyok")
    send("ucinewgame")
    send("isready"); until("readyok")
    nodes = []
    for i in range(n):
        if between and i > 0:
            send(between)
            send("isready"); until("readyok")
        send("position startpos")
        send("isready"); until("readyok")
        send(GO)
        block = until("bestmove")
        pv = [l for l in block if re.search(r"\binfo\b.*\bpv\b", l)]
        if pv:
            m = re.search(r"\bnodes (\d+)", pv[-1])
            nodes.append(int(m.group(1)) if m else None)
        else:
            nodes.append(None)
    send("quit")
    try:
        p.wait(timeout=15)
    except subprocess.TimeoutExpired:
        p.kill()
    return nodes


def separate_processes(n=3):
    """a FRESH process per run, reading to bestmove before quit (19-F12 discipline)"""
    out = []
    for _ in range(n):
        p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True, bufsize=1)
        lines = []

        def send(cmd):
            p.stdin.write(cmd + "\n")
            p.stdin.flush()

        def until(tok, limit=300):
            t0 = time.time()
            while time.time() - t0 < limit:
                line = p.stdout.readline()
                if line == "":
                    return
                line = line.rstrip("\n")
                lines.append(line)
                if line.startswith(tok):
                    return
        send("uci"); until("uciok")
        send("setoption name Threads value 1"); send("isready"); until("readyok")
        send("setoption name Hash value 16"); send("isready"); until("readyok")
        send("ucinewgame"); send("isready"); until("readyok")
        send("position startpos"); send("isready"); until("readyok")
        send(GO)
        until("bestmove")
        send("quit")
        try:
            p.wait(timeout=15)
        except subprocess.TimeoutExpired:
            p.kill()
        pv = [l for l in lines if re.search(r"\binfo\b.*\bpv\b", l)]
        if pv:
            m = re.search(r"\bnodes (\d+)", pv[-1])
            out.append(int(m.group(1)) if m else None)
        else:
            out.append(None)
    return out


print(f"exe: {EXE}   search: startpos, {GO}, Threads 1, Hash 16")
print()
a = one_process_repeats(3)
print(f"ONE process, 3 identical searches, NOTHING between them  : {a}")
b = separate_processes(3)
print(f"THREE separate processes, same search                    : {b}")
print()
print("seat 10 reported: one process 56,720 / 4,951 / 4,516 and three processes 56,720 three times.")
print(f"my first-process value: {a[0] if a else '?'}   my separate-process values: {b}")
print()
same_across_processes = len(set(b)) == 1 and b[0] is not None
falls_inside_process = (a[0] is not None and a[-1] is not None and a[-1] < a[0])
print(f"cold is stable across processes: {same_across_processes}")
print(f"warm repeats inside one process fall: {falls_inside_process}")
print()
if same_across_processes and falls_inside_process:
    print("RESULT: CONFIRMS seat 10's shape. A cold baseline must be a fresh process (or ucinewgame);")
    print("        a second search in the same process is NOT a baseline.")
else:
    print("RESULT: does NOT reproduce this shape on my build — reported as such.")
