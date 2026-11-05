#!/usr/bin/env python3
"""queue_throughput.py - games per hour per gate and the idle gaps between consecutive gates (Job C).

usage: python -I -B queue_throughput.py [--roots F:/forge_push D:/grok-pc-data/forge_push] [--last N]
                                        [--since YYYY-MM-DD] [--match TEXT] [--csv OUT.csv] [--json OUT.json] [--md OUT.md]

Per gate (read-only): start = RUN_INFO started_pc / started (the runner's clock before the pre-gate bench),
first game start and last game end = PGN GameStartTime / GameEndTime (the newer layout) or the time stamps of
the older timestamped logs (D: layout, 'YYYY-MM-DD HH:MM:SS | ...'), games and 'Total Time' = the log's last
result block, concurrency / threads / book = RUN_INFO + the block's settings, mean game duration = PGN
GameDuration. Derived: games per hour over the game window, games per hour per concurrency slot, slot overhead
(3600 * concurrency / games_per_hour - mean game duration), setup time (first game start - runner start),
and the gap from this gate's end to the next gate's start. A gate whose log has no 'Finished match' is marked
running and left out of the gap statistics. Time stamps are the PC wall clock (the PGN zone label is ignored).
Groups (threads, concurrency, book) are summarised separately - never pooled.
"""
import argparse
import datetime
import json
import os
import re
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gatelib as gl  # noqa: E402

GS_RX = re.compile(r'^\[GameStartTime "([^"]+)"\]')
GE_RX = re.compile(r'^\[GameEndTime "([^"]+)"\]')
GD_RX = re.compile(r'^\[GameDuration "(\d+):(\d+):(\d+)"\]')
PL_RX = re.compile(r'^\[PlyCount "(\d+)"\]')
SET_RX = re.compile(r'\(([^,]+), (\d+)t, (\d+)MB, ([^)]+)\)')


def scan_pgn_times(pgn):
    """(first start, last end, n games, mean duration s, mean plies) from the tag lines only (fast on 36 MB files)."""
    first = last = None
    durs, plies, n = [], [], 0
    with open(pgn, encoding='utf-8', errors='replace') as f:
        for line in f:
            if not line.startswith('[Game') and not line.startswith('[Ply'):
                continue
            m = GS_RX.match(line)
            if m:
                t = gl.parse_time(m.group(1))
                if t and (first is None or t < first):
                    first = t
                n += 1
                continue
            m = GE_RX.match(line)
            if m:
                t = gl.parse_time(m.group(1))
                if t and (last is None or t > last):
                    last = t
                continue
            m = GD_RX.match(line)
            if m:
                durs.append(int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3)))
                continue
            m = PL_RX.match(line)
            if m:
                plies.append(int(m.group(1)))
    return first, last, n, (statistics.mean(durs) if durs else None), (statistics.mean(plies) if plies else None)


