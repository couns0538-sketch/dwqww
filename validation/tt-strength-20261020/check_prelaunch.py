#!/usr/bin/env python3
"""Read-only package/source/trigger checks; does not build, play, push or launch."""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import yaml


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--require-ready', action='store_true')
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    package = repo / '.github/hosted-tt-strength'
    protocol = json.loads((package / 'protocol.json').read_text())
    assert protocol['candidate_sha'] == '8865666cc0ab4961cd507bae40ff6ce44e9319df'
    assert protocol['baseline_sha'] == 'c5cbf97a7291a3bd960c71dcd77a29bf7c95ad8e'
    assert protocol['candidate_version'] == '6.4.12' and protocol['baseline_version'] == '6.4.11'
    assert protocol['status'] in ('PENDING_REVIEW', 'PREREGISTERED_REVIEWED_READY_FOR_SINGLE_PUSH')
    spec = importlib.util.spec_from_file_location('strength_prelaunch_gate', package / 'run_hosted.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    ready = protocol['status'] == 'PREREGISTERED_REVIEWED_READY_FOR_SINGLE_PUSH'
    if ready:
        module.require_launch_protocol(protocol)
        assert protocol['source_gates_status'] == 'PASSED'
        evidence = protocol.get('correctness_evidence_sha256', {})
        assert evidence, 'Root correctness proof-file hashes required before launch'
        for path, digest in evidence.items():
            assert hashlib.sha256((repo / path).read_bytes()).hexdigest() == digest, path
    else:
        try:
            module.require_launch_protocol(protocol)
        except ValueError as error:
            assert 'review' in str(error)
        else:
            raise AssertionError('Pending-review gate did not reject')
    if args.require_ready:
        assert ready, 'Final source validation/review has not enabled this launch'
    workflow = repo / '.github/workflows/forge-hosted-tt-strength.yml'
    cfg = yaml.load(workflow.read_text(), Loader=yaml.BaseLoader)
    assert cfg['on'] == {'push': {'branches': ['forge/hosted-tt-strength-20261020-*']}}
    job = cfg['jobs']['tt-strength']
    assert job['if'] == 'github.run_attempt == 1' and job['timeout-minutes'] == '330'
    assert job['steps'][1]['timeout-minutes'] == '6' and job['steps'][2]['timeout-minutes'] == '310'
    for name in ('BASELINE', 'CANDIDATE', 'FASTCHESS'):
        assert job['env'][name + '_SHA'] == protocol[name.lower() + '_sha']
    commands = []
    for step in job['steps']:
        if 'run' in step:
            subprocess.run(['bash', '-n'], input=step['run'], text=True, check=True)
            commands.append(step['run'])
    build = commands[0]
    assert build.index('gate.require_launch_protocol(p)') < build.index('if ! command -v g++-14') < build.index('cmake -S')
    assert "-ffp-contract=off -fno-lto'" in build
    assert '-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF -DFORGE_NATIVE=OFF' in build
    assert '-pgnout' in (package / 'match/run_match.py').read_text()
    for path in package.rglob('*.py'):
        ast.parse(path.read_text(), filename=str(path))
    runtime = json.loads((package / 'provenance/runtime-order.json').read_text())
    pools = {}
    for phase, count in [('aa', 4), ('sprt', 1024)]:
        raw = (package / ('openings/' + phase + '.epd')).read_bytes()
        fens = raw.decode().splitlines()
        assert len(fens) == len(set(fens)) == count and all(fen.split()[3] == '-' for fen in fens)
        ordered = sorted(fens, key=lambda fen: hashlib.sha256(('20261022\n' + fen).encode('ascii')).digest())
        ordered_bytes = ('\n'.join(ordered) + '\n').encode('ascii')
        assert ordered == runtime[phase]['ordered_fens']
        assert hashlib.sha256(ordered_bytes).hexdigest() == runtime[phase]['selected_epd_sha256']
        assert ordered_bytes == (package / ('provenance/runtime-' + phase + '.epd')).read_bytes()
        pools[phase] = set(fens)
    assert not pools['aa'] & pools['sprt']
    selection = json.loads((package / 'provenance/openings-selection.json').read_text())
    assert selection['prospective_selection']['seed'] == '20261020-tt-exclusive-drain-strength-v1'
    nnue = selection['nnue_strength_reserved_exclusion']
    assert nnue['positions'] == 1028
    assert not (pools['aa'] | pools['sprt']) & set(nnue['canonical_positions'])
    assert hashlib.sha256((repo / nnue['selection_path']).read_bytes()).hexdigest() == nnue['selection_sha256']
    source_inventory = json.loads((Path(__file__).parent / 'source-inputs-SHA256.json').read_text())
    for path, row in source_inventory.items():
        for label in ('baseline', 'candidate'):
            digest = row[label + '_sha256']
            if digest is not None:
                raw = subprocess.check_output(['git', 'show', protocol[label + '_sha'] + ':' + path], cwd=repo)
                assert hashlib.sha256(raw).hexdigest() == digest, 'Frozen source mismatch: ' + label + ':' + path
    checksum = subprocess.run(['sha256sum', '-c', str(package / 'PACKAGE-SHA256SUMS')], cwd=repo,
                              text=True, capture_output=True, check=False)
    assert checksum.returncode == 0, checksum.stdout + checksum.stderr
    result = {'status': 'passed', 'protocol_status': protocol['status'], 'launch_authorized': ready,
              'candidate_sha': protocol['candidate_sha'], 'candidate_version': '6.4.12',
              'baseline_sha': protocol['baseline_sha'], 'workflow_yaml_and_bash': 'passed',
              'budgets_minutes': {'job': 330, 'build': 6, 'match': 310},
              'trigger': 'only new launch branch prefix; attempt1',
              'unchanged_unique_disjoint_ep_none_pools': {'aa': 4, 'sprt': 1024},
              'exact_frozen_runtime_order_and_sha': 'passed', 'runtime_seed': 20261022,
              'source_inventory_files_checked': len(source_inventory), 'source_bytes_match_frozen_git_objects': True,
              'active_nnue_reserved_positions_excluded': 1028,
              'package_and_workflow_sha_registry': 'passed', 'engine_executions': 0}
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
