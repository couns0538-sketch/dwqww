#!/usr/bin/env python3
"""Attribute every linked FMA and optionally require real AVX-512 NNUE code."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess

HEADER = re.compile(r'^([0-9a-fA-F]+) <(.+)>:$')
INSTRUCTION = re.compile(r'^\s*([0-9a-fA-F]+):\s+(?:[0-9a-fA-F]{2}\s+)+([a-zA-Z][a-zA-Z0-9_.]*)\s*(.*)$')
ZMM = re.compile(r'%zmm\d+\b')
FMA_PREFIXES = ('vfmadd', 'vfnmadd', 'vfmsub', 'vfnmsub')
NNUE_APIS = ('refresh', 'update', 'evaluate')


def is_forge_symbol(symbol):
    # Symbol ownership comes only from a raw, anchored objdump header. A
    # template argument, similarly named namespace or operand is not ownership.
    return bool(re.match(r'^(?:(?:non-virtual|virtual|covariant return) thunk to |transaction clone for )?forge::', symbol))


def scan_disassembly(lines):
    symbols = []
    current = None
    fma_hits = []
    for line in lines:
        line = line.rstrip('\n')
        header = HEADER.fullmatch(line)
        if header:
            current = {'address': header.group(1), 'name': header.group(2),
                       'instructions': 0, 'zmm_instructions': 0, 'zmm_mnemonics': {}}
            symbols.append(current)
            continue
        if line.startswith('Disassembly of section '):
            current = None
            continue
        instruction = INSTRUCTION.match(line)
        if not instruction:
            continue
        address, mnemonic, operands = instruction.groups()
        if current is not None:
            current['instructions'] += 1
            if ZMM.search(operands):
                current['zmm_instructions'] += 1
                counts = current['zmm_mnemonics']
                counts[mnemonic] = counts.get(mnemonic, 0) + 1
        if mnemonic.startswith(FMA_PREFIXES):
            fma_hits.append({'symbol': current['name'] if current else None,
                             'symbol_address': current['address'] if current else None,
                             'address': address, 'mnemonic': mnemonic,
                             'operands': operands, 'raw': line})
    return {'symbols': symbols, 'fma_hits': fma_hits,
            'forge_fma': [h for h in fma_hits if h['symbol'] and is_forge_symbol(h['symbol'])],
            'nonforge_fma': [h for h in fma_hits if h['symbol'] and not is_forge_symbol(h['symbol'])],
            'unattributed_fma': [h for h in fma_hits if h['symbol'] is None]}


def file_sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def audit_binary(binary, output, require_zmm, objdump):
    initial_hash = file_sha256(binary)
    raw = output / (binary.name + '.objdump.txt')
    stderr = output / (binary.name + '.objdump.stderr')
    command = [objdump, '-Cd', str(binary)]
    with raw.open('w') as stdout, stderr.open('w') as errors:
        process = subprocess.run(command, stdout=stdout, stderr=errors)
    if process.returncode:
        raise RuntimeError('objdump failed for ' + str(binary) + ': ' + stderr.read_text())
    with raw.open() as stream:
        result = scan_disassembly(stream)
    failures = []
    if not result['symbols']:
        failures.append('no raw symbol headers found')
    if result['forge_fma']:
        failures.append('fused arithmetic appears in forge:: symbols')
    if result['unattributed_fma']:
        failures.append('fused arithmetic appears without a symbol owner')
    nnue = {}
    for api in NNUE_APIS:
        matching = [s for s in result['symbols'] if s['name'].startswith('forge::nnue::' + api + '(')
                    and ' [clone ' not in s['name']]
        nnue[api] = matching
        if require_zmm and (len(matching) != 1 or matching[0]['zmm_instructions'] == 0):
            failures.append(api + ' lacks one actual public symbol with ZMM instructions')
    if require_zmm and nnue['evaluate']:
        mnemonics = nnue['evaluate'][0]['zmm_mnemonics']
        for instruction in ('vminps', 'vmaxps', 'vmulps', 'vaddps'):
            if instruction not in mnemonics:
                failures.append('evaluate lacks ZMM ' + instruction)
    final_hash = file_sha256(binary)
    if initial_hash != final_hash:
        failures.append('executable changed while disassembling')
    receipt = {'binary': str(binary), 'sha256_before': initial_hash, 'sha256_after': final_hash,
               'objdump_command': command, 'objdump_returncode': process.returncode,
               'raw_disassembly': str(raw), 'raw_sha256': file_sha256(raw),
               'require_zmm': require_zmm, 'symbol_count': len(result['symbols']),
               'instruction_count': sum(s['instructions'] for s in result['symbols']),
               'fma_total': len(result['fma_hits']),
               'forge_fma_count': len(result['forge_fma']),
               'unattributed_fma_count': len(result['unattributed_fma']),
               'fma_by_exact_symbol': dict(sorted(Counter(h['symbol'] for h in result['fma_hits'] if h['symbol']).items())),
               'fma_hits': result['fma_hits'], 'nnue': nnue, 'failures': failures}
    (output / (binary.name + '.receipt.json')).write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binaries', nargs='+', type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--require-zmm', action='append', default=[], type=Path,
                        help='Binary path that must contain ZMM in all three actual NNUE APIs')
    parser.add_argument('--objdump', default='objdump')
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    required = {p.resolve() for p in args.require_zmm}
    binaries = [p.resolve() for p in args.binaries]
    if required - set(binaries):
        parser.error('--require-zmm paths must also appear in binaries')
    if len({p.name for p in binaries}) != len(binaries):
        parser.error('binary basenames must be unique within one audit')
    version = subprocess.run([args.objdump, '--version'], capture_output=True, text=True, check=True).stdout.splitlines()[0]
    receipts = []
    for binary in binaries:  # Sequential disassembly keeps the audit at one CPU.
        receipt = audit_binary(binary, args.output_dir, binary in required, args.objdump)
        receipts.append(receipt)
        print(binary.name + ': ' + ('FAIL' if receipt['failures'] else 'PASS') +
              ', total FMA=' + str(receipt['fma_total']) +
              ', forge:: FMA=' + str(receipt['forge_fma_count']) +
              ', unattributed FMA=' + str(receipt['unattributed_fma_count']))
        for symbol, count in receipt['fma_by_exact_symbol'].items():
            print('  ' + str(count) + ' ' + symbol)
        for api, symbols in receipt['nnue'].items():
            for symbol in symbols:
                print('  ' + api + ' ZMM=' + str(symbol['zmm_instructions']) + ' @' + symbol['address'])
        for failure in receipt['failures']:
            print('  FAIL: ' + failure)
    (args.output_dir / 'summary.json').write_text(json.dumps({'objdump_version': version, 'receipts': receipts}, indent=2) + '\n')
    return int(any(r['failures'] for r in receipts))


if __name__ == '__main__':
    raise SystemExit(main())