def gate_row(d):
    tag = os.path.basename(os.path.normpath(d))
    pgn, log_p, ri_p, cfg_p, res_p = gl.find_gate_files(d)
    if not log_p and not pgn:
        return None
    try:
        info = gl.load_run_info(ri_p)
    except gl.GateError:
        info = {}
    row = {'gate': tag, 'dir': d, 'layout': 'pgn' if pgn else 'log-only'}
    s = info.get('started_pc') or info.get('started')
    row['runner_start'] = gl.parse_time(s.replace(' PC', '')) if isinstance(s, str) else None
    row['concurrency'] = info.get('concurrency')
    row['threads'] = info.get('threads')
    b = info.get('book')
    row['book'] = (b.get('key') or os.path.basename(b.get('file', ''))) if isinstance(b, dict) else None
    row['cap_games'] = info.get('cap_games')
    row['sprt'] = info.get('sprt') if isinstance(info.get('sprt'), str) else None
    if row['concurrency'] is None and isinstance(info.get('settings'), str):
        m = re.search(r'concurrency (\d+)', info['settings'])
        row['concurrency'] = int(m.group(1)) if m else None
    log = None
    if log_p:
        try:
            log = gl.parse_log(log_p)
        except (OSError, ValueError):
            log = None
    block = log['block'] if log else None
    row['finished'] = bool(block and block.get('finished'))
    row['games_printed'] = block.get('games') if block else None
    row['games_logged'] = len(log['finished']) if log else None
    row['total_time_s'] = block.get('total_time_s') if block else None
    row['verdict'] = block.get('sprt_completed') if block else None
    if block and block.get('settings'):
        m = SET_RX.search('(' + block['settings'] + ')')
        if m:
            row['tc'] = m.group(1)
            row['threads'] = row['threads'] or int(m.group(2))
            row['hash_mb'] = int(m.group(3))
            row['book'] = row['book'] or m.group(4)
    row['first_game_start'] = row['last_game_end'] = None
    row['mean_game_s'] = row['mean_plies'] = None
    row['games_pgn'] = None
    if pgn:
        first, last, n, md, mp = scan_pgn_times(pgn)
        row.update(first_game_start=first, last_game_end=last, games_pgn=n, mean_game_s=md, mean_plies=mp)
    if log and log.get('first_ts') and not row['first_game_start']:
        row['first_game_start'] = gl.parse_time(log['first_ts'])
        row['last_game_end'] = gl.parse_time(log['last_ts'])
        row['time_source'] = 'timestamped log'
    elif pgn:
        row['time_source'] = 'PGN GameStartTime/GameEndTime'
    else:
        row['time_source'] = 'none'
    if not row['last_game_end'] and row['runner_start'] and row['total_time_s']:
        row['last_game_end'] = row['runner_start'] + datetime.timedelta(seconds=row['total_time_s'])
        row['time_source'] = 'runner start + Total Time'
    if not row['first_game_start']:
        row['first_game_start'] = row['runner_start']
    row['games'] = row['games_printed'] or row['games_pgn'] or row['games_logged']
    fs, le = row['first_game_start'], row['last_game_end']
    if fs and le and le > fs and row['games']:
        span_h = (le - fs).total_seconds() / 3600.0
        row['window_h'] = round(span_h, 3)
        row['games_per_h'] = round(row['games'] / span_h, 1)
        if row['concurrency']:
            row['games_per_h_per_slot'] = round(row['games_per_h'] / row['concurrency'], 2)
            row['slot_s_per_game'] = round(3600.0 * row['concurrency'] / row['games_per_h'], 1)
            if row['mean_game_s']:
                row['slot_overhead_s'] = round(row['slot_s_per_game'] - row['mean_game_s'], 1)
    if row['runner_start'] and fs and fs >= row['runner_start']:
        row['setup_s'] = int((fs - row['runner_start']).total_seconds())
    return row


