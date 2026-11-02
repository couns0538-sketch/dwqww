"""Opt-in full-FEN/provenance binding for Forge REC32 and FPOS1 sidecars.

Original R10 glue; no trainer or engine implementation is copied. UNPROVEN.
Binary formats cannot authenticate absent game IDs or recover lost FEN fields.
The caller must pin the returned manifest hash independently.
"""
from __future__ import annotations
import hashlib
import itertools
import json
import mmap
import os
from pathlib import Path
import re
import struct
import chess

SCHEMA = 'forge-full-state-v1'


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def identity(path):
    path = Path(path).resolve(strict=True)
    return dict(path=str(path), bytes=path.stat().st_size, sha256=sha256(path))


def _json(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode('utf8')


def _binary_rows(path, binary_format):
    with Path(path).open('rb') as stream:
        size = os.fstat(stream.fileno()).st_size
        if binary_format == 'rec32':
            if size % 32:
                raise ValueError('REC32 byte count is not a multiple of 32')
            while row := stream.read(32):
                yield row
        elif binary_format == 'fpos1':
            header = stream.read(16)
            if len(header) != 16:
                raise ValueError('FPOS1 header truncated')
            magic, version, count = struct.unpack('<4sIQ', header)
            if magic != b'FPOS' or version != 1 or size != 16 + 35 * count:
                raise ValueError('FPOS1 format/size/count mismatch')
            with mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
                for index in range(count):
                    yield (data[16+32*index:16+32*(index+1)] +
                           data[16+32*count+2*index:16+32*count+2*(index+1)] +
                           data[16+34*count+index:17+34*count+index])
        else:
            raise ValueError('unsupported binary format')


def _check_features(raw, binary_format, row):
    fen = row.get('fen')
    if not isinstance(fen, str) or len(fen.split()) != 6:
        raise ValueError('original six-field FEN required')
    board = chess.Board(fen)
    if not board.is_valid():
        raise ValueError('invalid full-FEN chess position')
    game_id = row.get('game_id')
    if game_id is not None and (not isinstance(game_id, str) or not game_id.strip()):
        raise ValueError('game_id must be an authentic nonempty string or null')
    stm = int(not board.turn)
    if binary_format == 'fpos1':
        if struct.unpack('<h', raw[32:34])[0] == -32768:
            raise ValueError('FPOS1 score -32768 is reserved/invalid')
        expected = bytearray(32)
        for square, piece in board.piece_map().items():
            code = piece.piece_type + (0 if piece.color else 6)
            expected[square//2] |= code << (4*(square % 2))
        if raw[:32] != expected or not 0 <= raw[34] <= 5 or (raw[34] & 1) != stm:
            raise ValueError('full FEN does not match FPOS1 board/STM')
    else:
        nibble = []
        for square in chess.SquareSet(board.occupied):
            piece = board.piece_at(square)
            nibble.append(piece.piece_type - 1 + (0 if piece.color else 8))
        nibble += [0] * (32-len(nibble))
        pieces = bytes(nibble[2*i] | nibble[2*i+1] << 4 for i in range(16))
        castle = (int(board.has_kingside_castling_rights(chess.WHITE)) |
                  int(board.has_queenside_castling_rights(chess.WHITE)) << 1 |
                  int(board.has_kingside_castling_rights(chess.BLACK)) << 2 |
                  int(board.has_queenside_castling_rights(chess.BLACK)) << 3)
        ep = board.ep_square if board.ep_square is not None else 255
        if (raw[:8] != int(board.occupied).to_bytes(8, 'little') or raw[8:24] != pieces or
                raw[24] != stm or raw[25] != castle or raw[28] != ep):
            raise ValueError('full FEN does not match REC32 board/STM/castling/EP')


def write_state(binary, rows, manifest, *, binary_format, sources=(), state_origin='original_full_fen'):
    """Seal an aligned sidecar, then its manifest; never replace existing files.

    Rows retain all supplied provenance. In particular no game ID is derived from
    a row number, filename, FEN or shard name. None means unknown, not clearance.
    """
    if state_origin != 'original_full_fen':
        raise ValueError('state binding requires original full FEN; reconstructed state is not original')
    manifest = Path(manifest)
    metadata = manifest.with_name(manifest.name+'.rows.jsonl')
    pending = manifest.with_name(manifest.name+'.pending')
    if any(path.exists() or path.is_symlink() for path in (manifest, metadata, pending)):
        raise FileExistsError('state output already exists')
    binary_before = identity(binary)
    source_before = [identity(path) for path in sources]
    sentinel = object()
    count = missing = 0
    with metadata.open('xb') as stream:
        for index, (raw, row) in enumerate(itertools.zip_longest(_binary_rows(binary, binary_format), rows, fillvalue=sentinel)):
            if raw is sentinel or row is sentinel:
                raise ValueError('binary/metadata row count mismatch')
            _check_features(raw, binary_format, row)
            entry = dict(index=index, record_sha256=hashlib.sha256(raw).hexdigest(), metadata=row)
            stream.write(_json(entry))
            count += 1
            missing += row.get('game_id') is None
        stream.flush(); os.fsync(stream.fileno())
    if binary_before != identity(binary) or source_before != [identity(path) for path in sources]:
        raise ValueError('input changed while creating state binding')
    meta_id = identity(metadata)
    meta_id['path'] = metadata.name
    result = dict(schema=SCHEMA, binary_format=binary_format, binary=binary_before,
                  metadata=meta_id, rows=count, missing_game_ids=missing,
                  game_id_status='UNVERIFIED' if missing else 'SUPPLIED_NOT_INDEPENDENTLY_AUTHENTICATED',
                  state_origin=state_origin, sources=source_before, claim='UNPROVEN')
    with pending.open('xb') as stream:
        stream.write(_json(result)); stream.flush(); os.fsync(stream.fileno())
    os.link(pending, manifest)
    return result


def verify_state(manifest, expected_sha256, binary):
    """Verify every row and every file hash before returning any metadata."""
    manifest = Path(manifest)
    if not isinstance(expected_sha256, str) or not re.fullmatch('[0-9a-fA-F]{64}', expected_sha256):
        raise ValueError('an independently pinned state-manifest SHA256 is required')
    manifest_target = manifest.resolve(strict=True)
    manifest_bytes = manifest.read_bytes()
    if hashlib.sha256(manifest_bytes).hexdigest() != expected_sha256.lower():
        raise ValueError('state manifest SHA256 mismatch')
    receipt = json.loads(manifest_bytes)
    if receipt.get('schema') != SCHEMA or receipt.get('state_origin') != 'original_full_fen':
        raise ValueError('unsupported state manifest schema/origin')
    observed = identity(binary)
    if any(observed[key] != receipt['binary'][key] for key in ('bytes','sha256')):
        raise ValueError('state binary SHA256/size mismatch')
    name = receipt['metadata']['path']
    if (not isinstance(name, str) or Path(name).name != name or name in ('.','..') or
            any(character in name for character in '/\\:\0') or name.endswith((' ','.'))):
        raise ValueError('state metadata path must be a local filename')
    metadata = manifest.parent/name
    observed_metadata = identity(metadata)
    if any(observed_metadata[key] != receipt['metadata'][key] for key in ('bytes','sha256')):
        raise ValueError('state metadata SHA256/size mismatch')
    for source in receipt['sources']:
        if identity(source['path']) != source:
            raise ValueError('state original source changed')
    rows = []
    sentinel = object()
    consumed_hash = hashlib.sha256()
    consumed_bytes = 0
    with metadata.open('rb') as stream:
        for index, (raw, line) in enumerate(itertools.zip_longest(_binary_rows(binary, receipt['binary_format']), stream, fillvalue=sentinel)):
            if raw is sentinel or line is sentinel:
                raise ValueError('binary/metadata row count mismatch')
            consumed_hash.update(line)
            consumed_bytes += len(line)
            entry = json.loads(line)
            if type(entry.get('index')) is not int or entry['index'] != index or entry.get('record_sha256') != hashlib.sha256(raw).hexdigest():
                raise ValueError('state row index/record SHA256 mismatch')
            _check_features(raw, receipt['binary_format'], entry['metadata'])
            rows.append(entry['metadata'])
    if (consumed_hash.hexdigest() != receipt['metadata']['sha256'] or
            consumed_bytes != receipt['metadata']['bytes']):
        raise ValueError('state consumed metadata SHA256/size mismatch')
    if type(receipt.get('rows')) is not int or len(rows) != receipt['rows']:
        raise ValueError('state manifest row count mismatch')
    if sum(row.get('game_id') is None for row in rows) != receipt.get('missing_game_ids'):
        raise ValueError('state missing-game-ID count mismatch')
    if (manifest.resolve(strict=True) != manifest_target or
            sha256(manifest) != expected_sha256.lower() or
            identity(binary) != observed or identity(metadata) != observed_metadata or
            any(identity(source['path']) != source for source in receipt['sources'])):
        raise ValueError('state input identity changed during verification')
    return rows
