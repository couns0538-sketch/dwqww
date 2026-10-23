#!/usr/bin/env python3
"""Convert decoded SF plain, standard BINP binpack, or LC0 training chunks.

Keep forge_selfplay.py beside this file. Native binary decoding is delegated
to the format's own tools, not guessed: Sopel97/nnue_data_compress's
nnue_data_compression.exe, or LC0's lc0_rescorer.exe. See README.txt.
The shared OutputStore supplies rotation, persistent dedup and MD5 files.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import math
from pathlib import Path
import signal
import subprocess
import sys
import tempfile

import chess
import chess.engine

from forge_selfplay import MeteredUCI, OutputStore, eligible_score, stop_engine


@contextmanager
def decoded_plain(args):
    source = Path(args.input).resolve()
    if args.format == "plain":
        if not source.is_file():
            raise ValueError(f"Input not found: {source}")
        yield source
        return
    if not args.decoder or not Path(args.decoder).is_file():
        raise ValueError("--decoder must name the native decoder executable; see README.txt")
    with tempfile.TemporaryDirectory(prefix="forge-convert-", dir=args.temp_dir) as work:
        plain = Path(work) / "decoded.plain"
        if args.format == "binpack":
            if not source.is_file() or source.suffix.lower() != ".binpack":
                raise ValueError("A standard .binpack input file is required")
            with open(source, "rb") as src:
                if src.read(4) != b"BINP":
                    raise ValueError("Not a standard BINP binpack file")
            command = [str(Path(args.decoder).resolve()), str(source), str(plain)]
        else:
            if not source.is_dir():
                raise ValueError("Leela input must be a directory of unpacked training chunk files")
            if not args.syzygy:
                raise ValueError("LC0 rescorer requires --syzygy with at least 3-man tablebases")
            # Explicitly disable the rescorer's DESTRUCTIVE default. No output
            # chunk directory is passed, so only the temporary plain is written.
            command = [str(Path(args.decoder).resolve()),
                       f"--input={source}", f"--nnue-plain-file={plain}",
                       f"--syzygy-paths={Path(args.syzygy).resolve()}",
                       "--output=", "--delete-files=false", "--deblunder=false",
                       "--nnue-best-score=true", "--nnue-best-move=true", "--threads=1"]
        print("Decoding to a temporary .plain file; enough disk space is required.", flush=True)
        extra = ({"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
                 if sys.platform == "win32" else {"start_new_session": True})
        process = subprocess.Popen(command, cwd=work, **extra)
        try:
            code = process.wait()
            if code:
                raise subprocess.CalledProcessError(code, command)
        except KeyboardInterrupt:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            raise
        if not plain.is_file() or plain.stat().st_size == 0:
            raise RuntimeError("Decoder produced no data; check its messages/version/input format.")
        yield plain


def plain_records(path, scale=1.0):
    """SF plain score and {-1,0,+1} result are both from side-to-move POV."""
    record = {}
    with open(path, encoding="utf-8-sig") as src:
        for line_number, raw in enumerate(src, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line == "e":
                if not {"fen", "score", "result"} <= record.keys():
                    raise ValueError(f"Missing field near {path}:{line_number}")
                board = chess.Board(record["fen"])
                if not board.is_valid() or board.chess960:
                    raise ValueError(f"Unsupported or invalid orthodox position at line {line_number}")
                z = int(record["result"])
                if z not in (-1, 0, 1):
                    raise ValueError("Expected SF plain result -1/0/1 from side-to-move POV")
                score = float(record["score"]) * scale
                if not math.isfinite(score):
                    raise ValueError(f"Non-finite score near line {line_number}")
                result = (z + 1) / 2
                if board.turn == chess.BLACK:
                    result = 1.0 - result
                move = board.parse_uci(record["move"]) if "move" in record else None
                yield board, round(score), result, move
                record = {}
            else:
                key, value = line.split(maxsplit=1)
                if key not in {"fen", "move", "score", "ply", "result"}:
                    raise ValueError(f"Unknown plain field {key!r} at line {line_number}")
                if key in record:
                    raise ValueError(f"Repeated field {key!r} at line {line_number}")
                record[key] = value
    if record:
        raise ValueError("Truncated plain record: missing final 'e'")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("format", choices=["plain", "binpack", "leela"])
    p.add_argument("input")
    p.add_argument("--decoder", help="nnue_data_compression.exe or lc0_rescorer.exe")
    p.add_argument("--syzygy", help="Required by LC0 rescorer")
    p.add_argument("--temp-dir", help="Drive with space for expanded plain data")
    p.add_argument("--out", default="out-converted")
    p.add_argument("--lines-per-file", type=int, default=10_000_000)
    p.add_argument("--score-scale", type=float,
                   help="Input score units -> cp multiplier (default: 1, or 100/208 for LC0)")
    p.add_argument("--rescore-engine", help="Optional UCI engine for fresh, native cp labels")
    p.add_argument("--nodes", type=int, default=5000)
    p.add_argument("--quiet-only", action="store_true",
                   help="Filter check/capture/promotion/|cp|>3000; needs move field or rescoring")
    a = p.parse_args()
    if a.nodes <= 0 or a.lines_per_file <= 0:
        p.error("nodes and lines-per-file must be positive")
    scale = a.score_scale if a.score_scale is not None else (100 / 208 if a.format == "leela" else 1.0)
    if not math.isfinite(scale) or scale <= 0:
        p.error("score-scale must be positive and finite")
    if a.format == "leela" and not a.rescore_engine:
        print("LC0 labels are Q-derived cp estimates, using legacy SF PawnValueEg=208 scaling. "
              "Use --rescore-engine for your engine's cp calibration.", flush=True)
    engine = None
    writer = None
    pending, seen, saved = [], 0, 0
    interrupted = False
    try:
        if a.rescore_engine:
            path = Path(a.rescore_engine).resolve()
            engine = chess.engine.SimpleEngine.popen(MeteredUCI, [str(path)], timeout=60,
                                                    setpgrp=True, cwd=str(path.parent))
            engine.configure({"Threads": 1, "Hash": 16})
        writer = OutputStore(a.out, a.lines_per_file)
        with decoded_plain(a) as plain:
            for board, cp, result, move in plain_records(plain, scale):
                seen += 1
                if engine is not None:
                    if board.is_game_over():
                        continue
                    reply = engine.play(board, chess.engine.Limit(nodes=a.nodes),
                                        game=object(), info=chess.engine.INFO_SCORE)
                    score = reply.info["score"].pov(board.turn)
                    if score.is_mate() or engine.protocol.score_is_bound:
                        continue
                    cp, move = score.score(), reply.move
                if a.quiet_only:
                    if move is None:
                        raise ValueError("--quiet-only needs legal moves or --rescore-engine")
                    if eligible_score(board, move, chess.engine.Cp(cp)) is None:
                        continue
                pending.append((board.fen(en_passant="fen"), cp, result))
                if len(pending) == 4096:
                    saved += writer.append(pending)
                    pending.clear()
                    print(f"Read {seen:,}; saved {saved:,} unique positions", flush=True)
    except KeyboardInterrupt:
        interrupted = True
        print("Interrupted; flushing converted records.", flush=True)
    finally:
        # Further Ctrl+C must not interrupt the final data/DB/checksum commit.
        old = signal.signal(signal.SIGINT, signal.SIG_IGN)
        try:
            if writer is not None:
                try:
                    if pending and not writer.failed:
                        saved += writer.append(pending)
                finally:
                    writer.close()
        finally:
            stop_engine(engine)
            signal.signal(signal.SIGINT, old)
    print(f"Done: read {seen:,}, saved {saved:,} unique positions.")
    return 130 if interrupted else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError,
            chess.engine.EngineError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
