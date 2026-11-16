#!/usr/bin/env python3
"""selfcheck.py FORGE_EXE [--runs N] — one command: are MY Hash/MultiPV settings safe on THIS machine?

Why this exists: the Hash x MultiPV timings measured by seat 12 were taken on a 4-core cloud box.
The SHAPE of the effect (cost linear in Hash and in MultiPV-1) is a property of the code and
transfers anywhere; the absolute milliseconds are a property of the machine and do not. This script
lets the owner re-measure the four recommended settings on his own PC in about a minute.

It needs nothing but Python 3 and the engine binary. No python-chess, no pip.

Usage
    python selfcheck.py C:\\path\\to\\forge.exe
    python selfcheck.py /path/to/forge --runs 5 --threads 1

It runs, for each setting: a FRESH engine process, sends uci -> setoption Hash -> setoption MultiPV
-> setoption OwnBook false -> position -> isready -> `go depth 6`, and times from `go` to
`bestmove` with a monotonic clock. It reads every line up to `bestmove` before quitting (never
pipelines `quit`: an engine that is killed mid-search answers a fabricated first legal move with 0
nodes, which would time suspiciously well and mean nothing).

Output: median / min / max per setting, and a PASS / WATCH / FAIL verdict against thresholds that
are 4x the cloud-box numbers, because a machine 4x slower than that box is still playing fine.
"""
import queue
import re
import statistics
import subprocess
import sys
import threading
import time

FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
# A SECOND position for the fabrication check, because the two orders agree on startpos and
# disagree here (engine order[0] = a2a3, alphabetical = a1b1). A check that passes on startpos
# alone would also pass on a checker that uses the wrong move order.
FEN_KIWI = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"

# (label, Hash MB, MultiPV). The verdict is a RATIO against the cloud number, one rule for every
# cell, so no cell can "pass" merely because its budget is large:
#   PASS <= 4x, WATCH <= 10x, FAIL > 10x.
SETTINGS = [
    ("MultiPV 2, Hash  16", 16, 2),
    ("MultiPV 2, Hash  64", 64, 2),
    ("MultiPV 4, Hash  64", 64, 4),
    ("MultiPV 2, Hash 256", 256, 2),
]
PASS_RATIO, WATCH_RATIO = 4.0, 10.0
# An ABSOLUTE floor beside the ratio: a ratio alone lets a huge budget excuse a slow search
# (901 ms "passed" at Hash 256 because its 4x line is 1000 ms). For interactive analysis nothing
# here should take a second at depth 6, whatever the ratio says.
SLOW_MS = 500.0
# The coordinator's own reference point, named so the reader can check it directly:
#   "MultiPV 2 at Hash 64 taking more than 200 ms" = a machine ~4x this cloud box.
CLOUD = {"MultiPV 2, Hash  16": 17, "MultiPV 2, Hash  64": 52,
         "MultiPV 4, Hash  64": 82, "MultiPV 2, Hash 256": 250}


def one_run(exe, hash_mb, multipv, threads, go="go depth 6", bound=120.0):
    cmd = exe if isinstance(exe, list) else [exe]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    q = queue.Queue()
    lines = []
    threading.Thread(target=lambda: ([q.put(l.rstrip("\n")) for l in p.stdout], q.put(None)),
                     daemon=True).start()

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def wait_for(pred, limit):
        end = time.monotonic() + limit
        while time.monotonic() < end:
            try:
                ln = q.get(timeout=0.2)
            except queue.Empty:
                if p.poll() is not None:
                    return None
                continue
            if ln is None:
                return None
            lines.append(ln)
            if pred(ln):
                return ln
        return "TIMEOUT"

    send("uci")
    wait_for(lambda l: l == "uciok", 30)
    for name, value in (("Hash", hash_mb), ("MultiPV", multipv),
                        ("Threads", threads), ("OwnBook", "false")):
        send(f"setoption name {name} value {value}")
        send("isready")
        wait_for(lambda l: l == "readyok", 30)
    send(f"position fen {FEN}")
    send("isready")
    wait_for(lambda l: l == "readyok", 30)

    t0 = time.monotonic()
    send(go)
    bm = wait_for(lambda l: l.startswith("bestmove"), bound)
    wall = time.monotonic() - t0
    send("quit")
    try:
        p.stdin.close()
    except (OSError, ValueError):
        pass
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()

    answered = isinstance(bm, str) and bm.startswith("bestmove")
    infos = sum(1 for l in lines if l.startswith("info depth"))
    reported = None
    for l in lines:
        if l.startswith("info depth"):
            m = re.search(r" nodes (\d+)", l)
            if m:
                reported = int(m.group(1))
    # A run with no info line is not a fast run, it is a run that never searched.
    return {"ms": wall * 1000, "answered": answered, "info_lines": infos,
            "reported": reported, "bestmove": bm.split()[1] if answered else None}



