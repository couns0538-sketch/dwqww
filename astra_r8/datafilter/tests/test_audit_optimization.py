"""Audit failures must remain failures under Python -O and -OO."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


CHILD = r'''
import json
from pathlib import Path
import sys
sys.path.insert(0, sys.argv[1])
import chess
from filter_positions import low_priority, sha256
from records import record, dumps
low_priority()
mode, root, corrupt = sys.argv[2], Path(sys.argv[3]), sys.argv[4] == 'corrupt'
root.mkdir()
if mode == 'orientation':
    import audit
    audit.read_records = lambda *args: iter([
        {'fen': chess.STARTING_FEN.replace(' w ', f' {turn} ')}
        for turn in ('w', 'b') for _ in range(125)
    ])
    if corrupt:
        audit.encode_result = lambda *args: (1, 0, 1)
    audit.orientation(root)
elif mode == 'binary_roundtrip':
    import audit_stm_roundtrip as roundtrip
    original = roundtrip.np.fromfile
    def read_binary(*args, **kwargs):
        values = original(*args, **kwargs)
        if corrupt and len(values):
            # Corrupt only the in-memory value returned to the audit reader.
            values[0]['rsv'][2] = 255
        return values
    roundtrip.np.fromfile = read_binary
    roundtrip.run(root/'roundtrip')
elif mode == 'raw_labels':
    import audit_raw_labels
    cohort = root/'cohort'
    cohort.mkdir()
    raw = root/'source.txt'
    raw.write_text((chess.STARTING_FEN+' | 20 | 1\n')*1000)
    (cohort/'manifest.json').write_text(json.dumps({'sources': [{'path':str(raw)}]}))
    with (cohort/'million.jsonl').open('x') as stream:
        for number in range(1,1001):
            score = 21 if corrupt and number == 1 else 20
            stream.write(dumps(record(chess.STARTING_FEN, score, 'cp', 1,
                                      str(raw), number, 'selfplay'))+'\n')
    audit_raw_labels.run(root)
elif mode == 'holdout':
    import clear_holdouts as clearing
    (root/'independent_audit').mkdir()
    (root/'filtered_default').mkdir()
    source = root/'filtered_default/records.jsonl'
    row = record(chess.STARTING_FEN, 20, 'cp', 1, 'fixture', 1, 'selfplay')
    payload = dumps(row)+'\n'
    source.write_text(payload)
    (source.parent/'report.json').write_text(json.dumps({'hashes':{'records.jsonl':sha256(source)}}))
    holdouts, pins = [], {}
    for shard in ('013', '014'):
        path = root/(shard+'.txt')
        path.write_text(chess.STARTING_FEN+' | 20 | 1\n')
        digest = sha256(path)
        pins[shard] = (digest, 1)
        holdouts.append(dict(shard=shard, path=str(path), sha256=digest,
                             rows=1, complete_scan=True))
    (root/'independent_audit/audit.json').write_text(json.dumps({'holdouts':holdouts}))
    clearing.EXPECTED_HOLDOUTS = pins
    original = clearing.write_selection
    def write_selection(*args, **kwargs):
        report = original(*args, **kwargs)
        if corrupt:
            # Reintroduce the held-out row only into this newly owned fixture.
            (root/'holdout_cleared.partial/records.jsonl').write_text(payload)
        return report
    clearing.write_selection = write_selection
    clearing.run(root)
else:
    raise ValueError('unknown fixture')
print('AUDIT_APPROVED')
'''


def run_case(tmp_path, mode, optimization, corrupt):
    script = tmp_path/'fixture_child.py'
    script.write_text(CHILD, encoding='utf-8')
    command = [sys.executable, *([optimization] if optimization else []), str(script),
               str(Path(__file__).resolve().parents[1]), mode, str(tmp_path/'case'),
               'corrupt' if corrupt else 'valid']
    result = subprocess.run(command, text=True, capture_output=True, timeout=30,
                            check=False, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'),
                            creationflags=subprocess.IDLE_PRIORITY_CLASS if os.name == 'nt' else 0)
    (tmp_path/'command.json').write_text(json.dumps(command, indent=2))
    (tmp_path/'stdout.log').write_text(result.stdout)
    (tmp_path/'stderr.log').write_text(result.stderr)
    return result


@pytest.mark.parametrize('mode,artifact', [
    ('orientation', 'orientation1000.json'),
    ('binary_roundtrip', 'roundtrip/report.json'),
    ('raw_labels', 'actual_source_orientation1000.json'),
    ('holdout', 'holdout_cleared/clearance.json'),
])
@pytest.mark.parametrize('optimization', [None, '-O', '-OO'])
def test_corrupt_proof_never_approved(tmp_path, mode, artifact, optimization):
    result = run_case(tmp_path, mode, optimization, corrupt=True)
    assert result.returncode != 0, result.stdout
    assert 'AUDIT_APPROVED' not in result.stdout
    assert not (tmp_path/'case'/artifact).exists()


@pytest.mark.parametrize('mode', ['orientation', 'binary_roundtrip', 'raw_labels', 'holdout'])
def test_valid_proof_still_works_with_optimization(tmp_path, mode):
    result = run_case(tmp_path, mode, '-OO', corrupt=False)
    assert result.returncode == 0, result.stderr
    assert 'AUDIT_APPROVED' in result.stdout
