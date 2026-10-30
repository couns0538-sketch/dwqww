#!/usr/bin/env python3
"""Offline, kept-only Forge data filtering; never mutates input shards.

IDEA_SOURCE: user Astra A1 task; same-repository FPOS/FHCE and Forge public search APIs.
The documented ordered waterfall is a data policy, not an Elo claim.
"""
from __future__ import annotations
import argparse
from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import gzip
import hashlib
import json
import re
from pathlib import Path
import sqlite3
import sys
import time
from typing import Any

RULES = ('holdout', 'disagreement', 'exact_duplicate', 'near_duplicate',
         'in_check', 'terminal', 'teacher_incomplete', 'bestmove_capture', 'bestmove_promotion')

@dataclass
class Config:
    positions: list[Path]
    sidecars: list[Path]
    out: Path
    probe: Path
    holdouts: list[Path] | None = None
    nodes: int = 1024
    workers: int = 1
    batch_size: int = 256
    hash_mb: int = 1
    limit: int | None = None
    disagreement_cp: int = 400
    draw_disagreement_cp: int = 800
    near_window: int = 64
    near_score_delta: int = 25
    stem: str = 'forge_filtered'


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def fingerprint(record: Any) -> bytes:
    return record.board + bytes([record.meta & 1])


def disagreement(record: Any, decisive_cp: int, draw_cp: int) -> bool:
    """Scores are STM; packed result is White's result, encoded 0/1/2."""
    result = record.meta >> 1
    if record.meta & 1:
        result = 2 - result
    return ((result == 0 and record.score >= decisive_cp) or
            (result == 2 and record.score <= -decisive_cp) or
            (result == 1 and abs(record.score) >= draw_cp))


def unpack(board: bytes) -> tuple[int, ...]:
    return tuple(piece for byte in board for piece in (byte & 15, byte >> 4))


class NearIndex:
    """A transparent bounded heuristic, not position or tactical equivalence."""
    def __init__(self, window: int, score_delta: int):
        require(window >= 0 and score_delta >= 0, 'negative near-duplicate parameter')
        self.window, self.score_delta = window, score_delta
        self.kept: deque[tuple[int, tuple, tuple[int, ...], int]] = deque()

    @staticmethod
    def signature(record: Any, fen: str) -> tuple:
        fields = fen.split()
        pieces = unpack(record.board)
        # White/black pawns and kings remain on exactly the same squares.
        fixed = tuple((sq, p) for sq, p in enumerate(pieces) if p in (1, 6, 7, 12))
        inventory = tuple(pieces.count(p) for p in range(1, 13))
        return record.meta, fields[2], fields[3], fixed, inventory

    def contains(self, index: int, record: Any, fen: str) -> bool:
        if self.window == 0:
            return False
        signature = self.signature(record, fen)
        pieces = unpack(record.board)
        for old_i, old_signature, old_pieces, old_score in self.kept:
            if not 0 < index - old_i <= self.window:
                continue
            if signature != old_signature or abs(record.score - old_score) > self.score_delta:
                continue
            differences = [sq for sq, (a, b) in enumerate(zip(pieces, old_pieces)) if a != b]
            # Exactly one non-pawn/non-king relocation; zero differences belong to exact dedupe.
            if len(differences) != 2:
                continue
            a, b = differences
            if (old_pieces[a] == pieces[b] not in (0, 1, 6, 7, 12) and
                    old_pieces[b] == pieces[a] == 0):
                return True
            if (old_pieces[b] == pieces[a] not in (0, 1, 6, 7, 12) and
                    old_pieces[a] == pieces[b] == 0):
                return True
        return False

    def add(self, index: int, record: Any, fen: str) -> None:
        if self.window == 0:
            return
        while self.kept and index - self.kept[0][0] > self.window:
            self.kept.popleft()
        self.kept.append((index, self.signature(record, fen), unpack(record.board), record.score))


