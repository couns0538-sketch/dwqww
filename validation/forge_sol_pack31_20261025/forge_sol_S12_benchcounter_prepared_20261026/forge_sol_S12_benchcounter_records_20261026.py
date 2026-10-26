#!/usr/bin/env python3
"""Validate original future helper stdout; no engine/compiler launch.

Synthetic unit records test this parser only. They are never native evidence.
"""
import argparse
import json
from pathlib import Path
import re

FIELDS = ('refreshes', 'updates', 'zero_dirty_edges', 'copies_avoided', 'alias_hits', 'evaluations')
REFERENCES = {11: 308972, 13: 745494, 16: 2460422, 20: 11901452, 22: 31111774}
MAX = (1 << 64) - 1


def natural(value, label, minimum=0):
    if type(value) is not int or not minimum <= value <= MAX:
        raise ValueError('invalid uint64 ' + label)
    return value


def counters(value):
    if type(value) is not dict or set(value) != set(FIELDS):
        raise ValueError('counter schema changed')
    return {key: natural(value[key], key) for key in FIELDS}


def read_json(line):
    def reject_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate JSON member')
            result[key] = value
        return result
    try:
        return json.loads(line, object_pairs_hook=reject_duplicates)
    except (TypeError, json.JSONDecodeError) as error:
        raise ValueError('invalid helper JSON') from error


def validate(text, binding, mode, depth):
    if mode not in ('OFF', 'ON') or depth not in REFERENCES:
        raise ValueError('unsupported mode/depth')
    records, diagnostics, active, events = [], [], 0, []
    diagnostic_prefix = 'info string NnueLazyAcc stats '
    for line in text.splitlines():
        if line == 'info string NnueLazyAcc active':
            active += 1
            events.append('active')
        elif line.startswith(diagnostic_prefix):
            words = line[len(diagnostic_prefix):].split()
            if len(words) != 12 or tuple(words[::2]) != FIELDS or not all(re.fullmatch(r'[0-9]+', x) for x in words[1::2]):
                raise ValueError('unknown NNUE diagnostic schema')
            diagnostics.append(counters({key: int(value) for key, value in zip(words[::2], words[1::2])}))
            events.append('stats')
        elif line.startswith('{'):
            record = read_json(line)
            if type(record) is not dict:
                raise ValueError('record object required')
            records.append(record)
            events.append(record.get('record'))
        else:
            raise ValueError('unrecognized stdout line; retain original raw stream')
    if len(records) != 10 or records[0].get('record') != 'binding' or records[-1].get('record') != 'total':
        raise ValueError('binding + eight original FEN rows + final total required')
    expected_events = ['binding'] + (['per_fen'] * 8 if mode == 'OFF' else ['active'] + ['stats', 'per_fen'] * 8) + ['total']
    if events != expected_events:
        raise ValueError('raw record/diagnostic order changed')
    header = records[0]
    for field in ['requested_depth', 'suite_count', 'hash_mib', 'threads']:
        natural(header.get(field), field)
    expected_header = {'record': 'binding', 'mode': mode, 'requested_depth': depth,
        'suite_count': 8, 'hash_mib': 16, 'threads': 1,
        'canonical_uci_sha256': binding['canonical_input_sha256']['src/uci.cpp'],
        'bench_block_sha256': binding['bench_block_sha256'], 'suite_sha256': binding['suite_sha256'],
        'candidate_header_sha256': binding['candidate_header_sha256'],
        'candidate_patch_sha256': binding['candidate_patch_sha256']}
    if header != expected_header:
        raise ValueError('source/suite/ABI/mode/depth header binding differs')
    rows = records[1:9]
    totals = {field: 0 for field in FIELDS}
    nodes = 0
    for index, row in enumerate(rows):
        if set(row) != {'record', 'mode', 'requested_depth', 'index', 'fen', 'nodes', 'completed_depth', 'stats'}:
            raise ValueError('per-FEN schema differs')
        for field in ['requested_depth', 'index', 'completed_depth']:
            natural(row[field], field)
        if (row['record'], row['mode'], row['requested_depth'], row['index'], row['fen'], row['completed_depth']) != (
            'per_fen', mode, depth, index, binding['fens'][index], depth):
            raise ValueError('missing/duplicate/reordered/early FEN result')
        item = counters(row['stats'])
        if item['refreshes'] < 1 or item['evaluations'] < 1:
            raise ValueError('missing actual root refresh or evaluation')
        if mode == 'OFF' and (item['copies_avoided'] or item['alias_hits'] or item['zero_dirty_edges'] > item['updates']):
            raise ValueError('OFF mode claims alias work')
        if mode == 'ON' and item['copies_avoided'] != item['zero_dirty_edges']:
            raise ValueError('ON zero-edge accounting inconsistent')
        nodes = natural(nodes + natural(row['nodes'], 'nodes', 1), 'summed nodes')
        for field in FIELDS:
            totals[field] = natural(totals[field] + item[field], 'summed ' + field)
    last = records[-1]
    if set(last) != {'record', 'mode', 'requested_depth', 'positions', 'nodes', 'reference_nodes', 'node_reference_match', 'completed_depths_match', 'stats'}:
        raise ValueError('total schema differs')
    for field in ['requested_depth', 'positions', 'nodes', 'reference_nodes']:
        natural(last[field], field)
    if (last['mode'], last['requested_depth'], last['positions'], last['nodes'], last['reference_nodes']) != (
        mode, depth, 8, nodes, REFERENCES[depth]) or nodes != REFERENCES[depth]:
        raise ValueError('total nodes differ from original rows/fixed reference')
    if last['node_reference_match'] is not True or last['completed_depths_match'] is not True or counters(last['stats']) != totals:
        raise ValueError('aggregate substituted or incomplete depths')
    if mode == 'OFF' and (active or diagnostics):
        raise ValueError('OFF mode emits ON diagnostics')
    if mode == 'ON' and (active != 1 or len(diagnostics) != 8 or diagnostics != [row['stats'] for row in rows] or totals['copies_avoided'] == 0):
        raise ValueError('ON branch/diagnostic/counter proof missing')
    return {'mode': mode, 'depth': depth, 'rows': rows, 'nodes': nodes, 'totals': totals}


