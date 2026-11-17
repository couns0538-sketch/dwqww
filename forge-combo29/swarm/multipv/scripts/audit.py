#!/usr/bin/env python3
"""MultiPV OUTPUT audit for forge-combo29 at base 6b98f217.

Measures the six properties the brief names, with counts stated as integers:

  1 ordering      wire order and index order, checked separately
  2 pv lengths    monotone in multipv index; and length vs the depth and seldepth printed
  3 monotonicity  scores non-increasing in multipv index, at fixed depth
  4 completeness  every index 1..N present at the final depth; N > legal moves; clock/node budgets
  5 agreement     multipv-1 line vs bestmove vs the single-PV search on the same position
  6 fast paths    book (no multipv line) and drawn root (one line) at MultiPV > 1

Every structural property is checked on EVERY depth block, not only the last, because a GUI
redraws on each block.  The final block is reported separately as well.

Counters are emitted from a script, never typed: `verify_counts.py` re-derives every integer in
FINDINGS.md from the JSON this writes.

Usage: python3 audit.py <exe> [--positions N] [--depth D] [--json out.json]
"""
import argparse
import itertools
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import chess

from multipv_lib import (Engine, bestmove_of, depth_lines, final_depth_group, score_cp)
from check_multipv import (check_bestmove, check_completeness, check_distinct_first_moves,
                           check_emission_order, check_index_order, check_pv_lengths,
                           check_pv_legal, check_pv_vs_seldepth)

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

STARTPOS = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def load_corpus(limit, seed=20261117):
    """FENs that python-chess round-trips byte for byte.

    tests_r3fu_12/positions.txt is a random-walk opening corpus already in the tree.  Part of it
    carries a stale en-passant field that python-chess rewrites, so the round-trip gate drops
    those rather than send the engine a board the sender did not mean (findings 1b).
    """
    path = os.path.join(REPO, "tests_r3fu_12", "positions.txt")
    good, dropped_ep, dropped_over = [], 0, 0
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                board = chess.Board(line)
            except ValueError:
                dropped_ep += 1
                continue
            if board.fen() != line:
                dropped_ep += 1
                continue
            if board.is_game_over():
                dropped_over += 1
                continue
            good.append(line)
    random.Random(seed).shuffle(good)
    return good[:limit], {"file": "tests_r3fu_12/positions.txt",
                          "eligible_after_gate": len(good),
                          "dropped_ep_normalised_or_invalid": dropped_ep,
                          "dropped_game_over": dropped_over}


def blocks(infos):
    """Group parsed info lines into per-depth blocks, in wire order."""
    return [(depth, list(grp)) for depth, grp in itertools.groupby(infos, key=lambda p: p["depth"])]


class Tally:
    def __init__(self):
        self.d = {}

    def add(self, key, n=1):
        self.d[key] = self.d.get(key, 0) + n

    def get(self, key):
        return self.d.get(key, 0)

    def as_dict(self):
        try:
            return dict(sorted(self.d.items()))
        except TypeError:
            return dict(sorted(self.d.items(), key=lambda kv: str(kv[0])))


def search(exe, fen, multipv, go, hash_mb=16):
    with Engine(exe=exe, hash_mb=hash_mb, multipv=multipv) as e:
        e.position(fen)
        return e.go(go)


EXAMPLES_PER_KIND = 40


def ex(res, kind, **kw):
    """Keep a per-kind sample. A global cap lets one noisy property crowd out every other."""
    n = res["example_counts"].get(kind, 0)
    res["example_counts"][kind] = n + 1
    if n < EXAMPLES_PER_KIND:
        res["examples"].append(dict(kind=kind, **kw))


# --------------------------------------------------------------------------------------------
# 1-4: structural, fixed depth
# --------------------------------------------------------------------------------------------
ZERO_IF_ABSENT = ("emission_order_violations", "index_order_violations", "pvlen_violations",
                  "pv_longer_than_depth", "pv_longer_than_seldepth", "illegal_pv_moves",
                  "duplicate_first_moves", "incomplete_blocks", "bestmove_mismatch_final",
                  "final_block_short", "printed_nodes_non_monotone_in_block",
                  "hashfull_decreases_inside_block", "line_pv_gt_depth", "no_info_lines",
                  "final_pv_len_eq_depth", "final_pv_len_ne_depth",
                  "final_block_pv_monotone", "final_block_pv_not_monotone",
                  "final_block_line1_longest", "final_block_line1_not_longest")


