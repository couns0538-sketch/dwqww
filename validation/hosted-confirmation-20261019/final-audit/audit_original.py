#!/usr/bin/env python3
"""Offline audit of original evidence. Executes no archived program and no engine.

Only read-only git show/cat-file inspect trusted repository objects. New output is
confined to this directory. Run with /workspace/.cloud-setup/venv/bin/python -B.
"""
import collections
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import re
import statistics
import subprocess
import sys
import traceback
import zipfile

import chess
import chess.pgn

sys.dont_write_bytecode = True
REPO = Path('/workspace/dwqww')
RAW = Path('/workspace/.cloud-setup/confirmation-recovered-39350375158/verified/files')
ART = RAW / 'original-artifact-files'
OUT = Path(__file__).resolve().parent
FROZEN = 'f1b44cc71554e8ea1ec61b3ca6adc90da65646b6'
SOURCES = {'baseline': '816423b1ddac23a00244449deef59dba736055a9',
           'candidate': '2c0c7efa49023d8e3f49de3f5596f333a3f01202'}
REPORT = {'status': 'in_progress', 'method': 'Independent legal replay and offline retained-evidence checks',
          'python_chess_version': chess.__version__, 'checks': [], 'sections': {},
          'scope': 'Original 6.4.7 versus 6.4.4; native hosted Linux only. No new match or engine execution.'}


def save():
    (OUT / 'audit-results.json').write_text(json.dumps(REPORT, indent=2, allow_nan=False) + '\n')


def check(name, passed, details=None):
    row = {'name': name, 'passed': bool(passed)}
    if details is not None:
        row['details'] = details
    REPORT['checks'].append(row)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def git_bytes(commit, path):
    return subprocess.run(['git', 'show', f'{commit}:{path}'], cwd=REPO,
                          check=True, capture_output=True).stdout


def load_trusted(name, relative):
    path = REPO / relative
    frozen_bytes = git_bytes(FROZEN, relative)
    check('trusted_module_' + name, path.read_bytes() == frozen_bytes, relative)
    if path.read_bytes() != frozen_bytes:
        raise ValueError('Trusted current module differs from frozen trusted source')
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def integrity():
    archive = RAW / 'original-downloads/artifact-12226439147.zip'
    check('original_official_zip_sha256', sha(archive) == '1dc3d43767bc95251acdf2ec363e4e79b8a00e15d16b1fbd3202ec644b9a5600', sha(archive))
    zip_rows = []
    with zipfile.ZipFile(archive) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            local = ART / info.filename
            h = hashlib.sha256()
            with z.open(info) as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b''):
                    h.update(block)
            digest = h.hexdigest()
            ok = local.is_file() and local.stat().st_size == info.file_size and sha(local) == digest
            check('original_zip_member:' + info.filename, ok)
            zip_rows.append({'path': info.filename, 'size': info.file_size, 'sha256': digest, 'matches_restored': ok})
    check('exact_original_zip_file_set', {r['path'] for r in zip_rows} == {p.relative_to(ART).as_posix() for p in ART.rglob('*') if p.is_file()})
    REPORT['sections']['original_zip'] = {'files': len(zip_rows), 'members': zip_rows}
    declared = json.loads((ART / 'artifacts-SHA256.json').read_text())
    binaries = {}
    for name, expected in declared.items():
        actual = sha(ART / 'artifacts' / name)
        check('archived_binary:' + name, actual == expected)
        binaries[name] = {'sha256': actual, 'size': (ART / 'artifacts' / name).stat().st_size}
    summary = json.loads((ART / 'confirmation/summary.json').read_text())
    final = json.loads((ART / 'confirmation/final-input-rehash.json').read_text())
    frozen_rows = []
    for original_path, expected in summary['frozen_inputs'].items():
        prefix = '/home/runner/work/dwqww/dwqww/'
        relative = original_path.removeprefix(prefix)
        if relative.startswith('hosted-results/'):
            local = ART / relative.removeprefix('hosted-results/')
            actual = sha(local)
        elif relative.startswith('.github/hosted-confirmation/'):
            local = ART / 'package' / relative.removeprefix('.github/hosted-confirmation/')
            actual = sha(local)
            check('frozen_package_vs_trusted_source:' + relative,
                  local.read_bytes() == git_bytes(FROZEN, relative))
        else:
            local = ART / ('windows_validate.py' if relative == 'tools/match/windows_validate.py' else 'workflow.yml')
            actual = sha(local)
            check('frozen_support_vs_trusted_source:' + relative, local.read_bytes() == git_bytes(FROZEN, relative))
        row = final['inputs'].get(original_path, {})
        ok = actual == expected == row.get('expected_sha256') == row.get('actual_sha256') and row.get('matches') is True
        check('initial_final_restored_hash:' + relative, ok)
        frozen_rows.append({'input': relative, 'sha256': actual, 'initial_final_restored_match': ok})
    check('final_rehash_complete', final['status'] == 'passed' and not final['mismatches'] and set(final['inputs']) == set(summary['frozen_inputs']))
    REPORT['sections']['artifacts'] = {'binaries': binaries, 'frozen_input_count': len(frozen_rows), 'inputs': frozen_rows}
    source_rows = {}
    for label, expected_commit in SOURCES.items():
        provenance = json.loads((ART / f'{label}-build-provenance.json').read_text())
        check('source_commit:' + label, provenance['source_commit'] == expected_commit)
        rows = []
        for path, expected in provenance['exported_source_sha256'].items():
            actual = hashlib.sha256(git_bytes(expected_commit, path)).hexdigest()
            check('source_blob:' + label + ':' + path, actual == expected)
            rows.append({'path': path, 'sha256': actual, 'matches_exported': actual == expected})
        for name, expected in provenance['built_artifacts_sha256'].items():
            check('build_provenance_binary:' + label + ':' + name, sha(ART / 'artifacts' / label / name) == expected == declared[f'{label}/{name}'])
        check('build_provenance_test_log:' + label, sha(ART / f'{label}-LastTest.log') == provenance['last_test_log_sha256'])
        testlog = (ART / f'{label}-LastTest.log').read_text()
        check('retained_release_tests:' + label, testlog.count('Test Passed.') == (7 if label == 'baseline' else 8) and 'Test Failed.' not in testlog)
        commands = json.loads((ART / f'{label}-compile-commands.json').read_text())
        bad = [c['file'] for c in commands if not all(flag in c['command'] for flag in ['g++-14', '-O3', '-DNDEBUG', '-march=x86-64-v3', '-mtune=generic', '-fno-fast-math', '-ffp-contract=off', '-std=gnu++20'])]
        check('actual_compile_flags:' + label, not bad, {'entries': len(commands), 'bad': bad})
        source_rows[label] = {'source_commit': expected_commit, 'verified_exported_files': rows, 'retained_release_tests_passed': testlog.count('Test Passed.')}
    REPORT['sections']['source_to_binary_provenance'] = source_rows
    save()


