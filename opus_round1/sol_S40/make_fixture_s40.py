#!/usr/bin/env python3
"""Build the S40 synthetic fixture in the PC's real record format (Opus 5.5, 2026-10-27).

usage: python -I -B make_fixture_s40.py OUT_DIR --fen2bin EXE --hce-dump EXE [--seed 20261027]

Text lines are written exactly like forge_selfplay.py (`{fen} | {cp} | {result:.1f}\\n`, fen with en_passant="fen",
per-folder dedupe on the generator's 4-field FEN identity), then converted with the PC's own fen2bin.exe / hce_dump.exe
(copies), so .pos/.hce are the real FPOS/FHCE v1 formats. Every position not in check is recorded (simpler than the
generator's move-based filter; the merge tool does not care). Layout of OUT_DIR:
  main/forge_selfplay_001..003.txt  training shards (+ .md5 seals); 004..005 = the holdout (like 013/014)
  pos/, hce/                         fen2bin / hce_dump output for main 001..005 (+ .info)
  second/forge_selfplay_001.txt, 002.txt (sealed) + 003.txt.part (unsealed, unterminated tail; written by a
                                     "restarted" generator with a fresh hash DB, so it repeats positions of 001)
  second_hce/                        hce_dump output for the sealed second files
  second_db/forge_seen_hashes.sqlite3  a generator-style DB copy: files table with the committed offset of 003
  second_ids/                        sealed second files + row-aligned .gameid sidecars; ids/ = ID lists
  interleaved/forge_selfplay_001.txt two games interleaved row by row (the tripwire must fail closed)
  fixture_truth.json                 true games per row, planted cases, split points, md5 of every file
Planted cases (second folder): copy of a training game, prefix of a training game, exact copy of a holdout game,
a game that transposes into a holdout game AFTER the 001->002 file junction (its 001 rows must go as holdout_game),
a game touching the holdout in exactly one row, an identical-score holdout replay (fingerprint ID test), a
castling-only variant of a training row (identity ignores castling), and dup_second repeats in the .part.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sqlite3
import subprocess
import sys
from pathlib import Path

import chess

RESULTS = (0.0, 0.5, 1.0)


def gen_identity(fen):
    """forge_selfplay.position_hash: blake2b-128 of placement, turn, castling, e.p. (no clocks)."""
    return hashlib.blake2b(" ".join(fen.split()[:4]).encode("ascii"), digest_size=16).digest()


def score_of(board, salt):
    """Deterministic pseudo-eval (STM cp): material balance + a salted hash term; independent of PYTHONHASHSEED."""
    val = {chess.PAWN: 100, chess.KNIGHT: 300, chess.BISHOP: 320, chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0}
    m = sum(val[p.piece_type] * (1 if p.color == board.turn else -1) for p in board.piece_map().values())
    h = int.from_bytes(hashlib.sha256((board.board_fen() + "|" + salt).encode()).digest()[:4], "little")
    return max(-3000, min(3000, m + (h % 61) - 30))


class Game:
    def __init__(self, label, moves, result, salt):
        self.label, self.moves, self.result, self.salt = label, moves, result, salt

    def records(self):
        """(fen, cp) for every position after the 8 opening plies that is not in check (position before each move)."""
        b = chess.Board(); out = []
        for i, mv in enumerate(self.moves):
            if i >= 8 and not b.is_check():
                out.append((b.fen(en_passant="fen"), score_of(b, self.salt)))
            b.push(mv)
        if not b.is_check() and not b.is_game_over():
            out.append((b.fen(en_passant="fen"), score_of(b, self.salt)))
        return out


def random_moves(rng, start_moves=(), plies=40, board=None):
    b = chess.Board() if board is None else board
    for mv in start_moves:
        b.push(mv)
    out = list(start_moves)
    for _ in range(plies):
        legal = list(b.legal_moves)
        if not legal or b.is_game_over():
            break
        mv = rng.choice(legal); b.push(mv); out.append(mv)
    return out


def ucis(seq):
    return [chess.Move.from_uci(u) for u in seq]


def random_game(rng, label, salt=None):
    opening_plies = 8
    moves = random_moves(rng, (), opening_plies)
    moves = random_moves(rng, moves, rng.randint(16, 50))
    return Game(label, moves, rng.choice(RESULTS), salt or label)


class Folder:
    """Generator-style writer: rows of a game are appended in one batch; positions already seen are skipped."""

    def __init__(self):
        self.rows = []  # (line, game_label)
        self.seen = set()

    def add(self, game, fresh_db=False):
        seen = set() if fresh_db else self.seen
        kept = 0
        for fen, cp in game.records():
            h = gen_identity(fen)
            if h in seen:
                continue
            seen.add(h)
            self.rows.append((f"{fen} | {int(cp)} | {game.result:.1f}\n", game.label)); kept += 1
        return kept


def write_split(folder_rows, out_dir, splits, names, part_tail=None):
    """splits: row indices where a new file starts (len(names)-1 of them)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    edges = [0] + list(splits) + [len(folder_rows)]
    files = []
    for k, name in enumerate(names):
        chunk = folder_rows[edges[k]:edges[k + 1]]
        data = "".join(r[0] for r in chunk).encode("ascii")
        if name.endswith(".part") and part_tail:
            data += part_tail
        (out_dir / name).write_bytes(data)
        if not name.endswith(".part"):
            md5 = hashlib.md5(data).hexdigest()
            (out_dir / (name + ".md5")).write_bytes(f"{md5}  {name}\n".encode("ascii"))
        files.append({"name": name, "first_row": edges[k], "rows": len(chunk), "games": sorted({r[1] for r in chunk})})
    return files