class ExactIndex:
    def __init__(self, path: Path):
        require(not path.exists(), 'index already exists')
        self.db = sqlite3.connect(path)
        self.db.execute('PRAGMA journal_mode=OFF')
        self.db.execute('PRAGMA synchronous=OFF')
        self.db.execute('PRAGMA cache_size=-65536')
        self.db.execute('CREATE TABLE kept(digest BLOB PRIMARY KEY, key BLOB NOT NULL) WITHOUT ROWID')
        self.db.execute('CREATE TABLE holdout(digest BLOB PRIMARY KEY, key BLOB NOT NULL) WITHOUT ROWID')

    def contains(self, table: str, key: bytes) -> bool:
        require(table in ('kept', 'holdout'), 'invalid index table')
        digest = hashlib.sha256(key).digest()
        found = self.db.execute('SELECT key FROM '+table+' WHERE digest=?', (digest,)).fetchone()
        if found is not None:
            require(found[0] == key, 'SHA256 collision: refusing false position match')
            return True
        return False

    def add(self, table: str, key: bytes) -> None:
        if not self.contains(table, key):
            self.db.execute('INSERT INTO '+table+' VALUES(?,?)', (hashlib.sha256(key).digest(), key))

    def commit(self) -> None:
        self.db.commit()

    def close(self) -> None:
        self.db.close()


def digest_file(path: Path) -> dict[str, Any]:
    sha, md5 = hashlib.sha256(), hashlib.md5()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b''):
            sha.update(block); md5.update(block)
    return {'path': str(path.resolve()), 'bytes': path.stat().st_size,
            'sha256': sha.hexdigest(), 'md5': md5.hexdigest()}


def _json(path: Path, value: Any, *, exclusive: bool = False) -> None:
    with path.open('x' if exclusive else 'w', encoding='utf8', newline='\n') as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write('\n')


def _validate_config(config: Config) -> None:
    require(bool(config.positions) and len(config.positions) == len(config.sidecars),
            'each .pos needs one aligned full-FEN sidecar')
    require(config.nodes >= 1 and 1 <= config.workers <= 3 and config.batch_size >= 1 and config.hash_mb >= 1,
            'nodes/batch/hash must be positive and workers must be1..3')
    require(config.limit is None or config.limit >= 1, 'limit must be positive')
    require(config.disagreement_cp > 0 and config.draw_disagreement_cp > 0,
            'disagreement thresholds must be positive')
    require(config.near_window >= 0 and config.near_score_delta >= 0, 'near parameters must be nonnegative')
    require(config.stem and Path(config.stem).name == config.stem and config.stem not in ('.', '..'), 'invalid stem')
    paths = config.positions + config.sidecars + (config.holdouts or [])
    for path in paths:
        require(path.is_file(), 'input is not a file: '+str(path))
        require(not any(c in str(path) for c in '\t\r\n'), 'control character in input path')
    require(config.probe.is_file(), 'probe is not a file: '+str(config.probe))
    require(len({p.resolve() for p in config.positions}) == len(config.positions), 'duplicate input .pos')
    require(len({p.resolve() for p in config.sidecars}) == len(config.sidecars), 'duplicate sidecar')


