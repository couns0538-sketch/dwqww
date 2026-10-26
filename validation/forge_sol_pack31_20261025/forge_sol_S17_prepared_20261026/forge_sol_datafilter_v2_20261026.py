"""Offline v3b filter v2. CLI production requires authoritative row game IDs.

The import API defaults to explicitly labelled diagnostic output for legacy
callers; its conservative inferred groups never establish authentic game IDs.
Record parsing and writing are reused from the unchanged hash-pinned Job D tool.
"""
from __future__ import annotations
import argparse
from collections import deque
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import tempfile

DATE = '20261026'
BASE_SHA256 = '6ccf78c864c44155cea22044fe05d0584bec5241acdc5ebb2b71e23886007ab3'
BASE_PATH = Path(__file__).with_name('forge_sol_datafilter_20261025.py')
if hashlib.sha256(BASE_PATH.read_bytes()).hexdigest() != BASE_SHA256:
    raise ValueError('unchanged Job D parser dependency SHA256 mismatch')
_spec = importlib.util.spec_from_file_location('forge_sol_S16_legacy_dependency', BASE_PATH)
_base = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _base
_spec.loader.exec_module(_base)
Record, Reader = _base.Record, _base.Reader
read_records, write_records = _base.read_records, _base.write_records
md5, identity = _base.md5, _base.identity
text_record, invalid_reason = _base.text_record, _base.invalid_reason
disagreement, insert_key = _base.disagreement, _base.insert_key


def _protected(path):
    components = str(path).replace('\\', '/').split('/')
    return any(p.rstrip(' .').casefold() in {'lock', 'locks', 'baseline', '.git'} or
               p.rstrip(' .').casefold().startswith('dist-v') for p in components)


def _free_ram_bytes():
    if os.name == 'nt':
        import ctypes
        from ctypes import wintypes
        class MemoryStatus(ctypes.Structure):
            _fields_ = [('length', wintypes.DWORD), ('load', wintypes.DWORD)] + [
                (name, ctypes.c_ulonglong) for name in ('total_phys', 'avail_phys', 'total_page', 'avail_page', 'total_virtual', 'avail_virtual', 'avail_extended')]
        status = MemoryStatus(); status.length = ctypes.sizeof(status)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            raise OSError('cannot query free RAM')
        return status.avail_phys
    value = os.sysconf('SC_AVPHYS_PAGES') * os.sysconf('SC_PAGE_SIZE')
    if value < 0: raise ValueError('cannot query free RAM')
    return value


