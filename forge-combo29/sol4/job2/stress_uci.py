#!/usr/bin/env python3
"""Exercise the ten Forge r15d Job 2 UCI sequences and preserve native output."""

import argparse
from collections import Counter
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import random
import re
import selectors
import subprocess
import time


SEQUENCES = {
    1: "isready_during_infinite",
    2: "idle_stop",
    3: "consecutive_go_nodes",
    4: "ucinewgame_during_search",
    5: "hash_during_search",
    6: "quit_during_infinite",
    7: "ponderhit",
    8: "ponder_stop",
    9: "position_cache",
    10: "illegal_position_move",
}
START_MOVES = {
    *(f"{file}2{file}{rank}" for file in "abcdefgh" for rank in "34"),
    "b1a3", "b1c3", "g1f3", "g1h3",
}
E4_MOVES = {
    *(f"{file}7{file}{rank}" for file in "abcdefgh" for rank in "56"),
    "b8a6", "b8c6", "g8f6", "g8h6",
}
E4_E5_MOVES = (START_MOVES - {"e2e3", "e2e4"}) | {
    "g1e2", "f1e2", "f1d3", "f1c4", "f1b5", "f1a6", "d1e2", "d1f3", "d1g4", "d1h5", "e1e2",
}
FEN_MOVES = {"e8d7", "e8d8", "e8e7", "e8f7", "e8f8"}
ENDGAME = "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1"
BESTMOVE = re.compile(r"bestmove ([a-h][1-8][a-h][1-8][qrbn]?|0000)(?: ponder ([a-h][1-8][a-h][1-8][qrbn]?))?")
ROOT = re.compile(r"([a-h][1-8][a-h][1-8][qrbn]?): (\d+)")
NODES = re.compile(r"\bnodes (\d+)\b")
DEPTH = re.compile(r"^info depth (\d+)\b")
TSAN_REPORT = re.compile(r"^WARNING: ThreadSanitizer: (.+)$", re.M)
TSAN_FATAL = re.compile(r"ThreadSanitizer: (?:CHECK failed|DEADLYSIGNAL)|FATAL: ThreadSanitizer")
ATTACK_INIT = re.compile(r"\bforge::attacks::init\b|\bbitboard\.cpp:(?:14[2-9]|1[5-9]\d|2[0-4]\d)[:\s)]")


