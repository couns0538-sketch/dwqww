"""Reproducible CPU-only audit stages; outputs must be new. UNPROVEN."""
import argparse
import hashlib
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import chess
import numpy as np
from records import selfplay_record, read_records, dumps
from result_codec import encode_result, decode_result
from filter_positions import low_priority, storage_guard, sha256

HERE = Path(__file__).resolve().parent

def freeze(root, sources):
    out = root / 'cohort'
    storage_guard(out, allowance=2*10**9)
    out.mkdir()
    receipts = []
    count = 0
    with open(out / 'million.jsonl', 'x', encoding='utf-8', newline='\n') as normalized, open(out / 'legacy100k.txt', 'x', encoding='utf-8', newline='\n') as legacy:
        for path in sources:
            storage_guard(root)
            before = path.stat()
            digest = sha256(path)
            consumed = 0
            first_row = last_row = None
            with open(path, encoding='utf-8-sig') as fh:
                for line_no, line in enumerate(fh, 1):
                    if not line.strip() or line.lstrip().startswith('#'):
                        continue
                    if count == 1_000_000:
                        break
                    row = selfplay_record(line, str(path), line_no)
                    normalized.write(dumps(row) + '\n')
                    if count < 100_000:
                        legacy.write(line.rstrip('\r\n') + '\n')
                    count += 1
                    if count % 8192 == 0:
                        storage_guard(allowance=64*1024*1024)
                    consumed += 1
                    first_row = first_row or line_no
                    last_row = line_no
            after = path.stat()
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns) or sha256(path) != digest:
                raise ValueError('source changed during freeze')
            receipts.append(dict(path=str(path), sha256=digest, bytes=before.st_size,
                                 consumed=consumed, first_source_row=first_row, last_source_row=last_row))
            if count == 1_000_000:
                break
    if count != 1_000_000:
        raise ValueError('insufficient cohort rows')
    manifest = dict(count=count, sources=receipts, source_order=[str(p) for p in sources],
                    boundary_policy='first million non-comment data rows; no replacement on malformed input',
                    hashes={p.name: sha256(p) for p in out.iterdir()})
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return manifest

def legacy(root):
    logs = root / 'legacy_logs'
    storage_guard(root, allowance=100*10**6)
    logs.mkdir()
    for name, script, extra in [('old', HERE/'baseline/convert_forge.py', []), ('new', HERE/'convert_forge.py', []), ('result', HERE/'convert_forge.py', ['--keep-result'])]:
        cmd = [sys.executable, str(script), str(root/name), '--selfplay', str(root/'cohort/legacy100k.txt'), *extra]
        with open(logs/(name+'.log'), 'xb') as log:
            completed = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, env=os.environ.copy())
        if completed.returncode:
            raise RuntimeError(f'{name} converter failed; see log')
    report = {}
    from filter_lichess_rec import REC
    for split in ('train', 'val'):
        old, new = sha256(root/'old'/f'{split}.bin'), sha256(root/'new'/f'{split}.bin')
        assert old == new
        arr = np.fromfile(root/'result'/f'{split}.bin', dtype=REC)
        rows = list(read_records(root/'result'/f'{split}.metadata.jsonl'))
        assert len(arr) == len(rows)
        from filter_lichess_rec import encode_board
        for item, row in zip(arr, rows):
            b = chess.Board(row['fen'])
            score = max(-3000, min(3000, row['score_stm'] * (1 if b.turn else -1)))
            expected = encode_board(b, score)[0]
            expected['rsv'] = encode_result(row['has_result'], row['result_stm'])
            assert decode_result(item['rsv'], item['stm']) == row['result_stm']
            assert item.tobytes() == expected.tobytes()
        stripped = arr.copy(); stripped['rsv'] = 0
        assert stripped.tobytes() == (root/'old'/f'{split}.bin').read_bytes()
        report[split] = dict(old_sha256=old, new_sha256=new, rows=len(arr), metadata_alignment='PASS')
    (logs/'identity.json').write_text(json.dumps(report, indent=2))
    return report

def orientation(root):
    destination = root/'orientation1000.json'
    storage_guard(destination)
    if destination.exists():
        raise FileExistsError(destination)
    # Literal table supplied by independent milestone reviewer.
    oracle = {('w','0'):(-1,True,0), ('w','0.5'):(0,True,1), ('w','1'):(1,True,2), ('w','?'):(None,False,0),
              ('b','0'):(1,True,2), ('b','0.5'):(0,True,1), ('b','1'):(-1,True,0), ('b','?'):(None,False,0)}
    by_turn = {'w': [], 'b': []}
    for row in read_records(root/'cohort/million.jsonl'):
        turn = row['fen'].split()[1]
        if len(by_turn[turn]) < 125:
            by_turn[turn].append(row['fen'])
        if all(len(v) == 125 for v in by_turn.values()):
            break
    cases = []
    for (turn, token), expected in oracle.items():
        for fen in by_turn[turn]:
            r = selfplay_record(f'{fen} | 123 | {token}', 'orientation-fixture', len(cases)+1)
            assert (r['result_stm'], r['has_result'], encode_result(r['has_result'], r['result_stm'])[1]) == expected
            opposite = {'0':'1', '1':'0', '0.5':'0.5', '?':'?'}[token]
            mirrored = selfplay_record(f'{chess.Board(fen).mirror().fen(en_passant="fen")} | 123 | {opposite}', 'mirror', 1)
            assert (r['score_stm'],r['result_stm'],r['has_result']) == (mirrored['score_stm'],mirrored['result_stm'],mirrored['has_result'])
            cases.append(dict(fen=fen, raw_white_result=token, expected_stm=expected[0], mask=expected[1], byte30=expected[2]))
    assert len(cases) == 1000
    with open(destination, 'x', encoding='utf-8') as fh:
        json.dump(cases, fh, indent=1)
    return dict(cases=1000, mirrors=1000, status='PASS', oracle='independent reviewer literal 8-cell table')

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('stage', choices=['freeze','legacy','orientation'])
    p.add_argument('root', type=Path)
    p.add_argument('--sources', nargs='*', type=Path)
    a = p.parse_args()
    low_priority(); storage_guard(a.root)
    result = freeze(a.root, a.sources) if a.stage == 'freeze' else globals()[a.stage](a.root)
    print(json.dumps(result, indent=2))
