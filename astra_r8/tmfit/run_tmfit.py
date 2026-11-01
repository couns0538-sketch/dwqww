#!/usr/bin/env python3
"""Original stdlib-only TM collection/qualification harness. Strength UNPROVEN.

Use a new output directory for each run. Engines have Threads=1 and BelowNormal
process priority; at most two engine processes exist and searches are sequential.
Legality/adjudication uses the separate Forge Board referee, not third-party code.
"""
from __future__ import annotations

import argparse
from contextlib import ExitStack
import hashlib
import json
import math
import os
from pathlib import Path
import queue
import re
import shutil
import statistics
import subprocess
import threading
import time

PINS = {11: 312866, 13: 862329, 16: 3024920, 20: 12389307, 22: 34048354}
START = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
KIWI = 'r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1'


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def order_positions(fens, seed):
    return sorted(set(fens), key=lambda fen: hashlib.sha256(f'{seed}\n{fen}'.encode()).digest())


def read_positions(path, seed):
    fens = []
    for line in Path(path).read_text(encoding='utf-8-sig').splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        fields = line.split()
        if len(fields) < 4:
            raise ValueError('Expected EPD/FEN openings')
        fen = ' '.join(fields[:4])
        fen += ' ' + ' '.join(fields[4:6]) if len(fields) >= 6 and all(x.isdigit() for x in fields[4:6]) else ' 0 1'
        fens.append(fen)
    return order_positions(fens, seed)


def resource_guard(scratch_root):
    """D scratch was authorized by user after F fell below its free-space floor."""
    root = Path(scratch_root).resolve()
    if os.name == 'nt':
        for drive, floor in [('C:/', 30e9), ('D:/', 50e9)]:
            free = shutil.disk_usage(drive).free
            if free < floor:
                raise RuntimeError(f'{drive} free={free} below {floor}')
        if root.drive.upper() == 'F:' and shutil.disk_usage('F:/').free < 50e9:
            raise RuntimeError('F: below 50 GB free')
    size = sum(p.stat().st_size for p in root.rglob('*') if p.is_file())
    if size > 5e9:
        raise RuntimeError('Task scratch exceeds 5 GB')


def is_sanitizer_report(line):
    # Catch summary-only diagnostics and shutdown/leak reports as well as the
    # usual first error line. Output is preserved in the transcript before fail.
    return any(marker in line for marker in (
        'AddressSanitizer', 'UndefinedBehaviorSanitizer', 'LeakSanitizer', 'runtime error:'))


class Process:
    def __init__(self, exe, log):
        flags = 0
        if os.name == 'nt':
            flags = subprocess.BELOW_NORMAL_PRIORITY_CLASS | subprocess.CREATE_NO_WINDOW
        self.process = subprocess.Popen([str(exe)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT, text=True, bufsize=1,
                                        encoding='utf-8', errors='replace', creationflags=flags)
        self.log = log
        self.lines = queue.Queue()
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self):
        for line in self.process.stdout:
            self.lines.put((time.perf_counter(), line.rstrip()))
        self.lines.put((time.perf_counter(), None))

    def send(self, command):
        self.log.write(f'> {command}\n')
        self.log.flush()
        self.process.stdin.write(command + '\n')
        self.process.stdin.flush()

    def until(self, predicate, timeout=30):
        deadline = time.perf_counter() + timeout
        result = []
        while True:
            try:
                stamp, line = self.lines.get(timeout=max(0.001, deadline-time.perf_counter()))
            except queue.Empty:
                raise TimeoutError('Engine response timeout') from None
            if line is None:
                raise RuntimeError(f'Process exited {self.process.poll()}')
            self.log.write(f'< {line}\n')
            if is_sanitizer_report(line):
                raise RuntimeError(f'Sanitizer report: {line}')
            result.append(line)
            if predicate(line):
                self.log.flush()
                return result, stamp
            if time.perf_counter() >= deadline:
                raise TimeoutError('Engine response timeout')

    def close(self):
        killed = False
        if self.process.poll() is None:
            try:
                self.send('quit')
                self.process.wait(timeout=10)
            except (OSError, subprocess.TimeoutExpired):
                # This is only the Popen child created by this object.
                self.process.kill()
                killed = True
                self.process.wait(timeout=10)
        self.reader.join(timeout=1)
        reports = []
        while True:
            try:
                _, line = self.lines.get_nowait()
            except queue.Empty:
                break
            if line is not None:
                self.log.write(f'< {line}\n')
                if is_sanitizer_report(line):
                    reports.append(line)
        self.log.flush()
        if reports:
            raise RuntimeError('Sanitizer report during shutdown: ' + reports[0])
        if not killed and self.process.returncode:
            raise RuntimeError(f'Child process exit status {self.process.returncode}')

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


