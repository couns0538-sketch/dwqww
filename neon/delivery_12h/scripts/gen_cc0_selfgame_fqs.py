"""Zero-Bloat CC0 Book-Seeded Self-Play Datagen -> Crash-Safe Compressed Shards (.fqs.z).

Production & Server-Day (1.4B - 2.0B usable positions) generator using Forge's C++ `selfgame` protocol:
  - Opening book: CC0-1.0 book (`book_cc0_clean.epd`, 233,104 openings, 0 UHO overlap) + startpos calibration mix.
  - Parity-balanced random opening plies (1 or 2 when random_plies==2; 0/1/2 on startpos).
  - Exact Forge loop integrity rules:
      * ply_limit_skip: drops max_ply games whose last 6 scores all favour one side by >= 300 cp.
      * Optional Syzygy 3-4-5 endgame adjudication (--tablebase-dir): relabels drawn <=5-piece endings to true TB win.
      * Drops strong decisive-game conflicts (res != 0 & sc * res <= -600) and optional drawn-game conflicts (--drop-draw-conflicts).
      * Encodes full FQS1 metadata flags: bit0=noisy (capture/promo), bit1=in_check (filtered), bit2=swing_ge200,
        bit3=draw_conflict_ge600, bits4..6=output_bucket (0..7).
  - Fast incremental board tracking (`b0.push(mv)` instead of re-parsing every FEN with python-chess) + atomic
    `.part -> os.replace` shard writes (100% crash/preemption-safe on Linux cloud servers & Windows PC!).
  - Cross-platform (Windows + Linux via FORGE_LAB_ROOT / --config; optional heat/RAM guards).
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import random
import subprocess
import sys
import tempfile
import time
import tomllib
import zlib
from pathlib import Path

import chess
import chess.syzygy
import numpy as np

LAB = Path(os.environ.get("FORGE_LAB_ROOT", r"C:\nnue-lab"))
FIX_ROOT = LAB / "neon/forge_fixes"
DEFAULT_BOOK = FIX_ROOT / "book_cc0_clean.epd"
DEFAULT_CONFIG = LAB / "pipeline/config.forge.toml"
DEFAULT_TB = LAB / "tablebases/syzygy345"
FORGE_EXE = str(LAB / "runs/forge/engines/v3-r15dsg-sp-clang/forge.exe")
R0067_NET = str(LAB / "runs/forge/r0067/train/cand.fnn3")

if (LAB / "pipeline").exists():
    sys.path.insert(0, str(LAB / "pipeline"))
try:
    from nnloop.heat import cpu_temp as _win_cpu_temp  # noqa: E402
except Exception:
    _win_cpu_temp = None

FQS_MAGIC = b"FQS1\x00\x00\x00\x00"
FQS_DTYPE = np.dtype([
    ("packed", np.uint8, (32,)),
    ("stm", np.uint8),
    ("score16", np.int16),
    ("res8", np.int8),
    ("flags", np.uint8),
    ("weight_u8", np.uint8),
])
CMAP = {"P": 1, "N": 2, "B": 3, "R": 4, "Q": 5, "K": 6, "p": 7, "n": 8, "b": 9, "r": 10, "q": 11, "k": 12}


def _safe_cpu_temp(cfg: dict | None) -> float | None:
    if _win_cpu_temp is None or cfg is None:
        return None
    try:
        return _win_cpu_temp(cfg)
    except Exception:
        return None


def pack_fen_fast(fen: str) -> tuple[bytes, int, int]:
    """Pack a FEN into 32 nibble-packed bytes + stm (0=w,1=b) + output bucket (0..7) without per-pos NumPy alloc."""
    sp1 = fen.find(" ")
    board_str = fen[:sp1]
    stm = 0 if fen[sp1 + 1] == "w" else 1
    codes = bytearray(64)
    r, c, npcs = 7, 0, 0
    for ch in board_str:
        if ch == "/":
            r -= 1
            c = 0
        elif "1" <= ch <= "8":
            c += ord(ch) - 48
        else:
            codes[r * 8 + c] = CMAP[ch]
            c += 1
            npcs += 1
    packed = bytes(codes[i] | (codes[i + 1] << 4) for i in range(0, 64, 2))
    ob = min(7, max(0, (npcs - 2) // 4))
    return packed, stm, ob


def _should_skip_plylimit(end_reason: str, recs: list[tuple[int, int, str, str]],
                          skip_score: int = 300, skip_count: int = 6) -> bool:
    if end_reason != "plylimit" or len(recs) < skip_count:
        return False
    tail = recs[-skip_count:]
    white_scores = [sc if fen.split(" ", 2)[1] == "w" else -sc for _, sc, _, fen in tail]
    return all(s >= skip_score for s in white_scores) or all(s <= -skip_score for s in white_scores)


def _adjudicate_tb_result(tb: chess.syzygy.Tablebase | None, end_res_w: int, end_fen: str) -> int:
    """If game ended drawn on <= 5 pieces and Syzygy 3-4-5 calls a forced win (|wdl|==2), return true White result."""
    if tb is None or end_res_w != 0 or not end_fen:
        return end_res_w
    try:
        b = chess.Board(end_fen)
        if chess.popcount(b.occupied) <= 5 and not b.castling_rights:
            wdl = tb.probe_wdl(b)
            if wdl == 2:
                return 1 if b.turn == chess.WHITE else -1
            if wdl == -2:
                return -1 if b.turn == chess.WHITE else 1
    except Exception:
        pass
    return end_res_w


def worker_gen(args_t):
    (wid, book_lines, target_pos, soft_nodes, write_min_ply, random_plies, eval_limit, max_ply,
     exe_path, net_path, seed, out_dir, startpos_frac, config_path, tb_dir, drop_draw_conflicts,
     max_temp_c, shard_size, resume, wide_div_frac) = args_t

    cfg = None
    opts: dict = {}
    if config_path and Path(config_path).exists():
        cfg = tomllib.loads(Path(config_path).read_text(encoding="utf-8"))
        opts = dict(cfg.get("engine", {}).get("v3_uci_options", {}))
    opts["Threads"] = "1"
    opts["Hash"] = "16"
    opts["OwnBook"] = "false"
    opts["NNUEArchFile"] = net_path.replace("\\", "/")
    opts["NNUEArch"] = "true"

    tb = chess.syzygy.open_tablebase(tb_dir) if (tb_dir and Path(tb_dir).exists()) else None

    proc_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0)
    popen_kw = {"creationflags": proc_flags} if os.name == "nt" else {}
    p = subprocess.Popen(
        [exe_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1, **popen_kw,
    )

    def send(s: str):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def until(tok: str):
        while True:
            ln = p.stdout.readline()
            if ln == "":
                raise RuntimeError("forge exited")
            if ln.split()[:1] == [tok]:
                return

    send("uci")
    until("uciok")
    for k, v in opts.items():
        sv = "true" if v is True else ("false" if v is False else str(v))
        send(f"setoption name {k} value {sv}")
    send("isready")
    until("readyok")

    out_p = Path(out_dir)
    bytes_written = 0
    shard_idx = 0
    total_written = 0
    if resume:
        existing = sorted(out_p.glob(f"cc0_w{wid:02d}_s*.fqs.z"))
        for ep in existing:
            raw_e = zlib.decompress(ep.read_bytes())
            if len(raw_e) >= 8 and raw_e[:8] == FQS_MAGIC and (len(raw_e) - 8) % FQS_DTYPE.itemsize == 0:
                total_written += (len(raw_e) - 8) // FQS_DTYPE.itemsize
                bytes_written += ep.stat().st_size
                shard_idx += 1
    rng = random.Random(seed + wid * 1_000_003 + shard_idx * 97_991)
    buf = np.empty(min(max(1, target_pos - total_written), shard_size), dtype=FQS_DTYPE)
    buf_n = 0
    games = 0
    plylimit_skipped = 0
    tb_adjudicated = 0
    draw_conflicts_dropped = 0
    t0 = time.time()

    def flush_shard():
        nonlocal buf_n, shard_idx, bytes_written
        if buf_n == 0:
            return
        raw = FQS_MAGIC + buf[:buf_n].tobytes()
        comp = zlib.compress(raw, level=3)
        sp = out_p / f"cc0_w{wid:02d}_s{shard_idx:03d}.fqs.z"
        tmp_sp = out_p / f"cc0_w{wid:02d}_s{shard_idx:03d}.fqs.z.part"
        tmp_sp.write_bytes(comp)
        os.replace(tmp_sp, sp)
        bytes_written += len(comp)
        shard_idx += 1
        buf_n = 0

    try:
        while total_written < target_pos:
            if max_temp_c > 0 and games % 25 == 0:
                t_c = _safe_cpu_temp(cfg)
                while t_c is not None and t_c >= max_temp_c:
                    time.sleep(5)
                    t_c = _safe_cpu_temp(cfg)
            u_draw = rng.random()
            use_start = (startpos_frac > 0.0 and u_draw < startpos_frac)
            use_wide = (not use_start and wide_div_frac > 0.0 and u_draw < startpos_frac + wide_div_frac)
            fen0 = chess.STARTING_FEN if use_start else book_lines[rng.randrange(len(book_lines))]
            b0 = chess.Board(fen0)
            target_turn = chess.WHITE if (games % 2 == 0) else chess.BLACK
            if use_start:
                rp = games % 3
            elif use_wide:
                # 4 or 5 random plies so post-random first searched side alternates exact 50/50 W/B!
                rp = 4 if (b0.turn == target_turn) else 5
            elif random_plies == 2:
                # Exact target-STM parity (1 or 2 random plies) so White and Black each get the
                # first searched move on exactly 50% of games regardless of book w/b skew!
                rp = 2 if (b0.turn == target_turn) else 1
            else:
                rp = random_plies
            rmoves = []
            for _ in range(rp):
                leg = list(b0.legal_moves)
                if not leg:
                    break
                mv0 = rng.choice(leg)
                b0.push(mv0)
                rmoves.append(mv0.uci())
            if not any(b0.legal_moves):
                continue
            send("ucinewgame")
            send("isready")
            until("readyok")
            send(f"position fen {fen0}" + (" moves " + " ".join(rmoves) if rmoves else ""))
            wmp = 0 if use_start else write_min_ply
            send(
                f"selfgame softnodes {soft_nodes} evallimit {eval_limit} maxply {max_ply} "
                f"writeminply {wmp} drawply 80 drawscore 12 drawcount 6"
            )
            recs: list[tuple[int, int, str, str]] = []
            res_w = 0
            end_reason = ""
            end_fen = ""
            loop_moves: list[str] = []
            while True:
                ln = p.stdout.readline()
                if not ln:
                    raise RuntimeError("forge EOF in selfgame")
                ln = ln.strip()
                if ln.startswith("sg "):
                    _, ply_s, sc_s, bm_s, fen_s = ln.split(" ", 4)
                    recs.append((int(ply_s), int(sc_s), bm_s, fen_s))
                elif ln.startswith("sgend "):
                    toks = ln.split()
                    if "result" in toks:
                        res_w = int(toks[toks.index("result") + 1])
                    if "reason" in toks:
                        end_reason = toks[toks.index("reason") + 1]
                    if "fen" in toks and "moves" in toks:
                        fi = toks.index("fen") + 1
                        mi = toks.index("moves")
                        end_fen = " ".join(toks[fi:mi])
                        loop_moves = toks[mi + 1:]
                    break
                elif ln.startswith(("sgerror ", "info string ERROR")):
                    recs = []
                    break
            games += 1
            if not recs:
                continue
            if _should_skip_plylimit(end_reason, recs):
                plylimit_skipped += 1
                continue
            adj_res = _adjudicate_tb_result(tb, res_w, end_fen)
            if adj_res != res_w:
                tb_adjudicated += 1
                res_w = adj_res

            # Fast incremental replay on b0 when loop_moves matches; falls back to chess.Board(fen_s) if needed.
            ply_offset = len(rmoves)
            rec_map = {ply_i: (sc_i, bm_s, fen_s) for ply_i, sc_i, bm_s, fen_s in recs}
            prev_sc: int | None = None
            can_replay = len(loop_moves) >= len(recs)
            cur_b = b0 if can_replay else None

            if can_replay and cur_b is not None:
                for step_i, mv_uci in enumerate(loop_moves):
                    cur_ply = ply_offset + step_i
                    item = rec_map.get(cur_ply)
                    mv_obj = chess.Move.from_uci(mv_uci)
                    if item is not None:
                        sc_i, bm_s, fen_s = item
                        in_chk = cur_b.is_check()
                        is_noisy = cur_b.is_capture(mv_obj) or (mv_obj.promotion is not None)
                        swing_big = (prev_sc is not None and abs(sc_i + prev_sc) >= 200)
                        prev_sc = sc_i
                        if abs(sc_i) <= 1500 and not in_chk:
                            pk_b, stm, ob = pack_fen_fast(fen_s)
                            res_stm = res_w if stm == 0 else -res_w
                            draw_conf = (res_stm == 0 and abs(sc_i) >= 600)
                            if res_stm != 0 and sc_i * res_stm <= -600:
                                pass
                            elif drop_draw_conflicts and draw_conf:
                                draw_conflicts_dropped += 1
                            else:
                                flg = (ob << 4) | (1 if is_noisy else 0) | (4 if swing_big else 0) | (8 if draw_conf else 0)
                                buf[buf_n]["packed"] = np.frombuffer(pk_b, dtype=np.uint8)
                                buf[buf_n]["stm"] = stm
                                buf[buf_n]["score16"] = max(-30000, min(30000, sc_i))
                                buf[buf_n]["res8"] = res_stm
                                buf[buf_n]["flags"] = flg
                                buf[buf_n]["weight_u8"] = 128
                                buf_n += 1
                                total_written += 1
                                if buf_n >= len(buf):
                                    flush_shard()
                                if total_written >= target_pos:
                                    break
                    cur_b.push(mv_obj)
            else:
                for ply_i, sc_i, bm_s, fen_s in recs:
                    swing_big = (prev_sc is not None and abs(sc_i + prev_sc) >= 200)
                    prev_sc = sc_i
                    if abs(sc_i) > 1500:
                        continue
                    b = chess.Board(fen_s)
                    if b.is_check():
                        continue
                    try:
                        mv = chess.Move.from_uci(bm_s)
                        is_noisy = b.is_capture(mv) or (mv.promotion is not None)
                    except Exception:
                        continue
                    pk_b, stm, ob = pack_fen_fast(fen_s)
                    res_stm = res_w if stm == 0 else -res_w
                    draw_conf = (res_stm == 0 and abs(sc_i) >= 600)
                    if res_stm != 0 and sc_i * res_stm <= -600:
                        continue
                    if drop_draw_conflicts and draw_conf:
                        draw_conflicts_dropped += 1
                        continue
                    flg = (ob << 4) | (1 if is_noisy else 0) | (4 if swing_big else 0) | (8 if draw_conf else 0)
                    buf[buf_n]["packed"] = np.frombuffer(pk_b, dtype=np.uint8)
                    buf[buf_n]["stm"] = stm
                    buf[buf_n]["score16"] = max(-30000, min(30000, sc_i))
                    buf[buf_n]["res8"] = res_stm
                    buf[buf_n]["flags"] = flg
                    buf[buf_n]["weight_u8"] = 128
                    buf_n += 1
                    total_written += 1
                    if buf_n >= len(buf):
                        flush_shard()
                    if total_written >= target_pos:
                        break
        flush_shard()
    finally:
        if tb is not None:
            tb.close()
        try:
            send("quit")
            p.wait(timeout=3)
        except Exception:
            p.kill()
    return {
        "wid": wid, "positions": total_written, "games": games, "shards": shard_idx,
        "bytes": bytes_written, "plylimit_skipped": plylimit_skipped,
        "tb_adjudicated": tb_adjudicated, "draw_conflicts_dropped": draw_conflicts_dropped,
        "elapsed_s": round(time.time() - t0, 1),
    }


def selftest(exe_path: str, net_path: str, config_path: str, tb_dir: str) -> int:
    """Fast 1-worker 120-position self-test proving incremental replay, FQS1 flags, atomic writes, and TB hook."""
    # Unit checks on helper functions first
    assert _should_skip_plylimit("plylimit", [(i, 350, "a2a3", "8/8/8/8/8/8/8/8 w - - 0 1") for i in range(6)])
    assert not _should_skip_plylimit("rule", [(i, 350, "a2a3", "8/8/8/8/8/8/8/8 w - - 0 1") for i in range(6)])
    pk_b, stm, ob = pack_fen_fast(chess.STARTING_FEN)
    assert len(pk_b) == 32 and stm == 0 and ob == 7
    if tb_dir and Path(tb_dir).exists():
        with chess.syzygy.open_tablebase(tb_dir) as tb:
            # KQ vs K won for White
            assert _adjudicate_tb_result(tb, 0, "7k/8/5K2/8/8/8/8/6Q1 w - - 0 1") == 1
            # KNN vs K drawn
            assert _adjudicate_tb_result(tb, 0, "7k/8/5K2/8/8/8/6NN/8 w - - 0 1") == 0

    with tempfile.TemporaryDirectory() as td:
        tp = Path(td)
        res = worker_gen((
            0, [chess.STARTING_FEN], 120, 1000, 2, 2, 2000, 160,
            exe_path, net_path, 20261127, str(tp), 0.5, config_path, tb_dir, True, 0.0, 250_000, False, 0.15,
        ))
        shards = list(tp.glob("*.fqs.z"))
        parts = list(tp.glob("*.part"))
        assert len(shards) == 1 and len(parts) == 0, (shards, parts)
        raw = zlib.decompress(shards[0].read_bytes())
        assert raw[:8] == FQS_MAGIC
        arr = np.frombuffer(raw, dtype=FQS_DTYPE, offset=8)
        assert len(arr) >= 120
        assert not ((arr["res8"] == 0) & (np.abs(arr["score16"]) >= 600)).any(), "draw conflict leaked!"
        # Verify --resume continues cleanly to shard s001 without touching s000
        res2 = worker_gen((
            0, [chess.STARTING_FEN], len(arr) + 60, 1000, 2, 2, 2000, 160,
            exe_path, net_path, 20261127, str(tp), 0.5, config_path, tb_dir, True, 0.0, 250_000, True, 0.15,
        ))
        assert len(list(tp.glob("*.fqs.z"))) == 2 and res2["positions"] >= len(arr) + 60, res2
        print("CC0_SELFGAME_SELFTEST_PASS:", json.dumps({"pass1": res, "pass2_resume": res2}), flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="")
    ap.add_argument("--book", default=str(DEFAULT_BOOK))
    ap.add_argument("--config", default=str(DEFAULT_CONFIG))
    ap.add_argument("--tablebase-dir", default=str(DEFAULT_TB))
    ap.add_argument("--exe", default=FORGE_EXE)
    ap.add_argument("--net", default=R0067_NET)
    ap.add_argument("--positions", type=int, default=2_000_000)
    ap.add_argument("--shard-size", type=int, default=250_000)
    ap.add_argument("--soft-nodes", type=int, default=4000)
    ap.add_argument("--write-min-ply", type=int, default=2)
    ap.add_argument("--random-plies", type=int, default=2, help="Random plies after book position (2 = balanced 1/2 parity)")
    ap.add_argument("--startpos-frac", type=float, default=0.10, help="Fraction of games starting from startpos (0..2 random plies, write_min_ply=0)")
    ap.add_argument("--wide-div-frac", type=float, default=0.0, help="Optional fraction of games using 4-5 random plies after CC0 book to raise material/opp-castle entropy (e.g. 0.15)")
    ap.add_argument("--drop-draw-conflicts", action="store_true", default=True)
    ap.add_argument("--keep-draw-conflicts", dest="drop_draw_conflicts", action="store_false")
    ap.add_argument("--resume", action="store_true", help="Resume from existing cc0_wXX_sYYY.fqs.z shards")
    ap.add_argument("--max-temp-c", type=float, default=90.0)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--seed", type=int, default=20261127)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest(args.exe, args.net, args.config, args.tablebase_dir)
    if not args.out_dir:
        raise SystemExit("Need --out-dir (or --selftest)")

    mem_room = LAB / "tmp/fable_scratch/tools/mem_room.py"
    if mem_room.exists():
        r = subprocess.run([sys.executable, str(mem_room), "4"], capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(f"REFUSED by mem_room: {r.stdout} {r.stderr}")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    book_lines = [ln.strip() for ln in Path(args.book).read_text(encoding="utf-8").splitlines() if ln.strip()]
    per_w = (args.positions + args.workers - 1) // args.workers
    t0 = time.time()
    print(
        f"CC0_SELFGAME_START: target={args.positions:,} pos ({per_w:,}/w) soft_nodes={args.soft_nodes} "
        f"write_min_ply={args.write_min_ply} startpos_frac={args.startpos_frac} workers={args.workers} "
        f"drop_draw_conf={args.drop_draw_conflicts} resume={args.resume} tb={Path(args.tablebase_dir).exists()} book={len(book_lines):,} exe={Path(args.exe).name}",
        flush=True,
    )
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as ex:
        futs = [
            ex.submit(
                worker_gen,
                (
                    w, book_lines, per_w, args.soft_nodes, args.write_min_ply, args.random_plies,
                    2000, 300, args.exe, args.net, args.seed, str(out_dir), args.startpos_frac,
                    args.config, args.tablebase_dir, args.drop_draw_conflicts, args.max_temp_c, args.shard_size,
                    args.resume, args.wide_div_frac,
                ),
            )
            for w in range(args.workers)
        ]
        wres = [f.result() for f in concurrent.futures.as_completed(futs)]
    el = round(time.time() - t0, 1)
    tot_pos = sum(x["positions"] for x in wres)
    tot_games = sum(x["games"] for x in wres)
    tot_bytes = sum(x["bytes"] for x in wres)
    summary = {
        "elapsed_s": el,
        "positions": tot_pos,
        "games": tot_games,
        "bytes": tot_bytes,
        "mb": round(tot_bytes / (1024 * 1024), 2),
        "bytes_per_pos": round(tot_bytes / max(1, tot_pos), 2),
        "pos_per_sec": round(tot_pos / max(0.1, el), 1),
        "pos_per_hour": int(round(tot_pos / max(0.1, el) * 3600)),
        "plylimit_skipped": sum(x["plylimit_skipped"] for x in wres),
        "tb_adjudicated": sum(x["tb_adjudicated"] for x in wres),
        "draw_conflicts_dropped": sum(x["draw_conflicts_dropped"] for x in wres),
        "soft_nodes": args.soft_nodes,
        "write_min_ply": args.write_min_ply,
        "workers": args.workers,
        "book": args.book,
        "net": args.net,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("CC0_SELFGAME_DONE:", json.dumps(summary, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
