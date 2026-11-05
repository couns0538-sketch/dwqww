#!/usr/bin/env python3
"""book_load_check.py - how long the gates' opening books take to load / parse, and whether an EPD conversion of
the PGN book would load faster (measure only; nothing is changed in the queue).

usage: python -I -B book_load_check.py [--books C:/.../8moves_v3.pgn C:/.../UHO_Lichess_4852_v1.epd] [--tmp F:/ospd/jobc/tmp]
                                       [--fastchess C:/.../fastchess.exe] [--repeats 3] [--json OUT.json] [--min-free-gb 51]

Steps (all on COPIES under --tmp; the originals are read once to copy them):
  1 copy each book to --tmp (a copy over 100 MB only when the drive keeps >= --min-free-gb free)
  2 raw read time of the copy (python, 1 MB chunks) - the floor for any parser
  3 python parse time: PGN book -> games (headers + movetext split, no move validation) ; EPD -> lines
  4 convert the PGN book to EPD with python-chess (play the moves, write the six-field FEN of each game's last
    position) -> <tmp>/<name>.epd, and time the line parse of that file
  5 fastchess's own indexing time, A/B: launch fastchess with the book copy and an exe that is not a UCI engine
    (C:/Windows/System32/whoami.exe); fastchess prints 'Indexing opening suite...', indexes the book, starts game 1 and
    dies with 'engine startup failure' when no uciok arrives, so the wall time from launch to exit minus the same run
    with a 1-line EPD is the index cost. No game is ever played. (fastchess writes its autosave config.json into --tmp.)
Reports the minimum of --repeats runs. Numbers are wall-clock seconds on the caller's CPU mask / priority.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time


def free_gb(path):
    return shutil.disk_usage(os.path.splitdrive(os.path.abspath(path))[0] + os.sep).free / 1e9


def t_read(path):
    t0 = time.perf_counter()
    n = 0
    with open(path, 'rb') as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            n += len(b)
    return time.perf_counter() - t0, n


def t_parse_pgn(path):
    """Split a PGN book into games (headers + movetext), count games and moves; no legality check."""
    t0 = time.perf_counter()
    games = 0
    moves = 0
    in_moves = False
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            if line.startswith('['):
                if in_moves:
                    in_moves = False
                continue
            s = line.strip()
            if not s:
                continue
            if not in_moves:
                games += 1
                in_moves = True
            moves += sum(1 for tok in s.split() if not tok[0].isdigit() and tok not in ('*', '1-0', '0-1', '1/2-1/2'))
    return time.perf_counter() - t0, games, moves


def t_parse_epd(path):
    t0 = time.perf_counter()
    n = 0
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            if line.strip():
                n += 1
    return time.perf_counter() - t0, n


def convert_pgn_to_epd(src, dst):
    import chess
    import chess.pgn
    t0 = time.perf_counter()
    n = 0
    with open(src, encoding='utf-8', errors='replace') as f, open(dst, 'w', encoding='utf-8', newline='\n') as out:
        while True:
            g = chess.pgn.read_game(f)
            if g is None:
                break
            b = g.board()
            for mv in g.mainline_moves():
                b.push(mv)
            out.write(b.fen() + '\n')
            n += 1
    return time.perf_counter() - t0, n


NON_UCI_EXE = 'C:/Windows/System32/whoami.exe'   # exists, exits at once, never answers 'uciok'


def t_fastchess_index(fastchess, book, fmt, tmp, repeats):
    """Wall time of fastchess from launch to exit with an exe that is not a UCI engine: fastchess prints
    'Indexing opening suite...', indexes the book, starts game 1, gets no uciok and dies ('engine startup failure').
    No game is played. (A non-existent engine path does NOT work: fastchess checks the path before indexing.)"""
    bogus = NON_UCI_EXE
    args = [fastchess, '-engine', f'cmd={bogus}', 'name=a', '-engine', f'cmd={bogus}', 'name=b', '-each', 'tc=1+0.01', 'proto=uci',
            '-openings', f'file={book}', f'format={fmt}', 'order=random', '-games', '2', '-rounds', '1', '-concurrency', '1', '-srand', '1']
    best = None
    outs = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        try:
            p = subprocess.run(args, capture_output=True, text=True, timeout=600, cwd=tmp)
            out = (p.stdout + p.stderr)[-400:]
        except subprocess.TimeoutExpired:
            out = 'TIMEOUT'
        dt = time.perf_counter() - t0
        best = dt if best is None else min(best, dt)
        outs.append(out.replace('\n', ' | ')[:200])
    return best, outs[0]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--books', nargs='+', default=['C:/Users/Administrator/grok-pc/coder-fuzz/8moves_v3.pgn',
                                                   'C:/Users/Administrator/grok-pc/coder-fuzz/UHO_Lichess_4852_v1.epd'])
    ap.add_argument('--tmp', default='F:/ospd/jobc/tmp')
    ap.add_argument('--fastchess', default='C:/Users/Administrator/grok-pc/tools/fastchess/fastchess.exe')
    ap.add_argument('--repeats', type=int, default=3)
    ap.add_argument('--min-free-gb', type=float, default=51.0)
    ap.add_argument('--json')
    a = ap.parse_args()
    if a.json and os.path.exists(a.json):
        print(f'book_load_check: {a.json} exists (never overwritten)', file=sys.stderr)
        return 2
    os.makedirs(a.tmp, exist_ok=True)
    rep = {'pc_clock': time.strftime('%Y-%m-%d %H:%M:%S'), 'books': []}
    # the 1-line EPD baseline for the fastchess A/B
    base_epd = os.path.join(a.tmp, 'one_line.epd')
    if not os.path.exists(base_epd):
        with open(base_epd, 'w', newline='\n') as f:
            f.write('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1\n')
    fc_base, fc_note = t_fastchess_index(a.fastchess, base_epd, 'epd', a.tmp, a.repeats) if os.path.exists(a.fastchess) else (None, 'no fastchess')
    rep['fastchess_baseline_1line_epd_s'] = round(fc_base, 3) if fc_base is not None else None
    rep['fastchess_baseline_output'] = fc_note
    print(f'fastchess launch-to-exit with a 1-line EPD and the non-UCI exe: {fc_base:.3f} s  ({fc_note[:120]})' if fc_base is not None else 'no fastchess')
    for src in a.books:
        name = os.path.basename(src)
        size = os.path.getsize(src)
        r = {'book': src, 'size_mb': round(size / 1e6, 1)}
        dst = os.path.join(a.tmp, name)
        if not os.path.exists(dst):
            if size > 100e6 and free_gb(a.tmp) - size / 1e9 < a.min_free_gb:
                r['skipped'] = f'copy of {size / 1e6:.0f} MB would leave the drive under {a.min_free_gb} GB free'
                rep['books'].append(r)
                print(r)
                continue
            t0 = time.perf_counter()
            shutil.copyfile(src, dst)
            r['copy_s'] = round(time.perf_counter() - t0, 3)
        r['copy'] = dst
        r['read_s'] = round(min(t_read(dst)[0] for _ in range(a.repeats)), 3)
        fmt = 'pgn' if name.lower().endswith('.pgn') else 'epd'
        if fmt == 'pgn':
            dt, games, moves = min((t_parse_pgn(dst) for _ in range(a.repeats)), key=lambda x: x[0])
            r['python_parse_s'] = round(dt, 3)
            r['games'] = games
            r['moves'] = moves
            epd = os.path.join(a.tmp, os.path.splitext(name)[0] + '.epd')
            if not os.path.exists(epd):
                dt, n = convert_pgn_to_epd(dst, epd)
                r['convert_to_epd_s'] = round(dt, 1)
                r['epd_lines'] = n
            r['epd_copy'] = epd
            r['epd_size_mb'] = round(os.path.getsize(epd) / 1e6, 2)
            r['epd_python_parse_s'] = round(min(t_parse_epd(epd)[0] for _ in range(a.repeats)), 3)
            if fc_base is not None:
                fc, note = t_fastchess_index(a.fastchess, dst, 'pgn', a.tmp, a.repeats)
                r['fastchess_index_pgn_s'] = round(fc - fc_base, 3)
                r['fastchess_pgn_output'] = note
                fc2, note2 = t_fastchess_index(a.fastchess, epd, 'epd', a.tmp, a.repeats)
                r['fastchess_index_epd_s'] = round(fc2 - fc_base, 3)
                r['fastchess_epd_output'] = note2
        else:
            dt, n = min((t_parse_epd(dst) for _ in range(a.repeats)), key=lambda x: x[0])
            r['python_parse_s'] = round(dt, 3)
            r['lines'] = n
            if fc_base is not None:
                fc, note = t_fastchess_index(a.fastchess, dst, 'epd', a.tmp, a.repeats)
                r['fastchess_index_epd_s'] = round(fc - fc_base, 3)
                r['fastchess_epd_output'] = note
        rep['books'].append(r)
        print(json.dumps(r))
    if a.json:
        with open(a.json, 'w', newline='\n') as f:
            json.dump(rep, f, indent=1)
            f.write('\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