def audit_structural(exe, fens, mpvs, depth, res):
    t = res["structural"]
    # register every counter at 0 before measuring, so a clean run reports 0 rather than omitting
    # the key.  An absent key and a measured zero print the same in a report; only one is evidence.
    for k in ZERO_IF_ABSENT:
        t.add(k, 0)
    for fen in fens:
        legal = chess.Board(fen).legal_moves.count()
        for mpv in mpvs:
            lines = search(exe, fen, mpv, "go depth %d" % depth)
            infos = depth_lines(lines)
            bm = bestmove_of(lines)
            expected = min(mpv, legal)
            t.add("searches")
            t.add("searches:mpv%d" % mpv)
            if not infos:
                t.add("no_info_lines")
                continue
            for depth_seen, blk in blocks(infos):
                t.add("blocks")
                t.add("blocks:mpv%d" % mpv)
                for bad in check_emission_order(blk):
                    t.add("emission_order_violations")
                    ex(res, "emission_order", fen=fen, mpv=mpv, depth=depth_seen, detail=bad)
                for bad in check_index_order(blk):
                    t.add("index_order_violations")
                    ex(res, "index_order", fen=fen, mpv=mpv, depth=depth_seen, detail=bad)
                t.add("info_lines", len(blk))
                pvlen_bad, depth_bad = check_pv_lengths(blk)
                for bad in pvlen_bad:
                    t.add("pvlen_violations")
                    ex(res, "pvlen", fen=fen, mpv=mpv, depth=depth_seen, detail=bad)
                for bad in depth_bad:
                    t.add("pv_longer_than_depth")
                for bad in check_pv_vs_seldepth(blk):
                    t.add("pv_longer_than_seldepth")
                    ex(res, "pv_gt_seldepth", fen=fen, mpv=mpv, depth=depth_seen, detail=bad)
                for bad in check_pv_legal(fen, blk, chess):
                    t.add("illegal_pv_moves")
                    ex(res, "illegal_pv", fen=fen, mpv=mpv, depth=depth_seen, detail=bad)
                for bad in check_distinct_first_moves(blk):
                    t.add("duplicate_first_moves")
                    ex(res, "duplicate", fen=fen, mpv=mpv, depth=depth_seen, detail=bad)
                # node counter and hashfull behave as per-block running values
                ns = [p["nodes"] for p in blk]
                if any(b < a for a, b in zip(ns, ns[1:])):
                    t.add("printed_nodes_non_monotone_in_block")
                hf = [p["hashfull"] for p in blk]
                if len(hf) > 1 and any(b < a for a, b in zip(hf, hf[1:])):
                    t.add("hashfull_decreases_inside_block")
                missing, dupes, extra = check_completeness(blk, expected)
                if missing or dupes or extra:
                    t.add("incomplete_blocks")
                    ex(res, "incomplete", fen=fen, mpv=mpv, depth=depth_seen,
                       detail={"expected": expected, "missing": missing, "dupes": dupes,
                               "extra": extra})
                if legal < mpv:
                    t.add("blocks_where_legal_lt_requested")
            top, final = final_depth_group(infos)
            t.add("final_blocks")
            lens = [p["pv"] for p in final]
            lens = [len(p) for p in lens]
            mono = all(b <= a for a, b in zip(lens, lens[1:]))
            t.add("final_block_pv_monotone" if mono else "final_block_pv_not_monotone")
            if lens and lens[0] < max(lens):
                t.add("final_block_line1_not_longest")
            if lens and lens[0] == max(lens):
                t.add("final_block_line1_longest")
            if len(final) != expected:
                t.add("final_block_short")
                ex(res, "final_short", fen=fen, mpv=mpv, depth=top,
                   detail={"expected": expected, "got": len(final),
                           "indices": [p["multipv"] for p in final]})
            err = check_bestmove(final, bm)
            if err:
                t.add("bestmove_mismatch_final")
                ex(res, "bestmove", fen=fen, mpv=mpv, depth=top, detail=err)
            # pv length at the FINAL block against the depth it claims
            t.add("final_pv_len_eq_depth" if len(final[0]["pv"]) == top
                  else "final_pv_len_ne_depth" if final else "final_empty")
            for p in final:
                t.add("lines_checked_for_depth")
                if len(p["pv"]) > p["depth"]:
                    t.add("line_pv_gt_depth")
            res["depth_span"].append({"fen": fen, "mpv": mpv, "depth": top,
                                      "max_pv_len": max((len(p["pv"]) for p in final), default=0),
                                      "min_pv_len": min((len(p["pv"]) for p in final), default=0),
                                      "pv_lens": [len(p["pv"]) for p in final]})


