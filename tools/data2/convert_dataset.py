#!/usr/bin/env python3
"""Sealed, resumable Forge-FEN conversion and explicit holdout exclusion.

IDEA_SOURCE: user20261030 contract; existing Forge A1 format/probe; MIT bulletformat schema.
No engine code, live trainer or source-data file is modified.
"""
from __future__ import annotations
import argparse, collections, hashlib, itertools, json, os, shutil, sqlite3, subprocess, sys, time, uuid
import copy, re, stat
from contextlib import ExitStack, contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'data'))
from forge_pos import PosReader, aligned_records, text_record
from forge_probe import ProbeClient
from filter_positions import disagreement
from bullet_records import encode, verify_record

RULES = ('holdout_game','holdout_position','duplicate','score_cap','result_disagreement','in_check','terminal','teacher_incomplete','bestmove_capture','bestmove_promotion','kept')
DISK_CHECK_ROWS = 1024
INDEX_BYTES_PER_KEY = 64  # Measured ~42.5 bytes/key, with allocation headroom.
PROBE_LOG_BYTES_PER_ROW = 2048  # Conservative estimate, including gzip framing/stderr allowance.
INDEX_LIFECYCLE = 'verified-disposable-v1'


def disk_guard(out, min_free_mb, phase, additional_bytes=0):
    required = min_free_mb * 1024 * 1024 + additional_bytes
    free = shutil.disk_usage(out).free
    if free < required:
        raise ValueError(f'free-space guard: {phase}; free={free}, required={required} bytes; use another volume, do not remove source data')


def row_count(path):
    if Path(path).suffix == '.pos':
        with PosReader(path) as reader: return len(reader)
    count = 0; last = b''
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            count += block.count(b'\n'); last = block[-1:]
    return count + bool(last and last != b'\n')


def disk_budget(args, chunks):
    source_rows = row_count(args.pos or args.input)
    remaining = max(0, min(source_rows, args.limit or source_rows) - sum(c['input_rows'] for c in chunks))
    holdout_rows = sum(row_count(p) for p in args.holdout)
    prior_rows = sum(row_count(p) for p in args.dedup_against)
    recovered_rows = sum(c['kept'] for c in chunks)
    keys = holdout_rows + (prior_rows + recovered_rows + remaining if not args.no_dedupe else 0)
    # Budget the full input text even for a bounded slice: no dependence on a
    # potentially unrepresentative average line size. IDs are <=256 characters,
    # not bytes; charge their entire UTF-8 file instead of assuming ASCII.
    text_bytes = Path(args.input).stat().st_size if remaining else 0
    game_id_bytes = Path(args.game_ids).stat().st_size if args.game_ids and remaining else 0
    probe_log_bytes = remaining * PROBE_LOG_BYTES_PER_ROW if not args.no_filters else 0
    output_bytes = text_bytes + game_id_bytes + remaining * (32 + 32) + probe_log_bytes
    if args.binpack_tool: output_bytes += text_bytes + remaining * 128
    game_index_bytes = sum(Path(p).stat().st_size + row_count(p) * INDEX_BYTES_PER_KEY for p in args.holdout_game_ids)
    return {'index_keys_upper_bound': keys, 'index_bytes_per_key': INDEX_BYTES_PER_KEY,
            'index_bytes_estimate': keys * INDEX_BYTES_PER_KEY + game_index_bytes + 1024 * 1024,
            'remaining_input_rows': remaining, 'output_bytes_estimate': output_bytes,
            'probe_log_bytes_estimate': probe_log_bytes,
            'reserve_bytes': args.min_free_mb * 1024 * 1024}


