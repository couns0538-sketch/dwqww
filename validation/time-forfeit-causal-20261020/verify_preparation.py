#!/usr/bin/env python3
"""Read-only offline preparation audit: never imports or launches an engine."""
import ast
import gzip
import hashlib
import json
from pathlib import Path
import re
import tarfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE/name).read_text())


def checked(path, expected):
    assert sha(path) == expected, str(path)


def function(path, name):
    matches = [node for node in ast.walk(ast.parse(path.read_text()))
               if isinstance(node, ast.FunctionDef) and node.name == name]
    assert len(matches) == 1, name
    return ast.dump(matches[0], include_attributes=False)


def main():
    protocol, source, build = map(read, ['PROTOCOL.json', 'SOURCE.json', 'BUILD.json'])
    assert protocol['baseline_sha'] == source['baseline_sha'] == build['baseline_sha']
    assert source['timing_execution'] is False and build['engine_executed'] is False
    assert build['status'] == 'PASS_BUILD_ONLY'
    for field, name in [('source_manifest_sha256', 'SOURCE.json'),
                        ('build_provenance_sha256', 'BUILD.json'),
                        ('runner_sha256', 'run_diagnostic.py'),
                        ('analysis_sha256', 'analyze_diagnostic.py'),
                        ('diagnostic_header_sha256', 'time_diagnostic.hpp'),
                        ('instrumentation_patch_sha256', 'instrumentation.patch')]:
        checked(HERE/name, protocol[field])
    checked(HERE/'SOURCE.json', build['source_manifest_sha256'])
    assert protocol['source_export'] == source['source_export']
    exported = Path(source['source_export'])
    inventory = {str(p.relative_to(exported)): sha(p)
                 for p in exported.rglob('*') if p.is_file()}
    assert inventory == source['instrumented_sha256']
    checked(HERE/'baseline-source.tar', source['baseline_archive_sha256'])
    with tarfile.open(HERE/'baseline-source.tar') as archive:
        original = {p.name: hashlib.sha256(archive.extractfile(p).read()).hexdigest()
                    for p in archive.getmembers() if p.isfile()}
    assert original == source['baseline_sha256']
    assert sorted(n for n in inventory if original.get(n) != inventory[n]) == source['changed_files']
    for name in ['engine', 'core_library']:
        assert protocol[name] == build[name]
        checked(build[name]['path'], build[name]['sha256'])
        assert Path(build[name]['path']).stat().st_size == build[name]['bytes']
    build_dir = Path(build['engine']['path']).parent
    for field, name in [('compile_commands_sha256', 'compile_commands.json'),
                        ('cmake_cache_sha256', 'CMakeCache.txt')]:
        checked(build_dir/name, build[field])
        checked(HERE/'build-attempt1'/name, build[field])
    commands = read(build['commands'])
    assert commands['status'] == 'PASS_BUILD_ONLY' and commands['engine_executed'] is False
    assert commands['source_sha256_before'] == commands['source_sha256_after'] == inventory
    for step in commands['steps']:
        assert step['exit_code'] == step['expected_exit_code'] == 0
        for stream in ['stdout', 'stderr']:
            checked(HERE/'build-attempt1'/(step['label']+'.'+stream), step[stream+'_sha256'])
    inputs = {}
    for name, entry in protocol['original_inputs'].items():
        path = Path(entry['path'])
        if not path.is_absolute():
            path = REPO/path
        checked(path, entry['sha256'])
        inputs[name] = path
    assert set(inputs) == {'game85-baseline-original-input.txt', 'game85-original-protocol.log.gz', 'forfeit-exchange.json'}
    warm = inputs['game85-baseline-original-input.txt'].read_text().splitlines()
    exchange = json.loads(inputs['forfeit-exchange.json'].read_text())
    session = gzip.decompress(inputs['game85-original-protocol.log.gz'].read_bytes())
    assert hashlib.sha256(session).hexdigest() == exchange['session_original_sha256']
    assert len(warm) == 260 and sum(s.startswith('go ') for s in warm) == 50
    assert len(re.findall(rb'  Baseline ---> bestmove (\S+)', session)) == 50
    assert warm[6] == 'isready'
    assert exchange['final_search']['go_command_original'] == [s for s in warm if s.startswith('go ')][-1]
    cleanup = read('cleanup-regression-attempt1/RESULTS.json')
    assert cleanup['status'] == 'cleanup_contracts_red_green_passed'
    assert cleanup['active_fixture_group_members_after_tests'] == []
    checked(HERE/'test_cleanup.py', cleanup['test_sha256'])
    checked(HERE/'pre-registry-binding/run_diagnostic.py', cleanup['corrected_runner_sha256'])
    for name, identity in read('cleanup-regression-attempt1/SHA256.json').items():
        path = HERE/'cleanup-regression-attempt1'/name
        checked(path, identity['sha256'])
        assert path.stat().st_size == identity['bytes']
    for name in ['close', 'run_case']:
        assert function(HERE/'run_diagnostic.py', name) == function(HERE/'pre-registry-binding/run_diagnostic.py', name)
    registry = read('pre-registry-binding/RESULTS.json')
    assert registry['status'] == 'data_only_frozen_registry_red_green_passed'
    assert registry['baseline_expected_failure'] == 1
    assert registry['corrected_tests'] == 2 and registry['corrected_exit_code'] == 0
    assert registry['engine_executed'] is False
    checked(HERE/'run_diagnostic.py', registry['runner_sha256'])
    checked(HERE/'test_registry_binding.py', registry['test_sha256'])
    assert 'FAILED (failures=1)' in (HERE/'pre-registry-binding/red.stderr').read_text()
    assert (HERE/'pre-registry-binding/green.stderr').read_text().endswith('\nOK\n')
    for color in ['red', 'green']:
        valid = read('pre-registry-binding/'+color+'/valid.json')
        mutated = read('pre-registry-binding/'+color+'/mutated.json')
        assert valid['capture_reached'] is True and valid['engine_executed'] is False
        assert mutated['engine_executed'] is False
        assert mutated['capture_reached'] is (color == 'red')
    for entry in protocol['offline_contract_evidence'].values():
        checked(REPO/entry['results_path'], entry['results_sha256'])
    before = read('pre-readiness-freeze-attempt1/BEFORE.json')
    intentional_changes = {'PROTOCOL.json', 'PREPARATION.md', 'RUNNER_REVIEW.md'}
    for name, identity in before['files'].items():
        if name not in intentional_changes:
            checked(HERE/name, identity['sha256'])
    for name in intentional_changes:
        assert sha(HERE/'pre-readiness-freeze-attempt1'/name) == before['files'][name]['sha256']
    for name in ['run_diagnostic.py', 'analyze_diagnostic.py', 'test_registry_binding.py', 'test_cleanup.py']:
        ast.parse((HERE/name).read_text(), filename=name)
    assert not (HERE/'diagnostic-attempt1').exists()
    assert not (HERE/'ROOT-CLEARANCE.json').exists()
    print(json.dumps({'status': 'PASS_OFFLINE_PREPARATION', 'protocol_sha256': sha(HERE/'PROTOCOL.json'),
                      'source_files_verified': len(inventory), 'baseline_archive_files_verified': len(original),
                      'source_binary_build_protocol_input_binding': 'PASS',
                      'preserved_registry_contract': 'One expected RED failure; two GREEN passes; data only.',
                      'preserved_cleanup_contract': 'Two expected RED failures; two GREEN passes; exact close/run_case AST unchanged.',
                      'historical_commands': 260, 'warm_searches': 50, 'cold_searches': 1,
                      'engine_executed_by_this_verifier': False, 'resource_clearance': 'NOT_ISSUED'}, indent=2))


if __name__ == '__main__':
    main()
