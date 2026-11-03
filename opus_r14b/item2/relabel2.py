#!/usr/bin/env python3
"""relabel2.py - Opus R14-B item 2: sharded, resumable relabel that keeps the original FEN and splits validation by
game (own code, 2026-11-02). UNPROVEN as training data: Engine NNUE decides whether the labels are used.
Normalized (Astra JSONL) input must be in source order (source, source_row): see sort_normalized.py.

usage (python with python-chess, e.g. C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe -I -B):
  relabel2.py prepare  --job DIR --run-id ID (--selfplay FILE ... | --normalized FILE ...) [--rows N]
                       [--val-ppm 10000] [--salt S] [--drop-terminal] [--jobs 1|2]
  relabel2.py run      --job DIR --run-id ID --probe EXE [--nodes 20000] [--hash-mb 1] [--workers 1]
                       [--shard-size 10000] [--mask 0xC] [--max-shards K] [--until "YYYY-MM-DD HH:MM"]
  relabel2.py assemble --job DIR --run-id ID
  relabel2.py status   --job DIR       (one readable progress line, then status.json)
  prepare / run / assemble also take [--min-free-gb 50]: the job's drive keeps that much free (PC rule: C: and D:
  >= 50 GB); prepare and assemble refuse to start a write that would cross it, run stops before the shard that would.
Exit codes: 0 done, 2 bad input, 3 configuration differs from the job (or a target exists, the job is busy, or the
disk floor would be crossed), 4 integrity failure (a published file changed or a check failed), 1 anything else.

- prepare: every input row is validated with Astra's records.py (unchanged copy in astra/): original full FEN (castling,
  en passant, clocks kept), STM score, White result. A bad row stops with exit 2 and nothing is published. Game id =
  (origin, game index), the origin being the self-play text file a row comes from (the input file for --selfplay,
  the record's own source / source_row for --normalized; rows.tsv keeps origin index + row, prepare.json the origin
  names; a game takes the origin of its first row). All inputs are ONE stream in the given order, and a new game
  starts between two consecutive rows only when the ply does not increase, the result changes, the piece count rises
  or a castling right appears (all impossible inside one game, so a real game is never split; two games may merge,
  which cannot leak). R8 v5 self-play writes fixed 1M-position shards, so a game can run from one file into the next:
  --selfplay files must therefore be given in name order (= the order they were written), else exit 2.
  Split: sha256(salt|game id) mod 1e6 < val ppm.
  --rows N keeps whole games only (the sample ends at a game boundary). Output rows.tsv + prepare.json. Every input
  is given once (same path or same content twice -> exit 2: its games would get two ids) and hashed before and after
  it is read (a file that changes meanwhile, e.g. the self-play file still being written -> exit 2). --jobs 2 checks
  the rows of --selfplay input in two worker processes (the same rows.tsv byte for byte). An interrupted prepare
  leaves its folder as it is (rows.tsv.part, never published): prepare again into a new folder.
- run: shard k = rows [k*S, (k+1)*S). A shard is labelled in shards/shard_K.part.N (labels.tsv, manifest.json with
  sha256, summary.json with the run id; all fsynced) and published by renaming the directory to shard_K. The same
  command resumes: the configuration and the relabel2.py hash are pinned in run_config.json (exit 3 on a change;
  `--accept-new-tool` resumes on changed code, and every sessions.log line names the code hash; a run_config.json that
  is lost or damaged while shards are published is exit 4, never re-created), every published shard is
  re-hashed (exit 4 on a mismatch), interrupted .part.N directories stay as evidence (nothing is deleted or modified)
  and the shard is redone as .part.N+1. Labels come from the R13 probe (lock source d4f4312; transposition table,
  histories and caches cleared before every search), so a label depends only on FEN, nodes and hash. This process
  and the probes run at Idle priority on --mask; --workers <= 2. One process per job: prepare / run / assemble hold
  job/job.lock (released by the OS when the process ends; never deleted), a second one stops with exit 3.
- assemble: (only when every shard is published and intact) published shards in order -> final/train.txt and
  final/val.txt (self-play text format, new label) and final/labels.tsv (all columns), checked (every row id exactly
  once and in order, game ids disjoint across the splits, counts = prepare.json); MANIFEST.json (md5 + sha256) is
  written next to them and all four are published together by renaming final.part.N to final. The three data files
  contain no run id or time, so an interrupted-and-resumed job gives byte-identical files.
"""

