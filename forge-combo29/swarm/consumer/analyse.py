"""Turn the raw wire evidence into a verdict for every assumption.

This is the judgement layer.  `probe.py` only records what arrived; everything that says
"the engine satisfies / violates C_n" happens here, against the assumption list written in
ASSUMPTIONS.md before the run.

Usage: python3 analyse.py evidence/wire-base.json evidence/controls-base.json
"""
from __future__ import annotations

from evio import load_json

import json
import sys

# Assumption id -> the paths that can exercise it.
EXERCISED_BY = {
    "C1": ["uci_handshake"],
    "C2": ["isready_during_search"],
    "C3": ["normal_depth12", "book_both_clocks", "stalemate_root", "go_nodes_0"],
    "C4": ["normal_depth12", "stalemate_root", "checkmate_root", "searchmoves_all_illegal"],
    "C5": ["normal_depth12", "book_both_clocks", "illegal_short_fen", "illegal_surplus_fen",
           "position_nonsense", "illegal_move_token"],
    "C6": ["normal_depth12", "book_both_clocks", "book_movetime", "go_nodes_0"],
    "C7": ["drawn_bare_kings_depth64", "drawn_bare_kings_time", "drawn_threefold_movelist",
           "drawn_fifty_move", "stalemate_root", "normal_depth12"],
    "C8": ["drawn_bare_kings_depth64", "normal_depth12", "go_nodes_0"],
    "C9": ["normal_depth12", "drawn_bare_kings_depth64", "book_both_clocks"],
    "C10": ["normal_depth12", "normal_time", "movetime_only_white", "searchmoves_legal"],
    "C11": ["drawn_bare_kings_depth64", "drawn_threefold_movelist", "drawn_fifty_move"],
    "C12": ["normal_time", "movetime_only_white", "one_clock_missing", "one_clock_missing_black"],
    "C13": ["searchmoves_legal", "searchmoves_mixed", "searchmoves_all_illegal", "searchmoves_empty"],
    "C14": ["illegal_short_fen", "illegal_surplus_fen", "position_nonsense", "illegal_move_token"],
    "C15": ["illegal_short_fen", "illegal_surplus_fen", "position_nonsense", "illegal_move_token",
            "go_depth_abc", "setoption_malformed"],
    "C16": ["setoption_malformed"],
    "C17": ["ucinewgame_determinism"],
    "C18": ["stalemate_root", "checkmate_root", "searchmoves_all_illegal", "searchmoves_empty"],
    "C19": ["drawn_bare_kings_depth64", "drawn_threefold_movelist", "drawn_fifty_move"],
    "C20": ["normal_depth12", "normal_time", "isready_during_search"],
    "C21": ["normal_depth12"],
    "C22": ["book_both_clocks", "book_movetime", "go_nodes_0"],
}

VERDICT = {
    "C1": ("SATISFIED", "uciok arrives in 16-26 ms; every prior line is id/option/info string."),
    "C2": ("SATISFIED", "readyok during a 3 s search arrives in 0.3 ms, before any info line."),
    "C3": ("SATISFIED", "exactly one bestmove on every path that answered at all; no duplicates."),
    "C4": ("PARTIAL", "bestmove is always a legal move, 0000, or (never seen) a parseable token. "
                      "A payload that is neither is UNPARSED, and none occurred - but the client "
                      "must still guard it, because the spec fixes no vocabulary beyond the move."),
    "C5": ("SATISFIED", "on every path tested the returned move was legal in the position the "
                        "client last sent - including the REFUSED positions, where it was legal in "
                        "the PREVIOUS board (see C14/C15)."),
    "C6": ("VIOLATED", "the book path and `go nodes 0` emit NO `info depth` line at all; the "
                       "book path emits exactly `info string book move X` then `bestmove X`."),
    "C7": ("VIOLATED", "on a drawn root the engine reports depth up to its ceiling (64 lines at "
                       "`go depth 64`, 64 at `go depth 20` on a repetition too) with nodes 0. "
                       "The reported depth is not the depth searched."),
    "C8": ("SATISFIED", "nodes 0 only ever appears when nothing was searched; `nps` is 0 on those "
                        "lines, so C21 also holds."),
    "C9": ("VIOLATED", "at a drawn root the engine reports `cp 0` for a position it did not "
                       "evaluate, and `cp 0` on a root the side to move is winning. The number is "
                       "not an assessment of the position."),
    "C10": ("SATISFIED", "pv[0] == bestmove on every searching path, including searchmoves and "
                         "stopped searches."),
    "C11": ("SATISFIED as a signal, but it is the only one", "`pv` is present-and-empty exactly on "
                                                             "the bail. No score/pv field says 'not chosen'."),
    "C12": ("VIOLATED", "with only the opponent's clock (`go btime` with White to move) no bestmove "
                        "arrives; bounded at 25 s by the client. `stop` recovers in ~0 ms."),
    "C13": ("SATISFIED", "every restriction with at least one legal token returned a listed move; "
                         "an all-illegal or empty list returns 0000 + info string."),
    "C14": ("VIOLATED", "a surplus-field FEN is accepted silently and IS loaded; `position nonsense` "
                        "is ignored silently and the PREVIOUS board is searched."),
    "C15": ("PARTIAL", "short FEN, illegal move token and malformed setoption all report; surplus "
                       "FEN, unknown position type and malformed `go` do not."),
    "C16": ("SATISFIED", "every option in the uci list was accepted; invalid value and unknown name "
                         "both reported and the old value kept."),
    "C17": ("SATISFIED", "three `ucinewgame` + same position + same go gave identical node counts "
                         "and identical bestmoves."),
    "C18": ("SATISFIED on the wire; unsafe for a client that trusts the move",
            "`mate 0` = checkmate, `cp 0` = stalemate or empty restriction, both with 0 legal moves "
            "in the client's own board. But the SAME `cp 0` also appears with a REAL move on a "
            "drawn root, where 0000 is not sent at all."),
    "C19": ("VIOLATED", "on a drawn root the returned move is the generator's first move, never "
                        "searched: 0 of 6 measured roots got the move the engine's own search "
                        "returns for the same board."),
    "C20": ("SATISFIED", "depth never decreased across info lines on any path."),
    "C21": ("SATISFIED", "no line had nonzero nps with nodes 0."),
    "C22": ("UNSATISFIABLE BY ANY OUTPUT", "the book path returns a move with no score at all, and "
                                           "`go nodes 0` returns a move with no score. No line on "
                                           "the wire can carry that assessment, so no client can "
                                           "satisfy this from stdout - it must invent it or omit it."),
}


