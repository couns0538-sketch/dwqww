#!/usr/bin/env python3
"""One bounded active-UCI mutation session using the existing trusted evidence driver."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import threading
import time
from types import SimpleNamespace
import chess

root = Path("/workspace/dwqww")
trusted_path = root / 'tools/audit/run-full-engine-tt.py'
spec = importlib.util.spec_from_file_location('trusted_full_engine_tt', trusted_path)
trusted = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trusted)


class ActiveEdges(trusted.Engine):
    def send(self, command):
        authorized = (command.startswith('setoption name Threads value ') or
                      command.startswith('setoption name Hash value ') or
                      command == 'setoption name Clear Hash' or command == 'ucinewgame' or
                      command.startswith('position '))
        if self.active and authorized:
            # The trusted sender deliberately forbids these baseline scenarios.
            # Extend that driver policy only; preserve its exact byte capture.
            self.record('authorized_active_uci_edge', text=command)
            previous = self.active
            self.active = False
            try:
                super().send(command)
            finally:
                self.active = previous
        else:
            super().send(command)

    def edge(self, label, position, mutation, quit_edge=False):
        if self.active:
            raise AssertionError('previous edge was not joined')
        self.send('position ' + position)
        self.ready()
        board = chess.Board() if position == 'startpos' else chess.Board(position.removeprefix('fen '))
        item = dict(label=label, position=position, mutation=mutation, quit_edge=quit_edge,
                    completed=False, start_monotonic_ns=time.monotonic_ns())
        self.result['searches'].append(item)
        self.record('active_edge_start', **item)
        self.send('go infinite')
        self.active = True
        lines = self.until(lambda line: bool(re.match(r'^info depth .*\bnodes [1-9][0-9]*\b', line)),
                           self.args.search_timeout, label + ': first positive-node info')
        item['mutation_sent_monotonic_ns'] = time.monotonic_ns()
        self.send(mutation) # Intentionally no preceding stop/quiesce call.
        if not quit_edge:
            self.send('isready')
            lines += self.until(lambda line: line == 'readyok', self.args.stop_timeout,
                                label + ': bestmove then readiness', accept_bestmove=True)
        else:
            lines += self.until(lambda line: line.startswith('bestmove '), self.args.stop_timeout,
                                label + ': bestmove before exit', accept_bestmove=True)
            self.process.wait(timeout=self.args.quit_timeout)
        best_indices = [i for i, line in enumerate(lines) if line.startswith('bestmove ')]
        if len(best_indices) != 1:
            raise AssertionError(label + ': expected exactly one bestmove before readiness/exit')
        best_index = best_indices[0]
        if not quit_edge:
            ready_index = lines.index('readyok')
            if best_index >= ready_index:
                raise AssertionError(label + ': readiness preceded joined-search bestmove')
            item['bestmove_before_readyok'] = True
        fields = lines[best_index].split()
        if len(fields) not in (2, 4) or (len(fields) == 4 and fields[2] != 'ponder'):
            raise AssertionError(label + ': malformed bestmove')
        move = chess.Move.from_uci(fields[1])
        if move not in board.legal_moves:
            raise AssertionError(label + ': illegal bestmove against the original searched position')
        if len(fields) == 4:
            reply_board = board.copy()
            reply_board.push(move)
            if chess.Move.from_uci(fields[3]) not in reply_board.legal_moves:
                raise AssertionError(label + ': illegal ponder continuation')
        samples = []
        for line in lines:
            if line.startswith('info depth '):
                nodes = re.search(r'\bnodes ([0-9]+)\b', line)
                fullness = re.search(r'\bhashfull ([0-9]+)\b', line)
                if nodes and fullness:
                    if not 0 <= int(fullness[1]) <= 1000:
                        raise AssertionError(label + ': hashfull outside per-mille range')
                    samples.append(dict(nodes=int(nodes[1]), hashfull=int(fullness[1])))
        if not samples:
            raise AssertionError(label + ': no genuine structured search info')
        self.active = False
        item.update(completed=True, finish_monotonic_ns=time.monotonic_ns(),
                    bestmove_line=lines[best_index], legality='checked_with_python_chess',
                    node_hashfull_samples=samples, observed_lines=lines)
        self.record('active_edge_complete', label=label, bestmove=fields[1])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--session-timeout', type=float, default=90)
    args = parser.parse_args()
    engine_path = args.engine.resolve(strict=True)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    environment = os.environ.copy()
    if environment.get('TSAN_OPTIONS') != 'halt_on_error=1:exitcode=66':
        raise RuntimeError('this frozen run requires exactly the declared TSan options')
    configuration = dict(engine=str(engine_path), engine_sha256=trusted.digest(engine_path),
                         driver_sha256=trusted.digest(Path(__file__)),
                         trusted_driver_sha256=trusted.digest(trusted_path),
                         python=sys.executable, python_chess_version=chess.__version__,
                         session_timeout_seconds=args.session_timeout,
                         tsan_options=environment['TSAN_OPTIONS'], attempts=1,
                         stop_before_active_mutations=False)
    trusted.save_json(output / 'configuration.json', configuration)
    evidence = trusted.Evidence(output)
    result = dict(index=0)
    summary = dict(status='running', completed_all_scenarios=False, session=result,
                   engine_sha256_before=configuration['engine_sha256'])
    launch = SimpleNamespace(engine=engine_path, engine_arg=[], cwd=engine_path.parent,
                             environment=environment, output=output, handshake_timeout=15,
                             search_timeout=20, stop_timeout=15, quit_timeout=10)
    engine = None
    watchdog = None
    expired = threading.Event()
    started = time.monotonic_ns()
    try:
        engine = ActiveEdges(launch, evidence, 0, result)
        def kill_at_deadline():
            expired.set()
            evidence.record('hard_session_deadline_expired')
            if engine.process.poll() is None:
                engine.process.kill()
        watchdog = threading.Timer(args.session_timeout, kill_at_deadline)
        watchdog.daemon = True
        watchdog.start()
        engine.handshake() # OwnBookfalse, Ponderfalse, Hash1, Threads4.
        engine.option('Threads', 1)
        engine.edge('active1-threads4', trusted.POSITIONS[0], 'setoption name Threads value 4')
        engine.edge('active4-hash-resize', trusted.POSITIONS[1], 'setoption name Hash value 2')
        engine.edge('active4-threads1', trusted.POSITIONS[2], 'setoption name Threads value 1')
        engine.edge('active1-clear-hash', trusted.POSITIONS[1], 'setoption name Clear Hash')
        engine.edge('active1-newgame', trusted.POSITIONS[2], 'ucinewgame')
        engine.edge('active1-position', trusted.POSITIONS[1], 'position startpos moves e2e4 e7e5')
        moved = chess.Board()
        moved.push_uci('e2e4')
        moved.push_uci('e7e5')
        engine.edge('active1-stop', 'fen ' + moved.fen(), 'stop')
        engine.edge('active1-quit', trusted.POSITIONS[1], 'quit', quit_edge=True)
        result['completed'] = True
    except BaseException as failure:
        summary.update(status='failed', error=repr(failure))
    finally:
        if engine is not None:
            try:
                engine.shutdown()
            except BaseException as failure:
                summary.update(status='failed', cleanup_error=repr(failure))
        if watchdog is not None:
            watchdog.cancel()
            watchdog.join(timeout=2)
        summary['hard_deadline_expired'] = expired.is_set()
        summary['elapsed_seconds'] = (time.monotonic_ns() - started) / 1e9
        summary['engine_sha256_after'] = trusted.digest(engine_path)
        if (summary['status'] == 'running' and result.get('completed') and
                len(result.get('searches', [])) == 8 and
                all(item.get('completed') for item in result['searches']) and
                result.get('exit_code') == 0 and result.get('capture_complete') and
                result.get('sanitizer_classification') == 'none' and not expired.is_set() and
                summary['engine_sha256_before'] == summary['engine_sha256_after'] and
                not any('deadline exceeded' in line for line in result.get('cleanup', []))):
            raw_stdout = (output / 'process-00/stdout.bin').read_bytes()
            if len(re.findall(rb'(?m)^bestmove ', raw_stdout)) == 8:
                summary.update(status='passed', completed_all_scenarios=True)
            else:
                summary.update(status='failed', error='unexpected total bestmove count')
        elif summary['status'] == 'running':
            summary.update(status='failed', error='incomplete session or evidence/sanitizer failure')
        evidence.record('run_complete', status=summary['status'])
        evidence.close()
        summary['events_sha256'] = trusted.digest(output / 'events.jsonl')
        trusted.save_json(output / 'summary.json', summary)
    print(json.dumps(dict(status=summary['status'], completed=len(result.get('searches', [])),
                          error=summary.get('error'), output=str(output))))
    return 0 if summary['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
