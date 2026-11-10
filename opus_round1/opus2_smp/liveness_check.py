#!/usr/bin/env python3
"""opus2 SMP pack (fable bug hunt NIT-1): prove in CI that UCI TtLockless is APPLIED, not only advertised and accepted.
A node-identical option cannot be proven live by pins. Its documented side effect is: a mode change reallocates the
table empty (SPEC 3.6). Port of opus_smp_layout/tools/liveness_check.ps1, Threads 1, Hash 16, OwnBook false:
  session A (option off): ucinewgame + go depth D -> a1 (cold); go depth D -> a2 (warm); Clear Hash; go depth D -> a3
  session B (option on):  ucinewgame + go depth D -> b1 (cold); go depth D -> b2 (warm); TtLockless false; go depth D -> b3
PASS needs b1 = a1 and b2 = a2 (lockless node-identical cold and warm), a2 != a1 (the warm search reuses the table),
a3 != a2 (emptying the table is visible) and b3 = a3 (the toggle emptied the table exactly as Clear Hash does).
Nodes, best move and score are compared; every engine must exit 0 after quit.
usage: liveness_check.py <forge_exe> [depth=12]"""
import re
import subprocess
import sys

FEN = "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP1B1PPP/R2QKB1R w KQ - 0 8"


def session(exe, depth, options, empty_cmd):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def wait(pattern):
        rx = re.compile(pattern)
        for line in p.stdout:
            if rx.search(line):
                return line
        raise SystemExit("engine exited before matching " + pattern)

    def search(new_game):
        if new_game:
            send("ucinewgame")
        send("position fen " + FEN)
        send(f"go depth {depth}")
        nodes = score = None
        for line in p.stdout:
            if line.startswith("info ") and " nodes " in line:
                m = re.search(r" nodes (\d+)", line)
                nodes = int(m.group(1))
                s = re.search(r" score (cp|mate) (-?\d+)", line)
                if s:
                    score = s.group(1) + " " + s.group(2)
            if line.startswith("bestmove"):
                return (nodes, line.split()[1], score)
        raise SystemExit("engine exited during a search")

    send("uci")
    wait(r"^uciok")
    for o in ["Threads value 1", "Hash value 16", "OwnBook value false"] + options:
        send("setoption name " + o)
    send("isready")
    wait(r"^readyok")
    r = [search(True), search(False)]
    send(empty_cmd)
    send("isready")
    wait(r"^readyok")
    r.append(search(False))
    send("quit")
    code = p.wait(timeout=60)
    return r, code


def main():
    exe = sys.argv[1]
    depth = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    a, code_a = session(exe, depth, [], "setoption name Clear Hash")
    b, code_b = session(exe, depth, ["TtLockless value true"], "setoption name TtLockless value false")
    names = ["cold", "warm", "after empty"]
    for tag, rows in (("a legacy", a), ("b lockless", b)):
        for name, row in zip(names, rows):
            print(f"{tag:10s} {name:11s} nodes {row[0]} best {row[1]} score {row[2]}")
    checks = [
        ("lockless cold = legacy cold (b1 = a1)", b[0] == a[0]),
        ("lockless warm = legacy warm (b2 = a2)", b[1] == a[1]),
        ("warm reuses the table (a2 != a1 nodes)", a[1][0] != a[0][0]),
        ("emptying the table is visible (a3 != a2 nodes)", a[2][0] != a[1][0]),
        ("toggle emptied the table like Clear Hash (b3 = a3)", b[2] == a[2]),
        ("both engines exit 0 after quit", code_a == 0 and code_b == 0),
    ]
    bad = 0
    for text, ok in checks:
        print(f"{text:52s} {'OK' if ok else 'FAIL'}")
        bad += 0 if ok else 1
    print("LIVENESS: PASS (TtLockless is live and node-identical cold and warm)" if bad == 0 else f"LIVENESS: FAIL ({bad})")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
