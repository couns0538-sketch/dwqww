"""Combine complete, disjoint source inspections into descriptive evidence only."""
import argparse
from collections import Counter
from datetime import datetime
import json
import math
import os
from pathlib import Path

from profile_corpus import correlation, low_priority, sha256, stat_key, write_json
from resource_policy import storage_guard

EXPECTED_SOURCES = {f'forge_selfplay_{n:03}.txt' for n in range(1, 40) if n not in (13, 14)}
HISTOGRAMS = ('result_white', 'result_stm', 'turn', 'absolute_cp', 'ply', 'pieces', 'score_result')
COUNTS = ('data_rows', 'valid_rows', 'invalid_rows', 'known_results', 'unknown_results',
          'in_check', 'mate_score', 'ply_gt160', 'default_keep', 'mirror_checks',
          'zero_cp', 'abs_cp_gt3000', 'native_score_or_ply_out_of_range',
          'castling_rights_present', 'ep_square_present', 'halfmove_ge80')


def require_count(value, name):
    if type(value) is not int or value < 0:
        raise ValueError('invalid count: '+name)
    return value


def validate_source(report):
    if report.get('status') != 'PASS' or report.get('complete_scan') is not True:
        raise ValueError('source inspection is incomplete or failed')
    counts = {key: require_count(report.get(key), key) for key in COUNTS}
    size = counts['valid_rows']
    if not size or counts['invalid_rows'] or size != counts['data_rows']:
        raise ValueError('source row accounting failed')
    if counts['known_results']+counts['unknown_results'] != size:
        raise ValueError('result coverage accounting failed')
    if any(value > size for value in counts.values()):
        raise ValueError('source counter exceeds rows')
    histograms = report['histograms']
    if set(histograms) != set(HISTOGRAMS):
        raise ValueError('incomplete source histograms')
    for name, histogram in histograms.items():
        if not isinstance(histogram, dict) or sum(require_count(v, name) for v in histogram.values()) != size:
            raise ValueError('histogram row accounting failed: '+name)
    result = histograms['result_stm']
    if not set(result) <= {'-1', '0', '1', 'None'} or result.get('None', 0) != counts['unknown_results']:
        raise ValueError('result histogram accounting failed')
    score_outcomes = Counter()
    for key, value in histograms['score_result'].items():
        label, separator, outcome = key.rpartition(':')
        if not separator or not label or outcome not in ('-1', '0', '1', 'None'):
            raise ValueError('invalid score/outcome histogram key')
        score_outcomes[outcome] += value
    if score_outcomes != Counter(result):
        raise ValueError('score/outcome marginals differ from result coverage')
    moments = report['moments']
    if len(moments) != 6 or any(type(n) is not int for n in moments):
        raise ValueError('invalid correlation moments')
    n, sx, sy, sxx, syy, sxy = moments
    if (n != counts['known_results'] or sy != result.get('1', 0)-result.get('-1', 0)
            or syy != result.get('1', 0)+result.get('-1', 0)):
        raise ValueError('correlation result moments mismatch')
    vx, vy, covariance = n*sxx-sx*sx, n*syy-sy*sy, n*sxy-sx*sy
    if (sxx < 0 or syy < 0 or vx < 0 or vy < 0 or covariance*covariance > vx*vy
            or n == 0 and any(moments[1:])):
        raise ValueError('impossible score/result moments')
    computed = correlation(moments)
    observed = report['pearson_stm_score_result']
    if computed is None:
        if observed is not None:
            raise ValueError('undefined correlation was reported as measured')
    elif (type(observed) not in (int, float) or not math.isfinite(observed)
          or not -1 <= observed <= 1 or not math.isclose(computed, observed, rel_tol=1e-12, abs_tol=1e-12)):
        raise ValueError('correlation does not match source moments')
    if stat_key(report['path']) != report['source_identity']:
        raise ValueError('profiled source identity changed')
    if sha256(report['path']+'.md5') != report['sidecar_sha256']:
        raise ValueError('profiled producer sidecar changed')
    if report['md5'] != report['expected_md5']:
        raise ValueError('profile did not match producer digest')
    return counts


