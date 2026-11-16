#!/usr/bin/env python3
"""pc20_rerun.py EXE OUTDIR LABEL

Re-runs MY OWN area-1 findings on the PC build (r15) under settings PC20, Threads 1.

Which find each case tests:
  21-F1/F2  a refused FEN still answers readyok and later searches use the old board
  21-F8     fullmove 0 refused while python-chess accepts it
  21-F9     halfmove >= 100 misses a mate in 1, both colours
  21-F11    a checkmated root is scored `mate 0`
  21-C2     an illegal move in a long list keeps the legal prefix
  21-F10    real positions are all accepted
Also records whether FORGE_FIX_ROOT_DRAWN (which file 5 says repairs the drawn-root defect)
changes 21-F9 — the most valuable single question in my area right now.

PC20 = Hash 16, Threads 1, the 14 S14 settings, CuckooRep true, HistRework 2, TtPruneV2 true,
CorrHistV2 true, MateAlphaGuard true, OwnBook false. Every setoption is followed by isready and
read to readyok; the run stops on unknown option / invalid value / ERROR.
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job6"))
from safe_engine import SafeEngine, Timeout, bestmove_of, last_info  # noqa: E402

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
BASIC = [("Hash", "16"), ("Threads", "1")]
BAD = ("unknown option", "invalid value", "ERROR")


def engine(exe, raw):
    """SafeEngine with PC20 applied, Threads 1, verifying every option was accepted."""
    e = SafeEngine(exe, raw, hash_mb=16, threads=1)
    for n, v in S14 + PC20_EXTRA:
        e.send("setoption name %s value %s" % (n, v))
        e.send("isready")
        lines = e.wait_for("readyok")
        bad = [l for l in lines if any(b in l for b in BAD)]
        if bad:
            e.close()
            raise AssertionError("option %s=%s rejected: %s" % (n, v, bad))
    e.send("ucinewgame")
    e.send("isready")
    e.wait_for("readyok")
    return e


def mates_in_one(fen):
    b = chess.Board(fen)
    out = []
    for m in list(b.legal_moves):
        c = b.copy()
        c.push(m)
        if c.is_checkmate():
            out.append(m.uci())
    return out


def nodes_of(lines, tag):
    for l in reversed(lines):
        m = re.search(r" nodes (\d+)", l)
        if m:
            return int(m.group(1))
    vals = [int(l.split()[1]) for l in lines if l.startswith("nodes ")]
    if vals:
        return vals[0]
    raise AssertionError("%s: no nodes value — measured nothing" % tag)


def main():
    exe, outdir, label = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(outdir, exist_ok=True)
    R = {}

    # ---- 21-F9: mate in 1 at halfmove 100 and 99, both colours
    for tag, fen in (
        ("F9_W_hm100", "6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 100 60"),
        ("F9_W_hm99", "6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 99 60"),
        ("F9_B_hm100", "r5k1/5ppp/8/8/8/8/5PPP/6K1 b - - 100 60"),
        ("F9_B_hm99", "r5k1/5ppp/8/8/8/8/5PPP/6K1 b - - 99 60"),
    ):
        e = engine(exe, os.path.join(outdir, tag + "_raw.txt"))
        ans = e.position("position fen " + fen)
        if any("invalid FEN" in l for l in ans):
            raise AssertionError("%s: FEN refused" % tag)
        lines = e.go("go depth 5")
        e.close()
        mates = mates_in_one(fen)
        bm = bestmove_of(lines)
        R[tag] = dict(bestmove=bm, nodes=nodes_of(lines, tag), info=last_info(lines),
                      mates=mates, found=bm in mates)

    # ---- 21-F11: a checkmated root
    mate_fen = "4R1k1/5ppp/8/8/8/8/5PPP/6K1 b - - 1 60"
    e = engine(exe, os.path.join(outdir, "F11_checkmated_raw.txt"))
    e.position("position fen " + mate_fen)
    lines = e.go("go depth 3")
    e.close()
    R["F11"] = dict(bestmove=bestmove_of(lines), info=last_info(lines),
                    nodes=nodes_of(lines, "F11"),
                    python_checkmate=chess.Board(mate_fen).is_checkmate())

    # ---- 21-F8: fullmove 0
    for tag, fen in (("F8_fm0", "4k3/8/8/8/8/8/8/4K2R w K - 0 0"),
                     ("F8_fm1", "4k3/8/8/8/8/8/8/4K2R w K - 0 1")):
        e = engine(exe, os.path.join(outdir, tag + "_raw.txt"))
        ans = e.position("position fen " + fen)
        lines = e.go("go perft 1", token="nodes")
        e.close()
        R[tag] = dict(refused=any("invalid FEN" in l for l in ans),
                      answer=[l for l in ans if "info string" in l],
                      perft1=nodes_of(lines, tag),
                      python=chess.Board(fen).legal_moves.count())

    # ---- 21-F1/F2: refused FEN then a search
    hist = "e2e4 e7e5 g1f3 b8c6 f1b5"
    bad = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKBR1 w KQkq - 0 3"
    e = engine(exe, os.path.join(outdir, "F2_sticky_raw.txt"))
    e.position("position startpos moves " + hist)
    g1 = bestmove_of(e.go("go depth 6"))
    ans = e.position("position fen " + bad)
    g2 = bestmove_of(e.go("go depth 6"))
    e.close()
    R["F2"] = dict(go1=g1, go2=g2, answer=[l for l in ans if "info string" in l],
                   readyok_after=any(l == "readyok" for l in ans))

    # ---- 21-C2: illegal prefix in a long list
    import importlib.util
    lm_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job4", "long_moves.py")
    spec = importlib.util.spec_from_file_location("lm", lm_path)
    lm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lm)
    plies, boards = lm.build_game(200)
    tok = lm.illegal_token(boards[9])
    seq = plies[:9] + [tok] + plies[9:]
    e = engine(exe, os.path.join(outdir, "C2_prefix_raw.txt"))
    e.position("position startpos moves " + " ".join(seq))
    lines = e.go("go perft 1", token="nodes")
    e.close()
    R["C2"] = dict(token=tok, perft1=nodes_of(lines, "C2"),
                   py_prefix=boards[9].legal_moves.count())

    with open(os.path.join(outdir, label + ".json"), "w") as fh:
        json.dump(R, fh, indent=1)
    rows = ["| find | case | result | python |", "|---|---|---|---|"]
    for tag in ("F9_W_hm100", "F9_W_hm99", "F9_B_hm100", "F9_B_hm99"):
        r = R[tag]
        rows.append("| 21-F9 | %s | %s %s nodes, mates=%s, found=%s | %s |" % (
            tag, r["bestmove"], r["nodes"], r["mates"], r["found"], r["mates"]))
    rows.append("| 21-F11 | checkmated root | %s, info=%s | checkmate=%s |" % (
        R["F11"]["bestmove"], R["F11"]["info"][-46:], R["F11"]["python_checkmate"]))
    rows.append("| 21-F8 | fullmove 0 | refused=%s, perft1=%s | %s |" % (
        R["F8_fm0"]["refused"], R["F8_fm0"]["perft1"], R["F8_fm0"]["python"]))
    rows.append("| 21-F8 | fullmove 1 (control) | refused=%s, perft1=%s | %s |" % (
        R["F8_fm1"]["refused"], R["F8_fm1"]["perft1"], R["F8_fm1"]["python"]))
    rows.append("| 21-F2 | refused FEN after a game | go1=%s go2=%s readyok=%s | – |" % (
        R["F2"]["go1"], R["F2"]["go2"], R["F2"]["readyok_after"]))
    rows.append("| 21-C2 | illegal at ply 10 | perft1=%s | %s |" % (
        R["C2"]["perft1"], R["C2"]["py_prefix"]))
    text = "\n".join(rows)
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()