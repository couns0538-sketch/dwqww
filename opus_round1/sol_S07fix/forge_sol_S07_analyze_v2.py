#!/usr/bin/env python3
"""S07-1 / S07-2 analysis: read the screens of forge_sol_S07_wac_interleave_v2.py runs and Sol's official 271 run
(raw stdout + result.json from his native evidence archive) and write one table of score vs search effort.
For every screen: movetime, engine, score, median nodes per position (last info line before bestmove), median
nps, mean depth, CPU busy % of the PC during the screen. Per (movetime, engine): mean, range, scores. Position
level: which positions flip between repeats, and the positions Sol's 271 run missed that the PC 1000 ms lock
runs solved (and the other way round). The official 271 is quoted, never replaced.
usage: forge_sol_S07_analyze_v2.py --runs RUN_DIR [RUN_DIR ...] --sol-wac-dir SOL_DIR --out OUT.json [--md OUT.md]"""
import argparse
import importlib.util
import json
from pathlib import Path
import statistics

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('drv', HERE / 'forge_sol_S07_wac_interleave_v2.py')
drv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(drv)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--runs', nargs='+', type=Path, required=True)
    ap.add_argument('--sol-wac-dir', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--md', type=Path)
    args = ap.parse_args()
    screens = []
    for run in args.runs:
        for line in (run / 'screens.jsonl').read_text(encoding='utf-8').splitlines():
            s = json.loads(line)
            s['run_dir'] = run.name
            screens.append(s)
    sol_result = json.loads((args.sol_wac_dir / 'result.json').read_text())
    sol_stats = drv.search_stats(next(args.sol_wac_dir.glob('*_wac300_fixedtime.stdout')))
    sol_solved = {r['id'] for r in sol_result['results'] if r['bestmove_allowed']}
    rows = [{'source': 'Sol official (Linux Xeon 8573C, CPU 4, nice 19)', 'movetime_ms': sol_result['movetime_ms'],
             'engine': 'L build e3df99cd (h256_e12 lock source, bench 308972)', 'score': sol_result['solved'],
             'median_nodes': sol_stats['median_nodes'], 'median_nps': sol_stats['median_nps'],
             'median_time_ms': sol_stats['median_time_ms'], 'total_nodes': sol_stats['total_nodes'],
             'mean_depth': sol_stats['mean_depth'], 'cpu_busy_pct': None}]
    for s in screens:
        rows.append({'source': f"PC {s['run_dir']}/{s['screen']}", 'movetime_ms': s['movetime_ms'], 'engine': s['arm'],
                     'score': s['solved'], 'median_nodes': (s['search'] or {}).get('median_nodes'),
                     'median_nps': (s['search'] or {}).get('median_nps'),
                     'median_time_ms': (s['search'] or {}).get('median_time_ms'),
                     'total_nodes': (s['search'] or {}).get('total_nodes'),
                     'mean_depth': (s['search'] or {}).get('mean_depth'),
                     'cpu_busy_pct': s['cpu_busy_pct']['mean']})
    groups = {}
    for s in screens:
        groups.setdefault((s['movetime_ms'], s['arm']), []).append(s)
    summary = []
    for (mt, arm), items in sorted(groups.items()):
        scores = [s['solved'] for s in items]
        nodes = [s['search']['median_nodes'] for s in items]
        solved_sets = [set(s['solved_ids']) for s in items]
        always = set.intersection(*solved_sets)
        ever = set.union(*solved_sets)
        summary.append({'movetime_ms': mt, 'engine': arm, 'screens': len(items), 'scores': scores,
                        'mean': round(statistics.fmean(scores), 2), 'range': max(scores) - min(scores),
                        'median_nodes_per_position': statistics.median(nodes),
                        'flipping_positions': sorted(ever - always),
                        'pc_solved_always_sol_missed': sorted(always - sol_solved),
                        'sol_solved_pc_missed_always': sorted(sol_solved - ever)})
    result = {'rows': rows, 'summary': summary, 'sol_stats': sol_stats,
              'historical_reference': {'h256_e12 lock at 1000 ms, saved Coder artifact rescored by Sol': 283,
                                       'CR different-net candidates': '286 / 287',
                                       'source': "Sol's forge_sol_S07_WAC_comparability_audit_20261026.json"}}
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    if args.md:
        lines = ['| Source | Movetime | Engine | Score | Median nodes/position | Total nodes | Median time ms | '
                 'Median nps | Mean depth | PC CPU busy % |',
                 '|---|---:|---|---:|---:|---:|---:|---:|---:|---:|']
        for r in rows:
            lines.append(f"| {r['source']} | {r['movetime_ms']} | {r['engine']} | {r['score']} | {r['median_nodes']} | "
                         f"{r['total_nodes']} | {r['median_time_ms']} | {r['median_nps']} | {r['mean_depth']} | "
                         f"{r['cpu_busy_pct']} |")
        lines += ['', '| Movetime | Engine | Scores | Mean | Range | Median nodes/position | Flipping positions |',
                  '|---:|---|---|---:|---:|---:|---|']
        for g in summary:
            lines.append(f"| {g['movetime_ms']} | {g['engine']} | {g['scores']} | {g['mean']} | {g['range']} | "
                         f"{g['median_nodes_per_position']} | {len(g['flipping_positions'])} |")
        args.md.write_text('\n'.join(lines) + '\n')
    for g in summary:
        print(json.dumps({k: v for k, v in g.items() if not isinstance(v, list) or k == 'scores'}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
