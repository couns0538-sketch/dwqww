#!/usr/bin/env python3
"""harness_checks.py EXE — the two defects a HARNESS or GUI can trip over, as self-checks.

These are not engine-strength checks. They answer "is my harness sane?", which is the failure mode
that bit three seats in this swarm before anyone noticed.

  CHECK 1  FABRICATED BESTMOVE
      Send `go depth 12` and an immediate `quit`. If the reply has no `info depth` line and the move
      is the first legal move in the generator order, the engine published a move it never searched.
      A harness that pipes quit (or closes stdin) gets that answer and will record it as a result.

  CHECK 2  SEARCHMOVES BRANCHES
      `go ... searchmoves <a legal move>` must answer THAT move with real search lines.
      `go ... searchmoves <no legal match>` must answer `0000` with zero-node lines and an
      explanatory `info string`. A user testing a harness sees both sides of the branch.

Each check has a planted control: a fake engine that is deliberately wrong in exactly that way, so
"the engine passed" is only reported when the checker can also fail.

Threads 1 (no Threads option sent). Every read goes to `bestmove` unless the check IS about
quitting mid-search.
"""
import json
import queue
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

import chess

START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def read_all(exe, script, timeout=120.0, close_after=None):
    """Run EXE, write `script`, collect everything until the process exits or timeout.

    `close_after` (seconds) closes stdin that long after the last write, which is how a harness
    that pipelines `quit` behaves; None means the script itself ends the session.
    """
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    q = queue.Queue()
    out = []
    threading.Thread(target=lambda: ([q.put(l.rstrip("\n")) for l in p.stdout], q.put(None)),
                     daemon=True).start()
    try:
        p.stdin.write(script)
        p.stdin.flush()
        if close_after is not None:
            time.sleep(close_after)
            p.stdin.close()
    except (BrokenPipeError, OSError, ValueError):
        pass
    end = time.monotonic() + timeout
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
    return out


def first_legal_move(fen):
    return sorted(m.uci() for m in chess.Board(fen).legal_moves)[0]


def check1_fabricated(exe):
    """`go depth 12` + immediate quit: is the published move a fabrication?"""
    script = (f"uci\nsetoption name OwnBook value false\nposition fen {START_FEN}\nisready\n"
              f"go depth 12\nquit\n")
    out = read_all(exe, script, timeout=60)
    infos = [l for l in out if l.startswith("info depth")]
    bms = [l for l in out if l.startswith("bestmove")]
    bm = bms[-1].split()[1] if bms else None
    nodes = None
    if infos:
        m = re.search(r" nodes (\d+)", infos[-1])
        nodes = int(m.group(1)) if m else None
    fabricated = bool(bms) and not infos
    # generator order: the engine's own perft-1 listing, not python-chess's alphabetical order
    p1 = read_all(exe, f"uci\nsetoption name OwnBook value false\nposition fen {START_FEN}\n"
                       f"isready\ngo perft 1\nisready\nquit\n", timeout=60)
    order = [l.split(":")[0] for l in p1 if re.match(r"^[a-h][1-8][a-h][1-8][qrbn]?: \d+$", l)]
    first = order[0] if order else None
    return {"check": "fabricated_bestmove", "bestmove": bm, "info_depth_lines": len(infos),
            "nodes": nodes, "fabricated": fabricated, "first_legal": first,
            "is_first_legal": (bm == first) if (bm and first) else None,
            "verdict": ("FABRICATED" if fabricated else
                        "ok (the search produced lines before the answer)")}


def search_and_read(exe, go_line, timeout=90.0):
    """Send `go ...`, READ TO `bestmove`, and only then quit.

    A search command must never be followed by more input before its answer: sending `isready` and
    `quit` while the search runs makes the engine stop and publish a fabricated move, which is the
    very defect check 1 looks for. That mistake cost me one run of this harness; the fix is to wait.
    """
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
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
        send("setoption name OwnBook value false")
        send("isready")
        wait(lambda l: l == "readyok", 30)
        send(f"position fen {START_FEN}")
        send("isready")
        wait(lambda l: l == "readyok", 30)
        send(go_line)
        wait(lambda l: l.startswith("bestmove"), timeout)
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


def check2_searchmoves(exe):
    """Both sides of the searchmoves branch: a match must answer that move; no match must answer 0000."""
    legal = search_and_read(exe, "go depth 6 searchmoves e2e4")
    legal_bm = next((l.split()[1] for l in legal if l.startswith("bestmove")), None)
    legal_infos = [l for l in legal if l.startswith("info depth")]
    legal_nodes = None
    if legal_infos:
        m = re.search(r" nodes (\d+)", legal_infos[-1])
        legal_nodes = int(m.group(1)) if m else None

    nomatch = search_and_read(exe, "go depth 6 searchmoves zzzz")
    nomatch_bm = next((l.split()[1] for l in nomatch if l.startswith("bestmove")), None)
    note = next((l for l in nomatch if l.startswith("info string")), None)
    nm_infos = [l for l in nomatch if l.startswith("info depth")]
    nm_nodes = []
    for l in nm_infos:
        m = re.search(r" nodes (\d+)", l)
        if m:
            nm_nodes.append(int(m.group(1)))

    legal_ok = legal_bm == "e2e4" and bool(legal_infos) and (legal_nodes or 0) > 0
    nomatch_ok = nomatch_bm == "0000" and bool(note) and all(n == 0 for n in nm_nodes)
    return {"check": "searchmoves_branches",
            "legal_move": legal_bm, "legal_info_lines": len(legal_infos),
            "legal_nodes": legal_nodes, "legal_ok": legal_ok,
            "no_match_move": nomatch_bm, "no_match_note": note,
            "no_match_nodes": nm_nodes, "no_match_ok": nomatch_ok,
            "verdict": ("ok (both branches correct)" if (legal_ok and nomatch_ok)
                        else "WRONG BRANCH BEHAVIOUR")}


