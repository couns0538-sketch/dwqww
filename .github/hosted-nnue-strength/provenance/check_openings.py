import hashlib
import io
import json
import subprocess
import zipfile
from collections import Counter
from pathlib import Path

import chess
import chess.pgn

ROOT = Path('/workspace/.cloud-setup/strength-openings-research-20261019')
REPO = Path('/workspace/dwqww')
SEED = '20261019-official-stockfish-8moves-v3-long-strength-v1'

def sha(data):
    return hashlib.sha256(data).hexdigest()

archive_path = ROOT / '8moves_v3.pgn.zip'
archive = archive_path.read_bytes()
assert sha(archive) == '7e1e9dd118b4bb97d8a8b5b8a790c86e21f8509d59a27d2883767d94477be02e'
assert hashlib.sha1(('blob ' + str(len(archive)) + '\0').encode() + archive).hexdigest() == '572bcf2eff104c51c64e796313f0589ce97e7044'
with zipfile.ZipFile(io.BytesIO(archive)) as z:
    members = z.infolist()
    assert sum(m.file_size for m in members) <= 32 * 1024 * 1024
    pgn_members = [m for m in members if m.filename.endswith('.pgn')]
    assert len(pgn_members) == 1
    member = pgn_members[0]
    pgn = z.read(member)
(ROOT / '8moves_v3.pgn').write_bytes(pgn)

excluded = set()
registries = []
for path in sorted(Path('/workspace').rglob('*.epd')):
    if path.name == 'forge-10000.epd' or '/fastchess/' in str(path) or ROOT in path.parents:
        continue
    raw = path.read_bytes()
    positions = set()
    for line in raw.decode().splitlines():
        if not line.strip():
            continue
        fields = line.split()[:4]
        assert len(fields) == 4, str(path)
        # Historical equivalence check only. Candidate PGN positions are never
        # rewritten or accepted after clearing an en-passant target.
        board = chess.Board(' '.join(fields) + ' 0 1')
        positions.add(' '.join(fields))
        positions.add(' '.join(board.fen(en_passant='legal').split()[:4]))
    excluded.update(positions)
    registries.append({'path': str(path), 'sha256': sha(raw), 'nonempty_rows': sum(bool(x.strip()) for x in raw.decode().splitlines()),
                       'exact_or_historical_legal_ep_unique': len(positions)})

confirmation = json.loads((REPO / '.github/hosted-confirmation/provenance/openings-selection.json').read_text())
confirmation_fens = {item['fen'] for phase in confirmation['selections'].values() for item in phase}
assert len(confirmation_fens) == 164 and confirmation_fens <= excluded
excluded.update(confirmation['exclusions']['canonical_positions'])

handle = io.StringIO(pgn.decode('utf-8-sig'))
stats = Counter()
depths = Counter()
eligible = {}
all_positions = set()
ep_dash_unique = set()
headers_first = None
while True:
    game = chess.pgn.read_game(handle)
    if game is None:
        break
    stats['games'] += 1
    if headers_first is None:
        headers_first = dict(game.headers)
    assert not game.errors, (stats['games'], game.errors)
    assert not game.headers.get('FEN') and game.headers.get('Variant', 'Standard') == 'Standard'
    board = game.board()
    plies = 0
    for move in game.mainline_moves():
        assert board.is_legal(move), stats['games']
        board.push(move)
        plies += 1
    depths[plies] += 1
    assert board.is_valid() and board.legal_moves.count() > 0, stats['games']
    # PGN carries moves rather than FEN. Use strict FEN EP semantics and require
    # no actual last-double-push EP square; never use the default EP normalization.
    fen = ' '.join(board.fen(en_passant='fen').split()[:4])
    all_positions.add(fen)
    if board.ep_square is not None:
        stats['non_dash_ep_games_skipped'] += 1
        continue
    assert fen.split()[3] == '-'
    stats['ep_dash_games'] += 1
    ep_dash_unique.add(fen)
    if fen in excluded:
        stats['prior_overlap_games'] += 1
        continue
    eligible.setdefault(fen, stats['games'])