import argparse
import ctypes
import datetime as dt
import hashlib
import json
import os
import re
import shutil
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


def move_retry(src: Path, dst: Path, replace: bool = False, tries: int = 50, wait: float = 0.2) -> None:
    """os.rename (never over an existing target) or os.replace, retried on PermissionError: on Windows a virus
    scanner, an indexer or a reader of the file can hold a handle for a moment; a rename that fails changes nothing."""
    for i in range(tries):
        try:
            (os.replace if replace else os.rename)(src, dst)
            return
        except PermissionError:
            if i == tries - 1:
                raise
            time.sleep(wait)


def write_status(path: Path, obj) -> None:
    """Status files are replaced atomically; everything else is created once. A status file that stays locked (someone
    reading it) is skipped with a warning: it is information only and must never stop the labelling."""
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(obj, indent=1) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    try:
        move_retry(tmp, path, replace=True, tries=25)
    except PermissionError as e:
        print(f"warning: {path} not updated ({e}); the next shard tries again", file=sys.stderr)


def read_json(path: Path, what: str, keys=()) -> dict:
    """A job file that is missing, unreadable, not a JSON object or lacks a key is an integrity failure (exit 4)."""
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise IntegrityError(f"{what} is missing") from None
    except (OSError, ValueError) as e:
        raise IntegrityError(f"{what} is unreadable ({type(e).__name__}: {e})") from None
    if not isinstance(obj, dict):
        raise IntegrityError(f"{what} is not a JSON object")
    missing = [k for k in keys if k not in obj]
    if missing:
        raise IntegrityError(f"{what} lacks {', '.join(missing)}")
    return obj


def numbered(parent: Path, stem: str):
    """N of every parent/<stem>.N (attempt dirs); other names there are not ours and are ignored."""
    return [int(m.group(1)) for p in parent.glob(stem + ".*") if (m := re.fullmatch(re.escape(stem) + r"\.(\d+)", p.name))]


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


def parse_line(selfplay: bool, path: str, row_no: int, line: str):
    """One input line -> (record, result token) with Astra's records.py; ValueError on bad input."""
    import records  # Astra's unchanged records.py

    if selfplay:
        if not line.strip():
            raise ValueError("empty line")
        return records.selfplay_record(line, path, row_no), line.split("|")[2].strip()
    r = records.validate_record(json.loads(line))
    if r["source_kind"] != "selfplay" or type(r["source_row"]) is not int:
        raise ValueError("needs a self-play row with an integer source_row")
    return r, RESULT_TOKEN.get(r["result_white"])


def check_row(r) -> bool:
    """Own checks after parsing; True = terminal position (no legal move). ValueError on bad input."""
    import chess

    if r["result_white"] is None:
        raise ValueError("no game result")
    if not -32767 <= r["score_stm"] <= 32767:  # engine scores are int16 (mate ~32000); prepare fuzz, 2026-11-02 21:55
        raise ValueError(f"score {r['score_stm']} outside -32767..32767")
    if not (r["fen"].isascii() and r["fen"].isprintable()):  # a tab would split rows.tsv columns
        raise ValueError("FEN contains a tab, control or non-ASCII character")
    return not any(chess.Board(r["fen"]).legal_moves)


