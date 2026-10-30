#!/usr/bin/env python3
"""Sealed, resumable Forge-FEN conversion and explicit holdout exclusion.

IDEA_SOURCE: user20261030 contract; existing Forge A1 format/probe; MIT bulletformat schema.
No engine code, live trainer or source-data file is modified.
"""
from __future__ import annotations
import argparse, collections, hashlib, itertools, json, os, shutil, sqlite3, subprocess, sys, time, uuid
from contextlib import ExitStack
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'data'))
from forge_pos import PosReader, aligned_records, text_record
from forge_probe import ProbeClient
from filter_positions import disagreement
from bullet_records import encode, verify_record

RULES = ('holdout_game','holdout_position','duplicate','score_cap','result_disagreement','in_check','terminal','teacher_incomplete','bestmove_capture','bestmove_promotion','kept')


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


def load_holdouts(db, paths, game_paths):
    counts = []
    if game_paths and len(game_paths) != len(paths):
        raise ValueError('each holdout needs one --holdout-game-ids path')
    for hi, path in enumerate(paths):
        n = 0
        gids = games(game_paths[hi] if game_paths else None)
        reader = PosReader(path) if Path(path).suffix == '.pos' else None
        try:
            rows = iter(reader) if reader else (text_record(s)[0] for s in Path(path).open(encoding='utf8'))
            for r in rows:
                gid = next(gids, None)
                if gid is None:
                    raise ValueError('holdout game-ID sidecar truncated')
                db.execute('INSERT OR IGNORE INTO holdout VALUES(?)', (key(r),))
                if gid:
                    db.execute('INSERT OR IGNORE INTO holdout_games VALUES(?)', (gid,))
                n += 1
            if game_paths and next(gids, None) is not None:
                raise ValueError('holdout game-ID sidecar has extra rows')
        finally:
            if reader: reader.close()
        counts.append({'path': str(Path(path).resolve()), 'rows': n})
    db.commit()
    return counts


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
        for rel, meta in chunk['files'].items():
            file = out / rel
            if file.resolve().parent.parent != out.resolve():
                raise ValueError('unsafe manifest path')
            if verify and (file.stat().st_size != meta['bytes'] or sha(file) != meta['sha256']):
                raise ValueError('sealed chunk hash mismatch: ' + rel)
        next_row += chunk['input_rows']
        chunks.append(chunk)
    return chunks


