#!/usr/bin/env python3
"""relabel2.py - Opus R14-B item 2: sharded, resumable relabel that keeps the original FEN and splits validation by
game (own code, 2026-11-02). Normalized (Astra JSONL) input must be in source order (source, source_row). UNPROVEN as training data: Engine NNUE decides whether the labels are used.

usage (python with python-chess, e.g. C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe -I -B):
  relabel2.py prepare  --job DIR --run-id ID (--selfplay FILE ... | --normalized FILE ...) [--rows N]
                       [--val-ppm 10000] [--salt S] [--drop-terminal]
  relabel2.py run      --job DIR --run-id ID --probe EXE [--nodes 20000] [--hash-mb 1] [--workers 1]
                       [--shard-size 10000] [--mask 0xC] [--max-shards K] [--until "YYYY-MM-DD HH:MM"]
  relabel2.py assemble --job DIR --run-id ID
  relabel2.py status   --job DIR
Exit codes: 0 done, 2 bad input, 3 configuration differs from the job (or a target exists), 4 integrity failure
(a published file changed or a check failed), 1 anything else.

- prepare: every input row is validated with Astra's records.py (unchanged copy in astra/): original full FEN (castling,
  en passant, clocks kept), STM score, White result. A bad row stops with exit 2 and nothing is published. Game id =
  (input file, game index); a new game starts between two consecutive rows of a file when the ply does not increase,
  the result changes, the piece count rises or a castling right appears (all impossible inside one game, so a real
  game is never split; two games may merge, which cannot leak). Split: sha256(salt|game id) mod 1e6 < val ppm.
  --rows N keeps whole games only (the sample ends at a game boundary). Output rows.tsv + prepare.json.
- run: shard k = rows [k*S, (k+1)*S). A shard is labelled in shards/shard_K.part.N (labels.tsv, manifest.json with
  sha256, summary.json with the run id; all fsynced) and published by renaming the directory to shard_K. The same
  command resumes: the configuration is pinned in run_config.json (exit 3 on a change), every published shard is
  re-hashed (exit 4 on a mismatch), interrupted .part.N directories stay as evidence (nothing is deleted or modified)
  and the shard is redone as .part.N+1. Labels come from the R13 probe (lock source d4f4312; transposition table,
  histories and caches cleared before every search), so a label depends only on FEN, nodes and hash. This process
  and the probes run at Idle priority on --mask; --workers <= 2.
- assemble: (only when every shard is published and intact) published shards in order -> final/train.txt and final/val.txt (self-play text format, new label) and
  final/labels.tsv (all columns), checked (every row id exactly once and in order, game ids disjoint across the
  splits, counts = prepare.json) and published by renaming; MANIFEST.json holds md5 + sha256. The three data files
  contain no run id or time, so an interrupted-and-resumed job gives byte-identical files.
"""

import argparse
import ctypes
import datetime as dt
import hashlib
import json
import os
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "astra"))

TOOL = "opus_r14b/item2/relabel2.py"
ROWS_HEADER = "row_id\tgame_id\tsplit\tfen\told_score_stm\tresult\tsource\tsource_row\n"
LABELS_HEADER = "row_id\tgame_id\tsplit\tfen\tscore_stm\told_score_stm\tresult\tdepth\tnodes\n"
RESULT_TOKEN = {-1: "0", 0: "0.5", 1: "1"}


class BadInput(Exception):
    pass


class ConfigMismatch(Exception):
    pass


class IntegrityError(Exception):
    pass


def now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def file_hash(path, algo="sha256") -> str:
    h = hashlib.new(algo)
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_new(path: Path, text: str) -> None:
    """Exclusive create + fsync (never overwrites)."""
    with open(path, "x", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())


def write_status(path: Path, obj) -> None:
    """Status files are replaced atomically; everything else is created once."""
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(obj, indent=1) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def append_log(job: Path, line: str) -> None:
    with open(job / "sessions.log", "a", encoding="utf-8", newline="\n") as fh:
        fh.write(f"{now()} pid={os.getpid()} {line}\n")
        fh.flush()
        os.fsync(fh.fileno())


