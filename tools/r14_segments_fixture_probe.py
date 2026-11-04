"""Owned synthetic integration probe for the unchanged segment-driver entry point."""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import time

import chess

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r14_segments as s


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--cpu', type=int, default=3)
    args = parser.parse_args()
    admission = s.Guard(180, args.cpu)
    base = s.safe_path(args.out, write=True)
    s.resource_guard(reserve_bytes=8 * 1024**2)
    base.mkdir(parents=True, exist_ok=False)
    for name in ('TEMP', 'TMP'):
        os.environ[name] = str(base)
    for name in ('CUDA_VISIBLE_DEVICES', 'HIP_VISIBLE_DEVICES'):
        os.environ[name] = '-1'
    candidate = s.hashes(Path(s.__file__))
    qualification = s.ROOT / 'sep/qualification-million01/REPORT.json'
    if s.hashes(qualification)['md5'] != 'b91461a33503289c3025b5723d202d72':
        raise ValueError('qualification fixture dependency changed')
    rng = random.Random(141103)
    board = chess.Board()
    raw_rows = []
    for index in range(2200):
        if board.is_game_over() or board.ply() >= 120:
            board = chess.Board()
        raw_rows.append((board.fen(en_passant='fen') + ' | 0 | 0.5\n').encode())
        board.push(rng.choice(list(board.legal_moves)))
    specs = []
    for source_id, (first, last) in enumerate(((0, 1000), (1000, 2200))):
        path = base / f'synthetic_{source_id:03}.txt'
        payload = b''.join(raw_rows[first:last])
        path.write_bytes(payload)
        specs.append(s.SourceSpec(source_id, source_id + 1, path, hashlib.md5(payload).hexdigest(),
                                  'all' if source_id == 0 else 'prefix',
                                  None if source_id == 0 else 1000, None if source_id == 0 else 900))
    original = s.spec_set
    s.spec_set = lambda mode, pins: specs
    began = time.monotonic()
    try:
        exit_code = s.main(['--mode', 'jobA', '--cpu', str(args.cpu), '--seconds', '120',
                            '--qualification', str(qualification), '--qualification-md5',
                            'b91461a33503289c3025b5723d202d72', '--out', str(base / 'driver')])
    finally:
        s.spec_set = original
    elapsed = time.monotonic() - began
    if exit_code != 0:
        raise RuntimeError(f'fixture driver incomplete: {exit_code}')
    report_path = base / 'driver/REPORT.json'
    report = json.loads(report_path.read_text())
    assert report['complete'] and report['status'] == 'UNVERIFIED'
    assert sum(item['scanned_rows'] for item in report['source_counts'].values()) == 2000
    assert [item['rows'] for item in report['input_receipts']] == [1000, 1200]
    assert report['input_receipts'][1]['context_rows'] == 100
    assert report['input_receipts'][1]['open_right'] is True
    assert all(item['complete'] and item['chain_key_fill_rate'] == 1 for item in report['input_receipts'])
    assert report['cross_file_adjacent_pairs'][0]['code'] == 0
    assert report['cross_file_adjacent_pairs'][0]['continued_segment_id'] is not None
    assert sum(item['records'] for item in report['artifacts'] if item['kind'] == 'pairs') == 2000
    assert all(s.hashes(item['path'])['md5'] == item['md5'] for item in report['artifacts'])

    board = chess.Board()
    line = ['e2e4', 'e7e5', 'g1f3', 'b8c6', 'f1c4', 'g8f6', 'd2d3', 'f8c5', 'b1c3']
    states = [board.fen(en_passant='fen')]
    for move in line:
        board.push_uci(move)
        states.append(board.fen(en_passant='fen'))
    native = s.Native(s.DEFAULT_CANDIDATE, '--pairs', base / 'extra-native.stderr.log', admission.deadline)
    results = []
    try:
        for depth in (1, 2, 8):
            query = '\t'.join((f'depth-{depth}', states[0], '0.5', states[depth], '0.5', '8', '1000000'))
            reply = native.query(query)
            assert reply['status'] == 'REACHABLE', reply
            witness = chess.Board(states[0])
            for move in reply['witness']:
                assert chess.Move.from_uci(move) in witness.legal_moves
                witness.push_uci(move)
            assert witness.fen(en_passant='fen') == states[depth]
            results.append(dict(depth=depth, **reply))

        def record(line_number, depth, result='0.5'):
            from r14_scan import parse_row
            row = parse_row((states[depth] + ' | 0 | ' + result).encode())
            return s.SourceRecord(13, line_number, row, line_number > 1)

        fixture_verdicts = {}
        for name, records, split_at in (
            ('straddle', [record(1,0), record(2,1), record(3,2)], 2),
            ('shuffle', [record(1,0), record(2,2), record(3,1)], None),
            ('result_mismatch', [record(1,0), record(2,1,'1')], None),
            ('gap_above_k', [record(1,0), record(2,9)], None)):
            truth = {(r.source_id, r.line): 'synthetic-authentic-game' for r in records}
            splits = {key: 'val' if split_at and key[1] >= split_at else 'train' for key in truth}
            events = list(s.scan_pairs(records, native.query_many))
            verdict = s.fixture_audit(records, events, truth, splits)
            expected = 'UNVERIFIED' if name == 'gap_above_k' else 'FAIL'
            assert verdict['status'] == expected, verdict
            fixture_verdicts[name] = dict(verdict, pair_codes=[event.code for event in events])
    finally:
        native.close()
    assert s.hashes(Path(s.__file__)) == candidate
    receipt = dict(schema=1, scope='synthetic_fixture_integration', status='PASS', production_data=False,
                   probe=s.hashes(Path(__file__)),
                   source_selection_injection='owned synthetic SourceSpec values only; unchanged main entry point',
                   driver=candidate, native=s.hashes(s.DEFAULT_CANDIDATE), report=s.hashes(report_path),
                   inputs=[s.hashes(spec.path) for spec in specs], selected_rows=2000,
                   elapsed_driver_seconds=elapsed, observed_rows_per_second=2000/elapsed,
                   timing_limitation='Synthetic one-ply rows; no production throughput or deep-gap completion prediction.',
                   positive_depth_checks=results, negative_fixture_audits=fixture_verdicts,
                   time_vienna=datetime.now().strftime('%Y-%m-%d %H:%M:%S Vienna'))
    s.resource_guard(reserve_bytes=1024**2)
    (base / 'RECEIPT.json').write_text(json.dumps(receipt, sort_keys=True, indent=2)+'\n')
    print(json.dumps(receipt, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
