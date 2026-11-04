import hashlib
import json
import subprocess
import sys
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / 'tools' / 'opus_boardstm_triage.py'
EXPAND = str.maketrans({str(n): '.' * n for n in range(1, 9)})
PAIRS = [
    # (train FEN, holdout FEN, expected key class)
    ('8/8/8/8/6KP/8/2k5/1q6 b - h3 0 48', '8/8/8/8/6KP/8/2k5/1q6 b - - 2 60', 'ep_format_diff'),
    ('4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 2', '4k3/8/8/3pP3/8/8/8/4K3 w - - 1 5', 'real_ep_diff'),
    ('r3k3/8/8/8/8/8/8/4K3 b q - 0 9', 'r3k3/8/8/8/8/8/8/4K3 b - - 3 20', 'other'),
]


def key(fen):
    f = fen.split()
    return ''.join(r.translate(EXPAND) for r in f[0].split('/')) + ' ' + f[1]


def listing(pairs):
    return [dict(key=key(t), train=[dict(path='D:\\x\\t.txt', line=i + 1, fen=t)],
                 holdout=[dict(path='D:\\x\\forge_selfplay_013.txt', line=10 + i, fen=h)])
            for i, (t, h, _) in enumerate(pairs)]


def write_report(path, pairs):
    items = listing(pairs)
    path.write_text(json.dumps(dict(status='FAIL', complete=True, keys=dict(board_stm=dict(
        listing_complete=True, shared_keys=items, shared_exact_keys=len(items), train_overlap_rows=len(items),
        holdout_overlap_rows=len(items), hash_collision_rows=0,
        train=dict(key_fill_rate=1.0), holdout=dict(key_fill_rate=1.0))))))


def write_probe(dir_, pairs):
    shared = dir_ / 'SHARED.jsonl'
    rows = []
    for item in listing(pairs):
        fen = item['train'][0]['fen'].split()
        rows.append(json.dumps(dict(key=fen[0] + ' ' + fen[1], train=item['train'], holdout=item['holdout'])))
    shared.write_text('\n'.join(rows) + '\n')
    probe = dir_ / 'PROBE.json'
    probe.write_text(json.dumps(dict(status='COMPLETE', shared_listing=dict(
        path=str(shared), md5=hashlib.md5(shared.read_bytes()).hexdigest()))))
    return probe


def run(tmp_path, *args):
    out = tmp_path / 'TRIAGE.json'
    proc = subprocess.run([sys.executable, '-I', '-B', str(TOOL), *args, '--out', str(out),
                           '--rows', str(tmp_path / 'rows.tsv')], capture_output=True, text=True)
    return proc, (json.loads(out.read_text()) if out.exists() else None)


def test_classes_recount_and_cross_check(tmp_path):
    write_report(tmp_path / 'R.json', PAIRS)
    probe = write_probe(tmp_path, PAIRS)
    proc, rec = run(tmp_path, '--report', str(tmp_path / 'R.json'), '--probe', str(probe), '--expect', '3,3,3')
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert rec['status'] == 'COMPLETE' and rec['reasons'] == []
    assert rec['keys_per_class'] == {'ep_format_diff': 1, 'real_ep_diff': 1, 'other': 1}
    assert rec['other_pair_reasons'] == {'castling_diff': 1}
    assert rec['normalised_4field_recount']['shared_keys'] == 1
    assert rec['normalised_4field_recount']['train_rows'] == 1 and rec['normalised_4field_recount']['holdout_rows'] == 1
    assert rec['per_holdout_file'] == {'forge_selfplay_013.txt': {'ep_format_diff': 1, 'real_ep_diff': 1, 'other': 1}}
    assert len((tmp_path / 'rows.tsv').read_text().splitlines()) == 1 + 6


def test_identical_four_field_pair_fails_closed(tmp_path):
    same = [('4k3/8/8/8/8/8/8/4K3 w - - 0 1', '4k3/8/8/8/8/8/8/4K3 w - - 9 30', 'other')]
    write_report(tmp_path / 'R.json', same)
    proc, rec = run(tmp_path, '--report', str(tmp_path / 'R.json'), '--expect', '1,1,1')
    assert proc.returncode == 2 and rec['status'] == 'UNVERIFIED'
    assert rec['other_pair_reasons'] == {'identical_4field': 1}


def test_disagreeing_listings_fail_closed(tmp_path):
    write_report(tmp_path / 'R.json', PAIRS)
    probe = write_probe(tmp_path, PAIRS[:2])
    proc, rec = run(tmp_path, '--report', str(tmp_path / 'R.json'), '--probe', str(probe), '--expect', '3,3,3')
    assert proc.returncode == 2 and any('listings differ' in r for r in rec['reasons'])


def test_wrong_totals_fail_closed(tmp_path):
    write_report(tmp_path / 'R.json', PAIRS)
    proc, rec = run(tmp_path, '--report', str(tmp_path / 'R.json'), '--expect', '7610,7700,7612')
    assert proc.returncode == 2 and any('totals' in r for r in rec['reasons'])
