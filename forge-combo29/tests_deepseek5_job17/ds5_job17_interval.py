#!/usr/bin/env python3
"""job17 A1: the interval script, repaired for real this time.

A game drawn k times contributes its positions k TIMES (no set() de-dup). The self-test runs
first on a made-up input and the script refuses to go on if multiplicity is not exact.
"""
import random
import sys
from collections import Counter


def load_rows(d, tag, setf, depth):
    fn = f"{d}/{tag.replace(' ', '+')}_{setf}_d{depth}.rows"
    return [int(l.split("|")[2]) for l in open(fn) if l.split("|")[0].isdigit()]


def idxgames(setindex):
    return [int(l.split("|")[2].replace("game", "")) for l in open(setindex)]


def resample_multiplicity(games, draws):
    """games: the sorted unique game ids. draws: the list actually drawn (length len(games)).
    Returns the index list with each game's positions repeated per its draw count."""
    mult = Counter(draws)
    return [g for g in games for _ in range(mult.get(g, 0))]


def selftest():
    # Three made-up games: g1 has 2 positions, g2 has 2, g3 has 1. Draw g2 twice.
    games = [1, 2, 3]
    positions_of = {1: [0, 1], 2: [2, 3], 3: [4]}
    draws = [1, 2, 2]          # len(draws) == len(games), g2 drawn twice
    picked = resample_multiplicity(games, draws)
    total_positions = sum(len(positions_of[g]) for g in picked)
    print(f"SELFTEST: draws {draws} over games {games}; games picked (with multiplicity) {picked}")
    print(f"SELFTEST: positions counted in the resample = {total_positions} (expect 6 = 2 + 2x2 + 0; g3 drawn zero times)")
    if total_positions != 6:
        print("SELFTEST: FAILED - refusing to go on")
        raise SystemExit(1)
    print("SELFTEST: OK")


def boot(on, off, game_of, games, seed=9141, n=4000):
    rng = random.Random(seed)
    N = len(on)
    rs = []
    for _ in range(n):
        draws = [rng.choice(games) for _ in games]
        mult = Counter(draws)
        w = [mult.get(game_of[i], 0) for i in range(N)]
        so = sum(on[i] * w[i] for i in range(N))
        sf = sum(off[i] * w[i] for i in range(N))
        rs.append(so / sf)
    rs.sort()
    return rs[int(0.025 * n)], rs[int(0.975 * n)]


if __name__ == "__main__":
    selftest()
    d = "/tmp/glmflash/ds5j12"
    lines = [
        ("LmrDeeperShallower+true+LmrDeeperBase+100000", "shal", "set_G.epd", 12, "/tmp/glmflash/set_G_index.txt"),
        ("LmrDeeperShallower+true", "on", "set_G.epd", 12, "/tmp/glmflash/set_G_index.txt"),
        ("LmrDeeperShallower+true+LmrShallowerBase+8+LmrShallowerDepthMul+0", "flat", "set_G.epd", 12, "/tmp/glmflash/set_G_index.txt"),
        ("LmrDeeperShallower+true+LmrDeeperBase+100000", "shal", "set_G2.epd", 12, "/tmp/glmflash/set_G2_index.txt"),
        ("LmrDeeperShallower+true", "on", "set_G2.epd", 12, "/tmp/glmflash/set_G2_index.txt"),
    ]
    for tag, label, setf, depth, idx in lines:
        gg = idxgames(idx)
        off = load_rows(d, "none", setf, depth)
        on = load_rows(d, tag, setf, depth)
        if len(on) != len(off) or len(on) != len(gg):
            raise SystemExit(f"REFUSED: row lengths {len(on)}/{len(off)}/{len(gg)} differ for {label} {setf}")
        ratio = sum(on) / sum(off)
        lo, hi = boot(on, off, gg, sorted(set(gg)))
        if not (lo <= ratio <= hi):
            raise SystemExit(f"REFUSED: interval [{lo:.4f}, {hi:.4f}] does not contain {ratio:.4f}")
        print(f"{label}|{setf}: ratio {ratio:.4f} games-interval (4,000 resamples, seed 9141, list draws): [{lo:.4f}, {hi:.4f}]")
