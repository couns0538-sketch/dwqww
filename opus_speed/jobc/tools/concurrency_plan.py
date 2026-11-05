#!/usr/bin/env python3
"""concurrency_plan.py - games per hour for given core counts at Threads=1 (math only, never runs a game).

usage: python -I -B concurrency_plan.py [--from-throughput throughput.json] [--sec-per-game S] [--overhead-s O]
                                        [--cores 4 6 8 12] [--caps 3000 4000 6000] [--pairs-per-check 1]

Model: at Threads=1 one game occupies one CPU slot (the two engines alternate on the clock), so games/h(C) =
C * 3600 / (seconds per game + per-game slot overhead). Both inputs are measured, not guessed: the seconds per
game come from the PGN GameDuration tags of finished gates (--from-throughput takes the medians per group of
queue_throughput.py; the 10+0.1 game length does not depend on Threads, only on the clock and the move count),
the slot overhead = 3600 * concurrency / observed games per hour - mean game duration (engine start, book
move replay, PGN writing, fastchess scheduling), measured at 0.5-1.5 s per game in the finished gates.

Two readings of "cores": physical cores (one game per core, the SMT sibling idle) keep the nodes per game of
the finished Threads=1 gates; logical CPUs (one game per SMT thread) give about 2x the games per hour at the
same wall-clock TC but every game searches fewer nodes (siblings share one core), which changes what the gate
measures (a weaker, faster engine pair) - the crew decides; this tool only prints both.
"""
import argparse
import json
import os
import sys


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--from-throughput', help='queue_throughput.py --json output: take game duration and overhead medians per group')
    ap.add_argument('--sec-per-game', type=float, help='mean seconds per game (default from --from-throughput, else 28.4 = 8moves_v3 Threads=1 median)')
    ap.add_argument('--overhead-s', type=float, help='per-game slot overhead in s (default from --from-throughput, else 0.6)')
    ap.add_argument('--cores', nargs='+', type=int, default=[2, 4, 6, 8, 12])
    ap.add_argument('--caps', nargs='+', type=int, default=[1500, 3000, 4000, 6000])
    ap.add_argument('--json')
    a = ap.parse_args()
    src = 'defaults (8moves_v3, Threads=1 conc 8 gates of 2026-10-27..29: 28.4 s per game, 0.6 s overhead)'
    sec, ovh = 28.4, 0.6
    groups = []
    if a.from_throughput:
        j = json.load(open(a.from_throughput))
        groups = j.get('groups', [])
        src = a.from_throughput
    if a.sec_per_game:
        sec = a.sec_per_game
    if a.overhead_s is not None:
        ovh = a.overhead_s
    rows = []
    print(f'inputs: {src}')
    print(f'per-game seconds (clock-bound at 10+0.1) + slot overhead: {sec:.1f} + {ovh:.1f} s per game per slot')
    print()
    print('| book / group | slot s per game | cores (one game each) | games/h | h to cap ' + ' / '.join(str(c) for c in a.caps) + ' |')
    print('|---|---|---|---|---|')
    plan_groups = [g for g in groups if g.get('mean_game_s_median')] or [{'book': 'given', 'threads': 1, 'concurrency': None,
                                                                            'mean_game_s_median': sec, 'slot_overhead_s_median': ovh, 'gates': 0}]
    for g in plan_groups:
        s = g['mean_game_s_median']
        o = g.get('slot_overhead_s_median') or ovh
        slot = s + o
        for c in a.cores:
            gph = c * 3600.0 / slot
            hours = [cap / gph for cap in a.caps]
            rows.append({'group': f"{g['book']} (measured at Threads={g['threads']} conc {g['concurrency']}, {g['gates']} gates)", 'slot_s': round(slot, 1),
                         'cores': c, 'games_per_h': round(gph, 1), 'hours_to_cap': {cap: round(h, 2) for cap, h in zip(a.caps, hours)}})
            print(f"| {rows[-1]['group']} | {slot:.1f} | {c} | {gph:.0f} | " + ' / '.join(f'{h:.1f}' for h in hours) + ' |')
    print()
    print('Reading: CPUs 4-15 of the queue = 6 physical cores (12 logical CPUs). 6 games at once keep the measured nodes per')
    print('game; 12 games at once roughly double the games/h at the same clock but each engine searches fewer nodes (SMT')
    print('siblings share a core) - a different gate, crew decision. The Threads=2 conc 4 setting of the current queue')
    print('(8 engine threads on 12 logical CPUs) measured 431-502 games/h; Threads=1 conc 8 measured 993 games/h (median).')
    if a.json:
        if os.path.exists(a.json):
            print(f'concurrency_plan: {a.json} exists (never overwritten)', file=sys.stderr)
            return 2
        with open(a.json, 'w', newline='\n') as f:
            json.dump({'inputs': src, 'rows': rows}, f, indent=1)
            f.write('\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
