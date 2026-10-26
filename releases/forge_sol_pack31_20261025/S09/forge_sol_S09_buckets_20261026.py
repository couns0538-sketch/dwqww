"""Step-1-compatible one-to-eight output-head converter; float inference unchanged."""
import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re

STEP1_SHA256 = '39ec705a93fed1cb80773fc37ea4a2dfe20008c628fcd38b462620c1c112b6b0'
_path = Path(__file__).with_name('make_heads_inc.py')
if hashlib.sha256(_path.read_bytes()).hexdigest() != STEP1_SHA256:
    raise ValueError('unchanged CR-passed step-1 converter dependency hash mismatch')
_spec = importlib.util.spec_from_file_location('forge_s09_step1', _path)
step1 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(step1)
# Keep the pinned parser source unchanged while its open(...).read() consumes
# a managed in-memory text stream, so no filesystem descriptor is leaked.
step1.open = lambda path: io.StringIO(Path(path).read_text(encoding='ascii'))
F006_RECIPE = {'shape': 256, 'buckets': 1, 'batch_size': 8192, 'lr': 0.000707,
               'warmup_steps': 300, 'blend_end': 0.6, 'seed': 25, 'epochs': 48, 'residual': True}


def _head_directives(text):
    result = []
    for match in re.finditer(r'^[ \t]*#[ \t]*define[ \t]+FORGE_NNUE_OUTPUT_(?:HEADS|BUCKETS)\b[^\n]*(?:\n|$)', text, re.M):
        line = re.sub(r'/\*[^\n]*?\*/', '', match.group()).split('//', 1)[0].strip()
        value = re.fullmatch(r'#[ \t]*define[ \t]+FORGE_NNUE_OUTPUT_(?:HEADS|BUCKETS)[ \t]+(\d+)', line)
        if not value: raise ValueError('output head directive must be a literal 1 or 8')
        result.append((match.start(), match.end(), int(value.group(1))))
    return result


