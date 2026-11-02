#!/usr/bin/env python3
"""UNPROVEN. Forge PGNs (fastchess {+0.44/16 0.68s} comments) and/or forge_selfplay 'FEN | score | result'
lines -> quiet, deduped, shuffled 32-byte records (same REC as filter_lichess.py / train.py; score WHITE POV cp).
PGN: comment eval = mover's POV of the position BEFORE the move, at depth d; label that position, played move
= best move for quiet filter. Selfplay: score is STM POV -> flipped to White POV; result ignored (train.py uses score only).
Filters as data40m: not check, <=max-pieces, move not capture/promo, not game over, no mate, |cp| clipped to 3000.
Usage: nice -n 19 venv/bin/python convert_forge.py OUTDIR --pgn a.pgn ... --selfplay x.txt ... [--min-depth 10]"""
import os, re, sys, json, time, argparse, numpy as np, chess, chess.pgn
from pathlib import Path
from filter_lichess_rec import REC, encode_board
from records import record, selfplay_record, read_records, read_pgn_game, dumps
from result_codec import encode_result
from resource_policy import storage_guard
from filter_positions import low_priority
ap = argparse.ArgumentParser(); ap.add_argument('outdir'); ap.add_argument('--pgn', nargs='*', default=[])
ap.add_argument('--selfplay', nargs='*', default=[]); ap.add_argument('--min-depth', type=int, default=10)
ap.add_argument('--clip', type=int, default=3000); ap.add_argument('--max-pieces', type=int, default=30)
ap.add_argument('--val', type=float, default=0.01); ap.add_argument('--seed', type=int, default=1)
ap.add_argument('--max-load', type=float, default=4.0)
ap.add_argument('--keep-result', action='store_true')
ap.add_argument('--lichess', nargs='*', default=[])
ap.add_argument('--normalized', nargs='*', default=[])
a = ap.parse_args()
destination = Path(a.outdir)
partial = destination.with_name(destination.name + '.partial')
if os.path.lexists(destination) or os.path.lexists(partial): sys.exit('refusing existing output destination')
low_priority()
storage_guard(destination)
storage_guard(partial)
metadata = []
current_metadata = None
def throttle():
    return
EV = re.compile(r'^\s*([+-]?)(M?)(\d+(?:\.\d+)?)/(\d+)')
st = dict(games=0, moves=0, book_or_noeval=0, mate=0, shallow=0, check=0, pieces_gt_max=0, capture_promo=0,
          gameover=0, clipped=0, sp_lines=0, sp_bad=0, kept=0); out = []
def keep(b, w, mv):
    if b.is_check(): st['check'] += 1; return
    if len(b.piece_map()) > a.max_pieces: st['pieces_gt_max'] += 1; return
    if mv is not None and (b.is_capture(mv) or mv.promotion): st['capture_promo'] += 1; return
    if b.is_game_over(): st['gameover'] += 1; return
    if abs(w) > a.clip: st['clipped'] += 1; w = max(-a.clip, min(a.clip, w))
    encoded = encode_board(b, w)
    if a.keep_result:
        encoded['rsv'][0] = encode_result(current_metadata['has_result'], current_metadata['result_stm'])
        metadata.append(current_metadata)
    out.append(encoded)
