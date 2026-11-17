#!/usr/bin/env python3
"""Verify mate labels with the two-halves method from findings S4.

A UCI `mate N` claim means the SHORTEST forced mate is exactly N MOVES.
(UCI mate scores are in moves, not plies: a win mates on ply 2N-1, a loss is
delivered on ply 2N. That is also why the S4 length filter wants 2N-1 / 2N.)

Checking "exactly N" splits into two independent halves:

  WIN  (N > 0):  (A) the engine's own move forces mate within 2N-1 plies  [pinned]
                 (B) NO legal move forces mate within 2N-3 plies        [full, cheaper]
  LOSS (N < 0):  (A) the side to move cannot avoid mate within 2N plies [full]
                 (B) it is not already forced within 2N-2 plies        [full, cheaper]

Half (A) is cheap only when it can be PINNED to the engine's move, which is
possible for a win and impossible for a loss: for a loss the engine's bestmove
is the DEFENDER's move, and proving the opponent mates requires every defence,
so pinning pins the wrong side. Both halves of a loss are therefore full
searches. This is recorded per row rather than glossed.

THE 2x2 (win case):
  (A) true,  (B) false -> EXACT
  (A) true,  (B) true  -> WRONG_OVERSTATED (a shorter mate exists)
  (A) false, (B) --    -> if an UNPINNED (A) succeeds: the DISTANCE is right but
                          the engine's MOVE does not deliver it (MV_WRONG);
                          if unpinned (A) also fails: WRONG_UNDERSTATED.
Cells are disjoint and exhaustive over {A,B}, so no separate full-distance
search is needed -- which is the S4 affordability result.

Every call is deadline-bounded and runs in a FRESH process, so the S4 state-leak
bug (unwound recursion leaving the board deep, only on the timeout path) cannot
occur here by construction.
"""
import json
import subprocess
import sys
import time

sys.path.insert(0, "/tmp/fw")
import chess

ORACLE = "/tmp/fw/oracle/oracle"

# Deadline policy from the S4 ceiling evidence:
#   |N| <= 3 -> 60 s per half   (S4: 27/27 safe)
#   |N| == 4 -> 180 s per half  (S4: 2/3, one timeout -- the measured ceiling)
#   |N| >= 5 -> 300 s per half  (S4: 0/3; kept deliberately so the unverifiable
#                                count is MEASURED, not assumed away)
DEADLINE = {1: 60_000, 2: 60_000, 3: 60_000, 4: 180_000}
DEFAULT_DEADLINE = 300_000


def deadline_for(n):
    return DEADLINE.get(n, DEFAULT_DEADLINE)


def ask(mode, plies, fen, deadline_ms, extra=None):
    """One oracle query in a fresh process. Returns (reply, wall_seconds)."""
    parts = ["Q", mode, str(plies), str(deadline_ms)]
    if extra:
        parts.append(extra)
    parts.append(fen)
    req = " ".join(parts) + "\n"
    t0 = time.time()
    out = subprocess.run([ORACLE], input=req, capture_output=True, text=True, timeout=3600)
    elapsed = time.time() - t0
    lines = [l for l in out.stdout.strip().split("\n") if l.startswith("{")]
    if len(lines) < 2:
        return {"error": "no_reply"}, elapsed
    try:
        return json.loads(lines[-1]), elapsed
    except json.JSONDecodeError:
        return {"error": "bad_json"}, elapsed


def classify_win(row, verdict):
    n = verdict["abs_n"]
    fen = row["fen"]
    dl = verdict["deadline_ms"]

    # Half (A) pinned to the engine's own move.
    a, a_secs = ask("pinwin", 2 * n - 1, fen, dl, row["bestmove"])
    verdict.update(half_A_mode="pinwin", half_A_plies=2 * n - 1,
                   half_A_value=a.get("value"), half_A_status=a.get("status", a.get("error")),
                   half_A_nodes=a.get("nodes"), half_A_seconds=round(a_secs, 2))

    a_ok = a.get("status") == "ok"
    if not a_ok:
        verdict["class"] = "UNVERIFIABLE"
        verdict["reason"] = f"half A pinned {verdict['half_A_status']}"
        return verdict

    if a.get("value") is False:
        # The engine's move does not deliver. Two very different causes:
        # the move is wrong, or the distance is unreachable. An unpinned (A)
        # separates them, and S4 insists these are different findings.
        un, un_secs = ask("win", 2 * n - 1, fen, dl)
        verdict.update(unpinned_A_value=un.get("value"),
                       unpinned_A_status=un.get("status", un.get("error")),
                       unpinned_A_nodes=un.get("nodes"),
                       unpinned_A_seconds=round(un_secs, 2))
        if un.get("status") != "ok":
            verdict["class"] = "UNVERIFIABLE"
            verdict["reason"] = f"pinned A false; unpinned A {verdict['unpinned_A_status']}"
        elif un.get("value") is True:
            verdict["class"] = "MV_WRONG"
            verdict["reason"] = ("the engine's move does not deliver mate within the "
                                 "claimed budget, but some other move does: distance "
                                 "plausible, move wrong")
        else:
            verdict["class"] = "WRONG_UNDERSTATED"
            verdict["reason"] = ("no legal move reaches mate within the claimed budget: "
                                 "the claimed distance cannot be reached at all")
        return verdict

    # (A) holds. Half (B): is a SHORTER mate also available?
    b_plies = 2 * n - 3
    if b_plies <= 0:
        verdict.update(half_B_mode="win", half_B_plies=b_plies, half_B_value=False,
                       half_B_status="ok", half_B_nodes=0, half_B_seconds=0.0)
        b_ok, b_val = True, False
    else:
        b, b_secs = ask("win", b_plies, fen, dl)
        verdict.update(half_B_mode="win", half_B_plies=b_plies,
                       half_B_value=b.get("value"), half_B_status=b.get("status", b.get("error")),
                       half_B_nodes=b.get("nodes"), half_B_seconds=round(b_secs, 2))
        b_ok = b.get("status") == "ok"
        b_val = b.get("value")

    if not b_ok:
        verdict["class"] = "UNVERIFIABLE"
        verdict["reason"] = f"half B {verdict['half_B_status']}"
    elif b_val is True:
        verdict["class"] = "WRONG_OVERSTATED"
        verdict["reason"] = ("a forced mate also exists at the shorter budget; the true "
                             "distance is below the claim")
    else:
        verdict["class"] = "EXACT"
        verdict["reason"] = "mate within 2N-1 and none within 2N-3"
    return verdict


