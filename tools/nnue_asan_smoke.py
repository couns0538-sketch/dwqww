#!/usr/bin/env python3
"""Exercise real T1/T2 depth-10 search under caller-configured sanitizers."""
import argparse
import hashlib
import json
import re
import time
from pathlib import Path

from uci_regression import Engine


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('engine', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--int16', action='store_true', help='require the OFF-default runtime integer backend to activate')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    before = hashlib.sha256(args.engine.read_bytes()).hexdigest()
    report = {'status': 'RUNNING', 'engine': str(args.engine.resolve()), 'nnue_int16': args.int16,
              'before_sha256': before, 'searches': [], 'started_unix': time.time()}
    engine = None
    try:
        engine = Engine(args.engine)
        engine.send('uci')
        greeting = engine.until(lambda line: line == 'uciok')
        engine.send('setoption name Hash value 16')
        engine.send('setoption name OwnBook value false')
        if args.int16:
            assert 'option name NnueInt16 type check default false' in greeting
            engine.send('setoption name NnueInt16 value true')
            response = engine.until(lambda line: line.startswith('info string NnueInt16 '))
            assert response[-1] == 'info string NnueInt16 active', 'integer backend did not activate'
        positions = [
            'startpos',
            'fen r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1',
            'fen r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10',
        ]
        for threads in (1, 2):
            engine.send(f'setoption name Threads value {threads}')
            engine.ready()
            for position in positions:
                engine.send('ucinewgame')
                engine.position(position)
                engine.send('go perft 1')
                divided = engine.until(lambda line: re.fullmatch(r'nodes \d+', line) is not None)
                legal = {line.split(':', 1)[0] for line in divided
                         if re.fullmatch(r'[a-h][1-8][a-h][1-8][qrbn]?: \d+', line)}
                assert legal, 'perft did not provide legal moves'
                engine.send('go depth 10')
                lines = engine.until(lambda line: line.startswith('bestmove '), timeout=60)
                best = lines[-1].split()[1]
                depths = [int(match.group(1)) for line in lines
                          if (match := re.match(r'info depth (\d+) ', line))]
                assert best in legal, f'best move {best} outside actual legal move list'
                assert depths and max(depths) == 10, f'depth10 incomplete: {depths}'
                report['searches'].append({'threads': threads, 'position': position,
                                           'bestmove': best, 'completed_depth': max(depths),
                                           'legal_moves': len(legal)})
        engine.close()
        assert engine.process.returncode == 0, 'engine exited abnormally'
        report['actual_engine_exit'] = engine.process.returncode
        diagnostic = re.compile(r'AddressSanitizer|LeakSanitizer|UndefinedBehaviorSanitizer|runtime error:')
        assert not any(diagnostic.search(line) for line in engine.transcript), 'sanitizer diagnostic'
        assert hashlib.sha256(args.engine.read_bytes()).hexdigest() == before
        report['status'] = 'PASS'
    except Exception as error:
        report['status'] = 'FAIL'
        report['error'] = str(error)
    finally:
        if engine is not None:
            if engine.process.poll() is None:
                try:
                    engine.close()
                except Exception as error:
                    report['status'] = 'FAIL'
                    report['shutdown_error'] = str(error)
            report['actual_engine_exit'] = engine.process.returncode
            (args.out / 'uci-transcript.log').write_text('\n'.join(engine.transcript) + '\n')
        report['finished_unix'] = time.time()
        report['after_sha256'] = hashlib.sha256(args.engine.read_bytes()).hexdigest()
        (args.out / 'RESULT.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
