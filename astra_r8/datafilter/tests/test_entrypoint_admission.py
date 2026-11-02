"""Admission checks and CPU initialization only; never run training updates."""
import json
import os
from pathlib import Path
import random
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture
def entry(tmp_path, monkeypatch):
    import train_adapter as adapter
    events = []
    manifest = tmp_path/'manifest.json'
    manifest.write_text('{}', encoding='utf-8')
    output = tmp_path/'new_training_output'
    runtime = {'fixture': 'pinned'}

    class Context:
        def __init__(self, path, recipe):
            events.append('context')
            self.manifest = {'training_ready': True, 'runtime': runtime}
        def state_dict(self):
            return {'fixture': 'context'}

    def verify(path):
        events.append('verify')
        return {'status': 'PASS'}

    monkeypatch.setattr(adapter, 'Context', Context)
    monkeypatch.setattr(adapter, 'verify', verify, raising=False)
    monkeypatch.setattr(adapter, 'storage_guard', lambda p: events.append('guard'), raising=False)
    monkeypatch.setattr(adapter, 'runtime_identity', lambda: runtime)
    monkeypatch.setattr(adapter, 'install', lambda *a: events.append('install'))
    monkeypatch.setattr(adapter, 'seed_runtime', lambda: events.append('seed'), raising=False)
    monkeypatch.setitem(sys.modules, 'train', SimpleNamespace(main=lambda: events.append('delegate')))

    def run(*, check=True, device='cpu', resume=None, manifest_path=None, output_path=None):
        args = ['train_adapter.py', '--manifest', str(manifest_path or manifest),
                '--recipe', 'filtered_wdl_v1', '--output', str(output_path or output),
                '--device', device]
        if check:
            args.append('--check')
        if resume is not None:
            args += ['--resume', str(resume)]
        monkeypatch.setattr(sys, 'argv', args)
        adapter.main()
    return SimpleNamespace(adapter=adapter, events=events, run=run,
                           manifest=manifest, output=output)


def test_check_verifies_handoff_before_context_and_pass(entry, capsys):
    entry.run()
    assert entry.events[:3] == ['guard', 'verify', 'context']
    assert json.loads(capsys.readouterr().out)['status'] == 'PASS'
    assert 'delegate' not in entry.events


def test_failed_handoff_never_constructs_context_or_reports_pass(entry, monkeypatch, capsys):
    def reject(path):
        raise ValueError('clearance missing')
    monkeypatch.setattr(entry.adapter, 'verify', reject)
    with pytest.raises(ValueError, match='clearance missing'):
        entry.run()
    assert 'context' not in entry.events and 'delegate' not in entry.events
    assert not capsys.readouterr().out


@pytest.mark.parametrize('check', [False, True])
def test_existing_output_rejected_before_preflight_or_training(entry, check):
    entry.output.mkdir()
    with pytest.raises(FileExistsError, match='existing training output'):
        entry.run(check=check)
    assert 'context' not in entry.events and 'delegate' not in entry.events


def test_dangling_output_entry_rejected(entry, monkeypatch):
    original = os.path.lexists
    monkeypatch.setattr(os.path, 'lexists', lambda p: p == entry.output or original(p))
    with pytest.raises(FileExistsError, match='existing training output'):
        entry.run()
    assert 'context' not in entry.events


@pytest.mark.parametrize('check', [False, True])
def test_missing_resume_rejected_before_preflight_or_training(entry, check):
    with pytest.raises(ValueError, match='missing checkpoint'):
        entry.run(check=check, resume=entry.manifest.parent/'missing.ckpt')
    assert 'context' not in entry.events and 'delegate' not in entry.events


def test_actual_output_policy_rejects_F_destination(entry, monkeypatch):
    from resource_policy import storage_guard
    monkeypatch.setattr(entry.adapter, 'storage_guard', storage_guard)
    with pytest.raises(ValueError, match='output must stay under'):
        entry.run(output_path=Path('F:/astra8_data/forbidden_training_output'))
    assert 'context' not in entry.events


def test_resource_failure_blocks_preflight(entry, monkeypatch):
    def reject(path):
        raise OSError('C:/ below 50 GB reserve plus planned allocation')
    monkeypatch.setattr(entry.adapter, 'storage_guard', reject)
    with pytest.raises(OSError, match='50 GB reserve'):
        entry.run()
    assert 'context' not in entry.events


@pytest.mark.parametrize(('check', 'device'), [(False, 'cpu'), (False, 'cuda:0'), (True, 'cuda:0')])
def test_partial_manifest_cannot_enter_training(entry, check, device):
    partial = entry.manifest.parent/'candidate.partial'/'nested'/'manifest.json'
    with pytest.raises(ValueError, match='partial'):
        entry.run(check=check, device=device, manifest_path=partial)
    assert 'context' not in entry.events and 'delegate' not in entry.events


def test_cpu_check_accepts_staged_manifest_after_verification(entry):
    entry.run(manifest_path=entry.manifest.parent/'candidate.partial'/'manifest.json')
    assert entry.events[:3] == ['guard', 'verify', 'context']
    assert 'delegate' not in entry.events


def test_seeding_precedes_delegation(entry):
    entry.run(check=False)
    assert entry.events == ['guard', 'verify', 'context', 'install', 'seed', 'delegate']


def test_same_seed_repeats_actual_small_cpu_model_initialization():
    import numpy as np
    import torch
    import train_adapter as adapter
    from model.config import NNUEConfig
    from npt_adapter import MaskedNNUE
    assert callable(getattr(adapter, 'seed_runtime', None)), 'entrypoint needs a pre-construction seed'
    cfg = NNUEConfig()
    cfg.features = 'K32H3^'
    cfg.model_config.L1 = 8
    adapter.seed_runtime()
    first = MaskedNNUE(cfg, max_epoch=8, num_batches_per_epoch=9307)
    first_random = (random.random(), np.random.rand())
    torch.rand(11)
    random.random()
    np.random.rand()
    adapter.seed_runtime()
    second = MaskedNNUE(cfg, max_epoch=8, num_batches_per_epoch=9307)
    assert all(torch.equal(a, b) for a, b in zip(first.parameters(), second.parameters()))
    assert first_random == (random.random(), np.random.rand())