@contextmanager
def output_lock(out):
    """Serialize converter/pruner processes; the lock file is never removed."""
    path = out / '.converter.lock'
    if path.is_symlink(): raise ValueError('unsafe output lock symlink')
    fd = os.open(path, os.O_RDWR | os.O_CREAT | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    with os.fdopen(fd, 'r+b') as f:
        if not stat.S_ISREG(os.fstat(f.fileno()).st_mode): raise ValueError('unsafe output lock')
        if os.name == 'nt':
            import msvcrt
            if not os.fstat(f.fileno()).st_size: f.write(b'0'); f.flush()
            f.seek(0)
            try: msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError: raise ValueError('output is locked by another converter/pruner') from None
            try: yield
            finally: f.seek(0); msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            try: fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError: raise ValueError('output is locked by another converter/pruner') from None
            try: yield
            finally: fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def prune_owned_indexes(out, config):
    """Caller holds output_lock and has verified all retained sealed data."""
    if config.get('index_lifecycle') != INDEX_LIFECYCLE: return 0
    config_sha = sha(out / 'config.json'); removed_bytes = 0
    protected = {Path(item['path']).resolve() for item in config['inputs']}
    for attempt in sorted(out.glob('attempt_*')):
        if not re.fullmatch(r'attempt_[0-9a-f]{32}', attempt.name): continue
        if attempt.is_symlink(): raise ValueError('unsafe attempt directory symlink')
        marker = attempt / 'INDEX_OWNER.json'
        if not marker.exists(): continue  # Old, unmarked evidence is never removed.
        if marker.is_symlink(): raise ValueError('unsafe index ownership symlink')
        if json.loads(marker.read_text()) != {'schema': 1, 'attempt': attempt.name, 'config_sha256': config_sha}:
            raise ValueError('index ownership/config mismatch; refusing prune')
        for name in ('index.sqlite', 'index.sqlite-journal', 'index.sqlite-wal', 'index.sqlite-shm'):
            path = attempt / name
            if not path.exists() and not path.is_symlink(): continue
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or path.resolve() in protected:
                raise ValueError('unsafe disposable index path: ' + str(path))
            path.unlink(); removed_bytes += info.st_size
    return removed_bytes


def checked_counts(value):
    if not isinstance(value, dict) or set(value) - set(RULES) or any(type(n) is not int or n < 0 for n in value.values()):
        raise ValueError('invalid counts keys/types/values')
    return {k: value.get(k, 0) for k in RULES}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def identity(path):
    p = Path(path).resolve(strict=True)
    return {'path': str(p), 'bytes': p.stat().st_size, 'sha256': sha(p)}


def dump_new(path, obj):
    path = Path(path)
    pending = path.with_name(path.name + '.pending_' + uuid.uuid4().hex)
    with pending.open('x', encoding='utf8', newline='\n') as f:
        json.dump(obj, f, sort_keys=True, indent=2)
        f.write('\n'); f.flush(); os.fsync(f.fileno())
    os.link(pending, path)
    if os.name == 'posix':
        fd = os.open(path.parent, os.O_RDONLY)
        try: os.fsync(fd)
        finally: os.close(fd)


def key(record):
    return record.board + bytes((record.meta & 1,))


def canonical(record, fen):
    return f'{fen} | {record.score} | {("0.0", "0.5", "1.0")[record.meta >> 1]}\n'


def sources(args):
    if args.pos:
        with PosReader(args.pos) as r:
            yield from aligned_records(r, args.input, sidecar_format=args.sidecar_format)
    else:
        if args.sidecar_format != 'text':
            raise ValueError('FEN-only input requires --pos')
        with Path(args.input).open(encoding='utf8') as f:
            for line in f:
                yield text_record(line)


def games(path, count=None):
    if path is None:
        yield from itertools.repeat('')
        return
    with Path(path).open(encoding='utf8') as f:
        for line in f:
            s = line.rstrip('\r\n')
            if not s or len(s) > 256 or any(c in s for c in '\t\r\n'):
                raise ValueError('game IDs must be nonempty single-token lines of <=256characters')
            yield s


def load_holdouts(db, paths, game_paths, guard=lambda phase: None):
    counts = []
    if game_paths and len(game_paths) != len(paths):
        raise ValueError('each holdout needs one --holdout-game-ids path')
    for hi, path in enumerate(paths):
        n = 0
        gids = games(game_paths[hi] if game_paths else None)
        with ExitStack() as stack:
            reader = stack.enter_context(PosReader(path)) if Path(path).suffix == '.pos' else None
            text = None if reader else stack.enter_context(Path(path).open(encoding='utf8'))
            rows = iter(reader) if reader else (text_record(s)[0] for s in text)
            for r in rows:
                gid = next(gids, None)
                if gid is None:
                    raise ValueError('holdout game-ID sidecar truncated')
                db.execute('INSERT OR IGNORE INTO holdout VALUES(?)', (key(r),))
                if gid:
                    db.execute('INSERT OR IGNORE INTO holdout_games VALUES(?)', (gid,))
                n += 1
                if n % DISK_CHECK_ROWS == 0:
                    guard('loading holdout index')
            if game_paths and next(gids, None) is not None:
                raise ValueError('holdout game-ID sidecar has extra rows')
        counts.append({'path': str(Path(path).resolve()), 'rows': n})
        guard('loading holdout index')
    db.commit()
    return counts


def load_prior_training(db, paths, guard=lambda phase: None):
    """Seed the same exact-key dedup index from immutable prior kept shards."""
    sources = []; total_rows = 0
    for path in paths:
        count = 0
        with ExitStack() as stack:
            reader = stack.enter_context(PosReader(path)) if Path(path).suffix == '.pos' else None
            text = None if reader else stack.enter_context(Path(path).open(encoding='utf8'))
            rows = iter(reader) if reader else (text_record(s)[0] for s in text)
            for record in rows:
                db.execute('INSERT OR IGNORE INTO kept VALUES(?)', (key(record),))
                count += 1
                if count % DISK_CHECK_ROWS == 0:
                    guard('loading prior training index')
        sources.append({'path': path, 'rows': count}); total_rows += count
        guard('loading prior training index')
    db.commit()
    return {'sources': sources, 'rows_indexed': total_rows,
            'unique_keys': db.execute('SELECT COUNT(*) FROM kept').fetchone()[0],
            'identity': 'board32 plus STM; result, score, rights, EP and clocks excluded'}


def read_chunks(out, verify=True):
    chunks = []
    next_row = 0
    for i, p in enumerate(sorted(out.glob('chunk_*.json'))):
        if p.name != f'chunk_{i:06d}.json':
            raise ValueError('noncontiguous sealed chunks')
        chunk = json.loads(p.read_text())
        if type(chunk['start_row']) is not int or type(chunk['input_rows']) is not int or chunk['start_row'] != next_row or chunk['input_rows'] < 1:
            raise ValueError('noncontiguous source range')
        counts = checked_counts(chunk['counts'])
        if type(chunk['kept']) is not int or counts['kept'] != chunk['kept'] or sum(counts.values()) != chunk['input_rows']:
            raise ValueError('chunk waterfall/count mismatch')
        if not isinstance(chunk['files'], dict): raise ValueError('invalid files manifest')
        roles = [chunk[k] for k in ('text','bullet','provenance')]
        if len(set(roles)) != 3 or any(not isinstance(r, str) or r not in chunk['files'] for r in roles):
            raise ValueError('required data role absent from files manifest')
        if len({str(Path(r).parent) for r in roles}) != 1:
            raise ValueError('data roles must share one chunk directory')
        for rel, meta in chunk['files'].items():
            file = out / rel
            if not isinstance(rel, str) or Path(rel).is_absolute() or '..' in Path(rel).parts or file.resolve().parent.parent != out.resolve():
                raise ValueError('unsafe manifest path')
            if type(meta.get('bytes')) is not int or meta['bytes'] < 0 or not isinstance(meta.get('sha256'),str) or len(meta['sha256']) != 64:
                raise ValueError('invalid file metadata')
            if verify and (file.stat().st_size != meta['bytes'] or sha(file) != meta['sha256']):
                raise ValueError('sealed chunk hash mismatch: ' + rel)
        next_row += chunk['input_rows']
        chunks.append(chunk)
    return chunks


def verify_chunk_rows(out, chunks):
    count = 0
    for chunk in chunks:
        n = 0
        with (out/chunk['bullet']).open('rb') as binary, (out/chunk['text']).open(encoding='utf8') as txt, (out/chunk['provenance']).open(encoding='utf8') as prov:
            for line in txt:
                record, _ = text_record(line); verify_record(binary.read(32), record)
                if not prov.readline(): raise ValueError('provenance truncated')
                n += 1
            if binary.read(1) or prov.readline(): raise ValueError('extra records')
        if n != chunk['kept']: raise ValueError('chunk kept-count mismatch')
        count += n
    return count


def encode_binpack(args, chunkdir, guard):
    moves_path = chunkdir / 'bestmoves.txt'
    command = [args.binpack_tool, 'encode', '-' if moves_path.exists() else str(chunkdir/'rows.txt'), str(chunkdir/'rows.binpack')]
    if args.allow_transport_moves: command.append('--allow-transport-move')
    guard('before binpack encoding')
    with (chunkdir/'binpack.stdout').open('xb') as stdout, (chunkdir/'binpack.stderr').open('xb') as stderr:
        if not moves_path.exists():
            subprocess.run(command, stdout=stdout, stderr=stderr, check=True)
        else:
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr, text=True)
            try:
                with (chunkdir/'rows.txt').open(encoding='utf8') as rows, moves_path.open(encoding='utf8') as moves:
                    for i, pair in enumerate(itertools.zip_longest(rows, moves), 1):
                        row, move = pair
                        if row is None or move is None: raise ValueError('binpack bestmove sidecar row mismatch')
                        process.stdin.write(row.rstrip('\n') + ' | ' + move)
                        if i % DISK_CHECK_ROWS == 0: guard('streaming binpack output')
                process.stdin.close()
                if process.wait(): raise subprocess.CalledProcessError(process.returncode, command)
            finally:
                if process.poll() is None: process.terminate(); process.wait()
                process.stdin.close()
    guard('after binpack encoding')


