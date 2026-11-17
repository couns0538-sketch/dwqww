#!/usr/bin/env python3
"""Aggregate the exposure runs into rates with uncertainty.

TWO RATES, TWO DIFFERENT DENOMINATORS, and quoting one as the other is the error
this seat exists to correct:

  game rate  -- games containing >=1 firing / games played. Wilson interval.
  ply  rate  -- firings per 1,000 plies, with the n that produced it.

THE PLY RATE'S INTERVAL IS THE SUBTLE PART. Consecutive plies inside one game are
not independent: a threefold that persists fires on every ply until something
changes, and a fifty-move siege fires for as long as it lasts. So the naive exact
Poisson interval over plies treats a run of dependent firings as independent evidence
and is too narrow. Both are reported:

  * naive Poisson (Garwood) over firings -- the standard interval, honest only if
    firings were independent events;
  * CLUSTER BOOTSTRAP resampling whole GAMES -- the interval to quote, because the
    game is the unit that was actually sampled.

The ratio of the two is the design effect, printed rather than hidden.
"""
from __future__ import annotations

import glob
import json
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from predicates import wilson  # noqa: E402
from scipy.stats import chi2  # noqa: E402
import os

# Evidence root: override with FORGE_EXPOSURE_ROOT. Defaults to the parent of scripts/.
ROOT = os.environ.get("FORGE_EXPOSURE_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def poisson_ci(k: int, exposure: float = 1.0) -> tuple[float, float]:
    lo = 0.0 if k == 0 else chi2.ppf(0.025, 2 * k) / 2 / exposure
    hi = chi2.ppf(0.975, 2 * (k + 1)) / 2 / exposure
    return lo, hi


def load(pattern: str) -> list[dict]:
    rows = []
    for path in sorted(glob.glob(pattern)):
        with open(path) as fh:
            d = json.load(fh)
        d["_path"] = path
        rows.append(d)
    return rows


def cluster_bootstrap(games: list[dict], reps: int = 20000, seed: int = 5) -> tuple[float, float]:
    """Percentile interval for firings/1000 plies, resampling whole games."""
    rng = random.Random(seed)
    n = len(games)
    stats = []
    for _ in range(reps):
        f = 0
        p = 0
        for _ in range(n):
            g = games[rng.randrange(n)]
            f += g["n_firings"]
            p += g["plies"]
        if p:
            stats.append(1000.0 * f / p)
    stats.sort()
    return stats[int(0.025 * reps)], stats[int(0.975 * reps)]


def summarise(runs: list[dict], label: str) -> dict:
    games_rows = [g for r in runs for g in r["rows"]]
    games = len(games_rows)
    plies = sum(g["plies"] for g in games_rows)
    firings = sum(g["n_firings"] for g in games_rows)
    with_firing = sum(1 for g in games_rows if g["n_firings"])

    rate_1000 = 1000.0 * firings / plies if plies else 0.0
    lo, hi = poisson_ci(firings, exposure=plies / 1000.0) if plies else (0.0, 0.0)
    g_lo, g_hi = wilson(with_firing, games)
    b_lo, b_hi = cluster_bootstrap(games_rows)

    return {
        "label": label,
        "runs": [r["_path"] for r in runs],
        "depth": sorted({r["depth"] for r in runs}),
        "games": games,
        "distinct_games": len({tuple(g["moves"]) for g in games_rows}),
        "plies": plies,
        "firings": firings,
        "games_with_firing": with_firing,
        "game_rate": with_firing / games if games else 0.0,
        "game_rate_ci": [g_lo, g_hi],
        "firings_per_1000_plies": rate_1000,
        "firings_per_1000_plies_ci_poisson_naive": [lo, hi],
        "firings_per_1000_plies_ci_cluster_bootstrap": [b_lo, b_hi],
        "design_effect": ((b_hi - b_lo) / (hi - lo)) if hi > lo else None,
        "plies_per_firing": (plies / firings) if firings else None,
        "mean_firings_per_firing_game": (firings / with_firing) if with_firing else None,
    }


def main() -> int:
    out = {}
    d10 = load(os.path.join(ROOT, "runs", "d10_s*.json"))
    d6 = load(os.path.join(ROOT, "runs", "d6_s*.json"))
    if d10:
        out["depth10"] = summarise(d10, "depth 10, 1000 random-prefix engine self-play games")
    if d6:
        out["depth6"] = summarise(d6, "depth 6, 500 random-prefix engine self-play games")
    both = d10 + d6
    if both:
        out["combined"] = summarise(both, "both depths pooled")
    print(json.dumps(out, indent=2))
    with open(os.path.join(ROOT, "rates.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