def iter_rows(a, sources, counters, origins):
    """Yield (origin index, origin row, record, result token) in game order, validating every row.

    The origin is the self-play text file a row comes from: the input file itself for --selfplay, the record's own
    `source` / `source_row` for --normalized (one JSONL file may hold several origins). `origins` collects their
    names in order of first appearance (a game may continue from one origin into the next)."""
    origin_index = {}
    last_key = None  # normalized input: (source, source_row) increases across all files, so no row comes twice
    for si, src in enumerate(sources):
        p = Path(src["path"])
        path, file_origin = str(p), str(p.resolve())  # once per file: resolve() costs ~77 us per call on this PC
        src["read"] = True
        with open(p, encoding="utf-8-sig") as fh:
            for row_no, line in enumerate(fh, 1):
                counters["read"] += 1
                try:
                    r, token = parse_line(bool(a.selfplay), path, row_no, line)
                    if not a.selfplay:
                        key = (r["source"], r["source_row"])
                        if last_key is not None and key <= last_key:
                            raise ValueError("normalized rows must be in source order (sort by source, source_row)")
                        last_key = key
                    terminal = check_row(r)
                except Exception as e:  # noqa: BLE001 - every rejection is bad input
                    raise BadInput(f"{p}:{row_no}: {e}") from None
                if terminal:
                    if not a.drop_terminal:
                        raise BadInput(f"{p}:{row_no}: terminal position (no legal move) cannot be searched")
                    counters["terminal"] += 1
                    continue
                r["stats"] = board_stats(r["fen"])
                name, origin_row = (file_origin, row_no) if a.selfplay else (r["source"], r["source_row"])
                if name not in origin_index:
                    origin_index[name] = len(origins)
                    origins.append(name)
                yield origin_index[name], origin_row, r, token


BLOCK_LINES = 4096


def check_block(job):
    """--jobs 2 worker: parse_line + check_row for a block of self-play lines, in order, up to the first bad line."""
    path, first, lines = job
    out = []
    for i, line in enumerate(lines):
        try:
            r, token = parse_line(True, path, first + i, line)
            terminal = check_row(r)
        except Exception as e:  # noqa: BLE001 - every rejection is bad input
            return out, f"{path}:{first + i}: {e}"
        out.append((r["fen"], r["score_stm"], r["result_white"], r["ply"], token, terminal))
    return out, None


def iter_rows_parallel(a, sources, counters, origins):
    """iter_rows for --selfplay with a.jobs worker processes: the same rows, records, errors and counters in the same
    order (workers check blocks of lines; this process keeps the order, counts and names the origins). At most
    2 * jobs + 1 blocks are in flight, so memory stays small."""
    import collections
    import itertools
    import multiprocessing

    origin_index = {}
    with multiprocessing.get_context("spawn").Pool(a.jobs) as pool:
        for src in sources:
            p = Path(src["path"])
            path, name = str(p), str(p.resolve())
            src["read"] = True
            pending = collections.deque()
            with open(p, encoding="utf-8-sig") as fh:
                row_no, eof = 1, False
                while not eof or pending:
                    if not eof:
                        lines = list(itertools.islice(fh, BLOCK_LINES))
                        eof = not lines
                        if lines:
                            pending.append((row_no, pool.apply_async(check_block, ((path, row_no, lines),))))
                            row_no += len(lines)
                    if not pending or (not eof and len(pending) <= 2 * a.jobs):
                        continue
                    first, res = pending.popleft()
                    out, err = res.get()
                    for i, (fen, score, result_white, ply, token, terminal) in enumerate(out):
                        counters["read"] += 1
                        if terminal:
                            if not a.drop_terminal:
                                raise BadInput(f"{path}:{first + i}: terminal position (no legal move) cannot be searched")
                            counters["terminal"] += 1
                            continue
                        if name not in origin_index:
                            origin_index[name] = len(origins)
                            origins.append(name)
                        r = {"fen": fen, "score_stm": score, "result_white": result_white, "ply": ply,
                             "stats": board_stats(fen)}
                        yield origin_index[name], first + i, r, token
                    if err:
                        counters["read"] += 1
                        raise BadInput(err)