def run(args):
    # Bind the actual reads to the exact resolved paths hashed here. Also retain
    # and recheck each caller's original path binding, including symlinks.
    args = copy.deepcopy(args)
    if args.chunk_rows < 1 or args.limit is not None and args.limit < 1:
        raise ValueError('positive chunk/limit required')
    if args.min_free_mb < 0: raise ValueError('min-free-mb cannot be negative')
    if not args.no_filters and not args.probe:
        raise ValueError('filtering requires --probe; use explicit --no-filters only for format qualification')
    if args.score_cap < 0 or args.disagreement_cp < 1 or args.nodes < 1:
        raise ValueError('invalid score/budget thresholds')
    if not args.no_filters and not args.shard_id:
        raise ValueError('production conversion requires explicit --shard-id; holdout013/014 cannot train')
    if args.shard_id is not None and (len(args.shard_id) != 3 or not args.shard_id.isdigit() or not 1 <= int(args.shard_id) <= 39):
        raise ValueError('shard identity must be001..039')
    if args.shard_id in ('013','014'):
        raise ValueError('holdout shard013/014 cannot be converted as training')
    if args.require_game_clearance and not args.shard_id:
        raise ValueError('accepted game clearance policy requires explicit nonholdout shard identity')
    inputs = []; bindings = []
    if args.binpack_tool and args.no_filters and not args.allow_transport_moves:
        raise ValueError('format-only binpack requires explicit --allow-transport-moves')
    if args.dedup_against and args.no_dedupe:
        raise ValueError('--dedup-against cannot be combined with --no-dedupe')
    for name in ('input','pos','game_ids','probe','binpack_tool','holdout','holdout_game_ids','dedup_against'):
        value = getattr(args,name)
        values = value if isinstance(value,list) else [value]
        pinned = []
        for p in values:
            if p:
                observed = identity(p); inputs.append(observed)
                bindings.append({'reference': os.path.abspath(p), 'resolved': observed['path']})
                pinned.append(observed['path'])
            else: pinned.append(p)
        setattr(args,name,pinned if isinstance(value,list) else pinned[0])
    config = {k: v for k, v in vars(args).items() if k not in ('out', 'resume', 'stop_after_chunks', 'command')}
    config['inputs'] = inputs
    config['input_bindings'] = bindings
    config['index_lifecycle'] = INDEX_LIFECYCLE
    dependency_dir = Path(__file__).resolve().parents[1] / 'data'
    config['tool_sha256'] = {p.name: sha(p) for p in [Path(__file__), Path(__file__).with_name('bullet_records.py'), *(dependency_dir/n for n in ('forge_pos.py','forge_probe.py','filter_positions.py'))]}
    out = Path(args.out)
    if not args.resume: out.mkdir(parents=True, exist_ok=False)
    with output_lock(out):
        if args.resume:
            if json.loads((out / 'config.json').read_text()) != config:
                raise ValueError('resume config/source/tool identity mismatch; old checkpoints require their frozen converter')
            if (out / 'COMPLETE.json').exists():
                result = verify(out)
                prune_owned_indexes(out, config)
                return result
        else: dump_new(out / 'config.json', config)
        return convert_locked(args, out, config, inputs, bindings)