# ---------------------------------------------------------------------------------------------
# THE ANCHOR'S REFERENCE MEASUREMENT, and what it does and does not tell you.
#
# Measured on the reference box (4 cores, go nodes 1000000 -> 920,173 reported nodes):
#     median 604 ms per million reported nodes over 10 runs, range 591..633 (stdev 13, spread 7%)
#
# CORE COUNT WAS MEASURED AND DOES NOT MATTER for this anchor, because a Threads 1 search uses one
# core: pinning the process to ONE core gave 601 ms/M against 594 unpinned (within run-to-run noise),
# and running four engines at once on the four cores gave 553 ms/M against 543 idle (1.0x).
# So a 2-core, 4-core or 8-core machine of the SAME generation should land in the same band.
#
# What DOES move it: CPU generation, clock and cache. I have no second machine to measure, so I do
# NOT claim a number for a different generation. The band below is the honest envelope:
# run-to-run noise plus a modest allowance for a slower same-class CPU.
# TEMPORAL DRIFT, measured on this box: five blocks of four runs, ~20 s apart, gave block medians
# of 653 / 625 / 636 / 608 / 623 ms/M — a 15% spread on an IDLE machine (load 0.51). An earlier
# session on the same box measured 591-633. So the same hardware wanders over roughly 590-700 ms/M
# depending on the minute, and a narrow band around one session's number would flag this very box
# as broken. The band below is therefore the union of what one machine was seen to do.
CLOUD_MS_PER_M_NODES = 630.0      # reference value the ratio is taken against
REFERENCE_RANGE = (540, 820)      # "same class of machine", widened to contain the measured drift
# ---------------------------------------------------------------------------------------------
ANCHOR_NODES = 1000000


def machine_speed(exe, threads, runs=3):
    """Absolute machine-speed anchor: a fixed NODE count, so the work is identical everywhere.

    This is independent of Hash and MultiPV, which is why it is a better absolute check than any
    depth-6 wall time: a depth search's work varies with pruning, a node count does not.
    """
    ms = []
    reported = None
    for _ in range(runs):
        r = one_run(exe, 16, 1, threads, go=f"go nodes {ANCHOR_NODES}", bound=300)
        if not r["answered"] or r["info_lines"] == 0 or not r.get("reported"):
            continue
        ms.append(r["ms"])
        reported = r["reported"]
    if not ms:
        return None
    med = statistics.median(ms)
    # use the REPORTED node count: `go nodes N` stops short of N (measured 92% at N=1e6),
    # so dividing by the request would understate the machine by 8%.
    per_m = med / (reported / 1e6)
    return {"median_ms": med, "reported": reported, "ms_per_m": per_m,
            "ratio": per_m / CLOUD_MS_PER_M_NODES, "runs": len(ms)}




# ---------------------------------------------------------------------------------------------
# HARNESS CHECKS: the two defects a harness or GUI can trip over. These are about whether a
# MEASUREMENT is trustworthy, not about engine strength.
#
#   1. fabricated bestmove: `go` then an immediate `quit` publishes a move the search never made.
#      A harness that pipes quit (or closes stdin) records that as a result.
#   2. searchmoves branches: a legal restriction must answer that move with real lines; a
#      restriction matching nothing must answer 0000 with zero-node lines.
# ---------------------------------------------------------------------------------------------