def output_head(piece_count):
    return min(7, max(0, (piece_count - 1) // 4))


def evaluate_numeric(codes, stm, net):
    """NumPy float32 reference only; this does not execute the native engine.

    Feature layout and the fixed 16-lane association follow the preserved
    step-1 contract. Integer arrays describe storage; accumulators stay float32.
    """
    import numpy as np
    codes, stm = np.asarray(codes), np.asarray(stm)
    if codes.ndim != 2 or codes.shape[1] != 64 or stm.shape != (len(codes),):
        raise ValueError('codes must be N*64 with one STM per row')
    if np.any((codes < 0) | (codes > 12)) or np.any((stm != 0) & (stm != 1)):
        raise ValueError('invalid piece/STM values')
    hidden = net['hidden']; count = len(codes)
    w1 = np.asarray(net['w1'], dtype=np.float32).reshape(768, hidden) / np.float32(4096)
    b1 = np.asarray(net['b1'], dtype=np.float32) / np.float32(4096)
    w2 = np.asarray(net['w2'], dtype=np.float32).reshape(net['heads'], 2 * hidden) / np.float32(4096)
    b2 = np.asarray(net['b2'], dtype=np.float32) / np.float32(4096)
    accumulators = []
    for perspective in (stm, 1 - stm):
        acc = np.broadcast_to(b1, (count, hidden)).copy()
        for square in range(64):
            mask = codes[:, square] != 0
            piece = codes[mask, square].astype(np.int32) - 1
            color, typ = piece // 6, piece % 6
            rel = (color != perspective[mask]).astype(np.int32)
            rsq = np.where(perspective[mask] == 1, square ^ 56, square)
            feature = (rel * 6 + typ) * 64 + rsq
            acc[mask] += w1[feature]
        accumulators.append(np.clip(acc, np.float32(0), np.float32(1)))
    heads = np.zeros(count, dtype=np.int64) if net['heads'] == 1 else np.clip((np.count_nonzero(codes, axis=1) - 1) // 4, 0, 7)
    selected = w2[heads]; lanes = np.zeros((count, 16), dtype=np.float32)
    ours, theirs = accumulators
    for begin in range(0, hidden, 16):
        end = min(begin + 16, hidden); width = end - begin
        a, b = ours[:, begin:end], theirs[:, begin:end]
        term = (a * a) * selected[:, begin:end] + (b * b) * selected[:, hidden + begin:hidden + end]
        lanes[:, :width] += term
    logits = b2[heads].copy()
    for lane in range(16): logits += lanes[:, lane]
    cp_float = (logits * np.float32(400)) / np.float32(2.25)
    cp = np.trunc(np.clip(cp_float, np.float32(-30000), np.float32(30000))).astype(np.int32)
    return {'logits': logits, 'cp': cp, 'heads': heads}


def inspect_inc(path, hidden=256):
    try: text, arrays, scalar, head_def = step1.parse(str(path))
    except (SystemExit, KeyError, TypeError) as error: raise ValueError('invalid step-1 include: ' + str(error)) from error
    required = {'NnueW1', 'NnueB1', 'NnueW2'}
    if not required <= set(arrays): raise ValueError('missing required NNUE array')
    declarations = re.findall(r'static const std::int16_t (NnueW1|NnueB1|NnueW2|NnueB2)(?:\[|\s*=)', text)
    if any(declarations.count(name) != 1 for name in required | {'NnueB2'}):
        raise ValueError('each NNUE array/bias must have one declaration')
    definitions = _head_directives(text)
    heads = definitions[0][2] if definitions else 1
    if heads not in (1, 8) or any(value != heads for _, _, value in definitions):
        raise ValueError('output head defines must consistently declare 1 or 8')
    h = len(arrays['NnueB1'][2]); b2 = arrays['NnueB2'][2] if 'NnueB2' in arrays else [int(scalar.group(1))] if scalar else []
    w1, b1, w2 = [arrays[name][2] for name in ('NnueW1', 'NnueB1', 'NnueW2')]
    if not h or (hidden is not None and h != hidden) or len(w1) != 768 * h or len(w2) != heads * 2 * h or len(b2) != heads:
        raise ValueError('NNUE shape does not match input768/hidden/heads')
    if any(not -32768 <= value <= 32767 for values in (w1, b1, w2, b2) for value in values):
        raise ValueError('NNUE storage value outside signed int16 range')
    return {'hidden': h, 'heads': heads, 'w1': w1, 'b1': b1, 'w2': w2, 'b2': b2}


def replicate_1_to_8(source, destination, hidden=256):
    source, destination = Path(source), Path(destination)
    if destination.exists() or source.resolve() == destination.resolve():
        raise FileExistsError('destination must be a new file, separate from the input')
    if any(part.rstrip(' .').casefold() in {'lock', 'locks', 'baseline', '.git'} or part.rstrip(' .').casefold().startswith('dist-v')
           for part in str(destination.resolve()).replace('\\', '/').split('/')):
        raise ValueError('protected output path')
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    net = inspect_inc(source, hidden)
    if net['heads'] != 1: raise ValueError('converter requires a one-head net')
    text, arrays, scalar, _ = step1.parse(str(source))
    start, end, _ = arrays['NnueW2']
    replacements = [(start, end, step1.fmt('NnueW2', net['w2'] * 8))]
    if 'NnueB2' in arrays:
        start, end, _ = arrays['NnueB2']
    else: start, end = scalar.span()
    replacements.append((start, end, step1.fmt('NnueB2', net['b2'] * 8, 8)))
    definitions = _head_directives(text)
    for index, (start, end, _) in enumerate(definitions):
        replacements.append((start, end, '#define FORGE_NNUE_OUTPUT_HEADS 8\n' if index == 0 else ''))
    if not definitions:
        anchor = re.search(r'^#define FORGE_NNUE_RESIDUAL[^\n]*\n', text, re.M)
        position = anchor.end() if anchor else 0
        replacements.append((position, position, '#define FORGE_NNUE_OUTPUT_HEADS 8\n'))
    for start, end, replacement in sorted(replacements, reverse=True): text = text[:start] + replacement + text[end:]
    if hashlib.sha256(source.read_bytes()).hexdigest() != before: raise ValueError('source changed during conversion')
    with destination.open('x', encoding='ascii', newline='\n') as stream: stream.write(text)
    converted = inspect_inc(destination, hidden)
    if converted['w1'] != net['w1'] or converted['b1'] != net['b1'] or converted['w2'] != net['w2'] * 8 or converted['b2'] != net['b2'] * 8:
        raise ValueError('conversion roundtrip validation failed')
    if hashlib.sha256(source.read_bytes()).hexdigest() != before: raise ValueError('source changed after conversion')
    return {'heads': 8, 'hidden': net['hidden'], 'source_sha256': before,
            'output_sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
            'feature_weights_unchanged': True, 'all_heads_identical': True,
            'inference': 'FLOAT_UNCHANGED; int16 is existing include storage only'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['replicate', 'check', 'recipe'])
    parser.add_argument('source', nargs='?', type=Path); parser.add_argument('destination', nargs='?', type=Path)
    parser.add_argument('--hidden', type=int, default=256)
    args = parser.parse_args()
    if args.command == 'recipe': result = F006_RECIPE
    elif args.command == 'check':
        result = inspect_inc(args.source, args.hidden); result = {k: v for k, v in result.items() if k in ('hidden', 'heads')}
    else: result = replicate_1_to_8(args.source, args.destination, args.hidden)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__': main()