class Engine(Process):
    def __init__(self, exe, log, mode, options):
        super().__init__(exe, log)
        try:
            self.initialize(mode, options)
        except BaseException:
            self.close()
            raise

    def initialize(self, mode, options):
        self.send('uci')
        identification, _ = self.until(lambda line: line == 'uciok')
        names = {line.split(' type ', 1)[0].removeprefix('option name ') for line in identification if line.startswith('option name ')}
        if 'TmFitModel' not in names:
            self.close()
            raise RuntimeError('TmFitModel was not advertised')
        self.options = dict(Threads='1', Hash='16', OwnBook='false', Ponder='false', TmFitModel=str(mode))
        self.options['Move Overhead'] = '20'
        self.options.update(options)
        if self.options.get('Threads') != '1' or self.options.get('Hash') != '16':
            raise ValueError('Harness requires Threads=1, Hash=16')
        for key, value in self.options.items():
            if key not in names:
                self.close()
                raise RuntimeError(f'Option not advertised: {key}')
            self.send(f'setoption name {key} value {value}')
        self.sync()

    def sync(self):
        self.send('isready')
        lines, _ = self.until(lambda line: line == 'readyok')
        if any(line.startswith('bestmove ') for line in lines):
            raise RuntimeError('Duplicate/unexpected bestmove')

    def search(self, position, command, timeout):
        self.send(position)
        self.sync()
        begin = time.perf_counter()
        self.send(command)
        lines, stamp = self.until(lambda line: line.startswith('bestmove '), timeout)
        wall_ms = (stamp-begin)*1000
        self.sync()
        move = lines[-1].split()[1]
        engine_times = [int(m[1]) for line in lines if (m := re.search(r'\btime (\d+)', line))]
        diagnostics = [json.loads(line[len('info string tmfit '):]) for line in lines if line.startswith('info string tmfit {')]
        return dict(bestmove=move, wall_ms=wall_ms, engine_ms=engine_times[-1] if engine_times else None,
                    diagnostics=diagnostics, lines=lines)


class Referee(Process):
    def state(self, command):
        self.send(command)
        lines, _ = self.until(lambda line: line.startswith('{'))
        result = json.loads(lines[-1])
        if not result['ok']:
            raise RuntimeError(f'Referee rejected {command}')
        return result


def iteration_rows(lines, game_id, search_id, final, pair_id):
    rows = []
    for line in lines:
        if line.startswith('info string tm_log {'):
            row = json.loads(line[len('info string tm_log '):])
            row.update(game_id=game_id, search_id=search_id, final_best_move=final, pair_id=pair_id, complete=True)
            rows.append(row)
    for index, row in enumerate(rows):
        row.update(search_iteration_index=index, search_iteration_count=len(rows))
    return rows


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def sanitizer_summary(games, requested_games):
    """Bounded all-ON smoke; distinct from the 200-game timing qualification."""
    all_on = bool(games) and all(g['mode'] == 1 for g in games)
    faults = sum(g['result'] in ('illegal', 'time_loss') for g in games)
    exercised = bool(games) and all(g['moves'] > 0 for g in games)
    return dict(requested_games=requested_games, all_on=all_on, exercised=exercised,
                scope='Bounded all-ON self-play; no time-normalization or playing-strength claim',
                pass_=requested_games > 0 and len(games) == requested_games and
                all_on and exercised and faults == 0)


