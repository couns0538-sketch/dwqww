"""QA fix 3: no agent-scratch (F:/opus_scratch) dependency; trainer location is a parameter."""
import os
import subprocess
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]

def test_no_scratch_paths_in_runtime_code():
    for name in ('npt_adapter.py', 'train_adapter.py', 'rebind_manifest.py'):
        assert 'opus_scratch' not in (HERE / name).read_text(encoding='utf-8')

def test_missing_npt_root_fails_clearly(tmp_path):
    env = dict(os.environ, ASTRA_NPT_ROOT=str(tmp_path / 'nope'))
    p = subprocess.run([sys.executable, '-B', '-c', 'import npt_adapter'], cwd=str(HERE), env=env, capture_output=True, text=True)
    assert p.returncode != 0 and 'installed npt not found' in p.stderr

def test_cli_npt_root_overrides_env(tmp_path):
    env = dict(os.environ)  # valid ASTRA_NPT_ROOT from the test environment
    p = subprocess.run([sys.executable, '-B', str(HERE / 'train_adapter.py'), '--npt-root', str(tmp_path / 'nope'),
                        '--manifest', 'm.json', '--recipe', 'filtered_eval_v1', '--output', 'o', '--seed', '1', '--check'],
                       cwd=str(HERE), env=env, capture_output=True, text=True)
    assert p.returncode != 0 and 'installed npt not found' in p.stderr and 'nope' in p.stderr