def lower_priority(mask: int) -> None:
    """Idle class + CPU mask for this process; the probe children inherit both."""
    if os.name != "nt":
        os.nice(19)
        return
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.GetCurrentProcess.restype = ctypes.c_void_p
    h = ctypes.c_void_p(k.GetCurrentProcess())
    if not k.SetPriorityClass(h, 0x40):
        raise OSError(ctypes.get_last_error(), "SetPriorityClass")
    if not k.SetProcessAffinityMask(h, ctypes.c_size_t(mask)):
        raise OSError(ctypes.get_last_error(), "SetProcessAffinityMask")


# ---------------------------------------------------------------- prepare

def board_stats(fen: str):
    fields = fen.split()
    pieces = sum(ch.isalpha() for ch in fields[0])
    castling = set(fields[2]) - {"-"}
    return pieces, castling


def new_game(prev, cur) -> bool:
    """True when cur cannot follow prev inside one game (leak-safe: never splits a real game)."""
    if cur["ply"] <= prev["ply"] or cur["result_white"] != prev["result_white"]:
        return True
    p_pieces, p_castle = prev["stats"]
    c_pieces, c_castle = cur["stats"]
    return c_pieces > p_pieces or not c_castle <= p_castle


def iter_rows(a, sources, counters):
    """Yield (source index, row number, record, result token) in game order, validating every row."""
    import chess
    import records  # Astra's unchanged records.py

    paths = a.selfplay or a.normalized
    for si, path in enumerate(paths):
        p = Path(path)
        if not p.is_file():
            raise BadInput(f"{p}: input file not found")
        sources.append({"index": si, "path": str(p.resolve()), "sha256": file_hash(p),
                        "kind": "selfplay" if a.selfplay else "normalized"})
        last_key = None
        with open(p, encoding="utf-8-sig") as fh:
            for row_no, line in enumerate(fh, 1):
                counters["read"] += 1
                try:
                    if a.selfplay:
                        if not line.strip():
                            raise ValueError("empty line")
                        r = records.selfplay_record(line, str(p), row_no)
                        token = line.split("|")[2].strip()
                    else:
                        r = records.validate_record(json.loads(line))
                        if r["source_kind"] != "selfplay" or type(r["source_row"]) is not int:
                            raise ValueError("needs a self-play row with an integer source_row")
                        key = (r["source"], r["source_row"])
                        if last_key is not None and key <= last_key:
                            raise ValueError("normalized rows must be in source order (sort by source, source_row)")
                        last_key = key
                        token = RESULT_TOKEN.get(r["result_white"])
                    if r["result_white"] is None:
                        raise ValueError("no game result")
                    board = chess.Board(r["fen"])
                except Exception as e:  # noqa: BLE001 - every rejection is bad input
                    raise BadInput(f"{p}:{row_no}: {e}") from None
                if not any(board.legal_moves):
                    if not a.drop_terminal:
                        raise BadInput(f"{p}:{row_no}: terminal position (no legal move) cannot be searched")
                    counters["terminal"] += 1
                    continue
                r["stats"] = board_stats(r["fen"])
                yield si, row_no, r, token


