#!/usr/bin/env python3
"""Audit frozen openings without engines or a new full-corpus legal replay.

The authoritative cache retains the original 34,700-game legal replay. This
checker replays only the 516 newly selected original games; all other games are
visited with skip_game. It writes only its explicitly requested audit report.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import zipfile

import chess
import chess.pgn


REPO = Path(__file__).resolve().parents[2]
PACKAGE = REPO / '.github/hosted-tt-refresh-strength'
SEED = '20261021-tt-refresh-v1'
RUNTIME_SEED = 20261101
COUNTS = {'aa': 4, 'sprt': 512}
TOTAL = sum(COUNTS.values())
BOOK_SHA = '7e1e9dd118b4bb97d8a8b5b8a790c86e21f8509d59a27d2883767d94477be02e'
CACHE_SHA = '42735af2eb7ef9a43695de69b256e519075e3a30ef6a565febcabf0abd2bdcff'
PGN_SHA = '5835239f88cc2c7511b177c32392a69f3ede21819cf0616f80a7f907cd21d17e'
COHORT_COUNTS = {
    'hosted-nnue-strength': 1028,
    'hosted-tt-strength': 1028,
    'hosted-pin-see-strength': 132,
    'hosted-pin-mask-strength': 132,
    'hosted-promotion-see-strength': 132,
    'hosted-correction-history-strength':260,
    'hosted-pv-metadata-strength':516,
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    observed = {}
    payloads = {}

    def read(path, expected=None):
        path = Path(path).resolve(strict=True)
        if path not in payloads:
            payloads[path] = path.read_bytes()
            observed[path] = sha(payloads[path])
        if expected is not None:
            require(observed[path] == expected, 'Input SHA mismatch: ' + str(path))
        return payloads[path]

    def document(path, expected=None):
        return json.loads(read(path, expected))

    marker = document(PACKAGE / 'provenance/reservation-frozen.json')
    require(marker['selector_seed'] == SEED and marker['runtime_seed'] == RUNTIME_SEED,
            'Reservation seeds differ from the new preregistered cohort')
    require(marker.get('engine_executions') == 0, 'Reservation must not execute engines')
    require(marker.get('full_corpus_replays_this_preparation') == 0,
            'This preparation must reuse the existing verified corpus cache')
    selection = document(PACKAGE / 'provenance/openings-selection.json', marker['selection_sha256'])
    source = selection['source']
    require(source['head'] == 'a804a97e709f40aa75a00f9d19e84915b7a3a45c', 'Official book source pin changed')
    require(source['archive_sha256'] == BOOK_SHA and source['pgn_sha256'] == PGN_SHA,
            'Official book bytes changed')
    cacheinfo = selection['book_legal_cache']
    require(cacheinfo['sha256'] == marker['book_cache_sha256'] == CACHE_SHA,
            'Verified corpus cache SHA changed')
    cacheraw = read(REPO / cacheinfo['path'], CACHE_SHA)
    cache = json.loads(cacheraw)
    require(cache['source'] == source, 'Cache/source provenance mismatch')
    require(cache['cache_key_archive_sha256'] == cacheinfo['key'] == BOOK_SHA,
            'Cache is not keyed by the original archive SHA')
    require(cache['status'] == 'FULL_LEGAL_REPLAY_COMPLETE', 'Original cache was not fully replayed')
    require(cache['statistics'] == {'games': 34700, 'strict_ep_none': 31603, 'actual_ep_excluded': 3097},
            'Cache corpus counts changed')
    require(cache['engine_executions'] == 0 and cacheinfo['full_corpus_replays_this_preparation'] == 0,
            'Unexpected engine execution or new full corpus replay')
    require(read(REPO / cacheinfo['origin_path']) == cacheraw, 'Cache differs from its retained origin')
    generator_sha = sha(read(REPO / cacheinfo['origin_generator_path']))
    require(generator_sha == cacheinfo['origin_generator_sha256'] == cache['generator_sha256'],
            'Original full-replay generator differs')
    originproof = document(REPO / cacheinfo['origin_full_replay_proof_path'],
                           cacheinfo['origin_full_replay_proof_sha256'])
    require(originproof['status'] == 'passed' and originproof['book_cache_full_legal_replay'] == 34700
            and originproof['book_cache_sha256'] == CACHE_SHA, 'Original full-replay proof mismatch')
    document(REPO / cacheinfo['origin_selection_path'], cacheinfo['origin_selection_sha256'])
    positions = cache['positions']
    require(len(positions) == len(set(positions.values())) == 31603, 'Cache position/index uniqueness failed')
    require(all(type(index) is int and 1 <= index <= 34700 for index in positions.values()),
            'Cache source-game index is invalid')
    require(all(len(fen.split()) == 4 and fen.split()[3] == '-' for fen in positions),
            'Cache must retain exact strict four-field EP-none positions')

    exclusion = document(PACKAGE / 'provenance/historical-exclusions.json',
                         selection['historical_exclusions_sha256'])
    excluded = set(exclusion['excluded_canonical_positions'])
    historical_sources = exclusion['historical_sources_sha256']
    historical_paths = set()
    for relative, digest in historical_sources.items():
        path = (REPO / relative).resolve(strict=True)
        read(path, digest)
        historical_paths.add(path)
    original = document(REPO / '.github/hosted-tt-strength/provenance/openings-selection.json')
    require(len(original['registries']) == 42, 'Original registry cohort changed')
    registry_paths = set()
    for row in original['registries']:
        path = Path(row['path']).resolve(strict=True)
        read(path, row['sha256'])
        registry_paths.add(path)
    require(registry_paths <= historical_paths, 'Original registry missing from frozen exclusion inventory')

    key_cache = {}

    def historical_keys(fen):
        fen = ' '.join(fen.split()[:4])
        if fen not in key_cache:
            require(len(fen.split()) == 4, 'Malformed historical FEN key')
            board = chess.Board(fen + ' 0 1')
            key_cache[fen] = {fen, ' '.join(board.fen(en_passant='legal').split()[:4])}
        return key_cache[fen]

    reconstructed = set()
    registry_paths |= {path for path in historical_paths if path.suffix == '.epd'}
    for path in sorted(registry_paths, key=lambda item: item.as_posix()):
        for line in read(path).decode().splitlines():
            if line.strip() and not line.lstrip().startswith('#'):
                reconstructed.update(historical_keys(line))
    require(reconstructed <= excluded, 'Historical first-four-field/EP-equivalent position was omitted')

    for name in ['hosted-confirmation', *COHORT_COUNTS]:
        path = REPO / '.github' / name / 'provenance/openings-selection.json'
        prior = document(path)
        cohort = {row['fen'] for row in prior.get('prospective_selection', {}).get('selections', [])}
        for rows in prior.get('selections', {}).values():
            cohort.update(row['fen'] for row in rows)
        cohort.update(prior.get('exclusions', {}).get('canonical_positions', []))
        frozen = exclusion['reserved_cohorts'][name]
        require(set(frozen['canonical_positions']) == cohort and frozen['reserved_positions'] == len(cohort),
                'Reserved cohort contents/count mismatch: ' + name)
        if name in COHORT_COUNTS:
            require(len(cohort) == COHORT_COUNTS[name], 'Full reserved pool not retained: ' + name)
        for fen in cohort:
            require(historical_keys(fen) <= excluded, 'Reserved cohort position missing: ' + name)
        require(path.resolve(strict=True) in historical_paths, 'Reserved selection missing from source inventory: ' + name)

    # Check any EPD files added since the frozen inventory without modifying the
    # reservation. Additional copies are harmless only when every key is excluded.
    current = subprocess.check_output(['rg', '--files', '--hidden', '--no-ignore', '-g', '*.epd',
                                       '-g', '!.git/**'], cwd=REPO, text=True).splitlines()
    extra_registries = 0
    for relative in current:
        path = (REPO / relative).resolve(strict=True)
        if PACKAGE.resolve() in path.parents or path in registry_paths:
            continue
        extra_registries += 1
        for line in read(path).decode().splitlines():
            if line.strip() and not line.lstrip().startswith('#'):
                require(historical_keys(line) <= excluded, 'Unexcluded position in current EPD registry: ' + relative)

    eligible = {fen: index for fen, index in positions.items() if fen not in excluded}
    require(len(eligible) == selection['eligible_unique'], 'Eligible position count differs')
    chosen = selection['prospective_selection']
    ranked = sorted(eligible, key=lambda fen: hashlib.sha256((SEED + '\n' + fen).encode('ascii')).digest())[:TOTAL]
    require(chosen['seed'] == SEED and [row['fen'] for row in chosen['selections']] == ranked,
            'Prospective positions differ from independent deterministic ranking')
    require(len(set(ranked)) == TOTAL and not set(ranked) & excluded, 'Selected pool is not fresh and unique')
    require(all(eligible[row['fen']] == row['source_game_1based'] for row in chosen['selections']),
            'Selected original game index differs')
    runtime = document(PACKAGE / 'provenance/runtime-order.json')
    start = 0
    for phase, count in COUNTS.items():
        fens = ranked[start:start + count]
        start += count
        raw = ('\n'.join(fens) + '\n').encode('ascii')
        require(read(PACKAGE / 'openings' / (phase + '.epd'), chosen['outputs'][phase]['sha256']) == raw,
                'Selector pool bytes differ: ' + phase)
        require(chosen['outputs'][phase]['positions'] == count, 'Selector pool count differs: ' + phase)
        ordered = sorted(fens, key=lambda fen: hashlib.sha256((str(RUNTIME_SEED) + '\n' + fen).encode('ascii')).digest())
        ordered_raw = ('\n'.join(ordered) + '\n').encode('ascii')
        require(runtime[phase]['seed'] == RUNTIME_SEED and runtime[phase]['ordered_fens'] == ordered,
                'Frozen runtime order/seed differs: ' + phase)
        require(sha(ordered_raw) == runtime[phase]['selected_epd_sha256'], 'Runtime selection hash differs: ' + phase)
        require(read(PACKAGE / 'provenance' / ('runtime-' + phase + '.epd')) == ordered_raw,
                'Runtime EPD bytes differ: ' + phase)

    archive = read(PACKAGE / 'provenance/8moves_v3.pgn.zip', BOOK_SHA)
    with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
        pgn = zipped.read(source['zip_member'])
    require(sha(pgn) == PGN_SHA, 'Original PGN member changed')
    stream = io.StringIO(pgn.decode('utf-8-sig'))
    wanted = {row['source_game_1based']: row['fen'] for row in chosen['selections']}
    visited = replayed = 0
    while True:
        index = visited + 1
        if index in wanted:
            board = chess.pgn.read_game(stream, Visitor=chess.pgn.BoardBuilder)
            if board is None:
                break
            require(board.ply() == 16 and board.is_valid() and board.legal_moves.count() > 0
                    and board.ep_square is None, 'Selected original game failed legal/strict-EP audit')
            require(' '.join(board.fen(en_passant='fen').split()[:4]) == wanted[index],
                    'Selected original game does not reproduce frozen FEN')
            replayed += 1
        elif not chess.pgn.skip_game(stream):
            break
        visited += 1
    require(visited == 34700 and replayed == TOTAL, 'Original source game visit/selected replay counts differ')
    require(all(sha(path.read_bytes()) == digest for path, digest in observed.items()),
            'Consumed frozen input changed during independent audit')
    result = {
        'status': 'passed', 'book_cache_sha256': CACHE_SHA,
        'book_cache_full_legal_replay': 34700, 'full_corpus_replays_this_preparation': 0,
        'verified_book_cache_reused_byte_exact': True,
        'independent_selected_source_games_legally_replayed': replayed,
        'official_source_games_visited': visited, 'strict_ep_none_cache': 31603,
        'fresh_eligible_after_exclusions': len(eligible),
        'historical_reserved_source_positions_excluded': 31603 - len(eligible),
        'historical_source_hashes_verified': len(historical_sources),
        'historical_canonical_keys_reconstructed': len(reconstructed),
        'current_additional_epd_registries_checked': extra_registries,
        'old42registry_hashes_verified': True,
        'all_historical_keys_and_reserved_cohorts_in_exclusion_snapshot': True,
        'full_reserved_cohorts_excluded': dict(COHORT_COUNTS),
        'fresh_unique_positions': TOTAL, 'frozen_aa_pairs': COUNTS['aa'],
        'frozen_sprt_pairs': COUNTS['sprt'], 'selector_seed': SEED, 'runtime_seed': RUNTIME_SEED,
        'engine_executions': 0, 'frozen_inputs_rewritten': False,
        'consumed_input_files_rehashed': len(observed),
        'checker_sha256': sha(Path(__file__).read_bytes()),
    }
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
