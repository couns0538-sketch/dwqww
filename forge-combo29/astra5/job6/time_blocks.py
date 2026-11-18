"""Serial O depth-12 timing for astra5 job 6. Exit 2 on a wrong sum and 3 on a deadline."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

STAGES = {"A1": (0, 0), "A2": (0, 1), "B1": (1, 2)}
SUMS = {0: 8315168, 1: 8315218, 2: 8315218}
COLS = "stage block slot arm guard cpu_id start_utc finish_utc positions nodes user_s sys_s cpu_s wall_s status".split()
LOCAL = Path(__file__).resolve().parent
DEPTH_AND_NODES = re.compile(r"\bdepth (\d+)\b.*?\bnodes (\d+)\b")


def utc():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def send(child, command):
    child.stdin.write(command + "\n")
    child.stdin.flush()


def lines(child):
    for line in child.stdout:
        line = line.rstrip()
        if "unknown option" in line.lower() or "invalid value" in line.lower() or "ERROR" in line:
            raise ValueError(line)
        yield line


def ready(child):
    send(child, "isready")
    for line in lines(child):
        if line == "readyok":
            return
    raise ValueError("engine closed before readyok")


def search(child, fen):
    send(child, "ucinewgame")
    ready(child)
    send(child, "position fen " + fen)
    send(child, "go depth 12")
    deepest = None
    for line in lines(child):
        if line.startswith("info "):
            info = DEPTH_AND_NODES.search(line)
            if info:
                deepest = int(info[1]), int(info[2])
        if line.startswith("bestmove "):
            if not deepest or deepest[0] != 12:
                raise ValueError(f"expected depth 12 when bestmove arrived, got {deepest}, FEN {fen}")
            return deepest[1]
    raise ValueError("engine closed before bestmove")


def session(row, exe, fens, settings, cpu, deadline):
    proc = None
    status = "ok"
    error = None
    start = time.perf_counter()
    row["start_utc"] = utc()
    row["positions"] = row["nodes"] = 0
    try:
        remaining = deadline - time.time()
        if remaining <= 0:
            raise TimeoutError("running deadline reached")
        signal.setitimer(signal.ITIMER_REAL, remaining)
        # The child's affinity is inherited at fork, before even the executable loader runs.
        original = os.sched_getaffinity(0)
        os.sched_setaffinity(0, {cpu})
        try:
            proc = subprocess.Popen([exe], cwd=exe.parent, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True, encoding="utf-8", bufsize=1)
        finally:
            os.sched_setaffinity(0, original)
        send(proc, "uci")
        offered = set()
        for line in lines(proc):
            if line.startswith("option name "):
                offered.add(line[12:].split(" type ", 1)[0])
            if line == "uciok":
                break
        else:
            raise ValueError("engine closed before uciok")
        if os.sched_getaffinity(proc.pid) != {cpu}:
            raise ValueError("child CPU affinity incorrect")
        for command in [*settings, "setoption name NullChildFloor value 0",
                        f"setoption name NullMateGuard value {row['guard']}"]:
            if command[15:].rsplit(" value ", 1)[0] not in offered:
                raise ValueError(f"missing engine option: {command}")
            send(proc, command)
        ready(proc)
        for fen in fens:
            row["nodes"] += search(proc, fen)
            row["positions"] += 1
        send(proc, "quit")
        for _ in lines(proc):
            pass
        if row["nodes"] != SUMS[row["guard"]]:
            status = "wrong_sum"
            error = f"expected {SUMS[row['guard']]}, got {row['nodes']}"
    except TimeoutError as exc:
        status, error = "interrupted", str(exc)
    except (Exception, KeyboardInterrupt) as exc:
        status, error = "error", repr(exc)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        if proc is not None:
            if status in ("interrupted", "error"):
                try:
                    os.kill(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            _, wstatus, usage = os.wait4(proc.pid, 0)
            proc.returncode = os.waitstatus_to_exitcode(wstatus)
            if proc.returncode and status == "ok":
                status, error = "error", f"engine exit {proc.returncode}"
            row.update(user_s=f"{usage.ru_utime:.6f}", sys_s=f"{usage.ru_stime:.6f}",
                       cpu_s=f"{usage.ru_utime + usage.ru_stime:.6f}")
        row["wall_s"] = f"{time.perf_counter() - start:.6f}"
        row["finish_utc"] = utc()
        row["status"] = status
        if proc is not None:
            proc.stdin.close()
            proc.stdout.close()
    return error


def deadline_signal(sig, frame):
    raise TimeoutError("running deadline reached")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=STAGES)
    parser.add_argument("exe_a", type=Path)
    parser.add_argument("exe_b", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--cpu", type=int, required=True)
    parser.add_argument("--deadline", required=True, help="ISO UTC deadline")
    parser.add_argument("--positions", type=Path, default=LOCAL / "O.tsv")
    parser.add_argument("--settings", type=Path, default=LOCAL / "O.meta")
    args = parser.parse_args()
    deadline = datetime.fromisoformat(args.deadline.replace("Z", "+00:00")).timestamp()
    if args.cpu not in os.sched_getaffinity(0):
        raise ValueError(f"unavailable logical CPU {args.cpu}")
    exes = {"A": args.exe_a.resolve(strict=True), "B": args.exe_b.resolve(strict=True)}
    if args.stage == "A1":
        if os.path.samefile(exes["A"], exes["B"]) or sha(exes["A"]) != sha(exes["B"]):
            raise ValueError("A1 requires distinct, byte-identical executable files")
    with args.positions.open() as source:
        positions = list(csv.DictReader(source, delimiter="\t"))
    if [int(r["index"]) for r in positions] != list(range(1, 201)):
        raise ValueError("timing requires the ordered 200-row O suite")
    fens = [r["fen"] for r in positions]
    settings = [s for s in args.settings.read_text().splitlines() if s.startswith("setoption name ")
                and "name NullMateGuard " not in s and "name NullChildFloor " not in s]
    if len(settings) != 22:
        raise ValueError("expected Threads, Hash and all 20 PC20 options")
    args.out.mkdir(exist_ok=True, parents=True)
    meta = args.out / (args.stage + ".meta.txt")
    with meta.open("x") as m:
        m.write(f"stage {args.stage}\nlogical_cpu {args.cpu}\n"
                "pin inherited sched_setaffinity, checked on child after uciok\n"
                "cpu wait4 direct engine PID user plus system; wall monotonic before fork through wait4\n"
                "warmup slot 0 uses the first arm for that block; even BAAB, odd ABBA\n"
                f"deadline {args.deadline}\npositions {args.positions} sha256 {sha(args.positions)}\n"
                f"sha256_A {sha(exes['A'])}  {exes['A']}\nsha256_B {sha(exes['B'])}  {exes['B']}\n"
                + "\n".join(settings) + "\nsetoption name NullChildFloor value 0\n"
                f"NullMateGuard A,B={STAGES[args.stage]}\n")
    signal.signal(signal.SIGALRM, deadline_signal)
    with (args.out / (args.stage + ".tsv")).open("x", newline="", buffering=1) as output:
        writer = csv.DictWriter(output, fieldnames=COLS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for block in range(1, 13):
            order = "ABBA" if block % 2 else "BAAB"
            for slot, arm in enumerate(order[0] + order):
                row = dict(stage=args.stage, block=block, slot=slot, arm=arm,
                           guard=STAGES[args.stage][arm == "B"], cpu_id=args.cpu)
                error = session(row, exes[arm], fens, settings, args.cpu, deadline)
                writer.writerow(row)
                print(f"{args.stage} block {block} slot {slot} {arm} {row['status']} "
                      f"nodes={row['nodes']} cpu={row.get('cpu_s', '')} wall={row['wall_s']}", flush=True)
                if error:
                    print(error, file=sys.stderr, flush=True)
                    return 3 if row["status"] == "interrupted" else 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
