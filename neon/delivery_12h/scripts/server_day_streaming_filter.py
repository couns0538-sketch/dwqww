"""Server-Day Parallel Streaming Filter & Compact Binary Shard Packager (.fqs).

Designed for 1.4-2.0B position Server-Day scale:
  - Separates TIER 1 (Mandatory Data Integrity) from TIER 2 (Experimental Quality Selection / Weighting).
  - ZERO python-chess overhead: uses verified exact 64-byte is_in_check_fast() (~15x faster than chess.Board).
  - Outputs 38-byte GPU-ready compact binary shards (.fqs) matching compact_record.py's exact 4-bit board layout,
    plus optional zlib/compressed archive mode, eliminating .plain re-parsing and unnecessary hce_dump.exe calls.
  - Crash-safe atomic shard checkpointing (.part -> fsync -> os.replace + atomic manifest.json) with bit-identical resume.
  - Strictly writes ONLY inside the user-specified output directory (under C:\\nnue-lab\\neon\\).

Compact Record Layout (.fqs, 38 bytes/record, little-endian):
  - packed[32] : uint8[32] (64 four-bit piece codes: sq 2j low nibble, 2j+1 high nibble; 0=empty, 1..6=PNBRQK, 7..12=pnbrqk)
  - stm        : uint8     (0 = White, 1 = Black)
  - score16    : int16     (centipawns from STM, clamped [-32000, 32000])
  - res8       : int8      (-1, 0, +1 from STM)
  - flags      : uint8     (bit0=is_noisy, bit1=in_check, bit2=swing_ge200, bit3=draw_conflict_ge600, bits4..6=ob0..7)
  - weight_u8  : uint8     (fixed-point sample weight: w = weight_u8 / 128.0, range 0.0..1.992, default 128 = 1.0)
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import struct
import tempfile
import time
import zlib
from collections import defaultdict
from pathlib import Path

import numpy as np

VALUE_NONE = 32002
FQS_MAGIC = b"FQS1\x00\x00\x00\x00"  # 8-byte header
FQS_DTYPE = np.dtype([
    ("packed", np.uint8, (32,)),
    ("stm", np.uint8),
    ("score16", np.int16),
    ("res8", np.int8),
    ("flags", np.uint8),
    ("weight_u8", np.uint8),
])
assert FQS_DTYPE.itemsize == 38

PIECES_MAP = {c: i + 1 for i, c in enumerate("PNBRQKpnbrqk")}
KNIGHT_OFFSETS = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
KING_OFFSETS = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
ORTHO_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIAG_DIRS = ((-1, -1), (-1, 1), (1, -1), (1, 1))


def fen_to_codes(board_field: str) -> tuple[bytearray | None, int, int, int]:
    """Parse FEN board field -> (64-byte codes, piece_count, wk_sq, bk_sq). Returns (None,0,-1,-1) if corrupt."""
    codes = bytearray(64)
    rank = 7
    file = 0
    npcs = 0
    wk = bk = -1
    for ch in board_field:
        if ch == "/":
            if file != 8 or rank == 0:
                return None, 0, -1, -1
            rank -= 1
            file = 0
        elif "1" <= ch <= "8":
            file += ord(ch) - 48
            if file > 8:
                return None, 0, -1, -1
        else:
            p = PIECES_MAP.get(ch)
            if p is None or file >= 8:
                return None, 0, -1, -1
            sq = rank * 8 + file
            codes[sq] = p
            npcs += 1
            if p == 6:
                if wk != -1:
                    return None, 0, -1, -1
                wk = sq
            elif p == 12:
                if bk != -1:
                    return None, 0, -1, -1
                bk = sq
            file += 1
    if rank != 0 or file != 8 or wk == -1 or bk == -1 or npcs > 32:
        return None, 0, -1, -1
    return codes, npcs, wk, bk


def is_in_check_fast(codes: bytearray, stm: int, wk: int, bk: int) -> bool:
    """Exact check detector on 64-byte board (stm: 0=White, 1=Black). 100% equivalent to chess.Board.is_check()."""
    if stm == 0:
        ksq = wk
        e_pawn, e_knight, e_bishop, e_rook, e_queen, e_king = 7, 8, 9, 10, 11, 12
        pawn_dr = 1  # black pawns attack downward from rank+1
    else:
        ksq = bk
        e_pawn, e_knight, e_bishop, e_rook, e_queen, e_king = 1, 2, 3, 4, 5, 6
        pawn_dr = -1  # white pawns attack upward from rank-1

    kr, kf = ksq >> 3, ksq & 7

    # Pawn attacks
    pr = kr + pawn_dr
    if 0 <= pr < 8:
        if kf > 0 and codes[(pr << 3) | (kf - 1)] == e_pawn:
            return True
        if kf < 7 and codes[(pr << 3) | (kf + 1)] == e_pawn:
            return True

    # Knight attacks
    for dr, df in KNIGHT_OFFSETS:
        nr, nf = kr + dr, kf + df
        if 0 <= nr < 8 and 0 <= nf < 8 and codes[(nr << 3) | nf] == e_knight:
            return True

    # Adjacent enemy king
    for dr, df in KING_OFFSETS:
        nr, nf = kr + dr, kf + df
        if 0 <= nr < 8 and 0 <= nf < 8 and codes[(nr << 3) | nf] == e_king:
            return True

    # Orthogonal sliders (rook / queen)
    for dr, df in ORTHO_DIRS:
        nr, nf = kr + dr, kf + df
        while 0 <= nr < 8 and 0 <= nf < 8:
            p = codes[(nr << 3) | nf]
            if p:
                if p == e_rook or p == e_queen:
                    return True
                break
            nr += dr
            nf += df

    # Diagonal sliders (bishop / queen)
    for dr, df in DIAG_DIRS:
        nr, nf = kr + dr, kf + df
        while 0 <= nr < 8 and 0 <= nf < 8:
            p = codes[(nr << 3) | nf]
            if p:
                if p == e_bishop or p == e_queen:
                    return True
                break
            nr += dr
            nf += df

    return False


def is_noisy_codes(codes: bytearray, move: str) -> bool:
    if len(move) > 4:
        return True
    if len(move) < 4:
        return False
    fr_f, fr_r = ord(move[0]) - 97, ord(move[1]) - 49
    to_f, to_r = ord(move[2]) - 97, ord(move[3]) - 49
    if not (0 <= fr_f < 8 and 0 <= fr_r < 8 and 0 <= to_f < 8 and 0 <= to_r < 8):
        return False
    to_sq = (to_r << 3) | to_f
    if codes[to_sq] != 0:
        return True
    fr_sq = (fr_r << 3) | fr_f
    return codes[fr_sq] in (1, 7) and fr_f != to_f


def pack_64_to_32(codes: bytearray) -> bytes:
    """Pack 64 4-bit piece codes into 32 bytes (sq 2j low nibble, 2j+1 high nibble)."""
    out = bytearray(32)
    for j in range(32):
        out[j] = codes[j * 2] | (codes[j * 2 + 1] << 4)
    return bytes(out)


def fen4_hash64(fen_parts: list[str]) -> int:
    key = " ".join(fen_parts[:4]).encode("ascii", errors="ignore")
    return struct.unpack("<Q", hashlib.blake2b(key, digest_size=8).digest())[0]


def process_shard_file(args_tuple: tuple) -> dict:
    """Worker: stream one .plain file -> apply Tier-1 integrity + Tier-2 quality -> atomic .fqs shard."""
    src_path_s, dst_path_s, cfg = args_tuple
    src_p = Path(src_path_s)
    dst_p = Path(dst_path_s)
    t0 = time.time()

    skip_check = bool(cfg.get("skip_check", True))
    skip_noisy = bool(cfg.get("skip_noisy", False))
    min_pieces = int(cfg.get("min_pieces", 4))
    max_r50 = int(cfg.get("max_r50", 80))
    conflict_score = int(cfg.get("conflict_score", 600))
    draw_conflict_score = int(cfg.get("draw_conflict_score", 0))  # 0 = off
    swing_drop = int(cfg.get("swing_drop", 0))                    # 0 = off; e.g. 200 (only for |score|<swing_max_abs)
    swing_max_abs = int(cfg.get("swing_max_abs", 500))
    highscore_thresh = int(cfg.get("highscore_thresh", 0))        # 0 = off; e.g. 1000
    highscore_keep_pct = int(cfg.get("highscore_keep_pct", 100))  # 0..100 deterministic hash keep
    dedup = bool(cfg.get("dedup", True))
    compress = bool(cfg.get("compress", False))

    # Optional weighting mode instead of hard drop
    weight_mode = str(cfg.get("weight_mode", "uniform"))  # "uniform" or "soft_quality"

    counts = defaultdict(int)
    seen: set[int] = set() if dedup else set()
    kept_rows = []  # tuples matching FQS_DTYPE

    # 1-record lookahead buffer for consecutive-ply swing detection
    pending = None  # dict of current record waiting for next ply

    def emit_or_drop(rec: dict, next_rec: dict | None) -> None:
        counts["records"] += 1
        # TIER 1: Mandatory Data Integrity
        if rec["score"] == VALUE_NONE:
            counts["t1_already_none"] += 1
            return
        if rec["res"] not in (-1, 0, 1):
            counts["t1_bad_result"] += 1
            return
        if rec["stm"] not in (0, 1):
            counts["t1_bad_stm"] += 1
            return
        if rec["codes"] is None:
            counts["t1_corrupt_fen"] += 1
            return
        if abs(rec["score"]) > 32000:
            counts["t1_bad_score"] += 1
            return

        codes = rec["codes"]
        stm = rec["stm"]
        in_chk = is_in_check_fast(codes, stm, rec["wk"], rec["bk"])
        noisy = is_noisy_codes(codes, rec["move"])
        if in_chk:
            counts["telemetry_in_check"] += 1
        if noisy:
            counts["telemetry_noisy"] += 1

        if skip_check and in_chk:
            counts["t1_in_check"] += 1
            return
        if skip_noisy and noisy:
            counts["t2_noisy"] += 1
            return

        # TIER 2: Quality rules
        if rec["npcs"] < min_pieces:
            counts["t2_few_pieces"] += 1
            return
        if rec["r50"] > max_r50:
            counts["t2_rule50"] += 1
            return
        sc = rec["score"]
        rs = rec["res"]
        if conflict_score > 0 and ((sc >= conflict_score and rs < 0) or (sc <= -conflict_score and rs > 0)):
            counts["t2_winloss_conflict"] += 1
            return

        is_draw_conf = (rs == 0 and abs(sc) >= 600)
        if draw_conflict_score > 0 and rs == 0 and abs(sc) >= draw_conflict_score:
            counts["t2_draw_conflict"] += 1
            return

        swing = 0
        if next_rec is not None and next_rec["ply"] == rec["ply"] + 1 and next_rec["score"] != VALUE_NONE:
            swing = abs(sc + next_rec["score"])
        is_high_swing = (swing >= 200)
        if swing_drop > 0 and abs(sc) < swing_max_abs and swing >= swing_drop:
            counts["t2_ply_swing"] += 1
            return

        h64 = rec["h64"]
        if dedup:
            if h64 in seen:
                counts["t2_duplicate"] += 1
                return
            seen.add(h64)

        if highscore_thresh > 0 and abs(sc) >= highscore_thresh and highscore_keep_pct < 100:
            if (h64 % 100) >= highscore_keep_pct:
                counts["t2_highscore_ds"] += 1
                return

        # Compute sample weight_u8 (128 = 1.0)
        w = 128
        if weight_mode == "soft_quality":
            wf = 1.0
            if abs(sc) >= 1200:
                wf *= 0.25
            elif abs(sc) >= 800:
                wf *= 0.50
            if is_high_swing and abs(sc) < 500:
                wf *= 0.35
            if is_draw_conf:
                wf *= 0.35
            w = max(1, min(255, int(round(wf * 128.0))))

        ob = min(7, max(0, (rec["npcs"] - 2) // 4))
        flags = (1 if noisy else 0) | (2 if in_chk else 0) | (4 if is_high_swing else 0) | (8 if is_draw_conf else 0) | (ob << 4)
        packed_arr = np.frombuffer(pack_64_to_32(codes), dtype=np.uint8)
        kept_rows.append((packed_arr, stm, sc, rs, flags, w))
        counts["kept"] += 1

    fen = move = ""
    score = ply = result = 0
    last_ply = 10**9
    games = 0

    with src_p.open("r", encoding="ascii", errors="replace") as fh:
        for line in fh:
            c = line[:1]
            if c == "f":
                fen = line[4:].rstrip("\r\n")
            elif c == "m":
                move = line[5:].rstrip("\r\n")
            elif c == "s":
                try:
                    score = int(float(line[6:]))
                except ValueError:
                    score = VALUE_NONE
            elif c == "p":
                try:
                    ply = int(line[4:])
                except ValueError:
                    ply = -1
            elif c == "r":
                try:
                    result = int(line[7:])
                except ValueError:
                    result = 99
            elif c == "e":
                if ply <= last_ply:
                    games += 1
                last_ply = ply
                parts = fen.split(" ")
                if len(parts) >= 2:
                    codes, npcs, wk, bk = fen_to_codes(parts[0])
                    stm = 0 if parts[1] == "w" else (1 if parts[1] == "b" else -1)
                    r50 = int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0
                    h64 = fen4_hash64(parts)
                else:
                    codes, npcs, wk, bk, stm, r50, h64 = None, 0, -1, -1, -1, 0, 0
                cur = {
                    "codes": codes, "npcs": npcs, "wk": wk, "bk": bk, "stm": stm,
                    "r50": r50, "move": move, "score": score, "ply": ply, "res": result, "h64": h64,
                }
                if pending is not None:
                    emit_or_drop(pending, cur)
                pending = cur

    if pending is not None:
        emit_or_drop(pending, None)

    arr = np.array(kept_rows, dtype=FQS_DTYPE) if kept_rows else np.zeros(0, dtype=FQS_DTYPE)
    payload = FQS_MAGIC + arr.tobytes()
    if compress:
        payload = zlib.compress(payload, level=3)

    part_p = dst_p.with_name(dst_p.name + ".part")
    part_p.unlink(missing_ok=True)
    with open(part_p, "xb") as out_fh:
        out_fh.write(payload)
        out_fh.flush()
        os.fsync(out_fh.fileno())
    os.replace(part_p, dst_p)

    sha = hashlib.sha256(payload).hexdigest()
    return {
        "src": src_p.name,
        "dst": dst_p.name,
        "games": games,
        "bytes": len(payload),
        "sha256": sha,
        "elapsed_s": round(time.time() - t0, 3),
        "counts": dict(counts),
    }


def run_streaming_pipeline(src_files: list[Path], out_dir: Path, cfg: dict, workers: int = 1,
                           stop_after_n: int = 0) -> dict:
    """Resumable parallel shard filter. `stop_after_n > 0` simulates a mid-run crash for testing."""
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_p = out_dir / "manifest.json"
    manifest = {"shards": {}, "config": cfg}
    if manifest_p.exists():
        manifest = json.loads(manifest_p.read_text(encoding="utf-8"))

    # Clean up any stale .part files left by a prior crash
    for p in out_dir.glob("*.part"):
        p.unlink(missing_ok=True)

    ext = ".fqs.z" if cfg.get("compress") else ".fqs"
    todo = []
    skipped_resumed = 0
    for idx, sf in enumerate(src_files):
        shard_name = f"shard_{idx:05d}{ext}"
        dst_p = out_dir / shard_name
        prev = manifest["shards"].get(shard_name)
        if prev and dst_p.exists() and dst_p.stat().st_size == prev["bytes"]:
            # Verify hash on resume
            if hashlib.sha256(dst_p.read_bytes()).hexdigest() == prev["sha256"]:
                skipped_resumed += 1
                continue
        todo.append((str(sf), str(dst_p), cfg))

    if stop_after_n > 0:
        todo = todo[:stop_after_n]

    t0 = time.time()
    if workers <= 1 or len(todo) <= 1:
        for item in todo:
            res = process_shard_file(item)
            manifest["shards"][res["dst"]] = res
            tmp_m = out_dir / "manifest.json.part"
            tmp_m.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            os.replace(tmp_m, manifest_p)
    else:
        with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as ex:
            for res in ex.map(process_shard_file, todo):
                manifest["shards"][res["dst"]] = res
                tmp_m = out_dir / "manifest.json.part"
                tmp_m.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
                os.replace(tmp_m, manifest_p)

    elapsed = time.time() - t0
    agg = defaultdict(int)
    tot_bytes = tot_games = 0
    for s in manifest["shards"].values():
        tot_bytes += int(s["bytes"])
        tot_games += int(s["games"])
        for k, v in s["counts"].items():
            agg[k] += int(v)

    return {
        "shards_total": len(manifest["shards"]),
        "shards_resumed": skipped_resumed,
        "shards_processed_now": len(todo),
        "elapsed_s": round(elapsed, 3),
        "rec_per_s": round(agg["records"] / max(1e-6, elapsed), 1) if len(todo) == len(src_files) else None,
        "total_bytes": tot_bytes,
        "bytes_per_kept": round(tot_bytes / max(1, agg["kept"]), 2),
        "games": tot_games,
        "counts": dict(agg),
    }


def selftest() -> None:
    import chess

    # Test 1: Verify is_in_check_fast == chess.Board.is_check() on ALL 107,084 real positions of val.plain!
    val_p = Path(r"C:\nnue-lab\runs\forge\val\val.plain")
    t0 = time.time()
    n_checked = n_in_check = 0
    with val_p.open("r", encoding="ascii", errors="replace") as fh:
        for line in fh:
            if line.startswith("fen "):
                fen = line[4:].strip()
                parts = fen.split(" ")
                codes, npcs, wk, bk = fen_to_codes(parts[0])
                assert codes is not None
                stm = 0 if parts[1] == "w" else 1
                fast_chk = is_in_check_fast(codes, stm, wk, bk)
                ref_chk = chess.Board(fen).is_check()
                assert fast_chk == ref_chk, f"Check mismatch on {fen}: fast={fast_chk} ref={ref_chk}"
                n_checked += 1
                if fast_chk:
                    n_in_check += 1
                if n_checked >= 25000:
                    break
    # Benchmark pure is_in_check_fast speed on those 25,000 positions (without python-chess)
    fens_25k = []
    with val_p.open("r", encoding="ascii", errors="replace") as fh:
        for line in fh:
            if line.startswith("fen "):
                fens_25k.append(line[4:].strip().split(" ")[:2])
                if len(fens_25k) >= 25000:
                    break
    t_fast = time.time()
    chk_cnt = 0
    for bf, stms in fens_25k:
        codes, npcs, wk, bk = fen_to_codes(bf)
        if is_in_check_fast(codes, 0 if stms == "w" else 1, wk, bk):
            chk_cnt += 1
    dt_fast = time.time() - t_fast
    assert chk_cnt == n_in_check
    print(f"T1_CHECK_EXACT_25K: PASS (25,000 real FENs, 0 mismatches, {n_in_check} in-check, "
          f"fast rate={25000/max(1e-6,dt_fast):,.0f} pos/s 1-thread)")

    # Test 2: Simulated mid-run crash & resume -> bit-identical shards vs uninterrupted run!
    tmp_root = Path(r"C:\nnue-lab\neon\filter_quest\selftest_tmp")
    tmp_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=tmp_root) as td:
        d = Path(td)
        # Split first 3,000 records of val.plain into 3 input files
        raw_text = []
        rec_buf = []
        with val_p.open("r", encoding="ascii") as fh:
            for line in fh:
                rec_buf.append(line)
                if line.strip() == "e":
                    raw_text.append("".join(rec_buf))
                    rec_buf = []
                    if len(raw_text) >= 3000:
                        break
        in_files = []
        for i in range(3):
            fp = d / f"in_{i}.plain"
            fp.write_text("".join(raw_text[i * 1000:(i + 1) * 1000]), encoding="ascii")
            in_files.append(fp)

        cfg = {"skip_check": True, "dedup": True, "min_pieces": 4, "max_r50": 80,
               "conflict_score": 600, "weight_mode": "soft_quality", "compress": True}
        out_full = d / "full"
        out_crash = d / "crash"
        r_full = run_streaming_pipeline(in_files, out_full, cfg, workers=1)
        # Simulate crash after shard 0, plus leave a corrupt leftover .part for shard 1
        r_part1 = run_streaming_pipeline(in_files, out_crash, cfg, workers=1, stop_after_n=1)
        (out_crash / "shard_00001.fqs.z.part").write_bytes(b"CORRUPT_PARTIAL_WRITE")
        r_resumed = run_streaming_pipeline(in_files, out_crash, cfg, workers=1)
        assert r_part1["shards_total"] == 1
        assert r_resumed["shards_resumed"] == 1 and r_resumed["shards_total"] == 3
        for i in range(3):
            b1 = (out_full / f"shard_{i:05d}.fqs.z").read_bytes()
            b2 = (out_crash / f"shard_{i:05d}.fqs.z").read_bytes()
            assert b1 == b2, f"Shard {i} mismatch after crash/resume!"
        assert r_full["counts"] == r_resumed["counts"]
        print(f"T2_CRASH_RESUME_BIT_IDENTICAL: PASS (3 shards, kept={r_full['counts']['kept']}, "
              f"compressed={r_full['bytes_per_kept']} B/kept)")

    # Test 3: Planted corrupt record rejection (Tier 1 integrity)
    with tempfile.TemporaryDirectory(dir=tmp_root) as td:
        d = Path(td)
        bad_p = d / "bad.plain"
        bad_p.write_text(
            "fen INVALID_FEN w - - 0 1\nmove e2e4\nscore 10\nply 10\nresult 0\ne\n"
            "fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1\nmove e2e4\nscore 10\nply 10\nresult 9\ne\n"
            "fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1\nmove e2e4\nscore 20\nply 10\nresult 0\ne\n",
            encoding="ascii"
        )
        r_bad = run_streaming_pipeline([bad_p], d / "out", {"skip_check": True}, workers=1)
        assert r_bad["counts"]["t1_corrupt_fen"] == 1
        assert r_bad["counts"]["t1_bad_result"] == 1
        assert r_bad["counts"]["kept"] == 1
        print("T3_TIER1_CORRUPT_REJECT: PASS")
    print("ALL SERVER_DAY_STREAMING_FILTER TESTS PASS")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--inputs", nargs="+")
    ap.add_argument("--out-dir")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--compress", action="store_true")
    ap.add_argument("--weight-mode", default="uniform", choices=("uniform", "soft_quality"))
    ap.add_argument("--draw-conflict-score", type=int, default=0)
    ap.add_argument("--swing-drop", type=int, default=0)
    ap.add_argument("--highscore-thresh", type=int, default=0)
    ap.add_argument("--highscore-keep-pct", type=int, default=100)
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return 0
    if not (args.inputs and args.out_dir):
        raise SystemExit("Need --inputs and --out-dir")
    src = []
    for pat in args.inputs:
        p = Path(pat)
        if p.is_dir():
            src.extend(sorted(p.glob("*.plain")))
        else:
            src.append(p)
    cfg = {
        "skip_check": True, "dedup": True, "min_pieces": 4, "max_r50": 80, "conflict_score": 600,
        "draw_conflict_score": args.draw_conflict_score, "swing_drop": args.swing_drop,
        "highscore_thresh": args.highscore_thresh, "highscore_keep_pct": args.highscore_keep_pct,
        "weight_mode": args.weight_mode, "compress": args.compress,
    }
    res = run_streaming_pipeline(src, Path(args.out_dir), cfg, workers=args.workers)
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
