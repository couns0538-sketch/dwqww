#!/usr/bin/env python3
"""Build the KPK table, and the KQK/KRK/KBK/KNK tables it needs for promotions.

The KPK table is the one that matters for item 2: the drawn/won boundary. It uses
only the 2 rank-preserving symmetries, because a white pawn's direction is not
preserved by a rank flip or a transpose. That choice is asserted, not assumed.

Promotions leave the signature (KPK -> KQK / KRK / KBK / KNK) and captures leave it
the other way (KPK -> KK). All four destinations are looked up in tables solved
first, so the boundary is exact and never an engine claim.

Also emits the boundary cells themselves: for each (pawn file, pawn rank, king
placement) class the table says won or drawn, which is what the sweep in item 2 is
scored against.
"""
import json
import sys
import time

sys.path.insert(0, "/tmp/fx")
import chess
import solver

CACHE = "/tmp/fx/tables_nopawn.json"
OUT = "/tmp/fx/kpk_table.json"


def load_nopawn():
    blob = json.load(open(CACHE))
    tables = {}
    for label, d in blob.items():
        syms = solver.ALL_SYMS
        tab = {"value": {}, "dtm": {}, "syms": syms,
               "n_canonical": d["summary"]["canonical_states"],
               "n_placement": d["summary"]["legal_states"]}
        for ks, v in d["value"].items():
            key = json.loads(ks)
            tab["value"][(tuple((int(sq), sym) for sq, sym in key[0]), key[1])] = v
        for ks, v in d["dtm"].items():
            key = json.loads(ks)
            tab["dtm"][(tuple((int(sq), sym) for sq, sym in key[0]), key[1])] = v
        tables[label_sig(label)] = tab
    return tables


def label_sig(label):
    """'KQK' / 'KK' -> the (piece_type, colour) signature the solver keys on.

    The labels in the cache are written as Kw v Kb with no separator, so 'KQK' is
    "white has Q", 'KK' is "neither side has anything". Parsed by walking the
    string instead of splitting on a marker that only some labels carry.
    """
    m = {"P": chess.PAWN, "N": chess.KNIGHT, "B": chess.BISHOP,
         "R": chess.ROOK, "Q": chess.QUEEN}
    assert label.startswith("K"), label
    body = label[1:]
    white, black = body, ""
    if "vK" in body:
        white, black = body.split("vK")
    else:
        # 'KK' or 'KQK': the second K begins black's material only when the
        # remainder is exactly the black king.
        i = body.find("K")
        white, black = body[:i], body[i + 1:]
    sig = [(m[c], True) for c in white]
    sig += [(m[c], False) for c in black]
    return tuple(sorted(sig))


if __name__ == "__main__":
    t0 = time.time()
    tables = load_nopawn()
    print(f"loaded {len(tables)} no-pawn tables in {time.time()-t0:.0f}s", flush=True)
    pieces = [(chess.KING, True), (chess.PAWN, True), (chess.KING, False)]
    tab = solver.solve(pieces, solver.PAWN_SYMS, tables)
    s = solver.summarise(tab, "KPK")
    print(s, flush=True)
    print("CHECK KPK.dtm_max_moves: classical figure is 28 moves for the worst won KPK",
          flush=True)
    json.dump({"summary": s,
               "value": {json.dumps(k): v for k, v in tab["value"].items()},
               "dtm": {json.dumps(k): v for k, v in tab["dtm"].items()},
               "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
              open(OUT, "w"))
    print("wrote", OUT, f"{time.time()-t0:.0f}s")
