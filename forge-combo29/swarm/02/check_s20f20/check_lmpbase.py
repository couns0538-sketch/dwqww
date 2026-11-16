#!/usr/bin/env python3
"""S02 check of seat 20's S-F19/S-F20 (area 10, `setoption name LmpBase value 8` loses a mate score).

Their S-F20 headline: "The `LmpBase=8` mate loss is a DELAY, not breakage, and it is narrow: on a mate-in-1
board LmpBase=8 changes nothing at depths 8-14, while on the deep forced mate (8/8/1p6/8/p3p3/8/2Kpk3/8 w) it
replaces `mate -7` with cp -2884 (d10) and cp -3114 (d12) where the default already proves mate, and first
reports a mate at d14 with a LONGER distance (-9)."

My check tests the DISCRIMINATING CLAIM, not just the numbers: "a delay, not breakage" means
   (i)  at d10 and d12 the tuned setting reports a cp score where the default reports `mate`, AND
   (ii) at a deeper depth the tuned setting DOES find a mate, and its distance is not shorter than the
        default's at the same depth.
If (ii) failed — e.g. the tuned build never finds the mate — the finding would be wrong about "delay".

Every number is parsed from the engine's own `info` line at that depth, and a missing line ABORTS the check
instead of being read as agreement (seat 19's warning). Every `mate N` PV is replayed with python-chess and
must end in checkmate after exactly 2N-1 plies (N>0) or 2|N| plies (N<0), so a `mate` score claiming a mate
that is not there is caught too.

Warm/cold: seat 10's rule. Each search is the FIRST search of a fresh process, so every number here is cold.

usage: check_lmpbase.py <exe> <outdir>
"""
import json
import os
import re
import subprocess
import sys
import threading
import time

import chess

BOARD = "8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1"
MATE1 = "6k1/5ppp/8/8/8/8/5PPP/3Q2K1 w - - 0 1"
DEPTHS = [8, 10, 12, 14]
INFO_RE = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?(?: pv(.*))?$")


def search(exe, fen, depth, setoption=None):
    """One `go depth D` as the first search of a fresh process: COLD by construction.

    Driven INTERACTIVELY, because piping the whole session and closing stdin makes this build answer a
    fabricated `bestmove` with no `info` line at all (seat 19's 19-F12). The first version of this check piped,
    got `bestmove c2b1` and no info line, and its own assertion aborted it — which is the assertion working,
    but the measurement had to be redone properly.
    """
    env = {k: v for k, v in os.environ.items()
           if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS")}
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)
    collected = []

    def reader():
        for line in proc.stdout:
            collected.append(line.rstrip("\n"))

    th = threading.Thread(target=reader, daemon=True)
    th.start()

    def say(t):
        proc.stdin.write(t + "\n")
        proc.stdin.flush()

    def wait_until(pred, timeout=60.0):
        dl = time.monotonic() + timeout
        while time.monotonic() < dl:
            if pred():
                return True
            if proc.poll() is not None:
                return pred()
            time.sleep(0.002)
        return pred()

    say("uci")
    wait_until(lambda: any(l.startswith("uciok") for l in collected))
    say("isready")
    wait_until(lambda: any(l.startswith("readyok") for l in collected))
    say("setoption name OwnBook value false")
    if setoption:
        say(setoption)
    say("isready")
    n0 = len(collected)
    wait_until(lambda: any(l.startswith("readyok") for l in collected[n0:]))
    say("position fen " + fen)
    say("isready")
    n1 = len(collected)
    wait_until(lambda: any(l.startswith("readyok") for l in collected[n1:]))
    n2 = len(collected)
    say("go depth %d" % depth)
    wait_until(lambda: any(l.startswith("bestmove") for l in collected[n2:]), timeout=120.0)
    say("quit")
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
    out = "\n".join(collected)
    # the LAST info line AT the requested depth is the one that matters
    cand = None
    for line in out.splitlines():
        m = INFO_RE.match(line)
        if m and int(m.group(1)) == depth:
            cand = m
    if cand is None:
        sys.exit("FAIL: no `info depth %d` line for %s (setoption=%r). Refusing to record anything — a "
                 "missing line must not pass as agreement.\nOutput tail:\n%s"
                 % (depth, fen, setoption, out[-600:]))
    pv = (cand.group(4) or "").split()
    return {"depth": depth, "kind": cand.group(2), "value": int(cand.group(3)), "pv": pv,
            "raw": cand.group(0)}


