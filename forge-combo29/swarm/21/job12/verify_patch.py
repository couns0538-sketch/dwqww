#!/usr/bin/env python3
"""verify_patch.py PATCHED_EXE BASE_EXE OUTDIR

Does the fullmove-0 patch fix the fault without changing anything else?

Cases (both engines, fresh process each):
  A  the fullmove-0 FEN: refused by base, ACCEPTED by patched, and the patched perft 1
     must equal the fullmove-1 FEN's perft 1 (15) instead of the stale 20
  B  a fullmove-0 FEN pulled from a game-like position: same question
  C  NEGATIVE: a fullmove of -1 must STILL be refused by the patched build (the patch must
     not turn a genuine error into a silent acceptance)
  D  NEGATIVE: halfmove -1, three fields, 9 in a rank, two kings, ep on a wrong rank must
     all still be refused by the patched build
  E  REGRESSION: every FEN of G and R (6,073) accepted by the patched build, exactly as by
     the base build (a patch that made the parser stricter would show up here)
  F  real-position perft 2 equality: the first 200 of G, patched vs python-chess
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job6"))
from safe_engine import SafeEngine, Timeout  # noqa: E402

import chess


def run(exe, outdir, tag, lines):
    env = dict(os.environ)
    for k in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
        env.pop(k, None)
    p = subprocess.run([exe], input="\n".join(lines + ["quit"]) + "\n", text=True,
                       capture_output=True, timeout=300, env=env)
    with open(os.path.join(outdir, tag + ".txt"), "w") as fh:
        fh.write("=== exe: %s\n" % exe)
        fh.write("=== lines:\n" + "\n".join(">>> " + s for s in lines) + "\n")
        fh.write("=== stdout:\n" + p.stdout + "\n=== stderr:\n" + p.stderr)
    return p.stdout


def perft1(exe, outdir, tag, fen):
    out = run(exe, outdir, tag, ["position fen " + fen, "isready", "go perft 1"])
    refused = "invalid FEN" in out
    nodes = [int(l.split()[1]) for l in out.splitlines() if l.startswith("nodes ")]
    return refused, (nodes[0] if nodes else None), out


NEGATIVES = [
    ("fullmove_-1", "4k3/8/8/8/8/8/8/4K2R w K - 0 -1"),
    ("halfmove_-1", "4k3/8/8/8/8/8/8/4K2R w K - -1 1"),
    ("three_fields", "8/8/8/8/8/8/8/8"),
    ("nine_in_rank", "r9/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1"),
    ("two_kings", "4k3/8/8/8/8/8/8/4K1KR w K - 0 1"),
    ("ep_wrong_rank", "4k3/8/8/8/8/4P3/8/4K2R w K - e3 0 1"),
]


def main():
    patched, base, outdir = sys.argv[1:4]
    os.makedirs(outdir, exist_ok=True)
    rows = ["| case | base | patched | python-chess legal moves | verdict |",
            "|---|---|---|---|---|"]
    ok = True

    # A / B: the fault
    faults = [
        ("A_fullmove0", "4k3/8/8/8/8/8/8/4K2R w K - 0 0", "4k3/8/8/8/8/8/8/4K2R w K - 0 1"),
        ("B_fullmove0_game", "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 0",
         "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 1"),
    ]
    for tag, fen0, fen1 in faults:
        rb, nb, _ = perft1(base, outdir, tag + "_base", fen0)
        rp, np_, _ = perft1(patched, outdir, tag + "_patched", fen0)
        _, n1, _ = perft1(patched, outdir, tag + "_patched_fm1", fen1)
        py = chess.Board(fen0).legal_moves.count()
        good = (rb is True) and (rp is False) and (np_ == n1) and (np_ == py)
        ok = ok and good
        rows.append("| %s | refused=%s nodes=%s | refused=%s nodes=%s | %d | %s |" % (
            tag, rb, nb, rp, np_, py, "FIXED" if good else "NOT FIXED"))

    # C / D: negatives must still be refused by the patched build
    for tag, fen in NEGATIVES:
        rp, np_, _ = perft1(patched, outdir, "neg_" + tag, fen)
        good = rp is True
        ok = ok and good
        rows.append("| NEG %s | – | refused=%s nodes=%s | – | %s |" % (
            tag, rp, np_, "still refused (good)" if good else "ACCEPTED (REGRESSION)"))

    # E: no stricter parsing on real positions
    fens = [l.strip() for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job1", "set_G.fens")) if l.strip()]
    fens += [l.strip() for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job1", "set_R.fens")) if l.strip()]
    batch = ["uci", "isready"]
    for f in fens:
        batch += ["position fen " + f, "isready"]
    for exe, tag in ((base, "E_base"), (patched, "E_patched")):
        out = run(exe, outdir, tag, batch)
        refusals = sum(1 for l in out.splitlines() if "invalid FEN" in l)
        rows.append("| E %s: refusals over %d real FENs | | %d | | %s |" % (
            os.path.basename(os.path.dirname(exe)), len(fens), refusals,
            "same as base" if tag == "E_patched" else "reference"))
        if tag == "E_patched":
            ok = ok and (refusals == 0)

    # F: perft 2 on 200 G positions, patched vs python-chess
    bad = 0
    e = SafeEngine(patched, os.path.join(outdir, "F_patched_raw.txt"))
    for f in fens[:200]:
        try:
            e.position("position fen " + f)
            lines = e.go("go perft 2", token="nodes", timeout=120)
        except (Timeout, EOFError):
            bad += 1
            continue
        vals = [int(l.split()[1]) for l in lines if l.startswith("nodes ")]
        if not vals:
            bad += 1
            continue
        b = chess.Board(f)
        t = 0
        for m in b.legal_moves:
            c = b.copy()
            c.push(m)
            t += c.legal_moves.count()
        if vals[0] != t:
            bad += 1
    e.close()
    rows.append("| F perft 2 on 200 G positions, patched vs python-chess | | %d mismatches | | %s |" % (
        bad, "ok" if bad == 0 else "REGRESSION"))
    ok = ok and (bad == 0)

    text = "\n".join(rows) + "\n\n=> " + ("PATCH VERIFIED" if ok else "PATCH NOT VERIFIED")
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()