def audit_controls(exe, fens, depth, res):
    """The MultiPV 1 baseline for the same properties, so each count has something to be read against.

    A property that holds at MultiPV 1 as well is not a MultiPV defect; a property that only
    breaks above 1 is.  Without this run, "49% of blocks have a PV longer than their depth" reads
    as a MultiPV bug when it is ordinary extension behaviour that MultiPV 1 shares.
    """
    c = res["controls"]
    for fen in fens:
        lines = search(exe, fen, 1, "go depth %d" % depth)
        infos = depth_lines(lines)
        c.add("searches")
        for depth_seen, blk in blocks(infos):
            c.add("blocks")
            one = blk[0]
            c.add("pv_len_gt_depth" if len(one["pv"]) > one["depth"] else "pv_len_le_depth")
            if one["seldepth"] is not None:
                c.add("pv_len_gt_seldepth" if len(one["pv"]) > one["seldepth"]
                      else "pv_len_le_seldepth")
            if one["seldepth"] is not None:
                c.add("pv_len_eq_depth" if len(one["pv"]) == one["depth"] else "pv_len_ne_depth")
        # hashfull across the whole reply: monotone at MultiPV 1?
        hf = [p["hashfull"] for p in infos]
        c.add("hashfull_monotone" if all(b >= a for a, b in zip(hf, hf[1:]))
              else "hashfull_not_monotone")
        # nodes across the whole reply
        ns = [p["nodes"] for p in infos]
        c.add("nodes_monotone" if all(b >= a for a, b in zip(ns, ns[1:]))
              else "nodes_not_monotone")


def audit_pvlen_mechanism(exe, fens, mpv, depth, res):
    """Why line 1's PV can be shorter than an alternate's, measured rather than asserted.

    The primary search reuses one transposition table across iterations, so its PV is truncated
    where a TT hit ends the line; each excluded-root alternate clears its own table before it
    runs (search.cpp: `alt_shared->tt.clear()`), so its PV runs to the nominal depth plus
    extensions.  If that is the mechanism, line 1's PV should be short in exactly the blocks where
    alternates are long, and line 1's PV should be the one closest to its own seldepth.
    """
    m = res["pvlen_mechanism"]
    for fen in fens:
        lines = search(exe, fen, mpv, "go depth %d" % depth)
        top, final = final_depth_group(depth_lines(lines))
        if len(final) < 2:
            continue
        m.add("final_blocks_with_two_lines")
        one = next(p for p in final if p["multipv"] == 1)
        alts = [p for p in final if p["multipv"] != 1]
        if not alts:
            continue
        shortest = min(len(p["pv"]) for p in final)
        longest = max(len(p["pv"]) for p in final)
        if len(one["pv"]) == shortest:
            m.add("line1_is_shortest")
        if len(one["pv"]) == longest:
            m.add("line1_is_longest")
        if len(one["pv"]) < max(len(p["pv"]) for p in alts):
            m.add("line1_shorter_than_an_alternate")
        # is the primary's PV cut at exactly its seldepth (a saturated search) or short of it?
        m.add("line1_pv_below_seldepth" if len(one["pv"]) < one["seldepth"]
              else "line1_pv_at_seldepth")
        res["pvlen_rows"].append({"fen": fen, "depth": top,
                                  "lens": {p["multipv"]: len(p["pv"]) for p in final},
                                  "seldepths": {p["multipv"]: p["seldepth"] for p in final}})