def combine(profiles):
    totals = Counter()
    histograms = {name: Counter() for name in HISTOGRAMS}
    moments = [0]*6
    sources, inputs, seen_paths, seen_names, starts, finishes = [], [], set(), set(), [], []
    for supplied in profiles:
        path = Path(supplied).resolve()
        before = sha256(path)
        summary = json.loads(path.read_text(encoding='utf-8'))
        if (type(summary.get('schema')) is not int or summary['schema'] != 1 or summary.get('status') != 'PASS'
                or summary.get('training_ready') is not False or summary.get('strength') != 'UNPROVEN'
                or type(summary.get('workers')) is not int or summary['workers'] != 1
                or summary.get('max_rows_per_source') is not None):
            raise ValueError('only complete descriptive profiles are accepted')
        if summary['script_sha256'] != sha256(Path(__file__).with_name('profile_corpus.py')):
            raise ValueError('profile source implementation identity mismatch')
        local_rows = 0
        for index, report in enumerate(summary['sources']):
            source = Path(report['path']).resolve()
            if source in seen_paths or source.name in seen_names:
                raise ValueError('overlapping source profiles')
            if source.name not in EXPECTED_SOURCES:
                raise ValueError('unexpected source or holdout')
            seen_paths.add(source); seen_names.add(source.name)
            report_path = path.parent/f'{index:03}.json'
            if json.loads(report_path.read_text(encoding='utf-8')) != report:
                raise ValueError('summary differs from sealed source report')
            sample_path = path.parent/f'{index:03}.sample.jsonl'
            if sha256(sample_path) != report['sample_sha256']:
                raise ValueError('audit reservoir hash mismatch')
            counts = validate_source(report)
            totals.update(counts)
            local_rows += counts['data_rows']
            for name in HISTOGRAMS:
                histograms[name].update(report['histograms'][name])
            moments = [a+b for a,b in zip(moments, report['moments'])]
            sources.append(report)
        if local_rows != summary['total_data_rows'] or sha256(path) != before:
            raise ValueError('profile summary count or identity mismatch')
        inputs.append({'path': str(path), 'sha256': before})
        starts.append(datetime.fromisoformat(summary['started_utc']))
        finishes.append(datetime.fromisoformat(summary['finished_utc']))
    if seen_names != EXPECTED_SOURCES:
        raise ValueError('incomplete 001-039 source coverage excluding 013/014')
    return dict(schema=1, status='PASS', strength='UNPROVEN', training_ready=False,
                reporter_sha256=sha256(__file__),
                scope='descriptive accounting only; no training, full-corpus holdout or game-ID clearance',
                profile_inputs=inputs, sources=sorted(sources, key=lambda r: r['path']),
                totals=dict(totals), histograms={k:dict(v) for k,v in histograms.items()},
                moments=moments, pearson_stm_score_result=correlation(moments),
                elapsed_span_seconds=(max(finishes)-min(starts)).total_seconds(),
                timing_note='Overlapping one-worker scans; elapsed span includes staggered starts, recorded owned-worker yields and other authorized work, not a filter benchmark.')


