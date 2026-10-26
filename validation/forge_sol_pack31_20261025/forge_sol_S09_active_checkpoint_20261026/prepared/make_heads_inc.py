#!/usr/bin/env python3
"""Forge NNUE output-head include tool (buckets8). Stdlib only.

  make_heads_inc.py replicate SRC.inc DST.inc
      Legacy single-head include -> 8-head include whose 8 heads are exact
      copies of the source head. W1/B1 text is copied unchanged.
  make_heads_inc.py check INC [--hidden N]
      Validate an include against the layout in README_BUCKETS8.md and
      report heads, sizes and which heads are identical.
  make_heads_inc.py control SRC.inc DST.inc
      TEST ONLY: replicate, then add (head+1)*64 to head k's bias (int16),
      so each head gives a different eval. Used by the parity harness to
      prove the head is really selected by piece count. Never ship it.

Layout (head-major): NnueW2[8 * 2 * H] = head0[stm H | opp H], head1[...], ...
NnueB2[8]. Bucket of a position = output_head(pieces incl. kings) =
clamp((pieces - 1) >> 2, 0, 7).
"""
import re, sys

HEADS = 8

def parse(path):
    text = open(path).read()
    arrays = {}
    for m in re.finditer(r'static const std::int16_t (Nnue\w+)\[(\d+)\] = \{(.*?)\};', text, re.S):
        vals = [int(v) for v in m.group(3).replace('\n', ' ').split(',') if v.strip()]
        if len(vals) != int(m.group(2)):
            sys.exit(f'{path}: {m.group(1)} declares {m.group(2)} values, has {len(vals)}')
        arrays[m.group(1)] = (m.start(), m.end(), vals)
    scalar = re.search(r'static const std::int16_t NnueB2 = (-?\d+);', text)
    heads_def = re.search(r'#define FORGE_NNUE_OUTPUT_(?:HEADS|BUCKETS) (\d+)', text)
    return text, arrays, scalar, heads_def

def fmt(name, vals, per_line=24):
    rows = [', '.join(str(v) for v in vals[i:i + per_line]) for i in range(0, len(vals), per_line)]
    return f'static const std::int16_t {name}[{len(vals)}] = {{\n  ' + ',\n  '.join(rows) + ',\n};'

def replicate(src, dst, bias_step=0):
    text, arrays, scalar, heads_def = parse(src)
    if heads_def or scalar is None or 'NnueB2' in arrays:
        sys.exit(f'{src}: not a legacy single-head include')
    s, e, w2 = arrays['NnueW2']
    b2 = int(scalar.group(1))
    new_w2 = w2 * HEADS
    new_b2 = [b2 + (k + 1) * bias_step for k in range(HEADS)]
    if any(not -32768 <= v <= 32767 for v in new_b2):
        sys.exit('bias out of int16 range')
    out = text[:s] + fmt('NnueW2', new_w2) + text[e:scalar.start()] + fmt('NnueB2', new_b2, HEADS) + text[scalar.end():]
    tag = '#define FORGE_NNUE_OUTPUT_HEADS 8\n'
    note = ('// buckets8: 8 output heads (head-major NnueW2/NnueB2), made by tools/nnue/make_heads_inc.py\n'
            f'// {"CONTROL (TEST ONLY): head k bias += (k+1)*%d" % bias_step if bias_step else "replicate"} from {src.split("/")[-1]}\n')
    out = note + out
    anchor = '#define FORGE_NNUE_RESIDUAL'
    i = out.find(anchor)
    i = out.find('\n', i) + 1 if i >= 0 else out.find('\n', out.find('#include <cstdint>')) + 1
    out = out[:i] + tag + out[i:]
    open(dst, 'w').write(out)
    print(f'wrote {dst}: heads {HEADS}, W2 {len(new_w2)}, B2 {new_b2}')

def check(path, hidden=None):
    text, arrays, scalar, heads_def = parse(path)
    w1 = arrays['NnueW1'][2]; b1 = arrays['NnueB1'][2]; w2 = arrays['NnueW2'][2]
    h = len(b1)
    if hidden and h != hidden: sys.exit(f'FAIL hidden {h} != {hidden}')
    if len(w1) != 768 * h: sys.exit(f'FAIL W1 {len(w1)} != 768*{h}')
    heads = int(heads_def.group(1)) if heads_def else 1
    b2 = arrays['NnueB2'][2] if 'NnueB2' in arrays else [int(scalar.group(1))]
    if len(w2) != heads * 2 * h or len(b2) != heads:
        sys.exit(f'FAIL heads {heads}: W2 {len(w2)} (want {heads*2*h}), B2 {len(b2)} (want {heads})')
    if heads not in (1, HEADS): sys.exit(f'FAIL heads {heads} not 1 or {HEADS}')
    blocks = [tuple(w2[k * 2 * h:(k + 1) * 2 * h]) + (b2[k],) for k in range(heads)]
    same = [k for k in range(heads) if blocks[k] == blocks[0]]
    resid = re.search(r'#define FORGE_NNUE_RESIDUAL (\d)', text)
    print(f'OK {path}: hidden {h}, heads {heads}, residual {resid.group(1) if resid else 0}, '
          f'heads identical to head0: {same}, B2 {b2}')

if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) == 3 and a[0] == 'replicate': replicate(a[1], a[2])
    elif len(a) == 3 and a[0] == 'control': replicate(a[1], a[2], bias_step=64)
    elif len(a) >= 2 and a[0] == 'check': check(a[1], int(a[3]) if len(a) == 4 and a[2] == '--hidden' else None)
    else: sys.exit(__doc__)