def _preflight_space(out, work, counts, train, aliases=(), game_id_map=None):
    if out.exists(): raise FileExistsError('output directory must be new; no overwrite')
    if not out.parent.is_dir() or not work.is_dir():
        raise ValueError('output parent and --work-dir must already exist')
    if _protected(out) or _protected(out.resolve()) or _protected(work): raise ValueError('protected output/work directory')
    total_rows = sum(counts.values())
    max_stem_bytes = max([len(stem.encode()) for stem in counts], default=0)
    id_segments = id_segment_bytes = max_id_bytes = row_id_bytes = 0
    for path in (game_id_map or {}).values():
        previous = None
        with open(path, encoding='utf-8') as stream:
            for line in stream:
                gid = line.rstrip('\r\n'); width = len(gid.encode())
                row_id_bytes += width
                max_id_bytes = max(max_id_bytes, width)
                if gid != previous:
                    id_segments += 1; id_segment_bytes += width + 1
                previous = gid
    # The legacy 300 B/row is only the base. IDs and stems also occur in
    # segment/kept tables and indexes; reserve separately and bound WAL batches.
    stem_reserve = 4 * max_stem_bytes * total_rows
    id_reserve = 8 * id_segment_bytes + 256 * id_segments + 2 * row_id_bytes
    wal_reserve = max(8 * 1024 * 1024, 20000 * (300 + 4 * max_stem_bytes + 8 * max_id_bytes + 256))
    scratch = 300 * total_rows + stem_reserve + id_reserve + wal_reserve
    alias_rows = 0
    for path in aliases:
        with Reader(path) as reader: alias_rows += reader.n
    train_rows = sum(counts[p.stem] for p in train) + alias_rows
    # Include the row-removal ledger and the columnar writer's temporary blocks.
    largest_stem = max([p.stem for p in list(train) + list(aliases)],
                       key=lambda value: len(json.dumps(value).encode()), default='')
    ledger_bytes = len(json.dumps({'stem': largest_stem, 'row': max(counts.values(), default=0),
                                   'position_sha256': 'f' * 64, 'game_id': 'g' * 128,
                                   'reason': 'result_loss_score_positive', 'conflicting_label': False}, sort_keys=True).encode()) + 1
    output = (37 + ledger_bytes) * train_rows + 37 * max([counts[p.stem] for p in train] or [0]) + 1024 * 1024
    same_volume = os.stat(out.parent).st_dev == os.stat(work).st_dev
    if same_volume:
        if shutil.disk_usage(work).free < scratch + output:
            raise ValueError('insufficient free disk: need {} bytes for scratch plus new output'.format(scratch + output))
    else:
        if shutil.disk_usage(work).free < scratch or shutil.disk_usage(out.parent).free < output:
            raise ValueError('insufficient free disk on scratch/output volume')
    return {'sqlite_estimate_bytes_per_row': 300, 'scratch_required_bytes': scratch,
            'stem_index_reserve_bytes': stem_reserve, 'id_segment_reserve_bytes': id_reserve,
            'per_row_id_reserve_bytes': 2 * row_id_bytes,
            'id_segments_upper_bound': id_segments, 'wal_reserve_bytes': wal_reserve,
            'output_required_bytes': output, 'removal_ledger_budget_bytes_per_row': ledger_bytes,
            'same_volume': same_volume}


def _check_maps(paths, text_map, order):
    if (not text_map or not order or set(text_map) != set(paths) or
            set(order) != set(paths) or len(order) != len(paths)):
        raise ValueError('complete text map and chronological stems required for ALL training/holdout sources')


def _text_tripwire(text_map, order):
    previous = None; flags = deque(maxlen=99); largest = windows = boundaries = 0
    for stem in order:
        with open(text_map[stem], encoding='utf-8') as stream:
            for line in stream:
                _, context = text_record(line)
                if previous is not None:
                    boundary = context[0] < previous[0] or context[1] > previous[1] or context[2] != previous[2]
                    flags.append(int(boundary)); boundaries += boundary
                    if len(flags) == 99:
                        windows += 1; largest = max(largest, sum(flags))
                        if sum(flags) > 20:
                            raise ValueError('suspected interleaved text: more than 20 boundaries in a rolling 100 rows')
                previous = context
    return {'window_rows': 100, 'boundary_limit': 20, 'complete_windows': windows,
            'largest_boundary_count': largest, 'boundaries': boundaries,
            'proof': 'ANOMALY_CHECK_ONLY_NOT_AUTHENTIC_GAME_IDS'}