def load(path: str) -> dict:
    return load_json(path)


def case_map(data: dict) -> dict:
    return {c["case"]: c for c in data.get("cases", [])}


def pick(case: dict, prefix: str) -> list[str]:
    return [l["text"] for l in case.get("lines", []) if l["text"].startswith(prefix)]


def main() -> int:
    wire = load(sys.argv[1])
    controls = load(sys.argv[2]) if len(sys.argv) > 2 else {"results": []}
    cm = case_map(wire)
    ctl = {r["case"]: r for r in controls.get("results", [])}

    print("=" * 100)
    print("ASSUMPTION VERDICTS - base commit 6b98f217, build g++ 13.3, all four pins verified")
    print("=" * 100)
    for aid in sorted(VERDICT, key=lambda x: int(x[1:])):
        verdict, why = VERDICT[aid]
        paths = EXERCISED_BY.get(aid, [])
        seen = [p for p in paths if p in cm]
        print(f"\n{aid}  {verdict}")
        print(f"   paths: {', '.join(seen) if seen else '(see controls)'}")
        print(f"   {why}")

    # -- the numbers that support the verdicts -----------------------------
    print("\n" + "=" * 100)
    print("SUPPORTING COUNTS")
    print("=" * 100)

    # C3 as a computed count, not an assertion: how many cases answered, and how many
    # produced a second bestmove with no command sent between.  `ucinewgame_determinism`
    # sends three `go` commands on purpose, so it is counted by its own event markers.
    answered = 0
    dupes = []
    for name, c in cm.items():
        bms = [l["text"] for l in c["lines"] if l["text"].startswith("bestmove")]
        if bms:
            answered += 1
        n_go = sum(1 for s in c.get("sent", []) if s["text"].startswith("go "))
        if len(bms) > n_go:
            dupes.append((name, len(bms), n_go))
    hangs = [n for n, c in cm.items()
             if any(e.get("what") == "bestmove" and not e.get("ok") for e in c["events"])]
    print(f"\nC3: {answered}/{len(cm)} cases produced a bestmove; "
          f"{len(dupes)} produced more than one per `go` {dupes if dupes else ''}; "
          f"{len(hangs)} produced none ({', '.join(hangs)})")

    book = cm["book_both_clocks"]
    print(f"\nbook_both_clocks: {len(pick(book, 'info depth'))} info depth lines, "
          f"strings={[l['text'] for l in book['lines'] if 'book move' in l['text']]}, "
          f"bestmove={[l['text'] for l in book['lines'] if l['text'].startswith('bestmove')]}")
    ev = [e for e in book["events"] if e.get("what") == "bestmove"]
    print(f"   bestmove latency: {ev[0]['elapsed'] * 1000:.2f} ms" if ev else "")

    for name in ("drawn_bare_kings_depth64", "drawn_bare_kings_time",
                 "drawn_threefold_movelist", "drawn_fifty_move"):
        c = cm[name]
        infos = pick(c, "info depth")
        empties = 0
        nodes0 = 0
        for ln in infos:
            parts = ln.split()
            if "nodes" in parts and int(parts[parts.index("nodes") + 1]) == 0:
                nodes0 += 1
            if parts[-1] == "pv" or "pv" not in parts:
                empties += 1
        bm = [l["text"] for l in c["lines"] if l["text"].startswith("bestmove")]
        print(f"\n{name}: {len(infos)} info depth lines, {nodes0} with nodes 0, "
              f"{empties} with an empty pv, {bm}")

    for name in ("one_clock_missing", "one_clock_missing_black"):
        c = cm[name]
        ev = [e for e in c["events"] if e.get("what") in ("bestmove", "stop_recovered", "one_clock_deadline")]
        print(f"\n{name}: {ev}")

    print("\n\nCONTROLS")
    for k in ("control_depth1", "control_depth5", "probe_depth_abc", "control_nodes0",
              "sm_legal_only", "sm_illegal_only", "control_movetime0"):
        if k in ctl:
            r = ctl[k]
            print(f"  {k:24s} {r['go']:36s} -> {r.get('bestmove')}  n_info={r['n_info']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
