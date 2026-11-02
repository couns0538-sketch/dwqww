#!/usr/bin/env python3
"""Audit frozen Forge text + result-aware JSONL against complete raw holdouts.

Original R10 adapter; uses audit_exports' independent FEN and input-identity
checks. Does not decode NPT/binpack, infer game IDs, modify inputs, or train.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import stat
import sys
import time
from audit_exports import fen_state, fingerprint, identity, unique

ROOT = Path('D:/a10')
CAP = 15_000_000_000
RESERVATION = 2_000_000_000
INTERVAL = 4096
IMPLEMENTATIONS = {str(p): fingerprint(p) for p in (Path(__file__), Path(__file__).with_name('audit_exports.py'))}


class AuditFailure(ValueError):
    pass


class ResourceBlocked(RuntimeError):
    pass


def require(ok, message):
    if not ok:
        raise AuditFailure(message)


def safe_path(value):
    require(isinstance(value, (str, Path)), 'path must be text')
    raw = str(value)
    require(re.match(r'^[dD]:[\\/]', raw) is not None, 'absolute D:/a10 path required')
    require(':' not in raw[2:] and not any(c in raw for c in '*?\x00'), 'invalid path syntax')
    require(not any(p in ('.', '..') for p in re.split(r'[\\/]', raw)), 'dot path components refused')
    path = Path(raw)
    require(path.is_relative_to(ROOT), 'all audit I/O must remain under D:/a10')
    for p in (path, *path.parents):
        if p.exists() or p.is_symlink():
            s = p.lstat()
            require(not stat.S_ISLNK(s.st_mode) and not getattr(s, 'st_file_attributes', 0) & 1024,
                    'reparse/symlink refused: ' + str(p))
    return path


def tree_bytes(root):
    total = 0
    if not root.exists():
        return total
    for parent, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            p = Path(parent) / name
            s = p.lstat()
            require(not stat.S_ISLNK(s.st_mode) and not getattr(s, 'st_file_attributes', 0) & 1024,
                    'workspace reparse refused')
            if name in files:
                total += s.st_size
    return total


class Guard:
    """Check floors/output every4096 rows; rescan other workspace usage each60s."""
    def __init__(self, out):
        self.out = out
        self.external = tree_bytes(ROOT)
        self.last = time.monotonic()
        if self.external + RESERVATION > CAP:
            raise ResourceBlocked('15 GB workspace cap plus2 GB index reservation')
        self.check(reserve=True)

    def check(self, reserve=False):
        produced = tree_bytes(self.out)
        if time.monotonic() - self.last >= 60:
            self.external = tree_bytes(ROOT) - produced
            self.last = time.monotonic()
        if produced > RESERVATION or self.external + produced > CAP:
            raise ResourceBlocked('audit reservation/workspace cap exceeded')
        free_c = shutil.disk_usage('C:/').free
        free_d = shutil.disk_usage('D:/').free
        if free_c < 30 * 1024**3 or free_d < 50 * 1024**3 + (RESERVATION if reserve else 0):
            raise ResourceBlocked('C30 GiB/D50 GiB floor or preflight reservation')


def json_object(raw):
    def nonfinite(value):
        raise AuditFailure('nonfinite JSON: ' + value)
    obj = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique, parse_constant=nonfinite)
    require(isinstance(obj, dict), 'JSON object required')
    return obj


class BoundInputs:
    def __init__(self):
        self.before = {}

    def bind(self, spec):
        path = safe_path(spec['path'])
        require(path.is_file(), 'input must be regular file')
        expected = spec.get('sha256')
        require(isinstance(expected, str) and re.fullmatch('[a-f0-9]{64}', expected), 'trusted SHA256 required')
        key = str(path)
        if key not in self.before:
            self.before[key] = fingerprint(path)
        require(self.before[key]['sha256'] == expected, 'trusted input hash mismatch: ' + key)
        return path

    def load(self, spec, *, with_bytes=False):
        path = self.bind(spec)
        require(path.stat().st_size <= 8 * 1024**2, 'metadata size limit')
        raw = path.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == spec['sha256'], 'metadata consumed hash mismatch')
        obj = json_object(raw)
        return (obj, raw) if with_bytes else obj

    def lines(self, spec, guard):
        path = self.bind(spec)
        before = self.before[str(path)]
        require(identity(path.stat()) == before['identity'] and identity(path.lstat()) == before['link_identity'],
                'input identity changed before scan')
        consumed = hashlib.sha256()
        with path.open('rb') as stream:
            require(identity(os.fstat(stream.fileno())) == before['identity'], 'descriptor changed before scan')
            for row in range(1, 2**63):
                line = stream.readline(1024 * 1024 + 1)
                if not line:
                    break
                require(len(line) <= 1024 * 1024, 'record exceeds1 MiB')
                consumed.update(line)
                if row % INTERVAL == 1:
                    guard.check()
                yield row, line.decode('utf-8-sig' if row == 1 else 'utf-8')
            require(identity(os.fstat(stream.fileno())) == before['identity'] and
                    identity(path.stat()) == before['identity'] and identity(path.lstat()) == before['link_identity'] and
                    consumed.hexdigest() == before['sha256'], 'input identity or consumed bytes changed during scan')

    def final(self):
        for path, before in self.before.items():
            require(fingerprint(safe_path(path)) == before, 'input changed during audit: ' + path)


def valid_game(value):
    require(value is None or isinstance(value, str) and bool(value.strip()), 'game ID must be nonempty text or null')
    return value


def rows_with_games(spec, bindings, guard):
    """A sidecar has one {physical_row,game_id} JSON object per input line."""
    sidecar = spec.get('game_ids')
    games = None
    if sidecar is not None:
        require(isinstance(sidecar, dict) and isinstance(sidecar.get('provenance'), str) and sidecar['provenance'].strip(),
                'trusted original game-ID provenance required')
        require(type(sidecar.get('rows')) is int and sidecar['rows'] > 0, 'game sidecar row count required')
        games = iter(bindings.lines(sidecar, guard))
    count = 0
    try:
        for number, line in bindings.lines(spec, guard):
            game = None
            if games is not None:
                try:
                    game_row, game_line = next(games)
                except StopIteration:
                    raise AuditFailure('game sidecar missing row') from None
                obj = json_object(game_line.encode('utf-8'))
                require(set(obj) == {'physical_row', 'game_id'} and type(obj['physical_row']) is int and
                        obj['physical_row'] == number == game_row, 'misaligned game sidecar row')
                game = valid_game(obj['game_id'])
            count += 1
            yield number, line, game
        if games is not None:
            try:
                next(games)
            except StopIteration:
                pass
            else:
                raise AuditFailure('game sidecar has extra row')
            require(count == sidecar['rows'], 'trusted game sidecar count mismatch')
    finally:
        if games is not None:
            games.close()


def raw_record(line):
    fields = [value.strip() for value in line.split('|')]
    require(len(fields) == 3, 'raw record must be FEN | score | result')
    require(re.fullmatch('[+-]?[0-9]+', fields[1]) is not None, 'invalid raw centipawn score')
    require(fields[2] in ('0', '0.0', '0.5', '1', '1.0', '?', '*', ''), 'invalid raw result')
    return fen_state(fields[0])


def audit(manifest_path, out):
    manifest_path = safe_path(manifest_path)
    out = safe_path(out)
    require(not out.exists(), 'new output directory required; preserve prior evidence')
    bindings = BoundInputs()
    manifest_hash = fingerprint(manifest_path)['sha256']
    manifest, manifest_bytes = bindings.load({'path': str(manifest_path), 'sha256': manifest_hash}, with_bytes=True)
    require(manifest.get('schema') == 1 and manifest.get('purpose') in ('actual-inputs', 'synthetic-fixture'), 'manifest schema/purpose')
    sources = manifest['source_maps']
    holds = manifest['holdouts']
    require(isinstance(sources, list) and sources, 'source mappings required')
    require(isinstance(holds, list) and {h['name'] for h in holds} == {'013', '014'} and len(holds) == 2,
            'distinct complete013/014 required')
    specs = [*sources, manifest['cohort'], manifest['filtered'], *holds]
    paths = [safe_path(s['path']) for s in specs]
    require(len(set(paths)) == len(paths), 'distinct data inputs required')
    require(all(out != p and out not in p.parents for p in [manifest_path, *paths]), 'output cannot contain input')
    source_literals = [s['record_source_literal'] for s in sources]
    require(all(isinstance(x, str) and x for x in source_literals) and len(set(source_literals)) == len(source_literals),
            'distinct exact source literals required')
    roles = [s.get('role') for s in sources]
    require(all(isinstance(r, str) and r and r not in ('cohort', 'filtered', 'holdout013', 'holdout014') for r in roles)
            and len(set(roles)) == len(roles), 'distinct source role names required')
    expected_source = 0
    for source in sources:
        lo, hi = source['first_source_row'], source['last_source_row']
        require(type(lo) is int and type(hi) is int and 1 <= lo <= hi, 'invalid physical source row range')
        expected_source += hi - lo + 1
    for spec in [manifest['cohort'], manifest['filtered'], *holds]:
        require(type(spec.get('rows')) is int and spec['rows'] > 0, 'trusted row count required')
    require(manifest['cohort']['rows'] == expected_source, 'cohort must cover complete selected source ranges')
    guard = Guard(out)
    for path, before in IMPLEMENTATIONS.items():
        require(fingerprint(Path(path)) == before, 'implementation changed after import')
    # Bind all inputs before constructing an index; final and consumed-byte checks
    # independently detect mutations after these initial complete-file hashes.
    for spec in specs:
        bindings.bind(spec)
        if spec.get('game_ids'):
            bindings.bind(spec['game_ids'])
    if manifest['purpose'] == 'actual-inputs':
        frozen = bindings.load(manifest['frozen_manifest'])
        require(frozen.get('status') == 'FROZEN_HASH_IDENTICAL', 'completed frozen-input receipt required')
        pinned = {str(safe_path(row['copy'])): row['sha256'] for row in frozen['files']}
        for spec in specs:
            require(pinned.get(str(safe_path(spec['path']))) == spec['sha256'], 'input differs from frozen receipt')
        for spec in holds:
            trusted = bindings.load(spec['trusted_metadata'])
            require(trusted.get('complete_scan') is True and trusted.get('shard') == spec['name'] and
                    trusted.get('rows') == spec['rows'] and trusted.get('sha256') == spec['sha256'],
                    'trusted complete holdout metadata mismatch')
    out.mkdir(parents=True)
    (out / 'manifest.json').write_bytes(manifest_bytes)
    result = {'schema': 1, 'status': 'BLOCKED', 'classification': 'UNPROVEN', 'complete': False,
              'evidence_scope': manifest['purpose'], 'format': 'Forge full-FEN selfplay text + result-aware JSONL',
              'limitations': ['Does not certify NPT/binpack decoding or training readiness.',
                              'Full-FEN syntax/state comparison does not establish chess legality.',
                              'Synthetic fixture PASS never clears actual native inputs.'],
              'manifest_sha256': manifest_hash, 'source_rows': 0, 'training_rows': 0, 'cohort_rows': 0,
              'row_counts': {}, 'missing_game_ids_by_role': {}, 'holdouts': {},
              'position_overlap_rows': 0, 'game_overlap_rows': 0, 'state_mismatch_rows': 0,
              'cohort_state_mismatch_rows': 0, 'training_state_mismatch_rows': 0,
              'unknown_game_id_rows': 0, 'examples': [],
              'position_key': 'expanded board + side to move; rights/clocks ignored for conservative exclusion',
              'game_policy': 'Only original row-aligned sidecars or exact source-provenance join; never inferred IDs',
              'guard': 'every4096 rows: floors/output quota; full workspace scan at most once per60s',
              'index_retention': 'retained without pruning', 'index_reservation_bytes': RESERVATION}
    conn = sqlite3.connect(out / 'audit.sqlite')
    conn.execute('PRAGMA temp_store=MEMORY')
    conn.execute('PRAGMA cache_size=-32768')
    conn.execute('PRAGMA threads=1')
    conn.executescript('CREATE TABLE source(origin TEXT,row INTEGER,fen TEXT NOT NULL,game TEXT,PRIMARY KEY(origin,row)) WITHOUT ROWID;'
                       'CREATE TABLE cohort(origin TEXT,row INTEGER,PRIMARY KEY(origin,row)) WITHOUT ROWID;'
                       'CREATE TABLE train(origin TEXT,row INTEGER,PRIMARY KEY(origin,row)) WITHOUT ROWID;'
                       'CREATE TABLE positions(key TEXT PRIMARY KEY) WITHOUT ROWID;'
                       'CREATE TABLE games(id TEXT PRIMARY KEY) WITHOUT ROWID;')

    def example(item):
        if len(result['examples']) < 20:
            result['examples'].append(item)

    try:
        for source in sources:
            role = source['role']
            count = selected = missing = 0
            for number, line, game in rows_with_games(source, bindings, guard):
                fen, key = raw_record(line)
                count += 1
                missing += game is None
                if source['first_source_row'] <= number <= source['last_source_row']:
                    conn.execute('INSERT INTO source VALUES(?,?,?,?)', (source['record_source_literal'], number, fen, game))
                    selected += 1
                if number % INTERVAL == 0:
                    conn.commit()
            require(selected == source['last_source_row'] - source['first_source_row'] + 1, 'missing source provenance row')
            result['row_counts'][role] = {'physical_rows': count, 'selected_rows': selected}
            result['missing_game_ids_by_role'][role] = missing
            result['source_rows'] += selected
            conn.commit()
        for role, table, spec in [('cohort', 'cohort', manifest['cohort']), ('filtered', 'train', manifest['filtered'])]:
            count = missing = mismatches = 0
            for number, line, supplied_game in rows_with_games(spec, bindings, guard):
                record = json_object(line.encode('utf-8'))
                require(isinstance(record.get('source'), str) and type(record.get('source_row')) is int and
                        record['source_row'] > 0, 'exact source and positive physical source_row required')
                origin, row = record['source'], record['source_row']
                source_row = conn.execute('SELECT fen,game FROM source WHERE origin=? AND row=?', (origin, row)).fetchone()
                require(source_row is not None, 'missing or unmapped source provenance row')
                if table == 'train':
                    require(conn.execute('SELECT 1 FROM cohort WHERE origin=? AND row=?', (origin, row)).fetchone() is not None,
                            'retained row absent from cohort')
                try:
                    conn.execute('INSERT INTO ' + table + ' VALUES(?,?)', (origin, row))
                except sqlite3.IntegrityError:
                    raise AuditFailure('duplicate ' + role + ' provenance row') from None
                fen, key = fen_state(record.get('fen'))
                # The exact provenance join can carry a real original game ID into
                # a derived row. Explicit derived IDs must agree; never fabricate.
                game = source_row[1]
                if 'game_id' in record:
                    require(valid_game(record['game_id']) == game, 'derived game ID differs from original source')
                if spec.get('game_ids') is not None:
                    require(supplied_game == game, 'derived sidecar game ID differs from original source')
                missing += game is None
                if fen != source_row[0]:
                    mismatches += 1
                    example({'role': role, 'source': origin, 'source_row': row, 'expected_fen': source_row[0], 'observed_fen': fen})
                if table == 'train':
                    conn.execute('INSERT OR IGNORE INTO positions VALUES(?)', (key,))
                    if game is not None:
                        conn.execute('INSERT OR IGNORE INTO games VALUES(?)', (game,))
                count += 1
                if count % INTERVAL == 0:
                    conn.commit()
            require(count == spec['rows'], 'trusted ' + role + ' row count mismatch')
            result['row_counts'][role] = count
            result['missing_game_ids_by_role'][role] = missing
            result['cohort_rows' if table == 'cohort' else 'training_rows'] = count
            result['cohort_state_mismatch_rows' if table == 'cohort' else 'training_state_mismatch_rows'] = mismatches
            result['state_mismatch_rows'] += mismatches
            if table == 'train':
                result['unknown_game_id_rows'] += missing
            conn.commit()
        require(conn.execute('SELECT count(*) FROM source LEFT JOIN cohort USING(origin,row) WHERE cohort.row IS NULL').fetchone()[0] == 0,
                'cohort missing selected source provenance rows')
        for spec in holds:
            count = missing = positions = games = 0
            for number, line, game in rows_with_games(spec, bindings, guard):
                fen, key = raw_record(line)
                pos_hit = conn.execute('SELECT 1 FROM positions WHERE key=?', (key,)).fetchone() is not None
                game_hit = game is not None and conn.execute('SELECT 1 FROM games WHERE id=?', (game,)).fetchone() is not None
                count += 1
                missing += game is None
                positions += pos_hit
                games += game_hit
                if pos_hit or game_hit:
                    example({'role': 'holdout' + spec['name'], 'physical_row': number, 'fen': fen,
                             'game_id': game, 'position_overlap': pos_hit, 'game_overlap': game_hit})
            require(count == spec['rows'], 'trusted holdout row count mismatch: ' + spec['name'])
            result['holdouts'][spec['name']] = {'rows': count, 'sha256': spec['sha256'],
                'trusted_complete': manifest['purpose'] == 'actual-inputs', 'position_overlap_rows': positions,
                'game_overlap_rows': games, 'missing_game_id_rows': missing}
            result['row_counts']['holdout' + spec['name']] = count
            result['missing_game_ids_by_role']['holdout' + spec['name']] = missing
            result['unknown_game_id_rows'] += missing
            result['position_overlap_rows'] += positions
            result['game_overlap_rows'] += games
        bindings.final()
        for path, before in IMPLEMENTATIONS.items():
            require(fingerprint(Path(path)) == before, 'implementation changed during audit')
        guard.check()
        failed = any(result[k] for k in ('position_overlap_rows', 'game_overlap_rows', 'state_mismatch_rows'))
        result['status'] = 'FAIL' if failed else 'UNVERIFIED' if result['unknown_game_id_rows'] else 'PASS'
        result['complete'] = True
    except (AuditFailure, ValueError, UnicodeError, sqlite3.IntegrityError) as error:
        result['status'] = 'FAIL'
        result['error'] = str(error)
    except (OSError, ResourceBlocked, sqlite3.Error) as error:
        result['status'] = 'BLOCKED'
        result['error'] = str(error)
    finally:
        conn.close()
    result['source_identities'] = bindings.before
    result['source_hashes'] = {path: value['sha256'] for path, value in bindings.before.items()}
    result['implementation_hashes'] = {path: value['sha256'] for path, value in IMPLEMENTATIONS.items()}
    result['index_bytes'] = (out / 'audit.sqlite').stat().st_size
    result['index_sha256'] = fingerprint(out / 'audit.sqlite')['sha256']
    with (out / 'audit.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--threads', required=True, type=int, choices=[1])
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT / 'pydeps'))
    import psutil
    proc = psutil.Process()
    require(proc.nice() == psutil.IDLE_PRIORITY_CLASS and len(proc.cpu_affinity()) <= 2, 'Idle, at most2 CPUs required')
    load = psutil.cpu_percent(interval=2, percpu=True)
    require(max(load[cpu] for cpu in proc.cpu_affinity()) < 70 and sum(load) / len(load) < 98,
            'host saturated; audit not started')
    try:
        result = audit(args.manifest, args.out)
    except (ValueError, KeyError, TypeError) as error:
        result = {'status': 'FAIL', 'complete': False, 'classification': 'UNPROVEN', 'error': str(error)}
    except (OSError, ResourceBlocked, sqlite3.Error) as error:
        result = {'status': 'BLOCKED', 'complete': False, 'classification': 'UNPROVEN', 'error': str(error)}
    print(json.dumps(result, indent=2))
    return 0 if result['status'] == 'PASS' else 1 if result['status'] == 'FAIL' else 2


if __name__ == '__main__':
    raise SystemExit(main())
