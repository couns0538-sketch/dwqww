"""Audit the actual selected networks and original inputs after the native matrix closes."""
from pathlib import Path
import argparse, hashlib, json

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--native', type=Path, required=True)
parser.add_argument('--files', type=Path, required=True)
parser.add_argument('--before', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
controller = json.loads((args.native / 'forge_sol_S28_native_controller_result_20261025.json').read_text())
assert controller['status'] == 'PASS' and len(controller['runs']) == 4
rows = []
references = {
    '74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b': [308972,745494,2460422,11901452,31111774],
    '0fdf9bdb6bdf4c9f1622bcef29921912acb139fdf388e541b017a948118d4661': [328459,945640,3024381,9162399,20421972],
}
for run in controller['runs']:
    assert run['status'] == 'PASS' and run['exit'] == 0
    argv = run['argv']
    out = Path(argv[argv.index('--out') + 1])
    plan = json.loads((out / 'forge_sol_S28_plan_20261025.json').read_text())
    result = json.loads((out / 'forge_sol_S28_results_20261025.json').read_text())
    selected = plan['net_sha256']
    assert result['status'] == 'PASS_OBSERVATIONAL_NOT_ADOPTED' and result['input_immutability']['equal']
    for stage in result['stages']:
        source = out / ('forge_sol_S28_' + stage['id'] + '_source_20261025')
        net = source / 'src/nnue_weights.inc'
        assert digest(net) == selected
        allow = json.loads((out / ('forge_sol_S28_' + stage['id'] + '_known_fail_allowlist_20261025.json')).read_text())
        assert allow['source_sha256'][str(net)] == selected
        assert all(digest(Path(path)) == value for path, value in allow['source_sha256'].items())
        assert digest(Path(stage['engine'])) == stage['engine_sha256']
        assert [row['nodes'] for row in stage['off']] == references[selected]
        assert [row['nodes'] for row in stage['perft']] == [4865609,193690690]
        assert [row['count'] for row in stage['fma']] == [0,0]
        rows.append(dict(case=run['case'], stage=stage['id'], selected_net_sha256=selected,
                         actual_net_sha256=digest(net), engine_sha256=stage['engine_sha256'],
                         all_recorded_source_hashes_match=True, status='PASS'))
before = json.loads(args.before.read_text())
for base, relative in [('L','01_lock_src_h256_e12/forge_h256_e12_1ab50b2d_src'),
                       ('B','01b_base_h256_e12_buffix/forge_h256_e12_buffix_src')]:
    tree = args.files / relative
    current = {str(path.relative_to(tree)): digest(path) for path in sorted(tree.rglob('*')) if path.is_file()}
    assert current == before[base]
assert len(rows) == 10
record = dict(status='PASS', source_stages=rows, original_input_files=sum(map(len,before.values())),
              original_L_B_input_hashes_unchanged=True, accepted_lock='h256_e12 unchanged',
              scope='Ten actual copied nets, every retained source hash, executable identity and fixed numeric results; full filesystem syscall tracing not claimed.')
with args.out.open('x') as output:
    json.dump(record, output, indent=2)
    output.write('\n')
print('PASS: ten copied nets and executables; all original input files unchanged')