class CheckError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise CheckError(message)


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class Engine:
    def __init__(self, args, rng):
        self.args = args
        self.rng = rng
        self.start = time.monotonic()
        self.events = []
        self.buffers = {}
        self.raw = {"stdout": bytearray(), "stderr": bytearray()}
        self.selector = selectors.DefaultSelector()
        try:
            self.process = subprocess.Popen(
                args.command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, cwd=args.cwd, env=args.env, bufsize=0,
            )
        except BaseException:
            self.selector.close()
            raise
        for stream in self.raw:
            pipe = getattr(self.process, stream)
            self.selector.register(pipe, selectors.EVENT_READ, stream)
            self.buffers[stream] = b""

    def record(self, stream, line):
        self.events.append((round((time.monotonic() - self.start) * 1000, 3), stream, line))

    def read(self, timeout):
        for key, _ in self.selector.select(timeout):
            stream = key.data
            chunk = os.read(key.fd, 65536)
            if not chunk:
                if self.buffers[stream]:
                    self.record(stream, self.buffers[stream].decode("utf-8", errors="backslashreplace"))
                self.selector.unregister(key.fileobj)
                continue
            self.raw[stream].extend(chunk)
            lines = (self.buffers[stream] + chunk).split(b"\n")
            self.buffers[stream] = lines.pop()
            for line in lines:
                self.record(stream, line.removesuffix(b"\r").decode("utf-8", errors="backslashreplace"))

    def send(self, command, *, jitter=True):
        if jitter:
            delay = self.rng.uniform(self.args.min_sleep_ms, self.args.max_sleep_ms) / 1000
            deadline = time.monotonic() + delay
            while self.selector.get_map() and time.monotonic() < deadline:
                self.read(max(0, deadline - time.monotonic()))
        self.read(0)
        try:
            self.process.stdin.write((command + "\n").encode())
        except (BrokenPipeError, ValueError) as exc:
            raise CheckError(f"engine closed input before {command!r}") from exc
        self.record("command", command)
        return len(self.events) - 1

    def lines(self, stream, after=-1, before=None):
        return [line for _, kind, line in self.events[after + 1:before] if kind == stream]

    def expect(self, predicate, label, *, after):
        deadline = time.monotonic() + self.args.timeout
        next_index = after + 1
        while True:
            for index in range(next_index, len(self.events)):
                _, stream, line = self.events[index]
                if stream == "stdout" and predicate(line):
                    return index
            next_index = len(self.events)
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not self.selector.get_map():
                raise CheckError(f"missing {label} after {self.events[after][2]!r}")
            self.read(remaining)

    def ready(self):
        marker = self.send("isready")
        return self.expect(lambda line: line == "readyok", "readyok", after=marker)

    def best(self, after):
        return self.expect(lambda line: line.startswith("bestmove "), "bestmove", after=after)

    def running(self, go):
        marker = self.send(go)
        self.expect(DEPTH.match, "an in-search depth line", after=marker)
        return marker

    def perft(self, expected):
        marker = self.send("go perft 1")
        end = self.expect(lambda line: re.fullmatch(r"nodes \d+", line), "perft node total", after=marker)
        total = int(self.events[end][2].split()[1])
        roots = [ROOT.fullmatch(line) for line in self.lines("stdout", marker, end)]
        rows = [row.groups() for row in roots if row]
        moves = {move for move, _ in rows}
        require(total == len(rows) == len(moves) == len(expected)
                and all(nodes == "1" for _, nodes in rows),
                f"perft expected {len(expected)} unique depth-one rows, got {total} and {rows}")
        require(moves == expected, f"unexpected perft roots, missing {sorted(expected - moves)}, "
                f"extra {sorted(moves - expected)}")

    def finish(self, timeout):
        deadline = time.monotonic() + timeout
        while self.selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise CheckError("engine did not exit and close both streams after quit")
            self.read(remaining)
        try:
            return self.process.wait(timeout=max(0, deadline - time.monotonic()))
        except subprocess.TimeoutExpired as exc:
            raise CheckError("engine closed its streams but did not exit") from exc

    def close(self):
        if self.process.poll() is None:
            self.process.kill()
            self.record("runner", "killed engine after exit timeout")
        try:
            self.finish(2)
        finally:
            self.selector.close()
            for name in ("stdin", "stdout", "stderr"):
                getattr(self.process, name).close()
            self.process.wait(timeout=2)


def setup(engine, threads, sequence):
    uci = engine.send("uci")
    end = engine.expect(lambda line: line == "uciok", "uciok", after=uci)
    options = engine.lines("stdout", uci, end)
    for name, value in [("Threads", threads), ("Hash", 16), ("OwnBook", "false"),
                        ("UseNNUE", "true"), ("MultiPV", 1)]:
        require(any(line.startswith(f"option name {name} type ") for line in options),
                f"missing advertised UCI option {name!r}")
        engine.send(f"setoption name {name} value {value}")
    if sequence in (7, 8):
        engine.send("setoption name Ponder value true")
    engine.ready()
    if sequence <= 8:
        engine.send("position startpos")


def no_best_before(engine, go, command, reason):
    require(not any(line.startswith("bestmove ") for line in engine.lines("stdout", go, command)),
            f"premature bestmove {reason}")


def one_finite_go(engine):
    go = engine.send("go nodes 200")
    engine.best(go)


