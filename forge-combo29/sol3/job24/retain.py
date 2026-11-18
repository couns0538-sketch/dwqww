#!/usr/bin/env python3
"""Summarize sealed text streams and enforce Job 24 publication limits."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys


FILE_LIMIT = 5_000_000
JOB_LIMIT = 20_000_000
REPORT_LIMIT = 200
LABEL = re.compile(r'[A-Za-z0-9_][A-Za-z0-9_.-]{0,79}')
INSTRUMENTED_ASSERT = re.compile(rb'^job(?:23 assert (A[123])|24 assert (A1s|A2s|A4|A7)) move ')
ASSERTION = re.compile(rb'\b[Aa]ssertion [`\'"][^\r\n]{1,4096}?[`\'"] failed(?:[.!:]|\s*$)')
CHECKER = re.compile(rb'^\s*(?:==\d+==\s*)?(?:ERROR|WARNING): (AddressSanitizer|LeakSanitizer|ThreadSanitizer):')
UBSAN = re.compile(rb'^\s*\S.*?:\d+(?::\d+)?: runtime error:')
RUNTIME = re.compile(rb'^\s*(?:==\d+==\s*)?(?:AddressSanitizer: ?(?:DEADLYSIGNAL|CHECK failed|FATAL)|'
                     rb'FATAL: (?:AddressSanitizer|ThreadSanitizer):|ThreadSanitizer(?:: ?FATAL| CHECK failed)|'
                     rb'ASan runtime does not come first|Shadow memory range interleaves)')
DELIMITER = re.compile(rb'^={10,}\s*$')
ABORT = re.compile(rb'^\s*(?:==\d+==\s*)?ABORTING\s*$')
DEFAULT_CONTEXT = r'^\s*(?:info string )?(?:job2[34] context|assert context)\b'


def diagnostic(line):
    if instrumented := INSTRUMENTED_ASSERT.match(line):
        return 'assert', (instrumented[1] or instrumented[2]).decode()
    if ASSERTION.search(line):
        return 'assert', 'assertion'
    if matched := CHECKER.match(line):
        return 'checker', matched[1].decode()
    if UBSAN.match(line):
        return 'checker', 'UndefinedBehaviorSanitizer'
    if RUNTIME.match(line):
        sanitizer = 'ThreadSanitizer' if b'ThreadSanitizer' in line else 'AddressSanitizer'
        return 'runtime', sanitizer
    return None


def stat_key(stat):
    return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns


def valid_text(content):
    if b'\0' in content:
        return False
    try:
        content.decode('utf-8')
    except UnicodeDecodeError:
        return False
    return True


class Block:
    def __init__(self, first, header, category, tool, line_limit):
        self.first = first
        self.header = header
        self.category = category
        self.tool = tool
        self.line_limit = line_limit
        self.data = bytearray()
        self.lines = 0
        self.raw_bytes = 0

    def add(self, line, storage_limit):
        self.lines += 1
        self.raw_bytes += len(line)
        if self.line_limit is None or self.lines <= self.line_limit:
            if len(self.data) + len(line) > storage_limit:
                raise ValueError('report evidence exceeds retention budget, use --first-lines-only '
                                 'or keep separate batches with sufficient job budget')
            self.data.extend(line)


def read_stream(path, context_re, first_lines_only, storage_limit):
    before = stat_key(path.stat())
    digest = hashlib.sha256()
    total_bytes = 0
    num = 0
    prefix = None
    block = None
    reports = []
    header_count = Counter()
    block_counts = Counter()
    retained_bytes = 0

    def save_block():
        nonlocal retained_bytes
        if block is not None and len(reports) < REPORT_LIMIT:
            reports.append(block)
            retained_bytes += len(block.data)

    with path.open('rb') as raw:
        for num, line in enumerate(raw, 1):
            digest.update(line)
            total_bytes += len(line)
            match = diagnostic(line)
            if match is not None:
                category, tool = match
                header_count[category] += 1
                if (block is not None and block.category == category == 'assert'
                        and block.tool != 'assertion' and tool == 'assertion' and block.lines <= 4):
                    block.add(line, storage_limit - retained_bytes)
                    prefix = None
                    continue
                if (block is not None and block.category == 'runtime' and block.tool == 'AddressSanitizer'
                        and tool == 'AddressSanitizer' and (b'DEADLYSIGNAL' in line or category == 'checker')):
                    if category == 'checker':
                        block_counts['runtime'] -= 1
                        block_counts['checker'] += 1
                        block.category = 'checker'
                        block.header = num
                    block.add(line, storage_limit - retained_bytes)
                    prefix = None
                    continue
                save_block()
                block_counts[category] += 1
                first = num - 1 if prefix is not None else num
                line_limit = 0 if len(reports) == REPORT_LIMIT else 30 if first_lines_only else None
                block = Block(first, num, category, tool, line_limit)
                if prefix is not None:
                    block.add(prefix, storage_limit - retained_bytes)
                block.add(line, storage_limit - retained_bytes)
                prefix = None
                continue
            context = context_re.search(line)
            separator = DELIMITER.fullmatch(line)
            if block is not None:
                if context:
                    save_block()
                    block = None
                else:
                    block.add(line, storage_limit - retained_bytes)
                    if (block.tool == 'ThreadSanitizer' and separator) or ABORT.fullmatch(line):
                        save_block()
                        block = None
                    prefix = None
                    continue
            prefix = line if context or separator else None
    save_block()
    if stat_key(path.stat()) != before or before[2] != total_bytes:
        raise ValueError(f'{path} changed during readback; wait for the process log to close')
    return {'path': str(path), 'bytes': total_bytes, 'lines': num, 'sha256': digest.hexdigest(),
            'report_headers': sum(header_count.values()), 'headers_by_type': dict(header_count),
            'report_blocks': sum(block_counts.values()), 'blocks_by_type': {k: v for k, v in block_counts.items() if v},
            'assert_stops': block_counts['assert'], 'checker_reports': block_counts['checker'],
            'runtime_failures': block_counts['runtime']}, reports


def write_block_files(outputs, label, blocks):
    current = bytearray()
    ordinal = 1
    details = []

    def shard_name():
        return f'{label}.reports.{ordinal:03d}.txt'

    for block in blocks:
        last = block.first + block.lines - 1
        banner = (f'\n=== {block.category} | {block.tool} | raw lines {block.first}-{last} '
                  f'| diagnostic line {block.header} ===\n').encode()
        raw = bytes(block.data)
        if not valid_text(raw):
            raise ValueError(f'{label} report at line {block.header} is not UTF-8 text')
        entry = banner + raw + (b'' if raw.endswith(b'\n') else b'\n')
        if len(entry) > FILE_LIMIT:
            raise ValueError(f'{label} report at line {block.header} is >{FILE_LIMIT:,} bytes with headers; '
                             'use --first-lines-only')
        if len(current) + len(entry) > FILE_LIMIT:
            outputs[shard_name()] = bytes(current)
            current.clear()
            ordinal += 1
        details.append({'type': block.category, 'tool': block.tool, 'diagnostic_line': block.header,
                        'first_raw_line': block.first, 'last_raw_line': last, 'first_30_through': min(last, block.first + 29),
                        'raw_bytes': block.raw_bytes, 'retained_raw_bytes': len(raw),
                        'raw_sha256_of_retained_lines': hashlib.sha256(raw).hexdigest(), 'published_file': shard_name(),
                        'published_byte_offset': len(current) + len(banner)})
        current.extend(entry)
    if current:
        outputs[shard_name()] = bytes(current)
    return details


def assignments(values):
    sources = {}
    for value in values:
        name, equal, path = value.partition('=')
        if not equal or not LABEL.fullmatch(name) or not path or name in sources:
            raise ValueError(f'invalid or repeated LABEL=PATH input {value!r}')
        sources[name] = Path(path).resolve(strict=True)
    return sources


def retain(options):
    sources = assignments(options.input)
    copy_labels = set(options.copy_small)
    if unknown := copy_labels - set(sources):
        raise ValueError(f'--copy-small names no input for {sorted(unknown)}')
    if not 1 <= options.budget <= JOB_LIMIT:
        raise ValueError(f'--budget must be 1..{JOB_LIMIT}')
    context = re.compile(options.context_regex.encode())
    receipt = []
    outputs = {}
    used = 0
    for label, path in sources.items():
        if not path.is_file():
            raise ValueError(f'not a regular stream file: {path}')
        record, reports = read_stream(path, context, options.first_lines_only, options.budget - used)
        record.update({'label': label, 'retained_reports': write_block_files(outputs, label, reports),
                       'raw_copy': 'local_only'})
        if label in copy_labels and record['bytes'] > FILE_LIMIT:
            record['raw_copy'] = 'omitted_above_file_limit'
        elif label in copy_labels:
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != record['sha256'] or len(raw) != record['bytes']:
                raise ValueError(f'{path} changed before optional raw copy')
            if not valid_text(raw):
                raise ValueError(f'{path} is not UTF-8 text')
            key = f'{label}.raw.txt'
            outputs[key] = raw
            record['raw_copy'] = key
        receipt.append(record)
        used = sum(map(len, outputs.values()))
        if used > options.budget:
            raise ValueError(f'retained output would need at least {used:,} bytes with {options.budget:,} available')
    about = {'per_file_limit_bytes': FILE_LIMIT, 'job_limit_bytes': JOB_LIMIT, 'batch_budget_bytes': options.budget,
             'first_reports_per_stream': REPORT_LIMIT, 'first_lines_only': options.first_lines_only, 'streams': receipt}
    outputs['receipts.json'] = (json.dumps(about, indent=2, ensure_ascii=False) + '\n').encode()
    total = sum(map(len, outputs.values()))
    if total > options.budget or any(len(data) > FILE_LIMIT for data in outputs.values()):
        raise ValueError(f'retention files plus receipts would use {total:,} bytes (budget {options.budget:,}) '
                         'or breach the per-file limit')
    options.out.mkdir()
    for filename, content in outputs.items():
        with (options.out / filename).open('xb') as handle:
            handle.write(content)
    return {'retention_files': len(outputs), 'retention_bytes': total, 'receipt': str(options.out / 'receipts.json')}


def check(options):
    if not options.root.is_dir():
        raise ValueError(f'not a job directory: {options.root}')
    members = sorted(path for path in options.root.rglob('*') if not path.is_dir() or path.is_symlink())
    members.extend(options.extra)
    seen = set()
    data = []
    issues = []
    for path in members:
        if path.is_symlink() or not path.is_file():
            issues.append(f'not a regular text file: {path}')
            continue
        if path.resolve() in seen:
            continue
        seen.add(path.resolve())
        size = path.stat().st_size
        data.append({'path': str(path), 'bytes': size})
        if size > FILE_LIMIT:
            issues.append(f'{path} is {size:,} bytes (limit {FILE_LIMIT:,})')
        elif not valid_text(path.read_bytes()):
            issues.append(f'{path} is not UTF-8 text')
    total = sum(item['bytes'] for item in data)
    if total > JOB_LIMIT:
        issues.append(f'job totals {total:,} bytes (limit {JOB_LIMIT:,})')
    return {'ok': not issues, 'files': len(data), 'job_bytes': total, 'job_limit_bytes': JOB_LIMIT,
            'per_file_limit_bytes': FILE_LIMIT, 'errors': issues, 'members': data}


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    commands = cli.add_subparsers(dest='operation', required=True)
    publication = commands.add_parser('retain', help='create an auditable scratch retention batch')
    publication.add_argument('--out', required=True, type=Path, help='new output directory (parent must exist)')
    publication.add_argument('--input', metavar='LABEL=PATH', action='append', required=True)
    publication.add_argument('--copy-small', metavar='LABEL', action='append', default=[])
    publication.add_argument('--budget', type=int, default=JOB_LIMIT, help='actual available publication bytes')
    publication.add_argument('--context-regex', default=DEFAULT_CONTEXT, help='raw marker regex immediately before a diagnostic')
    publication.add_argument('--first-lines-only', action='store_true', help='explicit fallback if full blocks exceed caps')
    ceiling = commands.add_parser('check', help='validate the publication tree and explicit outside artifacts')
    ceiling.add_argument('--root', type=Path, required=True)
    ceiling.add_argument('--extra', type=Path, action='append', default=[])
    options = cli.parse_args()
    try:
        result = retain(options) if options.operation == 'retain' else check(options)
        print(json.dumps(result, indent=2))
        return 0 if result.get('ok', True) else 1
    except (OSError, ValueError, re.error) as error:
        print(f'Retention failed: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
