#!/usr/bin/env python3
"""Independent legality and arithmetic checks of bounded actual-engine traces."""
from pathlib import Path
import collections
import json
import chess

HERE = Path(__file__).resolve().parent
OUT = HERE / 'diagnostic-v2-attempt1'
rows = json.loads((OUT / 'traces.json').read_text())
groups = collections.Counter()
checks = 0
examples = {}
no_move_events = {'incoming_parent_path_mismatch', 'null_parent_path_mismatch'}
for row in rows:
    board = chess.Board(row['fen'])
    assert board.is_valid(), row
    checks += 1
    if row['event'] not in no_move_events:
        assert chess.Move.from_uci(row['move']) in board.legal_moves, row
        checks += 1
    else:
        # Forge move_to_uci(Move::none()) currently renders a1a1. These records
        # describe entry/null metadata, not an emitted move or a real capture.
        assert row['move'] == 'a1a1', row
        checks += 1
    event = row['event']
    if event == 'actual_child_vs_true_path_mismatch':
        assert row['frame_after'] != row['expected_path_before_move'] + (row['extension'] == 2), row
    elif event == 'single_extension_parent_mismatch':
        assert row['extension'] == 1 and row['frame_after'] != row['parent_actual'], row
    elif event == 'incoming_parent_path_mismatch':
        assert row['parent_actual'] != row['expected_path_before_move'], row
    elif event in {'null_parent_path_mismatch', 'probcut_parent_path_mismatch'}:
        assert row['frame_after'] != row['expected_path_before_move'], row
    elif event == 'singular_same_ply_changed':
        assert row['frame_before'] != row['frame_after'], row
    elif event != 'singular_same_ply_before':
        raise AssertionError(row)
    checks += 1
    groups[event] += 1
    examples.setdefault(event, row)
assert len(groups) == 7, groups
summary = json.loads((OUT / 'commands.json').read_text())
assert summary['status'] == 'PASS' and summary['inputs_unchanged']
assert summary['bench_nodes_parity'] == 419798
assert summary['summary_totals']['eligibility_mismatch'] == 0
result = {'status': 'PASS', 'python_chess_version': chess.__version__,
          'trace_rows': len(rows), 'checks': checks, 'event_sample_counts': dict(groups),
          'all_positions_valid': True, 'all_real_candidate_moves_legal': True,
          'all_mismatch_arithmetic_verified': True, 'examples': examples,
          'limit': 'Bounded journals, not full game replay; no eligibility-threshold breach observed.'}
(OUT / 'independent-legal-trace-check.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k != 'examples'}))