throttle()
for f in a.pgn:
    fh = open(f, encoding='utf-8', errors='ignore')
    source_game = 0
    while True:
        g = read_pgn_game(fh) if a.keep_result else chess.pgn.read_game(fh)
        if g is None: break
        st['games'] += 1
        source_game += 1
        if st['games'] % 500 == 0: throttle()
        if g.headers.get('Variant', 'Standard') not in ('Standard', '') or g.headers.get('FEN') and 'SetUp' in g.headers and False: pass
        b = g.board()
        for source_ply, node in enumerate(g.mainline()):
            mv = node.move; st['moves'] += 1; m = EV.match(node.comment or '')
            if not m: st['book_or_noeval'] += 1
            elif m.group(2): st['mate'] += 1
            elif int(m.group(4)) < a.min_depth: st['shallow'] += 1
            else:
                cp = round(float(m.group(3)) * 100) * (-1 if m.group(1) == '-' else 1)
                if a.keep_result:
                    rw = {'1-0': 1, '0-1': -1, '1/2-1/2': 0, '*': None}[g.headers.get('Result', '*')]
                    current_metadata = record(b.fen(en_passant='fen'), cp, 'cp', rw, f,
                                              str(source_game) + ':' + str(source_ply), 'pgn', mv.uci(), node.comment, int(m.group(4)))
                keep(b, cp if b.turn else -cp, mv)
            b.push(mv)
for f in a.selfplay:
    for source_row, line in enumerate(open(f, encoding='utf-8-sig'), 1):
        if not line.strip() or line.startswith('#'): continue
        st['sp_lines'] += 1
        try: fen, sc, _ = [x.strip() for x in line.split('|')]; b = chess.Board(fen); s = int(sc)
        except Exception: st['sp_bad'] += 1; continue
        if not b.is_valid(): st['sp_bad'] += 1; continue
        if a.keep_result: current_metadata = selfplay_record(line, f, source_row)
        keep(b, s if b.turn else -s, None)   # selfplay already quiet-filtered by eligible_score
for kind, paths in [('lichess', a.lichess), ('normalized', a.normalized)]:
    for f in paths:
        for current_metadata in read_records(f, kind):
            b = chess.Board(current_metadata['fen'])
            if current_metadata['score_type'] == 'mate': st['mate'] += 1; continue
            sc = current_metadata['score_stm']
            mv = chess.Move.from_uci(current_metadata['best_move']) if current_metadata['best_move'] else None
            keep(b, sc if b.turn else -sc, mv)
if not out: sys.exit('no records')
arr = np.concatenate(out); st['kept'] = len(arr)
import signcheck; st['signcheck'] = signcheck.check(arr, n=1000)
key = arr.copy(); key['score'] = 0
if a.keep_result: key['rsv'] = 0
_, first = np.unique(np.ascontiguousarray(key).view(np.dtype((np.void, 32))), return_index=True)
st['dupes'] = len(arr) - len(first); indices = np.sort(first); arr = arr[indices]
if a.keep_result: metadata = [metadata[i] for i in indices]
indices = np.random.default_rng(a.seed).permutation(len(arr))
arr = arr[indices]; nv = max(1, int(round(len(arr) * a.val)))
if a.keep_result: metadata = [metadata[i] for i in indices]
metadata_bytes = sum(len(dumps(row).encode('utf-8')) + 1 for row in metadata) if a.keep_result else 0
storage_guard(partial, allowance=int(arr.nbytes) + metadata_bytes + 1024*1024)
partial.mkdir(parents=True, exist_ok=False)
arr[nv:].tofile(partial / 'train.bin'); arr[:nv].tofile(partial / 'val.bin')
if a.keep_result:
    for name, rows in [('train', metadata[nv:]), ('val', metadata[:nv])]:
        with open(partial / f'{name}.metadata.jsonl', 'x', encoding='utf-8', newline='\n') as fh:
            for row in rows: fh.write(dumps(row) + '\n')
s = arr['score'].astype(np.int32)
st.update(final=len(arr), train=len(arr)-nv, val=nv, mean=float(s.mean()), std=float(s.std()),
          abs_median=float(np.median(np.abs(s))), black_to_move=float(arr['stm'].mean()), min_depth=a.min_depth,
          sources=a.pgn + a.selfplay + a.lichess + a.normalized)
with open(partial / 'stats.json', 'x', encoding='utf-8') as fh:
    json.dump(st, fh, indent=1)
storage_guard(destination, allowance=0)
partial.rename(destination)
print(json.dumps(st, indent=1))