def convert_locked(args, out, config, inputs, bindings):
    chunks = read_chunks(out)
    start = sum(c['input_rows'] for c in chunks)
    if args.resume:
        verify_chunk_rows(out, chunks)
        prune_owned_indexes(out, config)
    guard = lambda phase: disk_guard(out, args.min_free_mb, phase)
    guard('before index creation')
    budget = disk_budget(args, chunks)
    print(json.dumps({'disk_preflight': budget}), flush=True)
    disk_guard(out, args.min_free_mb, 'preflight index/output budget', budget['index_bytes_estimate'] + budget['output_bytes_estimate'])
    attempt = out / ('attempt_' + uuid.uuid4().hex)
    attempt.mkdir()
    dump_new(attempt / 'INDEX_OWNER.json', {'schema': 1, 'attempt': attempt.name, 'config_sha256': sha(out / 'config.json')})
    db = sqlite3.connect(attempt / 'index.sqlite')
    before = time.monotonic()
    total = collections.Counter({k: 0 for k in RULES})
    for c in chunks: total.update(c['counts'])
    try:
        db.execute('PRAGMA cache_size=-16384')
        # This index is disposable, never a recovery authority. Avoid a second
        # full-size rollback journal; every resume rebuilds from verified rows.
        db.execute('PRAGMA journal_mode=OFF')
        db.execute('PRAGMA synchronous=OFF')
        for table in ('kept', 'holdout'):
            db.execute(f'CREATE TABLE {table}(key BLOB PRIMARY KEY) WITHOUT ROWID')
        db.execute('CREATE TABLE holdout_games(id TEXT PRIMARY KEY) WITHOUT ROWID')
        holdout_counts = load_holdouts(db, args.holdout, args.holdout_game_ids, guard)
        prior_training = load_prior_training(db, args.dedup_against, guard)
        for c in chunks if not args.no_dedupe else []:
            with (out / c['text']).open(encoding='utf8') as f:
                for i, line in enumerate(f, 1):
                    db.execute('INSERT INTO kept VALUES(?)', (key(text_record(line)[0]),))
                    if i % DISK_CHECK_ROWS == 0:
                        guard('loading recovered training index')
        db.commit(); guard('after loading indexes')
        with ExitStack() as stack:
            probe = stack.enter_context(ProbeClient(args.probe, args.nodes, workdir=attempt / 'probe')) if not args.no_filters else None
            gids = games(args.game_ids)
            source = iter(sources(args))
            stack.callback(gids.close)
            stack.callback(source.close)
            for _ in range(start):
                if next(source, None) is None or next(gids, None) is None:
                    raise ValueError('source truncated while resuming')
            exhausted = False
            while not exhausted and (args.limit is None or start < args.limit):
                guard('before output chunk')
                chunkdir = out / ('data_' + uuid.uuid4().hex)
                chunkdir.mkdir()
                counts = collections.Counter(); consumed = 0; kept = 0
                with ExitStack() as files_stack:
                    txt = files_stack.enter_context((chunkdir / 'rows.txt').open('x', encoding='utf8', newline='\n'))
                    binary = files_stack.enter_context((chunkdir / 'rows.bullet').open('xb'))
                    provenance = files_stack.enter_context((chunkdir / 'provenance.tsv').open('x', encoding='utf8', newline='\n'))
                    bestmoves = files_stack.enter_context((chunkdir/'bestmoves.txt').open('x', encoding='utf8', newline='\n')) if args.binpack_tool and probe else None
                    for _ in range(min(args.chunk_rows, args.limit - start) if args.limit else args.chunk_rows):
                        if consumed and consumed % DISK_CHECK_ROWS == 0: guard('writing output chunk/index')
                        pair = next(source, None)
                        if pair is None:
                            exhausted = True
                            if args.game_ids and next(gids, None) is not None:
                                raise ValueError('input game-ID sidecar has extra rows')
                            break
                        gid = next(gids, None)
                        if gid is None: raise ValueError('input game-ID sidecar truncated')
                        r, fen = pair; row_index = start + consumed; consumed += 1
                        why = None; k = key(r); proof = None
                        if gid and db.execute('SELECT 1 FROM holdout_games WHERE id=?', (gid,)).fetchone(): why = 'holdout_game'
                        elif db.execute('SELECT 1 FROM holdout WHERE key=?', (k,)).fetchone(): why = 'holdout_position'
                        elif not args.no_dedupe and db.execute('SELECT 1 FROM kept WHERE key=?', (k,)).fetchone(): why = 'duplicate'
                        elif not args.no_filters and abs(r.score) > args.score_cap: why = 'score_cap'
                        elif not args.no_filters and disagreement(r, args.disagreement_cp, args.draw_disagreement_cp): why = 'result_disagreement'
                        if why is None and probe:
                            proof = probe.query(fen, 'filter', str(row_index))
                            if proof.get('fen') != fen or proof.get('nodes_limit') != args.nodes or proof.get('threads') != 1 or proof.get('hash_mb') != 1:
                                raise ValueError('native FEN/config mismatch')
                            if any(type(proof.get(k)) is not bool for k in ('in_check','terminal')):
                                raise ValueError('missing native state flags')
                            if proof.get('in_check'): why = 'in_check'
                            elif proof.get('terminal'): why = 'terminal'
                            elif proof.get('analyzed') is False:
                                if proof.get('analysis_status') != 'insufficient_budget' or proof.get('depth') != 0 or proof.get('score') is not None or proof.get('bestmove') is not None:
                                    raise ValueError('invalid incomplete native result')
                                why = 'teacher_incomplete'
                            else:
                                if proof.get('analyzed') is not True or not isinstance(proof.get('depth'), int) or proof['depth'] < 1 or any(type(proof.get(k)) is not bool for k in ('capture','promotion')):
                                    raise ValueError('invalid completed native result')
                                if proof['capture']: why = 'bestmove_capture'
                                elif proof['promotion']: why = 'bestmove_promotion'
                        if why:
                            counts[why] += 1
                            continue
                        binary.write(encode(r)); txt.write(canonical(r, fen)); provenance.write(f'{row_index}\t{gid}\n')
                        if bestmoves: bestmoves.write(proof['bestmove'] + '\n')
                        if not args.no_dedupe: db.execute('INSERT INTO kept VALUES(?)', (k,))
                        kept += 1
                    for f in (txt, binary, provenance, bestmoves):
                        if f is not None: f.flush(); os.fsync(f.fileno())
                if consumed == 0: break
                if args.binpack_tool: encode_binpack(args, chunkdir, guard)
                # Persist every sealed data file, including the native adapter's
                # output and logs, before publishing the commit receipt.
                for p in chunkdir.iterdir():
                    with p.open('rb') as f: os.fsync(f.fileno())
                if os.name == 'posix':
                    fd = os.open(chunkdir, os.O_RDONLY)
                    try: os.fsync(fd)
                    finally: os.close(fd)
                counts['kept'] = kept
                files = {str(p.relative_to(out)): {'bytes': p.stat().st_size, 'sha256': sha(p)} for p in sorted(chunkdir.iterdir())}
                chunk = {'start_row': start, 'input_rows': consumed, 'kept': kept, 'counts': dict(counts), 'text': str((chunkdir/'rows.txt').relative_to(out)), 'bullet': str((chunkdir/'rows.bullet').relative_to(out)), 'provenance': str((chunkdir/'provenance.tsv').relative_to(out)), 'files': files}
                db.commit()
                dump_new(out / f'chunk_{len(chunks):06d}.json', chunk)
                chunks.append(chunk); start += consumed; total.update(counts)
                print(json.dumps({'sealed_chunks': len(chunks), 'input_rows': start, 'counts': dict(total)}), flush=True)
                if args.stop_after_chunks and len(chunks) >= args.stop_after_chunks:
                    return {'status': 'CHECKPOINT', 'input_rows': start, 'counts': dict(total)}
        for item in inputs:
            if identity(item['path']) != item: raise ValueError('input changed during run')
        for binding in bindings:
            if str(Path(binding['reference']).resolve(strict=True)) != binding['resolved']:
                raise ValueError('input path binding changed during run')
        result = {'status': 'COMPLETE', 'input_rows': start, 'counts': dict(total), 'chunks': len(chunks), 'holdouts': holdout_counts, 'prior_training_index': prior_training, 'game_clearance': 'ACCEPTED_WHOLE_SHARD_SPLIT_013_014' if args.shard_id else 'FORMAT_ONLY_NO_SHARD_ID', 'shard_id': args.shard_id, 'game_id_exclusion': bool(args.game_ids and args.holdout_game_ids), 'elapsed_seconds_this_attempt': time.monotonic()-before, 'representation': 'bullet32 + exact aligned full-FEN/STM-score/White-result sidecar; raw bullet loses state', 'binpack': 'GENERATED' if args.binpack_tool else 'NOT_REQUESTED', 'chunk_receipts': {p.name:sha(p) for p in sorted(out.glob('chunk_*.json'))}}
        dump_new(out / 'COMPLETE.json', result)
        db.close()
        verify(out)
        prune_owned_indexes(out, config)
        return result
    finally: db.close()