# --------------------------------------------------------------------------------------------
# 5: multipv-1 vs the single-PV search
# --------------------------------------------------------------------------------------------
def audit_agreement(exe, fens, mpv, depth, res):
    a = res["agreement"]
    for fen in fens:
        base = search(exe, fen, 1, "go depth %d" % depth)
        multi = search(exe, fen, mpv, "go depth %d" % depth)
        bm1, bmN = bestmove_of(base), bestmove_of(multi)
        top1, f1 = final_depth_group(depth_lines(base))
        topN, fN = final_depth_group(depth_lines(multi))
        a.add("positions")
        one = next((p for p in fN if p["multipv"] == 1), None)
        if not f1 or one is None:
            a.add("missing_comparable_line")
            continue
        s1 = score_cp(f1[0]["score_kind"], f1[0]["score"])
        sN = score_cp(one["score_kind"], one["score"])
        row = {"fen": fen, "depth1": top1, "depthN": topN, "bestmove1": bm1, "bestmoveN": bmN,
               "score1": s1, "scoreN": sN, "kind1": f1[0]["score_kind"],
               "kindN": one["score_kind"], "pv1": f1[0]["pv"][:6], "pvN": one["pv"][:6],
               "delta": (sN - s1) if (s1 is not None and sN is not None) else None}
        if bm1 != bmN:
            row["single_pv_move_rank_in_block"] = next(
                (p["multipv"] for p in fN if p["pv"] and p["pv"][0] == bm1), None)
            row["single_pv_move_score_in_block"] = next(
                (p["score"] for p in fN if p["pv"] and p["pv"][0] == bm1), None)
            if row["single_pv_move_rank_in_block"] is not None:
                a.add("single_pv_move_still_listed")
        if s1 != sN:
            a.add("score_differs")
        if bm1 == bmN and s1 == sN and f1[0]["pv"] == one["pv"]:
            a.add("identical_all_three")
        if bm1 == bmN:
            a.add("bestmove_same")
        else:
            a.add("bestmove_differs")
        if s1 is not None and sN is not None:
            d = abs(sN - s1)
            a.add("abs_delta:" + ("0" if d == 0 else "1-4" if d <= 4 else "5-19" if d <= 19
                                  else "20-49" if d <= 49 else "50+"))
            if sN > s1:
                a.add("multipv1_score_higher_than_single_pv")
            elif sN < s1:
                a.add("multipv1_score_lower_than_single_pv")
        if one["pv"] and bmN != one["pv"][0]:
            a.add("bestmove_ne_multipv1_pv0")
        # does the block still LIST the single-PV move, and at what rank?
        ranks = [p["multipv"] for p in fN if p["pv"] and p["pv"][0] == bm1]
        row["single_pv_move_listed_at"] = ranks
        res["agreement_rows"].append(row)


def audit_determinism(exe, fens, res):
    """Control for property 5: MultiPV 1 against itself must be bit-identical (time fields aside)."""
    d = res["determinism"]
    for fen in fens[:10]:
        a = search(exe, fen, 1, "go depth 10")
        b = search(exe, fen, 1, "go depth 10")
        keep = lambda lines: [(p["depth"], p["score_kind"], p["score"], tuple(p["pv"]), p["nodes"])
                              for p in depth_lines(lines)]
        d.add("pairs")
        d.add("identical" if keep(a) == keep(b) else "differs")
        # and MultiPV 4 against itself
        a = search(exe, fen, 4, "go depth 10")
        b = search(exe, fen, 4, "go depth 10")
        d.add("pairs_mpv4")
        d.add("identical_mpv4" if keep(a) == keep(b) else "differs_mpv4")


