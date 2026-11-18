#!/usr/bin/env python3
"""Verify opening identity when fastchess omits an unusable en-passant target."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess

import chess


FEN_HEADER = re.compile(rb'(?m)^\[FEN "([^"]+)"\]\r?$')


def key(fen):
    return sha256(' '.join(fen.split()[:4]).encode()).hexdigest()


def legal_ep_fen(fen):
    fields = fen.split()
    if len(fields) != 6:
        raise ValueError(f'Expected a six-field FEN, got {fen}')
    if fields[3] == '-':
        return ' '.join(fields)
    board = chess.Board(fen)
    if board.has_legal_en_passant():
        return ' '.join(fields)
    fields[3] = '-'
    return ' '.join(fields)


def canonical_key(fen):
    return key(legal_ep_fen(fen))


def match_fens(raw):
    return {item.decode() for item in FEN_HEADER.findall(raw)}


def checked_read(path, expected):
    data = path.read_bytes()
    if sha256(data).hexdigest() != expected:
        raise ValueError(f'{path}: SHA-256 differs from the pinned receipt')
    return data


def receipt_aliases(path, manifest, manifest_sha):
    proof = json.loads(path.read_bytes())
    if proof['manifest_sha256'] != manifest_sha or proof['overlaps'] != dict(sol_archive=0, job3_replay=0, astra5_archive=0):
        raise ValueError('Canonical opening receipt does not pin a disjoint opening manifest')
    if proof['cells'].keys() != manifest['cells'].keys():
        raise ValueError('Canonical opening receipt has an unexpected match list')
    result, seen = {}, set()
    for name, cell in manifest['cells'].items():
        raw = set(cell['fen_keys_sha256'])
        aliases = {}
        for row in proof['cells'][name]['aliases']:
            before, after = row['epd_fen'], row['canonical_fen']
            source, normalized = key(before), key(after)
            if before == after or after != legal_ep_fen(before) or source not in raw or source in aliases:
                raise ValueError(f'{name}: invalid canonical replacement {row}')
            aliases[source] = normalized
        updated = {aliases.get(value, value) for value in raw}
        if len(updated) != len(raw) or len(updated) != proof['cells'][name]['canonical_count'] or seen & updated:
            raise ValueError(f'{name}: canonical opening keys collide')
        seen.update(updated)
        result[name] = updated
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('history_root', type=Path)
    parser.add_argument('astra_receipt', type=Path)
    parser.add_argument('repo', type=Path)
    args = parser.parse_args()
    raw = args.manifest.read_bytes()
    manifest_sha = sha256(raw).hexdigest()
    manifest = json.loads(raw)
    reserved, cells = set(), {}
    for name, cell in manifest['cells'].items():
        book = args.manifest.parent / cell['file']
        source = checked_read(book, cell['sha256']).decode().splitlines()
        expected = set(cell['fen_keys_sha256'])
        if len(source) != cell['count'] or {key(fen) for fen in source} != expected:
            raise ValueError(f'{book}: original opening keys differ from the frozen manifest')
        aliases, canonical = [], set()
        for fen in source:
            normalized = legal_ep_fen(fen)
            canonical.add(key(normalized))
            if fen != normalized:
                before, after = chess.Board(fen), chess.Board(normalized)
                if set(before.legal_moves) != set(after.legal_moves):
                    raise ValueError(f'{book}: canonical FEN changed the legal move set')
                aliases.append(dict(epd_fen=fen, canonical_fen=normalized))
        if len(canonical) != cell['count'] or reserved & canonical:
            raise ValueError(f'{book}: opening collision after normalization')
        reserved.update(canonical)
        cells[name] = dict(canonical_count=len(canonical), aliases=aliases)

    old_fens = set()
    for entry in manifest['historical']['files']:
        pgndata = checked_read(args.history_root / entry['path'], entry['sha256'])
        old_fens.update(match_fens(pgndata))
    old = {canonical_key(fen) for fen in old_fens}
    starts = {canonical_key(line.split('\t')[1]) for line in (args.history_root / 'job3/games.txt').read_text().splitlines()}
    astra = json.loads(args.astra_receipt.read_bytes())
    foreign_fens = set()
    for cell in astra['rows']:
        specification = f'{astra["astra5_commit"]}:{cell["source"]}.pgn'
        pgn = subprocess.check_output(['git', '-C', str(args.repo), 'show', specification])
        if sha256(pgn).hexdigest() != cell['pgn_sha256']:
            raise ValueError(f'{specification}: foreign PGN hash differs')
        foreign_fens.update(match_fens(pgn))
    foreign = {canonical_key(fen) for fen in foreign_fens}
    overlaps = dict(sol_archive=len(old & reserved), job3_replay=len(starts & reserved), astra5_archive=len(foreign & reserved))
    if any(overlaps.values()):
        raise ValueError(f'Canonical opening overlaps: {overlaps}')
    print(json.dumps(dict(manifest_sha256=manifest_sha, cells=cells, overlaps=overlaps,
                          earlier_pgns=manifest['historical']['pgn_count'], sol_canonical_keys=len(old),
                          job3_canonical_starts=len(starts), astra5_canonical_keys=len(foreign)), indent=2))


if __name__ == '__main__':
    main()