def run(config: Config, pool_factory=None) -> dict[str, Any]:
    from forge_pos import PosReader, PosWriter, Record, text_record
    if pool_factory is None:
        from forge_probe import ProbePool
        pool_factory = ProbePool
    _validate_config(config)
    config.out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    counts = {rule: {'eligible': 0, 'dropped': 0} for rule in RULES}
    stats: dict[str, Any] = {
        'status': 'RUNNING', 'started_utc': datetime.now(timezone.utc).isoformat(),
        'config': {k: ([str(p) for p in v] if isinstance(v, list) else str(v) if isinstance(v, Path) else v)
                   for k, v in asdict(config).items()},
        'policy_order': list(RULES), 'rules': counts, 'input_rows': 0, 'kept': 0,
        'native_queries': 0, 'speculative_native_queries_not_used': 0, 'native_cpu_ns': 0,
        'exact_label_rows': 0, 'reconstructed_label_rows': 0,
        'source_alignment': [], 'inputs': [], 'holdouts': [],
        'shards': [{'path': str(p), 'input_rows': 0, 'kept': 0,
                    'rules': {r: {'eligible': 0, 'dropped': 0} for r in RULES}} for p in config.positions],
        'command': list(sys.argv),
        'validation_scope': 'Selected rows have structural FPOS/FEN alignment checks; native legal-state validation runs only on rows surviving the cheap rules.',
        'game_overlap': 'UNVERIFIED_NO_AUTHENTICATED_GAME_IDS',
        'near_policy': 'Prior kept rows within near_window ORIGINAL input indices; same STM/result/castling/EP/pawn+king squares/inventory; one nonpawn nonking relocation; source score within delta. Clocks are not used; this is explicitly a sampling heuristic.',
        'exact_identity': 'SHA256(board32 || STM), with stored full-key collision check',
        'holdout_scope': 'Only the explicit supplied holdouts; missing holdout shards/game provenance are not certified.',
        'fractions': 'Ordered first-drop waterfall, not independent marginal rule prevalence.',
        'teacher_incomplete_policy': 'Drop only explicit insufficient_budget/depth0 with null score and move; do not treat other native failures as filtered data.',
        'claim': 'Data filtering measurements only; no Elo or training-gain claim.'}
    _json(config.out/'progress.json', stats)
    database = ExactIndex(config.out/'position_index.sqlite')
    near = NearIndex(config.near_window, config.near_score_delta)
    writer = None
    decisions_raw = None
    decisions = None
    provenance = None
    try:
        stats['inputs'] = [{'pos': digest_file(p), 'sidecar': digest_file(f)}
                           for p, f in zip(config.positions, config.sidecars)]
        if config.probe.is_file():
            stats['probe'] = digest_file(config.probe)
        stats['implementation'] = {name: digest_file(Path(__file__).with_name(name))
                                   for name in ('filter_positions.py', 'forge_pos.py', 'forge_probe.py')}
        for path in config.holdouts or []:
            info = digest_file(path); count = 0
            if path.suffix.lower() == '.pos':
                with PosReader(path) as reader:
                    for i in range(reader.n):
                        database.add('holdout', fingerprint(reader.row(i))); count += 1
            else:
                with path.open(encoding='utf8') as source:
                    for line in source:
                        record, _ = text_record(line)
                        database.add('holdout', fingerprint(record)); count += 1
            info['rows'] = count; stats['holdouts'].append(info); database.commit()
        writer = PosWriter(config.out, config.stem, with_hce=True, with_fen=True)
        decisions_raw = (config.out/'decisions.tsv.gz').open('xb')
        decisions = gzip.GzipFile(filename='', fileobj=decisions_raw, mode='wb', mtime=0, compresslevel=1)
        decisions.write(b'input_index\tdecision\tbestmove\tteacher_score\tnodes\n')
        provenance = (config.out/'kept_rows.tsv').open('x', encoding='utf8', newline='\n')
        provenance.write('output_index\tinput_index\tinput_file\tinput_row\tstate_origin\tteacher_nodes\tteacher_depth\tteacher_score\tbestmove\toriginal_score\n')

        def cheap_reason(index, record, fen):
            key = fingerprint(record)
            if database.contains('holdout', key): return 'holdout'
            if disagreement(record, config.disagreement_cp, config.draw_disagreement_cp): return 'disagreement'
            if database.contains('kept', key): return 'exact_duplicate'
            if near.contains(index, record, fen): return 'near_duplicate'
            return None

        with pool_factory(config.probe, config.nodes, config.workers, config.out/'probe_logs',
                          hash_mb=config.hash_mb) as pool:
            def process(batch):
                requests = [(str(i), fen) for i, _, _, record, fen in batch if cheap_reason(i, record, fen) is None]
                responses = pool.map(requests, op='filter') if requests else []
                require(len(responses) == len(requests), 'native response count mismatch')
                answers = {}
                for (identifier, requested_fen), response in zip(requests, responses):
                    require(str(response.get('id')) == identifier and response.get('ok') is True,
                            'native failure/misaligned response: '+repr(response))
                    require(identifier not in answers, 'duplicate native response ID')
                    require(isinstance(response.get('fen'), str) and
                            ' '.join(response['fen'].split()) == ' '.join(requested_fen.split()),
                            'native response FEN differs from requested full state')
                    for name, expected in (('nodes_limit', config.nodes), ('hash_mb', config.hash_mb), ('threads', 1)):
                        require(type(response.get(name)) is int and response[name] == expected,
                                'native configuration mismatch: '+name)
                    answers[identifier] = response
                    cpu = response.get('cpu_ns', 0)
                    require(type(cpu) is int and cpu >= 0, 'invalid native CPU accounting')
                    stats['native_cpu_ns'] += cpu
                stats['native_queries'] += len(requests)
                for index, file_index, file_row, record, fen in batch:
                    drop = cheap_reason(index, record, fen)
                    response = answers.get(str(index))
                    for rule in RULES[:4]:
                        counts[rule]['eligible'] += 1
                        if drop == rule:
                            counts[rule]['dropped'] += 1
                            break
                    if drop is not None:
                        if response is not None: stats['speculative_native_queries_not_used'] += 1
                    else:
                        require(response is not None, 'eligible row missing native result')
                        for flag in ('in_check', 'terminal'):
                            require(type(response.get(flag)) is bool, 'missing native boolean '+flag)
                        counts['in_check']['eligible'] += 1
                        if response['in_check']: drop = 'in_check'
                        else:
                            counts['terminal']['eligible'] += 1
                            if response['terminal']: drop = 'terminal'
                            else:
                                counts['teacher_incomplete']['eligible'] += 1
                                if response.get('analyzed') is False:
                                    require(response.get('analysis_status') == 'insufficient_budget' and
                                            type(response.get('depth')) is int and response['depth'] == 0 and
                                            type(response.get('nodes')) is int and 0 <= response['nodes'] <= config.nodes and
                                            'bestmove' in response and response['bestmove'] is None and
                                            'score' in response and response['score'] is None,
                                            'unrecognized incomplete teacher result: '+repr(response))
                                    drop = 'teacher_incomplete'
                                else:
                                    require(response.get('analyzed') is True and type(response.get('depth')) is int and response['depth'] >= 1,
                                            'no completed teacher iteration: '+repr(response))
                                    require(type(response.get('nodes')) is int and 0 < response['nodes'] <= config.nodes,
                                            'searched node count outside requested budget')
                                    require(type(response.get('score')) is int and -32000 <= response['score'] <= 32000, 'invalid teacher score')
                                    require(type(response.get('hce')) is int and -32767 <= response['hce'] <= 32767, 'invalid HCE')
                                    for flag in ('capture', 'promotion'):
                                        require(type(response.get(flag)) is bool, 'missing native boolean '+flag)
                                    require(isinstance(response.get('bestmove'), str) and
                                            re.fullmatch(r'[a-h][1-8][a-h][1-8][nbrq]?', response['bestmove']) is not None,
                                            'missing/invalid native bestmove')
                                    counts['bestmove_capture']['eligible'] += 1
                                    if response['capture']: drop = 'bestmove_capture'
                                    else:
                                        counts['bestmove_promotion']['eligible'] += 1
                                        if response['promotion']: drop = 'bestmove_promotion'
                        if drop is not None: counts[drop]['dropped'] += 1
                    stats['input_rows'] += 1
                    shard = stats['shards'][file_index]
                    shard['input_rows'] += 1
                    for rule in RULES:
                        shard['rules'][rule]['eligible'] += 1
                        if drop == rule:
                            shard['rules'][rule]['dropped'] += 1
                            break
                    if drop is None: shard['kept'] += 1
                    decision = drop or 'kept'
                    decisions.write((f"{index}\t{decision}\t{response.get('bestmove','') if response else ''}\t{response.get('score','') if response else ''}\t{response.get('nodes','') if response else ''}\n").encode())
                    if drop is None:
                        out_record = Record(record.board, record.score, record.meta, response['hce'])
                        writer.append(out_record, fen=fen)
                        provenance.write(f"{stats['kept']}\t{index}\t{config.positions[file_index]}\t{file_row}\texact_full_fen\t{response['nodes']}\t{response['depth']}\t{response['score']}\t{response['bestmove']}\t{record.score}\n")
                        stats['kept'] += 1; stats['exact_label_rows'] += 1
                        database.add('kept', fingerprint(record)); near.add(index, record, fen)
                database.commit(); decisions.flush(); provenance.flush()
                stats['wall_seconds_so_far'] = time.monotonic()-started
                _json(config.out/'progress.json', stats)

            index = 0; selected = 0; batch = []
            for file_index, (pos_path, fen_path) in enumerate(zip(config.positions, config.sidecars)):
                verified = 0; total_lines = 0
                with PosReader(pos_path) as reader, fen_path.open(encoding='utf8') as sidecar:
                    for file_row, line in enumerate(sidecar):
                        total_lines += 1
                        require(file_row < reader.n, 'sidecar has more rows than POS')
                        # A prefix run is explicitly prefix alignment, while total line count is still checked.
                        if config.limit is not None and selected >= config.limit:
                            continue
                        record = reader.row(file_row)
                        text_value, fen = text_record(line)
                        require((record.board, record.score, record.meta) == (text_value.board, text_value.score, text_value.meta),
                                f'sidecar/POS mismatch: {pos_path} row {file_row}')
                        verified += 1; selected += 1
                        batch.append((index, file_index, file_row, record, fen)); index += 1
                        if len(batch) >= config.batch_size:
                            process(batch); batch = []
                    require(total_lines == reader.n, 'sidecar row count differs from POS')
                    stats['source_alignment'].append({'pos': str(pos_path), 'total_rows': reader.n,
                        'sidecar_rows': total_lines, 'record_matches_verified': verified,
                        'scope': 'full' if verified == reader.n else 'selected_prefix_only_other_rows_counted_not_decoded'})
            if batch: process(batch)
        require(stats['input_rows'] == selected, 'processing count mismatch')
        require(stats['kept'] + sum(v['dropped'] for v in counts.values()) == selected, 'waterfall count mismatch')
        for local_counts, denominator in [(counts, selected)] + [(s['rules'], s['input_rows']) for s in stats['shards']]:
            for values in local_counts.values():
                values['fraction_input'] = values['dropped']/denominator if denominator else 0.0
                values['fraction_eligible'] = values['dropped']/values['eligible'] if values['eligible'] else None
                values['not_evaluated_after_earlier_rule'] = denominator-values['eligible']
        overlap = database.db.execute('SELECT COUNT(*) FROM kept JOIN holdout USING(digest) WHERE kept.key=holdout.key').fetchone()[0]
        require(overlap == 0, 'held-out position survived filtering')
        stats['supplied_holdout_position_overlap'] = overlap if config.holdouts else None
        stats['holdout_unique_positions'] = database.db.execute('SELECT COUNT(*) FROM holdout').fetchone()[0]
        # The source release is read-only by contract; verify it stayed that way before sealing.
        for source in stats['inputs']:
            for kind in ('pos', 'sidecar'):
                current = digest_file(Path(source[kind]['path']))
                require(current['sha256'] == source[kind]['sha256'] and current['bytes'] == source[kind]['bytes'],
                        'source changed during filtering: '+source[kind]['path'])
        for holdout in stats['holdouts']:
            current = digest_file(Path(holdout['path']))
            require(current['sha256'] == holdout['sha256'] and current['bytes'] == holdout['bytes'],
                    'holdout changed during filtering: '+holdout['path'])
        stats['source_hashes_unchanged'] = True
        writer.close(); writer = None
        decisions.close(); decisions = None; decisions_raw.close(); decisions_raw = None
        provenance.close(); provenance = None; database.close(); database = None
        stats.update(status='SEALED', finished_utc=datetime.now(timezone.utc).isoformat(), wall_seconds=time.monotonic()-started)
        stats['output'] = {suffix: digest_file(config.out/(config.stem+suffix)) for suffix in ('.pos', '.hce', '.fen')}
        _json(config.out/'summary.json', stats, exclusive=True)
        _json(config.out/'progress.json', stats)
        manifest = {str(p.relative_to(config.out)): digest_file(p) for p in sorted(config.out.rglob('*')) if p.is_file()}
        _json(config.out/'manifest.json', manifest, exclusive=True)
        return stats
    except BaseException as error:
        stats.update(status='FAILED_UNSEALED', error_type=type(error).__name__, error=str(error), wall_seconds=time.monotonic()-started)
        _json(config.out/'failure.json', stats, exclusive=True)
        _json(config.out/'progress.json', stats)
        raise
    finally:
        # Close handles only; partial outputs and scratch columns are deliberately retained.
        for item in (decisions, decisions_raw, provenance, database):
            if item is not None:
                try: item.close()
                except Exception: pass
        if writer is not None and hasattr(writer, 'abort'):
            writer.abort()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pos', nargs='+', type=Path, required=True)
    parser.add_argument('--sidecar', nargs='+', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--probe', type=Path, required=True)
    parser.add_argument('--holdout', nargs='*', type=Path, default=[])
    parser.add_argument('--probe-nodes', '--nodes', dest='nodes', type=int, default=1024)
    parser.add_argument('--probe-workers', '--workers', dest='workers', type=int, default=1)
    parser.add_argument('--batch-size', type=int, default=256)
    parser.add_argument('--hash-mb', type=int, default=1)
    parser.add_argument('--limit', type=int)
    parser.add_argument('--disagreement-cp', type=int, default=400)
    parser.add_argument('--draw-disagreement-cp', type=int, default=800)
    parser.add_argument('--near-window', type=int, default=64)
    parser.add_argument('--near-score-delta', type=int, default=25)
    parser.add_argument('--stem', default='forge_filtered')
    args = parser.parse_args(argv)
    config = Config(args.pos, args.sidecar, args.out, args.probe, args.holdout, args.nodes, args.workers,
                    args.batch_size, args.hash_mb, args.limit, args.disagreement_cp,
                    args.draw_disagreement_cp, args.near_window, args.near_score_delta, args.stem)
    summary = run(config)
    print(json.dumps({k: summary[k] for k in ('status','input_rows','kept','rules','native_queries','wall_seconds')}, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
