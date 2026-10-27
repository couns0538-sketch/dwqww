"""S20: relabel/rescore Forge training positions with a fixed-depth re-search (depth 8 by default).

Input: text lines "FEN | stm_cp | white_result" (the forge_selfplay.py / fen2bin format: score = side-to-move cp,
result = WHITE's game result 0 / 0.5 / 1). Output: the same format, line for line for every valid input line, with
the score replaced by the engine's fixed-depth search score (side-to-move cp) and the WHITE result unchanged, so it
feeds fen2bin, hce_dump, Sol's D filter and the v3b loaders exactly as self-play text does.

  python -I -B opus_rescore.py --engine E.exe --in input.txt --out-dir F:/opus_scratch/rescore_d8/<run>
      [--depth 8] [--limit N] [--chunk-lines 50000] [--max-score 3000] [--blend 1.0] [--k 2.25] [--hash 16]

Resumable: the input is processed in chunks of --chunk-lines input lines. Chunk i covers input lines
[i*chunk, (i+1)*chunk) and is written to chunk_iiiii.txt.partial, then renamed to chunk_iiiii.txt; progress.json
records each finished chunk (lines, sha256, stats, seconds). A restart verifies the recorded chunks (file present,
sha256 equal) and continues with the first missing one; the parameters and the input sha256 must match the
recorded run. When every chunk is done the chunks are joined into rescored.txt (+ rescored.txt.stats.json).

- Determinism: every position is searched alone from a cleared hash (ucinewgame), Threads=1, Hash=16 (<= 64 MB),
  OwnBook=false, fixed depth: its score depends only on the position, so the output is identical on every run, in
  any order, and after any restart.
- Mate scores become +-max-score (sign of the mate); cp scores are clipped to +-max-score (3000 = forge_selfplay
  default). No NaN can occur: scores are parsed as integers, and a missing score stops the run.
- Blend (default 1.0 = the pure search score). The f006 recipe blends at training time (teacher blend 1.0 -> 0.6),
  so the data keeps the pure score. With --blend L < 1 the written score is that of the WDL-blended target,
  s' = 400/k * logit(L * sigmoid(k*s/400) + (1-L) * stm_result), k = 2.25 (the trainer's K_DEFAULT).
- The engine runs at IDLE priority, one search thread. All output stays under --allowed-root
  (default F:/opus_scratch/rescore_d8); the tool refuses any other --out-dir.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

K_DEFAULT = 2.25
IDLE_PRIORITY_CLASS = 0x00000040
ALLOWED_ROOT = r"F:\opus_scratch\rescore_d8"


class Engine:
    def __init__(self, path: str, hash_mb: int = 16):
        flags = IDLE_PRIORITY_CLASS if sys.platform == "win32" else 0
        self.p = subprocess.Popen([path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1,
                                  creationflags=flags)
        self.send("uci")
        self.id_lines = [line for line in self.until("uciok") if line.startswith("id ")]
        for option in ("Threads value 1", f"Hash value {hash_mb}", "OwnBook value false"):
            self.send("setoption name " + option)
        self.send("isready"); self.until("readyok")

    def send(self, line: str) -> None:
        self.p.stdin.write(line + "\n")
        self.p.stdin.flush()

    def until(self, prefix: str) -> list[str]:
        lines = []
        for line in self.p.stdout:
            line = line.rstrip("\r\n")
            lines.append(line)
            if line.startswith(prefix):
                return lines
        raise RuntimeError(f"engine exited before {prefix!r}")

    def search(self, fen: str, depth: int) -> tuple[str, int]:
        """(kind 'cp'|'mate', value) of the last exact-score info line."""
        self.send("ucinewgame")
        self.send("position fen " + fen)
        self.send(f"go depth {depth}")
        kind, value = None, None
        for line in self.until("bestmove"):
            if line.startswith("info") and " score " in line and " depth " in line:
                parts = line.split()
                if "upperbound" in parts or "lowerbound" in parts:
                    continue
                i = parts.index("score")
                kind, value = parts[i + 1], int(parts[i + 2])
        if kind not in ("cp", "mate"):
            raise RuntimeError(f"no score for {fen}")
        return kind, value

    def close(self) -> None:
        try:
            self.send("quit")
            self.p.wait(timeout=30)
        except Exception:
            self.p.kill()


def to_cp(kind: str, value: int, max_score: int) -> tuple[int, bool, bool]:
    """(score, was_mate, was_clipped)"""
    if kind == "mate":
        return (max_score if value > 0 else -max_score), True, False
    clipped = max(-max_score, min(max_score, value))
    return clipped, False, clipped != value


def blend_score(score: int, stm_result: float, blend: float, k: float, max_score: int) -> int:
    if blend >= 1.0:
        return score
    teacher = 1.0 / (1.0 + math.exp(-max(-40.0, min(40.0, score * k / 400.0))))
    target = min(1.0 - 1e-9, max(1e-9, blend * teacher + (1.0 - blend) * stm_result))
    value = 400.0 / k * math.log(target / (1.0 - target))
    return int(max(-max_score, min(max_score, round(value))))


def placement_ok(placement: str) -> bool:
    ranks = placement.split("/")
    if len(ranks) != 8:
        return False
    for rank in ranks:
        squares = 0
        for ch in rank:
            if ch in "12345678":
                squares += int(ch)
            elif ch in "pnbrqkPNBRQK":
                squares += 1
            else:
                return False
        if squares != 8:
            return False
    return placement.count("K") == 1 and placement.count("k") == 1


def parse_line(line: str):
    """-> (fen, old_score, result_text, white_result, side_to_move); ValueError on a bad line."""
    fen, score_text, result_text = [part.strip() for part in line.split("|")]
    fields = fen.split()
    if len(fields) != 6 or fields[1] not in ("w", "b") or not placement_ok(fields[0]):
        raise ValueError("bad FEN")
    result = float(result_text)
    if result not in (0.0, 0.5, 1.0):
        raise ValueError("bad result")
    return fen, int(score_text), result_text, result, fields[1]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1 << 22), b""):
            digest.update(block)
    return digest.hexdigest()


def new_stats() -> dict:
    return {"lines_in": 0, "lines": 0, "bad_lines": 0, "mates": 0, "clipped": 0, "delta_sum": 0, "delta_abs_sum": 0,
            "delta_abs_max": 0, "hist_100cp": {}, "sign": {"agree": 0, "disagree": 0, "zero": 0}}


def merge(total: dict, part: dict) -> None:
    for key in ("lines_in", "lines", "bad_lines", "mates", "clipped", "delta_sum", "delta_abs_sum"):
        total[key] += part[key]
    total["delta_abs_max"] = max(total["delta_abs_max"], part["delta_abs_max"])
    for key, value in part["hist_100cp"].items():
        total["hist_100cp"][key] = total["hist_100cp"].get(key, 0) + value
    for key in ("agree", "disagree", "zero"):
        total["sign"][key] += part["sign"][key]


def rescore_chunk(engine: Engine, lines: list[str], args, partial: Path) -> dict:
    stats = new_stats()
    with open(partial, "w", encoding="utf-8", newline="\n") as dst:
        for line in lines:
            stats["lines_in"] += 1
            line = line.rstrip("\r\n")
            try:
                fen, old, result_text, white_result, stm = parse_line(line)
            except ValueError:
                stats["bad_lines"] += 1
                continue
            kind, value = engine.search(fen, args.depth)
            score, mate, clipped = to_cp(kind, value, args.max_score)
            stm_result = white_result if stm == "w" else 1.0 - white_result
            score = blend_score(score, stm_result, args.blend, args.k, args.max_score)
            dst.write(f"{fen} | {score} | {result_text}\n")
            stats["lines"] += 1
            stats["mates"] += mate
            stats["clipped"] += clipped
            stats["delta_sum"] += score - old
            stats["delta_abs_sum"] += abs(score - old)
            stats["delta_abs_max"] = max(stats["delta_abs_max"], abs(score - old))
            bucket = str(max(-30, min(30, score // 100)) * 100)
            stats["hist_100cp"][bucket] = stats["hist_100cp"].get(bucket, 0) + 1
            if stm_result != 0.5:
                if score == 0:
                    stats["sign"]["zero"] += 1
                elif (score > 0) == (stm_result == 1.0):
                    stats["sign"]["agree"] += 1
                else:
                    stats["sign"]["disagree"] += 1
    return stats


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--engine", required=True)
    ap.add_argument("--in", dest="inp", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--depth", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0, help="first N input lines only (0 = all)")
    ap.add_argument("--chunk-lines", type=int, default=50000)
    ap.add_argument("--max-score", type=int, default=3000)
    ap.add_argument("--blend", type=float, default=1.0)
    ap.add_argument("--k", type=float, default=K_DEFAULT)
    ap.add_argument("--hash", type=int, default=16)
    ap.add_argument("--allowed-root", default=ALLOWED_ROOT)
    args = ap.parse_args(argv)
    out = args.out_dir.resolve()
    root = Path(args.allowed_root).resolve()
    if out != root and root not in out.parents:
        ap.error(f"--out-dir must be inside {root}")
    if not 0.0 <= args.blend <= 1.0 or args.depth < 1 or not 0 < args.max_score <= 32000 or not 0 < args.hash <= 64:
        ap.error("bad --blend/--depth/--max-score/--hash (Hash must be <= 64 MB)")
    out.mkdir(parents=True, exist_ok=True)
    params = {"depth": args.depth, "max_score": args.max_score, "blend": args.blend, "k": args.k, "hash_mb": args.hash,
              "chunk_lines": args.chunk_lines, "limit": args.limit, "input_sha256": sha256_file(args.inp),
              "engine_sha256": sha256_file(Path(args.engine))}
    progress_path = out / "progress.json"
    progress = json.loads(progress_path.read_text(encoding="utf-8")) if progress_path.exists() else {"params": params, "chunks": {}}
    if progress["params"] != params:
        ap.error("progress.json belongs to a run with other parameters or input; use a new --out-dir")
    with open(args.inp, encoding="utf-8-sig") as src:
        lines = src.read().splitlines()
    lines = [line for line in lines if line.strip()]
    if args.limit:
        lines = lines[:args.limit]
    chunks = [lines[i:i + args.chunk_lines] for i in range(0, len(lines), args.chunk_lines)]
    engine = None
    start = time.time()
    try:
        for index, chunk in enumerate(chunks):
            name = f"chunk_{index:05d}.txt"
            done = progress["chunks"].get(name)
            if done and (out / name).exists() and sha256_file(out / name) == done["sha256"]:
                continue
            if engine is None:
                engine = Engine(args.engine, args.hash)
                progress["engine_id"] = engine.id_lines
            t0 = time.time()
            partial = out / (name + ".partial")
            stats = rescore_chunk(engine, chunk, args, partial)
            os.replace(partial, out / name)
            stats.update(sha256=sha256_file(out / name), seconds=round(time.time() - t0, 1),
                         first_input_line=index * args.chunk_lines)
            progress["chunks"][name] = stats
            tmp = out / "progress.json.partial"
            tmp.write_text(json.dumps(progress, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
            os.replace(tmp, progress_path)
            print(f"{name}: {stats['lines']:,} positions in {stats['seconds']} s "
                  f"({stats['lines'] / max(1e-9, stats['seconds']):,.0f}/s)", flush=True)
    finally:
        if engine is not None:
            engine.close()
    total = new_stats()
    names = [f"chunk_{i:05d}.txt" for i in range(len(chunks))]
    for name in names:
        merge(total, progress["chunks"][name])
    final = out / "rescored.txt"
    partial = out / "rescored.txt.partial"
    with open(partial, "wb") as dst:
        for name in names:
            dst.write((out / name).read_bytes())
    os.replace(partial, final)
    decisive = total["sign"]["agree"] + total["sign"]["disagree"]
    total.update(params=params, input=str(args.inp), output=str(final), output_sha256=sha256_file(final),
                 chunks=len(names), chunk_seconds=sum(progress["chunks"][n]["seconds"] for n in names),
                 this_session_seconds=round(time.time() - start, 1), engine=str(args.engine),
                 engine_id=progress.get("engine_id"), delta_mean=total["delta_sum"] / max(1, total["lines"]),
                 delta_abs_mean=total["delta_abs_sum"] / max(1, total["lines"]),
                 sign_agreement_decisive=total["sign"]["agree"] / max(1, decisive),
                 hist_100cp=dict(sorted(total["hist_100cp"].items(), key=lambda kv: int(kv[0]))))
    (out / "rescored.txt.stats.json").write_text(json.dumps(total, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: total[k] for k in ("lines", "bad_lines", "mates", "clipped", "delta_mean", "delta_abs_mean",
                                            "sign_agreement_decisive", "output_sha256", "chunk_seconds")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
