#!/usr/bin/env python3
"""Strict, original integer-literal audit of Forge's supplied H256 networks.

Only parses generated data. Never executes include text or reads engine code.
All bounds are conservative superset bounds, not attainable-position claims.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

INPUTS = 768
HIDDEN = 256
SCALE = 4096
BINARY32_EXACT_INTEGER = 1 << 24
INT32_MAX = (1 << 31) - 1


def array(text, name, length):
    matches = list(re.finditer(r"static\s+const\s+std::int16_t\s+" + re.escape(name) + r"\[(\d+)\]\s*=\s*\{([^}]*)\}\s*;", text, re.S))
    if len(matches) != 1:
        raise ValueError(f"{name}: exactly one int16 literal array required")
    match = matches[0]
    if int(match.group(1)) != length:
        raise ValueError(f"{name}: wrong declared length")
    body = match.group(2)
    parts = body.split(',')
    if parts and not parts[-1].strip():
        parts.pop()
    if len(parts) != length or any(not re.fullmatch(r"\s*[+-]?\d+\s*", p) for p in parts):
        raise ValueError(f"{name}: integer literal count or syntax mismatch")
    result = [int(p) for p in parts]
    if any(not -32768 <= value <= 32767 for value in result):
        raise ValueError(f"{name}: out of int16 storage range")
    return result


def audit(path):
    data = path.read_bytes()
    text = data.decode('ascii')
    for required in [r"InputCount\s*==\s*768", r"HiddenSize\s*==\s*256", r"WeightScale\s*==\s*4096\.0F", r"OutputScale\s*==\s*4096\.0F"]:
        if not re.search(required, text):
            raise ValueError(f"{path.name}: unrecognized shape/scale")
    w1 = array(text, 'NnueW1', INPUTS * HIDDEN)
    b1 = array(text, 'NnueB1', HIDDEN)
    w2 = array(text, 'NnueW2', 2 * HIDDEN)
    b2 = re.findall(r"static\s+const\s+std::int16_t\s+NnueB2\s*=\s*([+-]?\d+)\s*;", text)
    if len(b2) != 1 or not -32768 <= int(b2[0]) <= 32767:
        raise ValueError('NnueB2: one int16 literal required')
    lanes = []
    for h in range(HIDDEN):
        column = w1[h::HIDDEN]
        negative = sorted(v for v in column if v < 0)
        positive = sorted((v for v in column if v > 0), reverse=True)
        sorted_absolute = sorted(map(abs, column), reverse=True)
        maximum_weight = max(map(abs, column))
        # Subsets of up to k distinct inputs; these also bound every refresh
        # prefix because a legal refresh cannot repeat a feature.
        bounds = {str(k): [b1[h] + sum(negative[:k]), b1[h] + sum(positive[:k])] for k in (32, 64, 768)}
        # Stronger than a legal-position bound: even all 768 inputs plus a
        # DirtyPieces batch's four add/sub operations fit these magnitudes.
        full_absolute_plus_dirty4 = abs(b1[h]) + sum(sorted_absolute) + 4 * maximum_weight
        top32_absolute_plus_dirty4 = abs(b1[h]) + sum(sorted_absolute[:32]) + 4 * maximum_weight
        lanes.append({'lane': h, 'bias': b1[h], 'refresh_prefix_bounds_q': bounds,
                      'max_abs_weight': maximum_weight,
                      'top32_absolute_plus_dirty4_q': top32_absolute_plus_dirty4,
                      'full768_absolute_plus_dirty4_q': full_absolute_plus_dirty4})
    full = max(row['full768_absolute_plus_dirty4_q'] for row in lanes)
    summary = {'file': path.name, 'bytes': len(data), 'md5': hashlib.md5(data).hexdigest(),
               'sha256': hashlib.sha256(data).hexdigest(),
               'shape': [INPUTS, HIDDEN], 'scale': SCALE,
               'weight1_range': [min(w1), max(w1)], 'bias1_range': [min(b1), max(b1)],
               'output_weight_range': [min(w2), max(w2)], 'output_bias': int(b2[0]),
               'refresh_prefix32_q': [min(row['refresh_prefix_bounds_q']['32'][0] for row in lanes), max(row['refresh_prefix_bounds_q']['32'][1] for row in lanes)],
               'refresh_prefix64_q': [min(row['refresh_prefix_bounds_q']['64'][0] for row in lanes), max(row['refresh_prefix_bounds_q']['64'][1] for row in lanes)],
               'top32_absolute_plus_dirty4_q': max(row['top32_absolute_plus_dirty4_q'] for row in lanes),
               'full768_absolute_plus_dirty4_q': full,
               'below_binary32_exact_grid': full < BINARY32_EXACT_INTEGER,
               'below_int32_limit': full <= INT32_MAX,
               'int16_bound_insufficient': max(row['top32_absolute_plus_dirty4_q'] for row in lanes) > 32767,
               'per_lane': lanes}
    assert summary['below_binary32_exact_grid'] and summary['below_int32_limit']
    return summary


def run(args):
    netdir = Path(args.nets)
    manifest = (netdir / 'NETS_MANIFEST_13_forge_nets_20261025.md').read_text()
    entries = []
    for line in manifest.splitlines():
        if line.startswith('| ') and '.inc' in line:
            fields = [field.strip() for field in line.split('|')[1:-1]]
            if len(fields) != 5:
                raise ValueError('Unexpected manifest row')
            label, filename, md5, sha256, length = fields
            row = audit(netdir / filename)
            assert (row['md5'], row['sha256'], row['bytes']) == (md5, sha256, int(length)), filename
            row['net'] = label
            entries.append(row)
    assert len(entries) == 13 and len({row['sha256'] for row in entries}) == 13
    result = {'status': 'PASS', 'source': 'User-supplied Forge network literals only; original audit arithmetic',
              'assumptions': ['IEEE754 binary32, round-to-nearest; unchanged WeightScale4096',
                              'Original integer network entries; no requantization or changed output association',
                              'Distinct feature inputs on refresh; DirtyPieces count at most4',
                              'Each refresh prefix has <=32 features on legal chess boards, <=64 on arbitrary occupied boards',
                              'full768 absolute sum +4 max|weight| bounds every lane even without chess piece-count restrictions'],
              'proof_scope': ['int32 addition/subtraction intermediates do not overflow for stated inputs',
                              'binary32 q/4096 accumulation and integer-q conversion/division are exact under the bound',
                              'No proof of arbitrary foreign network, invalid dirty stream, other rounding modes or output layer bit-exactness'],
              'net_manifest_sha256': hashlib.sha256((netdir/'NETS_MANIFEST_13_forge_nets_20261025.md').read_bytes()).hexdigest(),
              'nets': entries}
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    jsonpath = out / 'forge_sol_accumulator_bounds_20261025.json'
    with jsonpath.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    table = ['# Forge Job A independently recomputed accumulator bounds — 20261025\n',
             'Each range is a conservative possible-prefix superset in integer q units (real=q/4096), not an observed or attainable range. All13 manifest hashes match. No speed or strength claim.\n',
             '| Net | q min32 | q max32 | q min64 | q max64 | abs top32+4dirty | abs all768+4dirty | int32 / float exact-grid |\n',
             '|---|---:|---:|---:|---:|---:|---:|---|\n']
    for row in entries:
        table.append(f"| {row['net']} | {row['refresh_prefix32_q'][0]} | {row['refresh_prefix32_q'][1]} | {row['refresh_prefix64_q'][0]} | {row['refresh_prefix64_q'][1]} | {row['top32_absolute_plus_dirty4_q']} | {row['full768_absolute_plus_dirty4_q']} | PASS / PASS |\n")
    table.append('\nAll full768+dirty4 bounds are below2^24=16777216 and int32_max=2147483647. A refresh-only AVX2 int32 path that converts q to float then divides by4096 exactly can feed the unchanged float output layer without loss. This does not justify output requantization. True int16 accumulators are excluded. Existing float accumulators need not be changed.\n')
    with (out/'forge_sol_accumulator_bounds_20261025.md').open('x') as stream:
        stream.write(''.join(table))
    hashes = []
    for path in sorted(out.glob('forge_sol_accumulator_bounds_20261025.*')):
        hashes.append(hashlib.sha256(path.read_bytes()).hexdigest()+'  '+path.name+'\n')
    with (out/'forge_sol_accumulator_bounds_sha256_20261025.txt').open('x') as stream:
        stream.writelines(hashes)
    print(''.join(table))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--nets', required=True)
    parser.add_argument('--output', required=True)
    run(parser.parse_args())
