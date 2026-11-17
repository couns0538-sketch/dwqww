"""Family 5: one ply from insufficient material.

Question: does the engine's STATIC score and its SEARCH score agree that the
position is drawn?

Method: construct K vs K, K+minor vs K, and same-colour-bishop pairs; take the
static evaluation from the UCI `eval` command and the search score from
`go depth 12`; compare both against the true value (0.00, the game is drawn by
insufficient material).

`eval` prints `info string eval hce N nnue N total N` on this build (uci.cpp
line ~586), so the static number is on the wire and is not inferred.
"""
import json
import re
import sys
import chess

from forge_drv import Forge, RefusedFen

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-boundary/forge"
OUT = sys.argv[2] if len(sys.argv) > 2 else "../evidence/family5_material.json"

GO = "go depth 12"


def static_eval(eng, fen):
    """Read the engine's static evaluation for a FEN via `eval`."""
    eng.set_position(fen)
    lines = eng.raw_command("eval")
    out = {"hce": None, "nnue": None, "total": None, "raw": lines}
    for ln in lines:
        m = re.search(r"eval hce (-?\d+) nnue (-?\d+) total (-?\d+)", ln)
        if m:
            out["hce"] = int(m.group(1))
            out["nnue"] = int(m.group(2))
            out["total"] = int(m.group(3))
    return out


def gen_insufficient():
    """Positions drawn by insufficient material, plus one CONTROL.

    The control is K+N vs K+N: FIDE's insufficient-material rule covers K vs K,
    K+minor vs K, and same-colour K+B vs K+B, but NOT K+N vs K+N (mate is
    constructible with the defender's own knight in the way). python-chess
    returns False for it, so it is not part of the drawn denominator -- it is
    kept to show the engine does NOT flatten it to zero, which is the correct
    behaviour and must not be counted as an agreement.
    """
    out = []
    raw = [
        # K vs K
        ("4k3/8/8/8/8/8/8/4K3 w - - 0 40", "KvK", True),
        ("8/8/4k3/8/8/4K3/8/8 b - - 0 40", "KvK", True),
        # K+N vs K
        ("4k3/8/8/8/8/8/8/4KN2 w - - 0 40", "KNvK", True),
        ("8/8/4k3/8/8/4K3/8/6N1 b - - 0 40", "KNvK", True),
        # K+B vs K
        ("4k3/8/8/8/8/8/8/4KB2 w - - 0 40", "KBvK", True),
        ("8/8/4k3/8/8/4K3/8/5B2 b - - 0 40", "KBvK", True),
        # K+B vs K+B, same colour squares (f1 light, c8 light)
        ("2b1k3/8/8/8/8/8/8/4KB2 w - - 0 40", "KBvKB_same", True),
        # CONTROL: NOT insufficient material under FIDE / python-chess
        ("1n2k3/8/8/8/8/8/8/4KN2 w - - 0 40", "KNvKN_CONTROL", False),
    ]
    for fen, label, expect_drawn in raw:
        b = chess.Board(fen)
        out.append({
            "fen": fen, "label": label,
            "expect_drawn": expect_drawn,
            "valid": b.is_valid(),
            "legal": b.legal_moves.count(),
            "is_checkmate": b.is_checkmate(),
            "is_stalemate": b.is_stalemate(),
            # the earning predicate
            "py_insufficient": b.is_insufficient_material(),
            "piece_count": len(b.piece_map()),
        })
    return out


def main():
    fixtures = gen_insufficient()
    rows = []
    with Forge(EXE) as eng:
        for fx in fixtures:
            st = static_eval(eng, fx["fen"])
            try:
                rec = eng.search(fx["fen"], GO)
            except RefusedFen as e:
                rows.append({**fx, "static": st, "refused": True, "error": str(e)})
                continue
            se = rec.score()
            static_total = st["total"]
            # Judge: both must say "drawn".
            search_drawn = (se == ("cp", 0))
            # static is drawn if |total| is small; the claim under test is
            # whether it AGREES, so record the raw number and the gap.
            if static_total is None:
                static_drawn = None
            else:
                static_drawn = abs(static_total) <= 50
            rows.append({
                **fx, "static": st,
                "static_total": static_total,
                "search_score": se, "search_nodes": rec.nodes(),
                "search_depth": rec.depth(), "search_pv": rec.pv(),
                "search_bestmove": rec.bestmove,
                "search_drawn": search_drawn,
                "static_drawn": static_drawn,
                "agree": (static_drawn == search_drawn)
                         if static_drawn is not None else None,
            })

    with open(OUT, "w") as f:
        json.dump(rows, f, indent=2)

    print(f"{'label':15} {'fen':44} {'static':>8} {'search':12} {'nodes':>8} {'agree':>6}")
    for r in rows:
        print(f"{r['label']:15} {r['fen']:44} {str(r.get('static_total')):>8} "
              f"{str(r.get('search_score')):12} {str(r.get('search_nodes')):>8} "
              f"{str(r.get('agree')):>6}")

    n = len(rows)
    drawn_rows = [r for r in rows if r.get("expect_drawn")]
    ctrl_rows = [r for r in rows if not r.get("expect_drawn")]
    agree = sum(1 for r in drawn_rows if r.get("agree") is True)
    disagree = [r for r in drawn_rows if r.get("agree") is False]
    print(f"\nstatic and search agree on {agree}/{len(drawn_rows)} DRAWN positions")
    for r in disagree:
        print(f"  DISAGREE {r['fen']}: static {r['static_total']} vs search {r['search_score']}")
    for r in ctrl_rows:
        print(f"  CONTROL {r['fen']} ({r['label']}): static {r['static_total']} "
              f"search {r['search_score']} -- must NOT be 0.00, "
              f"{'correct' if r['search_score'] != ('cp', 0) else 'WRONGLY ZERO'}")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