def _groups(db, paths, holdout_set, text_map, order, game_id_map, provenance):
    if not game_id_map:
        if text_map or order:
            _check_maps(paths, text_map, order)
            guard = _text_tripwire(text_map, order)
        else: guard = None
        policy = _base.build_groups(db, paths, holdout_set, text_map, order)
        policy.update(authentic_ids=False, interleaving_tripwire=guard)
        return policy
    _check_maps(paths, text_map, order)
    if set(game_id_map) != set(paths): raise ValueError('game-ID map must cover every training and holdout stem')
    if not isinstance(provenance, str) or not provenance.strip():
        raise ValueError('authoritative game-ID provenance is required')
    previous_id = None; previous_context = None; count_groups = segments = 0
    text_hashes = {}; id_hashes = {}
    db.execute('CREATE TABLE authentic_groups(gid TEXT PRIMARY KEY)')
    for stem in order:
        text_hashes[stem] = md5(text_map[stem]); id_hashes[stem] = md5(game_id_map[stem])
        with Reader(paths[stem]) as reader, open(text_map[stem], encoding='utf-8') as text, open(game_id_map[stem], encoding='utf-8') as ids:
            start = 0; segment_id = None
            for row in range(reader.n):
                line = text.readline(); idline = ids.readline()
                if not line or not idline: raise ValueError('text/game-ID row count mismatch: ' + stem)
                gid = idline.rstrip('\r\n')
                if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}', gid):
                    raise ValueError('game-ID must be a nonempty portable identifier of at most 128 characters')
                tr, context = text_record(line); binary = reader.row(row)
                if (tr.board, tr.score, tr.meta) != (binary.board, binary.score, binary.meta):
                    raise ValueError('text/POS record mismatch: {} row {}'.format(stem, row))
                if gid != previous_id:
                    if db.execute('SELECT 1 FROM authentic_groups WHERE gid=?', (gid,)).fetchone():
                        raise ValueError('interleaved/reopened game-ID: ' + gid)
                    db.execute('INSERT INTO authentic_groups VALUES(?)', (gid,)); count_groups += 1
                elif (context[0] < previous_context[0] or context[1] > previous_context[1] or context[2] != previous_context[2]):
                    raise ValueError('inconsistent chronology/result inside authoritative game-ID ' + gid)
                if segment_id is None: segment_id = gid
                elif segment_id != gid:
                    db.execute('INSERT INTO segments VALUES(?,?,?,?)', (stem, start, row, segment_id)); segments += 1
                    start = row; segment_id = gid
                if stem in holdout_set: db.execute('INSERT OR IGNORE INTO held_groups VALUES(?)', (gid,))
                previous_id, previous_context = gid, context
                if row % 10000 == 0: db.commit()
            if text.readline() or ids.readline(): raise ValueError('text/game-ID row count exceeds POS: ' + stem)
            if reader.n:
                db.execute('INSERT INTO segments VALUES(?,?,?,?)', (stem, start, reader.n, segment_id)); segments += 1
    db.commit()
    return {'mode': 'AUTHORITATIVE_ROW_GAME_IDS', 'authentic_ids': True,
            'groups': count_groups, 'segments': segments, 'text_md5': text_hashes,
            'game_id_md5': id_hashes, 'provenance': provenance,
            'limitation': 'Owner-supplied game-ID authority is a required input contract, not inferred from FEN counters.'}


