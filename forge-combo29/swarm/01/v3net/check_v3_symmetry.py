#!/usr/bin/env python3
"""swarm seat 01: does seat 75's symmetry result HOLD on the v3 net? (S-C61)

Seat 75's `75-F7` question 2 reports **0 asymmetric pairs / 420**, with `hce` and `nnue` each symmetric individually. That
is a population-scale result for the **built-in** net. The owner's PC runs a **loaded FORGENN3 net** through the v3 path -
different code, different weights - and **nobody has tested symmetry there.**

That matters because symmetry is a property of the WEIGHT LAYOUT as much as of the code: `feature_index` reindexes by
king bucket and flips squares by perspective, so a net whose file was written for one perspective convention could be
asymmetric on positions where the two kings sit in different buckets. Startpos cannot show it - both sides are
identical there.

So: mirror every position in `set_G` (colour flip + board flip, keeping the side to move), evaluate both, and compare
`hce`, `nnue` and `total`. A mirror must give the SAME score, because the position is the same up to colour.

What "symmetric" means here, stated so it cannot be misread: `eval A == eval mirror(A)`, i.e. the score is
colour-invariant. That is what makes an evaluation trustworthy for both sides.

Usage: check_v3_symmetry.py <v3-exe> <net> <fens> <outdir> [limit]
"""
import hashlib
import subprocess
import sys
from pathlib import Path

import chess


def eval_at(exe, net, fen, use_v3):
    cmd = ["uci", "setoption name Threads value 1", "setoption name Hash value 16"]
    if use_v3:
        # ORDER: file first, then the boolean
        cmd += ["setoption name NNUEArchFile value " + net, "setoption name NNUEArch value true"]
    cmd += ["isready", "ucinewgame", "isready", "position fen " + fen, "isready", "eval", "quit"]
    p = subprocess.run([exe], input="\n".join(cmd) + "\n", capture_output=True, text=True, cwd="/tmp")
    for line in p.stdout.splitlines():
        if line.startswith("info string eval"):
            out = {}
            f = line.split()
            for i, t in enumerate(f):
                if t in ("hce", "nnue", "total") and i + 1 < len(f):
                    try:
                        out[t] = int(f[i + 1])
                    except ValueError:
                        pass
            return out if out else None
    return None


def main():
    exe, net, fensfile, out = sys.argv[1], sys.argv[2], sys.argv[3], Path(sys.argv[4])
    limit = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    out.mkdir(parents=True, exist_ok=True)
    sha_exe = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    sha_net = hashlib.sha256(Path(net).read_bytes()).hexdigest()

    fens = [l.split(";")[0].strip() for l in Path(fensfile).read_text().splitlines() if l.strip()]
    if limit:
        # spread the sample rather than taking a prefix: a prefix is a different population (S-C10b's error)
        step = max(1, len(fens) // limit)
        fens = fens[::step][:limit]

    rows = []
    asym_hce = asym_nnue = asym_total = 0
    skipped = 0
    for fen in fens:
        try:
            b = chess.Board(fen)
        except ValueError:
            skipped += 1
            continue
        if not b.is_valid():
            skipped += 1
            continue
        m = b.mirror()
        if not m.is_valid():
            skipped += 1
            continue
        a = eval_at(exe, net, fen, True)
        c = eval_at(exe, net, m.fen(), True)
        if a is None or c is None:
            skipped += 1
            continue
        # a mirror of the same position must score the same
        asym_hce += (a.get("hce") != c.get("hce"))
        asym_nnue += (a.get("nnue") != c.get("nnue"))
        asym_total += (a.get("total") != c.get("total"))
        rows.append({"fen": fen, "mirror": m.fen(), "a": a, "b": c,
                     "symmetric": a.get("total") == c.get("total")})

    n = len(rows)
    L = ["SEAT 75's symmetry result on the V3 NET (they tested the built-in net)",
         "exe: %s" % exe, "sha256: %s" % sha_exe,
         "net: %s" % net, "sha256: %s" % sha_net,
         "positions: %s sampled at stride (spread, not a prefix)" % (limit or "all"),
         "PC20-free settings; Threads 1, Hash 16; eval read from `info string eval`.", "",
         "pairs evaluated: %d | skipped (illegal or no reading): %d" % (n, skipped),
         "**asymmetric pairs: hce %d / nnue %d / total %d of %d**" % (asym_hce, asym_nnue, asym_total, n),
         ""]

    if n == 0:
        L.append("NOTHING WAS MEASURED - no pair produced a reading, so no symmetry claim is possible.")
        (out / "check_v3_symmetry.txt").write_text("\n".join(L) + "\n")
        print("\n".join(L))
        return 1

    if asym_total == 0:
        L.append("VERDICT: **CONFIRMS seat 75's symmetry result on the v3 path as well** - 0 asymmetric pairs of %d." % n)
        L.append("  Their 420-pair result was for the built-in net; this is the loaded FORGENN3 net through the v3 code,")
        L.append("  which nobody had tested. Symmetry therefore holds on BOTH evaluation paths, which is a stronger")
        L.append("  statement than either alone: a property of the engine, not of one net.")
    else:
        L.append("VERDICT: **CONTRADICTS symmetry on the v3 path** - %d of %d pairs score differently when mirrored." % (asym_total, n))
        L.append("  Seat 75's result holds for the built-in net; the v3 net is a different weight layout and may be")
        L.append("  asymmetric where the two kings fall in different buckets. First differing pairs:")
        for r in [x for x in rows if not x["symmetric"]][:5]:
            L.append("    %s  ->  %s   %s vs %s" % (r["fen"].split()[0], r["mirror"].split()[0], r["a"], r["b"]))

    L.append("")
    L.append("LIMIT: this compares `eval` only - the static score - not search results. A symmetric static evaluation")
    L.append("       can still be used asymmetrically by the search. And it samples rather than exhausting the set when")
    L.append("       a limit is given, so it is a population check, not an exhaustive one.")

    (out / "check_v3_symmetry.json").write_text(__import__("json").dumps(
        {"exe_sha": sha_exe, "net_sha": sha_net, "n": n, "skipped": skipped,
         "asym": {"hce": asym_hce, "nnue": asym_nnue, "total": asym_total}, "rows": rows}, indent=1))
    txt = "\n".join(L) + "\n"
    (out / "check_v3_symmetry.txt").write_text(txt)
    print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