def audit_promotion(exe, fens, mpv, depth, res):
    """Attribute property 5's difference: is the printed multipv-1 line a PROMOTED alternate?

    The printed block is the primary search's line plus one excluded-root search per alternate,
    then stably sorted by score.  So the entry printed as `multipv 1` need not be the move the
    primary search chose; when an alternate outscores it, a different move is printed as line 1
    AND returned as bestmove.  Two consequences are measured here:

      a) how often the printed multipv-1 move differs from the single-PV best move;
      b) for those, whether the printed score survives a clean re-search of the same move, or is
         an artefact of the excluded-root context it was scored in.
    """
    p = res["promotion"]
    for fen in fens:
        base = search(exe, fen, 1, "go depth %d" % depth)
        multi = search(exe, fen, mpv, "go depth %d" % depth)
        t1, f1 = final_depth_group(depth_lines(base))
        tN, fN = final_depth_group(depth_lines(multi))
        if not f1:
            continue
        one = next((x for x in fN if x["multipv"] == 1), None)
        if one is None or not one["pv"]:
            continue
        p.add("positions")
        base_move, printed_move = f1[0]["pv"][0], one["pv"][0]
        s_base = score_cp(f1[0]["score_kind"], f1[0]["score"])
        s_print = score_cp(one["score_kind"], one["score"])
        if base_move == printed_move:
            p.add("printed_line1_is_the_primary_move")
            if s_base == s_print:
                p.add("and_same_score")
            else:
                p.add("but_different_score")
            continue
        p.add("printed_line1_is_an_alternate")
        # where does the primary's own move appear in the printed block, if at all?
        ranks = [x for x in fN if x["pv"] and x["pv"][0] == base_move]
        if ranks:
            p.add("primary_move_still_listed")
            p.add("primary_move_at_multipv_%d" % min(r["multipv"] for r in ranks))
        else:
            p.add("primary_move_not_listed")
        if s_print > s_base:
            p.add("alternate_score_higher")
        elif s_print < s_base:
            p.add("alternate_score_lower")
        else:
            p.add("alternate_score_equal")
        # (b) re-search the printed move alone, same depth, and compare with its printed score
        alone = search(exe, fen, 1, "go depth %d searchmoves %s" % (depth, printed_move))
        ta, fa = final_depth_group(depth_lines(alone))
        if not fa or not fa[0]["pv"]:
            p.add("alone_search_no_line")
            continue
        s_alone = score_cp(fa[0]["score_kind"], fa[0]["score"])
        p.add("alone_searches")
        row = {"fen": fen, "printed_move": printed_move, "printed_score": s_print,
               "primary_move": base_move, "primary_score": s_base, "alone_score": s_alone,
               "printed_minus_alone": s_print - s_alone,
               "printed_minus_primary": s_print - s_base,
               "alone_pv": fa[0]["pv"][:4], "printed_pv": one["pv"][:4],
               "pv_agrees_with_alone": one["pv"] == fa[0]["pv"]}
        res["promotion_rows"].append(row)
        if s_print == s_alone:
            p.add("printed_score_reproduced")
        else:
            p.add("printed_score_not_reproduced")
            d = abs(s_print - s_alone)
            p.add("reproduction_gap:" + ("1-4" if d <= 4 else "5-19" if d <= 19
                                        else "20-49" if d <= 49 else "50+"))
        if one["pv"] != fa[0]["pv"]:
            p.add("printed_pv_differs_from_alone_pv")
        p.add("printed_rank_is_one")


# --------------------------------------------------------------------------------------------
# 4b: completeness under a budget
# --------------------------------------------------------------------------------------------
def audit_time_pressure(exe, fens, mpv, res):
    t = res["time_pressure"]
    for fen in fens:
        expected = min(mpv, chess.Board(fen).legal_moves.count())
        for go in ("go movetime 200", "go nodes 20000"):
            lines = search(exe, fen, mpv, go)
            infos = depth_lines(lines)
            bm = bestmove_of(lines)
            t.add("searches")
            t.add("searches:" + go.split()[1])
            if not infos:
                t.add("no_info_lines")
                continue
            top, final = final_depth_group(infos)
            grp = blocks(infos)
            earlier_full = any(len(b) == expected for dd, b in grp if dd != top)
            if len(final) != expected:
                t.add("final_block_short")
                t.add("final_block_short_after_full_block" if earlier_full
                      else "final_block_short_no_earlier_full")
                res["time_rows"].append({"fen": fen, "go": go, "depth": top, "blocks": len(grp),
                                         "final_lines": len(final), "expected": expected,
                                         "indices": [p["multipv"] for p in final],
                                         "earlier_full_block": earlier_full})
            else:
                t.add("final_block_full")
            err = check_bestmove(final, bm)
            if err:
                t.add("bestmove_mismatch")
                ex(res, "bestmove_budget", fen=fen, go=go, depth=top, detail=err)
            for bad in check_index_order(final):
                t.add("final_block_index_order_violation")
            for bad in check_emission_order(final):
                t.add("final_block_emission_order_violation")
            if len(final) != expected:
                t.add("budget_cut_block")


