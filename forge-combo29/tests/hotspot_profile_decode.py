#!/usr/bin/env python3
"""Decode this x86-64 little-endian glibc gmon format with explicit ELF ranges.

Independent of gprof's name attribution. Histogram bins use midpoint mapping;
raw arc entry counts include recursion. This is not a general gmon decoder.
"""
import argparse
import bisect
import collections
import json
import pathlib
import re
import struct
import subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('binary', type=pathlib.Path)
    parser.add_argument('gmon', type=pathlib.Path)
    parser.add_argument('output', type=pathlib.Path)
    args = parser.parse_args()
    raw = args.gmon.read_bytes()
    if raw[:4] != b'gmon' or struct.unpack_from('<I', raw, 4)[0] != 1:
        raise RuntimeError('Expected version-1 little-endian gmon')
    symbols = {}
    for line in subprocess.check_output(['nm', '-n', '-S', '-C', str(args.binary)], text=True).splitlines():
        m = re.match(r'([0-9a-f]+) ([0-9a-f]+) ([tTwW]) (.+)', line)
        if m:
            address, size = int(m[1], 16), int(m[2], 16)
            symbols.setdefault(address, {'address': address, 'size': size, 'symbol': m[4]})
    starts = sorted(symbols)
    def lookup(address):
        i = bisect.bisect_right(starts, address) - 1
        if i >= 0:
            row = symbols[starts[i]]
            if address < row['address'] + row['size']:
                return row['address']
        return None
    offset = 20
    sample_counts = collections.Counter()
    calls = collections.Counter()
    recursive = collections.Counter()
    unknown_samples = 0
    unknown_calls = 0
    bins = []
    arcs = []
    rates = []
    while offset < len(raw):
        tag = raw[offset]
        offset += 1
        if tag == 0:
            low, high, count, rate = struct.unpack_from('<QQII', raw, offset)
            offset += 40
            histogram = struct.unpack_from('<' + 'H' * count, raw, offset)
            offset += 2 * count
            rates.append(rate)
            for index, ticks in enumerate(histogram):
                if ticks == 0:
                    continue
                address = low + ((2 * index + 1) * (high - low)) // (2 * count)
                key = lookup(address)
                bins.append({'midpoint': address, 'ticks': ticks, 'function_address': key})
                if key is None:
                    unknown_samples += ticks
                else:
                    sample_counts[key] += ticks
        elif tag == 1:
            caller, callee, count = struct.unpack_from('<QQI', raw, offset)
            offset += 20
            key, caller_key = lookup(callee), lookup(caller)
            arcs.append({'caller_pc': caller, 'callee_pc': callee, 'calls': count,
                         'caller_function': caller_key, 'callee_function': key})
            if key is None:
                unknown_calls += count
            else:
                calls[key] += count
                if key == caller_key:
                    recursive[key] += count
        else:
            raise RuntimeError('Unsupported gmon record tag: ' + str(tag))
    if len(rates) != 1:
        raise RuntimeError('Expected one histogram record')
    total_ticks = sum(sample_counts.values()) + unknown_samples
    rows = []
    for key in sample_counts.keys() | calls.keys():
        item = dict(symbols[key])
        item.update({'sample_ticks': sample_counts[key],
                     'sampled_self_seconds': sample_counts[key] / rates[0],
                     'percent_of_all_histogram_ticks': 100 * sample_counts[key] / total_ticks,
                     'instrumented_entries_including_recursion': calls[key],
                     'recursive_entries': recursive[key]})
        # Entry+16 lies beyond common prologues while remaining in each function.
        pc = key + min(16, max(0, item['size'] - 1))
        item['source'] = subprocess.check_output(['addr2line', '-e', str(args.binary), hex(pc)], text=True).strip()
        rows.append(item)
    rows.sort(key=lambda x: (-x['sample_ticks'], -x['instrumented_entries_including_recursion']))
    report = {'format': 'glibc gmon version1, x86-64 little-endian', 'sample_rate_hz': rates[0],
              'total_histogram_ticks': total_ticks, 'unknown_sample_ticks': unknown_samples,
              'unknown_instrumented_entries': unknown_calls,
              'attribution': 'Histogram midpoint mapped to explicit nm symbol size; arcs mapped by callee PC. Function entry counts include recursion and omit inlined instances.',
              'ranked': rows, 'raw_nonzero_bins': bins, 'raw_arcs': arcs}
    args.output.write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