def run(args):
    if args.chunk_rows < 1 or args.limit is not None and args.limit < 1:
        raise ValueError('positive chunk/limit required')
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
    inputs = [identity(args.input)]
    if args.binpack_tool and args.no_filters and not args.allow_transport_moves:
        raise ValueError('format-only binpack requires explicit --allow-transport-moves')
    for p in [args.pos, args.game_ids, args.probe, args.binpack_tool, *args.holdout, *args.holdout_game_ids]:
        if p: inputs.append(identity(p))
    config = {k: v for k, v in vars(args).items() if k not in ('out', 'resume', 'stop_after_chunks', 'command')}
    config['inputs'] = inputs
    dependency_dir = Path(__file__).resolve().parents[1] / 'data'
    config['tool_sha256'] = {p.name: sha(p) for p in [Path(__file__), Path(__file__).with_name('bullet_records.py'), *(dependency_dir/n for n in ('forge_pos.py','forge_probe.py','filter_positions.py'))]}
    out = Path(args.out)
    if args.resume:
        if json.loads((out / 'config.json').read_text()) != config:
            raise ValueError('resume config/source/tool identity mismatch')
        if (out / 'COMPLETE.json').exists():
            return verify(out)
    else:
        out.mkdir(parents=True, exist_ok=False)
        dump_new(out / 'config.json', config)
    chunks = read_chunks(out)
    start = sum(c['input_rows'] for c in chunks)
    attempt = out / ('attempt_' + uuid.uuid4().hex)
    attempt.mkdir()
    db = sqlite3.connect(attempt / 'index.sqlite')
    db.execute('PRAGMA cache_size=-16384')
    for table in ('kept', 'holdout'):
        db.execute(f'CREATE TABLE {table}(key BLOB PRIMARY KEY) WITHOUT ROWID')
    db.execute('CREATE TABLE holdout_games(id TEXT PRIMARY KEY) WITHOUT ROWID')
    holdout_counts = load_holdouts(db, args.holdout, args.holdout_game_ids)
    for c in chunks if not args.no_dedupe else []:
        with (out / c['text']).open(encoding='utf8') as f:
            for line in f:
                db.execute('INSERT INTO kept VALUES(?)', (key(text_record(line)[0]),))
    db.commit()
    before = time.monotonic()
    total = collections.Counter({k: 0 for k in RULES})
    for c in chunks: total.update(c['counts'])
    try:
        with ExitStack() as stack:
            probe = stack.enter_context(ProbeClient(args.probe, args.nodes, workdir=attempt / 'probe')) if not args.no_filters else None
            gids = games(args.game_ids)
            source = iter(sources(args))
            for _ in range(start):
                if next(source, None) is None or next(gids, None) is None:
                    raise ValueError('source truncated while resuming')
            exhausted = False
            while not exhausted and (args.limit is None or start < args.limit):
                if shutil.disk_usage(out).free < args.min_free_mb * 1024 * 1024:
                    raise ValueError('free-space guard: start another volume, do not remove source data')
                chunkdir = out / ('data_' + uuid.uuid4().hex)
                chunkdir.mkdir()
                counts = collections.Counter(); consumed = 0; kept = 0
                with ExitStack() as files_stack:
                    txt = files_stack.enter_context((chunkdir / 'rows.txt').open('x', encoding='utf8', newline='\n'))
                    binary = files_stack.enter_context((chunkdir / 'rows.bullet').open('xb'))
                    provenance = files_stack.enter_context((chunkdir / 'provenance.tsv').open('x', encoding='utf8', newline='\n'))
                    binpack_input = files_stack.enter_context((chunkdir/'binpack_input.txt').open('x', encoding='utf8', newline='\n')) if args.binpack_tool else None
                    for _ in range(min(args.chunk_rows, args.limit - start) if args.limit else args.chunk_rows):
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
                        if binpack_input:
                            binpack_input.write(canonical(r, fen).rstrip('\n') + (' | ' + proof['bestmove'] if proof else '') + '\n')
                        if not args.no_dedupe: db.execute('INSERT INTO kept VALUES(?)', (k,))
                        kept += 1
                    for f in (txt, binary, provenance, binpack_input):
                        if f is not None: f.flush(); os.fsync(f.fileno())
                if consumed == 0: break
                if args.binpack_tool:
                    command = [args.binpack_tool, 'encode', str(chunkdir/'binpack_input.txt'), str(chunkdir/'rows.binpack')]
                    if args.allow_transport_moves: command.append('--allow-transport-move')
                    with (chunkdir/'binpack.stdout').open('xb') as stdout, (chunkdir/'binpack.stderr').open('xb') as stderr:
                        subprocess.run(command, stdout=stdout, stderr=stderr, check=True)
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
        result = {'status': 'COMPLETE', 'input_rows': start, 'counts': dict(total), 'chunks': len(chunks), 'holdouts': holdout_counts, 'game_clearance': 'ACCEPTED_WHOLE_SHARD_SPLIT_013_014' if args.shard_id else 'FORMAT_ONLY_NO_SHARD_ID', 'shard_id': args.shard_id, 'game_id_exclusion': bool(args.game_ids and args.holdout_game_ids), 'elapsed_seconds_this_attempt': time.monotonic()-before, 'representation': 'bullet32 + exact aligned full-FEN/STM-score/White-result sidecar; raw bullet loses state', 'binpack': 'GENERATED' if args.binpack_tool else 'NOT_REQUESTED', 'chunk_receipts': {p.name:sha(p) for p in sorted(out.glob('chunk_*.json'))}}
        dump_new(out / 'COMPLETE.json', result)
        return result
    finally: db.close()


