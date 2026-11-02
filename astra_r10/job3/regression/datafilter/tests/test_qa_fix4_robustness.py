"""QA fix 4: empty input and malformed self-play lines must fail loudly."""
import subprocess
import sys
from pathlib import Path
import pytest
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

def test_empty_input_fails_and_publishes_nothing(tmp_path):
    from filter_positions import run_filter
    inp = tmp_path / 'empty.jsonl'; inp.write_bytes(b'')
    out = tmp_path / 'out'
    with pytest.raises(ValueError, match='empty input'):
        run_filter(inp, out)
    assert not out.exists()
    assert inp.read_bytes() == b''

def test_empty_input_cli_exit_nonzero(tmp_path):
    inp = tmp_path / 'empty.jsonl'; inp.write_bytes(b'')
    p = subprocess.run([sys.executable, '-B', str(HERE / 'filter_positions.py'), str(inp), str(tmp_path / 'out')], capture_output=True, text=True)
    assert p.returncode != 0 and not (tmp_path / 'out').exists()

def test_converter_keep_result_malformed_selfplay_line_fails(tmp_path):
    src = tmp_path / 'sp.txt'
    import json
    outcome = {-1: '0', 0: '0.5', 1: '1'}
    lines = [f"{r['fen']} | {r['raw_score']} | {outcome[r['result_white']]}" for r in map(json.loads, (HERE / 'sample/positions.jsonl').read_text().splitlines()[:300])]
    src.write_text('\n'.join(lines + ['rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1 | 3']) + '\n')
    out = tmp_path / 'conv'
    p = subprocess.run([sys.executable, '-B', str(HERE / 'convert_forge.py'), str(out), '--selfplay', str(src), '--keep-result'], capture_output=True, text=True, cwd=str(HERE))
    assert p.returncode != 0 and 'malformed selfplay line' in p.stderr
    assert not out.exists()
    # Legacy (flag off) behaviour is unchanged: counted and skipped for byte identity with production.
    out2 = tmp_path / 'conv_legacy'
    p = subprocess.run([sys.executable, '-B', str(HERE / 'convert_forge.py'), str(out2), '--selfplay', str(src)], capture_output=True, text=True, cwd=str(HERE))
    assert p.returncode == 0 and '"sp_bad": 1' in p.stdout