def opening_and_calibration():
    prov = json.loads((ART / 'package/provenance/openings-selection.json').read_text())
    exclusions = set(prov['exclusions']['canonical_positions'])
    all_positions = []
    runtime = json.loads((ART / 'package/provenance/runtime-order.json').read_text())
    rows = {}
    corpus = (REPO / 'tools/openings/forge-10000.epd').read_text().splitlines()
    check('original_opening_corpus_hash', sha(REPO / 'tools/openings/forge-10000.epd') == prov['corpus']['sha256'])
    for phase, cap in [('aa', 4), ('sprt', 160)]:
        lines = (ART / f'package/openings/{phase}.epd').read_text().splitlines()
        selected = (ART / f'confirmation/{phase}/selected.epd').read_text().splitlines()
        expected_order = sorted(lines, key=lambda fen: hashlib.sha256(f'20261020\n{fen}'.encode('ascii')).digest())
        check('exact_runtime_opening_order:' + phase, selected == expected_order == runtime[phase]['ordered_fens'])
        check('opening_uniqueness_and_cap:' + phase, len(selected) == cap == len(set(selected)))
        check('fresh_prior_exclusion:' + phase, not set(selected) & exclusions)
        for row in prov['selections'][phase]:
            check('opening_source_row:' + phase + ':' + str(row['source_line']),
                  ' '.join(corpus[row['source_line'] - 1].split()[:4]) == row['fen'] and row['fen'].split()[3] == '-')
        all_positions += selected
        rows[phase] = {'count': len(selected), 'selected_sha256': sha(ART / f'confirmation/{phase}/selected.epd'), 'prior_exclusion_overlap': len(set(selected) & exclusions)}
    check('AA_SPRT_disjoint', len(all_positions) == len(set(all_positions)))
    bench = [json.loads((ART / f'confirmation/bench-{i:02}.json').read_text()) for i in range(8)]
    for i, row in enumerate(bench):
        stdout = (ART / f'confirmation/bench-{i:02}.stdout').read_text()
        check('bench_signature:' + str(i), row['index'] == i and row['warmup'] == (i < 2) and row['engine_nodes'] == 419798 and re.search(r'bench depth 11 nodes 419798 time \d+ nps \d+', stdout) and not (ART / f'confirmation/bench-{i:02}.stderr').stat().st_size)
    gates = {}
    for clock in ['wall_seconds', 'cpu_seconds']:
        ratios = [bench[i + 1][clock] / bench[i][clock] for i in [2, 4, 6]]
        median = statistics.median(ratios)
        check('bench_AA_gate:' + clock, .95 <= median <= 1.05 and all(.85 <= r <= 1.15 for r in ratios))
        gates[clock] = {'ratios': ratios, 'median': median}
    REPORT['sections']['openings_calibration'] = {'openings': rows, 'prior_frozen_exclusion_positions': len(exclusions), 'bench_AA': gates, 'bench_runs': 8, 'excluded_warmups': 2}
    save()