FIRST_LEGAL_CACHE = {}


def first_legal_move(exe, threads, fen=None):
    """The generator's first legal move: perft 1's first listed move.

    perft prints `nodes N` as its last line, so the session must wait for THAT, not for a
    `bestmove` (perft never sends one). The order is the ENGINE's, never python-chess's sorted
    order: those differ on kiwipete (a2a3 vs a1b1) and a checker using the sorted order would
    clear a real fabrication there.
    """
    fen = fen or FEN
    key = (exe if isinstance(exe, str) else tuple(exe), fen)
    if key in FIRST_LEGAL_CACHE:
        return FIRST_LEGAL_CACHE[key]
    cmd = exe if isinstance(exe, list) else [exe]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    q = queue.Queue()
    out = []
    threading.Thread(target=lambda: ([q.put(l.rstrip("\n")) for l in p.stdout], q.put(None)),
                     daemon=True).start()

    def wait(pred, limit):
        end = time.monotonic() + limit
        while time.monotonic() < end:
            try:
                ln = q.get(timeout=0.2)
            except queue.Empty:
                if p.poll() is not None:
                    return None
                continue
            if ln is None:
                return None
            out.append(ln)
            if pred(ln):
                return ln
        return None

    try:
        p.stdin.write(f"uci\nsetoption name OwnBook value false\nposition fen {fen}\n"
                      f"isready\ngo perft 1\n")
        p.stdin.flush()
        wait(lambda l: l == "readyok", 30)
        wait(lambda l: l.startswith("nodes "), 120)   # perft's final line
        p.stdin.write("quit\n")
        p.stdin.flush()
        p.stdin.close()
    except (BrokenPipeError, OSError, ValueError):
        pass
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
    moves = [l.split(":")[0] for l in out
             if re.match(r"^[a-h][1-8][a-h][1-8][qrbn]?: \d+$", l)]
    FIRST_LEGAL_CACHE[key] = moves[0] if moves else None
    return FIRST_LEGAL_CACHE[key]


def _session(exe, threads, commands, read_to_bestmove=True, bound=180.0):
    """Open an engine, set the standard options, send `commands`, return every output line.

    If read_to_bestmove, each command starting with `go` is followed by a wait for its `bestmove`
    before the next command: sending anything during a search is exactly the defect under test.
    """
    cmd = exe if isinstance(exe, list) else [exe]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    q = queue.Queue()
    out = []
    threading.Thread(target=lambda: ([q.put(l.rstrip("\n")) for l in p.stdout], q.put(None)),
                     daemon=True).start()

    def send(t):
        p.stdin.write(t + "\n")
        p.stdin.flush()

    def wait(pred, limit):
        end = time.monotonic() + limit
        while time.monotonic() < end:
            try:
                ln = q.get(timeout=0.2)
            except queue.Empty:
                if p.poll() is not None:
                    return None
                continue
            if ln is None:
                return None
            out.append(ln)
            if pred(ln):
                return ln
        return None

    try:
        send("uci")
        wait(lambda l: l == "uciok", 30)
        for name, value in (("Hash", 16), ("MultiPV", 1), ("Threads", threads),
                            ("OwnBook", "false")):
            send(f"setoption name {name} value {value}")
            send("isready")
            wait(lambda l: l == "readyok", 30)
        send(f"position fen {FEN}")
        send("isready")
        wait(lambda l: l == "readyok", 30)
        for c in commands:
            send(c)
            if read_to_bestmove and c.startswith("go") and "perft" not in c:
                wait(lambda l: l.startswith("bestmove"), bound)
        send("quit")
    except (BrokenPipeError, OSError, ValueError):
        pass
    try:
        p.stdin.close()
    except (OSError, ValueError):
        pass
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
    return out


