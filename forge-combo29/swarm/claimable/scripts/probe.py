#!/usr/bin/env python3
"""probe.py — correctness probe set, one fresh process per measurement.

Two documented traps are closed here by construction:
  * §7-3 warm process state: every search runs in its OWN process after `ucinewgame`;
    each search is run twice and both must agree, or the row is marked non-deterministic.
  * §7-3a (63-F8) hand-written fixtures: every fixture comes from fixtures.json, which
    build_fixtures.py asserts with python-chess. Nothing is typed twice.
  * §7-6 / refused FEN: a perft-1 identity gate runs in a separate process and must equal
    python-chess's legal-move count before the search row is trusted at all.

Usage: probe.py FIXTURES.json EXE LABEL [EXE LABEL ...]
"""
import json
import queue
import re
import subprocess
import sys
import threading
import time

ENV = {"PATH": "/usr/bin:/bin", "ASAN_OPTIONS": "detect_leaks=0"}


def _drive(exe, script, stop_prefix, timeout):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1, env=ENV)
    q = queue.Queue()

    def pump():
        try:
            for line in p.stdout:
                q.put(line.rstrip())
        finally:
            q.put(None)

    threading.Thread(target=pump, daemon=True).start()
    out = []
    try:
        p.stdin.write(script)
        p.stdin.flush()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                line = q.get(timeout=0.3)
            except queue.Empty:
                continue
            if line is None:
                break
            out.append(line)
            if line.startswith(stop_prefix):
                break
        try:
            p.stdin.write("quit\n")
            p.stdin.flush()
            p.stdin.close()
            p.wait(timeout=20)
        except (BrokenPipeError, OSError, subprocess.TimeoutExpired):
            p.kill()
    except (BrokenPipeError, OSError):
        p.kill()
    return out


def identity(exe, fen, moves):
    """perft 1 in a dedicated process; returns the node count the engine reports."""
    pos = f"position fen {fen}" + ((" moves " + " ".join(moves)) if moves else "")
    out = _drive(exe, f"uci\nsetoption name OwnBook value false\n{pos}\nisready\ngo perft 1\n", "nodes ", 120)
    for line in reversed(out):
        m = re.match(r"^nodes (\d+)$", line)
        if m:
            return int(m.group(1))
    return None


def search(exe, fen, moves, depth=12):
    """One search, fresh process, ucinewgame first. Returns the parsed last info line."""
    pos = f"position fen {fen}" + ((" moves " + " ".join(moves)) if moves else "")
    script = ("uci\nsetoption name OwnBook value false\nucinewgame\nisready\n"
              f"{pos}\nisready\ngo depth {depth}\n")
    out = _drive(exe, script, "bestmove", 300)
    infos = [x for x in out if x.startswith("info depth")]
    bms = [x for x in out if x.startswith("bestmove")]
    rec = {"bestmove": bms[-1].split()[1] if bms else None,
           "info_lines": len(infos),
           "max_depth": max([int(x.split()[2]) for x in infos], default=0),
           "score": None, "nodes": None, "pv_empty": None,
           "last_info": infos[-1] if infos else None}
    if infos:
        m = re.search(r"score (cp|mate) (-?\d+)", infos[-1])
        rec["score"] = [m.group(1), int(m.group(2))] if m else None
        n = re.search(r" nodes (\d+)", infos[-1])
        rec["nodes"] = int(n.group(1)) if n else None
        rest = infos[-1].split(" pv", 1)
        rec["pv_empty"] = len(rest) < 2 or rest[1].strip() == ""
    return rec


def judge(fx, rec):
    if rec["bestmove"] is None:
        return False, "no bestmove"
    claim = fx["claim"]
    sc, nodes = rec["score"], rec["nodes"] or 0
    is_mate = sc is not None and sc[0] == "mate"
    is_zero = sc is not None and sc[0] == "cp" and sc[1] == 0
    if claim in ("cp0_fifty", "insuff", "cp0_no_reset"):
        return is_zero, "cp 0" if is_zero else f"got {sc}"
    if claim == "mate":
        # A mate in one exists, so a mate SCORE is the only correct answer at this depth.
        # Accepting a large positive cp here would pass a build that lost the mate, which is
        # precisely the regression this fixture exists to catch.
        return is_mate, "mate" if is_mate else f"got {sc} (a mate in 1 exists)"
    if claim == "searched":
        return nodes > 0, "searched" if nodes > 0 else "adjudicated 0 nodes"
    if claim == "threefold_mate":
        ok = is_mate and nodes > 0
        return ok, "mate by search" if ok else f"got {sc} nodes {nodes}"
    return True, "control"


def main():
    fixtures = json.load(open(sys.argv[1]))
    pairs = [(sys.argv[i], sys.argv[i + 1]) for i in range(2, len(sys.argv), 2)]
    report = {}
    for exe, label in pairs:
        rows = {}
        for fx in fixtures:
            name = fx["name"]
            p1 = identity(exe, fx["fen"], fx["moves"])
            r1 = search(exe, fx["fen"], fx["moves"])
            r2 = search(exe, fx["fen"], fx["moves"])
            determ = (r1["bestmove"] == r2["bestmove"] and r1["score"] == r2["score"]
                      and r1["nodes"] == r2["nodes"])
            ok, why = judge(fx, r1)
            if p1 != fx["legal"]:
                ok, why = False, f"POSITION NOT CONFIRMED perft1={p1} want {fx['legal']}"
            if not determ:
                ok, why = False, f"NON-DETERMINISTIC: {r1['bestmove']}/{r1['score']}/{r1['nodes']} vs {r2['bestmove']}/{r2['score']}/{r2['nodes']}"
            r1.update({"ok": ok, "why": why, "claim": fx["claim"], "mates": fx["mates"],
                       "perft1": p1, "want_perft1": fx["legal"], "deterministic": determ,
                       "run2": {"bestmove": r2["bestmove"], "score": r2["score"], "nodes": r2["nodes"]}})
            rows[name] = r1
        report[label] = rows
    json.dump(report, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
