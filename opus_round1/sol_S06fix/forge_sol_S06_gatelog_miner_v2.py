"""Offline original Forge gate miner (S06 v2). No engine execution or adoption decisions.

v2 fix-ups over Sol's forge_sol_S06_gatelog_miner_20261026.py (17aa0cae, unchanged):
- S06-1: statistics use the exact fastchess normalized-pentanomial GSPRT as the primary LLR (Gaussian kept
  as a secondary cross-check); fastchess-style Elo +/-, nElo +/-, LOS are reported.
- S06-2: ``mine --result RESULT.md`` reconciles the PGN (complete pairs), the fastchess log and the gate's
  RESULT.md: games, W/L/D, Ptnml, complete pairs, time losses, crashes, LLR (exact, from the PGN Ptnml),
  Elo +/-, nElo +/-, LOS. Book-move opening keys and orphan games make real fastchess PGNs pairable.
- S06-3: non-"normal" Termination pairs are counted; ``--pgn`` may be given more than once; ``--out``
  refuses PC gate/lock/queue data: protected roots (D:/grok-pc-data/forge_push, D:/grok-pc-data/selfplay_out,
  F:/forge_nnue_train, C:/Users/Administrator/grok-pc, plus --protect / FORGE_S06_PROTECTED), any path
  component that looks like a gate/lock/queue directory (gate<N>..., gate_..., *_lock_*, *_queue_*), and any
  directory below an existing folder that holds gate markers (RUN_INFO.json, RESULT.md).
"""
from __future__ import annotations
import argparse
import csv
import datetime
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from forge_sol_S06_statistics_v2 import summarize_pentanomial, exact_llr  # noqa: E402
from forge_sol_S06_pgn_v2 import mine_pgns  # noqa: E402
from forge_sol_S06_logs_v2 import mine_log  # noqa: E402

STAMP = 'v2'
MAX_INPUT = 64 * 1024 * 1024
PRODUCTS = ('gatelog_miner', 'statistics', 'pgn', 'logs')
DEFAULT_PROTECTED = ('D:/grok-pc-data/forge_push', 'D:/grok-pc-data/selfplay_out', 'F:/forge_nnue_train',
                     'C:/Users/Administrator/grok-pc')
_PROTECTED_COMPONENT = re.compile(r'^gate(?:\d|_)|(?:^|[_.\-])(?:lock|queue)(?:[_.\-]|$)', re.I)
PRINT_TOLERANCE = 0.0051  # printed with two decimals


def _finite_float(value):
    x = float(value)
    if not math.isfinite(x):
        raise ValueError('number must be finite')
    return x


def _nonnegative_int(value):
    if not re.fullmatch(r'[0-9]+', value):
        raise ValueError('count must be a nonnegative integer')
    return int(value)


def _norm(path):
    return os.path.normcase(os.path.abspath(str(path)))


GATE_MARKERS = ('RUN_INFO.json', 'RESULT.md')


def check_out(out, extra_protected=()):
    """S06-3: refuse an output directory inside PC gate/lock/queue data."""
    target = _norm(out)
    roots = list(DEFAULT_PROTECTED) + list(extra_protected)
    roots += [r for r in os.environ.get('FORGE_S06_PROTECTED', '').split(os.pathsep) if r]
    for root in roots:
        r = _norm(root)
        if target == r or target.startswith(r.rstrip('\\/') + os.sep):
            raise ValueError(f'--out {out} is inside protected PC data {root}; write to a scratch directory')
    for part in Path(os.path.abspath(str(out))).parts:
        if _PROTECTED_COMPONENT.search(part.strip('\\/')):
            raise ValueError(f'--out path component {part!r} looks like a gate/lock/queue directory')
    for folder in Path(os.path.abspath(str(out))).parents:
        if folder.is_dir() and any((folder / marker).is_file() for marker in GATE_MARKERS):
            raise ValueError(f'--out {out} is below {folder}, which holds gate markers {GATE_MARKERS}')