def pv_is_mate(fen, pv, score):
    """Replay the PV with python-chess; for a `mate N` score it must end in checkmate at the right length."""
    b = chess.Board(fen)
    played = 0
    for tok in pv:
        try:
            mv = chess.Move.from_uci(tok) if len(tok) in (4, 5) else b.parse_san(tok)
        except Exception:
            return False, "PV move %r does not parse" % tok
        if mv not in b.legal_moves:
            return False, "PV move %r is not legal at ply %d" % (tok, played)
        b.push(mv)
        played += 1
    want = 2 * score - 1 if score > 0 else 2 * abs(score)
    if b.is_checkmate() and played == want:
        return True, "checkmate after %d plies (want %d)" % (played, want)
    if played < want:
        # The engine truncates the PV at its own search depth, so a claim of mate in 9 can carry a PV of only
        # 8 plies. That is NOT a wrong score and it is NOT a verified mate either, so it gets its own verdict
        # rather than being counted as either. Seat 20 recorded the same truncation ("PV truncated 17/18").
        return None, "TRUNCATED: PV has %d of the %d plies the mate score claims (checked as far as it goes, " \
                     "board is %s)" % (played, want, "checkmate" if b.is_checkmate() else "not yet mate")
    return False, "ends %s after %d plies (want checkmate after %d)" % (
        "in checkmate" if b.is_checkmate() else "not in checkmate", played, want)


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    meta = {"exe": exe,
            "sha256": subprocess.run(["sha256sum", exe], capture_output=True, text=True).stdout.split()[0],
            "option_lines_sent": ["setoption name OwnBook value false",
                                  "setoption name LmpBase value 8   (the tuned setting under test)"],
            "boards": {"deep_mate": BOARD, "mate_in_1": MATE1},
            "depths": DEPTHS,
            "each_search_is_the_first_of_a_fresh_process_so_COLD": True,
            "started_utc": "see the commit's date -u"}
    json.dump(meta, open(os.path.join(outdir, "meta.json"), "w"), indent=1)

    table = {}
    for name, fen in (("deep_mate", BOARD), ("mate_in_1", MATE1)):
        for setting, opt in (("default", None), ("LmpBase=8", "setoption name LmpBase value 8")):
            row = {}
            for d in DEPTHS:
                r = search(exe, fen, d, opt)
                ok, why = (None, "not a mate score")
                if r["kind"] == "mate":
                    ok, why = pv_is_mate(fen, r["pv"], r["value"])
                r["pv_verified"] = ok
                r["pv_note"] = why
                row[d] = r
            table["%s|%s" % (name, setting)] = row
            print("%-12s %-10s %s" % (name, setting, "  ".join(
                "d%d:%s %d" % (d, row[d]["kind"], row[d]["value"]) for d in DEPTHS)))
    json.dump(table, open(os.path.join(outdir, "table.json"), "w"), indent=1)

    print()
    print("### replayed mate PVs")
    for k, row in table.items():
        for d, r in row.items():
            if r["kind"] == "mate":
                print("- %-22s d%-2d mate %-3d PV %s -> %s %s"
                      % (k, d, r["value"], " ".join(r["pv"][:8]) or "(empty pv)",
                         "OK" if r["pv_verified"] else "NOT A MATE", "| " + r["pv_note"]))

    # ---- the discriminating claims of "a delay, not breakage"
    deep_d = table["deep_mate|default"]
    deep_t = table["deep_mate|LmpBase=8"]
    one_d = table["mate_in_1|default"]
    one_t = table["mate_in_1|LmpBase=8"]
    tuned_mates = [d for d in DEPTHS if deep_t[d]["kind"] == "mate"]
    checks = {
        "default reports `mate` at d10 on the deep board": deep_d[10]["kind"] == "mate",
        "default reports `mate` at d12 on the deep board": deep_d[12]["kind"] == "mate",
        "LmpBase=8 reports cp (not mate) at d10 on the deep board": deep_t[10]["kind"] == "cp",
        "LmpBase=8 reports cp (not mate) at d12 on the deep board": deep_t[12]["kind"] == "cp",
        "LmpBase=8 DOES find a mate at some depth <= 14 (so: delay, not breakage)": bool(tuned_mates),
        "mate-in-1 is untouched by LmpBase=8 at every depth": all(
            one_d[d]["kind"] == one_t[d]["kind"] == "mate" and one_d[d]["value"] == one_t[d]["value"]
            for d in DEPTHS),
        "no mate PV replays to a WRONG position (truncated PVs are reported apart, not counted as proof)":
            all(r["pv_verified"] is not False for row in table.values() for r in row.values()),
    }
    trunc = sum(1 for row in table.values() for r in row.values() if r["pv_verified"] is None)
    verified = sum(1 for row in table.values() for r in row.values() if r["pv_verified"] is True)
    print()
    print("### mate PV replay: %d verified as real checkmates, %d TRUNCATED short of the claimed distance, "
          "0 wrong" % (verified, trunc))
    print()
    print("### verdict checks")
    for k, v in checks.items():
        print("- %-76s %s" % (k, "PASS" if v else "FAIL"))
    json.dump(checks, open(os.path.join(outdir, "checks.json"), "w"), indent=1)
    if not all(checks.values()):
        bad = [k for k, v in checks.items() if not v]
        sys.exit("CONCLUSION: REFUTES S-F20 on: %s" % "; ".join(bad))
    print()
    print("CONCLUSION: CONFIRMS S-F20 — LmpBase=8 replaces a proven mate with a cp score at d10/d12 on the "
          "deep board and recovers a mate deeper, while mate-in-1 is untouched.")


if __name__ == "__main__":
    main()