def fmt_t(t):
    return t.strftime('%Y-%m-%d %H:%M:%S') if isinstance(t, datetime.datetime) else ''


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--roots', nargs='+', default=['F:/forge_push', 'D:/grok-pc-data/forge_push'])
    ap.add_argument('--last', type=int, default=0, help='only the last N gates by start time (0 = all)')
    ap.add_argument('--since', default='')
    ap.add_argument('--match', default='')
    ap.add_argument('--csv')
    ap.add_argument('--json')
    ap.add_argument('--md')
    a = ap.parse_args()
    for p in (a.csv, a.json, a.md):
        if p and os.path.exists(p):
            print(f'queue_throughput: {p} exists (never overwritten)', file=sys.stderr)
            return 2
    rows = []
    for root in a.roots:
        if not os.path.isdir(root):
            continue
        for n in sorted(os.listdir(root)):
            d = os.path.join(root, n)
            if not os.path.isdir(d) or a.match not in n:
                continue
            try:
                r = gate_row(d)
            except (OSError, ValueError) as e:
                r = {'gate': n, 'dir': d, 'error': str(e)}
            if r:
                rows.append(r)
    rows = [r for r in rows if r.get('first_game_start')]
    rows.sort(key=lambda r: r['first_game_start'])
    if a.since:
        t0 = gl.parse_time(a.since + ' 00:00:00') or gl.parse_time(a.since)
        rows = [r for r in rows if r['first_game_start'] >= t0]
    if a.last:
        rows = rows[-a.last:]
    # gaps: from this gate's end to the next gate's first game start (whatever the runner), finished gates only
    for i, r in enumerate(rows):
        r['gap_to_next_s'] = None
        if r.get('finished') and r.get('last_game_end') and i + 1 < len(rows):
            nxt = rows[i + 1]
            start = nxt.get('runner_start') or nxt['first_game_start']
            r['gap_to_next_s'] = int((start - r['last_game_end']).total_seconds())
            r['next_gate'] = nxt['gate']
    cols = ['gate', 'layout', 'first_game_start', 'last_game_end', 'games', 'concurrency', 'threads', 'book', 'window_h', 'games_per_h',
            'games_per_h_per_slot', 'mean_game_s', 'slot_overhead_s', 'setup_s', 'total_time_s', 'finished', 'gap_to_next_s', 'time_source']
    md = ['| ' + ' | '.join(cols) + ' |', '|' + '---|' * len(cols)]
    for r in rows:
        vals = []
        for c in cols:
            v = r.get(c)
            vals.append(fmt_t(v) if isinstance(v, datetime.datetime) else ('' if v is None else (f'{v:.1f}' if isinstance(v, float) else str(v))))
        md.append('| ' + ' | '.join(vals) + ' |')
    print('\n'.join(md))
    # group summary
    groups = {}
    for r in rows:
        if not r.get('games_per_h') or not r.get('finished'):
            continue
        key = (r.get('threads'), r.get('concurrency'), r.get('book'))
        groups.setdefault(key, []).append(r)
    summ = []
    for key, rs in sorted(groups.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][1]), str(kv[0][2]))):
        gph = [r['games_per_h'] for r in rs]
        per = [r['games_per_h_per_slot'] for r in rs if r.get('games_per_h_per_slot')]
        mg = [r['mean_game_s'] for r in rs if r.get('mean_game_s')]
        ov = [r['slot_overhead_s'] for r in rs if r.get('slot_overhead_s') is not None]
        summ.append({'threads': key[0], 'concurrency': key[1], 'book': key[2], 'gates': len(rs),
                     'games_per_h_median': round(statistics.median(gph), 1), 'games_per_h_min': min(gph), 'games_per_h_max': max(gph),
                     'per_slot_median': round(statistics.median(per), 2) if per else None,
                     'mean_game_s_median': round(statistics.median(mg), 1) if mg else None,
                     'slot_overhead_s_median': round(statistics.median(ov), 1) if ov else None})
    gaps = [r['gap_to_next_s'] for r in rows if r.get('gap_to_next_s') is not None]
    gap_stats = {}
    if gaps:
        gap_stats = {'n': len(gaps), 'median_s': int(statistics.median(gaps)), 'mean_s': int(statistics.mean(gaps)),
                     'negative (next started before this one ended, parallel runners)': sum(1 for g in gaps if g < 0),
                     'under_5min': sum(1 for g in gaps if 0 <= g < 300), 'over_30min': sum(1 for g in gaps if g >= 1800),
                     'sum_idle_h_of_gaps_0_to_6h': round(sum(g for g in gaps if 0 <= g <= 6 * 3600) / 3600.0, 2),
                     'big_gaps': [(r['gate'], r['next_gate'], r['gap_to_next_s']) for r in rows if (r.get('gap_to_next_s') or 0) >= 1800]}
    print('\nGroups (threads, concurrency, book) - finished gates only:')
    for s in summ:
        print(' ', s)
    print('\nGaps (this gate last game end -> next gate runner start):')
    print(' ', json.dumps(gap_stats, indent=None, default=str))
    out = {'rows': rows, 'groups': summ, 'gaps': gap_stats, 'generated_pc_clock': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    if a.json:
        with open(a.json, 'w', newline='\n') as f:
            json.dump(out, f, indent=1, default=fmt_t)
            f.write('\n')
    if a.csv:
        with open(a.csv, 'w', newline='\n') as f:
            f.write(','.join(cols) + '\n')
            for r in rows:
                f.write(','.join(fmt_t(r.get(c)) if isinstance(r.get(c), datetime.datetime) else ('' if r.get(c) is None else str(r.get(c))) for c in cols) + '\n')
    if a.md:
        with open(a.md, 'w', newline='\n', encoding='utf-8') as f:
            f.write('\n'.join(md) + '\n\nGroups:\n\n| threads | conc | book | gates | games/h median (min-max) | per slot | mean game s | slot overhead s |\n|---|---|---|---|---|---|---|---|\n')
            for s in summ:
                f.write(f"| {s['threads']} | {s['concurrency']} | {s['book']} | {s['gates']} | {s['games_per_h_median']} ({s['games_per_h_min']}-{s['games_per_h_max']}) | "
                        f"{s['per_slot_median']} | {s['mean_game_s_median']} | {s['slot_overhead_s_median']} |\n")
            f.write('\nGaps: ' + json.dumps(gap_stats, default=str) + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