def run_sequence(engine, sequence, observations):
    if sequence == 1:
        go = engine.running("go infinite")
        ready = engine.ready()
        stop = engine.send("stop")
        no_best_before(engine, go, stop, "during go infinite before stop")
        observations["ready_before_stop"] = ready < stop
        engine.best(stop)
    elif sequence == 2:
        stop = engine.send("stop")
        engine.ready()
        go = engine.send("go nodes 200")
        no_best_before(engine, stop, go, "after an idle stop")
        engine.best(go)
    elif sequence == 3:
        first = engine.send("go nodes 20000")
        second = engine.send("go nodes 20000")
        finished = any(line.startswith("bestmove ") for line in engine.lines("stdout", first, second))
        observations["first_bestmove_before_second_go"] = finished
        if not finished:
            engine.best(engine.best(second))
        else:
            engine.best(second)
    elif sequence in (4, 5):
        go = engine.running("go infinite")
        action = engine.send("ucinewgame" if sequence == 4 else "setoption name Hash value 32")
        no_best_before(engine, go, action, "while the infinite search was running")
        best = engine.best(action)
        ready = engine.ready()
        observations["old_bestmove_before_readyok"] = best < ready
        one_finite_go(engine)
    elif sequence == 6:
        go = engine.running("go infinite")
        quit_at = engine.send("quit")
        no_best_before(engine, go, quit_at, "during go infinite before quit")
    elif sequence in (7, 8):
        go = engine.running("go ponder wtime 1000 btime 1000 winc 0 binc 0")
        action = engine.send("ponderhit" if sequence == 7 else "stop")
        no_best_before(engine, go, action, "while pondering")
        engine.best(action)
        engine.ready()
    elif sequence == 9:
        engine.send("position startpos moves e2e4")
        engine.send("position startpos moves e2e4 e7e5")
        engine.send(f"position fen {ENDGAME} moves e2e4")
        engine.perft(FEN_MOVES)
        engine.send("position startpos moves e2e4")
        engine.perft(E4_MOVES)
        engine.send("position startpos moves e2e4 e7e5")
        engine.perft(E4_E5_MOVES)
    elif sequence == 10:
        engine.send("position startpos moves d2d4")
        illegal = engine.send("position startpos moves e2e4 e7e4 g1f3")
        end = engine.ready()
        lines = engine.lines("stdout", illegal, end)
        require(lines.count("info string illegal move e7e4") == 1,
                f"expected one illegal-move diagnostic, got {lines}")
        engine.perft(E4_MOVES)


def check_transcript(engine, sequence):
    commands = engine.lines("command")
    stdout = engine.lines("stdout")
    starts = [line for line in commands if line.startswith("go ") and not line.startswith("go perft ")]
    bestmoves = [line for line in stdout if line.split()[:1] == ["bestmove"]]
    require(len(bestmoves) == len(starts) or (sequence == 6 and not bestmoves),
            f"expected {len(starts)} bestmove replies for {starts}, got {bestmoves}")
    require(stdout.count("readyok") == commands.count("isready"), "mismatched isready/readyok counts")
    require(stdout.count("uciok") == commands.count("uci"), "mismatched uci/uciok counts")
    for line in bestmoves:
        move = BESTMOVE.fullmatch(line)
        require(move and move[1] in START_MOVES, f"malformed or illegal start-position bestmove {line!r}")


def search_observations(events):
    searches = []
    for _, source, line in events:
        if source == "command" and line.startswith("go ") and not line.startswith("go perft "):
            nodes = NODES.search(line)
            searches.append({"go": line, "requested_nodes": int(nodes[1]) if nodes else None,
                             "last_info_nodes": None, "last_info_depth": None, "bestmove": None})
        elif searches and source == "stdout":
            search = next((entry for entry in searches if entry["bestmove"] is None), None)
            if search is None:
                continue
            if line.startswith("bestmove "):
                search["bestmove"] = line
            else:
                depth = DEPTH.match(line)
                nodes = NODES.search(line)
                if depth and nodes:
                    search["last_info_nodes"] = int(nodes[1])
                    search["last_info_depth"] = int(depth[1])
    return searches


def tsan_reports(stderr):
    matches = list(TSAN_REPORT.finditer(stderr))
    reports = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(stderr)
        body = stderr[match.end():end]
        frames = []
        for line in body.splitlines():
            if re.match(r"\s*#0\b", line):
                frames.append(line.strip())
        reports.append({
            "warning": match[1],
            "first_frames": frames,
            "attack_init_path": bool(ATTACK_INIT.search(body)),
        })
    return reports


