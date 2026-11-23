"""Reproduce server-day failure-table cases 8 to 12 on the first package.

Run one case at a time. Exit 0 means its acceptance condition holds; 1 means
the case exposes a failure; 2 means the harness or its dependencies are missing.
All generated data and subprocess output go to a new temporary directory.
"""
import argparse
import contextlib
import hashlib
import io
import json
import lzma
import os
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch


def run_worker(args, spool, run_id, root_seed, games, until=None):
    command = [sys.executable, "-I", "-B", str(args.scripts / "run/worker.py"),
               "--exe", str(args.forge.resolve()), "--net", str(args.net.resolve()),
               "--manifest", str(args.scripts / "workloads/MANIFEST.json"),
               "--known-startup", str(args.scripts / "known/startup.json"),
               "--spool", str(spool), "--run-id", run_id, "--root-seed", root_seed,
               "--worker", "0", "--games", str(games), "--piece-games", "1"]
    if until is not None:
        command.extend(["--until", str(until)])
    return subprocess.run(command, text=True, capture_output=True, timeout=120)


def case8(args, work):
    spool = work / "spool"
    old = run_worker(args, spool, "oldrun", "seedA", 1)
    if old.returncode != 0:
        raise RuntimeError("The control did not pass the PC start checks: " + old.stdout[-250:])
    journal = spool / "w000/journal.txt"
    before = journal.read_bytes()
    if b"done oldrun-w000-g00000001 " not in before:
        raise RuntimeError("Control failed to persist its one complete game")
    new = run_worker(args, spool, "newrun", "seedB", 2)
    after = journal.read_bytes()
    new_ids = [line.split()[1] for line in after.decode().splitlines()
               if line.startswith("done newrun-")]
    print("restart exit", new.returncode, "new games", new_ids)
    return new.returncode != 0 and not new_ids and after == before


def case9(args, work):
    spool = work / "spool"
    result = run_worker(args, spool, "cutoff", "seedA", 1, until=time.time() - 60)
    journal = spool / "w000/journal.txt"
    rows = journal.read_text().splitlines() if journal.is_file() else []
    launches = [line for line in rows if line.startswith("engine_started ")]
    print("expired production cutoff: engine launches that completed a search",
          len(launches), "completed games", sum(line.startswith("done ") for line in rows))
    return len(launches) == 0 and not any(line.startswith("done ") for line in rows)


def case10(args, work):
    import uciproc

    def exercise(arrival_spacing):
        class ScheduledLines:
            def __init__(self):
                self.clock = 0.0
                self.index = 0

            def get(self, timeout):
                # Model Queue.get precisely: a result arriving after the allowed
                # wait is unavailable. Both time sources progress deterministically.
                arrival = (self.index + 1) * arrival_spacing
                if arrival > self.clock + timeout + 1e-10:
                    self.clock += timeout
                    raise queue.Empty
                self.clock = arrival
                self.index += 1
                return "bestmove e2e4" if self.index == 40 else "info depth 8"

        stream = ScheduledLines()
        engine = uciproc.Engine.__new__(uciproc.Engine)
        engine.log, engine.q = None, stream
        with patch.object(uciproc.time, "time", lambda: stream.clock), \
             patch.object(uciproc.time, "monotonic", lambda: stream.clock):
            try:
                engine.read_until(lambda line: line.startswith("bestmove"), 0.2, "test search")
            except uciproc.EngineError:
                return "timed out", round(stream.clock, 5)
        return "accepted", round(stream.clock, 5)

    fast, slow = exercise(0.02), exercise(0.3)
    print("200-ms limit, 20-ms progress intervals", fast, "300-ms intervals", slow)
    return fast[0] == "timed out" and slow[0] == "timed out"


