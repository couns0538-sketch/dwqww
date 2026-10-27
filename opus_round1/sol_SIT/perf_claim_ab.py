"""S-IT code-review follow-up: fixed-depth searches of several binaries with IntendedThreefold off/on.

Each run is a fresh engine process at Idle priority on Windows (Threads 1, Hash 16, OwnBook false, ucinewgame).
The search CPU time (user + kernel, GetProcessTimes on Windows, /proc/<pid>/stat on Linux) is read between readyok
and bestmove, so the CPU-time NPS is less sensitive to a loaded machine than wall time. Configurations rotate every
round (ABBA-like). Prints every run and a summary per case: nodes (must be identical across rounds), mean CPU NPS,
and on/off ratios. --same-tree: every configuration of a case must search the same tree (no claim can fire), else
"NODE MISMATCH" and exit status 1.
usage: python -I -B perf_claim_ab.py --exe base=<exe> --exe new=<exe> --rounds 4 [--cases name,name]
       [--options false,true] [--same-tree]
"""
import argparse
import os
import re
import statistics
import subprocess
import sys

CASES = {
    # reviewer's position: the history holds duplicated keys with castling rights that can never recur
    "shuffle_hist": ("rn2k1nr/8/1p1p1p1p/pPpPpPpP/P1P1P1P1/8/8/RN2K1NR w KQkq - 0 1",
                     "b1c3 b8c6 c3b1 c6b8 b1c3 b8c6 c3b1 e8f8 e1f1", 22),
    "shuffle_nohist": ("r4knr/8/1pnp1p1p/pPpPpPpP/P1P1P1P1/8/8/RN3KNR b - - 9 5", "", 22),
    # reviewer's 62-ply knight walk (no claim fires; nodes identical on/off)
    "longwalk_hist": ("rn2k1nr/8/1p1p1p1p/pPpPpPpP/P1P1P1P1/8/8/RN2K1NR w KQkq - 0 1",
                      "b1a3 b8d7 a3b1 d7f8 g1f3 f8h7 b1d2 h7f8 d2f1 f8g6 f1h2 g6f8 f3h4 g8e7 h4f3 e7g6 h2f1 f8h7 "
                      "f1d2 h7f8 f3d4 g6f4 d2f3 f8h7 d4e6 h7f8 f3g1 f4e2 e6d8 e2c3 d8b7 f8g6 g1h3 c3d1 b7d8 d1b2 "
                      "d8b7 g6f4 h3f2 b2d1 f2h3 d1f2 h3g1 f4h3 g1e2 h3f4 b7d8 f4h3 e2c1 h3g1 d8e6 g1h3 e6f8 h3g1 "
                      "c1e2 f2d1 e2c3 d1b2 f8d7 g1h3 e1e2 e8d8", 23),
    # reviewer's (verifier2) 34-ply queen/rook walk: duplicated keys keep black's q right, e8f7 drops it last
    "walk34_castle": ("r3k2r/8/8/8/8/8/8/1K1Q4 w q - 0 1",
                      "d1g4 h8f8 g4h4 f8g8 h4d4 g8f8 d4h4 f8g8 h4f4 g8h8 f4g4 h8f8 g4h3 f8g8 h3h2 g8f8 h2c2 f8h8 "
                      "c2f2 h8g8 f2f4 g8h8 f4f2 h8g8 f2d4 g8f8 d4d3 f8h8 d3b3 h8f8 b3h3 f8g8 h3h6 e8f7", 25),
    # claims fire in these (on/off trees differ; base vs perf-only build must still match node for node)
    "rook_walk41": ("1r4k1/5pp1/7p/8/8/7P/5PP1/3R2K1 w - - 0 30",
                    "d1c1 b8e8 c1a1 e8c8 a1d1 c8b8 d1a1 b8e8 a1b1 e8a8 b1d1 a8c8 d1a1 c8b8 a1c1 b8e8 c1b1 e8a8 "
                    "b1d1 a8c8 d1a1 c8e8 a1c1 e8b8 c1a1 b8c8 a1d1 c8a8 d1e1 a8d8 e1a1 d8b8 a1e1 b8a8 e1c1 a8b8 "
                    "c1d1 b8a8 d1e1 a8d8 e1a1", 44),
    "issue_positive": ("8/7k/8/8/8/8/8/K1R5 w - - 0 1", "a1a2 h7h8 a2a1 h8h7 a1a2 h7h8", 26),
    "review_qr": ("7k/1r6/8/8/8/8/8/K2Q4 w - - 0 1", "a1a2 b7b8 a2a1 b8b7 a1a2 b7b8", 28),
    "middlegame_dup": ("r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
                       "h1g1 f8e8 g1h1 e8f8 h1g1 f8e8 g1h1", 18),
}


