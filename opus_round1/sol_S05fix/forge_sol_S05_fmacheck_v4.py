#!/usr/bin/env python3
"""FMA-free and NNUE-output check of a Forge executable or object (S05 v4).

v4 fix (S05-1) over Sol's forge_sol_S05_fmacheck_v3_20261025.py (17aa0cae, unchanged):
- the fused-multiply-add scan covers the WHOLE .text section (every function, not only forge::nnue:: symbols)
  and every other executable section objdump disassembles (.init, .plt, .fini on ELF);
- ``fma_count`` is computed from that scan (v3 printed the literal 0 and raised on the first scoped hit);
- the whole-binary count is printed: ``FMA_COUNT whole_text=N whole_binary=M nnue_scoped=K`` on stdout,
  then one JSON line with the counts, per-section counts and the first fused instructions found.
The run FAILS (exit 1) if any fused instruction is found anywhere, or (unless --fma-only) if the NNUE output
contract of v3 is not met (unchanged v3 logic: 256-bit min/mul/add plus a max or a proven masked zero clamp in the
public or outlined forge::nnue evaluate body). Counted mnemonics: the FMA3/FMA4/AVX-512 families
v[4]f[n]m{add,sub}* (incl. fmaddsub/fmsubadd) and the AVX512-FP16 complex FMAs vf[c]maddc*.

usage: forge_sol_S05_fmacheck_v4.py BINARY [--objdump PATH] [--fma-only]
       forge_sol_S05_fmacheck_v4.py --disassembly SAVED_OBJDUMP_TEXT [--fma-only]   (fixtures / replays)
"""
from __future__ import annotations
import argparse
import json
import re
import subprocess
import sys

HEADER = re.compile(r'^\s*[0-9a-fA-F]+ <(.+)>:\s*$')
SECTION = re.compile(r'^Disassembly of section (\S+):\s*$')
FUSED = re.compile(r'^(?:v4?fn?m(?:add|sub)|vfc?maddc)[a-z0-9]*\b', re.I)
CMP = re.compile(r'^vcmp([a-z_]*)ps\s+(?:\$(0x[0-9a-f]+|\d+),)?%ymm(\d+),%ymm(\d+),%k([0-7])$')
ZERO = re.compile(r'^(?:vxorps|vpxor|vpxord|vpxorq)\s+%[xy]mm(\d+),%[xy]mm\1,%[xy]mm\1$')
ZERO_COPY = re.compile(r'^vmov(?:a|u)ps\s+%ymm(\d+),%ymm(\d+)$')
NNUE_PREFIX = 'forge::nnue::'
DEFAULT_SECTION = '.text'  # a listing without a section header is treated as .text (fixtures)
MAX_LISTED = 50


def instruction(line):
    m = re.match(r'^\s*[0-9a-fA-F]+:\s+(.+)$', line)
    if not m:
        return None
    value = re.sub(r'^(?:[0-9a-fA-F]{2}\s+)+', '', m.group(1))
    return re.sub(r'^\{evex\}\s*', '', value.split('#', 1)[0].strip())


def scan(lines):
    """One pass: whole-binary fused counts by section, plus forge::nnue:: symbol bodies for the v3 contract."""
    section, symbol = DEFAULT_SECTION, None
    by_section, scanned, listed, nnue_fused = {}, 0, [], 0
    nnue_rows, current = [], None
    for line in lines:
        line = line.rstrip('\r\n')
        m = SECTION.match(line)
        if m:
            section, symbol, current = m.group(1), None, None
            by_section.setdefault(section, {'instructions': 0, 'fused': 0})
            continue
        header = HEADER.match(line)
        if header:
            symbol = header.group(1)
            current = None
            if symbol.startswith(NNUE_PREFIX):
                current = {'name': symbol, 'instructions': []}
                nnue_rows.append(current)
            continue
        ins = instruction(line)
        if not ins:
            continue
        counts = by_section.setdefault(section, {'instructions': 0, 'fused': 0})
        counts['instructions'] += 1
        scanned += 1
        if current is not None:
            current['instructions'].append(ins)
        if FUSED.match(ins):
            counts['fused'] += 1
            if current is not None:
                nnue_fused += 1
            if len(listed) < MAX_LISTED:
                listed.append({'section': section, 'symbol': symbol, 'instruction': ins})
    return by_section, scanned, listed, nnue_fused, nnue_rows


# ---- v3 NNUE output contract, unchanged ----
def vector_destination(ins):
    fields = ins.split(None, 1)
    if len(fields) != 2:
        return None
    m = re.fullmatch(r'%[xyz]mm(\d+)(?:\{.*)?', fields[1].rsplit(',', 1)[-1])
    return m.group(1) if m else None


def update_zeroes(known, ins):
    dest = vector_destination(ins)
    if dest is not None:
        copy = ZERO_COPY.fullmatch(ins)
        if ZERO.fullmatch(ins) or (copy and copy.group(1) in known):
            known.add(dest)
        else:
            known.discard(dest)