def check_fabricated(exe, threads, fen=None):
    """`go depth 12` and an immediate quit, in ONE write, as a pipelining harness would do it.

    `fen` defaults to startpos. It is a parameter because the check is position-dependent in one
    subtle way: the fabricated move is `root_candidates.front()`, and the comparison against the
    generator order (not python-chess's alphabetical order) only DISTINGUISHES the two orders on
    some positions. See the two-position run in the output.
    """
    fen = fen or FEN
    cmd = exe if isinstance(exe, list) else [exe]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    q = queue.Queue()
    out = []
    threading.Thread(target=lambda: ([q.put(l.rstrip("\n")) for l in p.stdout], q.put(None)),
                     daemon=True).start()
    try:
        p.stdin.write(f"uci\nsetoption name OwnBook value false\nposition fen {fen}\n"
                      f"isready\ngo depth 12\nquit\n")
        p.stdin.flush()
    except (BrokenPipeError, OSError, ValueError):
        pass
    end = time.monotonic() + 60
    while time.monotonic() < end:
        try:
            ln = q.get(timeout=0.2)
        except queue.Empty:
            if p.poll() is not None:
                break
            continue
        if ln is None:
            break
        out.append(ln)
    try:
        p.stdin.close()
    except (OSError, ValueError):
        pass
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
    infos = [l for l in out if l.startswith("info depth")]
    bms = [l for l in out if l.startswith("bestmove")]
    bm = bms[-1].split()[1] if bms else None
    return {"fen": fen, "bestmove": bm, "info_lines": len(infos),
            "fabricated": bool(bms) and not infos,
            "is_first_legal": bm == first_legal_move(exe, threads, fen=fen) if bm else None}


def _write_order_probe():
    """A throwaway engine that is right on startpos and alphabetical (wrong) on kiwipete."""
    import tempfile
    import os
    import stat
    src = '''#!/usr/bin/env python3
import sys
KIWI = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
in_kiwi = False
for line in sys.stdin:
    w = line.split()
    if not w: continue
    if w[0] == "uci":
        print("id name OrderProbe"); print("option name OwnBook type check default true")
        print("uciok", flush=True)
    elif w[0] == "position":
        in_kiwi = KIWI.split()[0] in line
    elif w[0] == "isready":
        print("readyok", flush=True)
    elif w[0] == "go":
        if "perft" in w:
            pairs = [("a2a3",1),("b2b3",1),("g2g3",1)] if in_kiwi else [("a2a3",1),("b2b3",1)]
            for mv,c in pairs: print(f"{mv}: {c}")
            print("nodes 20", flush=True)
        else:
            print(f"bestmove {'a1b1' if in_kiwi else 'a2a3'}", flush=True)
    elif w[0] == "quit":
        break
'''
    try:
        fd, path = tempfile.mkstemp(suffix="_orderprobe.py")
        with os.fdopen(fd, "w") as f:
            f.write(src)
        os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)
        return path
    except OSError:
        return None


def check_searchmoves(exe, threads):
    legal = _session(exe, threads, ["go depth 6 searchmoves e2e4"])
    l_bm = next((l.split()[1] for l in legal if l.startswith("bestmove")), None)
    l_infos = [l for l in legal if l.startswith("info depth")]
    l_nodes = None
    if l_infos:
        m = re.search(r" nodes (\d+)", l_infos[-1])
        l_nodes = int(m.group(1)) if m else None
    nomatch = _session(exe, threads, ["go depth 6 searchmoves zzzz"])
    n_bm = next((l.split()[1] for l in nomatch if l.startswith("bestmove")), None)
    n_note = next((l for l in nomatch if l.startswith("info string")), None)
    n_nodes = [int(m.group(1)) for l in nomatch if l.startswith("info depth")
               for m in [re.search(r" nodes (\d+)", l)] if m]
    return {"legal_move": l_bm, "legal_info": len(l_infos), "legal_nodes": l_nodes,
            "legal_ok": l_bm == "e2e4" and bool(l_infos) and (l_nodes or 0) > 0,
            "no_match_move": n_bm, "no_match_note": n_note, "no_match_nodes": n_nodes,
            "no_match_ok": n_bm == "0000" and bool(n_note) and all(n == 0 for n in n_nodes)}