def cmd_prepare(a) -> int:
    job = Path(a.job)
    if job.exists():
        raise ConfigMismatch(f"job directory exists: {job}")
    job.mkdir(parents=True)
    sources, counters = [], {"read": 0, "terminal": 0}
    tmp = job / "rows.tsv.part"
    st = {"rows": 0, "games": 0, "val_rows": 0, "val_games": 0, "row_id": 0}
    lengths, starts, game_no = [], [], {}

    def emit(game, fh) -> bool:
        """Write one whole game; False when --rows would be exceeded (the sample ends before it)."""
        if a.rows and st["rows"] + len(game) > a.rows:
            return False
        si = game[0][0]
        gi = game_no.get(si, 0)
        game_no[si] = gi + 1
        game_id = f"s{si}g{gi}"
        h = int(hashlib.sha256(f"{a.salt}|{game_id}".encode()).hexdigest()[:16], 16)
        split = "val" if h % 1_000_000 < a.val_ppm else "train"
        for _, row_no, r, token in game:
            fh.write(f"{st['row_id']}\t{game_id}\t{split}\t{r['fen']}\t{r['score_stm']}\t{token}\t{si}\t{row_no}\n")
            st["row_id"] += 1
        st["rows"] += len(game)
        st["games"] += 1
        if split == "val":
            st["val_rows"] += len(game)
            st["val_games"] += 1
        lengths.append(len(game))
        starts.append(game[0][2]["ply"])
        return True

    try:
        with open(tmp, "x", encoding="utf-8", newline="\n") as fh:
            fh.write(ROWS_HEADER)
            game, prev, complete = [], None, True
            for item in iter_rows(a, sources, counters):
                si, _, r, _ = item
                if game and (si != game[-1][0] or new_game(prev, r)):
                    if not emit(game, fh):
                        complete = False
                        break
                    game = []
                game.append(item)
                prev = r
            if complete and game:
                emit(game, fh)
            fh.flush()
            os.fsync(fh.fileno())
        if st["rows"] == 0:
            raise BadInput("no rows selected (input empty, or --rows smaller than the first game)")
    except BadInput as e:
        write_new(job / "prepare_failed.json", json.dumps({"run_id": a.run_id, "time": now(), "error": str(e)}) + "\n")
        raise
    os.rename(tmp, job / "rows.tsv")
    lengths.sort()
    starts.sort()
    q = lambda v, f: v[min(len(v) - 1, int(len(v) * f))]  # noqa: E731
    info = {
        "run_id": a.run_id, "created": now(), "tool": TOOL, "tool_sha256": file_hash(__file__),
        "records_py_sha256": file_hash(HERE / "astra" / "records.py"), "inputs": sources,
        "rows": st["rows"], "games": st["games"], "rows_read": counters["read"], "terminal_dropped": counters["terminal"],
        "rows_requested": a.rows, "train_rows": st["rows"] - st["val_rows"], "val_rows": st["val_rows"],
        "train_games": st["games"] - st["val_games"], "val_games": st["val_games"], "val_ppm": a.val_ppm,
        "salt": a.salt,
        "game_rule": "new game when ply does not increase, result changes, piece count rises or a castling right appears",
        "game_length": {"min": lengths[0], "median": q(lengths, 0.5), "p99": q(lengths, 0.99), "max": lengths[-1]},
        "game_start_ply": {"min": starts[0], "median": q(starts, 0.5), "p99": q(starts, 0.99), "max": starts[-1]},
        "rows_tsv_sha256": file_hash(job / "rows.tsv"),
    }
    write_new(job / "prepare.json", json.dumps(info, indent=1) + "\n")
    print(json.dumps({k: info[k] for k in ("rows", "games", "rows_read", "train_rows", "val_rows", "val_games",
                                            "game_length", "game_start_ply", "terminal_dropped")}))
    return 0


# ---------------------------------------------------------------- run

def load_prepare(job: Path):
    info = json.loads((job / "prepare.json").read_text(encoding="utf-8"))
    if file_hash(job / "rows.tsv") != info["rows_tsv_sha256"]:
        raise IntegrityError("rows.tsv differs from prepare.json")
    return info


def row_offsets(job: Path, shard_size: int, n: int):
    """Byte offset of the first row of every shard (one pass over rows.tsv)."""
    offs = []
    with open(job / "rows.tsv", "rb") as fh:
        if fh.readline().decode() != ROWS_HEADER:
            raise IntegrityError("rows.tsv header")
        pos, i = fh.tell(), 0
        for line in fh:
            if i % shard_size == 0:
                offs.append(pos)
            pos += len(line)
            i += 1
    if i != n:
        raise IntegrityError(f"rows.tsv has {i} rows, prepare.json {n}")
    return offs


def read_shard_rows(job: Path, offset: int, count: int):
    out = []
    with open(job / "rows.tsv", "rb") as fh:
        fh.seek(offset)
        for _ in range(count):
            f = fh.readline().decode("utf-8").rstrip("\n").split("\t")
            out.append(f)
    return out