def input_sources(a):
    """Every input file once (by path and by content), hashed before it is read."""
    sources, seen = [], {}
    for si, path in enumerate(a.selfplay or a.normalized):
        p = Path(path)
        if not p.is_file():
            raise BadInput(f"{p}: input file not found")
        rp, h = str(p.resolve()), file_hash(p)
        # the same games twice would get two game ids each and could land in both splits
        for key in (rp.lower(), h):
            if key in seen:
                raise BadInput(f"{p}: same file or same content as input {seen[key]} (each input once)")
            seen[key] = si
        sources.append({"index": si, "path": rp, "sha256": h, "kind": "selfplay" if a.selfplay else "normalized",
                        "read": False})
    if a.selfplay:  # a game that runs from one shard into the next must meet its continuation right after it
        names = [s["path"].lower() for s in sources]
        if names != sorted(names):
            raise BadInput("give the --selfplay files in name order (the order they were written): a game can run "
                           "from one file into the next and must stay one game")
    return sources


def lock_job(job: Path):
    """Hold job/job.lock while this process works on the job: a second prepare / run / assemble on the same job stops
    with exit 3. The OS releases the lock when the process ends in any way; the file itself is never deleted."""
    fh = open(job / "job.lock", "a+b")
    try:
        if os.name == "nt":
            import msvcrt
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        fh.close()
        raise ConfigMismatch(f"{job}: another relabel2.py process is working on this job") from None
    return fh  # the caller keeps it open: closing it releases the lock


GIB = 1024 ** 3  # the PC's disk tools (pc_gate.ps1, the crew's disk_guard) count GB as GiB


def disk_check(path: Path, need_bytes: float, floor_gb: float, what: str) -> None:
    """PC rule: the job's drive keeps >= floor_gb free (C: and D: >= 50 GB); refuse what would cross it (exit 3)."""
    root = Path(path).resolve().anchor or "."
    free = shutil.disk_usage(root).free
    if free - need_bytes < floor_gb * GIB:
        raise ConfigMismatch(f"{what} needs about {need_bytes / GIB:.2f} GB on {root} but only {free / GIB:.1f} GB are free "
                             f"and {floor_gb:g} GB must stay free (--min-free-gb): free disk space, then run the same "
                             f"command again")


def open_job(job: Path):
    if not (job / "prepare.json").is_file():
        raise BadInput(f"{job}: not a prepared job (no prepare.json; after an interrupted prepare, prepare again "
                       "into a new folder)")
    return lock_job(job)