def selfplay(args, fens, options):
    games = []
    iteration_count = 0
    run_id = hashlib.sha256(str(args.out.resolve()).encode()).hexdigest()[:16]
    with ExitStack() as stack:
        transcript = stack.enter_context((args.out / 'transcript.log').open('x', encoding='utf-8'))
        raw = stack.enter_context((args.out / 'iterations.jsonl').open('x', encoding='utf-8'))
        moves_log = stack.enter_context((args.out / 'moves.jsonl').open('x', encoding='utf-8'))
        game_log = stack.enter_context((args.out / 'games.jsonl').open('x', encoding='utf-8'))
        referee = stack.enter_context(Referee(args.referee, transcript))
        # Engines are reused within the batch but reset between games. No concurrent search.
        initial_mode = 1 if args.command == 'sanitizer' else 0
        engines = [stack.enter_context(Engine(args.exe, transcript, initial_mode, options)) for _ in range(2)]
        for game in range(args.games if args.games else 100000):
            resource_guard(args.scratch_root)
            mode = 1 if args.command == 'sanitizer' else (game % 2 if args.command == 'smoke' else args.mode)
            pair_id = game // 2 if args.command == 'smoke' else game
            fen = fens[pair_id % len(fens)]
            opening_group = hashlib.sha256(fen.encode()).hexdigest()[:16]
            game_id = f'{run_id}:{game}'
            state = referee.state('fen ' + fen)
            for engine in engines:
                engine.send(f'setoption name TmFitModel value {mode}')
                engine.send('ucinewgame')
                engine.sync()
            clocks = [float(args.base_ms), float(args.base_ms)]
            moves = []
            times = []
            result = 'ply_cap'
            for ply in range(args.max_plies):
                if state['outcome'] != 'ongoing':
                    result = state['outcome']
                    break
                side = 0 if state['fen'].split()[1] == 'w' else 1
                position = 'position fen ' + fen + (' moves ' + ' '.join(moves) if moves else '')
                command = f'go wtime {max(1,int(clocks[0]))} btime {max(1,int(clocks[1]))} winc {args.inc_ms} binc {args.inc_ms}'
                searched = engines[side].search(position, command, clocks[side]/1000 + 5)
                move = searched['bestmove']
                times.append(searched['wall_ms'])
                if move not in state['legal']:
                    result = 'illegal'
                elif searched['wall_ms'] > clocks[side]:
                    result = 'time_loss'
                record = {k: v for k, v in searched.items() if k != 'lines'}
                record.update(game_id=game_id, pair_id=opening_group, ply=ply, mode=mode, remaining_ms=clocks[side], fen=state['fen'])
                moves_log.write(json.dumps(record) + '\n')
                rows = iteration_rows(searched['lines'], game_id, ply, move, opening_group)
                for row in rows:
                    raw.write(json.dumps(row, separators=(',', ':')) + '\n')
                iteration_count += len(rows)
                if result in ('illegal', 'time_loss'):
                    break
                clocks[side] += args.inc_ms - searched['wall_ms']
                moves.append(move)
                state = referee.state('push ' + move)
            completed = dict(game=game, pair_id=pair_id, mode=mode, opening=fen, result=result,
                             moves=len(times), total_wall_ms=sum(times), mean_wall_ms=statistics.mean(times) if times else 0,
                             iterations=iteration_count)
            games.append(completed)
            game_log.write(json.dumps(completed) + '\n')
            for stream in (raw, moves_log, game_log):
                stream.flush()
            print(json.dumps(completed), flush=True)
            if args.command == 'collect' and iteration_count == 0:
                raise RuntimeError('No tm_log records: collection requires FORGE_TM_LOG build')
            if args.command == 'collect' and iteration_count >= args.min_iterations:
                break
    summary = dict(strength='UNPROVEN', games=len(games), iterations=iteration_count,
                   illegal_moves=sum(g['result'] == 'illegal' for g in games),
                   time_losses=sum(g['result'] == 'time_loss' for g in games))
    if args.command == 'smoke':
        averages = {mode: sum(g['total_wall_ms'] for g in games if g['mode'] == mode) /
                    max(1, sum(g['moves'] for g in games if g['mode'] == mode)) for mode in (0, 1)}
        ratio = averages[1] / averages[0] if averages[0] else None
        mean_game_times = {mode: statistics.mean(g['total_wall_ms'] for g in games if g['mode'] == mode)
                           for mode in (0,1) if any(g['mode'] == mode for g in games)}
        summary.update(average_ms_per_move=averages, ratio_on_off=ratio,
                       average_ms_per_game=mean_game_times,
                       game_time_ratio_on_off=mean_game_times.get(1,0)/max(1,mean_game_times.get(0,0)),
                       pass_=len(games) >= 200 and ratio is not None and abs(ratio-1) <= .03 and
                       summary['illegal_moves'] == summary['time_losses'] == 0)
    elif args.command == 'sanitizer':
        summary.update(sanitizer_summary(games, args.games))
    else:
        summary['pass_'] = iteration_count >= args.min_iterations
    write_json(args.out/'summary.json', summary)
    return summary