# --------------------------------------------------------------------------------------------
# 4c: N greater than the legal move count
# --------------------------------------------------------------------------------------------
LEGAL_CASES = {
    "legal1": "8/8/8/8/8/8/1q6/K6k w - - 0 1",
    "legal2": "1q6/8/1K6/3R4/1k6/8/8/8 w - - 0 1",
    "legal3": "3q4/8/8/8/8/K2Q4/8/3k4 b - - 0 1",
    "legal4": "8/8/8/7R/1k6/8/2q4K/8 w - - 0 1",
    "legal5": "Q7/8/8/8/8/3K3q/8/2k5 w - - 0 1",
}


def audit_legal_ceiling(exe, res):
    for name, fen in LEGAL_CASES.items():
        n = chess.Board(fen).legal_moves.count()
        for mpv in (2, 6):
            for go in ("go depth 8", "go movetime 200"):
                lines = search(exe, fen, mpv, go)
                infos = depth_lines(lines)
                top, final = final_depth_group(infos)
                row = {"case": name, "fen": fen, "legal": n, "mpv": mpv, "go": go,
                       "final_depth": top, "lines_at_final": len(final),
                       "indices": [p["multipv"] for p in final],
                       "expected": min(mpv, n), "bestmove": bestmove_of(lines),
                       "multipv1_pv0": final[0]["pv"][0] if final and final[0]["pv"] else None,
                       "duplicate_first_moves": check_distinct_first_moves(final),
                       "all_depths_max_index": max((p["multipv"] for p in infos), default=0)}
                res["legal_ceiling"].append(row)
                # the engine must never claim more lines than legal moves
                if max((p["multipv"] for p in infos), default=0) > n:
                    res["legal_ceiling_overflow"].append(row)


