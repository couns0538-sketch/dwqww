#!/usr/bin/env python3
"""Read-only independent audit of run 39348571407; never executes artifacts.

Run with the prepared python-chess environment. The archive helper is loaded
only from the immutable launch commit, never from the downloaded archive.
"""
import argparse
from collections import Counter
import datetime
import hashlib
import io
import json
import math
from pathlib import Path
import re
import subprocess
import tarfile
import types

import chess
import chess.pgn

LAUNCH = '563bd406e9112b61f1f33f20f8ff8c07adb9b2a0'
BASELINE = '4edda780c68a742f20565d4e6a54a0c99a2c88a6'
CANDIDATE = 'c5cbf97a7291a3bd960c71dcd77a29bf7c95ad8e'
FASTCHESS = '60d7a7a26c6b0582a15c112fb29a1829bef2adb3'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args])


def load(root, name):
    return json.loads((root / name).read_text())


def llr(penta):
    # Independent constrained multinomial MLE, bisection rather than native ITP.
    counts = [float(n) if n else 0.001 for n in penta]
    probs = [n / math.fsum(counts) for n in counts]
    scores = [0, .25, .5, .75, 1]
    fitted = []
    for elo in [0, 5]:
        target = 1 / (1 + 10 ** (-elo / 400))
        low, high = -1 / (1 - target), 1 / target
        for _ in range(120):
            theta = (low + high) / 2
            value = math.fsum(p * (s - target) / (1 + theta * (s - target))
                              for p, s in zip(probs, scores))
            if value == 0:
                break
            if value > 0:
                low = theta
            else:
                high = theta
        q = [p / (1 + theta * (s - target)) for p, s in zip(probs, scores)]
        assert abs(math.fsum(q) - 1) < 1e-9
        assert abs(math.fsum(s * v for s, v in zip(scores, q)) - target) < 1e-9
        fitted.append(q)
    result = math.fsum(n * math.log(b / a) for n, a, b in zip(counts, *fitted))
    assert math.isfinite(result)
    return result


def tar_contents(raw):
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as archive:
        contents = {}
        for member in archive:
            assert not member.name.startswith('/') and '..' not in Path(member.name).parts
            if member.isdir():
                continue
            assert member.isfile(), member.name
            assert member.name not in contents
            contents[member.name] = sha(archive.extractfile(member).read())
        return contents


def provenance(repo, root):
    result = {}
    maps = {}
    flags = ['-O3', '-DNDEBUG', '-march=x86-64-v3', '-mtune=generic',
             '-fno-fast-math', '-ffp-contract=off', '-fno-lto']
    artifacts = load(root, 'artifacts-SHA256.json')
    for name, expected in artifacts.items():
        assert file_sha(root / 'artifacts' / name) == expected
    for label, revision in [('baseline', BASELINE), ('candidate', CANDIDATE)]:
        record = load(root, label + '-build-provenance.json')
        assert record['source_commit'] == revision
        source = (root / 'source' / (label + '.tar')).read_bytes()
        expected = git(repo, 'archive', revision, 'CMakeLists.txt', 'LICENSE',
                       'src', 'include', 'tests', 'bench', 'tools')
        assert source == expected
        contents = tar_contents(source)
        assert contents == record['exported_source_sha256']
        maps[label] = contents
        assert sha(source) == record['source_tar_sha256']
        for name, digest in record['built_artifacts_sha256'].items():
            assert file_sha(root / 'artifacts' / label / name) == digest
        test_log = (root / (label + '-LastTest.log')).read_bytes()
        assert sha(test_log) == record['last_test_log_sha256']
        assert test_log.count(b'Test Passed.') == 9
        assert b'Test Failed.' not in test_log
        commands = load(root, label + '-compile-commands.json')
        for row in commands:
            assert all(flag in row['command'].split() for flag in flags)
            assert '/usr/bin/g++-14 ' in row['command']
            assert '-ffast-math' not in row['command'] and '-march=native' not in row['command']
        result[label] = {'source_commit': revision, 'source_tar_sha256': sha(source),
                         'source_files': len(contents), 'compile_commands': len(commands),
                         'release_ctest_passed': 9, 'source_bytes_equal_git_export': True,
                         'artifacts': record['built_artifacts_sha256']}
    fc_source = (root / 'source/fastchess.tar').read_bytes()
    assert fc_source == git(Path('/workspace/.cloud-setup/fastchess'), 'archive', FASTCHESS)
    result['fastchess'] = {'commit': FASTCHESS, 'source_tar_sha256': sha(fc_source),
                          'source_bytes_equal_git_export': True,
                          'sha256': artifacts['runner/fastchess']}
    result['changed_exported_paths'] = sorted(p for p in set(maps['baseline']) | set(maps['candidate'])
                                              if maps['baseline'].get(p) != maps['candidate'].get(p))
    return result