def compare(off, on):
    if off['mode'] != 'OFF' or on['mode'] != 'ON' or off['depth'] != on['depth']:
        raise ValueError('not a matched OFF/ON pair')
    for left, right in zip(off['rows'], on['rows']):
        if any(left[key] != right[key] for key in ['index', 'fen', 'nodes', 'completed_depth']):
            raise ValueError('per-FEN search signature changed')
        a, b = left['stats'], right['stats']
        if any(a[key] != b[key] for key in ['refreshes', 'evaluations', 'zero_dirty_edges']):
            raise ValueError('refresh/evaluation/zero-edge work changed')
        if a['updates'] != b['updates'] + b['copies_avoided']:
            raise ValueError('nonempty update accounting changed')
    return {'status': 'PASS_COUNTER_AND_NODE_PAIR', 'depth': off['depth'], 'nodes': off['nodes'],
            'OFF': off['totals'], 'ON': on['totals'], 'speed_or_Elo_claim': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binding', type=Path, required=True)
    parser.add_argument('--off-stdout', type=Path, required=True)
    parser.add_argument('--on-stdout', type=Path, required=True)
    parser.add_argument('--depth', type=int, choices=REFERENCES, required=True)
    args = parser.parse_args()
    bound = json.loads(args.binding.read_text())
    print(json.dumps(compare(validate(args.off_stdout.read_text(), bound, 'OFF', args.depth),
                             validate(args.on_stdout.read_text(), bound, 'ON', args.depth)), indent=2))
