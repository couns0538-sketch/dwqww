#!/usr/bin/env python3
"""Blind-spot mutants: behavioural changes the bench pin CANNOT see.

The point is not that each change is good or bad. It is that each one changes what a
player observes and leaves all four pins bit-identical, so a gate made of pins passes
them. Each mutant is verified twice:

  (1) the four pins are unchanged      -> the gate passed it
  (2) a BEHAVIOURAL probe changed      -> the code path really is live

(2) is what makes (1) a finding rather than a broken build. A mutant that changes
nothing anywhere is a failed control, and this script reports it as such.

Mutant list (all on top of the audit base):
  B1 book off             OwnBook default false: book moves disappear from play
  B2 draw jitter          DrawJitter default 0 -> 8: leaf repetition scores change
  B3 rule50 damp          EvalRule50Damp default false -> true: clock-scaled eval
  B4 book variety         Book Variety default 30 -> 0: book RNG pinned
  B5 thread default       Threads default 1 -> 2: `go depth` node counts change
  B6 move overhead        Move Overhead default 10 -> 200: clocked search shortens
  B7 qsearch futility     QsFutilityMargin raised: leaf qsearch prunes more
  B8 fifty-move leaf      the drawn-leaf clock rule moved by one ply
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import sensitivity as S  # noqa: E402
from uci_driver import Engine  # noqa: E402

BOOKED = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
DRAWN = "8/8/8/8/8/1R6/8/k1K5 w - - 100 1"
KQK = "7k/8/5K2/4Q3/8/8/8/8 w - - 0 1"
# Halfmove clock 98 with mate on the board: the fifty-move leaf rule is what
# decides whether the score is 0 or a mate. One ply of that rule moves this score.
LEAF98 = "6k1/5p1p/8/8/8/8/5P1P/3R2K1 b - - 98 1"

MUTANTS = []


def mutant(name, why, probe):
    def deco(fn):
        MUTANTS.append((name, why, fn, probe))
        return fn
    return deco


def sub(path, old, new, n=1):
    t = path.read_text()
    if t.count(old) != n:
        raise SystemExit(f"{old[:50]!r} appears {t.count(old)}x in {path.name}, expected {n}")
    path.write_text(t.replace(old, new))


@mutant("B1_book_off", "OwnBook default true -> false: no book move is ever played",
        "booked start position, go movetime 100, is the reply a book move?")
def b1(root):
    sub(root / "forge-combo29/src/uci.cpp",
        "bool own_book = forge::book::embedded_available();", "bool own_book = false;")


@mutant("B2_draw_jitter", "DrawJitter default 0 -> 8: leaf repetition scores are no longer 0",
        "drawn leaf: go depth 12 from a repetition, compare nodes and score")
def b2(root):
    p = root / "forge-combo29/src/search.cpp"
    t = p.read_text()
    m = re.search(r"^int DrawJitter = (\d+);", t, re.M)
    if not m:
        raise SystemExit("DrawJitter definition not found")
    p.write_text(t.replace(m.group(0), "int DrawJitter = 8;"))


@mutant("B3_rule50_damp", "EvalRule50Damp default false -> true: static eval scaled by the clock",
        "high halfmove clock position, go depth 12, compare nodes/score")
def b3(root):
    p = root / "forge-combo29/src/search.cpp"
    t = p.read_text()
    old = "bool EvalRule50Damp = false;"
    if old not in t:
        raise SystemExit("EvalRule50Damp definition not found")
    p.write_text(t.replace(old, "bool EvalRule50Damp = true;"))


@mutant("B4_book_variety0", "Book Variety default 30 -> 0: the book's clock-seeded RNG pinned",
        "booked start position repeated 5x: is the book move stable?")
def b4(root):
    sub(root / "forge-combo29/src/uci.cpp", "int book_variety = 30;", "int book_variety = 0;")


@mutant("B5_threads_default2", "searcher constructed with 2 worker threads instead of 1",
        "go depth 11, compare the node count with the base")
def b5(root):
    sub(root / "forge-combo29/src/uci.cpp", "    forge::Searcher searcher;",
        "    forge::Searcher searcher(32, 2);")


@mutant("B6_move_overhead", "Move Overhead default 10 -> 200 ms: clocked searches shorten",
        "go wtime 1000, compare nodes and elapsed")
def b6(root):
    sub(root / "forge-combo29/src/uci.cpp", "int move_overhead_ms = 10;", "int move_overhead_ms = 200;")


@mutant("B7_qs_futility", "QsFutilityMargin greatly raised: leaf quiescence prunes more",
        "go depth 11, compare nodes")
def b7(root):
    p = root / "forge-combo29/src/search.cpp"
    t = p.read_text()
    m = re.search(r"^int QsFutilityMargin = (\d+);", t, re.M)
    if not m:
        raise SystemExit("QsFutilityMargin not found")
    p.write_text(t.replace(m.group(0), "int QsFutilityMargin = 4000;"))


@mutant("B8_fifty_move_leaf", "the drawn-leaf clock rule moved by one ply (99 -> 98)",
        "halfmove 98 leaf position, go depth 12, compare score/nodes")
def b8(root):
    p = root / "forge-combo29/src/search.cpp"
    t = p.read_text()
    m = re.search(r"halfmove_clock\(\) >= (\d+)", t)
    if not m:
        raise SystemExit("halfmove rule not found")
    p.write_text(t.replace(m.group(0), f"halfmove_clock() >= {int(m.group(1)) - 1}", 1))


@mutant("B9_drawn_root_move", "the drawn-root bail returns the LAST generator move instead of the "
        "first -- a change that is visible only on a drawn root",
        "a 100-halfmove drawn root: which move comes back?")
def b9(root):
    sub(root / "forge-combo29/src/search.cpp",
        "if (!root_candidates.empty()) result.best_move = root_candidates.front();",
        "if (!root_candidates.empty()) result.best_move = root_candidates[root_candidates.size() - 1];")


def _fresh(exe):
    """A probe context that is repeatable: a fresh process, ucinewgame, Clear Hash.

    This is required, not decorative. scripts/go_repeatability.py measures a bare
    `go depth 11` on one FEN returning 50,541 nodes as the first search of a process
    and 11,696 as the second in the same session; three prior searches give 72,365.
    A probe that reuses a process therefore measures its own search ORDER.
    """
    e = Engine(str(exe))
    e.uci()
    e.isready()
    e.send("ucinewgame")
    e.isready()
    e.send("setoption name Clear Hash")
    e.isready()
    return e


def behavioural_probe(exe: pathlib.Path) -> dict:
    out = {}
    with _fresh(exe) as e:
        booked = [e.search(f"position fen {BOOKED}", "go movetime 100", timeout=120) for _ in range(5)]
        out["booked_moves"] = booked
        out["book_move_lines"] = sum(1 for b in booked if b["book_move_line"])
        out["booked_stable"] = len({b["bestmove"] for b in booked}) == 1
    with _fresh(exe) as e:
        leaf = e.search(f"position fen {DRAWN}", "go depth 10", timeout=120)
        out["drawn_leaf"] = {"bestmove": leaf["bestmove"], "nodes": leaf["nodes"],
                             "info_lines": leaf["info_depth_lines"]}
    with _fresh(exe) as e:
        g = e.search(f"position fen {KIWIPETE}", "go depth 11", timeout=180)
        out["kiwipete_d11"] = {"nodes": g["nodes"], "bestmove": g["bestmove"],
                               "info_lines": g["info_depth_lines"]}
    with _fresh(exe) as e:
        clk = e.search("position startpos", "go wtime 1000 btime 1000", timeout=180)
        out["clocked_1s"] = {"nodes": clk["nodes"], "bestmove": clk["bestmove"]}
    with _fresh(exe) as e:
        leaf98 = e.search(f"position fen {LEAF98} moves e7e8q", "go depth 8", timeout=180)
        out["leaf98_d8"] = {"nodes": leaf98["nodes"], "bestmove": leaf98["bestmove"]}
    with _fresh(exe) as e:
        kqk = e.search(f"position fen {KQK}", "go depth 10", timeout=180)
        out["kqk_d10"] = {"nodes": kqk["nodes"], "bestmove": kqk["bestmove"],
                          "info_lines": kqk["info_depth_lines"]}
    return out


KIWIPETE = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"


def main():
    only = sys.argv[1:] or None
    base_tree = S.tree_sha(S.BASE)
    base_behaviour = behavioural_probe(S.BUILD)
    print("BASE behaviour:", json.dumps(base_behaviour, sort_keys=True), flush=True)
    results = []
    for name, why, fn, probe_text in MUTANTS:
        if only and name not in only:
            continue
        root = S.fresh(name)
        fn(root)
        if S.tree_sha(root) == base_tree:
            print(f"{name}: ERROR mutation had no effect"); continue
        try:
            exe = S.build(root, name)
        except Exception as exc:
            print(f"{name}: BUILD FAILED {exc}"); continue
        p = S.pins(exe)
        moved = {k: p[k]["nodes"] != S.EXPECT[k] for k in S.EXPECT}
        beh = behavioural_probe(exe)
        # `booked_moves` carries a clock-seeded RNG move, so its VALUE is noise at
        # Book Variety 30 (findings §3: 3 of 5 vary at Threads 1). The categorical
        # `book_move_lines` count is the signal; the value is excluded here and the
        # RNG is pinned separately by B4.
        NOISY = {"booked_moves"}
        changed = {k: beh[k] != base_behaviour[k] for k in beh if k not in NOISY}
        results.append({"mutant": name, "why": why, "probe": probe_text,
                        "pins": {k: p[k]["nodes"] for k in S.EXPECT},
                        "pins_all_match": not any(moved.values()),
                        "behaviour_changed": changed,
                        "behaviour": beh,
                        "verdict": ("gate-passes-a-real-change" if not any(moved.values())
                                    and any(changed.values()) else
                                    "mutant-changed-nothing" if not any(changed.values()) else
                                    "pin-moved")})
        print(f"{name:22s} pins_match={not any(moved.values())!s:5s} "
              f"behav={[k for k,v in changed.items() if v]}  verdict={results[-1]['verdict']}", flush=True)
    print(json.dumps({"base_behaviour": base_behaviour, "results": results}, indent=2))


if __name__ == "__main__":
    main()