def live_summary(rows):
    positions = sorted({row['position'] for row in rows})
    comparisons = []
    for position in positions:
        groups = [[r['wall_ms'] for r in rows if r['position'] == position and r['mode'] == mode] for mode in (0, 1)]
        if any(len(g) != 3 or any(t is None for t in g) for g in groups):
            raise ValueError('Live proof needs three measured wall times per mode and position')
        off, on = map(statistics.median, groups)
        info_groups = [[r['engine_ms'] for r in rows if r['position'] == position and r['mode'] == mode and
                        r['engine_ms'] is not None] for mode in (0,1)]
        nonneutral = any(d['multiplier_permille'] != 1000 for r in rows if r['position'] == position and r['mode']
                         for d in r['diagnostics'])
        meaningful = abs(on-off) >= max(2, .02*off)
        comparisons.append(dict(position=position, off_ms=off, on_ms=on, changed=on != off,
                                info_off_ms=statistics.median(info_groups[0]) if info_groups[0] else None,
                                info_on_ms=statistics.median(info_groups[1]) if info_groups[1] else None,
                                nonneutral_multiplier=nonneutral, meaningful_change=meaningful,
                                qualified_change=meaningful and nonneutral))
    changed = sum(c['qualified_change'] for c in comparisons)
    diagnostic = all(r['diagnostics'] for r in rows if r['mode'])
    return dict(positions=len(positions), changed_positions=changed,
                raw_changed_positions=sum(c['changed'] for c in comparisons), comparisons=comparisons,
                on_diagnostics_present=diagnostic, **{'pass': len(positions) >= 20 and changed >= math.ceil(.3*len(positions)) and diagnostic})


