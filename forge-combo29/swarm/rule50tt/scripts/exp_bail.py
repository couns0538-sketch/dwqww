"""Item 5: does the drawn-root bail store a 0 into the table?

The audit says the bail does not store. That matters here because a stored 0 at
clock 100 would satisfy `rule50_clock == capped` at any later probe at clock 100
(branch A), so it would be usable forever on that board -- the poisoning the
assignment asks about.

Two proofs are required (brief rule 2): that the path RAN, and that nothing
followed.

  RAN     : the bail is identified by its own signature -- 0 nodes, empty pv,
            one info line per depth. A search that returns 0 nodes on a board
            with legal moves is the bail and nothing else.
  NOTHING : the trace build counts every accepted store. If the bail's store
            count is 0 while a normal search on the SAME board stores > 0, the
            counter is proven to work and the bail is proven not to store.
            (A store counter that never moves cannot support either claim.)

The bail needs a drawn ROOT: a halfmove-100 position, a threefold, or
insufficient material. Halfmove 100 is the one that matters for rule 50, and it
is also the one where a stored 0 would poison branch A.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import uci_driver as u  # noqa: E402

TRACE = "/tmp/forge-variants/trace/build/forge"
SHIPPED = "/agent/repos/dwqww/forge-combo29/build-rule50/forge"

# Boards whose ROOT is drawn under one of the three arms.
CASES = [
    # (label, position command, is_bail_expected)
    ("hm100_krk",  "position fen 7k/8/8/R7/8/8/8/K7 w - - 100 60", True),
    ("hm100_kqk",  "position fen 8/8/8/8/8/1K6/2Q5/7k w - - 100 60", True),
    ("hm100_kp",   "position fen 8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 100 60", True),
    ("insufficient", "position fen 8/8/8/8/8/4k3/8/4K3 w - - 40 60", True),
    # Threefold via a move list: knights shuffle back and forth three times.
    ("threefold",
     "position startpos moves g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8", True),
    # Controls: the same boards at a clock that is NOT drawn.
    ("ctrl_krk_99", "position fen 7k/8/8/R7/8/8/8/K7 w - - 99 60", False),
    ("ctrl_krk_50", "position fen 7k/8/8/R7/8/8/8/K7 w - - 50 60", False),
    ("ctrl_kqk_99", "position fen 8/8/8/8/8/1K6/2Q5/7k w - - 99 60", False),
    ("ctrl_start",  "position startpos", False),
]


def trace_of(lines):
    last = None
    for l in lines:
        if "tt_trace" in l:
            last = l
    if last is None:
        return None
    parts = last.split()
    d = {}
    for i, tok in enumerate(parts):
        if tok in ("exact", "exact_mate_far", "mate", "inside", "outside", "stores", "stores_hi", "depthmax"):
            d[tok] = int(parts[i + 1])
    return d


def run(exe, posline, go="go depth 12"):
    e = u.Engine(exe, hash_mb=16, timeout=40.0)
    try:
        return e.search(posline, go, collect_all=True)
    finally:
        e.close()


def trace_all(lines):
    """Every tt_trace line, not just the last: a bail ends the search early and
    the counters are reset at the start of the next search, so the only place a
    bail's store count can appear is a line that was never printed. The absence of
    a trace line IS the evidence, so it is recorded explicitly."""
    return [l for l in lines if "tt_trace" in l]


def main():
    out = {}
    print(f"{'case':14} {'bestmove':9} {'score':>10} {'nodes':>9} {'infos':>6} {'bail?':>6} {'stores':>8}")
    for label, posline, expect_bail in CASES:
        shipped = run(SHIPPED, posline)
        traced = run(TRACE, posline)
        t = trace_of(traced["all"]) or {}
        # The bail's signature: no `info depth` line at all on a board that has
        # legal moves, and a bestmove that came from the generator. `nodes` is
        # None because the bail's one info line is not an `info depth` line.
        # An earlier version of this file required info_lines >= 1 (wrong: the
        # bail prints NO depth line) and then compared `nodes == 0` against a None
        # (also wrong), so it reported "NO BAIL REACHED" on five real bails.
        bail = shipped["info_lines"] == 0 and shipped["bestmove"] is not None
        out[label] = {
            "pos": posline,
            "bestmove": shipped["bestmove"],
            "score_kind": shipped["score_kind"],
            "score": shipped["score"],
            "nodes": shipped["nodes"],
            "info_lines": shipped["info_lines"],
            "pv": shipped["pv"],
            "bail_signature": bail,
            "expect_bail": expect_bail,
            "trace": t,
            "invalid_fen": shipped["invalid_fen"],
        }
        flag = "BAIL" if bail else "search"
        sk = shipped["score_kind"] or "-"
        sc = shipped["score"]
        sc_txt = f"{sk} {sc}" if sc is not None else sk
        nodes = shipped["nodes"]
        nodes_txt = nodes if nodes is not None else "-"
        print(f"{label:14} {str(shipped['bestmove']):9} {sc_txt:>10} "
              f"{str(nodes_txt):>9} {shipped['info_lines']:>6} {flag:>6} {t.get('stores', -1):>8}")

    json.dump(out, open(sys.argv[1] if len(sys.argv) > 1 else "/tmp/bail.json", "w"), indent=1)

    print("\n--- verdict")
    bails = [k for k, v in out.items() if v["bail_signature"]]
    stores_when_bail = {k: out[k]["trace"].get("stores") for k in bails}
    stores_when_search = {k: out[k]["trace"].get("stores") for k, v in out.items() if not v["bail_signature"]}
    print(f"bail signature observed on: {bails}")
    print(f"stores during a bail:  {stores_when_bail}")
    print(f"stores during a search: {stores_when_search}")
    nonbail = [v for v in stores_when_search.values() if v]
    if bails and nonbail and all(v == 0 for v in stores_when_bail.values()):
        print("CONFIRMED: the bail stores nothing, and the counter is proven to move on searches.")
    elif not bails:
        print("NO BAIL REACHED - this run cannot answer the question.")
    else:
        print("NOT CONFIRMED - see per-case trace.")


if __name__ == "__main__":
    main()