def run(exe, *args, cwd=None):
    kw = {"creationflags": 0x40} if os.name == "nt" else {}
    p = subprocess.run([str(exe), *map(str, args)], cwd=cwd, capture_output=True, text=True, **kw)
    if p.returncode != 0:
        sys.exit(f"{exe} failed: {p.stdout} {p.stderr}")
    return p.stdout.strip()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--fen2bin", required=True)
    ap.add_argument("--hce-dump", required=True); ap.add_argument("--seed", type=int, default=20261027)
    a = ap.parse_args()
    out = Path(a.out)
    if out.exists() and any(out.iterdir()):
        sys.exit(f"{out} exists and is not empty")
    rng = random.Random(a.seed)

    # ---------------- main folder: training games, then holdout games (one generator, one hash DB)
    main_f = Folder(); training = [random_game(rng, f"m{i:03d}") for i in range(45)]
    for g in training:
        main_f.add(g)
    n_train_rows = len(main_f.rows)
    # planted holdout games: H1 (transposition target, knights after the opening), H2 (one-row touch target)
    H1_open = ucis(["a2a3", "a7a6", "h2h3", "h7h6", "b1c3", "b8c6", "b2b3", "b7b6"])
    H1_pre = ucis(["g2g3", "g7g6", "g1f3", "g8f6"])
    G1_open = ucis(["a2a3", "a7a6", "h2h3", "h7h6", "b2b3", "b7b6", "g2g3", "g7g6"])
    G1_pre = ucis(["g1f3", "g8f6", "b1c3", "b8c6"])
    bT = chess.Board()
    for mv in G1_open + G1_pre:
        bT.push(mv)
    C1 = random_moves(random.Random(a.seed + 11), (), 30, board=bT.copy())
    H1 = Game("H1", H1_open + H1_pre + C1, 1.0, "H1")
    H2_open = ucis(["d2d3", "d7d6", "e2e3", "e7e6", "b1c3", "b8c6", "a2a3", "a7a6"])
    H2_pre = ucis(["h2h3", "h7h6", "g1f3", "g8f6"])
    G2_open = ucis(["d2d3", "d7d6", "e2e3", "e7e6", "a2a3", "a7a6", "h2h3", "h7h6"])
    G2_pre = ucis(["g1f3", "g8f6", "b1c3", "b8c6"])
    bT2 = chess.Board()
    for mv in G2_open + G2_pre:
        bT2.push(mv)
    C2 = random_moves(random.Random(a.seed + 12), (), 30, board=bT2.copy())
    H2 = Game("H2", H2_open + H2_pre + C2, 0.0, "H2")
    holdout = [random_game(rng, f"h{i:03d}") for i in range(10)] + [H1] + [random_game(rng, f"h{i:03d}") for i in range(10, 16)] + [H2] + \
              [random_game(rng, f"h{i:03d}") for i in range(16, 22)]
    for g in holdout:
        main_f.add(g)
    # training files: games cross 001->002 and 002->003; the 003->004 junction is a game boundary (as on the PC)
    s1, s2 = n_train_rows // 3 + 7, 2 * n_train_rows // 3 + 5
    hold_rows = len(main_f.rows) - n_train_rows; s3 = n_train_rows + hold_rows // 2 + 3
    main_files = write_split(main_f.rows, out / "main", [s1, s2, n_train_rows, s3],
                             [f"forge_selfplay_00{k}.txt" for k in range(1, 6)])

    # ---------------- second folder (its own generator and hash DB)
    sec = Folder(); planted = {}
    def add2(game, tag=None, fresh_db=False):
        start = len(sec.rows); kept = sec.add(game, fresh_db)
        if tag:
            planted[tag] = {"label": game.label, "first_row": start, "rows": kept}
        return kept
    pool = [random_game(rng, f"s{i:03d}") for i in range(30)]
    src_copy_main = training[7]; src_prefix_main = training[12]; src_copy_hold = holdout[3]; src_ident = holdout[5]
    add2(pool[0]); add2(pool[1])
    add2(Game("S_COPY_MAIN", list(src_copy_main.moves), src_copy_main.result, "S_COPY_MAIN"), "copy_of_training_game")
    add2(pool[2])
    pre = src_prefix_main.moves[:14]
    add2(Game("S_PREFIX_MAIN", random_moves(random.Random(a.seed + 21), pre, 24), src_prefix_main.result, "S_PREFIX_MAIN"), "prefix_of_training_game")
    add2(pool[3])
    add2(Game("S_COPY_HOLD", list(src_copy_hold.moves), src_copy_hold.result, "S_COPY_HOLD"), "copy_of_holdout_game")
    add2(pool[4]); add2(pool[5])
    # the castling-only variant: a training row (fullmove >= 6) with castling rights removed, as a one-row group
    cast_src = None
    for line, lab in main_f.rows[:n_train_rows]:
        f = line.split(" | ")[0].split()
        if f[2] == "KQkq" and 6 <= int(f[5]) <= 9:
            cast_src = line; break
    f = cast_src.split(" | ")[0].split(); f[2] = "-"
    assert chess.Board(" ".join(f)).is_valid()
    cast_line = " ".join(f) + " | " + cast_src.split(" | ")[1] + " | " + cast_src.split(" | ")[2]
    # make sure the previous row (end of pool[5]) has a higher fullmove so the one-row group is its own game
    planted["castling_only_variant"] = {"label": "S_CASTLE", "first_row": len(sec.rows), "rows": 1, "source_training_line": cast_src.strip()}
    sec.rows.append((cast_line, "S_CASTLE")); sec.seen.add(gen_identity(cast_line.split(" | ")[0]))
    add2(pool[6]); add2(pool[7])
    add2(Game("S_IDENT_HOLD", list(src_ident.moves), src_ident.result, src_ident.salt), "identical_holdout_replay_same_scores")
    add2(pool[8])
    # the transposition game G1 straddles the 001 -> 002 junction: its pre-transposition rows end file 001
    add2(pool[9])
    g1 = Game("S_XFILE_HOLD", G1_open + G1_pre + C1, 1.0, "S_XFILE_HOLD")
    add2(g1, "transposes_into_holdout_after_file_junction")
    split_12 = planted["transposes_into_holdout_after_file_junction"]["first_row"] + 4  # P0..P3 in 001, T.. in 002
    add2(pool[10]); add2(pool[11])
    # G2: transposes into H2 at T2, then diverges at once (its first continuation move differs from H2's)
    r99 = random.Random(a.seed + 99); bd = bT2.copy()
    first = r99.choice([m for m in bd.legal_moves if m != C2[0] and not bd.gives_check(m)]); bd.push(first)
    g2 = Game("S_TOUCH1_HOLD", G2_open + G2_pre + [first] + random_moves(r99, (), 23, board=bd), 0.0, "S_TOUCH1_HOLD")
    add2(g2, "touches_holdout_in_one_row")
    main_idents = {(r[0].split()[0], r[0].split()[1]) for r in main_f.rows}
    for i in range(12, 22):
        add2(pool[i])
        if i == 13:
            # a training position with the side to move flipped (e.p. cleared): a DIFFERENT position, must be kept
            for line, lab in main_f.rows[:n_train_rows]:
                f = line.split(" | ")[0].split()
                if not 6 <= int(f[5]) <= 12:
                    continue
                bd2 = chess.Board(" ".join(f)); bd2.turn = not bd2.turn; bd2.ep_square = None
                if bd2.is_valid() and (f[0], "b" if f[1] == "w" else "w") not in main_idents:
                    break
            g = bd2.fen(en_passant="fen").split()
            flip_line = " ".join(g) + " | " + line.split(" | ")[1] + " | " + line.split(" | ")[2]
            planted["stm_flipped_variant_kept"] = {"label": "S_STMFLIP", "first_row": len(sec.rows), "rows": 1, "source_training_line": line.strip()}
            sec.rows.append((flip_line, "S_STMFLIP")); sec.seen.add(gen_identity(flip_line.split(" | ")[0]))
    split_23 = len(sec.rows)
    # 003.part: a restarted generator with a fresh DB repeats pool[0] (in 001) -> dup_second, then new games
    add2(Game("S_DUP_SECOND", list(pool[0].moves), pool[0].result, "S_DUP_SECOND"), "repeat_of_second_001_game_fresh_db", fresh_db=True)
    for i in range(22, 26):
        add2(pool[i], fresh_db=True)
    tail = b"rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1 | -1"  # unterminated: crash mid-write
    sec_files = write_split(sec.rows, out / "second", [split_12, split_23],
                            ["forge_selfplay_001.txt", "forge_selfplay_002.txt", "forge_selfplay_003.txt.part"], part_tail=tail)
    part_rows = len(sec.rows) - split_23
    part_committed_rows = part_rows - 5  # the "DB" committed all but the last 5 complete lines
    part_bytes = sum(len(r[0]) for r in sec.rows[split_23:split_23 + part_committed_rows])

    # ---------------- conversions with the PC's own tools (copies)
    (out / "pos").mkdir(); (out / "hce").mkdir(); (out / "second_hce").mkdir()
    conv = {}
    for k in range(1, 6):
        stem = f"forge_selfplay_00{k}"
        conv[stem + ".pos"] = run(a.fen2bin, out / "main" / f"{stem}.txt", out / "pos" / f"{stem}.pos")
        conv[stem + ".hce"] = run(a.hce_dump, out / "main" / f"{stem}.txt", out / "hce" / f"{stem}.hce")
    for k in (1, 2):
        stem = f"forge_selfplay_00{k}"
        conv["second_" + stem + ".hce"] = run(a.hce_dump, out / "second" / f"{stem}.txt", out / "second_hce" / f"{stem}.hce")

    # ---------------- generator-style DB copy with the committed offset of 003
    (out / "second_db").mkdir()
    con = sqlite3.connect(out / "second_db" / "forge_seen_hashes.sqlite3")
    con.executescript("CREATE TABLE hashes (hash BLOB PRIMARY KEY) WITHOUT ROWID; CREATE TABLE files (name TEXT PRIMARY KEY, bytes INTEGER NOT NULL, lines INTEGER NOT NULL);")
    for f in sec_files[:2]:
        p = out / "second" / f["name"]
        con.execute("INSERT INTO files VALUES (?,?,?)", (f["name"], p.stat().st_size, f["rows"]))
    con.execute("INSERT INTO files VALUES (?,?,?)", ("forge_selfplay_003.txt", part_bytes, part_committed_rows))
    con.commit(); con.close()

    # ---------------- explicit game IDs (sealed second files + sidecars) and ID lists
    (out / "second_ids").mkdir(); (out / "ids").mkdir()
    labels = [lab for _, lab in sec.rows]
    for f in sec_files[:2]:
        src = (out / "second" / f["name"]).read_bytes(); (out / "second_ids" / f["name"]).write_bytes(src)
        ids = labels[f["first_row"]:f["first_row"] + f["rows"]]
        (out / "second_ids" / (f["name"] + ".gameid")).write_bytes("".join(f"sp2-{x}\n" for x in ids).encode("ascii"))
    (out / "ids" / "holdout_ids.txt").write_bytes(b"# authoritative holdout game IDs (fixture)\nsp2-s002\nsp2-zzz-not-present\n")
    (out / "ids" / "main_ids.txt").write_bytes(b"# authoritative main game IDs (fixture)\nsp2-s004\n")

    # ---------------- interleaved text (tripwire)
    ga, gb = random_game(random.Random(a.seed + 41), "IA"), random_game(random.Random(a.seed + 42), "IB")
    ga.result, gb.result = 1.0, 0.0
    ra, rb = ga.records(), gb.records(); inter = []
    for x, y in zip(ra, rb):
        inter.append(f"{x[0]} | {x[1]} | 1.0\n"); inter.append(f"{y[0]} | {y[1]} | 0.0\n")
    (out / "interleaved").mkdir(); (out / "interleaved" / "forge_selfplay_001.txt").write_bytes("".join(inter).encode("ascii"))

    # ---------------- self-checks of the planted cases (the fixture must contain what it claims)
    def rows_of(folder_rows, label):
        return [r[0] for r in folder_rows if r[1] == label]
    xf = planted["transposes_into_holdout_after_file_junction"]
    assert xf["rows"] >= 6 and split_12 == xf["first_row"] + 4, xf
    t_board = bT.board_fen()
    assert sec.rows[split_12][0].split()[0] == t_board, "file 002 must start at the transposition point T"
    assert all(r[0].split()[0] != t_board for r in sec.rows[xf["first_row"]:split_12]), "pre-transposition rows must differ from T"
    h1_boards = {r.split()[0] + r.split()[1] for r in rows_of(main_f.rows, "H1")}
    assert t_board + " w" in {r.split()[0] + " " + r.split()[1] for r in rows_of(main_f.rows, "H1")}, "H1 must record T"
    assert not any((r[0].split()[0] + r[0].split()[1]) in h1_boards for r in sec.rows[xf["first_row"]:split_12]), "G1 pre rows in H1"
    t2 = bT2.board_fen()
    assert t2 + " w" in {r.split()[0] + " " + r.split()[1] for r in rows_of(main_f.rows, "H2")}, "H2 must record T2"
    ident_rows = rows_of(sec.rows, "S_IDENT_HOLD"); assert ident_rows == rows_of(main_f.rows, src_ident.label), "identical replay differs"
    assert planted["repeat_of_second_001_game_fresh_db"]["rows"] > 0

    truth = {"seed": a.seed, "main_files": main_files, "training_rows": n_train_rows, "holdout_rows": len(main_f.rows) - n_train_rows,
             "second_files": sec_files, "second_rows": len(sec.rows), "second_row_game": labels,
             "second_split_rows": [split_12, split_23], "part_unterminated_tail_bytes": len(tail),
             "part_committed": {"rows": part_committed_rows, "bytes": part_bytes}, "planted": planted,
             "interleaved_rows": len(inter), "converter_stdout": conv,
             "md5": {str(p.relative_to(out)).replace("\\", "/"): hashlib.md5(p.read_bytes()).hexdigest()
                     for p in sorted(out.rglob("*")) if p.is_file()}}
    (out / "fixture_truth.json").write_text(json.dumps(truth, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: truth[k] for k in ("training_rows", "holdout_rows", "second_rows", "second_split_rows", "part_committed", "interleaved_rows")}))
    print(json.dumps(planted, indent=1))


if __name__ == "__main__":
    main()