def trial(args, sequence, threads, number):
    seed = args.seed + 1000003 * sequence + 10007 * threads + number
    result = {
        "sequence": sequence, "name": SEQUENCES[sequence], "threads": threads,
        "trial": number, "seed": seed, "started_utc": utc_now(), "errors": [],
        "observations": {}, "returncode": None,
    }
    try:
        engine = Engine(args, random.Random(seed))
    except OSError as exc:
        result["errors"].append(str(exc))
        return result, [], {"stdout": b"", "stderr": b""}

    try:
        setup(engine, threads, sequence)
        run_sequence(engine, sequence, result["observations"])
    except (CheckError, OSError) as exc:
        result["errors"].append(str(exc))
    finally:
        try:
            if "quit" not in engine.lines("command") and engine.process.poll() is None:
                engine.send("quit", jitter=False)
            engine.finish(args.timeout)
        except (CheckError, OSError) as exc:
            result["errors"].append(str(exc))
        finally:
            try:
                engine.close()
            except (CheckError, OSError, subprocess.TimeoutExpired) as exc:
                result["errors"].append(str(exc))
    result["returncode"] = engine.process.returncode
    result["ended_utc"] = utc_now()
    stderr = engine.raw["stderr"].decode("utf-8", errors="backslashreplace")
    result["tsan_reports"] = tsan_reports(stderr)
    result["tsan_runtime_failure"] = bool(TSAN_FATAL.search(stderr))
    result["searches"] = search_observations(engine.events)
    if not result["errors"]:
        try:
            check_transcript(engine, sequence)
        except CheckError as exc:
            result["errors"].append(str(exc))
    if result["tsan_runtime_failure"]:
        result["errors"].append("ThreadSanitizer runtime failed")
    if result["returncode"] != 0 and not (args.mode == "positive" and result["tsan_reports"]):
        result["errors"].append(f"engine exited with status {result['returncode']}")
    return result, engine.events, engine.raw


def record_trial(files, result, events, raw):
    header = (f"\n=== sequence={result['sequence']} {result['name']} threads={result['threads']} "
              f"trial={result['trial']} seed={result['seed']} started_utc={result['started_utc']} ===\n")
    for stream in ("stdout", "stderr"):
        files[stream].write(header.encode())
        files[stream].write(raw[stream])
        files[stream].write(f"\n=== returncode={result['returncode']} ===\n".encode())
        files[stream].flush()
    files["trace"].write(header)
    for ms, stream, line in events:
        files["trace"].write(f"{ms:12.3f} ms {stream:7s} {line}\n")
    files["trace"].write(f"=== returncode={result['returncode']} errors={result['errors']} ===\n")
    files["trace"].flush()
    files["results"].write(json.dumps(result) + "\n")
    files["results"].flush()


def tests(args):
    for number in range(1, args.repeat + 1):
        for sequence in args.sequences:
            for threads in args.threads:
                yield sequence, threads, number