ranked = sorted(eligible, key=lambda fen: hashlib.sha256((SEED + '\n' + fen).encode()).digest())
assert len(ranked) >= 1028
selected = ranked[:1028]
assert len(set(selected)) == 1028 and not set(selected) & excluded
selection_outputs = {}
for phase, fens in {'aa': selected[:4], 'sprt': selected[4:]}.items():
    payload = ('\n'.join(fens) + '\n').encode()
    path = ROOT / ('prospective-' + phase + '.epd')
    path.write_bytes(payload)
    selection_outputs[phase] = {'path': str(path), 'sha256': sha(payload), 'positions': len(fens)}

report = {
    'source': {'repository': 'https://github.com/official-stockfish/books',
               'head': subprocess.check_output(['git', '-C', str(ROOT / 'books'), 'rev-parse', 'HEAD'], text=True).strip(),
               'path': '8moves_v3.pgn.zip', 'file_blob': '572bcf2eff104c51c64e796313f0589ce97e7044',
               'pinned_url': 'https://raw.githubusercontent.com/official-stockfish/books/a804a97e709f40aa75a00f9d19e84915b7a3a45c/8moves_v3.pgn.zip',
               'archive_bytes': len(archive), 'archive_sha256': sha(archive), 'zip_member': member.filename,
               'pgn_bytes': len(pgn), 'pgn_sha256': sha(pgn), 'pgn_newline_count': pgn.count(b'\n'),
               'license': 'CC0-1.0, upstream root LICENSE', 'license_sha256': sha((ROOT / 'LICENSE-upstream').read_bytes()),
               'attribution': 'Stockfish developers, official-stockfish/books; upstream README and LICENSE retained; no individual author identified in README.'},
    'python_chess_version': chess.__version__, 'statistics': dict(stats), 'depths': dict(depths),
    'unique_four_field_positions': len(all_positions), 'ep_dash_unique': len(ep_dash_unique),
    'eligible_unique_after_all_exclusions': len(eligible), 'prior_overlap_ep_dash_unique': len(ep_dash_unique & excluded),
    'exclusion_registry_files': len(registries), 'excluded_exact_or_legal_ep_historical_keys': len(excluded),
    'new_164_confirmation_selection_explicitly_excluded': True, 'registries': registries,
    'first_pgn_headers': headers_first,
    'prospective_selection': {'state': 'INPUT_PREREQUISITE_ONLY_NO_MATCH_AUTHORIZED_OR_LAUNCHED', 'seed': SEED,
        'ranking': 'Ascending SHA256(UTF-8 seed + LF + exact strict-FEN first four fields); retain first source game for duplicates.',
        'eligibility': 'Standard game; every mainline move legal; valid final position with legal moves; final actual EP square absent before serialization; unique first-four-field FEN; exclude all recorded historical registries including frozen unused tails and new164selection; no engine evaluation.',
        'allocation': 'First4 AA, following1024 serial SPRT opening pairs; all1028positions reserved together, no outcome-based reselection.',
        'outputs': selection_outputs,
        'selections': [{'source_game_1based': eligible[fen], 'fen': fen, 'ranking_sha256': sha((SEED + '\n' + fen).encode())} for fen in selected]},
    'limitations': 'Standard opening suite at 16 plies, not an automatically balanced set. First upstream PGN headers identify Stockfish versus Stockfish dated2013.11.02; no human-opening-distribution claim. No engine evaluation or outcome filtering; equal-color pairs required. Exact future engines/clocks/protocol remain to be preregistered.'
}
(ROOT / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: report[k] for k in ['source', 'statistics', 'depths', 'unique_four_field_positions', 'ep_dash_unique', 'eligible_unique_after_all_exclusions', 'prior_overlap_ep_dash_unique', 'exclusion_registry_files']}, indent=2))
