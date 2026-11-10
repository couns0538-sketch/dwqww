#!/usr/bin/env python3
"""Reattribute existing HCE histogram bins; no execution of an engine."""
import argparse
import collections
import hashlib
import json
import pathlib
import re
import subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--binary', type=pathlib.Path, required=True)
    parser.add_argument('--decoded', type=pathlib.Path, required=True)
    parser.add_argument('--profile-metadata', type=pathlib.Path, required=True)
    parser.add_argument('--output', type=pathlib.Path, required=True)
    args = parser.parse_args()
    metadata = json.loads(args.profile_metadata.read_text())
    actual = hashlib.sha256(args.binary.read_bytes()).hexdigest()
    if actual != metadata['profile_binary_sha256']:
        raise RuntimeError('Profiling binary hash does not match recorded profile')
    decoded = json.loads(args.decoded.read_text())
    names = {}
    per_run = {}
    for name, run in decoded.items():
        hce = next(row for row in run['ranked'] if 'evaluate_position<false>' in row['symbol'])
        bins = [row for row in run['raw_nonzero_bins'] if row['function_address'] == hce['address']]
        for row in bins:
            names.setdefault(row['midpoint'], None)
        per_run[name] = {'hce_ticks': hce['sample_ticks'], 'all_ticks': run['total_histogram_ticks'], 'bins': bins}
    def classify(frames):
        # Use the first source-specific eval helper line. The common accumulator
        # add() at 31-42 is not a helper-specific attribution by itself.
        lines = [f['line'] for f in frames if f['file'].endswith('/src/eval.cpp') and f['line']]
        for line in lines:
            if 56 <= line <= 97: return 'pawn_structure'
            if 99 <= line <= 195: return 'pieces'
            if 197 <= line <= 273: return 'king'
            if 275 <= line <= 317: return 'threats'
            if 319 <= line <= 345: return 'passed_pawns'
        for line in lines:
            if 375 <= line <= 395: return 'setup_psqt_phase'
            if 397 <= line <= 413: return 'pawn_cache_dispatch'
            if 418 <= line <= 439: return 'attack_mobility_setup'
            if 441 <= line <= 448: return 'helper_dispatch_unresolved'
            if 450 <= line <= 474: return 'final_score_taper'
        return 'unresolved'
    for address in names:
        raw = subprocess.check_output(['addr2line', '-i', '-f', '-C', '-e', str(args.binary), hex(address)], text=True)
        lines = raw.splitlines()
        if len(lines) % 2:
            raise RuntimeError('Unexpected addr2line output')
        frames = []
        for index in range(0, len(lines), 2):
            location = lines[index + 1]
            match = re.match(r'(.+):(\d+)(.*)$', location)
            frames.append({'function': lines[index], 'location': location,
                           'file': match[1] if match else location,
                           'line': int(match[2]) if match else None})
        names[address] = {'address': address, 'address_hex': hex(address), 'frames': frames,
                          'coarse_group': classify(frames), 'raw_addr2line': raw}
    for name, run in per_run.items():
        groups = collections.Counter()
        line_ticks = collections.Counter()
        for row in run['bins']:
            location = names[row['midpoint']]
            groups[location['coarse_group']] += row['ticks']
            # Retain complete inline-chain identity; do not pretend the leaf
            # line owns all cost or that compiler discriminators are timings.
            chain = ' | '.join(f['location'] for f in location['frames'])
            line_ticks[chain] += row['ticks']
        run['coarse_group_ticks'] = dict(groups)
        run['inline_chain_ticks'] = dict(line_ticks)
    recurring = []
    for address, mapping in names.items():
        hits = {name: sum(row['ticks'] for row in run['bins'] if row['midpoint'] == address)
                for name, run in per_run.items()}
        hits = {name: count for name, count in hits.items() if count}
        if len(hits) >= 2:
            recurring.append({'address': address, 'address_hex': hex(address), 'run_ticks': hits,
                              'coarse_group': mapping['coarse_group']})
    recurring.sort(key=lambda x: (-len(x['run_ticks']), -sum(x['run_ticks'].values())))
    report = {'profile_binary_sha256': actual,
              'decoded_sha256': hashlib.sha256(args.decoded.read_bytes()).hexdigest(),
              'method': 'Existing histogram midpoints + addr2line -i -f -C; coarse source-range grouping, no new benchmark runs.',
              'limitations': 'Optimized DWARF and 4-byte histogram bins do not prove line-local costs. Inline chains and compiler discriminators are retained.',
              'runs': per_run, 'address_maps': list(names.values()), 'recurring_addresses': recurring}
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    for name, run in per_run.items():
        print(name, 'HCE ticks=', run['hce_ticks'], 'groups=', run['coarse_group_ticks'])
    print('unique HCE bins', len(names), 'recurring bins', len(recurring))


if __name__ == '__main__':
    main()