def cmd_prepare(a) -> int:
    job = Path(a.job)
    if job.exists():
        raise ConfigMismatch(f"job directory exists: {job}")
    try:  # once, up front: inside the row checks a missing module would look like a bad first input line
        import chess  # noqa: F401
        import records  # noqa: F401  (Astra's records.py, needs python-chess)
    except ImportError as e:
        raise BadInput(f"python-chess is needed ({e}); use C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe "
                       f"(python-chess 1.11.2)") from None
    sources = input_sources(a)
    # rows.tsv is ~1.4x the self-play text it comes from (89.7 MB per 1M rows from ~64 MB): plan for 1.5x
    need = 1.5 * sum(Path(s["path"]).stat().st_size for s in sources)
    if a.rows:
        need = min(need, 100.0 * a.rows)
    disk_check(job, need, a.min_free_gb, "prepare")
    job.mkdir(parents=True)
    lock = lock_job(job)  # noqa: F841 - held until the process ends
    counters, origins = {"read": 0, "terminal": 0}, []
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

    rows = (iter_rows_parallel if a.jobs > 1 else iter_rows)(a, sources, counters, origins)
    try:
        with open(tmp, "x", encoding="utf-8", newline="\n") as fh:
            fh.write(ROWS_HEADER)
            game, prev, complete = [], None, True
            for item in rows:
                r = item[2]
                if game and new_game(prev, r):  # inputs are one stream: a game may continue in the next file
                    if not emit(game, fh):
                        complete = False
                        break
                    game = []
                game.append(item)
                prev = r
            rows.close()  # after a --rows cut: stops the reading (and the --jobs workers) now
            if complete and game:
                emit(game, fh)
            fh.flush()
            os.fsync(fh.fileno())
        if st["rows"] == 0:
            raise BadInput("no rows selected (input empty, or --rows smaller than the first game)")
        for src in sources:  # e.g. the self-play file that is still being written: its hash would not fit the rows
            if src["read"] and file_hash(src["path"]) != src["sha256"]:  # files after a --rows cut do not matter
                raise BadInput(f"{src['path']}: changed while prepare read it (use finished files only)")
    except BadInput as e:
        write_new(job / "prepare_failed.json", json.dumps({"run_id": a.run_id, "time": now(), "error": str(e)}) + "\n")
        raise
    move_retry(tmp, job / "rows.tsv")
    lengths.sort()
    starts.sort()
    q = lambda v, f: v[min(len(v) - 1, int(len(v) * f))]  # noqa: E731
    info = {
        "run_id": a.run_id, "created": now(), "tool": TOOL, "tool_sha256": file_hash(__file__),
        "records_py_sha256": file_hash(HERE / "astra" / "records.py"), "inputs": sources,
        "origins": origins,  # rows.tsv `source` = index into this list, `source_row` = row in that self-play file
        "rows": st["rows"], "games": st["games"], "rows_read": counters["read"], "terminal_dropped": counters["terminal"],
        "rows_requested": a.rows, "train_rows": st["rows"] - st["val_rows"], "val_rows": st["val_rows"],
        "train_games": st["games"] - st["val_games"], "val_games": st["val_games"], "val_ppm": a.val_ppm,
        "salt": a.salt, "prepare_jobs": a.jobs,
        "game_rule": "inputs are one stream in the given order; new game when ply does not increase, result changes, "
                     "piece count rises or a castling right appears",
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
    info = read_json(job / "prepare.json", "prepare.json", ("run_id", "rows", "train_rows", "val_rows", "rows_tsv_sha256"))
    if not all(type(info[k]) is int and info[k] >= 0 for k in ("rows", "train_rows", "val_rows")) or info["rows"] < 1:
        raise IntegrityError("prepare.json: rows / train_rows / val_rows are not counts")
    try:
        same = file_hash(job / "rows.tsv") == info["rows_tsv_sha256"]
    except OSError as e:
        raise IntegrityError(f"rows.tsv is unreadable ({type(e).__name__}: {e})") from None
    if not same:
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
        want = (man["labels.tsv"], man["summary.json"])
        got = (summ["shard"], summ["first_row"], summ["rows"], summ["run_id"])
        labels = file_hash(d / "labels.tsv")
    except (OSError, ValueError, KeyError, TypeError) as e:  # missing / damaged files, a JSON that is not ours
        raise IntegrityError(f"{d.name}: unreadable manifest / summary / labels: {type(e).__name__}: {e}") from None
    if labels != want[0]:
        raise IntegrityError(f"{d.name}: labels.tsv sha256 differs from its manifest")
    if file_hash(d / "summary.json") != want[1]:
        raise IntegrityError(f"{d.name}: summary.json differs from its manifest")
    if got != (k, first, count, run_id):
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
    lock = open_job(job)  # noqa: F841 - held until the process ends
    info = load_prepare(job)
    if info["run_id"] != a.run_id:
        raise ConfigMismatch(f"run id {a.run_id} != job run id {info['run_id']}")
    if not 1 <= a.workers <= 2:
        raise ConfigMismatch("workers must be 1 or 2 (R14-B thread budget)")
    cfg = {"run_id": a.run_id, "probe": str(Path(a.probe).resolve()), "probe_sha256": file_hash(a.probe),
           "nodes": a.nodes, "hash_mb": a.hash_mb, "shard_size": a.shard_size,
           "prepare_json_sha256": file_hash(job / "prepare.json"), "tool": TOOL}
    rc = job / "run_config.json"
    tool_hash = file_hash(__file__)
    sdir = job / "shards"
    if sdir.exists() and not sdir.is_dir():
        raise IntegrityError(f"{sdir} is not a directory")
    if rc.exists():
        old = read_json(rc, "run_config.json", tuple(cfg))
        diff = [k for k in cfg if old.get(k) != cfg[k] and k not in ("probe", "tool")]
        if diff:
            raise ConfigMismatch(f"configuration differs from run_config.json: {diff}")
        # A job must not silently continue on other code: a changed relabel2.py resumes only when asked to.
        if old.get("tool_sha256") != tool_hash and not a.accept_new_tool:
            raise ConfigMismatch(f"relabel2.py changed since the job started ({str(old.get('tool_sha256'))[:8]} -> "
                                 f"{tool_hash[:8]}); pass --accept-new-tool to resume with it (logged)")
    else:
        # run_config.json pins probe / nodes / hash / shard size: without it a resume could mix labels of two settings
        if sdir.is_dir() and any(re.fullmatch(r"shard_\d{5}", p.name) for p in sdir.iterdir()):
            raise IntegrityError("run_config.json is missing but shards are published: the job's configuration is "
                                 "unknown, so a resume could mix labels; restore run_config.json or start a new job")
        write_new(rc, json.dumps(dict(cfg, created=now(), tool_sha256=tool_hash), indent=1) + "\n")
    n = info["rows"]
    shards = (n + a.shard_size - 1) // a.shard_size
    offs = row_offsets(job, a.shard_size, n)
    sdir.mkdir(exist_ok=True)
    done = set()
    for k in range(shards):
        d = sdir / f"shard_{k:05d}"
        if d.is_dir():
            verify_shard(d, k, k * a.shard_size, min(a.shard_size, n - k * a.shard_size), a.run_id)
            done.add(k)
        elif d.exists():
            raise IntegrityError(f"{d.name} exists but is not a directory")
    deadline = dt.datetime.strptime(a.until, "%Y-%m-%d %H:%M") if a.until else None
    append_log(job, f"run start run_id={a.run_id} tool={tool_hash[:16]} shards_done={len(done)}/{shards} "
                    f"workers={a.workers} test_kill_after_s={a.test_kill_after_seconds}")
    if a.test_kill_after_seconds > 0:  # proof hook: abrupt exit at an arbitrary point (like a hard kill)
        threading.Thread(target=lambda: (time.sleep(a.test_kill_after_seconds), os._exit(137)), daemon=True).start()
    t0, rows_session, shards_session = time.monotonic(), 0, 0
    status = {"run_id": a.run_id, "session_start": now(), "shards_total": shards, "rows_total": n}
    if len(done) == shards:  # every shard published and re-verified: no probe needs to start
        append_log(job, f"run end run_id={a.run_id} tool={tool_hash[:16]} shards_done={shards}/{shards} "
                        f"session_rows=0 (nothing left to label)")
        print(json.dumps(dict(status, shards_done=shards, rows_done=n, note="nothing left to label")))
        return 0
    try:
        with ProbePool(a.probe, a.nodes, a.workers, None, hash_mb=a.hash_mb, timeout=300) as pool:
            for k in range(shards):
                if k in done:
                    continue
                if a.max_shards and shards_session >= a.max_shards:
                    break
                if deadline and dt.datetime.now() >= deadline:
                    break
                try:  # a shard writes ~1 MB per 10,000 rows; stop before the drive crosses the floor
                    disk_check(job, 64 * 2 ** 20, a.min_free_gb, f"shard {k}")
                except ConfigMismatch as e:
                    append_log(job, f"run stop run_id={a.run_id} tool={tool_hash[:16]} before shard {k}: disk floor ({e})")
                    raise
                first = k * a.shard_size
                count = min(a.shard_size, n - first)
                part = sdir / f"shard_{k:05d}.part.{max(numbered(sdir, f'shard_{k:05d}.part'), default=0) + 1}"
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
                move_retry(part, sdir / f"shard_{k:05d}")  # publish (fails if it exists: never overwrites)
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
    except ConfigMismatch:
        raise  # the disk floor wrote its own stop line
    except Exception as e:  # a probe died / timed out / answered wrongly, rows.tsv changed, ...: say so
        code = 4 if isinstance(e, IntegrityError) else 2 if isinstance(e, BadInput) else 1  # as main() maps them
        append_log(job, f"run stop run_id={a.run_id} tool={tool_hash[:16]} after {shards_session} new shards: "
                        f"{type(e).__name__}: {str(e)[:500]} (exit {code}; published shards stay, the interrupted "
                        f"attempt dir is kept; the same command resumes once the cause is fixed)")
        raise
    append_log(job, f"run end run_id={a.run_id} tool={tool_hash[:16]} shards_done={len(done)}/{shards} session_rows={rows_session}")
    print(json.dumps(status))
    return 0


# ---------------------------------------------------------------- assemble

def cmd_assemble(a) -> int:
    job = Path(a.job)
    lock = open_job(job)  # noqa: F841 - held until the process ends
    info = load_prepare(job)
    rc = read_json(job / "run_config.json", "run_config.json (written by run)", ("run_id", "shard_size"))
    if type(rc["shard_size"]) is not int or rc["shard_size"] < 1:
        raise IntegrityError("run_config.json: shard_size is not a positive integer")
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
    # train.txt + val.txt + labels.tsv: 157.8 MB per 1M rows in the proof; plan for 170 bytes per row
    disk_check(job, 170.0 * n, a.min_free_gb, "assemble")
    tmpdir = job / f"final.part.{max(numbered(job, 'final.part'), default=0) + 1}"  # an interrupted attempt stays as it is
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
    files = {nm: {"bytes": (tmpdir / nm).stat().st_size, "md5": file_hash(tmpdir / nm, "md5"),
                  "sha256": file_hash(tmpdir / nm)} for nm in names}
    man = {"run_id": a.run_id, "assembled": now(), "rows": n, "train_rows": counts["train"], "val_rows": counts["val"],
           "train_games": len(games["train"]), "val_games": len(games["val"]), "game_overlap": 0,
           "prepare_json_sha256": file_hash(job / "prepare.json"), "shard_labels_sha256": shard_hashes, "files": files}
    write_new(tmpdir / "MANIFEST.json", json.dumps(man, indent=1) + "\n")
    move_retry(tmpdir, final)  # publishes the data files and their manifest together
    print(json.dumps({nm: files[nm]["md5"] for nm in names}))
    return 0


def cmd_status(a) -> int:
    """One readable line (progress, last session's rate and ETA, kept attempts, free disk), then status.json."""
    job = Path(a.job)
    if not (job / "prepare.json").is_file():
        raise BadInput(f"{job}: not a prepared job (no prepare.json)")
    n = read_json(job / "prepare.json", "prepare.json", ("rows",))["rows"]
    if type(n) is not int or n < 1:
        raise IntegrityError("prepare.json: rows is not a positive count")

    def info_file(path: Path) -> dict:  # status.json / run_config.json are information here: warn, never stop
        try:
            return read_json(path, path.name) if path.exists() else {}
        except IntegrityError as e:
            print(f"warning: {e}", file=sys.stderr)
            return {}

    status, cfg = info_file(job / "status.json"), info_file(job / "run_config.json")
    sdir = job / "shards"
    size = cfg.get("shard_size") if type(cfg.get("shard_size")) is int and cfg["shard_size"] > 0 else 0
    total = (n + size - 1) // size if size else 0
    found = sorted(int(p.name[6:]) for p in sdir.glob("shard_*") if re.fullmatch(r"shard_\d{5}", p.name)) if sdir.is_dir() else []
    published = [k for k in found if k < total]
    if found and not size:
        print(f"warning: {len(found)} shard dirs but no readable run_config.json (shard size unknown)", file=sys.stderr)
    elif found != published:
        print(f"warning: shard dirs outside this job's {total} shards: "
              f"{[f'shard_{k:05d}' for k in found if k not in published]}", file=sys.stderr)
    parts = sorted(p.name for p in sdir.glob("*.part.*")) if sdir.is_dir() else []
    done = sum(min(size, n - k * size) for k in published)
    rate = status.get("session_rows_per_hour") if type(status.get("session_rows_per_hour")) in (int, float) else 0
    eta = f"{(n - done) / rate:.1f} h" if rate and done < n else "-"
    root = job.resolve().anchor or "."
    progress = f"{len(published)}/{total} shards" if size else "shard size unknown" if found else "not run yet"
    print(f"{job}: {progress}, {done:,}/{n:,} rows ({100 * done / n:.1f} %), final {'published' if (job / 'final').is_dir() else 'not yet'}; "
          f"last session {rate:,} rows/h (updated {status.get('updated', '-')}), ETA at that rate {eta}; "
          f"unpublished attempt dirs (interrupted; during a run the newest is the shard in progress): {parts or 'none'}; "
          f"{root} free {shutil.disk_usage(root).free / GIB:.1f} GB")
    print(json.dumps(status, indent=1))
    return 0


def check_args(a) -> None:
    """Out-of-range options are bad input (exit 2) before anything starts."""
    bad = []
    if hasattr(a, "mask"):
        try:
            if int(a.mask, 16) <= 0:
                bad.append("--mask must name at least one CPU")
            elif int(a.mask, 16) >= 1 << (os.cpu_count() or 64):
                bad.append(f"--mask {a.mask} names a CPU this PC does not have ({os.cpu_count()} logical CPUs)")
        except ValueError:
            bad.append(f"--mask {a.mask!r} is not hexadecimal")
    if a.cmd == "prepare" and (a.rows < 0 or not 0 <= a.val_ppm <= 1_000_000):
        bad.append("--rows >= 0 and 0 <= --val-ppm <= 1000000")
    if a.cmd == "prepare" and (a.jobs not in (1, 2) or (a.jobs > 1 and not a.selfplay)):
        bad.append("--jobs 1 or 2 (R14-B thread budget); --jobs 2 reads --selfplay input only")
    if getattr(a, "min_free_gb", 0) < 0:
        bad.append("--min-free-gb >= 0")
    if a.cmd == "run":
        if a.nodes < 1 or a.hash_mb < 1 or a.shard_size < 1 or a.max_shards < 0:
            bad.append("--nodes, --hash-mb, --shard-size >= 1 and --max-shards >= 0")
        if not Path(a.probe).is_file():
            bad.append(f"probe {a.probe} not found")
        if a.until:
            try:
                dt.datetime.strptime(a.until, "%Y-%m-%d %H:%M")
            except ValueError:
                bad.append(f"--until {a.until!r} is not YYYY-MM-DD HH:MM")
    if bad:
        raise BadInput("; ".join(bad))


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
    p.add_argument("--jobs", type=int, default=1, help="processes that check the rows (1 or 2; same rows.tsv)")
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
    r.add_argument("--accept-new-tool", action="store_true", help="resume a job with a changed relabel2.py (logged)")
    s = sub.add_parser("assemble")
    s.add_argument("--job", required=True)
    s.add_argument("--run-id", required=True)
    s.add_argument("--mask", default="0xC")
    for sp in (p, r, s):
        sp.add_argument("--min-free-gb", type=float, default=50.0,
                        help="GB (GiB) the job's drive keeps free: refuse / stop instead of crossing it (PC rule: 50)")
    t = sub.add_parser("status")
    t.add_argument("--job", required=True)
    a = ap.parse_args(argv)
    try:
        check_args(a)
        if a.cmd in ("prepare", "run", "assemble"):
            lower_priority(int(a.mask, 16))  # before any hashing or reading (a 50M rows.tsv is ~4.5 GB)
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
