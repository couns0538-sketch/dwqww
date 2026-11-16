#!/usr/bin/env python3
"""Analyse the depth-10 colour-mirror search output (area 6 job 3).

The colour mirror (python-chess board.mirror()) flips the board AND the side to move, so the
side-to-move-relative score must be EQUAL, not negated: job 1 measured e.g. total -351 for a position
and total -351 for its mirror. My committed prediction Q2 stated "negated"; both rules are reported here
and the report says which one is correct.

Compares, per record:
  (a) bestmove: the mirror's bestmove must equal the original bestmove with every square ^56
  (b) score, rule EQUAL   (correct semantics) and rule NEGATED (what prediction.txt said)
  (c) engine self-consistency: the last PV's first move equals the bestmove, on both sides
  (d) the mirror's PV equals the original PV with every square ^56

usage: analyse_search.py OUTFILE.jsonl [MORE.jsonl...]
"""
import json
import sys

import chess


def split_bestmove(line):
    if not line:
        return None
    tok = line.split()
    return tok[1] if len(tok) > 1 else None


def split_info(line):
    if not line:
        return None
    tok = line.split()
    out = {"pv": [], "depth": None, "score_kind": None, "score_value": None}
    for i, t in enumerate(tok):
        if t == "depth" and i + 1 < len(tok):
            out["depth"] = int(tok[i + 1])
        elif t == "score" and i + 2 < len(tok):
            out["score_kind"] = tok[i + 1]
            try:
                out["score_value"] = int(tok[i + 2])
            except ValueError:
                out["score_value"] = None
        elif t == "pv":
            out["pv"] = tok[i + 1:]
            break
    return out


def mirror_uci(uci):
    """Map a UCI move through the colour mirror: each square ^56, promotion letter kept."""
    if not uci or len(uci) < 4:
        return None
    frm = chess.parse_square(uci[0:2])
    to = chess.parse_square(uci[2:4])
    promo = uci[4:] if len(uci) > 4 else ""
    return chess.square_name(frm ^ 56) + chess.square_name(to ^ 56) + promo


def main(paths):
    total = 0
    fail_bm, fail_eq, fail_neg, fail_pvfirst, fail_pvmirror = [], [], [], [], []
    seconds, depths, nodes = [], [], []
    for path in paths:
        for raw in open(path):
            r = json.loads(raw)
            total += 1
            s, m = r["self"], r["mirror"]
            seconds.append(s["seconds"] + m["seconds"])
            bm_s, bm_m = split_bestmove(s["bestmove"]), split_bestmove(m["bestmove"])
            info_s, info_m = split_info(s["last_pv"]), split_info(m["last_pv"])
            for info in (info_s, info_m):
                if info and info["depth"]:
                    depths.append(info["depth"])

            expect = mirror_uci(bm_s)
            if bm_m != expect:
                fail_bm.append((r["index"], bm_s, bm_m, expect,
                                info_s["score_value"] if info_s else None,
                                info_m["score_value"] if info_m else None))

            if info_s and info_m and info_s["score_kind"] == info_m["score_kind"] \
                    and info_s["score_value"] is not None and info_m["score_value"] is not None:
                a, b = info_s["score_value"], info_m["score_value"]
                if a != b:
                    fail_eq.append((r["index"], info_s["score_kind"], a, b))
                if b != -a:
                    fail_neg.append((r["index"], info_s["score_kind"], a, b))
            elif info_s and info_m:
                fail_eq.append((r["index"], "kind differs", info_s["score_kind"], info_m["score_kind"]))

            for tag, bm, info in (("self", bm_s, info_s), ("mirror", bm_m, info_m)):
                if info and bm and (not info["pv"] or info["pv"][0] != bm):
                    fail_pvfirst.append((tag, r["index"], bm, info["pv"][:1]))

            if info_s and info_m and info_s["pv"] and info_m["pv"]:
                pm = [mirror_uci(x) for x in info_s["pv"]]
                if pm != info_m["pv"]:
                    fail_pvmirror.append((r["index"], info_s["pv"][:5], info_m["pv"][:5]))

    print("records: %d" % total)
    print("(a) bestmove differs after mirroring: %d of %d" % (len(fail_bm), total))
    print("(b) score differs, rule EQUAL  (correct semantics): %d of %d" % (len(fail_eq), total))
    print("(b') score differs, rule NEGATED (as prediction.txt said): %d of %d" % (len(fail_neg), total))
    print("(c) last-PV-first != bestmove: %d of %d sides" % (len(fail_pvfirst), 2 * total))
    print("(d) PV is not the mirror of the PV: %d of %d" % (len(fail_pvmirror), total))
    if depths:
        print("depth reached: min %d max %d (expect 10)" % (min(depths), max(depths)))
    if seconds:
        srt = sorted(seconds)
        print("seconds per position-pair: median %.3f  max %.3f  total %.0f"
              % (srt[len(srt) // 2], srt[-1], sum(seconds)))
    for name, rows in (("BESTMOVE", fail_bm), ("SCORE-EQUAL", fail_eq), ("SCORE-NEGATED", fail_neg),
                       ("PV-FIRST", fail_pvfirst), ("PV-MIRROR", fail_pvmirror)):
        print("")
        print("%s differences: %d" % (name, len(rows)))
        for row in rows[:25]:
            print("  " + "\t".join(str(x) for x in row))
        if len(rows) > 25:
            print("  ... %d more (see the raw .jsonl)" % (len(rows) - 25))


if __name__ == "__main__":
    main(sys.argv[1:])