def filter_data(train, holdout, hce_dir, out, seed=20261025, threshold=None,
                text_map=None, ordered_stems=None, *, work_dir=None,
                game_id_map=None, game_id_provenance=None, production=False, hce_map=None):
    """Filter new sealed files. Import default is DIAGNOSTIC, never train-approved.

    production=True requires owner-authoritative row-aligned game-ID maps with
    provenance plus matching chronological text for every source.
    """
    if threshold is not None and (type(threshold) is not int or threshold <= 0):
        raise ValueError('disagreement threshold must be a positive integer; omit for OFF')
    if production and not game_id_map: raise ValueError('production requires authoritative row-aligned game-ID maps and provenance')
    if game_id_map and (not isinstance(game_id_provenance, str) or not game_id_provenance.strip()):
        raise ValueError('authoritative game-ID provenance is required')
    out = Path(out).absolute(); work = Path(work_dir).resolve(strict=True) if work_dir else out.parent.resolve(strict=True)
    hce_dir = Path(hce_dir).resolve(strict=True)
    def hce_file(path):
        return Path(hce_map[path.stem]).resolve(strict=True) if hce_map and path.stem in hce_map else hce_dir / (path.stem + '.hce')
    train = [Path(p).resolve(strict=True) for p in train]; holdout = [Path(p).resolve(strict=True) for p in holdout]
    if not holdout: raise ValueError('explicit authoritative holdout inputs required')
    if len(set(holdout)) != len(holdout): raise ValueError('duplicate holdout paths')
    aliases = []; candidates = []
    for p in dict.fromkeys(train):
        if any(os.path.samefile(p, h) for h in holdout): aliases.append(p)
        else: candidates.append(p)
    paths = {p.stem: p for p in candidates + holdout}
    if len(paths) != len(candidates) + len(holdout): raise ValueError('unambiguous unique source stems required')
    counts = {}; input_md5 = {}
    for p in candidates + holdout:
        with Reader(p, hce_file(p) if p in candidates else None) as reader: counts[p.stem] = reader.n
        input_md5[p.name] = md5(p)
        if p in candidates: input_md5[p.stem + '.hce'] = md5(hce_file(p))
    space = _preflight_space(out, work, counts, candidates, aliases, game_id_map)
    if production: _check_maps(paths, text_map, ordered_stems)
    out.mkdir(mode=0o700); scratch = Path(tempfile.mkdtemp(prefix='forge_sol_S16_sqlite_', dir=work)); db = None
    try:
        db = sqlite3.connect(scratch / 'work.sqlite')
        db.executescript('PRAGMA journal_mode=WAL; PRAGMA synchronous=OFF; CREATE TABLE holdout(hash BLOB PRIMARY KEY,key BLOB NOT NULL); CREATE TABLE seen(hash BLOB PRIMARY KEY,key BLOB NOT NULL,score INTEGER,meta INTEGER,hce INTEGER); CREATE TABLE kept(stem TEXT,row INTEGER,gid TEXT,hash BLOB,PRIMARY KEY(stem,row)); CREATE TABLE segments(stem TEXT,start INTEGER,end INTEGER,gid TEXT); CREATE INDEX segments_order ON segments(stem,start); CREATE TABLE held_groups(gid TEXT PRIMARY KEY); CREATE TABLE audit(hash BLOB PRIMARY KEY,key BLOB NOT NULL);')
        for p in sorted(holdout, key=lambda p: p.name):
            for i, row in enumerate(read_records(p)):
                if invalid_reason(row): raise ValueError('invalid authoritative holdout record')
                digest, key = identity(row); insert_key(db, 'holdout', digest, key)
                if i % 10000 == 0: db.commit()
        db.commit()
        games = _groups(db, paths, {p.stem for p in holdout}, text_map, ordered_stems, game_id_map, game_id_provenance)
        summary = {'format': 'FPOS/FHCE version1, original columnar layout',
                   'position_identity': 'SHA256(board32 || STM1); excludes unavailable castling/EP/clocks',
                   'seed': seed, 'disagreement_threshold': threshold, 'input_md5': input_md5,
                   'base_parser_sha256': BASE_SHA256, 'disk_preflight': space,
                   'run_mode': 'PRODUCTION_WITH_OWNER_GAME_IDS' if production else 'DIAGNOSTIC_ONLY',
                   'game_policy': games, 'game_overlap': 'UNVERIFIED_NO_ORDERED_TEXT',
                   'game_overlap_verified': games['authentic_ids'],
                   'authentic_game_overlap': 'UNVERIFIED_NO_AUTHORITATIVE_GAME_IDS',
                   'production_eligible': bool(production and games['authentic_ids']),
                   'sealed_for_training': bool(production and games['authentic_ids']),
                   'real_holdout_overlap': 'UNVERIFIED_IDENTITY_OF_REAL_013_014_NOT_ATTESTED',
                   'excluded_holdout_shards': sorted(p.name for p in aliases),
                   'duplicate_holdout_shards': [], 'holdout_sources': sorted(p.name for p in holdout),
                   'holdout_unique_positions': db.execute('SELECT count(*) FROM holdout').fetchone()[0],
                   'shards': [], 'totals': {'input': 0, 'kept': 0, 'dropped': 0},
                   'conflicting_label_duplicates': 0, 'input_position_overlap': 0,
                   'input_game_overlap': 0 if games['authentic_ids'] else 'UNVERIFIED',
                   'removal_row_index': 'zero-based source row',
                   'supplied_holdout_overlap': None, 'output_duplicate_positions': None}
        holdout_md5 = {input_md5[p.name] for p in holdout}
        order = sorted(candidates, key=lambda p: (hashlib.sha256((str(seed) + '\0' + p.stem).encode()).digest(), p.name))
        with open(out / ('forge_sol_S16_removals_' + DATE + '.jsonl'), 'x', encoding='utf-8', newline='\n') as removal:
            def note(stem, row, digest, gid, reason, conflict=False):
                removal.write(json.dumps({'stem': stem, 'row': row, 'position_sha256': digest.hex(),
                                          'game_id': gid, 'reason': reason, 'conflicting_label': conflict}, sort_keys=True) + '\n')
            for p in sorted(aliases, key=lambda p: p.name):
                with Reader(p) as reader:
                    for i in range(reader.n):
                        digest, _ = identity(reader.row(i)); note(p.stem, i, digest, None, 'holdout_shard')
                    summary['shards'].append({'stem': p.stem, 'input': reader.n, 'kept': 0, 'dropped': {'holdout_shard': reader.n}, 'dropped_total': reader.n})
                    summary['totals']['input'] += reader.n; summary['totals']['dropped'] += reader.n
                    summary['input_position_overlap'] += reader.n
                    if games['authentic_ids']: summary['input_game_overlap'] += reader.n
            for p in order:
                whole_duplicate = input_md5[p.name] in holdout_md5
                if whole_duplicate: summary['duplicate_holdout_shards'].append(p.name)
                dropped = {}; kept = 0
                cursor = iter(db.execute('SELECT start,end,gid FROM segments WHERE stem=? ORDER BY start', (p.stem,)))
                segment = next(cursor, None)
                with Reader(p, hce_file(p)) as reader:
                    for i in range(reader.n):
                        row = reader.row(i); digest, key = identity(row); reason = invalid_reason(row); gid = None
                        if games['mode'] != 'UNVERIFIED_NO_ORDERED_TEXT':
                            while segment is not None and i >= segment[1]: segment = next(cursor, None)
                            if segment is None or not segment[0] <= i < segment[1]: raise ValueError('incomplete group index')
                            gid = segment[2]
                        held_group = gid is not None and bool(db.execute('SELECT 1 FROM held_groups WHERE gid=?', (gid,)).fetchone())
                        held = db.execute('SELECT key FROM holdout WHERE hash=?', (digest,)).fetchone()
                        if held and held[0] != key: raise ValueError('position hash collision with holdout')
                        if held: summary['input_position_overlap'] += 1
                        if held_group and games['authentic_ids']: summary['input_game_overlap'] += 1
                        if reason is None and whole_duplicate: reason = 'duplicate_holdout_shard'
                        if reason is None and held_group: reason = 'holdout_game_group'
                        if reason is None and held: reason = 'holdout_position'
                        conflict = False
                        seen = db.execute('SELECT key,score,meta,hce FROM seen WHERE hash=?', (digest,)).fetchone()
                        if seen and seen[0] != key: raise ValueError('position hash collision')
                        if reason is None and seen:
                            reason = 'duplicate_position'; conflict = tuple(seen[1:]) != (row.score, row.meta, row.hce)
                            summary['conflicting_label_duplicates'] += conflict
                        if reason is None: reason = disagreement(row, threshold)
                        if reason:
                            dropped[reason] = dropped.get(reason, 0) + 1; note(p.stem, i, digest, gid, reason, conflict)
                        else:
                            db.execute('INSERT INTO seen VALUES(?,?,?,?,?)', (digest, key, row.score, row.meta, row.hce))
                            db.execute('INSERT INTO kept VALUES(?,?,?,?)', (p.stem, i, gid, digest)); kept += 1
                        if i % 10000 == 0: db.commit()
                    db.commit()
                    if kept:
                        def selected():
                            for (i,) in db.execute('SELECT row FROM kept WHERE stem=? ORDER BY row', (p.stem,)): yield reader.row(i)
                        stem = p.stem + '_filtered_' + DATE
                        if write_records(out / (stem + '.pos'), out / (stem + '.hce'), selected()) != kept:
                            raise ValueError('writer selection count mismatch')
                    info = {'stem': p.stem, 'input': reader.n, 'kept': kept, 'dropped': dropped, 'dropped_total': sum(dropped.values())}
                    if reader.n != kept + info['dropped_total']: raise ValueError('accounting mismatch')
                    summary['shards'].append(info); summary['totals']['input'] += reader.n
                    summary['totals']['kept'] += kept; summary['totals']['dropped'] += info['dropped_total']
        written = overlaps = duplicates = 0
        for p in sorted(out.glob('*.pos')):
            for row in read_records(p, p.with_suffix('.hce')):
                if invalid_reason(row): raise ValueError('invalid output record')
                digest, key = identity(row)
                overlaps += bool(db.execute('SELECT 1 FROM holdout WHERE hash=?', (digest,)).fetchone())
                duplicates += not insert_key(db, 'audit', digest, key); written += 1
        if overlaps or duplicates or written != summary['totals']['kept']:
            raise ValueError('independent output overlap/uniqueness/count audit failed')
        summary.update(supplied_holdout_overlap=overlaps, output_duplicate_positions=duplicates)
        if games['mode'] != 'UNVERIFIED_NO_ORDERED_TEXT':
            if db.execute('SELECT count(*) FROM kept JOIN held_groups USING(gid)').fetchone()[0]:
                raise ValueError('retained holdout-touched game group')
            summary['game_overlap'] = 0
            if games['authentic_ids']: summary['authentic_game_overlap'] = 0
            else: summary['game_overlap_meaning'] = 'Observed conservative inferred-group count only; authentic game overlap UNVERIFIED'
        for p in candidates + holdout:
            if md5(p) != input_md5[p.name]: raise ValueError('input changed during read')
            if p in candidates and md5(hce_file(p)) != input_md5[p.stem + '.hce']:
                raise ValueError('HCE input changed during read')
        for field, mapping in [('text_md5', text_map), ('game_id_md5', game_id_map)]:
            for stem, digest in games.get(field, {}).items():
                if md5(mapping[stem]) != digest: raise ValueError('text/game-ID source changed during read')
        db.close(); db = None; shutil.rmtree(scratch)
        summary['outputs'] = {p.name: md5(p) for p in sorted(out.iterdir()) if p.is_file()}
        report = out / ('forge_sol_datafilter_summary_' + DATE + '.json')
        report.write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')
        manifest = out / ('forge_sol_datafilter_manifest_' + DATE + '.md5')
        manifest.write_text(''.join(md5(p) + '  ' + p.name + '\n' for p in sorted(out.iterdir()) if p.is_file() and p != manifest))
        for p in out.iterdir():
            if p.is_file(): p.chmod(0o444)
        return summary
    except BaseException as error:
        if db is not None: db.close()
        failure = out / ('forge_sol_S16_FAILED_UNSEALED_' + DATE + '.json')
        if not failure.exists(): failure.write_text(json.dumps({'status': 'FAILED_UNSEALED_OUTPUT', 'error': str(error)}, indent=2) + '\n')
        # Keep only this run's scratch for diagnosis; its path is not a manifest input.
        raise


