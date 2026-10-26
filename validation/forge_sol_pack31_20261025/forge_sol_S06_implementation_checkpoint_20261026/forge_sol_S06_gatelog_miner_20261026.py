"""Offline original Forge gate miner. No engine execution or adoption decisions."""
from __future__ import annotations
import argparse
import csv
import datetime
import hashlib
import io
import json
import math
from pathlib import Path
import re
import sys

from forge_sol_S06_statistics_20261026 import summarize_pentanomial
from forge_sol_S06_pgn_20261026 import mine_pgn
from forge_sol_S06_logs_20261026 import mine_log

STAMP = '20261026'
MAX_INPUT = 64 * 1024 * 1024
PRODUCTS = ('gatelog_miner', 'statistics', 'pgn', 'logs')


def _finite_float(value):
    x = float(value)
    if not math.isfinite(x):
        raise ValueError('number must be finite')
    return x


def _nonnegative_int(value):
    if not re.fullmatch(r'[0-9]+', value):
        raise ValueError('count must be a nonnegative integer')
    return int(value)


def _csv_triage(text):
    reader = csv.DictReader(io.StringIO(text.lstrip('\ufeff'), newline=''))
    fields = reader.fieldnames
    if not fields or 'gate' not in fields or len(fields) != len(set(fields)):
        raise ValueError('CSV requires unique headers including gate (UTF-8 BOM supported)')
    rows, issues, seen = [], [], set()
    for number, raw in enumerate(reader, 2):
        problems = []
        gate = raw.get('gate') or ''
        if not gate or gate in seen:
            problems.append('missing or duplicate gate identity; rows never pooled')
        seen.add(gate)
        if None in raw or any(value is None for value in raw.values()):
            problems.append('CSV row/header field count mismatch')
        n, wdl, point, llr, concurrency, bounds = None, None, None, None, None, None
        try:
            if any(raw.get(k) for k in ('W', 'D', 'L', 'games')):
                n = _nonnegative_int(raw.get('games') or '')
                wdl = [_nonnegative_int(raw.get(k) or '') for k in ('W', 'D', 'L')]
                if sum(wdl) != n:
                    problems.append('W/D/L sum differs from reported games')
                if n and sum(wdl) == n:
                    score = (wdl[0] + wdl[1]/2)/n
                    if 0 < score < 1:
                        point = 400 * math.log10(score/(1-score))
            if raw.get('llr'):
                llr = _finite_float(raw['llr'])
            if raw.get('conc'):
                concurrency = _nonnegative_int(raw['conc'])
                if concurrency == 0:
                    problems.append('concurrency must be positive when supplied')
            if raw.get('sprt_bounds'):
                m = re.fullmatch(r'\[\s*([^,]+)\s*,\s*([^,]+)\s*\]', raw['sprt_bounds'])
                if not m:
                    raise ValueError('unsupported hypothesis bounds')
                bounds = [_finite_float(x) for x in m.groups()]
                if bounds[0] >= bounds[1]:
                    problems.append('hypothesis bounds must be increasing')
        except (ValueError, TypeError, OverflowError) as exc:
            problems.append(str(exc))
        row = {'row': number, 'gate': gate, 'status': 'BLOCKED' if problems else 'UNVERIFIED',
               'raw': raw, 'games': n, 'wdl': wdl, 'elo_descriptive': point,
               'reported_llr': llr, 'reported_bounds': bounds, 'concurrency': concurrency,
               'pentabins': None, 'acceptance_verified': False, 'issues': problems,
               'unverified': ['paired counts and original PGN/log', 'paired Elo uncertainty',
                              'native likelihood/acceptance', 'input/build/protocol integrity',
                              'actual TL/crash and opening/phase splits'],
               'triage': 'REPAIR_METADATA' if problems else ('REQUEST_PAIRED_RAW_EVIDENCE' if n else 'NO_PLAYED_COUNTS')}
        rows.append(row)
        issues.extend(f'row {number}: {x}' for x in problems)
    if not rows:
        raise ValueError('CSV contains no gate rows')
    return {'status': 'BLOCKED' if issues else 'UNVERIFIED', 'rows': rows, 'issues': issues,
            'scope': 'Historical source-reported metadata only; no pooling, gate/confirm/lock acceptance or current live status.'}


def _statistics(args, counts):
    return summarize_pentanomial(counts, e0=args.e0, e1=args.e1, units=args.units,
                                alpha=args.alpha, beta=args.beta)