# --------------------------------------------------------------------------------------------
# planted controls: fake engines that are wrong in exactly the way each check looks for
# --------------------------------------------------------------------------------------------
FAKE_FABRICATING = r'''#!/usr/bin/env python3
import sys, time
POS = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
for line in sys.stdin:
    w = line.split()
    if not w: continue
    if w[0] == "uci":
        print("id name FakeFabricating"); print("id author control")
        print("option name OwnBook type check default true")
        print("uciok", flush=True)
    elif w[0] == "isready":
        print("readyok", flush=True)
    elif w[0] == "go":
        if "perft" in w:
            print("a2a3: 1"); print("nodes 20", flush=True)
        else:
            # never prints an info line; answers the generator's first move
            print("bestmove a2a3", flush=True)
    elif w[0] == "quit":
        break
'''

FAKE_BAD_SEARCHMOVES = r'''#!/usr/bin/env python3
import sys
for line in sys.stdin:
    w = line.split()
    if not w: continue
    if w[0] == "uci":
        print("id name FakeBadSearchmoves"); print("id author control")
        print("option name OwnBook type check default true")
        print("uciok", flush=True)
    elif w[0] == "isready":
        print("readyok", flush=True)
    elif w[0] == "go":
        if "perft" in w:
            print("a2a3: 1"); print("nodes 20", flush=True)
        else:
            # BOTH branches wrong: ignores searchmoves and never says 0000
            print("info depth 1 seldepth 1 score cp 20 nodes 20 time 1 pv e2e4", flush=True)
            print("bestmove e2e4", flush=True)
    elif w[0] == "quit":
        break
'''


def main():
    exe = sys.argv[1]
    tmp = Path("/tmp/_seat12_controls")
    tmp.mkdir(exist_ok=True)
    f_fab = tmp / "fake_fabricating.py"
    f_sm = tmp / "fake_bad_searchmoves.py"
    f_fab.write_text(FAKE_FABRICATING)
    f_sm.write_text(FAKE_BAD_SEARCHMOVES)
    for f in (f_fab, f_sm):
        f.chmod(0o755)

    print(f"engine under test: {exe}")
    print(f"Threads 1 (no Threads option sent)\n")

    r1 = check1_fabricated(exe)
    print("=== CHECK 1: fabricated bestmove (go depth 12 + immediate quit)")
    print(f"  bestmove {r1['bestmove']} with {r1['info_depth_lines']} info depth line(s), "
          f"nodes {r1['nodes']}")
    print(f"  first legal move in generator order: {r1['first_legal']}  "
          f"(move equals it: {r1['is_first_legal']})")
    print(f"  verdict: {r1['verdict']}")
    print(f"  NOTE: on this engine FABRICATED is EXPECTED and is a real engine defect, not yours —")
    print(f"        the point is that your harness must never record such an answer as a result.")

    r2 = check2_searchmoves(exe)
    print("\n=== CHECK 2: searchmoves branches")
    print(f"  legal   `searchmoves e2e4` -> bestmove {r2['legal_move']}, "
          f"{r2['legal_info_lines']} info lines, nodes {r2['legal_nodes']}  "
          f"[{'ok' if r2['legal_ok'] else 'WRONG'}]")
    print(f"  no-match `searchmoves zzzz` -> bestmove {r2['no_match_move']}, "
          f"nodes {r2['no_match_nodes']}  [{'ok' if r2['no_match_ok'] else 'WRONG'}]")
    print(f"  note line: {r2['no_match_note']}")
    print(f"  verdict: {r2['verdict']}")

    # ---- the planted controls, through the SAME check functions
    print("\n=== planted controls (the checks must CATCH these)")
    c1 = check1_fabricated(str(f_fab))
    print(f"  fabricating fake: verdict {c1['verdict']}  "
          f"-> {'CAUGHT' if c1['fabricated'] else 'MISSED'}")
    c2 = check2_searchmoves(str(f_sm))
    print(f"  bad-searchmoves fake: verdict {c2['verdict']}  "
          f"-> {'CAUGHT' if not (c2['legal_ok'] and c2['no_match_ok']) else 'MISSED'}")

    both = (c1["fabricated"] and not (c2["legal_ok"] and c2["no_match_ok"]))
    print(f"\ncontrols working: {both}")
    print(json.dumps({"engine": r1["verdict"], "searchmoves": r2["verdict"],
                      "control_fabricating_caught": c1["fabricated"],
                      "control_searchmoves_caught": not (c2["legal_ok"] and c2["no_match_ok"])},
                     indent=1))
    return 0 if both else 1


if __name__ == "__main__":
    sys.exit(main())