def verify(out, binpack_tool=None):
    out = Path(out); chunks = read_chunks(out)
    config = json.loads((out/'config.json').read_text())
    wants_binpack = bool(config.get('binpack_tool'))
    count = verify_chunk_rows(out, chunks); decoded_chunks = 0; decoded_rows = 0
    for c in chunks:
        n = c['kept']
        binpack = (out / c['text']).with_name('rows.binpack')
        binpack_rel = str(binpack.relative_to(out))
        if wants_binpack and (binpack_rel not in c['files'] or not binpack.is_file()):
            raise ValueError('required binpack missing from sealed files')
        if wants_binpack and binpack_tool:
            process = subprocess.Popen([str(binpack_tool), 'decode', str(binpack)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                with (out/c['text']).open('rb') as expected:
                    for line in expected:
                        decoded = process.stdout.readline()
                        # Windows stdout may translate LF to CRLF. Normalize
                        # only that terminal transport pair; every record byte
                        # (including embedded CR and other whitespace) is exact.
                        if decoded.endswith(b'\r\n'): decoded = decoded[:-2] + b'\n'
                        if decoded != line:
                            raise ValueError('binpack native decode differs from exact FEN/score/result sidecar')
                    if process.stdout.read(1): raise ValueError('extra binpack decoded rows')
                stderr = process.stderr.read()
                if process.wait(): raise ValueError('binpack decoder failed: '+stderr.decode(errors='replace'))
                decoded_chunks += 1; decoded_rows += n
            finally:
                if process.poll() is None: process.terminate(); process.wait()
                process.stdout.close(); process.stderr.close()
    result = json.loads((out/'COMPLETE.json').read_text())
    prior_paths = config.get('dedup_against', [])
    if prior_paths:
        prior = result.get('prior_training_index', {})
        sources = prior.get('sources')
        if not isinstance(sources, list) or [s.get('path') for s in sources] != prior_paths or any(type(s.get('rows')) is not int or s['rows'] < 0 for s in sources):
            raise ValueError('prior training source accounting mismatch')
        if type(prior.get('rows_indexed')) is not int or prior['rows_indexed'] != sum(s['rows'] for s in sources):
            raise ValueError('prior training indexed row count mismatch')
        if type(prior.get('unique_keys')) is not int or not 0 <= prior['unique_keys'] <= prior['rows_indexed']:
            raise ValueError('prior training key count invalid')
    if result.get('binpack') != ('GENERATED' if wants_binpack else 'NOT_REQUESTED'):
        raise ValueError('summary/config binpack expectation mismatch')
    totals = collections.Counter({k: 0 for k in RULES})
    for c in chunks: totals.update(c['counts'])
    if result.get('status') != 'COMPLETE' or type(result.get('chunks')) is not int or result['chunks'] != len(chunks):
        raise ValueError('summary status/chunk-count mismatch')
    if checked_counts(result.get('counts')) != dict(totals):
        raise ValueError('summary aggregate counts mismatch')
    if 'chunk_receipts' in result and result['chunk_receipts'] != {p.name:sha(p) for p in sorted(out.glob('chunk_*.json'))}:
        raise ValueError('sealed chunk receipt changed')
    if type(result.get('input_rows')) is not int or result['input_rows'] != sum(c['input_rows'] for c in chunks) or count != result['counts'].get('kept', 0): raise ValueError('summary count mismatch')
    return {'status': 'PASS', 'rows': count, 'chunks': len(chunks), 'scope': 'all chunk hashes; every bullet32/sidecar row and record count', 'binpack_decode': 'PERFORMED' if decoded_chunks else 'NOT_REQUESTED_HASHES_ONLY', 'binpack_decoded_chunks': decoded_chunks, 'binpack_decoded_rows': decoded_rows}


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    v = sub.add_parser('verify'); v.add_argument('--out', required=True); v.add_argument('--binpack-tool')
    v.add_argument('--prune-indexes', action='store_true', help='After full verification, remove only marked disposable converter indexes; retain all source/output data and logs.')
    for command in ('convert', 'holdout-dedup'):
        c = sub.add_parser(command)
        c.add_argument('--input', required=True); c.add_argument('--pos'); c.add_argument('--sidecar-format', choices=('text','fen'), default='text'); c.add_argument('--out', required=True)
        c.add_argument('--game-ids'); c.add_argument('--shard-id'); c.add_argument('--holdout', action='append', default=[]); c.add_argument('--holdout-game-ids', action='append', default=[]); c.add_argument('--require-game-clearance', action='store_true')
        c.add_argument('--dedup-against', action='append', default=[], help='Prior kept rows.txt or FPOS input; repeat for all preceding training chunks. Counts as duplicate, never holdout.')
        c.add_argument('--limit', type=int); c.add_argument('--chunk-rows', type=int, default=100000); c.add_argument('--min-free-mb', type=int, default=20000); c.add_argument('--resume', action='store_true'); c.add_argument('--stop-after-chunks', type=int)
        c.add_argument('--probe'); c.add_argument('--nodes', type=int, default=1024); c.add_argument('--score-cap', type=int, default=3000); c.add_argument('--disagreement-cp', type=int, default=400); c.add_argument('--draw-disagreement-cp', type=int, default=800)
        c.add_argument('--binpack-tool'); c.add_argument('--allow-transport-moves', action='store_true')
        c.add_argument('--no-filters', action='store_true'); c.add_argument('--no-dedupe', action='store_true')
    return p


def main():
    a = parser().parse_args()
    if a.command == 'holdout-dedup':
        if not a.holdout: raise ValueError('holdout-dedup requires --holdout')
        a.no_filters = True
    if a.command == 'verify' and a.prune_indexes:
        out = Path(a.out)
        with output_lock(out):
            result = verify(out, a.binpack_tool)
            result['pruned_index_bytes'] = prune_owned_indexes(out, json.loads((out/'config.json').read_text()))
    else: result = verify(a.out, a.binpack_tool) if a.command == 'verify' else run(a)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__': main()