def cpu_seconds(process):
    if os.name != "nt":
        # /proc/<pid>/stat: fields after "pid (comm)" start at field 3; utime and stime are fields 14 and 15.
        with open("/proc/%d/stat" % process.pid, encoding="ascii") as stat:
            fields = stat.read().rsplit(")", 1)[1].split()
        return (int(fields[11]) + int(fields[12])) / os.sysconf("SC_CLK_TCK")
    import ctypes
    from ctypes import wintypes

    class FILETIME(ctypes.Structure):
        _fields_ = [("lo", wintypes.DWORD), ("hi", wintypes.DWORD)]

    times = [FILETIME() for _ in range(4)]
    ok = ctypes.windll.kernel32.GetProcessTimes(int(process._handle), *[ctypes.byref(t) for t in times])
    if not ok:
        raise OSError("GetProcessTimes failed")
    seconds = lambda t: ((t.hi << 32) | t.lo) / 1e7
    return seconds(times[2]) + seconds(times[3])


def run(exe, option, fen, moves, depth):
    flags = getattr(subprocess, "IDLE_PRIORITY_CLASS", 0)
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1,
                         creationflags=flags)

    def send(text):
        p.stdin.write(text + "\n")
        p.stdin.flush()

    for command in ("uci", "setoption name Threads value 1", "setoption name Hash value 16",
                    "setoption name OwnBook value false", "setoption name IntendedThreefold value " + option,
                    "ucinewgame", "position fen " + fen + (" moves " + moves if moves else ""), "isready"):
        send(command)
    for line in p.stdout:
        if line.startswith("readyok"):
            break
    cpu0 = cpu_seconds(p)
    send("go depth %d" % depth)
    last = None
    for line in p.stdout:
        if line.startswith("info depth %d " % depth):
            last = line.strip()
        if line.startswith("bestmove"):
            best = line.split()[1]
            break
    cpu1 = cpu_seconds(p)
    send("quit")
    p.wait(timeout=60)
    m = re.search(r"score (cp|mate) (-?\d+) nodes (\d+) nps \d+ hashfull \d+ time (\d+)", last or "")
    if not m:
        raise RuntimeError("no final info line: %r" % last)
    return {"score": m.group(1) + " " + m.group(2), "nodes": int(m.group(3)), "wall_ms": int(m.group(4)),
            "cpu": cpu1 - cpu0, "best": best}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", action="append", required=True, help="label=path")
    ap.add_argument("--rounds", type=int, default=4)
    ap.add_argument("--cases", default=",".join(CASES))
    ap.add_argument("--options", default="false,true")
    ap.add_argument("--same-tree", action="store_true")
    a = ap.parse_args()
    exes = [tuple(item.split("=", 1)) for item in a.exe]
    options = a.options.split(",")
    configs = [(label, path, option) for label, path in exes for option in options]
    results = {}
    for case in a.cases.split(","):
        fen, moves, depth = CASES[case]
        print("# case %s depth %d: position fen %s%s" % (case, depth, fen, " moves " + moves if moves else ""),
              flush=True)
        for r in range(a.rounds):
            order = configs if r % 2 == 0 else list(reversed(configs))
            order = order[r // 2 % len(order):] + order[:r // 2 % len(order)]
            for label, path, option in order:
                res = run(path, option, fen, moves, depth)
                results.setdefault((case, label, option), []).append(res)
                print("%-15s %-6s IT=%-5s r%d score %-9s nodes %9d cpu %6.3fs cpu_nps %9.0f wall_ms %6d best %s"
                      % (case, label, option, r, res["score"], res["nodes"], res["cpu"],
                         res["nodes"] / max(res["cpu"], 1e-9), res["wall_ms"], res["best"]), flush=True)
    print("\n# summary: mean CPU-time NPS (k), nodes; ratio = on/off CPU NPS of the same binary")
    mismatch = False
    for case in a.cases.split(","):
        for label, _ in exes:
            row = []
            nps_by_option = {}
            for option in options:
                runs = results[(case, label, option)]
                nodes = {x["nodes"] for x in runs}
                nps = [x["nodes"] / max(x["cpu"], 1e-9) for x in runs]
                nps_by_option[option] = statistics.mean(nps)
                row.append("IT=%s nodes %s cpu_nps %.0fk (min %.0fk max %.0fk) score %s" % (
                    option, "/".join(str(n) for n in sorted(nodes)) + ("" if len(nodes) == 1 else " UNSTABLE"),
                    statistics.mean(nps) / 1000, min(nps) / 1000, max(nps) / 1000,
                    "/".join(sorted({x["score"] for x in runs}))))
            ratio = (nps_by_option["true"] / nps_by_option["false"]) if {"true", "false"} <= set(nps_by_option) else 0
            print("%-15s %-6s %s | on/off %.3f" % (case, label, " | ".join(row), ratio))
        for option in options:
            node_sets = {label: {x["nodes"] for x in results[(case, label, option)]} for label, _ in exes}
            same = len({frozenset(v) for v in node_sets.values()}) == 1
            print("%-15s nodes IT=%s identical across binaries: %s" % (case, option, "YES" if same else "NO " + str(node_sets)))
        all_nodes = {x["nodes"] for (c, _, _), runs in results.items() if c == case for x in runs}
        if a.same_tree and len(all_nodes) != 1:
            print("NODE MISMATCH %s: %s" % (case, sorted(all_nodes)))
            mismatch = True
    if a.same_tree and mismatch:
        sys.exit(1)


if __name__ == "__main__":
    main()
