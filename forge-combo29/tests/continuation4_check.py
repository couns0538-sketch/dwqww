#!/usr/bin/env python3
"""Default-zero equivalence and nonzero legal-PV smoke, not a strength test."""
import json
import pathlib
import subprocess
import sys
from equivalence_screen import Engine, sha

out = pathlib.Path(sys.argv[1]).resolve()
fixtures = pathlib.Path(__file__).with_name('equivalence_positions.fen')
positions = fixtures.read_text().splitlines()
report = {'scope': 'Unproven search experiment; no speed or Elo claim',
          'depth': 7, 'positions': len(positions), 'fixture_sha256': sha(fixtures),
          'binaries': {}, 'zero_weight_comparisons': 0, 'nonzero_searches': 0,
          'changed_searches': 0, 'positive_weight_speed_path_comparisons': 0, 'pv_plies': None}
pvs = []
positive_reference = {}
for speed in [0, 1]:
    paths = [out / f's{speed}-e{experiment}' for experiment in [0, 1]]
    for experiment, path in enumerate(paths):
        report['binaries'][path.name] = sha(path)
        output = subprocess.run([str(path)], input='uci\nquit\n', text=True,
                                capture_output=True, check=True).stdout
        expected = 'option name Continuation4Weight type spin default 0 min 0 max 100'
        assert (expected in output) == bool(experiment), (path, 'option exposure')
    for nnue in [True, False]:
        baseline, candidate = [Engine(path, nnue) for path in paths]
        try:
            zero = []
            for fen in positions:
                reference = baseline.search(fen, 7)
                actual = candidate.search(fen, 7)
                assert actual == reference, (speed, nnue, fen, reference, actual)
                zero.append(actual)
                report['zero_weight_comparisons'] += 1
            for weight in [50, 100]:
                candidate.send(f'setoption name Continuation4Weight value {weight}')
                candidate.send('uci')
                advertised = candidate.until('uciok')
                assert f'option name Continuation4Weight type spin default {weight} min 0 max 100' in advertised
                for index, fen in enumerate(positions[:32]):
                    actual = candidate.search(fen, 7)
                    key = (nnue, weight, index)
                    if speed == 0:
                        positive_reference[key] = actual
                    else:
                        assert actual == positive_reference[key], (key, 'positive-weight speed-path mismatch')
                        report['positive_weight_speed_path_comparisons'] += 1
                    report['nonzero_searches'] += 1
                    report['changed_searches'] += actual != zero[index]
                    if actual['pv']:
                        assert actual['bestmove'] == actual['pv'][0]
                        pvs.append(fen + '\t' + ' '.join(actual['pv']))
            # UCI clamps out-of-range weights and rejects malformed integers.
            for raw, expected_weight in [('-1', 0), ('101', 100), ('bad', 100), ('0', 0)]:
                candidate.send(f'setoption name Continuation4Weight value {raw}')
                candidate.send('uci')
                lines = candidate.until('uciok')
                assert f'option name Continuation4Weight type spin default {expected_weight} min 0 max 100' in lines
                if raw == 'bad':
                    assert 'info string invalid value for option Continuation4Weight' in lines
            assert candidate.search(positions[0], 7) == zero[0], 'resetting weight to zero must recover baseline'
        finally:
            baseline.close()
            candidate.close()
assert report['changed_searches'] > 0, 'positive weight must exercise changed search'
legal = subprocess.run([str(out / 'pv-validator')], input='\n'.join(pvs) + '\n',
                       text=True, capture_output=True, check=True)
report['pv_plies'] = legal.stdout.strip()
report['status'] = 'PASS'
(out / 'continuation4_results.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
