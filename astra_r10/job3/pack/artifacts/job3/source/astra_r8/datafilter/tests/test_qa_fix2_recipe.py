"""QA fix 2: seed, epochs and passes are explicit parameters; sane default pass count."""
import sys
from pathlib import Path
import pytest
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

def test_no_hard_coded_seed_or_epoch():
    src = (HERE / 'train_adapter.py').read_text(encoding='utf-8')
    for literal in ('5108', '152500000', '9307'):
        assert literal not in src

def test_epoch_plan_defaults_and_guard():
    from train_adapter import epoch_plan, DEFAULT_EPOCHS, DEFAULT_PASSES_PER_EPOCH
    plan = epoch_plan(999953, DEFAULT_PASSES_PER_EPOCH, DEFAULT_EPOCHS)
    assert plan['steps_per_epoch'] == 61 and plan['epoch_size'] == 61 * 16384 and plan['epochs'] == 3
    assert 2.9 < plan['total_passes'] <= 3.0
    with pytest.raises(ValueError, match='total passes'):
        epoch_plan(999953, 152.5, 8)          # the old ~1,220-pass recipe
    assert epoch_plan(999953, 152.5, 8, allow_many_passes=True)['total_passes'] > 1219

def test_context_requires_seed_and_uses_it(tmp_path):
    from records import dumps
    from filter_positions import sha256
    from test_adapter import rows
    import json
    from train_adapter import Context
    p = tmp_path / 'rows.jsonl'; p.write_text('\n'.join(map(dumps, rows())) + '\n')
    m = tmp_path / 'manifest.json'; m.write_text(json.dumps({'train': {'path': str(p), 'sha256': sha256(p)}, 'validation': {'path': str(p), 'sha256': sha256(p)}}))
    with pytest.raises(TypeError):
        Context(m, 'filtered_wdl_v1')
    with pytest.raises(ValueError, match='seed'):
        Context(m, 'filtered_wdl_v1', None, allow_many_passes=True)
    ctx = Context(m, 'filtered_wdl_v1', 61101, allow_many_passes=True)
    assert ctx.sampler.seed == 61101 and ctx.state_dict()['plan'] == ctx.plan

def test_cli_seed_required():
    import subprocess
    p = subprocess.run([sys.executable, '-B', str(HERE / 'train_adapter.py'), '--manifest', 'm.json', '--recipe', 'filtered_eval_v1', '--output', 'o', '--check'], capture_output=True, text=True)
    assert p.returncode != 0 and '--seed' in p.stderr
