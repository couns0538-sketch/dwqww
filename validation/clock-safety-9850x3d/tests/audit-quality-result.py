#!/usr/bin/env python3
"""Independently audit a completed fixed-node quality SPRT; never run an engine.

Usage: python3 audit-quality-result.py --run RUN_DIRECTORY --output NEW_EXTERNAL.json
The output must be new and outside RUN_DIRECTORY. Only standard-library modules
are used; neither the frozen runner nor pgn_stats is imported or executed.
"""
from __future__ import annotations

import argparse
import collections
import datetime
import hashlib
import json
import math
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
ZERO_BIN_REGULARIZATION = 0.001
PRINTED_LLR_TOLERANCE = 0.005000001  # Native format is {:.2f}.
BOUNDARY_NUMERIC_TOLERANCE = 1e-10
OUTCOMES = {'0-1': 0, '1/2-1/2': 1, '1-0': 2}
TAG_LINE = re.compile(r'^\[([A-Za-z0-9_]+) "((?:[^"\\]|\\["\\])*)"\]$')
MOVE = re.compile(r'[a-h][1-8][a-h][1-8][qrbn]?\Z')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def parse_pgn(text):
    """Read headers/movetext sequentially, independently of the match checker."""
    parsed, tags, body = [], {}, []

    def finish():
        if not tags:
            raise ValueError('PGN movetext has no headers')
        clean, in_comment, line_comment = [], False, False
        for char in '\n'.join(body):
            if line_comment:
                if char == '\n':
                    line_comment = False
                    clean.append(' ')
            elif in_comment:
                if char == '{':
                    raise ValueError('nested PGN comment')
                if char == '}':
                    in_comment = False
                    clean.append(' ')
            elif char == '{':
                in_comment = True
                clean.append(' ')
            elif char == ';':
                line_comment = True
            elif char in '}()':
                raise ValueError('unexpected PGN brace or variation')
            else:
                clean.append(char)
        if in_comment:
            raise ValueError('unfinished PGN comment')
        tokens = re.sub(r'\b\d+\.(?:\.\.)?', ' ', ''.join(clean)).split()
        if not tokens or tokens[-1] not in OUTCOMES or tokens[-1] != tags.get('Result'):
            raise ValueError('unfinished or inconsistent PGN result')
        moves = tokens[:-1]
        if any(not MOVE.fullmatch(move) for move in moves):
            raise ValueError('PGN contains unexpected/non-UCI movetext')
        if int(tags.get('PlyCount', '-1')) != len(moves):
            raise ValueError('PGN PlyCount disagrees with parsed moves')
        parsed.append({'tags': dict(tags), 'moves': moves})

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        match = TAG_LINE.fullmatch(line)
        if match:
            if body:
                finish()
                tags, body = {}, []
            name, value = match.groups()
            if name in tags:
                raise ValueError(f'duplicate PGN header: {name}')
            tags[name] = re.sub(r'\\(["\\])', r'\1', value)
        else:
            if not tags:
                raise ValueError('unexpected text before PGN headers')
            body.append(line)
    if tags or body:
        finish()
    if not parsed:
        raise ValueError('no completed PGN games')
    return parsed


