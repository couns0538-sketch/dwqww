#!/usr/bin/env python3
"""Freeze unused original-corpus openings without an engine or network."""
import datetime
import hashlib
import json
import sys
from pathlib import Path

REPO = Path('/workspace/dwqww')
OUT = (Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / '.github/hosted-confirmation').resolve()
CORPUS = REPO / 'tools/openings/forge-10000.epd'
SEED = '20261019-hosted-confirmation-160-v1'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def parse(line):
    fields = line.split()
    if len(fields) < 4:
        raise ValueError('EPD requires four FEN fields')
    return fields[:4]

def position(fields):
    board = {}
    for rank, text in zip(range(7, -1, -1), fields[0].split('/')):
        file = 0
        for char in text:
            if char.isdigit():
                file += int(char)
            else:
                board[(file, rank)] = char
                file += 1
        assert file == 8
    return board

def attacked(board, target, by):
    for (file, rank), piece in board.items():
        if piece.isupper() != (by == 'w'):
            continue
        dx, dy = target[0] - file, target[1] - rank
        kind = piece.lower()
        if kind == 'p' and abs(dx) == 1 and dy == (1 if by == 'w' else -1):
            return True
        if kind == 'n' and sorted((abs(dx), abs(dy))) == [1, 2]:
            return True
        if kind == 'k' and max(abs(dx), abs(dy)) == 1:
            return True
        diagonal = abs(dx) == abs(dy) and dx != 0
        straight = (dx == 0) != (dy == 0)
        if not ((kind in 'bq' and diagonal) or (kind in 'rq' and straight)):
            continue
        sx, sy = (dx > 0) - (dx < 0), (dy > 0) - (dy < 0)
        square = (file + sx, rank + sy)
        while square != target and square not in board:
            square = (square[0] + sx, square[1] + sy)
        if square == target:
            return True
    return False

def legal_ep(fields):
    if fields[3] == '-':
        return False
    board = position(fields)
    side = fields[1]
    up = 1 if side == 'w' else -1
    own_pawn, enemy_pawn, own_king = ('P', 'p', 'K') if side == 'w' else ('p', 'P', 'k')
    target = (ord(fields[3][0]) - ord('a'), int(fields[3][1]) - 1)
    captured = (target[0], target[1] - up)
    if target in board or board.get(captured) != enemy_pawn:
        return False
    king = next(square for square, piece in board.items() if piece == own_king)
    for dx in (-1, 1):
        origin = (target[0] + dx, target[1] - up)
        if board.get(origin) != own_pawn:
            continue
        after = dict(board)
        del after[origin]
        del after[captured]
        after[target] = own_pawn
        if not attacked(after, king, 'b' if side == 'w' else 'w'):
            return True
    return False

def canonical(fields):
    fields = list(fields)
    fields[2] = ''.join(right for right in 'KQkq' if right in fields[2]) or '-'
    if fields[3] != '-' and not legal_ep(fields):
        fields[3] = '-'
    return ' '.join(fields)

def lines(path):
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]

excluded = set()
registries = []
for path in sorted(Path('/workspace').rglob('*.epd')):
    if path.name == 'forge-10000.epd' or OUT in path.parents or '/fastchess/' in str(path):
        continue
    raw = lines(path)
    normalized = {canonical(parse(line)) for line in raw}
    excluded.update(normalized)
    registries.append({'path': str(path), 'sha256': sha(path.read_bytes()), 'lines': len(raw),
                       'canonical_unique': len(normalized),
                       'ep_fields_removed': sum(parse(line)[3] != '-' and canonical(parse(line)).split()[3] == '-' for line in raw)})

raw_corpus = lines(CORPUS)
eligible = {}
ep_skipped = 0
excluded_rows = 0
for index, line in enumerate(raw_corpus, 1):
    fields = parse(line)
    if fields[3] != '-':
        ep_skipped += 1
        continue
    key = canonical(fields)
    if key in excluded:
        excluded_rows += 1
        continue
    eligible.setdefault(key, index)

ranked = sorted(eligible, key=lambda fen: hashlib.sha256((SEED + '\n' + fen).encode()).digest())
assert len(ranked) >= 164
selected = ranked[:164]
assert len(set(selected)) == 164 and not (set(selected) & excluded)
phases = {'aa': selected[:4], 'sprt': selected[4:]}
files = {}
for phase, fens in phases.items():
    path = OUT / 'openings' / (phase + '.epd')
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = ('\n'.join(fens) + '\n').encode()
    with path.open('xb') as output:
        output.write(payload)
    files[str(path.relative_to(OUT))] = {'sha256': sha(payload), 'positions': len(fens)}

record = {
    'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'seed': SEED,
    'method': 'Ascending SHA256 of UTF-8 seed + LF + canonical first-four-field FEN; first4 AA, following160 SPRT; no screening, reset, resume or pooling.',
    'eligibility': 'Original corpus EP field must be -; original board/side/rights retained; no evaluator screening.',
    'canonicalization': 'Rights ordered KQkq. Historical EP target removed only if no side-to-move pawn can legally capture it after EP occupancy change and king-safety attack test. Legal EP targets retained.',
    'exclusion_scope': 'Every workspace .epd except full forge-10000.epd corpus copies, pinned Fastchess self-test fixtures, and this output directory. Includes all validation selections and portable6.4.2 AA/pilot/SPRT/prior-selected registries; unused tails excluded.',
    'corpus': {'path': str(CORPUS), 'sha256': sha(CORPUS.read_bytes()), 'positions': len(raw_corpus),
               'non_dash_ep_rows_skipped': ep_skipped, 'excluded_eligible_rows': excluded_rows,
               'eligible_unique_remaining': len(eligible)},
    'exclusions': {'registry_files': len(registries), 'raw_rows': sum(row['lines'] for row in registries),
                   'canonical_unique': len(excluded), 'registries': registries,
                   'canonical_positions': sorted(excluded)},
    'outputs': files,
    'selections': {phase: [{'source_line': eligible[fen], 'fen': fen, 'fen_sha256': sha(fen.encode()),
                           'ranking_sha256': sha((SEED + '\n' + fen).encode())} for fen in fens]
                   for phase, fens in phases.items()},
    'limitations': 'Synthetic quiet-development corpus; not a representative human opening distribution. No new engine-based opening validation or strength claim.'
}
manifest = OUT / 'provenance/openings-selection.json'
manifest.parent.mkdir(parents=True, exist_ok=True)
with manifest.open('x') as output:
    json.dump(record, output, indent=2)
    output.write('\n')
hash_paths = [OUT / relative for relative in files] + [manifest, Path(__file__)]
with (OUT / 'provenance/openings-SHA256SUMS').open('x') as output:
    for path in hash_paths:
        output.write(sha(path.read_bytes()) + '  ' + str(path.relative_to(OUT)) + '\n')
print(json.dumps({'outputs': files, 'corpus': record['corpus'],
                  'exclusions': {key: value for key, value in record['exclusions'].items() if key not in ('registries', 'canonical_positions')},
                  'manifest_sha256': sha(manifest.read_bytes())}, indent=2))
