"""Entrypoint identity races use only authored manifests and stub delegation."""
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

import filter_positions as filters
import train_adapter as adapter
from records import dumps, record


@pytest.fixture
def entry_identity(tmp_path, monkeypatch):
    rows = tmp_path/'rows.jsonl'
    rows.write_text(dumps(record('4k3/8/8/8/8/8/8/4K3 w - - 0 1', 20,
                                'cp', 1, 'fixture', 1, 'selfplay'))+'\n',
                    encoding='utf-8')
    source = {'path': str(rows), 'sha256': filters.sha256(rows)}
    runtime = {'fixture': 'runtime'}
    value = {'train': source, 'validation': source, 'runtime': runtime,
             'training_ready': True}
    manifest = tmp_path/'manifest.json'
    manifest.write_text(json.dumps(value), encoding='utf-8')
    events = []
    original_context = adapter.Context

    def context(*args, **kwargs):
        events.append('context')
        return original_context(*args, **kwargs)

    def verify(path):
        events.append('verify')
        return {'status': 'PASS', 'manifest_sha256': filters.sha256(path)}

    def mutate():
        manifest.write_text(json.dumps({**value, 'unverified': True}),
                            encoding='utf-8')

    monkeypatch.setattr(adapter, 'Context', context)
    monkeypatch.setattr(adapter, 'verify', verify)
    monkeypatch.setattr(adapter, 'runtime_identity', lambda: runtime)
    monkeypatch.setattr(adapter, 'storage_guard', lambda _: None)
    monkeypatch.setattr(adapter, 'install', lambda *_: events.append('install'))
    monkeypatch.setattr(adapter, 'seed_runtime', lambda: events.append('seed'))
    monkeypatch.setitem(sys.modules, 'train',
                        SimpleNamespace(main=lambda: events.append('delegate')))

    def run(check=True):
        argv = ['train_adapter.py', '--manifest', str(manifest), '--recipe',
                'filtered_eval_v1', '--output', str(tmp_path/'never_created'),
                '--device', 'cpu']
        if check:
            argv.append('--check')
        monkeypatch.setattr(sys, 'argv', argv)
        adapter.main()

    return SimpleNamespace(manifest=manifest, events=events, verify=verify,
                           mutate=mutate, run=run, runtime=runtime)


@pytest.mark.parametrize('check', [True, False])
def test_manifest_replacement_after_verification_never_constructs_context(
        entry_identity, monkeypatch, capsys, check):
    case = entry_identity

    def replaced(path):
        result = case.verify(path)
        case.mutate()
        return result

    monkeypatch.setattr(adapter, 'verify', replaced)
    with pytest.raises(ValueError, match='manifest'):
        case.run(check)
    assert 'context' not in case.events and 'delegate' not in case.events
    assert not capsys.readouterr().out


@pytest.mark.parametrize('check', [True, False])
def test_manifest_replacement_during_runtime_check_never_reports_or_delegates(
        entry_identity, monkeypatch, capsys, check):
    case = entry_identity

    def replaced():
        case.mutate()
        return case.runtime

    monkeypatch.setattr(adapter, 'runtime_identity', replaced)
    with pytest.raises(ValueError, match='manifest'):
        case.run(check)
    assert 'delegate' not in case.events
    assert not capsys.readouterr().out


@pytest.mark.parametrize('stage', ['install', 'seed_runtime'])
def test_manifest_replacement_in_last_initialization_step_never_delegates(
        entry_identity, monkeypatch, capsys, stage):
    case = entry_identity
    monkeypatch.setattr(adapter, stage, lambda *_: case.mutate())
    with pytest.raises(ValueError, match='manifest'):
        case.run(False)
    assert 'delegate' not in case.events
    assert not capsys.readouterr().out


def test_verifier_digest_must_match_the_original_manifest_before_context(
        entry_identity, monkeypatch, capsys):
    case = entry_identity
    monkeypatch.setattr(adapter, 'verify', lambda _: {
        'status': 'PASS', 'manifest_sha256': '0'*64})
    with pytest.raises(ValueError, match='manifest'):
        case.run()
    assert 'context' not in case.events and 'delegate' not in case.events
    assert not capsys.readouterr().out


@pytest.mark.parametrize('check', [True, False])
def test_unchanged_verified_manifest_allows_cpu_check_or_stub_delegation(
        entry_identity, capsys, check):
    case = entry_identity
    case.run(check)
    output = capsys.readouterr().out
    if check:
        assert json.loads(output)['status'] == 'PASS'
        assert 'delegate' not in case.events
    else:
        assert case.events[-3:] == ['install', 'seed', 'delegate']
        assert not output
    assert not (case.manifest.parent/'never_created').exists()


@pytest.mark.parametrize('check', [True, False])
def test_command_uses_verified_target_after_transient_alias_resolution(
        entry_identity, monkeypatch, capsys, check):
    case = entry_identity
    alternate = case.manifest.parent/'unverified.partial'/'manifest.json'
    original_resolve = Path.resolve
    original_command = adapter.command
    state = {'redirect': False}

    def runtime():
        state['redirect'] = True
        return case.runtime

    def transient_resolve(path, *args, **kwargs):
        if state['redirect'] and path == case.manifest:
            return alternate
        return original_resolve(path, *args, **kwargs)

    def build_command(*args, **kwargs):
        state['redirect'] = False
        return original_command(*args, **kwargs)

    monkeypatch.setattr(adapter, 'runtime_identity', runtime)
    monkeypatch.setattr(Path, 'resolve', transient_resolve)
    monkeypatch.setattr(adapter, 'command', build_command)
    case.run(check)
    output = capsys.readouterr().out
    argv = json.loads(output)['command'] if check else sys.argv
    assert argv[1] == str(case.manifest)
    assert argv[argv.index('--validation-datasets')+1] == str(case.manifest)
    assert not (case.manifest.parent/'never_created').exists()