def _path_map(path):
    path = Path(path).resolve(strict=True)
    value = json.loads(path.read_text(encoding='utf-8-sig'))
    if not isinstance(value, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in value.items()):
        raise ValueError('mapping must be a JSON object: source stem -> path')
    return {k: str((path.parent / v).resolve(strict=True)) for k, v in value.items()}


def _run_config(path):
    path = Path(path).resolve(strict=True); config = json.loads(path.read_text(encoding='utf-8-sig'))
    allowed = {'d_output_pos', 'sealed_pos_dirs', 'holdout_pos', 'hce_dir', 'out', 'work_dir',
               'text_map', 'ordered_stems', 'game_id_map', 'game_id_provenance', 'seed', 'disagreement_threshold'}
    if not isinstance(config, dict) or set(config) - allowed: raise ValueError('unknown or invalid production runner configuration fields')
    required = allowed - {'seed', 'disagreement_threshold'}
    if required - set(config): raise ValueError('missing production configuration fields: ' + ', '.join(sorted(required - set(config))))
    def resolve(value): return (path.parent / value).resolve()
    if not isinstance(config['d_output_pos'], list) or not config['d_output_pos']:
        raise ValueError('d_output_pos must explicitly list Job D output POS paths')
    if not isinstance(config['sealed_pos_dirs'], list) or not config['sealed_pos_dirs']:
        raise ValueError('sealed_pos_dirs must explicitly list every sealed-shard directory')
    train = [resolve(p) for p in config['d_output_pos']]
    for directory in config['sealed_pos_dirs']:
        folder = resolve(directory)
        if not folder.is_dir(): raise ValueError('sealed source directory missing: ' + str(folder))
        shards = sorted(folder.rglob('*.pos'))
        if not shards: raise ValueError('sealed source directory contains no POS shards: ' + str(folder))
        for p in shards:
            if p.stat().st_mode & 0o222: raise ValueError('sealed POS source is writable: ' + str(p))
        train.extend(shards)
    holdout = [resolve(p) for p in config['holdout_pos']]
    if sorted(p.name for p in holdout) != ['forge_selfplay_013.pos', 'forge_selfplay_014.pos']:
        raise ValueError('production runner requires both exact holdout filenames forge_selfplay_013.pos and forge_selfplay_014.pos')
    hce_dir = resolve(config['hce_dir'])
    hce_map = {p.stem: str(p.with_suffix('.hce') if p.with_suffix('.hce').is_file() else hce_dir / (p.stem + '.hce')) for p in train}
    return filter_data(train, holdout, hce_dir, resolve(config['out']), config.get('seed', 20261025),
                       config.get('disagreement_threshold'), _path_map(resolve(config['text_map'])),
                       config['ordered_stems'], work_dir=resolve(config['work_dir']),
                       game_id_map=_path_map(resolve(config['game_id_map'])),
                       game_id_provenance=config['game_id_provenance'], production=True, hce_map=hce_map)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--config', type=Path, help='One-command production configuration')
    ap.add_argument('--train', nargs='+', type=Path)
    ap.add_argument('--holdout-pos', nargs='+', type=Path)
    ap.add_argument('--hce-dir', type=Path); ap.add_argument('--out', type=Path)
    ap.add_argument('--work-dir', type=Path)
    ap.add_argument('--seed', type=int, default=20261025); ap.add_argument('--disagreement-threshold', type=int)
    ap.add_argument('--text-map', type=Path); ap.add_argument('--ordered-stems', nargs='+')
    ap.add_argument('--game-id-map', type=Path, help='JSON stem -> row-aligned authoritative game-ID file')
    ap.add_argument('--game-id-provenance', help='Owner statement identifying the authoritative ID origin')
    ap.add_argument('--diagnostic-mode', action='store_true', help='Explicitly prohibit production approval; inferred groups are diagnostic only')
    a = ap.parse_args(argv)
    try:
        if a.config and a.diagnostic_mode: raise ValueError('cannot combine production --config with --diagnostic-mode')
        if not a.diagnostic_mode and _free_ram_bytes() < 256 * 1024 * 1024:
            raise ValueError('insufficient free RAM: production runner requires at least 256 MiB')
        if a.config:
            result = _run_config(a.config)
        else:
            if not all((a.train, a.holdout_pos, a.hce_dir, a.out, a.work_dir)):
                raise ValueError('--train --holdout-pos --hce-dir --out --work-dir are required without --config')
            tm = _path_map(a.text_map) if a.text_map else None
            gm = _path_map(a.game_id_map) if a.game_id_map else None
            result = filter_data(a.train, a.holdout_pos, a.hce_dir, a.out, a.seed, a.disagreement_threshold,
                             tm, a.ordered_stems, work_dir=a.work_dir, game_id_map=gm,
                             game_id_provenance=a.game_id_provenance, production=not a.diagnostic_mode)
    except (ValueError, OSError, sqlite3.Error) as error:
        print(str(error), file=sys.stderr); return 2
    print(json.dumps(result, indent=2, sort_keys=True)); return 0


if __name__ == '__main__': sys.exit(main())
