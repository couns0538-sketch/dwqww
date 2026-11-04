import hashlib
import json
import subprocess
import sys
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / 'tools' / 'opus_boardstm_probe.py'
A = '4k3/8/8/8/8/8/8/4K3 w - - 0 1'
B = '4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 2'
C = '4k3/8/8/8/8/8/8/3K4 w - - 0 1'
D = '4k3/8/8/8/8/8/8/5K2 b - - 0 1'


def write(path, fens):
    data = ''.join(f'{fen} | 0 | 0.5\n' for fen in fens).encode()
    path.write_bytes(data)
    return dict(path=str(path), expected_md5=hashlib.md5(data).hexdigest(),
                actual_md5=hashlib.md5(data).hexdigest(), match=True)


def run(tmp_path, pins_override=None):
    h = tmp_path / 'h.txt'
    t1, t2 = tmp_path / 't1.txt', tmp_path / 't2.txt'
    pins = [write(h, [A, B, C]), write(t1, [A.replace('0 1', '5 9'), D]), write(t2, [B.replace('d6', '-'), A])]
    if pins_override:
        pins_override(pins)
    pin_file = tmp_path / 'pins.jsonl'
    pin_file.write_text(''.join(json.dumps(p) + '\n' for p in pins))
    out = tmp_path / 'probe'
    proc = subprocess.run([sys.executable, '-I', '-B', str(TOOL), '--out', str(out), '--holdout', str(h),
                           '--train', str(t1), '--train', str(t2), '--pins', str(pin_file), '--seconds', '60'],
                          capture_output=True, text=True)
    return proc, out, h, t1, t2


def test_probe_lists_every_shared_row_and_counts_ep(tmp_path):
    proc, out, h, t1, t2 = run(tmp_path)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    record = json.loads((out / 'PROBE.json').read_text())
    assert record['status'] == 'COMPLETE' and record['problems'] == []
    assert (record['shared_exact_keys'], record['train_overlap_rows'], record['holdout_overlap_rows']) == (2, 3, 2)
    assert record['train_rows'] == 4 and record['holdout_rows'] == 3 and record['hash_collision_train_rows'] == 0
    assert record['ep_census']['h.txt'] == dict(ep_rows=1, legal=1, no_capture=0, invalid=0, none=0)
    shared = [json.loads(line) for line in (out / 'SHARED.jsonl').read_text().splitlines()]
    by_key = {item['key']: item for item in shared}
    a_key, b_key = '4k3/8/8/8/8/8/8/4K3 w', '4k3/8/8/3pP3/8/8/8/4K3 w'
    assert by_key[a_key]['train'] == [dict(path=str(t1), line=1, fen=A.replace('0 1', '5 9')),
                                      dict(path=str(t2), line=2, fen=A)]
    assert by_key[a_key]['holdout'] == [dict(path=str(h), line=1, fen=A)]
    assert by_key[b_key]['train'] == [dict(path=str(t2), line=1, fen=B.replace('d6', '-'))]
    assert by_key[b_key]['holdout'] == [dict(path=str(h), line=2, fen=B)]


def test_probe_pin_mismatch_is_incomplete(tmp_path):
    def corrupt(pins):
        pins[1]['expected_md5'] = pins[1]['actual_md5'] = '0' * 32
    proc, out, *_ = run(tmp_path, corrupt)
    assert proc.returncode == 2
    record = json.loads((out / 'PROBE.json').read_text())
    assert record['status'] == 'INCOMPLETE' and any('md5' in p for p in record['problems'])
