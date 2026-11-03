"""Original synthetic counterexample to inferring original game IDs from rows."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import sys

import chess

from qc_core import DuplicateIndex
from run_policy import free_guard, new_directory, safe_path

ROOT = Path('D:/a14')
PREFIX = ('e4', 'e5', 'Nf3', 'Nc6', 'Bc4', 'Bc5', 'd3', 'Nf6', 'O-O', 'O-O')
CYCLES = {'X': ('Nh4', 'Ng4', 'Nf3', 'Nf6'), 'Y': ('Nc3', 'Ng4', 'Nb1', 'Nf6')}
WRITER = dict(path='C:/Users/Administrator/grok-pc/nnue/forge-nnue-tools/forge_selfplay.py',
              md5='0a7f225ae89ace5830b8840f17ada9d6',
              evidence='D:/a14/sep/WRITER_EVIDENCE.md',
              scope='inspected rules only; historical producer identity remains unverified')


@dataclass(frozen=True)
class Row:
    game_id: str
    ply: int
    fen: str
    score: int = 0
    result: float = 0.5


@dataclass(frozen=True)
class Game:
    rows: tuple[Row, ...]
    description: dict


@dataclass(frozen=True)
class Proof:
    report: dict
    h1: bytes
    h2: bytes


def four_fields(fen):
    fields = fen.split()
    if len(fields) != 6:
        raise ValueError('complete FEN required')
    return ' '.join(fields[0:4])


def dedup_id(fen):
    digest = hashlib.blake2b(digest_size=16)
    digest.update(four_fields(fen).encode('ascii'))
    return digest.digest()


def replay_game(game_id, cycle):
    if not cycle:
        raise ValueError('nonempty legal cycle required')
    board = chess.Board()
    moves, rows = [], []
    for token in PREFIX:
        move = board.parse_san(token)
        if move not in board.legal_moves:
            raise ValueError('illegal prefix move')
        moves.append(move.uci())
        board.push(move)
    step = 0
    while not board.is_repetition(3):
        if board.ply() >= 64 or board.is_game_over(claim_draw=False):
            raise ValueError('cycle failed to reach the specified repetition draw')
        move = board.parse_san(cycle[step % len(cycle)])
        if move not in board.legal_moves:
            raise ValueError('illegal cycle move')
        if board.is_check() or board.is_capture(move) or move.promotion:
            raise ValueError('fixture row is not a quiet noncheck sample')
        rows.append(Row(game_id, board.ply(), board.fen(en_passant='fen')))
        moves.append(move.uci())
        board.push(move)
        step += 1
    outcome = board.outcome(claim_draw=True)
    if outcome is None or outcome.termination is not chess.Termination.THREEFOLD_REPETITION or outcome.winner is not None:
        raise ValueError('verified actual-threefold draw required')
    return Game(tuple(rows), dict(game_id=game_id, moves_uci=moves, opening_plies=len(PREFIX),
                buffered_rows=len(rows), terminal_ply=board.ply(), terminal_fen=board.fen(en_passant='fen'),
                terminal_rule='claim at actual third occurrence, not a prospective claim',
                termination=outcome.termination.name, result_white=0.5,
                all_moves_legal=True, all_buffered_rows_quiet_noncheck=True))


def emit(games, prior):
    seen = set(prior)
    retained = []
    for game in games:
        for row in game.rows:
            identity = dedup_id(row.fen)
            if identity not in seen:
                seen.add(identity)
                retained.append(row)
    payload = ''.join(f'{row.fen} | {row.score:d} | {row.result:.1f}\n' for row in retained).encode('ascii')
    return retained, payload, seen


def construct(*, seed_unwanted=True):
    games = {name: replay_game(name, cycle) for name, cycle in CYCLES.items()}
    a, b = games['Y'].rows[:2]
    all_rows = games['X'].rows+games['Y'].rows
    all_keys = {four_fields(row.fen) for row in all_rows}
    all_hashes = {dedup_id(row.fen) for row in all_rows}
    if len(all_keys) != len(all_hashes):
        raise ValueError('synthetic digest collision')
    prior = all_hashes-{dedup_id(a.fen), dedup_id(b.fen)} if seed_unwanted else set()
    h1_rows, h1, final1 = emit([games['Y']], prior)
    h2_rows, h2, final2 = emit([games['X'], games['Y']], prior)
    board = chess.Board(a.fen)
    witness = chess.Move.from_uci('b1c3')
    legal = witness in board.legal_moves
    if legal:
        board.push(witness)
    exact = legal and board.fen(en_passant='fen') == b.fen
    index = DuplicateIndex()
    try:
        index.add('synthetic', 'train', a.fen)
        index.add('synthetic', 'val', b.fen)
        overlap = index.report('synthetic')
    finally:
        index.close()

    def history(original, rows, payload):
        buffered = sum(len(games[name].rows) for name in original)
        return dict(authentic_games=original, buffered_rows=buffered, emitted_rows=len(rows),
                    dropped_rows=buffered-len(rows), emitted_game_ids=[row.game_id for row in rows],
                    emitted_source_plies=[row.ply for row in rows],
                    md5=hashlib.md5(payload).hexdigest(), sha256=hashlib.sha256(payload).hexdigest())

    h1_ids = [row.game_id for row in h1_rows]
    h2_ids = [row.game_id for row in h2_rows]
    valid = (h1 == h2 and len(h1_rows) == len(h2_rows) == 2 and h1_ids != h2_ids and exact and
             all(key['train_val_shared_keys'] == 0 and key['key_fill_rate'] == 1.0 for key in overlap['keys'].values()))
    report = dict(schema=1, scope='synthetic_identity_information_loss', status='PASS' if valid else 'FAIL',
                  production_separation_status='UNVERIFIED', inspected_writer=WRITER,
                  assumptions=['Legal synthetic games and a shared synthetic initial seen state.',
                               'Opening prefix of ten plies is omitted; quiet cycle positions are buffered before their moves.',
                               'Score zero is an admitted fixture value, not a reconstructed engine evaluation.',
                               'No historical engine choices, configuration or shard history are reconstructed.',
                               'No claim is made that a particular real earlier history produced this initial seen state.'],
                  prefix_san=list(PREFIX), games={name: game.description for name, game in games.items()},
                  dedup_rule='BLAKE2b-128 of ASCII first four FEN fields; shared seen set; whole-game append order',
                  distinct_synthetic_keys=len(all_keys), collision_free_within_fixture=True,
                  initial_seen=dict(key_count=len(prior), serialized=False),
                  final_seen=dict(H1_key_count=len(final1), H2_key_count=len(final2), equal=final1 == final2, serialized=False),
                  histories=dict(H1=history(['Y'], h1_rows, h1), H2=history(['X', 'Y'], h2_rows, h2)),
                  same_row_bytes=h1 == h2, different_authentic_id_sequences=h1_ids != h2_ids,
                  observed_rows=dict(A=a.fen, B=b.fen, score_stm=0, result_white=0.5),
                  continuation=dict(move_uci=witness.uci(), legal_exact_full_fen=exact, ply_distance=b.ply-a.ply,
                                    halfmove_clock_delta=chess.Board(b.fen).halfmove_clock-chess.Board(a.fen).halfmove_clock,
                                    results_equal=a.result == b.result), position_overlap=overlap,
                  oracle=dict(chess_version=chess.__version__, module_path=chess.__file__))
    return Proof(report, h1, h2)


def file_hashes(path):
    path = safe_path(path)
    data = path.read_bytes()
    return dict(path=str(path), bytes=len(data), md5=hashlib.md5(data).hexdigest(), sha256=hashlib.sha256(data).hexdigest())


def publish(path, data):
    path = safe_path(path, write=True)
    free_guard(len(data)+1024*1024)
    pending = path.with_name(path.name+'.part')
    with pending.open('xb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    free_guard(1024*1024)
    pending.rename(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if Path(sys.executable).resolve() != (ROOT/'runtime/python/python.exe').resolve():
        raise ValueError('independent owned runtime required')
    proof = construct()
    if proof.report['status'] != 'PASS':
        raise ValueError('counterexample requirements failed')
    out = new_directory(args.out)
    report = dict(proof.report, generated=datetime.now().strftime('%Y-%m-%d %H:%M:%S Vienna'),
                  helper=file_hashes(Path(__file__)), oracle_file=file_hashes(Path(chess.__file__)))
    publish(out/'H1.synthetic.txt', proof.h1)
    publish(out/'H2.synthetic.txt', proof.h2)
    publish(out/'PROOF.json', (json.dumps(report, indent=2)+'\n').encode())
    readme = '''# Synthetic identity ambiguity

Status: PASS for this information-loss counterexample only. Production game
separation and training readiness remain UNVERIFIED. These tiny files are
synthetic proof artifacts, not training exports or copied production rows.

From the ordinary initial board, both games play e4 e5 Nf3 Nc6 Bc4 Bc5 d3 Nf6
O-O O-O. Call the resulting position A. X cycles Nh4 Ng4 Nf3 Nf6; Y cycles
Nc3 Ng4 Nb1 Nf6. Both stop at the actual third occurrence after two cycles,
at ply18. The oracle verifies every move and the claimed draw. Eight quiet
noncheck positions are buffered per game at plies10 through17. Score0 is an
admitted synthetic value, not an engine-search claim. B is Y's position after
its first Nc3, at ply11.

In RAM, initialize the shared seen set to the union of all buffered first-four-
field keys except A and B. This is four keys. No key/hash set is serialized.
H1 appends Y: it emits A then B, both from Y, dropping six of eight rows.
H2 appends X then Y: X emits A; Y emits B, dropping fourteen of sixteen rows.
Both final seen states are equal and contain six keys. All six fixture keys
have distinct 128-bit digests. The emitted full ASCII bytes, clocks, result and
score are identical between H1 and H2. Their MD5/SHA256 values are in PROOF.json.

Assign A to train and B to val. Shared six-field, four-field and board+side keys
are each zero with 2/2 valid keys (100% fill, no parse failures). A reaches B by
the legal move b1c3 with exact full-FEN and halfmove-clock consistency. Yet H1's
two rows belong to one original game while H2's belong to two original games.
Legal continuity therefore cannot identify the original boundary. Buffered
writing and zero position overlap do not remove this information loss.

Formally, this serialization maps two different original game-ID sequences to
the same observation. Any rule using only that observation must give the same
answer for both histories and hence cannot universally recover their different
IDs. This does not prove leakage or ambiguity for any particular real shard.
It assumes the specified synthetic initial seen state; no preceding production
history for that state is asserted. Actual historical engine choices and
configuration remain unknown. The inspected writer's actual-threefold stopping
rule, first-four-field dedup and row serialization motivate this model; source
agreement is not provenance of the real shards.

The negative control uses an empty initial seen set and does not produce the
same two-row observation. The illegal-move fixture is refused. Reproduce with
the owned runtime and tools/r14_identity_ambiguity.py --out NEW_OWNED_DIRECTORY,
using the recorded one-CPU Idle resource-admission command. Never reuse an output
directory. MANIFEST.json binds the proof artifacts; proof and test logs are
separate evidence, and independent review remains required.
'''
    publish(out/'README.md', readme.encode())
    files = [file_hashes(out/name) for name in ('H1.synthetic.txt', 'H2.synthetic.txt', 'PROOF.json', 'README.md')]
    manifest = dict(schema=1, scope=report['scope'], status='PASS', files=files,
                    helper=report['helper'], tests=file_hashes(ROOT/'tests/test_r14_identity_ambiguity.py'))
    publish(out/'MANIFEST.json', (json.dumps(manifest, indent=2)+'\n').encode())
    print(json.dumps(dict(status='PASS', scope=report['scope'], out=str(out), manifest=file_hashes(out/'MANIFEST.json'))))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
