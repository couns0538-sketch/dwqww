"""Map prepared groups to observed source chains without authenticating games."""
from __future__ import annotations

from bisect import bisect_right
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import hashlib

from r14_scan import Row, parse_row, iter_rows
from run_policy import free_guard, safe_path, signature

FIELDS = ('row_id', 'game_id', 'split', 'fen', 'old_score_stm', 'result', 'source', 'source_row')


@dataclass(frozen=True, slots=True)
class Prepared:
    row_id: int
    group: str
    split: str
    source: int
    source_line: int
    row: Row


@dataclass(frozen=True, slots=True)
class Segment:
    first: int
    last: int
    identity: int
    start_reason: str


def iter_prepared(path: Path, expected_md5: str, receipt: dict):
    """Read every physical TSV row, retaining invalid rows in coverage counts."""
    path = safe_path(path)
    before = path.stat()
    receipt.update(path=str(path), expected_md5=expected_md5, rows=0,
                   valid_key_rows=0, parse_failures=0, missing_key_rows=0,
                   key_fill_rate=None, complete=False)
    digest = hashlib.md5()
    previous_location = (-1, 0)
    with path.open('rb') as stream:
        header = stream.readline(4097)
        digest.update(header)
        if tuple(header.decode('ascii').rstrip('\r\n').split('\t')) != FIELDS:
            raise ValueError('prepared header mismatch')
        while raw := stream.readline(4097):
            digest.update(raw)
            long = len(raw) > 4096
            if long:
                while not raw.endswith(b'\n'):
                    raw = stream.readline(4097)
                    if not raw:
                        break
                    digest.update(raw)
            receipt['rows'] += 1
            item = None
            try:
                if long:
                    raise ValueError('long prepared row')
                values = raw.decode('ascii').rstrip('\r\n').split('\t')
                if len(values) != len(FIELDS):
                    raise ValueError('prepared column count')
                ident, group, split, fen, score, result, source, line = values
                if not all(value.isascii() and value.isdecimal() for value in (ident, source, line)):
                    raise ValueError('nonnegative decimal identities required')
                ident, source, line = int(ident), int(source), int(line)
                if ident != receipt['rows']-1 or source not in (0, 1) or line < 1:
                    raise ValueError('prepared identity or source location invalid')
                if not group or len(group) > 200 or any(ord(c) < 33 for c in group) or split not in ('train', 'val'):
                    raise ValueError('invalid group/split')
                if (source, line) <= previous_location:
                    raise ValueError('source locations repeated or reordered')
                position = parse_row((fen+' | '+score+' | '+result).encode('ascii'))
                item = Prepared(ident, group, split, source, line, position)
                previous_location = (source, line)
            except (ValueError, UnicodeError):
                receipt['parse_failures'] += 1
                receipt['missing_key_rows'] += 1
            else:
                receipt['valid_key_rows'] += 1
            if receipt['rows'] % 65536 == 0:
                free_guard()
            yield item
    actual = digest.hexdigest()
    receipt['actual_md5'] = actual
    receipt['key_fill_rate'] = receipt['valid_key_rows']/receipt['rows'] if receipt['rows'] else None
    if actual != expected_md5:
        raise ValueError('prepared input hash mismatch')
    if signature(path.stat()) != signature(before):
        raise ValueError('prepared input changed')
    receipt['complete'] = True


def checked_ranges(ranges):
    starts = {}
    for source, segments in ranges.items():
        if type(source) is not int or source < 0:
            raise ValueError('invalid source identity')
        previous = 0
        identities = set()
        for segment in segments:
            if (type(segment.first) is not int or type(segment.last) is not int
                    or segment.first <= previous or segment.last < segment.first):
                raise ValueError('overlapping or unordered segment range')
            if type(segment.identity) is not int or segment.identity < 0 or segment.identity in identities:
                raise ValueError('invalid or repeated segment identity')
            if segment.start_reason not in ('source_start', 'scope_gap', 'REACHABLE', 'UNREACHABLE', 'UNKNOWN'):
                raise ValueError('invalid segment start reason')
            identities.add(segment.identity)
            previous = segment.last
        starts[source] = [segment.first for segment in segments]
    return starts


def join_sources(records, sources, pins, receipt, *, guard=lambda: None):
    """Verify each selected row and consume/hash all original source bytes.

    Invalid prepared rows and failed joins yield None so downstream counts keep
    every selected record. Abandoned generators leave the receipt incomplete.
    """
    receipt.update(rows=0, matched_rows=0, mismatches=[], sources=[],
                   source_join_fill_rate=None, complete=False)
    cursors = {}
    for source, raw_path in sorted(sources.items()):
        path = safe_path(raw_path)
        key = str(path).casefold()
        if key not in pins:
            raise ValueError('source input lacks verified pin')
        source_receipt = {}
        receipt['sources'].append(source_receipt)
        cursors[source] = dict(iterator=iter_rows(path, pins[key], source_receipt),
                               line=0, row=None, exhausted=False)

    def advance(cursor, target=None):
        while not cursor['exhausted'] and (target is None or cursor['line'] < target):
            try:
                cursor['line'], cursor['row'] = next(cursor['iterator'])
            except StopIteration:
                cursor['exhausted'] = True
                break
            if cursor['line'] % 65536 == 0:
                guard()

    previous_location = (-1, 0)
    for item in records:
        receipt['rows'] += 1
        if item is None:
            yield None
            continue
        if (item.source, item.source_line) <= previous_location:
            raise ValueError('source join requires increasing source locations')
        previous_location = (item.source, item.source_line)
        for source, cursor in cursors.items():
            if source < item.source:
                advance(cursor)
        cursor = cursors.get(item.source)
        reason = None
        if cursor is None:
            reason = 'source_absent'
        else:
            advance(cursor, item.source_line)
            actual = cursor['row']
            if cursor['line'] != item.source_line:
                reason = 'source_row_absent'
            elif actual is None:
                reason = 'source_row_unparsable'
            elif (actual.fen, actual.score, actual.result) != (item.row.fen, item.row.score, item.row.result):
                reason = 'source_value_mismatch'
        if reason:
            receipt['mismatches'].append(dict(row_id=item.row_id, source=item.source,
                                              source_line=item.source_line, reason=reason))
            yield None
        else:
            receipt['matched_rows'] += 1
            yield item
    for cursor in cursors.values():
        advance(cursor)
    receipt['source_join_fill_rate'] = receipt['matched_rows']/receipt['rows'] if receipt['rows'] else None
    receipt['complete'] = bool(cursors) and all(item.get('complete') is True for item in receipt['sources'])