def parse_result_md(text):
    """Fields of a PC gate RESULT.md (forge_queue.ps1); missing fields stay None."""
    text = text.lstrip('\ufeff')
    out = dict.fromkeys(('candidate', 'baseline', 'model', 'e0', 'e1', 'games', 'W', 'L', 'D', 'ptnml', 'pairs',
                         'elo', 'elo_err', 'nelo', 'nelo_err', 'los', 'llr', 'time_losses', 'crashes', 'clean',
                         'orphans', 'verdict'))
    m = re.search(r'^# \S+ RESULT: (\S+) vs (\S+)', text, re.M)
    if m:
        out.update(candidate=m.group(1), baseline=m.group(2))
    m = re.search(r'SPRT (\w+) \[(-?[0-9.]+),\s*(-?[0-9.]+)\]', text)
    if m:
        out.update(model=m.group(1), e0=float(m.group(2)), e1=float(m.group(3)))
    m = re.search(r'Games: (\d+)\s+W/L/D \(candidate view\): (\d+) / (\d+) / (\d+)', text)
    if m:
        out.update(games=int(m.group(1)), W=int(m.group(2)), L=int(m.group(3)), D=int(m.group(4)))
    m = re.search(r'Ptnml\(0-2\): \[([^\]]*)\]\s+complete pairs = (\d+)', text)
    if m:
        out.update(ptnml=[int(x) for x in m.group(1).split(',')], pairs=int(m.group(2)))
    m = re.search(r'Elo: (-?[0-9.]+) \+/- ([0-9.]+)\s+nElo: (-?[0-9.]+) \+/- ([0-9.]+)\s+LOS ([0-9.]+) %', text)
    if m:
        out.update(elo=float(m.group(1)), elo_err=float(m.group(2)), nelo=float(m.group(3)),
                   nelo_err=float(m.group(4)), los=float(m.group(5)))
    m = re.search(r'LLR: (-?[0-9.]+)\s+bounds', text)
    if m:
        out['llr'] = float(m.group(1))
    m = re.search(r'Time losses: (\d+)\s+Crashes/disconnects/stalls/illegal: (\d+)', text)
    if m:
        out.update(time_losses=int(m.group(1)), crashes=int(m.group(2)))
    out['clean'] = (': CLEAN' in text) if 'clean requires' in text else None
    m = re.search(r'Orphan games \(Games - 2\*complete pairs\): (\d+)', text)
    if m:
        out['orphans'] = int(m.group(1))
    m = re.search(r'\*\*Verdict: ([^*]*)\*\*', text)
    if m:
        out['verdict'] = m.group(1).strip()
    return out


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


def _pair_wdl(six):
    """Candidate W/D/L of the games in valid pairs, from the six pair bins."""
    if six is None:
        return None
    return [2*six['WW'] + six['WD'] + six['WL'], six['WD'] + 2*six['DD'] + six['LD'],
            six['WL'] + six['LD'] + 2*six['LL']]


def _compare(label, values, tolerance=None):
    """values: {source: value}; PASS if every non-None value agrees (within tolerance for numbers)."""
    present = {k: v for k, v in values.items() if v is not None}
    if len(present) < 2:
        return {'field': label, 'status': 'UNVERIFIED', **values}
    items = list(present.values())
    if tolerance is None:
        same = all(v == items[0] for v in items)
    else:
        same = max(items) - min(items) <= tolerance
    return {'field': label, 'status': 'PASS' if same else 'FAIL', **values,
            **({'tolerance': tolerance} if tolerance is not None else {})}


