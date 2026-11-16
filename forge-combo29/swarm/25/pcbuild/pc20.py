#!/usr/bin/env python3
"""pc20.py EXE DEPTH FENS OUTJSONL [TAG] : search with settings PC20 on the PC r15 build.

PC20 = the 14 S14 settings, then CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true,
       MateAlphaGuard true, OwnBook false. Threads 1, Hash 16 (swarm rule: Threads 1 for every score).

HARD RULE (brief + Opus file 5): every option name must appear in the exe's own `uci` list, and the run
STOPS on `unknown option`, `invalid value`, `invalid FEN`, or `illegal move`. A silent option failure would
make the whole table meaningless, so this is enforced here and the run exits non-zero on any of them.

Also records, per position, the depth actually REACHED and the full info lines, so an aborted iteration can
never be mistaken for a completed one (the mistake I made earlier with S-F8).
"""
import json
import re
import shlex
import subprocess
import sys

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def list_options(exe):
    p = subprocess.run(shlex.split(exe), input="uci\nquit\n", capture_output=True, text=True, timeout=30)
    return {m.group(1) for m in re.finditer(r"^option name (.+?) type", p.stdout, re.M)}


def run_one(exe, position_cmd, depth, allowed):
    p = subprocess.Popen(shlex.split(exe), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    lines = []
    errors = []

    def send(cmd):
        p.stdin.write(cmd + "\n")
        p.stdin.flush()

    def drain_until(word):
        for line in p.stdout:
            s = line.rstrip("\n")
            lines.append(s)
            for b in BAD:
                if b in s:
                    errors.append(s)
            if s.strip() == word:
                return

    send("uci"); drain_until("uciok")
    send("setoption name Threads value 1"); send("isready"); drain_until("readyok")
    send("setoption name Hash value 16"); send("isready"); drain_until("readyok")
    for name, val in S14 + PC20_EXTRA:
        if name not in allowed:
            errors.append(f"OPTION NOT IN uci LIST: {name}")
        send(f"setoption name {name} value {val}")
    send("isready"); drain_until("readyok")
    send("ucinewgame"); send("isready"); drain_until("readyok")
    send(position_cmd); send("isready"); drain_until("readyok")
    send(f"go depth {depth}")
    best = None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        lines.append(s)
        for b in BAD:
            if b in s:
                errors.append(s)
        if s.startswith("bestmove"):
            best = s
            break
    send("quit")
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    return lines, best, errors


def main():
    exe, depth, fenfile, outfile = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
    allowed = list_options(exe)
    fens = [l.strip() for l in open(fenfile) if l.strip() and not l.startswith("#")]
    print(f"exe options: {len(allowed)} | positions: {len(fens)} | depth {depth} | Threads 1 | Hash 16 | PC20")
    missing = [n for n, _ in S14 + PC20_EXTRA if n not in allowed]
    if missing:
        print(f"STOP: exe does not list {missing}")
        return 3
    all_errors = []
    with open(outfile, "w") as out:
        for i, fen in enumerate(fens):
            lines, best, errors = run_one(exe, f"position fen {fen}", depth, allowed)
            if errors:
                all_errors.extend(errors[:3])
            reached = 0
            for l in lines:
                if l.startswith("info depth"):
                    d = re.search(r"depth (\d+)", l)
                    if d:
                        reached = max(reached, int(d.group(1)))
            m = None
            for l in reversed(lines):
                if l.startswith("info depth"):
                    m = re.search(r"score (cp|mate) (-?\d+)", l)
                    if m:
                        break
            out.write(json.dumps({
                "i": i, "fen": fen, "depth_requested": depth, "depth_reached": reached,
                "score_kind": m.group(1) if m else None,
                "score_value": int(m.group(2)) if m else None,
                "bestmove": best, "lines": lines}) + "\n")
            out.flush()
            if i % 25 == 0:
                print(f"  {i}/{len(fens)}", flush=True)
    if all_errors:
        print(f"CHECK FAILED: {len(all_errors)} option/parse errors, e.g. {all_errors[:3]}")
        return 3
    print("done, no option or parse errors")
    return 0


if __name__ == "__main__":
    sys.exit(main())