# --------------------------------------------------------------------------------------------
# 6: the two fast paths
# --------------------------------------------------------------------------------------------
def audit_fast_paths(exe, res):
    r = res["fast_paths"]

    for mpv in (2, 3, 6):
        with Engine(exe=exe, multipv=mpv, ownbook=True) as e:
            e.position(STARTPOS)
            lines = e.go("go movetime 300")
        r.append({"case": "book", "mpv": mpv, "lines": lines,
                  "info_depth_lines": sum(1 for ln in lines if ln.startswith("info depth")),
                  "multipv_tokens": sum(1 for ln in lines if " multipv " in ln),
                  "info_string_lines": [ln for ln in lines if ln.startswith("info string")],
                  "bestmove": bestmove_of(lines)})

    # control: the SAME position with OwnBook false must search, so the book case is attributable
    for mpv in (2, 3, 6):
        with Engine(exe=exe, multipv=mpv, ownbook=False) as e:
            e.position(STARTPOS)
            lines = e.go("go movetime 300")
        r.append({"case": "book_control_ownbook_false", "mpv": mpv,
                  "info_depth_lines": sum(1 for ln in lines if ln.startswith("info depth")),
                  "multipv_tokens": sum(1 for ln in lines if " multipv " in ln),
                  "all_lines": len(lines), "bestmove": bestmove_of(lines)})

    drawn = {
        "insufficient_material": "8/8/8/4k3/8/8/4K3/8 w - - 0 1",
        "stalemate": "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1",
        "checkmate": "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3",
        "fifty_move": "4k3/8/8/8/8/8/8/4K2R w - - 100 60",
    }
    for name, fen in drawn.items():
        for mpv in (1, 3, 6):
            with Engine(exe=exe, multipv=mpv, ownbook=False) as e:
                e.position(fen)
                lines = e.go("go depth 6")
            infos = depth_lines(lines)
            r.append({"case": "drawn:" + name, "mpv": mpv, "fen": fen,
                      "info_depth_lines": len(infos),
                      "multipv_indices": sorted({p["multipv"] for p in infos}),
                      "distinct_depths": len({p["depth"] for p in infos}),
                      "pv_all_empty": all(not p["pv"] for p in infos),
                      "nodes_all_zero": all(p["nodes"] == 0 for p in infos),
                      "bestmove": bestmove_of(lines),
                      "first_line": lines[0] if lines else None})

    # a drawn root that ALSO has a book entry: which path wins (trap 19a)
    for name, fen in (("fifty_move", "4k3/8/8/8/8/8/8/4K2R w - - 100 60"),):
        with Engine(exe=exe, multipv=3, ownbook=True) as e:
            e.position(fen)
            lines = e.go("go movetime 300")
        r.append({"case": "drawn_with_book_on", "which": name, "mpv": 3, "fen": fen,
                  "info_depth_lines": sum(1 for ln in lines if ln.startswith("info depth")),
                  "multipv_tokens": sum(1 for ln in lines if " multipv " in ln),
                  "lines": lines, "bestmove": bestmove_of(lines)})

    # searchmoves restricted to one legal move, at MultiPV 3: how many lines can exist?
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    with Engine(exe=exe, multipv=3) as e:
        e.position(fen)
        lines = e.go("go depth 8 searchmoves e2e4")
    infos = depth_lines(lines)
    top, final = final_depth_group(infos)
    r.append({"case": "searchmoves_single", "mpv": 3, "fen": fen, "cmd": "go depth 8 searchmoves e2e4",
              "info_depth_lines": len(infos), "indices": [p["multipv"] for p in final],
              "lines_at_final": len(final), "bestmove": bestmove_of(lines)})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe", nargs="?", default=os.path.join(REPO, "build", "forge"))
    ap.add_argument("--positions", type=int, default=40)
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--mpv", default="2,3,4,6")
    ap.add_argument("--json")
    args = ap.parse_args()
    mpvs = [int(x) for x in args.mpv.split(",")]

    res = {"exe": args.exe, "depth": args.depth, "mpvs": mpvs, "structural": Tally(),
           "agreement": Tally(), "time_pressure": Tally(), "determinism": Tally(),
           "promotion": Tally(), "controls": Tally(), "pvlen_mechanism": Tally(),
           "examples": [], "example_counts": {}, "agreement_rows": [], "time_rows": [], "depth_span": [],
           "promotion_rows": [], "pvlen_rows": [], "legal_ceiling": [],
           "legal_ceiling_overflow": [],
           "fast_paths": []}

    fens, corpus = load_corpus(args.positions)
    res["corpus"] = dict(corpus, used=len(fens))

    print("[1-4] structural: %d positions x MPV %s at depth %d" % (len(fens), mpvs, args.depth),
          flush=True)
    audit_structural(args.exe, fens, mpvs, args.depth, res)
    print("     ", res["structural"].as_dict(), flush=True)

    print("[C] MultiPV 1 baseline (the control for every count above)", flush=True)
    audit_controls(args.exe, fens, args.depth, res)
    print("     ", res["controls"].as_dict(), flush=True)

    print("[2b] pv-length mechanism", flush=True)
    audit_pvlen_mechanism(args.exe, fens, max(mpvs), args.depth, res)
    print("     ", res["pvlen_mechanism"].as_dict(), flush=True)

    print("[5] multipv-1 vs single-PV: %d positions at MPV %d" % (len(fens), max(mpvs)),
          flush=True)
    audit_agreement(args.exe, fens, max(mpvs), args.depth, res)
    print("     ", res["agreement"].as_dict(), flush=True)

    print("[5b] promotion attribution", flush=True)
    audit_promotion(args.exe, fens, max(mpvs), args.depth, res)
    print("     ", res["promotion"].as_dict(), flush=True)

    print("[5c] determinism control", flush=True)
    audit_determinism(args.exe, fens, res)
    print("     ", res["determinism"].as_dict(), flush=True)

    print("[4b] completeness under a budget", flush=True)
    audit_time_pressure(args.exe, fens[:20], max(mpvs), res)
    print("     ", res["time_pressure"].as_dict(), flush=True)

    print("[4c] legal-move ceiling", flush=True)
    audit_legal_ceiling(args.exe, res)

    print("[6] fast paths", flush=True)
    audit_fast_paths(args.exe, res)

    out = {k: (v.as_dict() if isinstance(v, Tally) else v) for k, v in res.items()}
    if args.json:
        with open(args.json, "w") as fh:
            json.dump(out, fh, indent=1, default=str)
        print("wrote", args.json)
    else:
        print(json.dumps({k: v for k, v in out.items() if k != "examples"},
                         indent=1, default=str))


if __name__ == "__main__":
    main()