def _mine(args, inputs):
    if not (args.pgn or args.log):
        raise ValueError('mine requires --pgn and/or --log')
    if not args.gate_id.strip():
        raise ValueError('gate-id must be nonempty')
    pgn = mine_pgns([record['text'] for record in inputs.get('pgn', [])], args.candidate, args.baseline,
                    pairing=args.pairing, phase_tag=args.phase_tag) if args.pgn else None
    log = mine_log(inputs['log'][0]['text'], args.candidate, args.baseline) if args.log else None
    result_md = parse_result_md(inputs['result'][0]['text']) if args.result else None
    issues, comparisons, by_pool = [], [], []
    if pgn:
        if not pgn['paired']['aggregate_eligible']:
            issues.append('PGN outcome/pair screen is not eligible; all records retained')
        if pgn['paired']['non_normal_termination_pairs']:
            issues.append(f"{pgn['paired']['non_normal_termination_pairs']} pairs with a non-normal Termination: "
                          f"{pgn['paired']['non_normal_termination_pairs_by_value']}")
        for pool in pgn['pools']:
            statistics = _statistics(args, pool['paired']['pentabins'])
            if statistics['status'] == 'blocked':
                issues.append(f"{pool['id']}: statistical hypothesis is unestimable")
            by_pool.append({'pool': pool['id'], 'metadata': pool['metadata'],
                            'statistics': statistics,
                            'outcome_screen_eligible': pool['paired']['aggregate_eligible']})
    if log and log['status'] == 'BLOCKED':
        issues.append('log observations contain faults or integrity issues')
    pgn_pairs = pgn['paired'] if pgn and len(pgn['pools']) <= 1 else None
    pgn_wdl = _pair_wdl(pgn_pairs['six_bins']) if pgn_pairs else None
    pgn_tl = sum(1 for g in pgn['games'] for f in g['faults'] if f['kind'] == 'time_loss') if pgn else None
    pgn_crash = sum(1 for g in pgn['games'] for f in g['faults'] if f['kind'] in ('crash', 'illegal')) if pgn else None
    log_wdl = log['reported']['wdl'] if log else None
    res_wdl = [result_md['W'], result_md['D'], result_md['L']] if result_md and result_md['W'] is not None else None
    sources = lambda p, l, r: {'pgn': p, 'log': l, 'result_md': r}  # noqa: E731
    if pgn or log or result_md:
        comparisons.append(_compare('games (complete pairs x 2)', sources(
            2 * pgn_pairs['valid_pairs'] if pgn_pairs else None, log['reported']['games'] if log else None,
            result_md['games'] if result_md else None)))
        comparisons.append(_compare('wdl (candidate W/D/L, complete pairs)', sources(pgn_wdl, log_wdl, res_wdl)))
        comparisons.append(_compare('pentabins (Ptnml 0-2)', sources(
            pgn_pairs['pentabins'] if pgn_pairs else None, log['reported']['pentabins'] if log else None,
            result_md['ptnml'] if result_md else None)))
        comparisons.append(_compare('time_losses', sources(
            pgn_tl, log['faults']['time_loss_events'] if log else None,
            result_md['time_losses'] if result_md else None)))
        comparisons.append(_compare('crashes/illegal', sources(
            pgn_crash, (log['faults']['crash_events'] + log['faults']['illegal_events']) if log else None,
            result_md['crashes'] if result_md else None)))
        if log and log['finished']['games']:
            comparisons.append(_compare('log finished-game pairs vs log summary Ptnml', {
                'finished_pairs': log['finished']['complete_pair_pentabins'],
                'summary': log['reported']['pentabins']}))
    exact = None
    if pgn_pairs and sum(pgn_pairs['pentabins']):
        exact = exact_llr(pgn_pairs['pentabins'], args.e0, args.e1, args.units)
    elif result_md and result_md['ptnml']:
        exact = exact_llr(result_md['ptnml'], args.e0, args.e1, args.units)
    native_llr = log['reported']['llr'] if log else None
    comparisons.append(_compare('LLR (exact GSPRT from Ptnml vs printed)', {
        'exact_from_ptnml': exact, 'log': native_llr['value'] if native_llr else None,
        'result_md': result_md['llr'] if result_md else None}, PRINT_TOLERANCE))
    if result_md:
        if result_md['model'] is not None and (result_md['model'] != 'normalized' or args.units != 'nelo'
                                               or result_md['e0'] != args.e0 or result_md['e1'] != args.e1):
            issues.append(f"RESULT.md SPRT {result_md['model']} [{result_md['e0']},{result_md['e1']}] differs "
                          f"from --units {args.units} [--e0 {args.e0}, --e1 {args.e1}]")
        if (result_md['candidate'], result_md['baseline']) not in ((None, None), (args.candidate, args.baseline)):
            issues.append(f"RESULT.md title names {result_md['candidate']} vs {result_md['baseline']}, "
                          f"not --candidate {args.candidate} --baseline {args.baseline}")
        counts = pgn_pairs['pentabins'] if pgn_pairs and sum(pgn_pairs['pentabins']) else result_md['ptnml']
        if counts:
            display = _statistics(args, counts)['fastchess_display']
            for key, field in (('elo', 'elo'), ('elo_err', 'elo_error95'), ('nelo', 'nelo'),
                               ('nelo_err', 'nelo_error95'), ('los', 'los_percent')):
                comparisons.append(_compare(f'{key} (recomputed vs RESULT.md)', {
                    'recomputed': display[field], 'result_md': result_md[key]}, PRINT_TOLERANCE))
    for c in comparisons:
        if c['status'] == 'FAIL':
            issues.append(f"{c['field']} mismatch; no favorable subset selected")
    gaussian = by_pool[0]['statistics']['gaussian_llr']['value'] if len(by_pool) == 1 else None
    llr_comparison = {'primary': 'exact GSPRT (fastchess normalized pentanomial)', 'exact_llr': exact,
                      'native_log_llr': native_llr['value'] if native_llr else None,
                      'gaussian_llr_secondary': gaussian,
                      'exact_minus_native': (exact - native_llr['value']) if exact is not None and native_llr
                      and native_llr['value'] is not None else None,
                      'gaussian_minus_exact': (gaussian - exact) if gaussian is not None and exact is not None else None}
    unresolved = [c for c in comparisons if c['status'] == 'UNVERIFIED']
    status = ('BLOCKED' if issues else
              'RECONCILED' if result_md and pgn and log and not unresolved else
              'OUTCOME_CHECKS_PASS' if pgn and not (log and log['status'] == 'UNVERIFIED') else 'UNVERIFIED')
    if args.detail == 'summary':
        if pgn:
            openings = len(pgn['per_opening'])
            pgn = {k: v for k, v in pgn.items() if k not in ('games', 'pairs', 'per_opening')}
            pgn['per_opening_count'] = openings
            pgn['pools'] = [{**{k: v for k, v in pool.items() if k not in ('pairs', 'games', 'per_opening')},
                             'games_count': len(pool['games']), 'per_opening_count': len(pool['per_opening'])}
                            for pool in pgn['pools']]
            pgn['detail'] = ('summary: per-game, per-pair and per-opening records omitted '
                             '(--detail full keeps them)')
        if log:
            log = dict(log)
            log['finished'] = {k: v for k, v in log['finished'].items() if k != 'records'}
            log['snapshots_count'] = len(log['snapshots'])
            log['snapshots'] = log['snapshots'][-1:]
            log['llr_observations'] = log['llr_observations'][-1:]
            log['headers_count'] = len(log['headers'])
            log['headers'] = log['headers'][-1:]
    return {'status': status, 'gate_id_declared': args.gate_id, 'pgn': pgn, 'log': log,
            'result_md': result_md, 'statistics_by_pool': by_pool,
            'reconciliation': {'comparisons': comparisons, 'issues': issues},
            'llr_comparison': llr_comparison,
            'unverified': ['engine source/build/binary binding', 'move legality',
                           'frozen protocol and stopping rule', 'original gate/confirm and lock acceptance']}