def probes(args, fens, options):
    rows = []
    count = 20 if args.command == 'live' else 50
    if len(fens) < count:
        raise ValueError(f'Need at least {count} positions')
    selected = fens[:count]
    (args.out/'positions.epd').write_text('\n'.join(selected)+'\n', encoding='ascii')
    with (args.out/'transcript.log').open('x', encoding='utf-8') as transcript, (args.out/'probes.jsonl').open('x', encoding='utf-8') as raw:
        for index, fen in enumerate(selected):
            resource_guard(args.scratch_root)
            for repeat in range(3 if args.command == 'live' else 1):
                # Alternate OFF/ON order across repetitions and positions, each in fresh processes.
                modes = (0, 1) if (index+repeat)%2 == 0 else (1, 0)
                if args.command != 'live':
                    modes = (1,)
                for mode in modes:
                    settings = dict(options)
                    if args.command == 'absurd':
                        settings['TmFitA'] = str(args.absurd_a)
                        settings['TmFitLo'] = '500'
                        settings['TmFitHi'] = '1500'
                    with Engine(args.exe, transcript, mode, settings) as engine:
                        remaining = args.base_ms if args.command == 'live' else 1000
                        increment = args.inc_ms if args.command == 'live' else 10
                        result = engine.search('position fen '+fen,
                                               f'go wtime {remaining} btime {remaining} winc {increment} binc {increment}',
                                               remaining/1000 + 5)
                        row = {k: v for k, v in result.items() if k != 'lines'}
                        row.update(position=index, fen=fen, repeat=repeat, mode=mode, remaining_ms=remaining,
                                   inside_clock=result['wall_ms'] <= remaining+20)
                        # Existing max-time cap is recorded by each model diagnostic.
                        row['targets_inside_hard'] = all(d['soft_target_ms'] <= d['hard_ms'] for d in row['diagnostics'])
                        row['inside_hard_plus20'] = bool(row['diagnostics']) and all(
                            row['wall_ms'] <= d['hard_ms']+20 for d in row['diagnostics'])
                        if args.command == 'absurd':
                            row['clamp_holds'] = bool(row['diagnostics']) and all(
                                d['multiplier_permille'] == 1500 for d in row['diagnostics'])
                        raw.write(json.dumps(row)+'\n')
                        raw.flush()
                        rows.append(row)
                        print(json.dumps({k: v for k,v in row.items() if k not in ('diagnostics','fen')}), flush=True)
    if args.command == 'live':
        summary = live_summary(rows)
    else:
        summary = dict(positions=len(rows), max_wall_ms=max(r['wall_ms'] for r in rows),
                       overruns=sum(not r['inside_clock'] for r in rows),
                       hard_budget_overruns=sum(not r['inside_hard_plus20'] for r in rows),
                       targets_inside_hard=all(r['targets_inside_hard'] for r in rows),
                       diagnostics_present=all(r['diagnostics'] for r in rows))
        summary['pass'] = summary['overruns'] == summary['hard_budget_overruns'] == 0 and summary['targets_inside_hard'] and summary['diagnostics_present']
        if args.command == 'absurd':
            summary['absurd_a'] = args.absurd_a
            summary['maximum_multiplier_permille'] = max(d['multiplier_permille'] for r in rows for d in r['diagnostics'])
            summary['clamp_holds'] = all(r['clamp_holds'] for r in rows)
            summary['pass'] = summary['pass'] and summary['clamp_holds']
    summary['strength'] = 'UNPROVEN'
    write_json(args.out/'summary.json', summary)
    return summary


def bench(args, options):
    rows = []
    with (args.out/'transcript.log').open('x', encoding='utf-8') as log:
        for mode in (0, 1):
            for depth, pin in PINS.items():
                resource_guard(args.scratch_root)
                with Engine(args.exe, log, mode, options) as engine:
                    engine.send(f'bench {depth}')
                    lines, _ = engine.until(lambda x: x.startswith('info string bench depth '), 1800)
                    nodes = int(re.search(r'\bnodes (\d+)', lines[-1])[1])
                    rows.append(dict(mode=mode, depth=depth, nodes=nodes, expected=pin, **{'pass': nodes == pin}))
                    print(json.dumps(rows[-1]), flush=True)
        for fen, pin in [(START, 4865609), (KIWI, 193690690)]:
            with Engine(args.exe, log, 0, options) as engine:
                engine.send('position fen '+fen)
                engine.send('go perft 5')
                lines, _ = engine.until(lambda x: x.startswith('nodes '), 600)
                nodes = int(lines[-1].split()[1])
                rows.append(dict(perft=5, fen=fen, nodes=nodes, expected=pin, **{'pass': nodes == pin}))
    summary = dict(strength='UNPROVEN', checks=rows, **{'pass': all(r['pass'] for r in rows)})
    write_json(args.out/'summary.json', summary)
    return summary