def run(args, files):
    groups = {(sequence, threads): Counter() for sequence in args.sequences for threads in args.threads}
    pending_cases = iter(tests(args))
    runtime_failures = 0
    stop_reason = None
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        active = set()
        while True:
            while not stop_reason and len(active) < args.workers:
                case = next(pending_cases, None)
                if case is None:
                    break
                active.add(pool.submit(trial, args, *case))
            if not active:
                break
            complete, active = wait(active, return_when=FIRST_COMPLETED)
            for future in complete:
                result, events, raw = future.result()
                record_trial(files, result, events, raw)
                reports = result.get("tsan_reports", [])
                counters = groups[result["sequence"], result["threads"]]
                counters["completed"] += 1
                counters["failed"] += bool(result["errors"])
                counters["tsan_reports"] += len(reports)
                counters["tsan_data_races"] += sum(item["warning"].startswith("data race") for item in reports)
                counters["attack_init_reports"] += sum(item["attack_init_path"] for item in reports)
                counters["runtime_failures"] += bool(result.get("tsan_runtime_failure"))
                if result["sequence"] == 3 and "first_bestmove_before_second_go" in result["observations"]:
                    key = ("first_already_done" if result["observations"]["first_bestmove_before_second_go"]
                           else "first_still_pending")
                    counters[key] += 1
                runtime_failures += bool(result.get("tsan_runtime_failure"))
                if result["errors"] or reports or counters["completed"] % args.progress_every == 0:
                    print(f"sequence={result['sequence']} threads={result['threads']} "
                          f"trial={result['trial']} completed={counters['completed']} "
                          f"reports={len(reports)} errors={result['errors']}", flush=True)
                if args.fatal_limit and runtime_failures >= args.fatal_limit:
                    stop_reason = f"ThreadSanitizer runtime failed {runtime_failures} times"
                if args.stop_on_positive and counters["tsan_data_races"]:
                    stop_reason = "observed a ThreadSanitizer data race in positive control"
    return groups, stop_reason


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--engine-arg", action="append", default=[])
    parser.add_argument("--out", type=Path, required=True, help="new directory for this run")
    parser.add_argument("--cwd", type=Path, help="optional working directory for the engine")
    parser.add_argument("--label", default="", help="build or evidence label")
    parser.add_argument("--mode", choices=("clean", "positive"), default="clean")
    parser.add_argument("--repeat", type=int, default=100)
    parser.add_argument("--threads", type=int, nargs="+", choices=(1, 2), default=[1, 2])
    parser.add_argument("--sequences", type=int, nargs="+", choices=SEQUENCES, default=list(SEQUENCES))
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--seed", type=int, default=20261118)
    parser.add_argument("--min-sleep-ms", type=float, default=0.1)
    parser.add_argument("--max-sleep-ms", type=float, default=3.0)
    parser.add_argument("--timeout", type=float, default=10.0, help="seconds per protocol wait or exit")
    parser.add_argument("--progress-every", type=int, default=25)
    parser.add_argument("--fatal-limit", type=int, default=0, help="stop scheduling after N TSan runtime failures")
    parser.add_argument("--stop-on-positive", action="store_true")
    parser.add_argument("--tsan-options", default=os.environ.get("TSAN_OPTIONS", "halt_on_error=0:exitcode=66"))
    args = parser.parse_args()
    if min(args.repeat, args.workers, args.timeout, args.progress_every) <= 0:
        parser.error("repeat, workers, timeout and progress interval must be positive")
    if not 0 <= args.min_sleep_ms <= args.max_sleep_ms or args.fatal_limit < 0:
        parser.error("invalid sleep range or fatal limit")
    if args.stop_on_positive and args.mode != "positive":
        parser.error("--stop-on-positive requires --mode positive")
    if len(set(args.sequences)) != len(args.sequences) or len(set(args.threads)) != len(args.threads):
        parser.error("duplicate sequence or thread selections")
    args.engine = args.engine.resolve(strict=True)
    args.out.mkdir(parents=True, exist_ok=False)
    args.command = [str(args.engine), *args.engine_arg]
    args.env = {**os.environ, "TSAN_OPTIONS": args.tsan_options}
    with args.engine.open("rb") as binary:
        sha = hashlib.file_digest(binary, "sha256").hexdigest()
    with (args.out / "run.json").open("w", encoding="utf-8") as output:
        config = {key: str(value) if isinstance(value, Path) else value
                  for key, value in vars(args).items() if key != "env"}
        json.dump({**config, "engine_sha256": sha, "started_utc": utc_now(),
                   "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   "options": {"Hash": 16, "OwnBook": False, "UseNNUE": True, "MultiPV": 1},
                   "node_counter": "last completed info depth value, not final search nodes"},
                  output, indent=2)
        output.write("\n")
    with (
        (args.out / "trace.txt").open("w", encoding="utf-8") as trace,
        (args.out / "stdout.txt").open("wb") as stdout,
        (args.out / "stderr.txt").open("wb") as stderr,
        (args.out / "results.jsonl").open("w", encoding="utf-8") as results,
    ):
        groups, stop_reason = run(args, {"trace": trace, "stdout": stdout, "stderr": stderr, "results": results})
    rows = [{"sequence": sequence, "name": SEQUENCES[sequence], "threads": threads,
             "planned": args.repeat, **dict(counters)} for (sequence, threads), counters in groups.items()]
    failures = sum(row.get("failed", 0) for row in rows)
    reports = sum(row.get("tsan_reports", 0) for row in rows)
    races = sum(row.get("tsan_data_races", 0) for row in rows)
    incomplete = any(row.get("completed", 0) != row["planned"] for row in rows)
    positive_pass = races > 0 and not any(row.get("runtime_failures", 0) for row in rows)
    status = positive_pass if args.mode == "positive" else not (incomplete or failures or reports)
    summary = {"ended_utc": utc_now(), "passed": status, "mode": args.mode, "incomplete": incomplete,
               "stop_reason": stop_reason, "failures": failures, "tsan_reports": reports,
               "tsan_data_races": races, "groups": rows}
    with (args.out / "summary.json").open("w", encoding="utf-8") as output:
        json.dump(summary, output, indent=2)
        output.write("\n")
    print(json.dumps(summary), flush=True)
    return 0 if status else 1


if __name__ == "__main__":
    raise SystemExit(main())