def _read_inputs(args):
    inputs = {}
    for role in ('csv', 'pgn', 'log', 'result'):
        paths = getattr(args, role, None)
        if paths is None:
            continue
        for path in (paths if isinstance(paths, list) else [paths]):
            if not path.is_file() or path.stat().st_size > MAX_INPUT:
                raise ValueError(f'{role}: require a regular input file <=64 MiB')
            # Read each source exactly once; parsing and evidence consume these same bytes.
            data = path.read_bytes()
            if len(data) > MAX_INPUT:
                raise ValueError(f'{role}: input grew beyond 64 MiB')
            inputs.setdefault(role, []).append({'path': str(path.resolve()), 'data': data,
                                                'text': data.decode('utf-8-sig'),
                                                'sha256': hashlib.sha256(data).hexdigest()})
    return inputs


def _save(args, result, inputs):
    result.update(schema='forge_sol_S06_result_v2', mode=args.mode, acceptance_authorized=False,
                  created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  source_hashes={}, inputs=[], arguments={k: [str(x) for x in v] if isinstance(v, list) else
                                                          (str(v) if isinstance(v, Path) else v)
                                                          for k, v in vars(args).items()})
    for part in PRODUCTS:
        p = Path(__file__).with_name(f'forge_sol_S06_{part}_{STAMP}.py')
        result['source_hashes'][p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
    retained = {}
    index = 0
    for role, records in inputs.items():
        for record in records:
            index += 1
            entry = {'role': role, 'original_path': record['path'], 'sha256': record['sha256'],
                     'bytes': len(record['data'])}
            if args.hash_only_inputs:
                entry['saved_as'] = None
            else:
                name = f'forge_sol_S06_input_{index:02d}_{role}_{STAMP}.bin'
                retained[name] = record['data']
                entry['saved_as'] = name
            result['inputs'].append(entry)
    name = f'forge_sol_S06_result_{STAMP}.json'
    retained[name] = (json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n').encode()
    # Serialization/validation precede mutation. Exclusive directory/file creation
    # protects an existing run; no input is edited, renamed or overwritten.
    args.out.mkdir(exist_ok=False)
    for filename, data in retained.items():
        with (args.out/filename).open('xb') as out:
            out.write(data)
    manifest = ''.join(hashlib.sha256(data).hexdigest()+'  '+filename+'\n' for filename, data in sorted(retained.items()))
    with (args.out/f'forge_sol_S06_SHA256SUMS_{STAMP}.txt').open('x') as out:
        out.write(manifest)
    print(f"{result['status']}: {args.out/name}; no acceptance or Elo-gain claim")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='mode', required=True)
    for mode in ('counts', 'mine', 'triage'):
        p = commands.add_parser(mode)
        p.add_argument('--out', required=True, type=Path, help='NEW directory; parent must exist; never gate/lock data')
        p.add_argument('--protect', type=Path, action='append', default=[],
                       help='extra directory --out must not be inside (repeatable)')
        p.add_argument('--hash-only-inputs', action='store_true',
                       help='record input path/sha256/bytes without copying the input bytes into --out')
        p.add_argument('--e0', type=float, default=0.0)
        p.add_argument('--e1', type=float, default=10.0)
        p.add_argument('--units', choices=('nelo', 'logistic'), default='nelo')
        p.add_argument('--alpha', type=float, default=0.05)
        p.add_argument('--beta', type=float, default=0.05)
        if mode == 'counts':
            p.add_argument('--penta', type=int, nargs=5, required=True)
        elif mode == 'triage':
            p.add_argument('--csv', type=Path, required=True)
        else:
            p.add_argument('--pgn', type=Path, action='append', help='PGN file (repeatable)')
            p.add_argument('--log', type=Path)
            p.add_argument('--result', type=Path, help="the gate's RESULT.md to reconcile against")
            p.add_argument('--gate-id', required=True)
            p.add_argument('--candidate', required=True)
            p.add_argument('--baseline', required=True)
            p.add_argument('--pairing', choices=('same-round', 'adjacent-rounds', 'round-prefix'), default='same-round')
            p.add_argument('--phase-tag', default='Phase')
            p.add_argument('--detail', choices=('full', 'summary'), default='full',
                           help='summary drops per-game/per-pair records from the saved JSON')
    args = parser.parse_args(argv)
    try:
        if args.out.exists() or args.out.is_symlink():
            raise ValueError('output already exists; choose a NEW directory')
        check_out(args.out, args.protect)
        _statistics(args, [0, 0, 0, 0, 0])  # Validate hypotheses even for metadata-only triage.
        inputs = _read_inputs(args)
        if args.mode == 'counts':
            statistics = _statistics(args, args.penta)
            result = {'status': 'BLOCKED' if statistics['status'] == 'blocked' else 'CALCULATED', 'statistics': statistics,
                      'scope': 'Arithmetic on caller-supplied paired counts only, not a match or acceptance.'}
        elif args.mode == 'triage':
            result = _csv_triage(inputs['csv'][0]['text'])
        else:
            result = _mine(args, inputs)
        _save(args, result, inputs)
        return 1 if result['status'] == 'BLOCKED' else 0
    except (OSError, ValueError, TypeError, OverflowError, csv.Error) as exc:
        print(f'S06: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