def main():
    import argparse
    ap = argparse.ArgumentParser(
        description="Are my Hash/MultiPV settings safe on THIS machine?",
        epilog="The engine takes no command-line arguments; this script feeds it on stdin.")
    ap.add_argument("engine", nargs="+",
                    help="path to the engine binary (put it after `--` if the path is odd)")
    ap.add_argument("--runs", type=int, default=5, help="fresh processes per setting (default 5)")
    ap.add_argument("--threads", type=int, default=1, help="Threads value to set (default 1)")
    ns = ap.parse_args()
    exe = ns.engine if len(ns.engine) > 1 else ns.engine[0]
    runs, threads = ns.runs, ns.threads

    print(f"engine : {exe}")
    print(f"runs   : {runs} fresh processes per setting, Threads {threads}, position startpos")
    print(f"search : go depth 6\n")

    # sanity: does this binary respond at all? an exit code of 0 with no output is not a result
    try:
        probe = one_run(exe, 16, 1, threads, go="go depth 1")
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"FATAL: could not run the engine: {exc}")
        return 1
    if not probe["answered"]:
        print("FATAL: the engine did not answer `go depth 1`.")
        print("  It takes no command-line arguments; this script feeds it on stdin.")
        print("  Check the path, and that this is the engine you meant to test.")
        return 1

    print(f"{'setting':22} {'cloud':>7} {'median':>8} {'min':>7} {'max':>7} "
          f"{'ratio':>7} {'runs':>5}  {'verdict'}")
    print("-" * 82)
    worst = 0
    grid_ratios = []
    for label, h, mpv in SETTINGS:
        ms, bad = [], 0
        for _ in range(runs):
            r = one_run(exe, h, mpv, threads)
            if not r["answered"] or r["info_lines"] == 0:
                bad += 1
                continue
            ms.append(r["ms"])
        if bad or not ms:
            print(f"{label:22} {CLOUD[label]:>5}ms {'--':>8} {'--':>7} {'--':>7} {'--':>7} "
                  f"{bad:>5}  FAIL (no completed search)")
            worst = max(worst, 3)
            continue
        med = statistics.median(ms)
        ratio = med / CLOUD[label]
        grid_ratios.append(ratio)
        if ratio <= PASS_RATIO:
            verdict = "PASS (within 4x)"
        elif ratio <= WATCH_RATIO:
            verdict = f"WATCH ({ratio:.1f}x the cloud box, usable)"
        else:
            verdict = f"FAIL ({ratio:.1f}x the cloud box)"
        if med > SLOW_MS and not verdict.startswith("FAIL"):
            # fine relative to this box, but too slow to sit and watch at depth 6
            verdict = f"SLOW ({med:.0f} ms absolute, {ratio:.1f}x)"
        worst = max(worst, 0 if verdict.startswith("PASS") else
                    (1 if (verdict.startswith("WATCH") or verdict.startswith("SLOW")) else 3))
        print(f"{label:22} {CLOUD[label]:>5}ms {med:>6.0f}ms {min(ms):>5.0f}ms "
              f"{max(ms):>5.0f}ms {ratio:>6.1f}x {runs - bad:>5}  {verdict}")

    # ---- the two harness checks
    print()
    print("=== harness checks (is a MEASUREMENT from this engine trustworthy?)")
    print(f"  fabricated-bestmove test: `go depth 12` + immediate `quit`, on TWO positions")
    print(f"    (two, because the engine's move order and alphabetical order AGREE on startpos")
    print(f"     and DISAGREE here, so a check on startpos alone cannot tell a correct checker")
    print(f"     from one that uses the wrong order)")
    fab_any = False
    fab_start = check_fabricated(exe, threads, fen=FEN)
    fab_kiwi = check_fabricated(exe, threads, fen=FEN_KIWI)
    for label, fab in (("startpos", fab_start), ("kiwipete", fab_kiwi)):
        print(f"    {label:9} -> bestmove {fab['bestmove']} with {fab['info_lines']} "
              f"info depth line(s)")
        if fab["fabricated"]:
            fab_any = True
            print(f"              FABRICATED: published {fab['bestmove']} without searching "
                  f"(matches the engine's own per-ply move order: {fab['is_first_legal']})")
        else:
            print(f"              ok: the search produced lines before answering")
    if fab_any:
        print(f"    YOUR harness must read to `bestmove` before quitting and must never record a")
        print(f"    reply with no info lines. This is an engine defect, not a setting: it is present")
        print(f"    on every build measured, on both positions.")
    fab = fab_start if fab_start["fabricated"] else fab_kiwi

    # A self-test of the CHECK ITSELF, not of the engine: a fake whose fabricated move is the
    # ALPHABETICAL first move is indistinguishable from a correct engine on startpos and
    # distinguishable only on kiwipete. If this line ever says "not distinguishable", the
    # two-position check has stopped doing its job.
    fake = _write_order_probe()
    if fake:
        k = check_fabricated(fake, threads, fen=FEN_KIWI)
        st = check_fabricated(fake, threads, fen=FEN)
        distinguishable = (k["is_first_legal"] is False and st["is_first_legal"] is True)
        print(f"    self-test of this check: an alphabetical-first fake is "
              f"{'DISTINGUISHED on kiwipete' if distinguishable else 'NOT distinguished'}"
              f" (startpos agrees: {st['is_first_legal']}, kiwipete: {k['is_first_legal']})")
        if not distinguishable:
            print(f"    WARNING: the second position is not doing its job; the check may be")
            print(f"    position-blind. Do not trust a PASS from it alone.")

    sm = check_searchmoves(exe, threads)
    print(f"  searchmoves branches:")
    print(f"    legal   `searchmoves e2e4` -> {sm['legal_move']}, {sm['legal_info']} info lines, "
          f"nodes {sm['legal_nodes']}   [{'ok' if sm['legal_ok'] else 'WRONG'}]")
    print(f"    no-match `searchmoves zzzz` -> {sm['no_match_move']}, nodes {sm['no_match_nodes']}"
          f"   [{'ok' if sm['no_match_ok'] else 'WRONG'}]")
    if not (sm["legal_ok"] and sm["no_match_ok"]):
        print(f"    WRONG BRANCH BEHAVIOUR: expected e2e4 with real lines and 0000 with zero-node")
        print(f"    lines. A harness testing a restricted root cannot trust either answer.")

    # ---- the ABSOLUTE anchor, independent of Hash and MultiPV
    print()
    print("=== absolute machine-speed anchor (fixed node count, not a ratio of a depth search)")
    speed = machine_speed(exe, threads)
    abs_verdict = None
    if speed is None:
        print("  could not measure: no completed search")
        abs_verdict = "unknown"
    else:
        abs_verdict = ("PASS" if speed["ratio"] <= PASS_RATIO else
                       "WATCH" if speed["ratio"] <= WATCH_RATIO else "FAIL")
        lo, hi = REFERENCE_RANGE
        in_band = lo <= speed["ms_per_m"] <= hi
        print(f"  `go nodes {ANCHOR_NODES:,}` -> {speed['reported']:,} reported nodes in "
              f"{speed['median_ms']:.0f} ms  =  {speed['ms_per_m']:,.0f} ms per million nodes")
        print(f"  reference box (4 cores, measured): {CLOUD_MS_PER_M_NODES:,.0f} ms per million")
        print(f"  same-class band                  : {lo}-{hi} ms per million"
              f"   -> your machine is {speed['ratio']:.2f}x the reference"
              f"   [{'in band' if in_band else 'OUTSIDE the band'}]")
        print(f"  core count does NOT move this anchor (a Threads 1 search uses one core: measured")
        print(f"  601 ms/M pinned to 1 core vs 594 unpinned). CPU generation and clock do.")
        print(f"  the SAME box drifts ~15% between minutes (block medians 653/625/636/608/623), so")
        print(f"  this anchor only means something for GROSS differences (2x or more), not small ones.")
        if speed["ms_per_m"] < lo:
            print(f"  Your CPU is FASTER than the reference box. The band is not a limit above --")
            print(f"  faster is good, and the grid's PASS lines still apply unchanged.")
        elif speed["ms_per_m"] > hi:
            print(f"  Your CPU is SLOWER than the reference class. The band cannot tell you whether")
            print(f"  that is normal for your CPU or something is wrong: I have no second machine to")
            print(f"  measure, so I do not claim a number for your generation. Treat the ANCHOR as")
            print(f"  comparable only to this reference measurement, scale the grid's thresholds by")
            print(f"  {speed['ratio']:.1f}x, and prefer smaller Hash / fewer PV lines.")

    print()
    print("How to read this")
    print("  cloud = median on the 4-core machine these tables came from; ratio = yours / cloud.")
    print("  PASS  = within 4x. A machine 4x slower is still fine to play with.")
    print("  WATCH = 4x to 10x. Usable; prefer one notch smaller Hash if a search feels slow.")
    print("  FAIL  = over 10x, or a run that never completed a search.")
    print(f"  SLOW  = within {WATCH_RATIO:.0f}x but over {SLOW_MS:.0f} ms absolute at depth 6: your")
    print("          machine is fine, this setting is just slow to watch. Drop a notch.")
    print("  Reference point: MultiPV 2 at Hash 64 over 200 ms means a machine about 4x this one.")
    print()
    print("WHICH VERDICT TO TRUST WHEN THEY DISAGREE")
    print("  The anchor measures the machine and nothing else; the grid measures the settings on")
    print("  that machine. If the anchor is PASS and a grid cell FAILs, the setting is the problem,")
    print("  not the machine: use a smaller Hash or fewer PV lines.")
    print("  If the anchor is WATCH/FAIL and the grid cells are PASS, trust the ANCHOR: the grid")
    print("  numbers are relative to this cloud box, and a uniformly slower machine can still")
    print("  finish a depth-6 search quickly while being slow at everything else.")
    print("  If both agree, trust both.")
    if speed is not None:
        grid_worst = max((c for c in grid_ratios), default=1.0)
        if speed["ratio"] < 0.85 and grid_worst > PASS_RATIO:
            print()
            print("  ** INCOHERENT: the anchor calls this machine FASTER than the cloud box while")
            print(f"     the grid finds a cell {grid_worst:.1f}x slower. That combination is not")
            print("     physically plausible for one binary. Most likely the engine misreports its")
            print("     node count (the anchor divides by the REPORTED count), so trust the GRID")
            print("     numbers here and treat the anchor as unmeasured.")
    print()
    print("The SHAPE is what matters and it does not depend on your machine:")
    print("  MultiPV 1 costs the same at every Hash size; the cost is (MultiPV-1) x Hash.")
    print("  So if a cell here is slow, halving Hash or dropping one MultiPV line fixes it.")
    print()
    print("The one setting that is never safe on any machine: Hash 2048 with MultiPV 8")
    print("  (8-9 s for `go depth 6`, depth 0-1 on a 5 s clock, on the cloud box).")
    # A fabricated bestmove is an ENGINE defect, reported loudly but not a machine problem,
    # so it does not fail the run; a wrong searchmoves branch does, because it means a
    # restricted-root measurement is untrustworthy.
    if not (sm["legal_ok"] and sm["no_match_ok"]):
        worst = max(worst, 1)
    anchor_bad = 0 if abs_verdict in ("PASS", None) else (1 if abs_verdict == "WATCH" else 3)
    worst = max(worst, anchor_bad)
    return 0 if worst == 0 else (1 if worst == 1 else 2)


if __name__ == "__main__":
    sys.exit(main())