def _mine(args, inputs):
    if not (args.pgn or args.log):
        raise ValueError('mine requires --pgn and/or --log')
    if not args.gate_id.strip():
        raise ValueError('gate-id must be nonempty')
    pgn = mine_pgn(inputs['pgn']['text'], args.candidate, args.baseline,
                   pairing=args.pairing, phase_tag=args.phase_tag) if args.pgn else None
    log = mine_log(inputs['log']['text'], args.candidate, args.baseline) if args.log else None
    issues, comparisons, by_pool = [], [], []
    if pgn:
        if not pgn['paired']['aggregate_eligible']:
            issues.append('PGN outcome/pair screen is not eligible; all records retained')
        for pool in pgn['pools']:
            by_pool.append({'pool': pool['id'], 'metadata': pool['metadata'],
                            'statistics': _statistics(args, pool['paired']['pentabins']),
                            'outcome_screen_eligible': pool['paired']['aggregate_eligible']})
    if log and log['status'] == 'BLOCKED':
        issues.append('log observations contain faults or integrity issues')
    if pgn and log:
        wdl = [pgn['raw'][key] for key in ('W', 'D', 'L')]
        for label, left, right in (
            ('games', pgn['raw']['games'], log['reported']['games']),
            ('wdl', wdl, log['reported']['wdl']),
            ('pentabins', pgn['paired']['pentabins'], log['reported']['pentabins'])):
            state = 'UNVERIFIED' if left is None or right is None else ('PASS' if left == right else 'FAIL')
            comparisons.append({'field': label, 'status': state, 'pgn': left, 'log': right})
            if state == 'FAIL':
                issues.append(f'PGN/log {label} mismatch; no favorable subset selected')
    native_llr = log['reported']['llr'] if log else None
    llr_comparison = {'status': 'UNVERIFIED', 'model': 'approximate Gaussian vs reported native observation',
                      'difference': None, 'note': 'A difference is not an exact Fastchess likelihood failure.'}
    if len(by_pool) == 1 and native_llr and native_llr['value'] is not None:
        calculated = by_pool[0]['statistics']['gaussian_llr']['value']
        if calculated is not None:
            llr_comparison.update(status='DESCRIPTIVE_ONLY', difference=calculated-native_llr['value'])
    return {'status': 'BLOCKED' if issues else ('OUTCOME_CHECKS_PASS' if pgn else 'UNVERIFIED'),
            'gate_id_declared': args.gate_id, 'pgn': pgn, 'log': log,
            'statistics_by_pool': by_pool,
            'reconciliation': {'comparisons': comparisons, 'issues': issues},
            'llr_comparison': llr_comparison,
            'unverified': ['engine source/build/binary binding', 'move legality',
                           'frozen protocol and stopping rule', 'original gate/confirm and lock acceptance']}


def _read_inputs(args):
    inputs = {}
    for role in ('csv', 'pgn', 'log'):
        path = getattr(args, role, None)
        if path is None:
            continue
        if not path.is_file() or path.stat().st_size > MAX_INPUT:
            raise ValueError(f'{role}: require a regular input file <=64 MiB')
        # Read each source exactly once; parsing and evidence consume these same bytes.
        data = path.read_bytes()
        if len(data) > MAX_INPUT:
            raise ValueError(f'{role}: input grew beyond64 MiB')
        inputs[role] = {'path': str(path.resolve()), 'data': data,
                        'text': data.decode('utf-8-sig'), 'sha256': hashlib.sha256(data).hexdigest()}
    return inputs


def _save(args, result, inputs):
    result.update(schema='forge_sol_S06_result_v1', mode=args.mode, acceptance_authorized=False,
                  created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  source_hashes={}, inputs=[], arguments={k: str(v) if isinstance(v, Path) else v for k,v in vars(args).items()})
    for part in PRODUCTS:
        p = Path(__file__).with_name(f'forge_sol_S06_{part}_{STAMP}.py')
        result['source_hashes'][p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
    retained = {}
    for index, (role, record) in enumerate(inputs.items(), 1):
        name = f'forge_sol_S06_input_{index:02d}_{role}_{STAMP}.bin'
        retained[name] = record['data']
        result['inputs'].append({'role': role, 'original_path': record['path'], 'saved_as': name,
                                 'sha256': record['sha256'], 'bytes': len(record['data'])})
    name = f'forge_sol_S06_result_{STAMP}.json'
    retained[name] = (json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n').encode()
    # Serialization/validation precede mutation. Exclusive directory/file creation
    # protects an existing run; no input is edited, renamed or overwritten.
    args.out.mkdir(exist_ok=False)
    for filename, data in retained.items():
        with (args.out/filename).open('xb') as out:
            out.write(data)
    manifest = ''.join(hashlib.sha256(data).hexdigest()+'  '+filename+'\n' for filename,data in sorted(retained.items()))
    with (args.out/f'forge_sol_S06_SHA256SUMS_{STAMP}.txt').open('x') as out:
        out.write(manifest)
    print(f"{result['status']}: {args.out/name}; no acceptance or Elo-gain claim")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='mode', required=True)
    for mode in ('counts', 'mine', 'triage'):
        p = commands.add_parser(mode)
        p.add_argument('--out', required=True, type=Path, help='NEW directory; parent must exist')
        p.add_argument('--e0', type=float, default=0.0)
        p.add_argument('--e1', type=float, default=10.0)
        p.add_argument('--units', choices=('nelo','logistic'), default='nelo')
        p.add_argument('--alpha', type=float, default=0.05)
        p.add_argument('--beta', type=float, default=0.05)
        if mode == 'counts':
            p.add_argument('--penta', type=int, nargs=5, required=True)
        elif mode == 'triage':
            p.add_argument('--csv', type=Path, required=True)
        else:
            p.add_argument('--pgn', type=Path)
            p.add_argument('--log', type=Path)
            p.add_argument('--gate-id', required=True)
            p.add_argument('--candidate', required=True)
            p.add_argument('--baseline', required=True)
            p.add_argument('--pairing', choices=('same-round','adjacent-rounds','round-prefix'), default='same-round')
            p.add_argument('--phase-tag', default='Phase')
    args = parser.parse_args(argv)
    try:
        if args.out.exists() or args.out.is_symlink():
            raise ValueError('output already exists; choose a NEW directory')
        _statistics(args, [0,0,0,0,0])  # Validate hypotheses even for metadata-only triage.
        inputs = _read_inputs(args)
        if args.mode == 'counts':
            result = {'status': 'CALCULATED', 'statistics': _statistics(args,args.penta),
                      'scope': 'Arithmetic on caller-supplied paired counts only, not a match or acceptance.'}
        elif args.mode == 'triage':
            result = _csv_triage(inputs['csv']['text'])
        else:
            result = _mine(args, inputs)
        _save(args, result, inputs)
        return 1 if result['status'] == 'BLOCKED' else 0
    except (OSError, ValueError, TypeError, OverflowError, csv.Error) as exc:
        print(f'S06: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