def audit_groups(records, ranges, *, guard=lambda: None):
    """Compare inferred group membership with a completed observed-range map.

    A comparison PASS is limited to the supplied observed chains. This function
    never supplies producer provenance or original game IDs and cannot permit
    export. Callers must separately bind range evidence to qualified source scans.
    """
    starts = checked_ranges(ranges)
    groups, owners = {}, {}
    total = valid = mapped = 0
    missing = []
    previous_group = None
    closed_groups = set()
    reappeared = set()
    for item in records:
        total += 1
        if total % 65536 == 0:
            guard()
        if item is None:
            continue
        valid += 1
        if item.group != previous_group:
            if previous_group is not None:
                closed_groups.add(previous_group)
            if item.group in closed_groups:
                reappeared.add(item.group)
            previous_group = item.group
        group = groups.setdefault(item.group, dict(group=item.group, rows=0,
                                  first_row_id=item.row_id, last_row_id=item.row_id,
                                  splits=set(), sources=set(), segments=set(),
                                  definite_breaks=[], unknown_breaks=[], mapped_rows=0,
                                  _last_location=None))
        group['rows'] += 1
        group['last_row_id'] = item.row_id
        group['splits'].add(item.split)
        group['sources'].add(item.source)
        offsets = starts.get(item.source, [])
        offset = bisect_right(offsets, item.source_line)-1
        segment = ranges[item.source][offset] if offset >= 0 else None
        if segment is None or item.source_line > segment.last:
            missing.append(dict(row_id=item.row_id, source=item.source, source_line=item.source_line))
            continue
        mapped += 1
        group['mapped_rows'] += 1
        previous_location = group['_last_location']
        if previous_location is not None:
            previous_source, previous_offset = previous_location
            if (item.source, offset) < previous_location:
                raise ValueError('group source locations moved backwards')
            for source in sorted(ranges):
                if not previous_source <= source <= item.source:
                    continue
                first = previous_offset+1 if source == previous_source else 0
                last = offset+1 if source == item.source else len(ranges[source])
                for boundary in ranges[source][first:last]:
                    if boundary.start_reason == 'REACHABLE':
                        continue
                    record = dict(source=source, first_line=boundary.first, segment=boundary.identity,
                                  start_reason=boundary.start_reason)
                    field = 'definite_breaks' if boundary.start_reason == 'UNREACHABLE' else 'unknown_breaks'
                    group[field].append(record)
        group['_last_location'] = (item.source, offset)
        group['segments'].add(segment.identity)
        owner = owners.setdefault(segment.identity, dict(groups=set(), splits=set(), selected_rows=0))
        owner['groups'].add(item.group)
        owner['splits'].add(item.split)
        owner['selected_rows'] += 1
    shared = [dict(segment=ident, groups=sorted(owner['groups']), splits=sorted(owner['splits']),
                   selected_rows=owner['selected_rows']) for ident, owner in sorted(owners.items())
              if len(owner['groups']) > 1 or len(owner['splits']) > 1]
    counts = Counter()
    for group in groups.values():
        del group['_last_location']
        counts['definite_fragmented_groups'] += bool(group['definite_breaks'])
        counts['unknown_fragmented_groups'] += bool(group['unknown_breaks'])
        counts['groups_with_multiple_splits'] += len(group['splits']) > 1
        for field in ('splits', 'sources', 'segments'):
            group[field] = sorted(group[field])
    counts['segments_with_multiple_groups'] = sum(len(owner['groups']) > 1 for owner in owners.values())
    counts['segments_shared_between_splits'] = sum(len(owner['splits']) > 1 for owner in owners.values())
    definite = (counts['definite_fragmented_groups'] or counts['groups_with_multiple_splits']
                or counts['segments_with_multiple_groups'] or reappeared)
    unknown = not total or mapped != total or counts['unknown_fragmented_groups']
    return dict(schema=1, scope='inferred_groups_vs_observed_chain_ranges',
                comparison_status='FAIL' if definite else 'UNVERIFIED' if unknown else 'PASS',
                authentic_game_ids='UNVERIFIED', export_allowed=False,
                rows=total, valid_prepared_rows=valid, mapped_rows=mapped,
                mapping_fill_rate=mapped/total if total else None,
                group_count=len(groups), reappeared_groups=sorted(reappeared),
                groups=list(groups.values()), shared_segments=shared, missing_mapping=missing,
                **{name: counts[name] for name in ('definite_fragmented_groups', 'unknown_fragmented_groups',
                   'groups_with_multiple_splits', 'segments_with_multiple_groups', 'segments_shared_between_splits')})