def mask_clamp(insns):
    zeroes = set()
    for index, ins in enumerate(insns):
        if re.match(r'^(?:callq?|retq?|j[a-z]+)\b', ins):
            zeroes.clear()
        match = CMP.fullmatch(ins)
        if match:
            pred, imm, zero, value, mask = match.groups()
            valid_predicate = ((pred in {'gt', 'gt_os', 'gt_oq', 'nle', 'nle_us', 'nle_uq'} and imm is None) if pred
                               else (imm is not None and int(imm, 0) in {6, 14, 22, 30}))
            if valid_predicate and mask != '0' and zero in zeroes and value not in zeroes:
                live_zeroes = set(zeroes)
                for after in insns[index + 1:]:
                    if re.search(r',%k' + mask + r'$', after):
                        break
                    source = after.rsplit(',', 1)[0]
                    uses_value = bool(re.search(r'%ymm' + value + r'(?!\d)', source))
                    if uses_value and '{%k' + mask + '}{z}' in after:
                        return 'mask-zero'
                    blend = re.fullmatch(r'vblendmps\s+%ymm(\d+),%ymm(\d+),%ymm\d+\{%k' + mask + r'\}', after)
                    if blend and blend.group(1) == value and blend.group(2) in live_zeroes:
                        return 'mask-blend'
                    if vector_destination(after) in (value, zero):
                        break
                    if re.match(r'^(?:callq?|retq?|j[a-z]+)\b', after):
                        break
                    update_zeroes(live_zeroes, after)
        update_zeroes(zeroes, ins)
    return None


def output_contract(insns):
    for op in ('vminps', 'vmulps', 'vaddps'):
        if not any(re.match(r'^' + op + r'\b', ins) and '%ymm' in ins for ins in insns):
            return None
    if any(re.match(r'^vmaxps\b', ins) and '%ymm' in ins for ins in insns):
        return 'vmaxps'
    return mask_clamp(insns)


def check(lines, fma_only=False):
    by_section, scanned, listed, nnue_fused, rows = scan(lines)
    whole_text = by_section.get('.text', {}).get('fused', 0)
    whole_binary = sum(v['fused'] for v in by_section.values())
    problems = []
    if scanned == 0:
        problems.append('no instructions disassembled')
    if whole_binary:
        problems.append(f'{whole_binary} fused multiply-add instruction(s) in the binary '
                        f'({whole_text} in .text, {nnue_fused} in forge::nnue::)')
    result = {'checker_version': 4, 'fma_count': whole_text, 'fma_count_whole_text': whole_text,
              'fma_count_whole_binary': whole_binary, 'fma_count_nnue_scoped': nnue_fused,
              'fma_by_section': {k: v['fused'] for k, v in sorted(by_section.items())},
              'instructions_by_section': {k: v['instructions'] for k, v in sorted(by_section.items())},
              'instructions_scanned': scanned, 'fused_listed': listed,
              'fused_listed_truncated': whole_binary > len(listed),
              'scope': 'every instruction in every section objdump -d disassembles (PE: .text; ELF: .init/.plt/'
                       '.text/.fini); NNUE output contract on forge::nnue:: symbol bodies (v3 logic)'}
    if fma_only:
        result['nnue_contract'] = 'skipped (--fma-only)'
    else:
        public = [r for r in rows if r['name'].startswith('forge::nnue::evaluate(')]
        output = [r for r in rows if re.match(r'^forge::nnue::(?:\(anonymous namespace\)::)?evaluate(?:_values)?\(',
                                              r['name'])]
        qualified = [{'symbol': r['name'], 'clamp': clamp} for r in output if (clamp := output_contract(r['instructions']))]
        result['nnue_symbols_scanned'] = [r['name'] for r in rows]
        result['qualified_output'] = qualified
        if not public:
            problems.append('public NNUE evaluate symbol not found (stripped binary? use --fma-only for counts only)')
        elif not qualified:
            problems.append('NNUE output lacks 256-bit clamp/min/multiply/add in public or outlined evaluate body')
        result['nnue_contract'] = 'PASS' if public and qualified else 'FAIL'
    result['problems'] = problems
    result['status'] = 'FAIL' if problems else 'PASS'
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('object', nargs='?', help='executable or object file (unstripped for the NNUE contract)')
    p.add_argument('--objdump', default='objdump')
    p.add_argument('--disassembly', help='read a saved `objdump -d -C --no-show-raw-insn` listing instead')
    p.add_argument('--fma-only', action='store_true', help='counts only; skip the NNUE output contract')
    args = p.parse_args()
    if bool(args.object) == bool(args.disassembly):
        p.error('give exactly one of BINARY or --disassembly')
    if args.disassembly:
        with open(args.disassembly, encoding='utf-8', errors='strict') as f:
            result = check(f, args.fma_only)
    else:
        proc = subprocess.Popen([args.objdump, '-d', '-C', '--no-show-raw-insn', args.object],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8',
                                errors='replace')
        result = check(proc.stdout, args.fma_only)
        stderr = proc.stderr.read()
        if proc.wait() != 0:
            raise ValueError(f'objdump failed with exit {proc.returncode}: {stderr.strip()[-500:]}')
    print(f"FMA_COUNT whole_text={result['fma_count_whole_text']} whole_binary={result['fma_count_whole_binary']} "
          f"nnue_scoped={result['fma_count_nnue_scoped']} instructions={result['instructions_scanned']} "
          f"nnue_contract={result['nnue_contract']} status={result['status']}")
    print(json.dumps(result, sort_keys=True))
    if result['problems']:
        print('FAIL: ' + '; '.join(result['problems']), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError) as exc:
        print('FAIL: ' + str(exc), file=sys.stderr)
        sys.exit(1)
