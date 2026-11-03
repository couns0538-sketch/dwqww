"""Independent decoding and cross-checks for compact observed-chain artifacts."""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import hashlib
import struct

from r14_group_map import Segment, checked_ranges
from run_policy import safe_path, signature

FORMATS = {'ranges': struct.Struct('<IIQB'), 'pairs': struct.Struct('<IBI'), 'boundaries': struct.Struct('<IBI')}
REASONS = {0: 'REACHABLE', 1: 'UNREACHABLE', 2: 'UNREACHABLE', 3: 'UNREACHABLE',
           4: 'UNKNOWN', 5: 'UNKNOWN', 6: 'UNKNOWN', 7: 'UNKNOWN', 8: 'UNKNOWN',
           250: 'source_start', 251: 'scope_gap'}


def artifact_records(entries, kind, *, guard=lambda: None):
    layout = FORMATS[kind]
    for entry in entries:
        path = safe_path(entry['path'])
        before = path.stat()
        if entry['bytes'] != before.st_size or entry['records']*layout.size != before.st_size:
            raise ValueError('artifact byte/record count mismatch')
        md5, sha256 = hashlib.md5(), hashlib.sha256()
        records = 0
        with path.open('rb') as stream:
            while block := stream.read(layout.size*4096):
                guard()
                md5.update(block)
                sha256.update(block)
                if len(block) % layout.size:
                    raise ValueError('truncated artifact record')
                for record in layout.iter_unpack(block):
                    records += 1
                    yield record
        if records != entry['records'] or signature(path.stat()) != signature(before):
            raise ValueError('artifact count/identity changed')
        if md5.hexdigest() != entry['md5'] or sha256.hexdigest() != entry['sha256']:
            raise ValueError('artifact hash mismatch')