def logistic_llr(penta, elo0, elo1):
    """Constrained multinomial MLE solved by bisection, not Fastchess's ITP.

    Maximizing sum(n_i log(q_i)) with sum(q_i)=1 and sum(a_i q_i)=s
    gives q_i=p_i/(1+theta*(a_i-s)). The scalar constraint equation
    sum(p_i*(a_i-s)/(1+theta*(a_i-s)))=0 is strictly decreasing.
    """
    if len(penta) != 5 or any(type(n) is not int or n < 0 for n in penta) or not sum(penta):
        raise ValueError('invalid pentanomial counts')
    counts = [float(n) if n else ZERO_BIN_REGULARIZATION for n in penta]
    total = math.fsum(counts)
    probabilities = [n / total for n in counts]
    scores = [0.0, 0.25, 0.5, 0.75, 1.0]

    def constrained_mle(elo):
        score = 1.0 / (1.0 + 10.0 ** (-elo / 400.0))
        if not 0.0 < score < 1.0:
            raise ValueError('hypothesis score is outside the MLE domain')
        lower, upper = -1.0 / (1.0 - score), 1.0 / score
        theta = 0.0
        for _ in range(100):
            theta = (lower + upper) / 2.0
            value = math.fsum(p * (a - score) / (1.0 + theta * (a - score))
                              for p, a in zip(probabilities, scores))
            if value == 0.0:
                break
            if value > 0.0:
                lower = theta
            else:
                upper = theta
        fitted = [p / (1.0 + theta * (a - score)) for p, a in zip(probabilities, scores)]
        if (any(not math.isfinite(q) or q <= 0 for q in fitted)
                or abs(math.fsum(fitted) - 1.0) > 1e-9
                or abs(math.fsum(a * q for a, q in zip(scores, fitted)) - score) > 1e-9):
            raise ValueError('constrained MLE failed its normalization/mean checks')
        return fitted

    q0, q1 = constrained_mle(elo0), constrained_mle(elo1)
    llr = math.fsum(n * math.log(b / a) for n, a, b in zip(counts, q0, q1))
    if not math.isfinite(llr):
        raise ValueError('independently recomputed likelihood is not finite')
    return llr


def classify_decision(accepted, llr, upper, lower, pairs, cap):
    if accepted == 'H1':
        if llr < upper - BOUNDARY_NUMERIC_TOLERANCE:
            raise ValueError('native H1 acceptance lacks an independent upper-bound crossing')
        return 'H1_accepted'
    if accepted == 'H0':
        if llr > lower + BOUNDARY_NUMERIC_TOLERANCE:
            raise ValueError('native H0 acceptance lacks an independent lower-bound crossing')
        return 'H0_accepted'
    if accepted is not None:
        raise ValueError('unknown native acceptance token')
    if pairs != cap:
        raise ValueError('run stopped before its pair cap without native acceptance')
    if not lower < llr < upper:
        raise ValueError('cap result lacks acceptance despite an independent boundary crossing')
    return 'inconclusive_at_pair_cap'