def markdown(report):
    total = report['totals']['data_rows']
    aggregate_rho = report['pearson_stm_score_result']
    aggregate_text = 'undefined (insufficient variance)' if aggregate_rho is None else f'{aggregate_rho:.10f}'
    lines = ['# Closed-source data profile — UNPROVEN', '',
             f'Inspected {total:,} rows across {len(report["sources"])} complete owned self-play shards.',
             'Sources are 001–039 excluding 013/014. Every source row received a full-board',
             'validity check; original producer MD5 and complete SHA256 were recorded.',
             'These are descriptive data statistics. No training input, game-ID separation,',
             'full-corpus holdout clearance or playing-strength result is produced.', '',
             f'Known outcomes: {report["totals"]["known_results"]:,}; unknown outcomes: {report["totals"]["unknown_results"]:,}.', '',
             f'Aggregate STM score/result correlation: {aggregate_text}.',
             'This uses summed raw moments, not an average of per-shard correlations.', '',
             '| Measurable rule | Kept | Keep rate |', '|---|---:|---:|']
    for label, rejected in [('In check', 'in_check'), ('Mate score', 'mate_score'), ('Ply >160', 'ply_gt160')]:
        kept = total-report['totals'][rejected]
        lines.append(f'| {label} | {kept:,} | {100*kept/total:.4f}% |')
    lines += ['', 'Capture/promotion and qsearch coverage remain unavailable for these sources.',
              'The matched recipes still use the separately cleared 999,953-row cohort.',
              'The ply boundary remains an experiment, not an enabled recipe change.', '',
              '| Shard | Rows | White W/D/L (known) | Correlation | Ply >160 |', '|---|---:|---:|---:|---:|']
    for source in report['sources']:
        outcomes = source['histograms']['result_white']
        wdl = '/'.join(f'{outcomes.get(key,0):,}' for key in ('1','0','-1'))
        rho = source['pearson_stm_score_result']
        rho_text = 'undefined' if rho is None else f'{rho:.6f}'
        lines.append(f'| {Path(source["path"]).stem} | {source["data_rows"]:,} | {wdl} | {rho_text} | {source["ply_gt160"]:,} |')
    for title, key in [('Absolute score (cp)', 'absolute_cp'), ('Zero-based ply', 'ply'), ('Pieces', 'pieces')]:
        lines += ['', f'## {title}', '', 'Bins are disjoint; each upper bound excludes the preceding bin.',
                  '', '| Upper bound | Rows | Share |', '|---|---:|---:|']
        order = sorted(report['histograms'][key], key=lambda s: (s.startswith('>'),int(s.lstrip('<=>'))))
        for label in order:
            n = report['histograms'][key][label]
            lines.append(f'| {label} | {n:,} | {100*n/total:.4f}% |')
    lines += ['', '## Observed outcomes by signed STM score', '',
              'Position-weighted counts are correlated within games. They are not independent',
              'game samples, calibrated probabilities, confidence intervals or Elo evidence.', '',
              '| Disjoint score bin | Loss | Draw | Win | Unknown |', '|---|---:|---:|---:|---:|']
    bins = sorted({key.split(':')[0] for key in report['histograms']['score_result']},
                  key=lambda s: (s.startswith('>'),int(s.lstrip('<=>'))))
    for label in bins:
        cells = [f'{report["histograms"]["score_result"].get(label+":"+result,0):,}' for result in ('-1','0','1','None')]
        lines.append('| '+label+' | '+' | '.join(cells)+' |')
    lines += ['', 'Full source hashes, counters, raw correlation moments and profile identities are',
              'in corpus_report.json. Audit reservoirs are evidence only, never recipe inputs.', '']
    return '\n'.join(lines)


def run(profiles, output):
    output = Path(output).resolve()
    partial = output.with_name(output.name+'.partial')
    if os.path.lexists(output) or os.path.lexists(partial):
        raise FileExistsError('refusing existing report output')
    storage_guard(output, allowance=5_000_000)
    report = combine(profiles)
    partial.mkdir(parents=True)
    write_json(partial/'corpus_report.json', report)
    with (partial/'DATA_PROFILE.md').open('x', encoding='utf-8', newline='\n') as fh:
        fh.write(markdown(report))
    storage_guard(output, allowance=0)
    partial.rename(output)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--profiles', nargs='+', type=Path, required=True)
    args = parser.parse_args()
    low_priority()
    result = run(args.profiles, args.output)
    print(json.dumps({'status':result['status'], 'rows':result['totals']['data_rows'], 'strength':'UNPROVEN'}))
