#!/usr/bin/env python3
"""Final consolidated numbers for the exposure audit.

Every figure quoted in FINDINGS.md is produced here, from the raw run files, in one
pass. The point of a single consolidation script is that no sentence in the report
carries a number this script did not print -- the failure mode section 6 describes,
where a report's most load-bearing figure is the one with no automatic check.
"""
from __future__ import annotations

import collections
import glob
import json
import os
import random
import statistics
import sys

import chess
from scipy.stats import chi2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import glob_under_root, load_json, open_json_out
from predicates import wilson  # noqa: E402

# Evidence root: override with FORGE_EXPOSURE_ROOT. Defaults to the parent of scripts/.
ROOT = os.environ.get("FORGE_EXPOSURE_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def poisson_ci(k: int, exposure: float) -> tuple[float, float]:
    lo = 0.0 if k == 0 else chi2.ppf(0.025, 2 * k) / 2 / exposure
    hi = chi2.ppf(0.975, 2 * (k + 1)) / 2 / exposure
    return lo, hi


def cluster_bootstrap(games: list[dict], reps: int = 40000, seed: int = 7) -> tuple[float, float]:
    rng = random.Random(seed)
    n = len(games)
    out = []
    for _ in range(reps):
        f = p = 0
        for _ in range(n):
            g = games[rng.randrange(n)]
            f += g["n_firings"]
            p += g["plies"]
        if p:
            out.append(1000.0 * f / p)
    out.sort()
    return out[int(0.025 * reps)], out[int(0.975 * reps)]


def first_divergence(base_moves: list[str], other_moves: list[str],
                     limit: int = 1000) -> int:
    """Index of the first differing move between two move lists.

    Bounded on purpose. The lists come from JSON evidence files, so their length is
    input-controlled; an unbounded walk over file content is the "unchecked input for
    loop condition" pattern. `limit` is well above the 300-ply game cap these files are
    produced under, and a list longer than it is treated as malformed rather than
    walked indefinitely.
    """
    if not isinstance(base_moves, list) or not isinstance(other_moves, list):
        raise TypeError("move lists must be lists of UCI strings")
    n = min(len(base_moves), len(other_moves), limit)
    for i in range(n):
        if base_moves[i] != other_moves[i]:
            return i
    if len(base_moves) > limit or len(other_moves) > limit:
        raise ValueError(f"move list exceeds the {limit}-move sanity bound")
    return n


def rate_block(globs: list[str], label: str) -> dict:
    games = []
    for pat in globs:
        for path in glob_under_root(pat):
            games.extend(load_json(path)["rows"])
    n = len(games)
    plies = sum(g["plies"] for g in games)
    firings = sum(g["n_firings"] for g in games)
    with_f = sum(1 for g in games if g["n_firings"])
    distinct = len({tuple(g["moves"]) for g in games})
    lo, hi = poisson_ci(firings, plies / 1000.0)
    b_lo, b_hi = cluster_bootstrap(games)
    g_lo, g_hi = wilson(with_f, n)
    return {
        "label": label, "games": n, "distinct_games": distinct, "plies": plies,
        "firings": firings, "games_with_firing": with_f,
        "game_rate": with_f / n, "game_rate_ci": [g_lo, g_hi],
        "per_1000_plies": 1000.0 * firings / plies,
        "per_1000_plies_ci_poisson": [lo, hi],
        "per_1000_plies_ci_cluster": [b_lo, b_hi],
        "plies_per_firing": plies / firings if firings else None,
        "design_effect": (b_hi - b_lo) / (hi - lo) if hi > lo else None,
        "mean_firings_per_firing_game": firings / with_f if with_f else None,
    }


def main() -> int:
    out = {}
    out["runs"] = {
        "prod_d10_1500": rate_block([os.path.join(ROOT, "prod", "d10_s*.json")],
                                    "depth 10, 1500 games (production)"),
        "runs_d10_1000": rate_block([os.path.join(ROOT, "runs", "d10_s*.json")],
                                    "depth 10, 1000 games (independent replication)"),
        "runs_d6_500": rate_block([os.path.join(ROOT, "runs", "d6_s*.json")],
                                  "depth 6, 500 games"),
    }

    # ---- cost / move-change, from the production adjudication -------------------
    d = load_json(os.path.join(ROOT, "cost_prod.json"))
    rows = [r for r in d["rows"] if "error" not in r]

    def grp(r):
        if "insufficient" in r["reason"]:
            return "insufficient"
        if "threefold" in r["reason"]:
            return "threefold"
        return "halfmove_only"

    cost = {
        "rows": len(rows),
        "errors": sum(1 for r in d["rows"] if "error" in r),
        "base_bailed": sum(r["base_bailed"] for r in rows),
        "patched_changes_move": sum(r["patched_changes_move"] for r in rows),
        "search_changes_move": sum(r["search_changes_move"] for r in rows),
        "roots_with_mate_in_1": sum(1 for r in rows if r["mating_moves"]),
        "unique_positions": len({r["fen"] for r in rows}),
    }
    # bail-caused forced mate vs pre-existing
    bail_only = both = searched_only = 0
    for r in rows:
        if grp(r) == "insufficient":
            continue
        br = (r["costs"].get("base") or {}).get("reply_score_cp")
        nr = (r["costs"].get("nobail") or {}).get("reply_score_cp")
        if br is None or nr is None:
            continue
        if br <= -90000 and nr <= -90000:
            both += 1
        elif br <= -90000:
            bail_only += 1
        elif nr <= -90000:
            searched_only += 1
    cost["bail_caused_forced_mate"] = bail_only
    cost["both_arms_allow_mate"] = both
    cost["only_search_arm_allows_mate"] = searched_only

    for name in ("threefold", "halfmove_only"):
        vals = [r["cost_cp"] for r in rows
                if grp(r) == name and r["cost_cp"] is not None and abs(r["cost_cp"]) < 90000]
        s = sorted(vals)
        cost[name] = {
            "n": len(s), "median": statistics.median(s),
            "mean": round(statistics.mean(s), 1),
            "p75": s[(3 * len(s)) // 4], "p90": s[int(0.9 * len(s))], "max": s[-1],
            "ge_100": sum(1 for v in s if v >= 100),
            "ge_300": sum(1 for v in s if v >= 300),
            "gt_0": sum(1 for v in s if v > 0),
            "eq_0": sum(1 for v in s if v == 0),
            "lt_0": sum(1 for v in s if v < 0),
        }
    out["cost"] = cost

    # ---- mechanism: does the bail play the engine's generated head? -------------
    m = load_json(os.path.join(ROOT, "mech_prod.json")) if glob_under_root(
        os.path.join(ROOT, "mech_prod.json")) else None
    if m:
        out["mechanism"] = {"rows": len(m["rows"]), "is_head": m["is_head"],
                            "in_generated": m["in_generated"]}

    # ---- games decided -------------------------------------------------------
    if glob_under_root(os.path.join(ROOT, "pairs_s101.json")):
        p = load_json(os.path.join(ROOT, "pairs_s101.json"))
        reached = [r for r in p["rows"] if r["base_reached_firing"]]
        trans = collections.Counter((r["base_result"], r["nobail_result"]) for r in reached)
        # divergence point vs first firing
        aligned = 0
        for r in reached:
            k = first_divergence(r["base"]["moves"], r["nobail"]["moves"])
            if r["base"]["first_firing_ply"] == k:
                aligned += 1
        out["pairs"] = {
            "games": p["games"], "games_reaching_firing": len(reached),
            "changed_result": sum(1 for r in reached if not r["same_result"]),
            "decisive_to_draw": sum(v for (a, b), v in trans.items()
                                    if a in ("1-0", "0-1") and b == "1/2-1/2"),
            "draw_to_decisive": sum(v for (a, b), v in trans.items()
                                    if a == "1/2-1/2" and b in ("1-0", "0-1")),
            "cap_involved": sum(v for (a, b), v in trans.items() if a == "cap" or b == "cap"),
            "divergence_at_first_firing": aligned,
            "results_base": p["results_base"], "results_nobail": p["results_nobail"],
        }

    # ---- clustering ---------------------------------------------------------
    fired = []
    played = collections.Counter()
    total_played = 0
    for path in glob_under_root(os.path.join(ROOT, "prod", "d10_s*.json")):
        for g in load_json(path)["rows"]:
            for f in g["firings"]:
                fired.append(f)
            board = chess.Board()
            for i, u in enumerate(g["moves"]):
                board.push_uci(u)
                if i % 5 == 0:
                    played[min(len(board.piece_map()), 20) // 3 * 3] += 1
                    total_played += 1
    fire_hist = collections.Counter(min(f["material_total"] + 2, 20) // 3 * 3 for f in fired)
    n_fire = sum(fire_hist.values())
    out["clustering"] = {
        "n_firings": n_fire,
        "n_played_sampled": total_played,
        "by_pieces": {
            f"{k}-{k+2}": {
                "played_share": played[k] / total_played,
                "firing_share": fire_hist.get(k, 0) / n_fire,
                "enrichment": ((fire_hist.get(k, 0) / n_fire) / (played[k] / total_played))
                if played[k] else None,
            } for k in sorted(played)
        },
        "reasons": dict(collections.Counter(f["reason"] for f in fired)),
        "endgame_top": collections.Counter(f["endgame_type"] for f in fired).most_common(8),
        "mobility": {
            "min": min(f["legal"] for f in fired),
            "median": statistics.median([f["legal"] for f in fired]),
            "max": max(f["legal"] for f in fired),
        },
    }
    # opening-family spread
    fam = collections.defaultdict(lambda: [0, 0])
    for path in glob_under_root(os.path.join(ROOT, "prod", "d10_s*.json")):
        for g in load_json(path)["rows"]:
            key = g["prefix"][0] if g["prefix"] else "none"
            fam[key][0] += 1
            if g["firings"]:
                fam[key][1] += 1
    rates = sorted((v[1] / v[0], k, v[0], v[1]) for k, v in fam.items() if v[0] >= 50)
    out["clustering"]["opening_rate_min"] = {"rate": rates[0][0], "first_move": rates[0][1],
                                             "games": rates[0][2]}
    out["clustering"]["opening_rate_max"] = {"rate": rates[-1][0], "first_move": rates[-1][1],
                                             "games": rates[-1][2]}
    out["clustering"]["n_opening_families"] = len(rates)

    print(json.dumps(out, indent=2))
    with open_json_out(os.path.join(ROOT, "final_numbers.json")) as fh:
        json.dump(out, fh, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