def main():
    if os.name == 'nt':
        import ctypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.GetCurrentProcess.restype = ctypes.c_void_p
        kernel.SetPriorityClass.argtypes = (ctypes.c_void_p, ctypes.c_ulong)
        if not kernel.SetPriorityClass(kernel.GetCurrentProcess(), subprocess.BELOW_NORMAL_PRIORITY_CLASS):
            raise ctypes.WinError(ctypes.get_last_error())
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['collect','smoke','sanitizer','live','hard','absurd','bench'])
    parser.add_argument('--exe', type=Path, required=True)
    parser.add_argument('--referee', type=Path)
    parser.add_argument('--openings', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--scratch-root', type=Path, default=Path('D:/grok-pc-data/dwqww/astra8-scratch'))
    parser.add_argument('--seed', type=int, default=2026110108)
    parser.add_argument('--base-ms', type=int, default=8000)
    parser.add_argument('--inc-ms', type=int, default=80)
    parser.add_argument('--games', type=int, default=0)
    parser.add_argument('--min-iterations', type=int, default=50000)
    parser.add_argument('--max-plies', type=int, default=400)
    parser.add_argument('--mode', type=int, choices=[0,1], default=0)
    parser.add_argument('--absurd-a', type=int, default=1000000)
    parser.add_argument('--option', action='append', default=[], help='NAME=VALUE, repeated')
    args = parser.parse_args()
    args.exe = args.exe.resolve(strict=True)
    args.scratch_root = args.scratch_root.resolve(strict=True)
    args.out = args.out.resolve()
    if not args.out.is_relative_to(args.scratch_root):
        parser.error('--out must be under --scratch-root')
    if args.command in ('collect','smoke','sanitizer') and not args.referee:
        parser.error('--referee required for self-play')
    if args.command != 'bench' and not args.openings:
        parser.error('--openings EPD/FEN required')
    if args.command == 'smoke' and not args.games:
        args.games = 200
    if args.command == 'sanitizer':
        if not args.games:
            args.games = 4
        args.mode = 1
    if args.base_ms <= 0 or args.inc_ms < 0 or args.games < 0 or args.min_iterations < 1 or args.max_plies < 1:
        parser.error('Invalid time/game/iteration limits')
    options = dict(item.split('=',1) for item in args.option)
    resource_guard(args.scratch_root)
    args.out.mkdir(parents=True, exist_ok=False)
    manifest = dict(strength='UNPROVEN', command=vars(args), engine_sha256=digest(args.exe),
                    runner_sha256=digest(Path(__file__)),
                    openings_sha256=digest(args.openings) if args.openings else None,
                    referee_sha256=digest(args.referee) if args.referee else None,
                    started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
                    priority='BelowNormal' if os.name == 'nt' else 'inherited', engine_threads=1,
                    legal_validator='Forge Board; same-family, not independent implementation')
    manifest['option_file_sha256'] = {name:digest(value) for name,value in options.items()
                                    if name in ('EvalFile','NNUEFile') and Path(value).is_file()}
    manifest['command'] = {key: str(value) if isinstance(value,Path) else value for key,value in vars(args).items()}
    write_json(args.out/'manifest.json', manifest)
    try:
        fens = read_positions(args.openings,args.seed) if args.openings else []
        if args.command in ('collect','smoke','sanitizer'):
            summary = selfplay(args,fens,options)
        elif args.command == 'bench':
            summary = bench(args,options)
        else:
            summary = probes(args,fens,options)
        write_json(args.out/'sha256.json', {p.name:digest(p) for p in args.out.iterdir() if p.is_file() and p.name != 'sha256.json'})
        print(json.dumps(summary), flush=True)
        if not summary.get('pass', summary.get('pass_', False)):
            raise RuntimeError('Qualification conditions failed; see summary.json')
    except BaseException as error:
        write_json(args.out/'failure.json', dict(type=type(error).__name__, message=str(error)))
        raise


if __name__ == '__main__':
    main()
