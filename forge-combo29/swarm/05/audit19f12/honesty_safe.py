#!/usr/bin/env python3
"""honesty_safe.py EXE OUTDIR -- re-runs the four honesty checks WITHOUT piping quit behind a live command
(the pattern seat 19's 19-F12 says can fabricate a bestmove). Each line is sent on a live pipe and stdout is
read until the command's own terminator (`uciok`, `readyok`, or `bestmove`) before anything else is sent.
Kept specifically because job0/honesty.sh used `printf '...\nquit\n' | forge`, which is the risky pattern.
"""
import hashlib
import os
import subprocess
import sys
import time

EXE = sys.argv[1]
OUT = sys.argv[2]
os.makedirs(OUT, exist_ok=True)

CASES = [
    # (name, command, terminator token that ends this command, expected nodes)
    ("bench11", "bench 11", "bestmove", 312866),
    ("bench13", "bench 13", "bestmove", 862329),
    ("bench16", "bench 16", "bestmove", 3024920),
    ("perft5", "go perft 5", "bestmove", 4865609),
]


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def run_one(cmd, token, limit=300):
    """live process: send the command, then isready, and read until the readyok that FOLLOWS the command's
    output. UCI is strictly ordered, so that readyok cannot arrive before the command has finished -- which
    makes this safe for commands that do not end in `bestmove` (bench prints an `info string bench ...` line).
    quit is only ever sent after that readyok.
    """
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, bufsize=1)
    out = []

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def until(tok):
        t0 = time.time()
        while time.time() - t0 < limit:
            line = p.stdout.readline()
            if line == "":
                out.append("### EOF")
                return False
            line = line.rstrip("\n")
            out.append(line)
            if line.startswith(tok):
                return True
        out.append("### TIMEOUT")
        return False

    send("uci")
    until("uciok")
    send("isready")
    until("readyok")
    send(cmd)
    send("isready")            # queued behind the command: its readyok means the command is done
    got = until("readyok")
    send("quit")
    try:
        p.wait(timeout=15)
    except subprocess.TimeoutExpired:
        p.kill()
    rest = p.stdout.read()
    if rest:
        out += rest.splitlines()
    return out, got


with open(f"{OUT}/meta.txt", "w") as m:
    m.write(f"exe_started: {os.path.abspath(EXE)}\n")
    m.write(f"sha256: {sha256(EXE)}\n")
    m.write(f"date_utc: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n")
    m.write("harness: honesty_safe.py -- one live process per line, reads stdout to the command's terminator\n")
    m.write("         before sending anything else; quit is only sent AFTER the terminator.\n")
    m.write("options_sent: none (engine defaults, as HONESTY.txt also records)\n")
    r = subprocess.run([EXE], input="uci\nquit\n", capture_output=True, text=True)
    for l in r.stdout.splitlines():
        if l.startswith("id name"):
            m.write("id_name: " + l + "\n")

print("| name | command | expected | got | verdict |")
print("|---|---|---|---|---|")
allok = True
for name, cmd, tok, want in CASES:
    lines, got = run_one(cmd, tok)
    with open(f"{OUT}/{name}.raw.txt", "w") as f:
        f.write("\n".join(lines) + "\n")
    got_nodes = None
    for l in lines:
        import re
        mm = re.search(r"nodes (\d+)", l)
        if mm:
            got_nodes = mm.group(1)
    ok = (got_nodes is not None and int(got_nodes) == want)
    allok = allok and ok
    print(f"| {name} | `{cmd}` | {want} | {got_nodes} | {'OK' if ok else 'MISMATCH'} |")
print()
print("HONESTY RECHECK", "PASS 4/4" if allok else "FAIL")
