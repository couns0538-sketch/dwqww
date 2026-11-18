"""Run one job-14 match. Every invocation requires the preceding match gate or frozen prediction."""
import argparse
from collections import Counter
from datetime import datetime
import hashlib
import os
from pathlib import Path
import re
import shlex
import signal
import subprocess as sp
import sys
import time

STAGES = {
    # games, seed, guard A, guard B, time control A, time control B (seconds + increment).
    "C14": (200, 7361, 0, 0, "5+0.05", "10+0.1"),
    "T1": (600, 7362, 2, 0, "10+0.1", "10+0.1"),
}
EXPECTED_EXE = "ca7ef24ddd1cc80216712646bf71beaa9eacf1ac2184e0e0f11d078b10ff4f2e"
EXPECTED_BOOK = "7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a"
VERSION = "fastchess alpha 1.8.3 20261107-d7b47e8"
DEADLINE = datetime.fromisoformat("2026-11-18T23:17:00+00:00").timestamp()


def now():
    return sp.check_output(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], text=True).strip()


def hash_file(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def record_time(meta, stamps, event, match):
    line = f"{now()} {match} {event}"
    print(line, file=meta, flush=True)
    with stamps.open("a") as f:
        print(line, file=f)
    print(line, flush=True)


def preflight(exe, common, guard, meta, role):
    commands = ["uci", *common, f"setoption name NullMateGuard value {guard}", "isready", "quit"]
    print(f"{role} preflight input", *commands, sep="\n", file=meta, flush=True)
    result = sp.run([exe], cwd=exe.parent, input="\n".join(commands)+"\n", text=True, stdout=sp.PIPE,
                    stderr=sp.STDOUT, timeout=60)
    print(f"{role} preflight output", result.stdout.rstrip(), sep="\n", file=meta, flush=True)
    output = result.stdout.splitlines()
    denied = re.search(r"unknown option|invalid value|\bERROR\b", result.stdout, flags=re.IGNORECASE)
    names = {line[12:].split(" type ", 1)[0] for line in output if line.startswith("option name ")}
    expected = {command[15:].rsplit(" value ", 1)[0] for command in commands if command.startswith("setoption ")}
    if result.returncode or denied or "readyok" not in output or "uciok" not in output or names < expected or expected-names:
        raise ValueError(f"{role} preflight failed: exit {result.returncode}, refused {bool(denied)}, missing {expected-names}")


def whole_pairs(path):
    if not path.is_file():
        return None
    data = path.read_bytes()
    if not data.rstrip().endswith((b"1-0", b"0-1", b"1/2-1/2")):
        return None
    rounds = Counter(re.findall(rb'^\[Round "(\d+)"\]\r?$', data, flags=re.MULTILINE))
    return len(rounds) if rounds and set(rounds.values()) == {2} else None


def wait_match(proc, pgn, meta):
    # Clock games can end unevenly. In the final 40 seconds, stop at the first PGN
    # boundary having only complete rounds; hard-stop even if none is available.
    try:
        return proc.wait(timeout=max(0, DEADLINE - time.time() - 40)), False
    except sp.TimeoutExpired:
        pass
    previous_size = -1
    while proc.poll() is None:
        remaining = DEADLINE-time.time()
        size = pgn.stat().st_size if pgn.exists() else 0
        closed = None
        if size != previous_size:
            closed = whole_pairs(pgn)
            previous_size = size
        if closed or remaining <= 3:
            print(f"{now()} stop request; {remaining:.3f}s remaining; complete-pair boundary {closed}", file=meta,flush=True)
            proc.send_signal(signal.SIGINT)
            try:
                return proc.wait(timeout=max(0,min(2,remaining-1))),True
            except sp.TimeoutExpired:
                os.killpg(proc.pid,signal.SIGKILL)
                return proc.wait(),True
        time.sleep(min(.10, max(.001, remaining-3)))
    return proc.returncode,False


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("match", choices=STAGES)
    p.add_argument("--fastchess", type=Path, default=Path("/workspace/work/j8fast/source/fastchess"))
    p.add_argument("--exe", type=Path, default=Path("/workspace/work/j7patch/build/forge"))
    p.add_argument("--source-book", type=Path, default=Path("/workspace/work/j8gate/UHO_Lichess_4852_v1.epd"))
    p.add_argument("--book", type=Path, required=True, help="EPD filtered for this match's opening exclusions")
    p.add_argument("--book-sha", required=True, help="SHA-256 from this match's opening preflight receipt")
    p.add_argument("--settings", type=Path, default=Path("/workspace/work/j7base/pc20.txt"))
    p.add_argument("--out", type=Path, default=Path(__file__).resolve().parent/"results")
    args = p.parse_args()
    match = args.match
    games, seed, ga, gb, clock_a, clock_b = STAGES[match]
    args.out = args.out.resolve()
    for prop in ("fastchess","exe","book","source_book","settings"):
        setattr(args, prop, getattr(args,prop).resolve(strict=True))
    if time.time() >= DEADLINE:
        return 3
    nproc = int(sp.check_output(["nproc"], text=True))
    concurrency = min(3,nproc-1)
    if concurrency < 1:
        raise RuntimeError("nproc-1 gives no available match workers")
    exe_hash, book_hash, source_hash = hash_file(args.exe), hash_file(args.book), hash_file(args.source_book)
    version = sp.check_output([args.fastchess,"--version"], text=True).strip()
    if (exe_hash,source_hash,version) != (EXPECTED_EXE,EXPECTED_BOOK,VERSION):
        raise ValueError("Step 0 executable/source book/controller identity differs")
    if args.book == args.source_book or book_hash != args.book_sha:
        raise ValueError("filtered EPD identity differs")
    common = args.settings.read_text().splitlines()
    if len(common)!=22 or common[:2]!=["setoption name Threads value 1","setoption name Hash value 16"] or common[-1]!="setoption name OwnBook value false":
        raise ValueError("PC20 plus Threads and Hash settings are incomplete")
    opts=[]
    for setting in common:
        name,val = setting.removeprefix("setoption name ").split(" value ")
        opts.append(f"option.{name}={val}")
    args.out.mkdir(exist_ok=True,parents=True)
    stamps=args.out/"times.txt"
    pgn=args.out/f"{match}.pgn"
    out=args.out/f"{match}.out"
    if pgn.exists() or out.exists():
        raise FileExistsError("existing match evidence")
    command=[str(args.fastchess)]
    for role,guard,clock in (("A",ga,clock_a),("B",gb,clock_b)):
        command+=["-engine",f"name={match}-{role}",f"cmd={args.exe}",f"dir={args.exe.parent}",f"option.NullMateGuard={guard}"]
        if clock_a!=clock_b:
            command.append(f"tc={clock}")
    command += ["-each", "proto=uci"]
    if clock_a==clock_b:
        command.append(f"tc={clock_a}")
    command += [*opts, "-openings", f"file={args.book}","format=epd","order=random","-srand",str(seed),
                "-rounds",str(games//2),"-games","2","-repeat","-concurrency",str(concurrency),
                "-maxmoves","300","-pgnout",f"file={pgn}"]
    with (args.out/f"{match}.meta").open("x") as meta:
        print(f"{match}\n{version}\nengine SHA256 {exe_hash}\noriginal book {args.source_book} SHA256 {source_hash}\nfiltered EPD {args.book} SHA256 {book_hash}\nnproc {nproc}; concurrency {concurrency}\n"
              f"A tc {clock_a}, B tc {clock_b}; seed {seed}; target games {games}\ncommand {shlex.join(command)}", file=meta)
        record_time(meta,stamps,"start", match)
        try:
            preflight(args.exe, common, ga, meta, "A")
            print("A preflight PASS", file=meta, flush=True)
            print(f"{now()} fastchess launch", file=meta,flush=True)
            with out.open("xb") as log:
                proc=sp.Popen(command,cwd=args.out,stdout=log,stderr=sp.STDOUT,start_new_session=True)
                try:
                    code,cut=wait_match(proc,pgn,meta)
                finally:
                    if proc.poll() is None:
                        proc.send_signal(signal.SIGINT)
                        try:
                            proc.wait(timeout=8)
                        except sp.TimeoutExpired:
                            os.killpg(proc.pid,signal.SIGKILL)
                            proc.wait()
            print(f"exit {code}\nstatus {'incomplete; minute 50' if cut else 'ended'}",file=meta)
            return 3 if cut else code
        finally:
            record_time(meta,stamps,"end",match)


if __name__ == "__main__":
    sys.exit(main())