def load_chain_ranges(report, directory, *, guard=lambda: None):
    """Hash every part, reconcile every pair and retain only compact ranges.

    This validates the supplied map's internal consistency. Caller must also bind
    the manifest, helper qualification and original inputs before using it.
    """
    base = safe_path(directory, write=True)
    if (report.get('schema') != 1 or report.get('scope') != 'bounded_adjacent_chain_segments'
            or report.get('mode') != 'jobA' or report.get('complete') is not True):
        raise ValueError('completed jobA chain report required')
    source_ids = [entry['source_id'] for entry in report['source_specs']]
    if not source_ids or source_ids != sorted(set(source_ids)) or any(type(s) is not int or s < 0 for s in source_ids):
        raise ValueError('invalid source identities')
    receipts = {entry['source_id']: entry for entry in report['input_receipts']}
    if len(receipts) != len(report['input_receipts']) or set(receipts) != set(source_ids):
        raise ValueError('source receipt coverage mismatch')
    parts, names = defaultdict(list), set()
    for entry in report['artifacts']:
        source, kind = entry['source_id'], entry['kind']
        if source not in source_ids or kind not in FORMATS:
            raise ValueError('unknown artifact source/kind')
        path = safe_path(entry['path'])
        if not path.is_relative_to(base):
            raise ValueError('artifact outside report directory')
        name = str(path).casefold()
        if name in names:
            raise ValueError('duplicate artifact path')
        names.add(name)
        if any(type(entry[field]) is not int or entry[field] < 0 for field in ('bytes', 'records')):
            raise ValueError('invalid artifact size')
        if entry['bytes'] > 10*1024**2:
            raise ValueError('artifact exceeds bounded part size')
        parts[source, kind].append(entry)
    ranges, start_codes = {}, {}
    last_identity = 0
    previous_source = None
    for source in source_ids:
        ranges[source], start_codes[source] = [], []
        for first, last, ident, code in artifact_records(parts[source, 'ranges'], 'ranges', guard=guard):
            if code not in REASONS:
                raise ValueError('unknown range code')
            if code == 0:
                seam = [edge for edge in report['cross_file_adjacent_pairs']
                        if edge['left_source'] == previous_source and edge['right_source'] == source]
                if (ranges[source] or ident != last_identity or first != 1 or len(seam) != 1
                        or seam[0]['code'] != 0 or seam[0]['continued_segment_id'] != ident):
                    raise ValueError('unbound repeated segment identity at seam')
            elif ident != last_identity+1:
                raise ValueError('nonmonotonic global segment identity')
            last_identity = ident
            ranges[source].append(Segment(first, last, ident, REASONS[code]))
            start_codes[source].append(code)
        if not ranges[source]:
            raise ValueError('missing range coverage')
        previous_source = source
    checked_ranges(ranges)
    seam_by_right = {}
    for edge in report['cross_file_adjacent_pairs']:
        left, right = edge['left_source'], edge['right_source']
        if right not in source_ids or source_ids.index(right) == 0 or right in seam_by_right:
            raise ValueError('duplicate or orphan seam')
        if left != source_ids[source_ids.index(right)-1]:
            raise ValueError('seam sources are not adjacent')
        left_last, right_first = ranges[left][-1], ranges[right][0]
        if (edge['left_line'] != left_last.last or left_last.last != receipts[left].get('rows')
                or edge['right_line'] != right_first.first or right_first.first != 1):
            raise ValueError('seam does not bind complete physical source endpoints')
        if edge['code'] not in REASONS or edge['code'] >= 250 or type(edge['nodes']) is not int or not 0 <= edge['nodes'] <= 1000000:
            raise ValueError('invalid seam outcome')
        continued = left_last.identity if edge['code'] == 0 else None
        if edge['continued_segment_id'] != continued or start_codes[right][0] != edge['code']:
            raise ValueError('seam continuation/range mismatch')
        seam_by_right[right] = edge
    for left, right in zip(source_ids, source_ids[1:]):
        physical = ranges[left][-1].last == receipts[left].get('rows') and ranges[right][0].first == 1
        if physical != (right in seam_by_right):
            raise ValueError('physical seam coverage mismatch')
    totals = dict(pairs=0, boundaries=0, ranges=sum(len(v) for v in ranges.values()), sources=len(source_ids))
    outcomes = Counter()
    if last_identity != report['segment_count'] or totals['ranges'] != report['range_count']:
        raise ValueError('manifest segment/range count mismatch')
    for source in source_ids:
        receipt = receipts[source]
        windows, covered = [], 0
        for segment in ranges[source]:
            covered += segment.last-segment.first+1
            if windows and segment.first == windows[-1][1]+1:
                windows[-1][1] = segment.last
            else:
                windows.append([segment.first, segment.last])
        if windows != receipt['chain_scanned_ranges'] or covered != receipt['chain_scanned_rows']:
            raise ValueError('range/source coverage mismatch')
        expected_lines = (line for first, last in windows for line in range(first, last+1))
        boundaries = artifact_records(parts[source, 'boundaries'], 'boundaries', guard=guard)
        range_offset = 0
        pair_count = 0
        for line, code, nodes in artifact_records(parts[source, 'pairs'], 'pairs', guard=guard):
            if line != next(expected_lines, None):
                raise ValueError('pair row coverage mismatch')
            if code not in REASONS or nodes > 1000000:
                raise ValueError('invalid pair code/node count')
            if pair_count == 0 and source in seam_by_right:
                edge = seam_by_right[source]
                if (line, code, nodes) != (edge['right_line'], edge['code'], edge['nodes']):
                    raise ValueError('seam/pair record mismatch')
            while line > ranges[source][range_offset].last:
                range_offset += 1
            segment = ranges[source][range_offset]
            required_code = start_codes[source][range_offset] if line == segment.first else 0
            if code != required_code:
                raise ValueError('pair/range boundary mismatch')
            if code != 0:
                if next(boundaries, None) != (line, code, nodes):
                    raise ValueError('missing or inconsistent boundary record')
                totals['boundaries'] += 1
            if code < 250:
                outcomes[REASONS[code]] += 1
            pair_count += 1
        if next(expected_lines, None) is not None or pair_count != covered:
            raise ValueError('incomplete pair coverage')
        if next(boundaries, None) is not None:
            raise ValueError('extra boundary record')
        totals['pairs'] += pair_count
    recorded = report['pair_counts']
    if (set(recorded)-{'REACHABLE', 'UNREACHABLE', 'UNKNOWN'}
            or any(type(value) is not int or value < 0 for value in recorded.values())
            or any(recorded.get(name, 0) != outcomes[name] for name in ('REACHABLE', 'UNREACHABLE', 'UNKNOWN'))):
        raise ValueError('manifest pair outcome count mismatch')
    totals['pair_counts'] = dict(outcomes)
    return ranges, totals
