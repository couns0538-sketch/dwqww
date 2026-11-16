#!/usr/bin/env python3
"""analyze_draw.py OUTJSONL : scores per set, against the prediction."""
import json, sys, collections
import chess

recs = [json.loads(l) for l in open(sys.argv[1])]
def score(info):
    """Parse 'score KIND VALUE' from an info line; FAIL LOUDLY if the token is absent."""
    t = info.split()
    if "score" not in t:
        raise SystemExit("PARSE FAILURE: no 'score' token in: %r" % info)
    i = t.index("score")
    if i + 2 >= len(t):
        raise SystemExit("PARSE FAILURE: 'score' with no kind/value in: %r" % info)
    kind, raw = t[i+1], t[i+2]
    if kind not in ("cp", "mate"):
        raise SystemExit("PARSE FAILURE: unknown score kind %r in: %r" % (kind, info))
    try:
        val = int(raw)
    except ValueError:
        raise SystemExit("PARSE FAILURE: score value %r is not an integer in: %r" % (raw, info))
    return kind, val

by = collections.OrderedDict()
for r in recs:
    by.setdefault(r["set"], []).append(r)

print("%-7s %3s %-28s %s" % ("set", "n", "scores (cp; 'm' prefix = mate)", "verdict"))
rows = []
for name, rs in by.items():
    sc = []
    bad = 0
    for r in rs:
        if not r["accepted"] or not r["infos"]:
            bad += 1; sc.append("NO_INFO"); continue
        k, v = score(r["infos"][-1])
        sc.append(("m%+d" % v) if k == "mate" else str(v))
    if bad:
        raise SystemExit("PARSE FAILURE: set %s had %d records with no info line" % (name, bad))
    if len(rs) != 20:
        raise SystemExit("SET SIZE FAILURE: set %s has %d records, expected 20" % (name, len(rs)))
    if any(x == "NO_INFO" for x in sc):
        raise SystemExit("PARSE FAILURE: set %s has an unparsed score" % name)
    rows.append((name, len(rs), sc, bad))
    print("%-7s %3d %-28s accepted=%d refused/noinfo=%d" % (name, len(rs), " ".join(sc[:10]) + (" ..." if len(sc) > 10 else ""), len(rs)-bad, bad))

print()
print("PER-SET SUMMARY")
for name, n, sc, bad in rows:
    vals = [int(s) for s in sc if not s.startswith("m") and s != "NO_INFO"]
    mates = [s for s in sc if s.startswith("m")]
    if vals:
        print("%-7s n=%d nonzero=%d min=%d max=%d mates=%d" % (
            name, n, sum(1 for v in vals if v != 0), min(vals), max(vals), len(mates)))
    else:
        print("%-7s n=%d no cp scores; mates=%d" % (name, n, len(mates)))

print()
print("ILLEGAL BESTMOVES")
nbad = 0
for r in recs:
    if not r["bestmove"]:
        print("NO BESTMOVE", r["set"], r["payload"][:40]); nbad += 1; continue
    tok = r["bestmove"].split()
    if len(tok) < 2 or tok[1] == "0000":
        continue
    if r["kind"] == "fen":
        b = chess.Board(r["payload"])
    else:
        b = chess.Board()
        for u in r["payload"].split():
            b.push(chess.Move.from_uci(u))
    mv = chess.Move.from_uci(tok[1])
    if mv not in b.legal_moves:
        print("ILLEGAL", r["set"], r["payload"][:40], tok[1]); nbad += 1
print("illegal/missing bestmoves: %d of %d" % (nbad, len(recs)))