def replay(phase, statsmod):
    text = (ART / f'confirmation/{phase}/games.pgn').read_text()
    bookkeeping = statsmod.summarize(text, require_identical_pairs=phase == 'aa')
    stream = io.StringIO(text)
    records, expectations = [], []
    outcomes = collections.Counter()
    selected = (ART / f'confirmation/{phase}/selected.epd').read_text().splitlines()
    min_timeleft = math.inf
    while (game := chess.pgn.read_game(stream)) is not None:
        index = len(records)
        h = dict(game.headers)
        check(f'{phase}:parse:{index+1}', not game.errors)
        b = game.board()
        check(f'{phase}:valid_initial_board:{index+1}', b.is_valid())
        moves = list(game.mainline_moves())
        check(f'{phase}:ply_count:{index+1}', len(moves) == int(h['PlyCount']))
        check(f'{phase}:opening_prefix:{index+1}', ' '.join(h['FEN'].split()[:4]) == selected[index // 2])
        check(f'{phase}:round_color_order:{index+1}', int(h['Round']) == index // 2 + 1 and h['White'] == ('Candidate' if index % 2 == 0 else 'Baseline'))
        check(f'{phase}:tc:{index+1}', h['TimeControl'] == ('-' if phase == 'aa' else '2+0.02'))
        expected = {'Candidate': [], 'Baseline': []}
        prefix = []
        for ply, move in enumerate(moves):
            legal = b.is_legal(move)
            if not legal:
                raise ValueError(f'{phase} game{index+1} ply{ply+1} illegal {move}')
            side = h['White'] if b.turn == chess.WHITE else h['Black']
            command = 'position fen ' + h['FEN'] + (' moves ' + ' '.join(prefix) if prefix else '')
            expected[side].append((command, move.uci()))
            prefix.append(move.uci())
            b.push(move)
        outcome = b.outcome(claim_draw=True)
        check(f'{phase}:final_result:{index+1}', outcome is not None and outcome.result() == h['Result'], {'reason': outcome.termination.name if outcome else None, 'result': h['Result']})
        if outcome:
            outcomes[outcome.termination.name] += 1
        for t in re.findall(r'\btl=(-?[\d.]+)s', game.end().comment):
            min_timeleft = min(min_timeleft, float(t))
        records.append({'game': index+1, 'round': int(h['Round']), 'white': h['White'], 'result': h['Result'], 'plies': len(moves), 'termination': h['Termination'], 'replayed_outcome': outcome.termination.name if outcome else None})
        expectations.append(expected)
    # Check all recorded clocks, rather than only final comments.
    clocks = [float(t) for t in re.findall(r'\btl=(-?[\d.]+)s', text)]
    check(phase + ':all_recorded_clocks_nonnegative', bool(clocks) and min(clocks) >= 0)
    cap = 4 if phase == 'aa' else 160
    check(phase + ':all_games_and_pairs', len(records) == 2 * cap == bookkeeping['games'] and bookkeeping['pairs'] == cap)
    (OUT / (phase + '-legal-replay.json')).write_text(json.dumps({'games': records}, indent=2) + '\n')
    REPORT['sections'][phase + '_legal_replay'] = {'statistics': bookkeeping, 'legal_plies': sum(r['plies'] for r in records), 'final_outcomes': dict(outcomes), 'recorded_clock_annotations': len(clocks), 'minimum_recorded_timeleft_seconds': min(clocks), 'all_initial_fens_match_exact_selected_prefix': True}
    save()
    return records, expectations, bookkeeping


def raw_exchanges(phase, expectations):
    counts = collections.defaultdict(collections.Counter)
    sessions = {'Candidate': -1, 'Baseline': -1}
    cursor = {'Candidate': 0, 'Baseline': 0}
    active = {'Candidate': None, 'Baseline': None}
    errors = []
    ids = collections.defaultdict(collections.Counter)
    settings = collections.defaultdict(collections.Counter)
    all_lines, nonengine = 0, []
    rx = re.compile(r'\b(Candidate|Baseline) (<---|--->) (.*)$')
    with (ART / f'confirmation/{phase}/fastchess.log').open() as f:
        for lineno, line in enumerate(f, 1):
            all_lines += 1
            if not line.startswith('[Engine]'):
                if line.strip(): nonengine.append({'line': lineno, 'text': line.strip()})
                continue
            match = rx.search(line.rstrip('\n'))
            if not match:
                errors.append(f'unparsed engine line {lineno}'); continue
            side, direction, msg = match.groups()
            if direction == '<---':
                first = msg.split()[0]
                counts[side][first] += 1
                if msg == 'uci':
                    if sessions[side] >= 0 and cursor[side] != len(expectations[sessions[side]][side]):
                        errors.append(f'incomplete session {side}:{sessions[side]}')
                    sessions[side] += 1
                    cursor[side] = 0
                if msg.startswith('setoption '): settings[side][msg] += 1
                if msg.startswith('position '):
                    i, j = sessions[side], cursor[side]
                    if i >= len(expectations) or j >= len(expectations[i][side]) or msg != expectations[i][side][j][0]:
                        errors.append(f'position mismatch {side} session{i} move{j} line{lineno}')
                    active[side] = msg
                if msg.startswith('go '):
                    if phase == 'aa' and msg != 'go nodes 10000': errors.append(f'AA go mismatch line{lineno}: {msg}')
                    if phase == 'sprt' and not re.fullmatch(r'go wtime \d+ btime \d+ winc 20 binc 20', msg): errors.append(f'SPRT go mismatch line{lineno}: {msg}')
            else:
                if msg.startswith('id name '): ids[side][msg] += 1
                if msg in ['uciok', 'readyok'] or msg.startswith('option name Ponder ') or msg.startswith('option name Book File ') or msg.startswith('Process exited '): counts[side][msg] += 1
                if msg.startswith('bestmove '):
                    counts[side]['bestmove'] += 1
                    i, j = sessions[side], cursor[side]
                    if i >= len(expectations) or j >= len(expectations[i][side]) or msg.split()[1] != expectations[i][side][j][1] or active[side] != expectations[i][side][j][0]:
                        errors.append(f'bestmove mismatch {side} session{i} move{j} line{lineno}')
                    cursor[side] += 1
    cap = len(expectations)
    for side in sessions:
        check(f'{phase}:raw_complete_last_session:{side}', cursor[side] == len(expectations[sessions[side]][side]))
        check(f'{phase}:raw_restart_count:{side}', sessions[side] + 1 == cap == counts[side]['uci'] == counts[side]['ucinewgame'] == counts[side]['quit'] == counts[side]['Process exited normally with status 0'])
        check(f'{phase}:raw_paired_search_count:{side}', counts[side]['position'] == counts[side]['go'] == counts[side]['bestmove'] == sum(len(e[side]) for e in expectations))
        expected_settings = {f'setoption name {k} value {v}': cap for k, v in [('Threads','1'),('Hash','32'),('Move Overhead','10'),('OwnBook','false')]}
        check(f'{phase}:raw_exact_setoptions:{side}', dict(settings[side]) == expected_settings)
        check(f'{phase}:raw_runtime_defaults:{side}', counts[side]['option name Ponder type check default false'] == cap == counts[side]['option name Book File type string default <empty>'])
        version = '6.4.7' if phase == 'sprt' and side == 'Candidate' else '6.4.4'
        check(f'{phase}:raw_engine_identity:{side}', dict(ids[side]) == {f'id name Chess Engine Forge {version} candidate': cap})
    check(phase + ':raw_all_positions_and_bestmoves_match_PGN', not errors, errors[:20])
    check(phase + ':raw_no_nonengine_faults', not nonengine, nonengine[:20])
    REPORT['sections'][phase + '_raw_exchanges'] = {'lines_scanned': all_lines, 'bytes': (ART / f'confirmation/{phase}/fastchess.log').stat().st_size, 'counts_by_side': {k:dict(v) for k,v in counts.items()}, 'settings_by_side': {k:dict(v) for k,v in settings.items()}, 'errors': errors, 'nonengine_lines': nonengine}
    save()


def stats_and_protocol(records, stats, validator):
    phase = ART / 'confirmation/sprt'
    console = (phase / 'console.txt').read_text()
    penta = stats['pentanomial_0_half_1_1half_2']
    llr = validator.logistic_llr(penta, 0, 10)
    native = validator.final_llr(console)
    check('native_final_llr_agreement', abs(llr - native) <= .005000001)
    check('native_no_acceptance', validator.native_acceptance(console) is None)
    check('native_finished_at_cap', console.rstrip().endswith('Total Time: 00:34:10 (hours:minutes:seconds)') and 'Finished match' in console)
    check('native_started_finished_games', [int(x) for x in re.findall(r'^Started game (\d+) of 320', console, re.M)] == list(range(1,321)) == [int(x) for x in re.findall(r'^Finished game (\d+) ', console, re.M)])
    check('native_no_fault_console', not re.search(r'^\s*(?:warning|error|fatal)\b|\[(?:WARN(?:ING)?|ERR(?:OR)?|FATAL)\s*\]', console, re.I|re.M))
    counts, sequential = [0]*5, []
    wdl = [0]*3
    for i in range(0, len(records), 2):
        scores = []
        for rec in records[i:i+2]:
            score = {'1-0':2, '1/2-1/2':1, '0-1':0}[rec['result']]
            if rec['white'] != 'Candidate': score = 2-score
            scores.append(score)
            wdl[2-score] += 1
        counts[sum(scores)] += 1
        value = validator.logistic_llr(counts, 0, 10)
        sequential.append({'pairs': i//2+1, 'penta': counts.copy(), 'llr': value})
    check('no_independent_prefix_boundary', all(abs(r['llr']) < math.log(19) for r in sequential))
    blocks = re.findall(r'Games: (\d+), Wins: (\d+), Losses: (\d+), Draws: (\d+),[^\n]*\nPtnml\(0-2\): \[([^\]]+)\][^\n]*\nLLR: (\S+)', console)
    native_prefix_rows = []
    for games, wins, losses, draws, bins, printed in blocks:
        row = sequential[int(games)//2-1]
        ns = [int(x.strip()) for x in bins.split(',')]
        ok = row['penta'] == ns and abs(row['llr'] - float(printed)) <= .005000001
        check('native_prefix:' + games, ok)
        native_prefix_rows.append({'games':int(games), 'printed_llr':float(printed), 'independent_llr':row['llr']})
    n = sum(penta)
    mu = math.fsum(c*i/4 for i,c in enumerate(penta))/n
    variance = math.fsum(c*(i/4-mu)**2 for i,c in enumerate(penta))/n
    z = 1.959963984540054
    se = math.sqrt(variance/n)
    elo = lambda s: 400*math.log10(s/(1-s))
    estimate, lo, hi = elo(mu), elo(mu-z*se), elo(mu+z*se)
    native_elo = re.findall(r'^Elo: ([+-]?[\d.]+) \+/- ([\d.]+)', console, re.M)[-1]
    check('native_elo_uncertainty_crosscheck', abs(estimate-float(native_elo[0])) < .005000001 and abs((hi-lo)/2-float(native_elo[1])) < .005000001)
    state = json.loads((phase / 'state.json').read_text())
    manifest = json.loads((phase / 'manifest.json').read_text())
    check('sprt_state_settings', state['sprt'] == {'alpha':.05,'beta':.05,'elo0':0.,'elo1':10.,'model':'logistic','enabled':True} and state['rounds']==160 and state['games']==2 and state['concurrency']==1 and state['seed']==20261020 and not state['recover'] and not state['noswap'])
    check('no_strength_adjudication', all(not state[k]['enabled'] for k in ['resign','draw','maxmoves','tb_adjudication']))
    for engine in state['engines']:
        check('equal_engine_limits:' + engine['name'], engine['restart'] and engine['options'] == [['Threads','1'],['Hash','32'],['Move Overhead','10'],['OwnBook','false']] and engine['limit']=={'tc':{'increment':20,'fixed_time':0,'time':2000,'moves':0,'timemargin':0},'nodes':0,'plies':0})
    check('pinned_runner_version', manifest['fastchess_version']=='fastchess alpha 1.8.2 20260912-60d7a7a')
    check('retained_match_exit_zero', manifest['exit_code']==0 and manifest['status']=='completed')
    for name, expected in manifest['outputs'].items(): check('retained_manifest_output:' + name, sha(phase/name)==expected)
    REPORT['sections']['strength_statistics'] = {'candidate_wins_draws_losses': wdl, 'penta':penta, 'score_fraction':mu, 'native_final_llr':native, 'independent_final_llr':llr, 'bounds':[-math.log(19),math.log(19)], 'native_acceptance':None, 'decision':'inconclusive_at_pair_cap', 'pairs':n, 'games':2*n, 'minimum_prefix_llr':min(r['llr'] for r in sequential), 'maximum_prefix_llr':max(r['llr'] for r in sequential), 'prefixes_audited':len(sequential), 'native_printed_prefixes_crosschecked':len(native_prefix_rows), 'elo_estimate':estimate, 'paired_approximate_95pct_interval':[lo,hi], 'native_elo_display':native_elo, 'paired_variance':variance, 'paired_score_standard_error':se, 'uncertainty_method':'Pair scores X in {0,.25,.5,.75,1}; empirical population variance v=sum(n_i*(X_i-mean)^2)/160; normal-score interval mean +/-1.959963984540054*sqrt(v/160), transformed by 400*log10(p/(1-p)). Descriptive fixed-cap large-sample interval, not a sequential confidence sequence; no strength acceptance.'}
    (OUT/'sequential-likelihood.json').write_text(json.dumps({'independent_complete_pair_prefixes':sequential,'native_crosschecks':native_prefix_rows},indent=2)+'\n')
    save()


def publication():
    path = RAW/'original-downloads/job-118334929163.log'
    lines = path.read_text().splitlines()
    evidence = [{'line':i+1,'text':line} for i,line in enumerate(lines) if ('152.78 MB' in line or 'pre-receive hook declined' in line or 'failed to push some refs' in line)]
    check('publication_failure_original_log', any('152.78 MB' in r['text'] and '100.00 MB' in r['text'] for r in evidence))
    check('original_publication_log_hash', sha(path)=='ad0418f6dd935baa7a02b3f82fc3065096a46ab1a393c4c9489987f40491eaf6')
    REPORT['sections']['publication_failure']={'cause':'Original results branch push rejected because raw Fastchess log exceeds GitHub 100MB file limit; completed match itself was retained by official artifact upload.', 'log_sha256':sha(path),'raw_fastchess_log_bytes':(ART/'confirmation/sprt/fastchess.log').stat().st_size,'original_log_evidence':evidence}
    save()


if '--supplement' in sys.argv:
    REPORT = json.loads((OUT / 'audit-results.json').read_text())
    # Recheck only the two auditor formatting assumptions that failed. GCC's
    # gnu++20 is the retained C++20 dialect; PGN encodes unlimited time as '-'.
    replaced = [c for c in REPORT['checks'] if c['name'].startswith('actual_compile_flags:') or c['name'].startswith('aa:tc:')]
    REPORT['checks'] = [c for c in REPORT['checks'] if c not in replaced]
    for label in SOURCES:
        commands = json.loads((ART / f'{label}-compile-commands.json').read_text())
        bad = [c['file'] for c in commands if not all(flag in c['command'] for flag in ['g++-14', '-O3', '-DNDEBUG', '-march=x86-64-v3', '-mtune=generic', '-fno-fast-math', '-ffp-contract=off', '-std=gnu++20'])]
        check('actual_compile_flags:' + label, not bad, {'entries':len(commands),'bad':bad,'retained_dialect':'GNU C++20'})
    aa_text = (ART/'confirmation/aa/games.pgn').read_text()
    aa_tcs = re.findall(r'^\[TimeControl "([^\"]+)"\]', aa_text, re.M)
    for i, tc in enumerate(aa_tcs, 1):
        check('aa:tc:' + str(i), tc == '-', {'PGN_unlimited_clock_marker':tc})
    check('aa_unlimited_clock_PGN_count', len(aa_tcs)==8)
    native_state = json.loads((ART/'confirmation/aa/state.json').read_text())
    check('aa_unlimited_clock_node_state', all(e['limit']['nodes']==10000 and e['limit']['tc']['time']==0 and e['limit']['tc']['increment']==0 for e in native_state['engines']))
    prior = set()
    for phase in ['aa','sprt']:
        prior.update(' '.join(line.split()[:4]) for line in git_bytes(FROZEN,'.github/hosted-strength/openings/'+phase+'.epd').decode().splitlines() if line.strip())
    current = set()
    for phase in ['aa','sprt']:
        current.update((ART/f'confirmation/{phase}/selected.epd').read_text().splitlines())
    check('disjoint_from_entire_504_prior_hosted_registry', len(prior)==504 and not prior & current, {'prior_positions':len(prior),'new_positions':len(current),'overlap':len(prior&current)})
    job = (RAW/'original-downloads/job-118334929163.log').read_text()
    version_evidence = [{'line':i+1,'text':line} for i,line in enumerate(job.splitlines()) if ('HEAD is now at 60d7a7a' in line or 'fastchess alpha 1.8.2 20260912-60d7a7a' in line or 'g++-14 (Ubuntu' in line or '100% tests passed' in line)]
    check('original_fastchess_checkout_and_runtime_version', any('HEAD is now at 60d7a7a' in r['text'] for r in version_evidence) and any('fastchess alpha 1.8.2 20260912-60d7a7a' in r['text'] for r in version_evidence))
    binary = (ART/'artifacts/runner/fastchess').read_bytes()
    check('retained_fastchess_elf_and_embedded_pin', binary.startswith(b'\x7fELF') and b'60d7a7a' in binary)
    native_source_rel = 'app/src/matchmaking/elo/elo_pentanomial.cpp'
    native_source = subprocess.run(['git','show','60d7a7a26c6b0582a15c112fb29a1829bef2adb3:'+native_source_rel],cwd='/workspace/.cloud-setup/fastchess',capture_output=True,check=True).stdout
    check('native_paired_CI_formula_source', all(token in native_source for token in [b'variance_ / pairs_',b'CI95ZSCORE * std::sqrt(variance_per_pair_)',b'error_             = (scoreToEloDiff(scoreUpperBound_) - scoreToEloDiff(scoreLowerBound_)) / 2.0']))
    REPORT['sections']['supplemental_rechecks'] = {'auditor_assumptions_corrected':'Initial helper expected -std=c++20 and TimeControl inf literal. Retained compiler uses -std=gnu++20 and standard PGN unlimited-clock marker -. Original command/state and raw go nodes10000 confirm intended settings. Only these affected checks repeated; full legal replay, hashes and raw exchange checks were already complete.', 'original_assumption_failures':replaced,'compiler_runner_original_log_evidence':version_evidence,'pinned_native_CI_source_sha256':hashlib.sha256(native_source).hexdigest()}
    failed = [c['name'] for c in REPORT['checks'] if not c['passed']]
    REPORT['failed_checks']=failed
    REPORT['status']='all_offline_audit_checks_passed_inconclusive_match' if not failed else 'audit_findings_require_review'
    save()
    print(json.dumps({'status':REPORT['status'],'checks':len(REPORT['checks']),'failed':failed},indent=2))
    sys.exit(0 if not failed else 1)

try:
    save()
    integrity()
    opening_and_calibration()
    statsmod = load_trusted('audit_trusted_pgn_stats', '.github/hosted-confirmation/match/pgn_stats.py')
    validator = load_trusted('audit_trusted_validator', 'tools/match/windows_validate.py')
    aa_records, aa_expected, aa_stats = replay('aa', statsmod)
    raw_exchanges('aa', aa_expected)
    records, expected, stats = replay('sprt', statsmod)
    raw_exchanges('sprt', expected)
    stats_and_protocol(records, stats, validator)
    publication()
    failed = [c['name'] for c in REPORT['checks'] if not c['passed']]
    REPORT['failed_checks'] = failed
    REPORT['status'] = 'all_offline_audit_checks_passed_inconclusive_match' if not failed else 'audit_findings_require_review'
    save()
    print(json.dumps({'status':REPORT['status'],'checks':len(REPORT['checks']),'failed':failed,'sections':list(REPORT['sections'])},indent=2))
except Exception as error:
    REPORT['status']='audit_interrupted_or_error'
    REPORT['error']=repr(error)
    REPORT['traceback']=traceback.format_exc()
    save()
    raise
