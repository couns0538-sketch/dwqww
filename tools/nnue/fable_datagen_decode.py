#!/usr/bin/env python3
"""Reference decoder for the FGB1 self-play game files of `forge datagen` (job FB2-J2), independent of the engine:
python-chess replays every game from its start FEN and rebuilds the FPOS rows (packed boards, scores, meta) of the
kept records.

  decode  <in.fgb> <out.pos>            write the FPOS rows of the kept records (no .hce: that needs the engine's HCE)
  compare <in.fgb> <direct.pos>         exact comparison with the engine's direct `--pos` output (or `datagen convert`)
  info    <in.fgb>                      header, counts, per-game summary, legality of every move
  test    <forge.exe> <scratch dir>     run a tiny datagen with --pos, then compare + check the converter files

Format: see include/forge/datagen2.hpp. Checksum: FNV-1a 64 over everything before the 8-byte trailer.
"""
import os
import struct
import subprocess
import sys

import numpy as np

try:
    import chess
except ImportError:  # pragma: no cover
    chess = None

FLAGS = {"kept": 1, "in_check": 2, "noisy_pv": 4, "mate": 8, "score_cap": 16, "early": 32, "subsampled": 64, "gives_check": 128}
TERMINATIONS = ["checkmate", "stalemate", "insufficient", "repetition", "fifty", "max_ply", "adj_win", "adj_draw"]
SCORE_NONE = 32002


def fnv1a64(data):
    h = 14695981039346656037
    mask = 0xFFFFFFFFFFFFFFFF
    for b in memoryview(data):
        h = ((h ^ b) * 1099511628211) & mask
    return h


def read_fgb(path):
    data = open(path, "rb").read()
    if data[:4] != b"FGB1":
        raise SystemExit(f"{path}: not an FGB1 file")
    version, games, plies, records, seed, _reserved = struct.unpack_from("<IQQQQQ", data, 4)
    if version != 1:
        raise SystemExit(f"{path}: unsupported version {version}")
    stored = struct.unpack_from("<Q", data, len(data) - 8)[0]
    if fnv1a64(data[:-8]) != stored:
        raise SystemExit(f"{path}: checksum mismatch")
    pos = 48
    out = []
    for _ in range(games):
        fen_len = struct.unpack_from("<H", data, pos)[0]
        pos += 2
        fen = data[pos:pos + fen_len].decode("ascii")
        pos += fen_len
        result, term, opening, n = struct.unpack_from("<BBHH", data, pos)
        pos += 6
        arr = np.frombuffer(data, dtype=np.dtype([("move", "<u2"), ("score", "<i2"), ("flags", "u1")]), count=n, offset=pos)
        pos += 5 * n
        out.append({"fen": fen, "result": result, "termination": term, "opening": opening, "plies": arr})
    if pos != len(data) - 8:
        raise SystemExit(f"{path}: trailing bytes")
    total_plies = sum(len(g["plies"]) for g in out)
    total_records = sum(int((g["plies"]["flags"] & 1).sum()) for g in out)
    if total_plies != plies or total_records != records:
        raise SystemExit(f"{path}: header counts differ from the games")
    return {"games": out, "seed": seed, "plies": plies, "records": records}


def decode_move(board, code):
    frm, to, promo = code & 63, (code >> 6) & 63, (code >> 12) & 7
    move = chess.Move(frm, to, promotion=promo if promo else None)
    if move not in board.legal_moves:
        return None
    return move


def pack_board(board):
    codes = np.zeros(64, np.uint8)
    for sq, piece in board.piece_map().items():
        codes[sq] = piece.piece_type + (0 if piece.color else 6)
    return (codes[0::2] | (codes[1::2] << 4)).astype(np.uint8).tobytes()


def replay(fgb, text=False):
    """FPOS bytes (boards, scores, meta) of the kept records plus legality / termination checks."""
    rows, scores, metas, lines = [], [], [], []
    problems = []
    for gi, g in enumerate(fgb["games"]):
        board = chess.Board(g["fen"])
        for pi, p in enumerate(g["plies"]):
            code, score, flags = int(p["move"]), int(p["score"]), int(p["flags"])
            if pi < g["opening"] and (score != SCORE_NONE or flags != 0):
                problems.append(f"game {gi} ply {pi}: opening ply with score/flags")
            if flags & 1:
                if board.is_check():
                    problems.append(f"game {gi} ply {pi}: kept record in check")
                rows.append(pack_board(board))
                scores.append(score)
                metas.append((0 if board.turn else 1) | (g["result"] << 1))
                if text:
                    # Forge prints the en-passant square after every double push (FEN style), python-chess only
                    # when a capture is legal: ask python-chess for the FEN style.
                    lines.append(f"{board.fen(en_passant='fen')} | {score} | {g['result'] / 2:.1f}")
            move = decode_move(board, code)
            if move is None:
                problems.append(f"game {gi} ply {pi}: illegal move code {code} in {board.fen()}")
                break
            if (flags & 1) and (board.is_capture(move) or move.promotion):
                problems.append(f"game {gi} ply {pi}: kept record with a noisy best move")
            # flags are recorded for searched plies only (opening plies carry neither score nor flags)
            if pi >= g["opening"] and bool(flags & 2) != board.is_check():
                problems.append(f"game {gi} ply {pi}: in-check flag wrong")
            board.push(move)
        term = TERMINATIONS[g["termination"]]
        if term == "checkmate" and not board.is_checkmate():
            problems.append(f"game {gi}: termination checkmate but the final position is not checkmate")
        if term == "checkmate" and g["result"] != (0 if board.turn else 2):
            problems.append(f"game {gi}: checkmate result wrong")
        if term == "stalemate" and not board.is_stalemate():
            problems.append(f"game {gi}: termination stalemate but not stalemate")
        if term in ("adj_draw", "max_ply", "stalemate", "insufficient", "repetition", "fifty") and g["result"] != 1:
            problems.append(f"game {gi}: draw termination with a decisive result")
    n = len(rows)
    pos = b"FPOS" + struct.pack("<IQ", 1, n) + b"".join(rows) + np.asarray(scores, "<i2").tobytes() + np.asarray(metas, np.uint8).tobytes()
    return pos, "\n".join(lines) + ("\n" if lines else ""), problems


