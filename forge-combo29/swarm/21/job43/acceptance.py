#!/usr/bin/env python3
"""acceptance.py EXE OUTDIR [LABEL]

THE ACCEPTANCE SPEC for DESIGN_drawn_root.md, as a runnable check.

Rule under test (from the design note):
  At a root the rules call drawn (third occurrence, or halfmove counter >= 100), SEARCH the root, then
  report the draw score UNLESS the search finds a win for the side to move.

Cases and what a CONFORMING engine must answer:

| case | root | must answer |
|---|---|---|
| S1 | halfmove 100, mate in 1 available | a MATE score for the side to move |
| S2 | halfmove 100, no mate available | cp 0 |
| S3 | insufficient material (K v K) | cp 0 |
| S4 | threefold, mate in 1 available | a MATE score for the side to move |
| S5 | threefold, no mate available | cp 0 |

This script does not fix anything: it prints PASS/FAIL per case for whichever build it is given, so a
patch can be judged by one command. Exit code 0 only when every case passes.

Every case asserts the FEN was accepted, and every case's premise (mate available / not) is verified
with python-chess before the engine is asked, so a false premise cannot pass as a pass.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job6"))
from safe_engine import SafeEngine, bestmove_of, last_info  # noqa: E402

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
PINS = [("bench 11", 312866), ("bench 13", 862329), ("bench 16", 3024920), ("go perft 5", 4865609)]

# boards
MATE_ROOK_E1 = "6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 100 60"      # e1e8 mates
NO_MATE_100 = "8/8/8/4k3/8/8/4P3/4K3 w - - 100 60"             # K+P vs K, no mate
KVK = "4k3/8/8/8/8/8/8/4K3 w - - 0 60"
REP_START = "6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 60"
REP_CYCLE = ["e1d1", "g8h8", "d1e1", "h8g8"]
NOMATE_START = "8/8/8/4k3/8/8/4P3/4K3 w - - 0 60"
NOMATE_CYCLE = ["e1f1", "e5d5", "f1e1", "d5e5"]


def mates_in_one(fen):
    b = chess.Board(fen)
    out = []
    for m in list(b.legal_moves):
        c = b.copy()
        c.push(m)
        if c.is_checkmate():
            out.append(m.uci())
    return out


def rep(fen, cycle, times):
    b = chess.Board(fen)
    seq = []
    for _ in range(times):
        for mv in cycle:
            b.push_uci(mv)
            seq.append(mv)
    return b, seq


def ask(exe, outdir, tag, pos, opts, go="go depth 12"):
    e = SafeEngine(exe, os.path.join(outdir, tag + "_raw.txt"), hash_mb=16, threads=1)
    for k, v in opts:
        e.send("setoption name %s value %s" % (k, v))
        e.send("isready")
        e.wait_for("readyok")
    if opts:
        e.send("ucinewgame"); e.send("isready"); e.wait_for("readyok")
    ans = e.position(pos)
    if any("invalid FEN" in l for l in ans):
        e.close()
        raise AssertionError("%s: FEN refused — premise broken" % tag)
    lines = e.go(go, timeout=180)
    e.close()
    info = last_info(lines)
    m = re.search(r"score (cp|mate) (-?\d+)", info)
    return (m.group(1), int(m.group(2))) if m else None, bestmove_of(lines), info


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    label = sys.argv[3] if len(sys.argv) > 3 else "build"
    opts = S14 + PC20_EXTRA if "pc" in label else []
    os.makedirs(outdir, exist_ok=True)

    b_rep, seq_rep = rep(REP_START, REP_CYCLE, 2)
    b_rep_no, seq_no = rep(NOMATE_START, NOMATE_CYCLE, 2)
    # premises, verified before the engine is asked
    premises = {
        "S1": mates_in_one(MATE_ROOK_E1),
        "S2": mates_in_one(NO_MATE_100),
        "S3": [],
        "S4": mates_in_one(b_rep.fen()),
        "S5": mates_in_one(b_rep_no.fen()),
    }
    assert premises["S1"], "S1 premise broken: no mate on the board"
    assert not premises["S2"], "S2 premise broken: a mate exists"
    assert premises["S4"], "S4 premise broken: no mate at the threefold root"
    assert not premises["S5"], "S5 premise broken: no mate at the threefold root"
    assert b_rep.is_repetition(3), "S4 root is not a threefold"
    assert b_rep_no.is_repetition(3), "S5 root is not a threefold"
    assert chess.Board(KVK).is_insufficient_material(), "S3 is not insufficient material"

    cases = [
        ("S1", "halfmove 100 + mate in 1", "position fen " + MATE_ROOK_E1, "mate"),
        ("S2", "halfmove 100, no mate", "position fen " + NO_MATE_100, "cp0"),
        ("S3", "insufficient material", "position fen " + KVK, "cp0"),
        ("S4", "threefold + mate in 1",
         "position fen %s moves %s" % (REP_START, " ".join(seq_rep)), "mate"),
        ("S5", "threefold, no mate",
         "position fen %s moves %s" % (NOMATE_START, " ".join(seq_no)), "cp0"),
    ]
    R = {}
    rows = ["| case | root | expect | got | bestmove | verdict |", "|---|---|---|---|---|---|"]
    all_pass = True
    for cid, desc, pos, expect in cases:
        sc, bm, info = ask(exe, outdir, cid, pos, opts)
        if expect == "mate":
            ok = sc is not None and sc[0] == "mate" and sc[1] > 0
        else:
            ok = sc == ("cp", 0)
        all_pass = all_pass and ok
        R[cid] = dict(expect=expect, got=sc, bestmove=bm, passed=ok)
        rows.append("| %s | %s | %s | %s | %s | **%s** |" % (
            cid, desc, expect, sc, bm, "PASS" if ok else "FAIL"))

    # pins: bench reads one line; perft answers `nodes N`. Both through the driver.
    pin_rows = []
    pins_ok = True
    for cmd, want in PINS:
        raw = os.path.join(outdir, "pin_" + re.sub(r"\W+", "_", cmd) + "_raw.txt")
        e = SafeEngine(exe, raw, hash_mb=16, threads=1)
        got = None
        try:
            if cmd.startswith("go perft"):
                e.position("position startpos")
                lines = e.go(cmd, token="nodes", timeout=300)
                vals = [int(l.split()[1]) for l in lines if l.startswith("nodes ")]
                got = vals[0] if vals else None
            else:
                e.send(cmd)
                ln = e.read_line(300.0)
                m = re.search(r"bench depth \d+ nodes (\d+)", ln)
                got = int(m.group(1)) if m else None
        except (Timeout, EOFError):
            got = None
        finally:
            e.close()
        ok = got == want
        pins_ok = pins_ok and ok
        pin_rows.append("| `%s` | %d | %s | %s |" % (cmd, want, got, "PASS" if ok else "FAIL"))

    text = "\n".join(rows) + "\n\n| pin | expected | got | verdict |\n|---|---|---|---|\n" + \
        "\n".join(pin_rows)
    text += "\n\n%s: spec %s, pins %s\n" % (
        label, "PASSED" if all_pass else "FAILED", "PASSED" if pins_ok else "FAILED")
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text)
    with open(os.path.join(outdir, "summary.json"), "w") as fh:
        json.dump(dict(cases=R, pins_ok=pins_ok, spec_ok=all_pass), fh, indent=1)
    print(text)
    sys.exit(0 if (all_pass and pins_ok) else 1)


if __name__ == "__main__":
    main()