def classify_loss(row, verdict):
    n = verdict["abs_n"]
    fen = row["fen"]
    dl = verdict["deadline_ms"]

    # (A) the side to move cannot avoid mate within 2N plies.
    a, a_secs = ask("loss", 2 * n, fen, dl)
    verdict.update(half_A_mode="loss", half_A_plies=2 * n,
                   half_A_value=a.get("value"), half_A_status=a.get("status", a.get("error")),
                   half_A_nodes=a.get("nodes"), half_A_seconds=round(a_secs, 2),
                   pinned=False, pin_note="loss labels cannot pin: the engine's move is the defender's")
    if a.get("status") != "ok":
        verdict["class"] = "UNVERIFIABLE"
        verdict["reason"] = f"half A loss {verdict['half_A_status']}"
        return verdict
    if a.get("value") is False:
        verdict["class"] = "WRONG_UNDERSTATED"
        verdict["reason"] = "mate is not even forced within the claimed budget"
        return verdict

    b_plies = 2 * n - 2
    if b_plies <= 0:
        verdict.update(half_B_mode="loss", half_B_plies=b_plies, half_B_value=False,
                       half_B_status="ok", half_B_nodes=0, half_B_seconds=0.0)
        b_ok, b_val = True, False
    else:
        b, b_secs = ask("loss", b_plies, fen, dl)
        verdict.update(half_B_mode="loss", half_B_plies=b_plies,
                       half_B_value=b.get("value"), half_B_status=b.get("status", b.get("error")),
                       half_B_nodes=b.get("nodes"), half_B_seconds=round(b_secs, 2))
        b_ok = b.get("status") == "ok"
        b_val = b.get("value")

    if not b_ok:
        verdict["class"] = "UNVERIFIABLE"
        verdict["reason"] = f"half B {verdict['half_B_status']}"
    elif b_val is True:
        verdict["class"] = "WRONG_OVERSTATED"
        verdict["reason"] = "mate is already forced at the shorter budget"
    else:
        verdict["class"] = "EXACT"
        verdict["reason"] = "mate forced within 2N and not within 2N-2"
    return verdict


def verify_row(row):
    n = abs(row["score_value"])
    verdict = {
        "id": row["id"], "fen": row["fen"], "claimed_N": row["score_value"], "abs_N": n, "abs_n": n,
        # S4 length filter, evaluated on the label as emitted.
        "pv_len": row["pv_len"], "pv_len_wanted": row["pv_len_wanted"],
        "pv_len_filter_pass": row["pv_len_filter_pass"],
        "pv_len_would_reject": not row["pv_len_filter_pass"],
        "deadline_ms": deadline_for(n),
        "engine_sha256": row["engine_sha256"], "base_commit": row["base_commit"],
        "options": row["options"], "depth": row["depth"],
        # The oracle row: state the build and settings on every row.
        "oracle_version": "matelabels-oracle v1",
    }
    if row["score_value"] < 0:
        return classify_loss(row, verdict)
    return classify_win(row, verdict)


def main():
    in_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/fw/harvest.jsonl"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "/tmp/fw/verdicts.jsonl"
    rows = [json.loads(l) for l in open(in_path)]
    # Smallest claims first: the cheap cells fill early, so a deadline cut still
    # leaves a usable partial result.
    rows.sort(key=lambda r: (abs(r["score_value"]), r["id"]))

    done = set()
    try:
        for line in open(out_path):
            done.add(json.loads(line)["id"])
    except FileNotFoundError:
        pass

    t0 = time.time()
    with open(out_path, "a") as out:
        for i, row in enumerate(rows):
            if row["id"] in done:
                continue
            board = chess.Board(row["fen"])
            if not board.is_valid():
                out.write(json.dumps({"id": row["id"], "class": "UNVERIFIABLE",
                                      "reason": "invalid fen by python-chess"}) + "\n")
                out.flush()
                continue
            v = verify_row(row)
            v["python_chess_valid"] = True
            out.write(json.dumps(v) + "\n")
            out.flush()
            print(f"[{i+1}/{len(rows)}] {row['id']} N={v['claimed_N']:>3} "
                  f"{v['class']:17} A={v['half_A_value']}({v['half_A_seconds']}s) "
                  f"B={v.get('half_B_value')}({v.get('half_B_seconds')}s) "
                  f"wall={time.time()-t0:.0f}s", flush=True)
    print("\ndone")


if __name__ == "__main__":
    main()
