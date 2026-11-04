"""Deterministic legal-path qualification of the boundary filters only."""
import argparse
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
import random
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parent))
import r14_boundary as core
from r14_boundary_run import _publish
from r14_segments import Guard
from r14_qualification.qualify import hashes,resource_guard
from run_policy import safe_path

SPECIAL = [
    ('white_castle','r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 7 15',['e1g1','e8c8']),
    ('black_castle','r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 7 15',['e8g8','e1c1']),
    ('white_ep','4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 2',['e5d6','e8f7']),
    ('black_ep','4k3/8/8/8/3Pp3/8/8/4K3 b - d3 0 2',['e4d3','e1f2']),
    ('promotion_capture','1r2k3/P7/8/8/8/8/7p/4K3 w - - 0 10',['a7b8q','e8f7']),
    ('black_promotion','4k3/8/8/8/8/8/7p/4K3 b - - 0 10',['h2h1n','e1d2']),
]


def check_path(start,target):
    endpoints = [core.parse_endpoint((board.fen(en_passant='fen')+' | 0 | 0.5').encode(),source,1)
                 for board,source in ((start,12),(target,13))]
    return core.count_candidates(core.Population([endpoints[0]]),core.Population([endpoints[1]]))['survivors'] == 1


def random_path(source,depth,rng):
    """Return features only for a path that reaches its requested depth."""
    if type(depth) is not int or not 1 <= depth <= 8:
        raise ValueError('requested path depth must be 1..8')
    target = source.copy()
    witness,features = [],Counter()
    for _ in range(depth):
        moves = list(target.legal_moves)
        if not moves:
            return None
        move = rng.choice(moves)
        if target.is_capture(move):
            features['random_capture_moves'] += 1
        if move.promotion:
            features['random_promotion_moves'] += 1
        witness.append(move.uci())
        target.push(move)
    return target,witness,dict(features)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--pairs',type=int,default=100000)
    parser.add_argument('--seed',type=int,default=141103)
    parser.add_argument('--cpu',type=int,default=3)
    parser.add_argument('--seconds',type=float,default=900)
    args = parser.parse_args(argv)
    if args.pairs < 1:
        raise ValueError('positive requested pair count required')
    guard = Guard(args.seconds,args.cpu)
    out = safe_path(args.out,write=True)
    resource_guard(reserve_bytes=1024**2)
    out.mkdir(parents=True,exist_ok=False)
    identities = [hashes(path) for path in (Path(core.__file__),Path(__file__),
                  Path(__file__).with_name('r14_boundary_run.py'),Path(sys.executable),
                  Path(core.chess.__file__),Path(core.np.__file__))]
    report = dict(schema=1,status='UNVERIFIED',complete=False,core=identities[0],tool_identities=identities,
                  scope='boundary_filter_qualification' if args.pairs >= 100000 else 'boundary_filter_smoke',
                  requested_random_pairs=args.pairs,resolved_random_pairs=0,rejected_legal_pairs=0,
                  special_pairs=0,special_failures=0,popcount_checks=0,popcount_disagreements=0,
                  per_depth={},seed=args.seed,failures=[],reasons=[],
                  feature_coverage_scope='completed verified random pairs and verified special-path prefixes',
                  start_vienna=datetime.now().strftime('%Y-%m-%d %H:%M:%S Vienna'))
    began,last_progress = time.monotonic(),0.0
    depths,coverage = Counter(),Counter()
    rng = random.Random(args.seed)
    try:
        for begin in range(0,args.pairs,4096):
            guard()
            words = [rng.getrandbits(64) for _ in range(min(4096,args.pairs-begin))]
            actual = core.np.bitwise_count(core.np.array(words,dtype=core.np.uint64)).tolist()
            disagreements = sum(value.bit_count() != observed for value,observed in zip(words,actual))
            if len(actual) != len(words):
                raise RuntimeError('popcount output cardinality mismatch')
            report['popcount_checks'] += len(words)
            report['popcount_disagreements'] += disagreements
            if disagreements:
                raise RuntimeError('popcount disagrees with scalar integer oracle')
        for family,fen,tokens in SPECIAL:
            start = core.chess.Board(fen)
            target = start.copy()
            for token in tokens:
                move = core.chess.Move.from_uci(token)
                if move not in target.legal_moves:
                    raise RuntimeError('invalid qualification fixture move')
                target.push(move)
                report['special_pairs'] += 1
                if not check_path(start,target):
                    report['special_failures'] += 1
                    report['failures'].append(dict(family=family,start=fen,target=target.fen(en_passant='fen')))
                    raise RuntimeError('legal special path was excluded')
                coverage[family] += 1
        source = core.chess.Board()
        while report['resolved_random_pairs'] < args.pairs:
            if report['resolved_random_pairs'] % 256 == 0:
                guard()
            if source.is_game_over() or source.ply() >= 240:
                source = core.chess.Board()
            source.push(rng.choice(list(source.legal_moves)))
            depth = 1+report['resolved_random_pairs']%8
            sampled = random_path(source,depth,rng)
            if sampled is None:
                continue
            target,witness,features = sampled
            if not check_path(source,target):
                report['rejected_legal_pairs'] += 1
                report['failures'].append(dict(start=source.fen(en_passant='fen'),target=target.fen(en_passant='fen'),
                                               witness=witness,depth=depth))
                raise RuntimeError('random legal path was excluded')
            report['resolved_random_pairs'] += 1
            coverage.update(features)
            depths[str(depth)] += 1
            coverage['source_white' if source.turn else 'source_black'] += 1
            if source.halfmove_clock:
                coverage['nonzero_start_clock'] += 1
            now = time.monotonic()
            if now-last_progress >= 30:
                print(json.dumps(dict(stage='random_paths',resolved=report['resolved_random_pairs'],
                                      requested=args.pairs,elapsed_seconds=now-began)),flush=True)
                last_progress = now
        report['complete'] = True
    except Exception as error:
        report['reasons'].append(f'{type(error).__name__}: {error}')
    finally:
        stable = True
        for identity in identities:
            try:
                stable = stable and hashes(identity['path']) == identity
            except Exception as error:
                stable = False
                report['reasons'].append(f'identity read: {type(error).__name__}: {error}')
        if not stable:
            report['complete'] = False
            report['reasons'].append('candidate or runtime identity changed')
        failures = report['rejected_legal_pairs']+report['special_failures']+report['popcount_disagreements']
        if stable and failures:
            report['status'] = 'FAIL'
        elif stable and report['complete']:
            if args.pairs >= 100000:
                report['status'] = 'PASS'
            else:
                report['smoke_status'] = 'PASS'
        report.update(per_depth=dict(depths),coverage=dict(coverage),elapsed_seconds=time.monotonic()-began,
                      end_vienna=datetime.now().strftime('%Y-%m-%d %H:%M:%S Vienna'))
        try:
            _publish(out/'REPORT.json',report)
        except Exception as error:
            print(json.dumps(dict(status='UNVERIFIED',complete=False,publication_error=str(error))),flush=True)
            return 2
        print(json.dumps(dict(status=report['status'],complete=report['complete'],resolved=report['resolved_random_pairs'],
                              report=str(out/'REPORT.json'))),flush=True)
    return 0 if report['complete'] and not failures else 2


if __name__ == '__main__':
    raise SystemExit(main())