def final_inputs(root, digests):
    summary = load(root, 'strength/summary.json')
    rehash = load(root, 'strength/final-input-rehash.json')
    assert summary['final_input_rehash'] == rehash
    assert rehash['status'] == 'passed' and rehash['mismatches'] == []
    assert set(rehash['inputs']) == set(summary['frozen_inputs'])
    mapped = {}
    for name, digest in summary['frozen_inputs'].items():
        if '/hosted-results/' in name:
            relative = name.split('/hosted-results/', 1)[1]
        elif '/.github/hosted-nnue-strength/' in name:
            relative = 'package/' + name.split('/.github/hosted-nnue-strength/', 1)[1]
        elif name.endswith('/tools/match/windows_validate.py'):
            relative = 'windows_validate.py'
        elif name.endswith('/.github/workflows/forge-hosted-nnue-strength.yml'):
            relative = 'workflow.yml'
        else:
            raise AssertionError('Unmapped frozen input ' + name)
        assert digests[relative] == digest
        assert rehash['inputs'][name] == {'expected_sha256': digest,
                                        'actual_sha256': digest, 'matches': True}
        mapped[name] = relative
    return {'status': 'passed', 'inputs': len(mapped), 'all_mapped_to_actual_payload': True,
            'mapping': mapped}


def phase_audit(root, phase):
    base = root / 'strength' / phase
    manifest = load(base, 'manifest.json')
    state = load(base, 'state.json')
    assert manifest['status'] == 'completed' and manifest['exit_code'] == 0
    assert manifest['concurrency'] == state['concurrency'] == 1
    assert manifest['affinity'] == [0] and manifest['same_engine_threads'] == 1
    assert manifest['seed'] == state['seed'] == 20261021
    assert state['recover'] is False and state['noswap'] is False
    assert state['games'] == 2 and state['rounds'] == (4 if phase == 'aa' else 1024)
    for name in ['resign', 'draw', 'maxmoves', 'tb_adjudication']:
        assert state[name]['enabled'] is False
    for engine in state['engines']:
        assert engine['restart'] is True
        assert dict(engine['options']) == {'Threads': '1', 'Hash': '32',
                                           'Move Overhead': '10', 'OwnBook': 'false'}
        limit = engine['limit']
        assert limit['plies'] == 0
        if phase == 'sprt':
            assert limit['nodes'] == 0 and limit['tc']['time'] == 2000
            assert limit['tc']['increment'] == 20
        else:
            assert limit['nodes'] == 10000
    assert state['sprt']['enabled'] is (phase == 'sprt')
    if phase == 'sprt':
        assert {k: state['sprt'][k] for k in ['elo0', 'elo1', 'alpha', 'beta', 'model']} == {
            'elo0': 0, 'elo1': 5, 'alpha': .05, 'beta': .05, 'model': 'logistic'}
    assert FASTCHESS[:7] in manifest['fastchess_version']
    for name, row in manifest['inputs'].items():
        mapped = {'fastchess': 'artifacts/runner/fastchess', 'baseline': 'artifacts/baseline/forge',
                  'candidate': 'artifacts/baseline/forge' if phase == 'aa' else 'artifacts/candidate/forge',
                  'openings': 'package/openings/' + phase + '.epd'}[name]
        assert file_sha(root / mapped) == row['sha256']
    for name, expected in manifest['outputs'].items():
        assert file_sha(base / name) == expected
    runtime = load(root, 'package/provenance/runtime-order.json')[phase]
    selected = (base / 'selected.epd').read_bytes()
    assert sha(selected) == manifest['selected_sha256'] == runtime['selected_epd_sha256']
    ordered = selected.decode().splitlines()
    assert ordered == runtime['ordered_fens']
    reserved = (root / ('package/openings/' + phase + '.epd')).read_text().splitlines()
    assert sorted(reserved, key=lambda fen: hashlib.sha256(('20261021\n' + fen).encode()).digest()) == ordered

    wdl, penta, ends = [0, 0, 0], [0] * 5, Counter()
    prefix, pair, moves_total = {}, [], 0
    with (base / 'games.pgn').open() as f:
        count = 0
        while (game := chess.pgn.read_game(f)) is not None:
            count += 1
            assert not game.errors
            tags = game.headers
            assert int(tags['Round']) == (count + 1) // 2
            assert tags['Termination'] == 'normal'
            assert tags['White'] == ('Candidate' if count % 2 else 'Baseline')
            assert tags['Black'] == ('Baseline' if count % 2 else 'Candidate')
            assert ' '.join(tags['FEN'].split()[:4]) == ordered[(count - 1) // 2]
            # Pinned Fastchess serializes its untimed limit as PGN "-".
            assert tags['TimeControl'] == ('-' if phase == 'aa' else '2+0.02')
            board = game.board()
            assert board.is_valid()
            moves = []
            for move in game.mainline_moves():
                assert board.is_legal(move)
                moves.append(move.uci())
                board.push(move)
            assert len(moves) == int(tags['PlyCount'])
            moves_total += len(moves)
            outcome = board.outcome(claim_draw=True)
            assert outcome and outcome.result() == tags['Result'], (count, tags['Result'], outcome)
            ends[outcome.termination.name] += 1
            result = {'0-1': 0, '1/2-1/2': 1, '1-0': 2}[tags['Result']]
            score = result if count % 2 else 2 - result
            wdl[2 - score] += 1
            pair.append((tags['FEN'], tuple(moves), tags['Result'], score))
            if not count % 2:
                assert pair[0][0] == pair[1][0]
                if phase == 'aa':
                    assert pair[0][1:3] == pair[1][1:3]
                penta[pair[0][3] + pair[1][3]] += 1
                prefix[count] = (wdl.copy(), penta.copy())
                pair.clear()
    assert not pair and count == (8 if phase == 'aa' else 2048)
    expected_stats = load(base, 'stats.json')
    assert wdl == expected_stats['candidate_wins_draws_losses']
    assert penta == expected_stats['pentanomial_0_half_1_1half_2']
    assert expected_stats == manifest['statistics']
    native = state['stats']['Candidate vs Baseline']
    assert [native['wins'], native['draws'], native['losses']] == wdl
    assert [native['penta_LL'], native['penta_LD'], native['penta_WL'] + native['penta_DD'],
            native['penta_WD'], native['penta_WW']] == penta
    console = (base / 'console.txt').read_text()
    assert not re.search(r'^\s*(?:warning|error|fatal)\b|\[(?:WARN(?:ING)?|ERR(?:OR)?|FATAL)\s*\]', console, re.I | re.M)
    started = re.findall(r'^Started game (\d+) of \d+', console, re.M)
    finished = re.findall(r'^Finished game (\d+) .*?: (\S+) \{([^}]+)\}', console, re.M)
    assert list(map(int, started)) == list(range(1, count + 1))
    assert [int(row[0]) for row in finished] == list(range(1, count + 1))
    assert console.count('Finished match') == 1
    decisions = re.findall(r'SPRT[^\n]*completed - (H[01]) was accepted', console)
    assert decisions == []
    result = {'status': 'passed', 'games': count, 'pairs': count // 2, 'legal_plies': moves_total,
              'candidate_wins_draws_losses': wdl, 'pentanomial': penta,
              'legal_final_board_outcomes': dict(ends), 'orphan_pairs': 0,
              'native_acceptance_messages': decisions,
              'elapsed_seconds': manifest['elapsed_seconds'], 'normal_console_finishes': len(finished),
              'native_final_state': native}
    if phase == 'sprt':
        reports = re.findall(r'Games: (\d+), Wins: (\d+), Losses: (\d+), Draws: (\d+),[^\n]*\n'
                             r'Ptnml\(0-2\): \[([^\]]+)\][^\n]*\nLLR: (\S+)', console)
        assert len(reports) == 512
        differences = []
        for games, wins, losses, draws, bins, printed in reports:
            native_wdl = list(map(int, [wins, draws, losses]))
            native_penta = [int(n.strip()) for n in bins.split(',')]
            assert (native_wdl, native_penta) == prefix[int(games)]
            likelihood = llr(native_penta)
            assert -math.log(19) < likelihood < math.log(19)
            assert math.isfinite(float(printed))
            differences.append(abs(likelihood - float(printed)))
        assert max(differences) < .005000001
        final_token = re.findall(r'LLR:\s*(\S+)', console)[-1]
        assert math.isfinite(float(final_token))
        result.update(decision='inconclusive_at_pair_cap', independent_llr=llr(penta),
                      native_printed_final_llr=float(final_token), lower_bound=-math.log(19),
                      upper_bound=math.log(19), hypotheses=[0, 5], alpha=.05, beta=.05,
                      native_interim_reports_checked=len(reports),
                      maximum_printed_llr_difference=max(differences))
        assert result['elapsed_seconds'] < 18000
    else:
        assert result['elapsed_seconds'] < 90
    return result


def protocol_log_audit(root, phase):
    path = root / 'strength' / phase / 'fastchess.log'
    counters = Counter()
    exits = Counter()
    names = Counter()
    warnings = []
    pattern = re.compile(rb'\[(?:WARN(?:ING)?|ERR(?:OR)?|FATAL)\s*\]|^\s*(?:warning|error|fatal)\b', re.I)
    with path.open('rb') as f:
        for line in f:
            counters['lines'] += 1
            if pattern.search(line):
                warnings.append(line.decode(errors='replace')[:500])
            # Info rows dominate the 1.1 GB log; they contain none of the
            # lifecycle/settings counters below. Fault scanning still reads them.
            if b' ---> info ' in line:
                continue
            if b'<stderr>' in line:
                assert b'Process exited normally with status 0' in line
            if b'Process exited' in line:
                assert b'Process exited normally with status 0' in line
                exits[line.split(b' --->')[0].split()[-1].decode()] += 1
            if b' ---> id name ' in line:
                names[line.split(b' ---> id name ', 1)[1].strip().decode()] += 1
            for name, token in [('go', b' <--- go '), ('bestmove', b' ---> bestmove '),
                                ('uci', b' <--- uci\n'), ('quit', b' <--- quit\n'),
                                ('threads1', b' <--- setoption name Threads value 1\n'),
                                ('hash32', b' <--- setoption name Hash value 32\n'),
                                ('overhead10', b' <--- setoption name Move Overhead value 10\n'),
                                ('ownbookfalse', b' <--- setoption name OwnBook value false\n')]:
                if token in line:
                    counters[name] += 1
            if b' <--- setoption name Book File ' in line:
                raise AssertionError('Unexpected book path')
    assert warnings == []
    assert counters['go'] == counters['bestmove']
    games = 8 if phase == 'aa' else 2048
    assert exits == {'Candidate': games, 'Baseline': games}
    for name in ['uci', 'quit', 'threads1', 'hash32', 'overhead10', 'ownbookfalse']:
        assert counters[name] == 2 * games, (name, counters[name])
    expected_names = {'Chess Engine Forge 6.4.9 candidate': 2 * games} if phase == 'aa' else {
        'Chess Engine Forge 6.4.9 candidate': games,
        'Chess Engine Forge 6.4.11 candidate': games}
    assert names == expected_names
    return {'status': 'passed', 'bytes': path.stat().st_size, 'counts': dict(counters),
            'normal_process_exits': dict(exits), 'advertised_engine_names': dict(names),
            'warnings_errors_fatals': warnings}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, default=Path('/workspace/dwqww'))
    p.add_argument('--root', type=Path, default=Path('/workspace/.cloud-setup/nnue-strength-final-audit-39348571407'))
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    result = {'status': 'running', 'launch_commit': LAUNCH, 'engine_executions': 0,
              'python_chess_version': chess.__version__, 'checks': {}}
    def save():
        a.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    save()
    root = a.root / 'verified/files'
    try:
        helper_source = git(a.repo, 'show', LAUNCH + ':.github/hosted-nnue-strength/archive_results.py')
        helper = types.ModuleType('trusted_archive_results')
        exec(compile(helper_source, 'git:' + LAUNCH + ':archive_results.py', 'exec'), helper.__dict__)
        manifest = helper.verify_archive(a.root / 'archived-results/nnue-strength-39348571407-1.manifest.json')
        digests = {}
        for row in manifest['files']:
            actual = root / row['path']
            assert actual.stat().st_size == row['size']
            digest = file_sha(actual)
            assert digest == row['sha256']
            digests[row['path']] = digest
        result['archive'] = manifest['archive']
        result['parts'] = manifest['parts']
        result['checks']['archive_and_extracted_payload'] = {'status': 'passed', 'files': len(digests),
            'bytes': sum(x['size'] for x in manifest['files']), 'trusted_helper_sha256': sha(helper_source)}
        for path in sorted((root / 'package').rglob('*')):
            if path.is_file():
                relative = path.relative_to(root / 'package').as_posix()
                assert path.read_bytes() == git(a.repo, 'show', LAUNCH + ':.github/hosted-nnue-strength/' + relative)
        for archived, trusted in [('workflow.yml', '.github/workflows/forge-hosted-nnue-strength.yml'),
                                  ('windows_validate.py', 'tools/match/windows_validate.py')]:
            assert (root / archived).read_bytes() == git(a.repo, 'show', LAUNCH + ':' + trusted)
        assert (root / 'protocol.json').read_bytes() == (root / 'package/protocol.json').read_bytes()
        result['checks']['launch_package_matches_git'] = 'passed'
        save()
        result['checks']['build_provenance'] = provenance(a.repo, root)
        result['checks']['final_inputs'] = final_inputs(root, digests)
        summary = load(root, 'strength/summary.json')
        assert summary['status'] == 'completed_independently_audited'
        assert 'error' not in summary and 'final_input_error' not in summary
        assert summary['raw_files_preserved_without_trimming'] is True
        assert summary['protocol'] == load(root, 'protocol.json')
        assert (root / 'wrapper.log').stat().st_size == 0
        for field in ['wall_seconds', 'cpu_seconds']:
            rows = [load(root, 'strength/bench-%02d.json' % n) for n in range(8)]
            assert all(r['engine_nodes'] == 419798 for r in rows)
            ratios = [rows[i+1][field] / rows[i][field] for i in [2, 4, 6]]
            assert ratios == summary['bench_aa'][field]['ratios']
            assert .95 <= sorted(ratios)[1] <= 1.05 and all(.85 <= r <= 1.15 for r in ratios)
        result['checks']['gross_operational_calibration'] = summary['bench_aa']
        result['checks']['host_context'] = {k: summary[k] for k in ['original_affinity', 'selected_cpu',
            'started_utc', 'finished_utc', 'host_context_before', 'host_context_after']}
        save()
        for phase in ['aa', 'sprt']:
            result['checks'][phase] = phase_audit(root, phase)
            save()
            result['checks'][phase + '_raw_protocol_log'] = protocol_log_audit(root, phase)
            assert result['checks'][phase + '_raw_protocol_log']['counts']['go'] == result['checks'][phase]['legal_plies']
            save()
        result['decision'] = result['checks']['sprt']['decision']
        result['accepted_strength_gain'] = False
        result['status'] = 'passed'
        result['limitations'] = 'Native hosted Linux 6.4.11 versus 6.4.9 at 2+0.02 only. No pooling with prior runs; no NPS, Windows, Ryzen or Stockfish inference. Cap is inconclusive and does not establish equivalence.'
    except BaseException as error:
        result['status'] = 'failed'
        result['error'] = repr(error)
        save()
        raise
    result['finished_audit_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    save()
    print(json.dumps({k: v for k, v in result.items() if k != 'checks'}, indent=2))


if __name__ == '__main__':
    main()