def case11(args, work):
    import chess
    import record
    import receiver

    moves = "e2e4 e7e5 g1f3 b8c6 f1b5 a7a6 b5a4 g8f6".split()
    board = chess.Board()
    for move in moves:
        board.push_uci(move)
    possible = board.legal_moves.count()
    if possible != 27:
        raise RuntimeError("Fixture expected 27 legal moves")
    openings = work / "openings.txt"
    openings.write_text(" ".join(moves) + "\n", encoding="ascii")
    raw = record.text("case-w000-g00000001", moves, "none", [],
                      "openingend plies 8 reason nomoves").encode("ascii")
    data = lzma.compress(raw)
    folder = work / "inbox/w000"
    folder.mkdir(parents=True)
    (folder / "p000000.raw.xz").write_bytes(data)
    (folder / "p000000.packed").write_text(
        f"{hashlib.sha256(data).hexdigest()}  {len(data)}  p000000.raw.xz\n"
        f"form rawxz games 1 rows 0 raw_bytes {len(raw)} raw_sha256 {hashlib.sha256(raw).hexdigest()}\n",
        encoding="ascii")
    command = ["receiver", "--inbox", str(folder.parent), "--state", str(work / "state"),
               "--root-seed", "trial", "--openings", str(openings), "--converter", sys.executable]
    # rawxz never invokes the converter.
    with patch.object(sys, "argv", command), contextlib.redirect_stdout(io.StringIO()):
        result = receiver.main()
    summary_file = work / "state/summary.json"
    if result or not summary_file.exists():
        raise RuntimeError("Could not run the raw compressed receiver path")
    summary = json.loads(summary_file.read_bytes())["in_all"]
    print("legal moves", possible, "reported empty", summary["no_rows"], "refused", summary["refused"])
    return summary["no_rows"] == 0 and summary["refused"] == 1


def case12(args, work):
    import packer
    import record

    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    text = record.text("case-w000-g00000001", [], "position startpos", ["sg 0 24 e2e4 " + fen],
                       "sgend result 1 reason score plies 1 run 1 searches 1 nodes 2000 moves e2e4")
    raw = work / "w000/closed/p000000.raw"
    raw.parent.mkdir(parents=True)
    raw.write_bytes(text.encode("ascii"))
    raw.with_suffix(".sha256").write_text(hashlib.sha256(raw.read_bytes()).hexdigest() + "\n")
    out = work / "offers"

    def converter(_exe, src, dst):
        # An intentionally tiny test double isolates the result field. It is
        # not a Stockfish converter or a measurement of compression efficiency.
        data = src.read_bytes()
        if src.suffix == ".binpack":
            if data.count(b"result 1\n") != 1:
                raise RuntimeError("Fixture expected exactly one white-to-move result of +1")
            data = data.replace(b"result 1\n", b"result -1\n")
        dst.write_bytes(data)

    with patch.object(packer, "convert", converter):
        form = packer.pack_piece(raw, out, "test-double", lambda message: None)
    print("offered format after converter changed only result", form)
    return form == "rawxz" and lzma.decompress((out / "p000000.raw.xz").read_bytes()) == raw.read_bytes()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scripts", required=True, type=Path)
    parser.add_argument("--work-dir", type=Path, help="parent directory for the private case folder")
    parser.add_argument("--forge", type=Path)
    parser.add_argument("--net", type=Path)
    parser.add_argument("case", type=int, choices=range(8, 13))
    args = parser.parse_args()
    args.scripts = args.scripts.resolve()
    if args.case in (8, 9) and not all(p and p.is_file() for p in (args.forge, args.net)):
        parser.error("Cases 8 and 9 require --forge and --net pointing to the matching build and frozen net")
    sys.path[:0] = [str(args.scripts / "run"), str(args.scripts / "home")]
    cases = {8: case8, 9: case9, 10: case10, 11: case11, 12: case12}
    try:
        if args.work_dir is not None:
            args.work_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=f"forge-case-{args.case}-", dir=args.work_dir) as directory:
            child_tmp = str(Path(directory).resolve())
            with patch.dict(os.environ, {"TMP": child_tmp, "TEMP": child_tmp, "TMPDIR": child_tmp}):
                sys.dont_write_bytecode = True
                accepted = cases[args.case](args, Path(child_tmp))
    except (ImportError, OSError, RuntimeError, KeyError, subprocess.SubprocessError) as error:
        print("TEST INCOMPLETE", error)
        return 2
    print("PASS" if accepted else "FAIL", "case", args.case)
    return 0 if accepted else 1


if __name__ == "__main__":
    sys.exit(main())
