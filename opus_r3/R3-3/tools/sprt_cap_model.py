"""APPROX MODEL: decision probabilities of a normalized-Elo SPRT with a 1500-game (750-pair) cap.

Not fastchess figures. Normal approximation of the normalized pentanomial GSPRT, checked after every pair:
  per-pair standardized score X_i ~ N(t, 1), t = nElo * sqrt(2) * ln(10) / 800
  LLR_n = dt * S_n - n * (t1^2 - t0^2) / 2 / ... with t0 = elo0 -> t-units, t1 = elo1 -> t-units
        = (t1 - t0) * S_n - n * (t1^2 - t0^2) / 2
  bounds +-ln((1-beta)/alpha) = +-2.944 (alpha = beta = 0.05)
fastchess 1.8.2 uses the exact constrained-MLE GSPRT (forge-gate-stats skill: the normal approximation is off by
up to 0.1 LLR at H1 stops), so read these as rough expectations only.

Also prints the observed nElo needed AT the cap (750 pairs) to cross each bound, and the nElo/Elo ratio seen in
the PC ledger copy (FORGE_RESULTS.csv), so nElo can be read in Elo terms for this engine pairing.

Usage: python -I -B sprt_cap_model.py <FORGE_RESULTS.csv copy> <out.json> [paths=20000] [seed=20261027]
"""
import csv
import json
import math
import sys

import numpy as np

K = math.sqrt(2.0) * math.log(10.0) / 800.0
B = math.log(0.95 / 0.05)
PAIRS = 750


def to_t(nelo):
    return nelo * K


def simulate(elo0, elo1, theta, paths, rng):
    t0, t1, tt = to_t(elo0), to_t(elo1), to_t(theta)
    a, c = t1 - t0, (t1 * t1 - t0 * t0) / 2.0
    h1 = h0 = 0
    stop_pairs = []
    chunk = 2000
    done = 0
    while done < paths:
        n = min(chunk, paths - done)
        x = rng.standard_normal((n, PAIRS)) + tt
        s = np.cumsum(x, axis=1)
        llr = a * s - c * np.arange(1, PAIRS + 1)
        up = llr >= B
        dn = llr <= -B
        first_up = np.where(up.any(axis=1), up.argmax(axis=1), PAIRS + 1)
        first_dn = np.where(dn.any(axis=1), dn.argmax(axis=1), PAIRS + 1)
        is_h1 = (first_up < first_dn) & (first_up <= PAIRS)
        is_h0 = (first_dn < first_up) & (first_dn <= PAIRS)
        h1 += int(is_h1.sum())
        h0 += int(is_h0.sum())
        stop_pairs += list(np.minimum(np.minimum(first_up, first_dn) + 1, PAIRS))
        done += n
    return {'theta_nelo': theta, 'P_H1': round(h1 / paths, 4), 'P_H0': round(h0 / paths, 4),
            'P_cap': round(1 - (h1 + h0) / paths, 4), 'mean_games': round(2 * float(np.mean(stop_pairs)), 0)}


def cap_thresholds(elo0, elo1):
    t0, t1 = to_t(elo0), to_t(elo1)
    a, c = t1 - t0, (t1 * t1 - t0 * t0) / 2.0
    # LLR at the cap = a * PAIRS * that + ... ; solve a*PAIRS*that - c*PAIRS = +-B for that (mean t per pair)
    up = (B / PAIRS + c) / a
    dn = (-B / PAIRS + c) / a
    return round(up / K, 1), round(dn / K, 1)


def ledger_ratio(path):
    ratios = []
    with open(path, newline='', encoding='utf-8-sig') as fh:
        for r in csv.DictReader(fh):
            try:
                e, n = float(r['elo']), float(r['nelo'])
            except (KeyError, ValueError):
                continue
            if abs(e) >= 3:
                ratios.append(n / e)
    ratios.sort()
    if not ratios:
        return None
    return {'n_rows_abs_elo_ge_3': len(ratios), 'min': round(ratios[0], 2), 'median': round(ratios[len(ratios) // 2], 2),
            'max': round(ratios[-1], 2)}


def main():
    paths = int(sys.argv[3]) if len(sys.argv) > 3 else 20000
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 20261027
    rng = np.random.default_rng(seed)
    out = {'model': 'APPROX: normal approximation of the normalized GSPRT, per-pair checks, cap 750 pairs',
           'paths': paths, 'seed': seed, 'ledger_nelo_per_elo': ledger_ratio(sys.argv[1]), 'bounds': {}}
    for e0, e1 in ((0, 5), (0, 10)):
        key = f'[{e0},{e1}]'
        up, dn = cap_thresholds(e0, e1)
        rows = [simulate(e0, e1, th, paths, rng) for th in (-20, -10, -5, 0, 5, 10, 20, 30, 50)]
        out['bounds'][key] = {'observed_nelo_needed_at_cap_for_H1': up, 'for_H0': dn, 'rows': rows}
        print(key, 'needed at cap: H1 >=', up, 'nElo, H0 <=', dn, 'nElo')
        for r in rows:
            print('  ', r)
    print('ledger nElo/Elo:', out['ledger_nelo_per_elo'])
    with open(sys.argv[2], 'w', newline='\n') as fh:
        json.dump(out, fh, indent=1)


if __name__ == '__main__':
    main()