def cmd_info(path):
    fgb = read_fgb(path)
    print(f"{path}: games {len(fgb['games'])} plies {fgb['plies']} records {fgb['records']} seed {fgb['seed']} bytes {os.path.getsize(path)}")
    pos, _, problems = replay(fgb)
    terms = {}
    results = [0, 0, 0]
    for g in fgb["games"]:
        terms[TERMINATIONS[g["termination"]]] = terms.get(TERMINATIONS[g["termination"]], 0) + 1
        results[g["result"]] += 1
    print(f"terminations {terms} results(black,draw,white) {results} replay problems {len(problems)}")
    for p in problems[:10]:
        print("  " + p)
    return 0 if not problems else 1


def cmd_compare(path, direct_pos):
    fgb = read_fgb(path)
    pos, _, problems = replay(fgb)
    direct = open(direct_pos, "rb").read()
    same = pos == direct
    print(f"records {fgb['records']} replay problems {len(problems)} python-chess FPOS == direct FPOS: {same} ({len(pos)} vs {len(direct)} bytes)")
    for p in problems[:10]:
        print("  " + p)
    if not same and len(pos) == len(direct):
        first = next(i for i in range(len(pos)) if pos[i] != direct[i])
        print(f"  first difference at byte {first}")
    print("PASS" if same and not problems else "FAIL")
    return 0 if same and not problems else 1


def cmd_test(exe, scratch):
    os.makedirs(scratch, exist_ok=True)
    out = os.path.join(scratch, "pytest").replace("\\", "/")
    cmds = f"datagen --out {out} --games 6 --nodes 300 --hash 1 --random-plies 6 --random-plies-jitter 2 --temp-plies 2 --opening-eval-cap 400 --min-ply 10 --skip-prob 0.1 --seed 5 --pos --text --quiet\n" \
           f"datagen convert {out}.fgb {out}_conv text\nquit\n"
    r = subprocess.run([exe], input=cmds, capture_output=True, text=True)
    print(r.stdout.strip()[-600:])
    if r.returncode != 0 or "ERROR" in r.stdout:
        print("FAIL: engine run")
        return 1
    rc = cmd_compare(out + ".fgb", out + ".pos")
    conv_pos, conv_hce = open(out + "_conv.pos", "rb").read(), open(out + "_conv.hce", "rb").read()
    direct_pos, direct_hce = open(out + ".pos", "rb").read(), open(out + ".hce", "rb").read()
    conv_txt, direct_txt = open(out + "_conv.txt", "rb").read(), open(out + ".txt", "rb").read()
    fgb = read_fgb(out + ".fgb")
    _, py_text, _ = replay(fgb, text=True)
    text_same = py_text.encode() == direct_txt.replace(b"\r\n", b"\n")
    ok = conv_pos == direct_pos and conv_hce == direct_hce and conv_txt == direct_txt and text_same
    print(f"converter .pos == direct: {conv_pos == direct_pos}; .hce == direct: {conv_hce == direct_hce}; .txt == direct: {conv_txt == direct_txt}; "
          f"python text == direct text: {text_same}")
    rows = struct.unpack_from("<Q", direct_pos, 8)[0]
    print(f"rows {rows}, fgb bytes {os.path.getsize(out + '.fgb')}, pos+hce bytes {len(direct_pos) + len(direct_hce)}")
    print("PASS" if ok and rc == 0 else "FAIL")
    return 0 if ok and rc == 0 else 1


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    if chess is None:
        raise SystemExit("python-chess is required")
    cmd = sys.argv[1]
    if cmd == "info":
        sys.exit(cmd_info(sys.argv[2]))
    if cmd == "decode":
        fgb = read_fgb(sys.argv[2])
        pos, _, problems = replay(fgb)
        open(sys.argv[3], "wb").write(pos)
        print(f"wrote {sys.argv[3]} ({len(pos)} bytes), replay problems {len(problems)}")
        sys.exit(0 if not problems else 1)
    if cmd == "compare":
        sys.exit(cmd_compare(sys.argv[2], sys.argv[3]))
    if cmd == "test":
        sys.exit(cmd_test(sys.argv[2], sys.argv[3]))
    print(__doc__)
    sys.exit(2)


if __name__ == "__main__":
    main()
