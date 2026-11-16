#!/usr/bin/env python3
"""matrix_builds.py OUTFILE BUILD:NAME ... : run `go depth 8` on the endgame positions for several builds and report,
per build, how many of the four known differences it reproduces.

"A difference is reproduced" means: the build plays the BASE answer where the base played it, i.e. the build's move
differs from the PC answer. Concretely, for each of the four positions the two answers are known:
    idx 153: base a4b4   pc a4b5
    idx 155: base c6d6   pc c6c7
    idx 156: base g5h3   pc f2e3
    idx 160: base f1e2   pc f1f2
A build "agrees with PC" on a position when it plays the pc move, "agrees with base" when it plays the base move, and
"other" when it plays neither (a third answer, which is itself interesting).

Settings: Threads 1, Hash 16, OwnBook false, fresh process per search, read to bestmove then quit.
The script fails loudly if any build produces no bestmove for any position.
"""
import os
import subprocess
import sys

OUT = sys.argv[1]
BUILDS = []
for a in sys.argv[2:]:
    name, _, path = a.partition(":")
    BUILDS.append((name, path))

HERE = os.path.dirname(os.path.abspath(__file__))
FENS26 = [l.strip() for l in open(os.path.join(HERE, "set_end26.fens")) if l.strip()]
IDX26 = [int(x) for x in open(os.path.join(HERE, "end26_indices.txt")).read().split()]
PC_ANSWERS = {153: "a4b5", 155: "c6c7", 156: "f2e3", 160: "f1f2"}
BASE_ANSWERS = {153: "a4b4", 155: "c6d6", 156: "g5h3", 160: "f1e2"}
DEPTH = 8

rawdir = OUT + ".raw"
os.makedirs(rawdir, exist_ok=True)


def bestmove(exe, fen, tag):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    raw = open(os.path.join(rawdir, tag + ".txt"), "w")

    def send(c):
        raw.write(f">>> {c}\n")
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def until(tok):
        while True:
            line = p.stdout.readline()
            if line == "":
                raise RuntimeError(f"engine died waiting for {tok!r} ({tag})")
            raw.write(line)
            raw.flush()
            s = line.strip()
            if s.startswith(tok):
                return s
            for w in ("unknown option", "invalid value", "ERROR", "invalid FEN"):
                if w in s:
                    raise RuntimeError(f"engine refused ({tag}): {s}")

    send("uci"); until("uciok")
    send("isready"); until("readyok")
    for o, v in (("Threads", "1"), ("Hash", "16"), ("OwnBook", "false")):
        send(f"setoption name {o} value {v}")
        send("isready"); until("readyok")
    send("ucinewgame"); send("isready"); until("readyok")
    send(f"position fen {fen}")
    send("isready"); until("readyok")
    send(f"go depth {DEPTH}")
    bm = None
    while True:
        line = p.stdout.readline()
        if line == "":
            raise RuntimeError(f"died before bestmove ({tag})")
        raw.write(line)
        raw.flush()
        s = line.strip()
        if s.startswith("bestmove"):
            bm = s.split()[1]
            break
    send("quit")
    try:
        p.wait(timeout=60)
    except Exception:  # noqa: BLE001
        p.kill()
    raw.close()
    return bm


results = {}
fails = []
for name, exe in BUILDS:
    moves = {}
    for pos, fen in enumerate(FENS26):
        idx = IDX26[pos]
        try:
            moves[idx] = bestmove(exe, fen, f"{name}_p{idx:03d}")
        except Exception as ex:  # noqa: BLE001
            fails.append((name, idx, str(ex)))
            print(f"FAIL {name} idx {idx}: {ex}", flush=True)
    results[name] = moves
    print(f"{name}: measured {len(moves)}/{len(FENS26)}", flush=True)

lines = []
lines.append(f"depth {DEPTH}, Threads 1, Hash 16, OwnBook false, fresh process per search")
lines.append(f"positions: the 26 endgame positions of the 200-position set (material <= 12 non-king)")
lines.append("")
hdr = "| build | " + " | ".join(f"idx {i}" for i in sorted(PC_ANSWERS)) + " | of 4 reproduce BASE | agrees with PC |"
lines.append(hdr)
lines.append("|---|" + "---|" * (len(PC_ANSWERS) + 2))
per_build = {}
for name, exe in BUILDS:
    row, base_like, pc_like, other = [name], 0, 0, 0
    for idx in sorted(PC_ANSWERS):
        mv = results[name].get(idx, "?")
        if mv == BASE_ANSWERS[idx]:
            base_like += 1
            cell = f"{mv} (base)"
        elif mv == PC_ANSWERS[idx]:
            pc_like += 1
            cell = f"{mv} (PC)"
        else:
            other += 1
            cell = f"{mv} (other)"
        row.append(cell)
    row.append(str(base_like))
    row.append(str(pc_like))
    lines.append("| " + " | ".join(row) + " |")
    per_build[name] = (base_like, pc_like, other)

lines.append("")
lines.append("full detail per build (all 26 endgame positions):")
for name, exe in BUILDS:
    lines.append(f"  {name}: " + ", ".join(f"{i}:{results[name].get(i,'?')}" for i in IDX26))

if fails:
    lines.append("")
    lines.append(f"MEASUREMENT FAILURES: {len(fails)}")
    for f in fails:
        lines.append(str(f))

open(OUT, "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
if fails:
    sys.exit(f"{len(fails)} measurement failures — table incomplete")