def verify(out, binpack_tool=None):
    out = Path(out); chunks = read_chunks(out)
    count = 0
    for c in chunks:
        n = 0
        with (out/c['bullet']).open('rb') as binary, (out/c['text']).open(encoding='utf8') as txt, (out/c['provenance']).open(encoding='utf8') as prov:
            for line in txt:
                r, fen = text_record(line); verify_record(binary.read(32), r)
                if not prov.readline(): raise ValueError('provenance truncated')
                n += 1
            if binary.read(1) or prov.readline(): raise ValueError('extra records')
        if n != c['kept']: raise ValueError('chunk kept-count mismatch')
        binpack = (out / c['text']).with_name('rows.binpack')
        if binpack.exists() and binpack_tool:
            process = subprocess.Popen([str(binpack_tool), 'decode', str(binpack)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                with (out/c['text']).open('rb') as expected:
                    for line in expected:
                        if process.stdout.readline() != line:
                            raise ValueError('binpack native decode differs from exact FEN/score/result sidecar')
                    if process.stdout.read(1): raise ValueError('extra binpack decoded rows')
                stderr = process.stderr.read()
                if process.wait(): raise ValueError('binpack decoder failed: '+stderr.decode(errors='replace'))
            finally:
                if process.poll() is None: process.terminate(); process.wait()
                process.stdout.close(); process.stderr.close()
        count += n
    result = json.loads((out/'COMPLETE.json').read_text())
    totals = collections.Counter({k: 0 for k in RULES})
    for c in chunks: totals.update(c['counts'])
    if result.get('status') != 'COMPLETE' or type(result.get('chunks')) is not int or result['chunks'] != len(chunks):
        raise ValueError('summary status/chunk-count mismatch')
    if checked_counts(result.get('counts')) != dict(totals):
        raise ValueError('summary aggregate counts mismatch')
    if 'chunk_receipts' in result and result['chunk_receipts'] != {p.name:sha(p) for p in sorted(out.glob('chunk_*.json'))}:
        raise ValueError('sealed chunk receipt changed')
    if type(result.get('input_rows')) is not int or result['input_rows'] != sum(c['input_rows'] for c in chunks) or count != result['counts'].get('kept', 0): raise ValueError('summary count mismatch')
    return {'status': 'PASS', 'rows': count, 'chunks': len(chunks), 'scope': 'all chunk hashes; every bullet32/sidecar row and record count', 'binpack_decode': 'PERFORMED_WHERE_PRESENT' if binpack_tool else 'NOT_REQUESTED_HASHES_ONLY'}


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    v = sub.add_parser('verify'); v.add_argument('--out', required=True); v.add_argument('--binpack-tool')
    for command in ('convert', 'holdout-dedup'):
        c = sub.add_parser(command)
        c.add_argument('--input', required=True); c.add_argument('--pos'); c.add_argument('--sidecar-format', choices=('text','fen'), default='text'); c.add_argument('--out', required=True)
        c.add_argument('--game-ids'); c.add_argument('--shard-id'); c.add_argument('--holdout', action='append', default=[]); c.add_argument('--holdout-game-ids', action='append', default=[]); c.add_argument('--require-game-clearance', action='store_true')
        c.add_argument('--limit', type=int); c.add_argument('--chunk-rows', type=int, default=100000); c.add_argument('--min-free-mb', type=int, default=256); c.add_argument('--resume', action='store_true'); c.add_argument('--stop-after-chunks', type=int)
        c.add_argument('--probe'); c.add_argument('--nodes', type=int, default=1024); c.add_argument('--score-cap', type=int, default=3000); c.add_argument('--disagreement-cp', type=int, default=400); c.add_argument('--draw-disagreement-cp', type=int, default=800)
        c.add_argument('--binpack-tool'); c.add_argument('--allow-transport-moves', action='store_true')
        c.add_argument('--no-filters', action='store_true'); c.add_argument('--no-dedupe', action='store_true')
    return p


def main():
    a = parser().parse_args()
    if a.command == 'holdout-dedup':
        if not a.holdout: raise ValueError('holdout-dedup requires --holdout')
        a.no_filters = True
    print(json.dumps(verify(a.out, a.binpack_tool) if a.command == 'verify' else run(a), sort_keys=True))


if __name__ == '__main__': main()