def audit_run(run):
    report = {'audit_status': 'failed', 'supported_decision': None,
              'quality_gain_established': False, 'equal_clock_gain_established': False,
              'elo_gain_claim': None, 'run_directory': str(run), 'errors': [],
              'scope': 'Declared 10,000-node search quality between these binaries only.',
              'limitations': ['No equal-clock, Ryzen, Windows or Stockfish strength conclusion.',
                              'PGN syntax/outcome audit does not independently validate move legality.',
                              'Recorded file identity does not prove source-to-binary build provenance.']}
    errors, snapshots = report['errors'], {}

    def check(condition, message):
        if not condition:
            errors.append(message)

    def read(path):
        path = path.resolve(strict=True)
        if path not in snapshots:
            snapshots[path] = path.read_bytes()
        return snapshots[path]

    def load(name):
        return json.loads(read(run / name))

    try:
        protocol, result = load('protocol.json'), load('result.json')
        check(result.get('status') == 'completed', 'result does not declare a completed SPRT')
        check(result.get('exit_code') == 0, 'Fastchess did not exit successfully')
        if result.get('status') != 'completed':
            raise ValueError('a running, failed or interrupted run cannot establish a result')
        inputs = protocol['inputs']
        check(load('input-hashes.json') == inputs, 'input-hashes.json differs from frozen protocol')
        required_inputs = {'baseline', 'candidate', 'fastchess', 'corpus', 'original_zip',
                           'pgn_checker', 'protocol_runner', 'selected'}
        check(required_inputs <= inputs.keys(), 'frozen protocol lacks required input identities')
        check(set(result['final_input_hashes']) == set(inputs), 'final input hash names differ from protocol')
        for name, record in inputs.items():
            expected = record['sha256']
            check(result['final_input_hashes'].get(name) == expected, f'final input hash changed: {name}')
            check(digest(read(Path(record['path']))) == expected, f'current input hash changed: {name}')
        output_hashes = result['outputs_sha256']
        required_outputs = {'protocol.json', 'input-hashes.json', 'command.json', 'selected.epd',
                            'games.pgn', 'console.txt', 'fastchess.log', 'stats.json', 'state.json'}
        check(required_outputs <= output_hashes.keys(), 'result lacks required output hashes')
        actual_outputs = {p.name for p in run.iterdir() if p.is_file() and p.name != 'result.json'}
        check(actual_outputs == set(output_hashes), 'output file set differs from recorded final snapshot')
        for name, expected in output_hashes.items():
            if Path(name).name != name or name in ('.', '..', 'result.json'):
                raise ValueError('unsafe/non-output name in final output hashes')
            check(digest(read(run / name)) == expected, f'output hash changed: {name}')
        report['checked_input_count'] = len(inputs)
        report['checked_output_count'] = len(output_hashes)
        report['result_sha256'] = digest(read(run / 'result.json'))

        command, state = load('command.json'), load('state.json')
        check(command == protocol['command'], 'command.json differs from frozen protocol')
        check(command[0] == inputs['fastchess']['path'] and '-strict' in command,
              'unexpected Fastchess executable or missing strict mode')
        check(protocol.get('kind') == 'fixed-node search-quality SPRT', 'unsupported experiment kind')
        for key, expected in {'nodes_per_move': 10000, 'tc': 'inf', 'threads': 1,
                              'hash_mib': 32, 'ownbook': False, 'restart': True, 'concurrency': 1}.items():
            check(protocol.get(key) == expected, f'unexpected protocol setting: {key}')
        cap = protocol['max_pairs']
        if type(cap) is not int or cap < 1:
            raise ValueError('invalid pair cap')
        sprt = protocol['sprt']
        if (sprt['model'] != 'logistic' or not 0 < sprt['alpha'] < 1 or not 0 < sprt['beta'] < 1
                or sprt['alpha'] + sprt['beta'] >= 1 or not sprt['elo0'] < sprt['elo1']):
            raise ValueError('unsupported or invalid frozen SPRT configuration')
        lower = math.log(sprt['beta'] / (1.0 - sprt['alpha']))
        upper = math.log((1.0 - sprt['beta']) / sprt['alpha'])
        check(all(math.isclose(a, b, abs_tol=1e-12) for a, b in zip(sprt['bounds'], [lower, upper]))
              and len(sprt['bounds']) == 2, 'declared SPRT bounds disagree with alpha/beta')
        for key, expected in {'rounds': cap, 'games': 2, 'concurrency': 1, 'report_penta': True,
                              'noswap': False, 'reverse': False, 'recover': False}.items():
            check(state.get(key) == expected, f'final native configuration mismatch: {key}')
        check(state['sprt'].get('enabled') is True, 'native SPRT was not enabled')
        for key in ('alpha', 'beta', 'elo0', 'elo1', 'model'):
            check(state['sprt'].get(key) == sprt[key], f'native SPRT setting mismatch: {key}')
        for key in ('resign', 'draw', 'maxmoves', 'tb_adjudication'):
            check(state[key].get('enabled') is False, f'unexpected native adjudication: {key}')
        check(len(state['engines']) == 2, 'native configuration does not contain exactly two engines')
        for engine, name in zip(state['engines'], ('Candidate', 'Baseline')):
            record = inputs[name.lower()]
            check(engine['name'] == name and engine['cmd'] == record['path'], f'native engine identity mismatch: {name}')
            check(engine.get('restart') is True, f'native restart mismatch: {name}')
            check(engine['limit']['nodes'] == 10000 and engine['limit']['plies'] == 0,
                  f'native search limit mismatch: {name}')
            tc = engine['limit']['tc']
            check(set(tc) == {'time', 'fixed_time', 'increment', 'moves', 'timemargin'}
                  and all(value == 0 for value in tc.values()), f'native clock was enabled or missing: {name}')
            options = dict(engine['options'])
            check(all(options.get(k) == v for k, v in {'OwnBook': 'false', 'Threads': '1', 'Hash': '32'}.items()),
                  f'native UCI options mismatch: {name}')

        selected = [' '.join(line.split()) for line in read(run / 'selected.epd').decode().splitlines() if line.strip()]
        check(selected == protocol['selected_fens'], 'selected openings differ from preregistered order')
        check(len(selected) == cap and len(set(selected)) == cap, 'opening schedule is incomplete or duplicated')
        check(all(len(fen.split()) == 4 and fen.split()[1] == 'w' and fen.split()[3] == '-' for fen in selected),
              'schedule violates white-to-move/no-EP eligibility')
        check(Path(inputs['selected']['path']).resolve() == run / 'selected.epd', 'selected input points outside run')
        check(state['opening']['order'] == 1 and state['opening']['start'] == 1
              and Path(state['opening']['file']).resolve() == run / 'selected.epd', 'native opening schedule mismatch')
        games = parse_pgn(read(run / 'games.pgn').decode())
        if len(games) % 2 or not 2 <= len(games) <= cap * 2:
            raise ValueError('PGN contains an incomplete pair or invalid game count')
        pairs, penta, wdl = len(games) // 2, [0] * 5, [0] * 3
        native_six = collections.Counter()
        pair_scores = []
        for index, game in enumerate(games):
            tags = game['tags']
            pair = index // 2
            check(tags.get('Round') == str(pair + 1), f'PGN round/order mismatch at game {index + 1}')
            expected_colors = ('Candidate', 'Baseline') if index % 2 == 0 else ('Baseline', 'Candidate')
            check((tags.get('White'), tags.get('Black')) == expected_colors,
                  f'PGN color/player order mismatch at game {index + 1}')
            check(tags.get('SetUp') == '1' and tags.get('FEN', '').split() == selected[pair].split() + ['0', '1'],
                  f'PGN is not the exact scheduled prefix at game {index + 1}')
            check(tags.get('Termination') == 'normal', f'non-normal PGN termination at game {index + 1}')
            check(tags.get('TimeControl') == '-', f'PGN reports a clock at game {index + 1}')
            score = OUTCOMES[tags['Result']]
            if index % 2:
                score = 2 - score
            wdl[2 - score] += 1
            pair_scores.append(score)
            if index % 2:
                one, two = sorted(pair_scores[-2:])
                penta[one + two] += 1
                native_six[{(0, 0): 'penta_LL', (0, 1): 'penta_LD', (0, 2): 'penta_WL',
                            (1, 1): 'penta_DD', (1, 2): 'penta_WD', (2, 2): 'penta_WW'}[(one, two)]] += 1
        stats = {'pairs': pairs, 'games': len(games), 'candidate_wins_draws_losses': wdl,
                 'pentanomial_0_half_1_1half_2': penta, 'unique_openings': pairs,
                 'terminations': {'normal': len(games)}, 'score_fraction': (wdl[0] + wdl[1] / 2) / len(games)}
        report['independent_statistics'] = stats
        for label, recorded in [('result.statistics', result['statistics']), ('stats.json', load('stats.json'))]:
            for key, expected in stats.items():
                check(recorded.get(key) == expected, f'{label} disagrees with independent PGN audit: {key}')
        check(set(state['stats']) == {'Candidate vs Baseline'}, 'unexpected native statistics perspective')
        recorded = state['stats']['Candidate vs Baseline']
        for key, expected in zip(('wins', 'draws', 'losses'), wdl):
            check(recorded[key] == expected, f'native state WDL mismatch: {key}')
        for key in ('penta_LL', 'penta_LD', 'penta_WL', 'penta_DD', 'penta_WD', 'penta_WW'):
            check(recorded[key] == native_six[key], f'native state pair category mismatch: {key}')

        console = re.sub(r'\x1b\[[0-9;]*m', '', read(run / 'console.txt').decode())
        finished = re.findall(r'^Finished game (\d+) \(([^\n]*?) vs ([^\n]*?)\): (1-0|0-1|1/2-1/2) \{[^\n]*\}$', console, re.M)
        expected_finished = [(str(i + 1), game['tags']['White'], game['tags']['Black'], game['tags']['Result'])
                             for i, game in enumerate(games)]
        check(finished == expected_finished, 'native finished-game sequence differs from PGNs')
        started = re.findall(r'^Started game (\d+) of (\d+) \(([^\n]*?) vs ([^\n]*?)\)$', console, re.M)
        check(started == [(i, str(cap * 2), white, black) for i, white, black, _ in expected_finished],
              'native started-game sequence contains missing/unfinished/reordered games')
        check(result['progress']['finished_game_messages'] == len(games), 'recorded progress count differs from PGNs')
        native_penta = re.findall(r'^Ptnml\(0-2\):\s*\[([^\]]+)\]', console, re.M)
        if not native_penta:
            raise ValueError('missing final native pentanomial report')
        check([int(value.strip()) for value in native_penta[-1].split(',')] == penta,
              'final console pentanomial counts disagree with independent PGN audit')
        native_wdl = re.findall(r'^Games: (\d+), Wins: (\d+), Losses: (\d+), Draws: (\d+),', console, re.M)
        check(bool(native_wdl) and tuple(map(int, native_wdl[-1])) == (len(games), wdl[0], wdl[2], wdl[1]),
              'final console game/WDL counts disagree with independent PGN audit')
        check(len(re.findall(r'^Finished match$', console, re.M)) == 1 and 'Tournament was interrupted' not in console,
              'native console does not show an uninterrupted completion')
        native_log = read(run / 'fastchess.log').decode()
        check(not re.search(r'^\[(?:WARN|ERR|FATAL)\s*\]', native_log, re.M), 'native log contains a warning/error/fatal event')
        accepted = re.findall(r'^SPRT[^\n]*completed - (H[01]) was accepted$', console, re.M)
        if len(accepted) > 1:
            raise ValueError('multiple native SPRT acceptances')
        likelihoods = re.findall(r'^LLR:\s*(\S+)', console, re.M)
        if not likelihoods:
            raise ValueError('missing final native likelihood')
        native_llr = float(likelihoods[-1])
        if not math.isfinite(native_llr):
            raise ValueError('final native likelihood is not finite')
        independent_llr = logistic_llr(penta, sprt['elo0'], sprt['elo1'])
        report['likelihood_audit'] = {'method': 'independent constrained multinomial MLE; 100-step bisection',
                                    'zero_bin_regularization': ZERO_BIN_REGULARIZATION,
                                    'native_printed_llr': native_llr, 'independent_llr': independent_llr,
                                    'printed_llr_tolerance': PRINTED_LLR_TOLERANCE,
                                    'lower_bound': lower, 'upper_bound': upper,
                                    'boundary_numeric_tolerance': BOUNDARY_NUMERIC_TOLERANCE}
        check(abs(native_llr - independent_llr) <= PRINTED_LLR_TOLERANCE,
              'independent likelihood disagrees with native two-decimal likelihood')
        token = accepted[0] if accepted else None
        decision = classify_decision(token, independent_llr, upper, lower, pairs, cap)
        report['native_decision'] = token + '_accepted' if token else 'no_native_acceptance'
        check(result.get('sprt_decision') == decision, 'runner decision disagrees with independently supported decision')
        check(result.get('quality_gain_established') is (decision == 'H1_accepted'), 'runner quality-gain flag disagrees with decision')
        check(result.get('equal_clock_gain_established') is False, 'runner makes an unsupported equal-clock gain claim')
        for path, data in snapshots.items():
            check(path.read_bytes() == data, f'audited file changed while reading: {path}')
        if not errors:
            report.update(audit_status='passed', supported_decision=decision,
                          quality_gain_established=decision == 'H1_accepted')
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, IndexError, ArithmeticError, AttributeError) as error:
        errors.append(f'audit could not establish a supported result: {error}')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True, help='completed frozen SPRT run directory')
    parser.add_argument('--output', type=Path, required=True, help='new audit JSON outside the run directory')
    args = parser.parse_args()
    run = args.run.resolve(strict=True)
    output = args.output.resolve()
    if not run.is_dir():
        parser.error('--run must be a directory')
    if output.is_relative_to(run):
        parser.error('--output must be outside the frozen run directory')
    if output.exists():
        parser.error('--output must name a new file; existing audit files are never replaced')
    if not output.parent.is_dir():
        parser.error('--output parent directory must already exist')
    report = audit_run(run)
    report['audited_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    report['audit_script_sha256'] = digest(Path(__file__).read_bytes())
    with output.open('x', encoding='utf-8') as target:
        json.dump(report, target, indent=2, allow_nan=False)
        target.write('\n')
    print(json.dumps({'audit_status': report['audit_status'], 'supported_decision': report['supported_decision'],
                      'errors': report['errors'], 'audit_file': str(output)}, indent=2))
    return 0 if report['audit_status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
