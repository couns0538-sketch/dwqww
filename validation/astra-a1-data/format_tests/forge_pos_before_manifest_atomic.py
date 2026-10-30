"""Forge FPOS/FHCE v1 I/O, with explicit full-position sidecar validation.

IDEA_SOURCE: same-project Job D format reader/writer and Forge datagen.hpp.
No search or trainer behavior is changed. Binary records do not encode castling,
en passant, clocks or game identities. Reconstruction is explicit and lossy.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import hashlib
import json
import mmap
import os
from pathlib import Path
import re
import shutil
import struct
from typing import Iterable, Iterator

HEADER = struct.Struct('<4sIQ')
PIECES = ' PNBRQKpnbrqk'
RECONSTRUCTION_POLICY = 'no-castling-no-ep-clocks-0-1'


@dataclass(frozen=True)
class Record:
    board: bytes
    score: int
    meta: int
    hce: int | None = None


def validate_record(record: Record, *, require_hce: bool = False) -> None:
    if not isinstance(record.board, bytes) or len(record.board) != 32:
        raise ValueError('record board must be exactly 32 bytes')
    if any((v & 15) > 12 or (v >> 4) > 12 for v in record.board):
        raise ValueError('record contains an invalid piece nibble')
    if type(record.score) is not int or not -32767 <= record.score <= 32767:
        raise ValueError('score must be an integer in [-32767,32767]')
    if type(record.meta) is not int or not 0 <= record.meta <= 5:
        raise ValueError('meta must encode STM and White result in [0,5]')
    if require_hce and record.hce is None:
        raise ValueError('paired writer requires HCE')
    if record.hce is not None and (type(record.hce) is not int or not -32767 <= record.hce <= 32767):
        raise ValueError('HCE must be an integer in [-32767,32767]; -32768 is invalid')


class PosReader:
    """Read-only mapped columns. Header/size checked on open; values on each row."""
    def __init__(self, pos: str | Path, hce: str | Path | None = None):
        self.pos = Path(pos)
        self.hce = Path(hce) if hce is not None else None
        self._files = []
        self._maps = []
        self._closed = False
        try:
            self._pos, self.n = self._open(self.pos, b'FPOS', 35)
            self._hce = None
            if self.hce is not None:
                self._hce, count = self._open(self.hce, b'FHCE', 2)
                if count != self.n:
                    raise ValueError('POS/HCE row-count mismatch')
        except BaseException:
            self.close()
            raise

    def _open(self, path, magic, width):
        f = path.open('rb')
        self._files.append(f)
        head = f.read(HEADER.size)
        if len(head) != HEADER.size:
            raise ValueError(f'truncated header: {path}')
        observed, version, count = HEADER.unpack(head)
        if observed != magic or version != 1:
            raise ValueError(f'unsupported magic/version: {path}')
        if os.fstat(f.fileno()).st_size != HEADER.size + width * count:
            raise ValueError(f'file size/count mismatch: {path}')
        data = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        self._maps.append(data)
        return data, count

    def row(self, i: int) -> Record:
        if self._closed:
            raise ValueError('reader is closed')
        if type(i) is not int or not 0 <= i < self.n:
            raise IndexError(i)
        r = Record(self._pos[16 + 32*i:16 + 32*(i+1)],
                   struct.unpack_from('<h', self._pos, 16 + 32*self.n + 2*i)[0],
                   self._pos[16 + 34*self.n + i],
                   struct.unpack_from('<h', self._hce, 16 + 2*i)[0] if self._hce is not None else None)
        validate_record(r)
        return r

    def __len__(self):
        return self.n

    def __iter__(self):
        for i in range(self.n):
            yield self.row(i)

    def close(self):
        if not self._closed:
            for m in self._maps:
                m.close()
            for f in self._files:
                f.close()
            self._maps.clear()
            self._files.clear()
            self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def _fen_fields(fen: str) -> tuple[bytes, int, str]:
    if not isinstance(fen, str):
        raise ValueError('FEN must be text')
    fields = fen.split()
    if len(fields) != 6 or fields[1] not in ('w', 'b'):
        raise ValueError('full six-field FEN required')
    ranks = fields[0].split('/')
    if len(ranks) != 8:
        raise ValueError('FEN needs eight ranks')
    board = bytearray(32)
    for rank, text in enumerate(reversed(ranks)):
        file = 0
        for char in text:
            if char in '12345678':
                file += int(char)
            elif char in PIECES[1:] and file < 8:
                square = rank * 8 + file
                board[square // 2] |= PIECES.index(char) << (4 * (square % 2))
                file += 1
            else:
                raise ValueError('invalid FEN piece/rank')
            if file > 8:
                raise ValueError('FEN rank overflow')
        if file != 8:
            raise ValueError('FEN rank width is not eight')
    rights = fields[2]
    if rights != '-' and (not re.fullmatch(r'[KQkqA-Ha-h]+', rights) or len(set(rights)) != len(rights)):
        raise ValueError('invalid FEN castling field')
    if fields[3] != '-' and not re.fullmatch(r'[a-h][36]', fields[3]):
        raise ValueError('invalid FEN en-passant field')
    if not re.fullmatch(r'[0-9]+', fields[4]) or not re.fullmatch(r'[0-9]+', fields[5]) or int(fields[5]) < 1:
        raise ValueError('invalid FEN clocks')
    # Structural syntax only. A native Board must validate legal chess state.
    return bytes(board), int(fields[1] == 'b'), ' '.join(fields)


def fen_record(fen: str, score: int, white_result) -> Record:
    board, stm, _ = _fen_fields(fen)
    if isinstance(white_result, bool):
        raise ValueError('White result must be 0, 0.5 or 1, not bool')
    try:
        value = Decimal(str(white_result))
    except (InvalidOperation, ValueError):
        raise ValueError('invalid White result') from None
    if not value.is_finite() or value not in (Decimal(0), Decimal('0.5'), Decimal(1)):
        raise ValueError('White result must be 0, 0.5 or 1')
    result = Record(board, score, stm | (int(value * 2) << 1))
    validate_record(result)
    return result


def text_record(line: str) -> tuple[Record, str]:
    fields = line.strip().split('|')
    if len(fields) != 3 or not re.fullmatch(r'[+-]?[0-9]+', fields[1].strip()):
        raise ValueError('expected FEN | integer STM score | WHITE result')
    fen = ' '.join(fields[0].split())
    return fen_record(fen, int(fields[1].strip()), fields[2].strip()), fen


def match_fen(record: Record, fen: str) -> str:
    validate_record(record)
    board, stm, normalized = _fen_fields(fen)
    if board != record.board or stm != (record.meta & 1):
        raise ValueError('FEN sidecar board/STM mismatch')
    return normalized


def match_text_record(record: Record, line: str) -> str:
    parsed, fen = text_record(line)
    if (parsed.board, parsed.score, parsed.meta) != (record.board, record.score, record.meta):
        raise ValueError('text sidecar board/STM/score/White-result mismatch')
    return fen


def aligned_records(reader: PosReader, sidecar: str | Path, *, sidecar_format='text') -> Iterator[tuple[Record, str]]:
    if sidecar_format not in ('text', 'fen'):
        raise ValueError('sidecar_format must be text or fen')
    with Path(sidecar).open('r', encoding='utf-8', newline=None) as f:
        for i in range(reader.n):
            line = f.readline()
            if not line:
                raise ValueError(f'sidecar truncated at row {i}')
            row = reader.row(i)
            try:
                fen = match_text_record(row, line) if sidecar_format == 'text' else match_fen(row, line)
            except ValueError as error:
                raise ValueError(f'sidecar row {i}: {error}') from error
            yield row, fen
        if f.readline():
            raise ValueError('sidecar has more rows than POS')


def board_to_fen(record: Record, *, policy: str | None = None) -> str:
    if policy != RECONSTRUCTION_POLICY:
        raise ValueError('lossy reconstruction requires explicit policy=' + RECONSTRUCTION_POLICY)
    validate_record(record)
    ranks = []
    for rank in range(7, -1, -1):
        text = ''; empty = 0
        for file in range(8):
            square = rank*8 + file
            code = (record.board[square//2] >> (4*(square%2))) & 15
            if code == 0:
                empty += 1
            else:
                if empty:
                    text += str(empty); empty = 0
                text += PIECES[code]
        if empty:
            text += str(empty)
        ranks.append(text)
    return '/'.join(ranks) + (' b' if record.meta & 1 else ' w') + ' - - 0 1'


def file_hash(path: str | Path, algorithm='sha256') -> str:
    h = hashlib.new(algorithm)
    with Path(path).open('rb') as f:
        while block := f.read(1024*1024):
            h.update(block)
    return h.hexdigest()


def write_manifest(path: str | Path, files: Iterable[str | Path], *, metadata=None) -> dict:
    path = Path(path)
    entries = []
    for name in files:
        p = Path(name)
        entries.append({'path': str(p), 'bytes': p.stat().st_size,
                        'sha256': file_hash(p), 'md5': file_hash(p, 'md5')})
    result = {'files': entries, 'metadata': metadata or {}}
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(result, f, indent=2, sort_keys=True, allow_nan=False)
        f.write('\n'); f.flush(); os.fsync(f.fileno())
    return result


class PosWriter:
    """Streaming column spool, no overwrites/deletions; publish POS last.

    Retains all .part files, including after failure. Atomic no-replace hard links
    publish sealed bytes; a filesystem lacking hard links fails closed.
    """
    def __init__(self, output_dir: str | Path, stem: str, with_hce: bool, *, with_fen: bool | None = None):
        if with_fen is not None and type(with_fen) is not bool:
            raise ValueError('with_fen must be bool or None')
        if not isinstance(stem, str) or not stem or stem in ('.', '..') or re.search(r'[\\/<>:"|?*\x00-\x1f]', stem) or stem.endswith((' ', '.')):
            raise ValueError('stem must be one safe filename component')
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.stem, self.with_hce, self.n = stem, bool(with_hce), 0
        self.pos_path = self.output_dir / (stem + '.pos')
        self.hce_path = self.output_dir / (stem + '.hce')
        self.fen_path = self.output_dir / (stem + '.fen')
        self._streams = {}; self._fen_mode = with_fen; self._failed = False; self._sealed = False; self._receipt = None
        suffixes = ['.pos', '.hce', '.fen', '.claim.part', '.boards.part', '.scores.part', '.meta.part', '.hce-data.part', '.pos.part', '.hce.part', '.fen.part']
        if any((self.output_dir/(stem+s)).exists() or (self.output_dir/(stem+s)).is_symlink() for s in suffixes):
            raise FileExistsError('output stem is already in use: ' + stem)
        try:
            with (self.output_dir/(stem+'.claim.part')).open('xb') as f:
                f.write(b'Forge FPOS writer: owned prefix, partials intentionally retained\n')
            for name in ['boards', 'scores', 'meta'] + (['hce-data'] if self.with_hce else []):
                self._streams[name] = (self.output_dir/(stem+'.'+name+'.part')).open('xb')
            if with_fen is True:
                self._streams['fen'] = (self.output_dir/(stem+'.fen.part')).open('xb')
        except BaseException:
            self.abort(); raise

    def append(self, record: Record, fen: str | None = None):
        if self._sealed or self._failed:
            raise ValueError('writer is sealed or aborted')
        try:
            validate_record(record, require_hce=self.with_hce)
            normalized = match_fen(record, fen) if fen is not None else None
            mode = fen is not None
            if self._fen_mode is not None and mode != self._fen_mode:
                raise ValueError('FEN sidecar must cover every output row or none')
            if self._fen_mode is None:
                self._fen_mode = mode
                if mode:
                    self._streams['fen'] = (self.output_dir/(self.stem+'.fen.part')).open('xb')
            self._streams['boards'].write(record.board)
            self._streams['scores'].write(struct.pack('<h', record.score))
            self._streams['meta'].write(bytes([record.meta]))
            if self.with_hce:
                self._streams['hce-data'].write(struct.pack('<h', record.hce))
            if mode:
                self._streams['fen'].write((normalized+'\n').encode('utf-8'))
            self.n += 1
        except BaseException:
            self.abort(); raise

    def abort(self):
        if not self._sealed:
            self._failed = True
        for f in self._streams.values():
            if not f.closed:
                f.close()

    def _assemble(self, suffix, magic, columns):
        path = self.output_dir/(self.stem+suffix+'.part')
        with path.open('xb') as out:
            out.write(HEADER.pack(magic, 1, self.n))
            for column in columns:
                with (self.output_dir/(self.stem+'.'+column+'.part')).open('rb') as src:
                    shutil.copyfileobj(src, out, 1024*1024)
            out.flush(); os.fsync(out.fileno())
        return path

    def seal(self) -> dict:
        if self._sealed:
            return self._receipt
        if self._failed:
            raise ValueError('cannot seal an aborted writer')
        try:
            for f in self._streams.values():
                f.flush(); os.fsync(f.fileno()); f.close()
            pos_part = self._assemble('.pos', b'FPOS', ['boards', 'scores', 'meta'])
            paths = []
            if self.with_hce:
                hce_part = self._assemble('.hce', b'FHCE', ['hce-data'])
                os.link(hce_part, self.hce_path); paths.append(self.hce_path)
            if self._fen_mode:
                os.link(self.output_dir/(self.stem+'.fen.part'), self.fen_path); paths.append(self.fen_path)
            os.link(pos_part, self.pos_path); paths.append(self.pos_path)
            self._sealed = True
            self._receipt = {'count': self.n, 'pos': str(self.pos_path),
                             'hce': str(self.hce_path) if self.with_hce else None,
                             'fen': str(self.fen_path) if self._fen_mode else None,
                             'files': [str(p) for p in paths], 'parts_retained': True}
            return self._receipt
        except BaseException:
            self.abort(); raise

    def close(self):
        return self.seal()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.close()
        else:
            self.abort()