def verify_shard(d: Path, k: int, first: int, count: int, run_id: str) -> None:
    try:
        man = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
        summ = json.loads((d / "summary.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise IntegrityError(f"{d.name}: unreadable manifest / summary: {e}") from None
    if file_hash(d / "labels.tsv") != man["labels.tsv"]:
        raise IntegrityError(f"{d.name}: labels.tsv sha256 differs from its manifest")
    if file_hash(d / "summary.json") != man["summary.json"]:
        raise IntegrityError(f"{d.name}: summary.json differs from its manifest")
    if (summ["shard"], summ["first_row"], summ["rows"], summ["run_id"]) != (k, first, count, run_id):
        raise IntegrityError(f"{d.name}: summary does not match the job (shard/rows/run id)")


def label_shard(pool, rows, cfg):
    """Probe every row; returns label lines. Raises on any probe answer that is not an exact searched label."""
    lines = []
    for b in range(0, len(rows), 256):
        chunk = rows[b:b + 256]
        answers = pool.map([(r[0], r[3]) for r in chunk], op="analyze")
        if len(answers) != len(chunk):
            raise RuntimeError("probe answer count")
        for r, ans in zip(chunk, answers):
            ok = (ans.get("ok") is True and str(ans.get("id")) == r[0] and ans.get("analyzed") is True
                  and ans.get("terminal") is False and type(ans.get("score")) is int and type(ans.get("depth")) is int
                  and ans["depth"] >= 1 and type(ans.get("nodes")) is int and 0 < ans["nodes"] <= cfg["nodes"]
                  and ans.get("nodes_limit") == cfg["nodes"] and ans.get("hash_mb") == cfg["hash_mb"]
                  and ans.get("threads") == 1 and " ".join(str(ans.get("fen", "")).split()) == " ".join(r[3].split())
                  and -32767 <= ans["score"] <= 32767)
            if not ok:
                raise RuntimeError(f"row {r[0]}: probe answer is not an exact searched label: {ans}")
            lines.append(f"{r[0]}\t{r[1]}\t{r[2]}\t{r[3]}\t{ans['score']}\t{r[4]}\t{r[5]}\t{ans['depth']}\t{ans['nodes']}\n")
    return lines


def cmd_run(a) -> int:
    from forge_probe import ProbePool  # R13 probe client, unchanged copy

    job = Path(a.job)
    info = load_prepare(job)
    if info["run_id"] != a.run_id:
        raise ConfigMismatch(f"run id {a.run_id} != job run id {info['run_id']}")
    if not 1 <= a.workers <= 2:
        raise ConfigMismatch("workers must be 1 or 2 (R14-B thread budget)")
    cfg = {"run_id": a.run_id, "probe": str(Path(a.probe).resolve()), "probe_sha256": file_hash(a.probe),
           "nodes": a.nodes, "hash_mb": a.hash_mb, "shard_size": a.shard_size,
           "prepare_json_sha256": file_hash(job / "prepare.json"), "tool": TOOL}
    rc = job / "run_config.json"
    if rc.exists():
        old = json.loads(rc.read_text(encoding="utf-8"))
        diff = [k for k in cfg if old.get(k) != cfg[k] and k not in ("probe", "tool")]
        if diff:
            raise ConfigMismatch(f"configuration differs from run_config.json: {diff}")
    else:
        write_new(rc, json.dumps(dict(cfg, created=now(), tool_sha256=file_hash(__file__)), indent=1) + "\n")
    lower_priority(int(a.mask, 16))
    n = info["rows"]
    shards = (n + a.shard_size - 1) // a.shard_size
    offs = row_offsets(job, a.shard_size, n)
    sdir = job / "shards"
    sdir.mkdir(exist_ok=True)
    done = set()
    for k in range(shards):
        d = sdir / f"shard_{k:05d}"
        if d.is_dir():
            verify_shard(d, k, k * a.shard_size, min(a.shard_size, n - k * a.shard_size), a.run_id)
            done.add(k)
    deadline = dt.datetime.strptime(a.until, "%Y-%m-%d %H:%M") if a.until else None
    append_log(job, f"run start run_id={a.run_id} shards_done={len(done)}/{shards} workers={a.workers} "
                    f"test_kill_after_s={a.test_kill_after_seconds}")
    if a.test_kill_after_seconds > 0:  # proof hook: abrupt exit at an arbitrary point (like a hard kill)
        threading.Thread(target=lambda: (time.sleep(a.test_kill_after_seconds), os._exit(137)), daemon=True).start()
    t0, rows_session, shards_session = time.monotonic(), 0, 0
    status = {"run_id": a.run_id, "session_start": now(), "shards_total": shards, "rows_total": n}
    with ProbePool(a.probe, a.nodes, a.workers, None, hash_mb=a.hash_mb, timeout=300) as pool:
        for k in range(shards):
            if k in done:
                continue
            if a.max_shards and shards_session >= a.max_shards:
                break
            if deadline and dt.datetime.now() >= deadline:
                break
            first = k * a.shard_size
            count = min(a.shard_size, n - first)
            attempts = [int(p.name.rsplit(".", 1)[1]) for p in sdir.glob(f"shard_{k:05d}.part.*")]
            part = sdir / f"shard_{k:05d}.part.{max(attempts, default=0) + 1}"
            part.mkdir()
            ts = time.monotonic()
            rows = read_shard_rows(job, offs[k], count)
            if [int(r[0]) for r in rows] != list(range(first, first + count)):
                raise IntegrityError(f"shard {k}: row ids in rows.tsv are not {first}..{first + count - 1}")
            lines = label_shard(pool, rows, cfg)
            write_new(part / "labels.tsv", LABELS_HEADER + "".join(lines))
            nodes = sum(int(x.split("\t")[8]) for x in lines)
            summ = {"run_id": a.run_id, "shard": k, "first_row": first, "rows": count, "nodes_total": nodes,
                    "seconds": round(time.monotonic() - ts, 2), "attempt": part.name, "finished": now()}
            write_new(part / "summary.json", json.dumps(summ, indent=1) + "\n")
            write_new(part / "manifest.json", json.dumps({"labels.tsv": file_hash(part / "labels.tsv"),
                                                          "summary.json": file_hash(part / "summary.json")}, indent=1) + "\n")
            os.rename(part, sdir / f"shard_{k:05d}")  # publish (fails if it exists: never overwrites)
            done.add(k)
            rows_session += count
            shards_session += 1
            el = time.monotonic() - t0
            rate = rows_session * 3600 / el if el > 0 else 0
            left = n - sum(min(a.shard_size, n - j * a.shard_size) for j in done)
            status.update(updated=now(), shards_done=len(done), rows_done=n - left, last_shard=k,
                          session_rows=rows_session, session_rows_per_hour=round(rate),
                          eta_hours=round(left / rate, 2) if rate else None, workers=a.workers, nodes=a.nodes)
            write_status(job / "status.json", status)
    append_log(job, f"run end run_id={a.run_id} shards_done={len(done)}/{shards} session_rows={rows_session}")
    print(json.dumps(status))
    return 0


# ---------------------------------------------------------------- assemble

def cmd_assemble(a) -> int:
    job = Path(a.job)
    info = load_prepare(job)
    rc = json.loads((job / "run_config.json").read_text(encoding="utf-8"))
    if info["run_id"] != a.run_id or rc["run_id"] != a.run_id:
        raise ConfigMismatch("run id differs from the job")
    n, size = info["rows"], rc["shard_size"]
    shards = (n + size - 1) // size
    final = job / "final"
    if final.exists():
        raise ConfigMismatch(f"{final} exists")
    for k in range(shards):  # every shard published and intact before anything is written
        d = job / "shards" / f"shard_{k:05d}"
        if not d.is_dir():
            raise IntegrityError(f"shard {k} is not published")
        verify_shard(d, k, k * size, min(size, n - k * size), a.run_id)
    tries = [int(x.name.rsplit(".", 1)[1]) for x in job.glob("final.part.*")]
    tmpdir = job / f"final.part.{max(tries, default=0) + 1}"  # an interrupted attempt stays as it is
    tmpdir.mkdir()
    names = ("train.txt", "val.txt", "labels.tsv")
    fh = {nm: open(tmpdir / nm, "x", encoding="utf-8", newline="\n") for nm in names}
    expect, games = 0, {"train": set(), "val": set()}
    counts = {"train": 0, "val": 0}
    shard_hashes = []
    try:
        fh["labels.tsv"].write(LABELS_HEADER)
        for k in range(shards):
            d = job / "shards" / f"shard_{k:05d}"
            if not d.is_dir():
                raise IntegrityError(f"shard {k} is not published")
            verify_shard(d, k, k * size, min(size, n - k * size), a.run_id)
            shard_hashes.append(json.loads((d / "manifest.json").read_text(encoding="utf-8"))["labels.tsv"])
            with open(d / "labels.tsv", encoding="utf-8") as lf:
                if lf.readline() != LABELS_HEADER:
                    raise IntegrityError(f"shard {k}: labels header")
                for line in lf:
                    f = line.rstrip("\n").split("\t")
                    if int(f[0]) != expect:
                        raise IntegrityError(f"row id {f[0]} where {expect} was expected (duplicate or missing row)")
                    expect += 1
                    games[f[2]].add(f[1])
                    counts[f[2]] += 1
                    fh["labels.tsv"].write(line)
                    fh["train.txt" if f[2] == "train" else "val.txt"].write(f"{f[3]} | {f[4]} | {f[6]}\n")
        if expect != n:
            raise IntegrityError(f"{expect} rows labelled, {n} prepared")
        if games["train"] & games["val"]:
            raise IntegrityError("a game id is in both train and val")
        if (counts["train"], counts["val"]) != (info["train_rows"], info["val_rows"]):
            raise IntegrityError("split counts differ from prepare.json")
        for f in fh.values():
            f.flush()
            os.fsync(f.fileno())
    finally:
        for f in fh.values():
            f.close()
    os.rename(tmpdir, final)
    files = {nm: {"bytes": (final / nm).stat().st_size, "md5": file_hash(final / nm, "md5"),
                  "sha256": file_hash(final / nm)} for nm in names}
    man = {"run_id": a.run_id, "assembled": now(), "rows": n, "train_rows": counts["train"], "val_rows": counts["val"],
           "train_games": len(games["train"]), "val_games": len(games["val"]), "game_overlap": 0,
           "prepare_json_sha256": file_hash(job / "prepare.json"), "shard_labels_sha256": shard_hashes, "files": files}
    write_new(final / "MANIFEST.json", json.dumps(man, indent=1) + "\n")
    print(json.dumps({nm: files[nm]["md5"] for nm in names}))
    return 0


def cmd_status(a) -> int:
    job = Path(a.job)
    st = job / "status.json"
    print(st.read_text(encoding="utf-8") if st.exists() else "{}")
    parts = sorted(p.name for p in (job / "shards").glob("*.part.*")) if (job / "shards").exists() else []
    print(f"published shards: {len(list((job / 'shards').glob('shard_?????')))}; interrupted attempts kept: {parts}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--job", required=True)
    p.add_argument("--run-id", required=True)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--selfplay", nargs="+")
    g.add_argument("--normalized", nargs="+")
    p.add_argument("--rows", type=int, default=0)
    p.add_argument("--val-ppm", type=int, default=10000)
    p.add_argument("--salt", default="r14b")
    p.add_argument("--drop-terminal", action="store_true")
    p.add_argument("--mask", default="0xC")
    r = sub.add_parser("run")
    r.add_argument("--job", required=True)
    r.add_argument("--run-id", required=True)
    r.add_argument("--probe", required=True)
    r.add_argument("--nodes", type=int, default=20000)
    r.add_argument("--hash-mb", type=int, default=1)
    r.add_argument("--workers", type=int, default=1)
    r.add_argument("--shard-size", type=int, default=10000)
    r.add_argument("--mask", default="0xC")
    r.add_argument("--max-shards", type=int, default=0)
    r.add_argument("--until")
    r.add_argument("--test-kill-after-seconds", type=float, default=0.0, help=argparse.SUPPRESS)
    s = sub.add_parser("assemble")
    s.add_argument("--job", required=True)
    s.add_argument("--run-id", required=True)
    s.add_argument("--mask", default="0xC")
    t = sub.add_parser("status")
    t.add_argument("--job", required=True)
    a = ap.parse_args(argv)
    if a.cmd in ("prepare", "assemble"):
        lower_priority(int(a.mask, 16))  # run does it itself, after its configuration checks
    try:
        return {"prepare": cmd_prepare, "run": cmd_run, "assemble": cmd_assemble, "status": cmd_status}[a.cmd](a)
    except BadInput as e:
        print(f"BAD INPUT: {e}", file=sys.stderr)
        return 2
    except ConfigMismatch as e:
        print(f"CONFIG MISMATCH: {e}", file=sys.stderr)
        return 3
    except IntegrityError as e:
        print(f"INTEGRITY: {e}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    sys.exit(main())
