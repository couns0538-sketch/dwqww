"""Run a fresh Forge process for one job 7 row set. Record every row and up to five unequal pairs per reference."""
import argparse
import csv
import hashlib
from pathlib import Path
import re
import signal
import subprocess
import time

PC20 = [
    ("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
    ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
    ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
    ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
    ("IirDepth", "2"), ("NonPawnCorrection", "true"), ("CuckooRep", "true"),
    ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
    ("MateAlphaGuard", "true"), ("OwnBook", "false"),
]
P_FEN = "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1"
SUITE = ("index", "fen", "nodes", "bestmove")
LADDER = ("requested_depth", "info_depth", "bestmove", "score_type", "score", "nodes", "mate_found", "info")
CHECKSUM = "30ab43b4ba5db5f3"
DEFAULT_DEADLINE = "2026-11-18T15:54:41Z"


def sha(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def read(path):
    with path.open() as f:
        return list(csv.DictReader(f, delimiter="\t"))


def send(process, log, command):
    log.write("> " + command + "\n")
    process.stdin.write(command + "\n")
    process.stdin.flush()


def receive(process, log, marker):
    lines = []
    for text in process.stdout:
        line = text.rstrip()
        if not (line.startswith("option name") or line.startswith("info depth")) or line.startswith("option name NullMateGuard "):
            log.write("< " + text)
        if any(error in line.lower() for error in ("unknown option", "invalid value", "info string error")):
            raise ValueError("engine diagnostic " + line)
        lines.append(line)
        if line == marker or line.startswith(marker + " "):
            return lines
    raise ValueError(f"engine closed before {marker}")


def compare(row, exp, cols):
    for col in cols:
        val1, val2 = row[col], exp[col]
        if col == "info":
            val1, val2 = (re.sub(r"\b(time|nps) \d+", r"\1", val) for val in (val1, val2))
        if val1 != val2:
            return False
    return True


def run(args, checks):
    exe = args.exe.resolve(strict=True)
    source = read(args.fens)
    size = {"O": 200, "G": 353, "P": 20}[args.suite]
    ladder = args.suite == "P"
    if len(source) != size:
        raise ValueError(f"FEN source has {len(source)} rows, expected {size}")
    columns = LADDER if ladder else SUITE
    refs = [(p, read(p)) for p in [args.reference, *args.also_ref]]
    if any(len(data) != size for _, data in refs):
        raise ValueError("reference row count differs from workload size")
    settings = [("Threads", "1"), ("Hash", "16"), *PC20, ("NullMateGuard", str(args.guard))]
    if args.net:
        settings += [("NNUEArchFile", str(args.net.resolve(strict=True))), ("NNUEArch", "true")]
    settings_text = "\n".join(f"setoption name {k} value {v}" for k, v in settings)
    ref_print = "\n".join(f"reference {path} sha256 {sha(path)}" for path, _ in refs)
    (args.out / "settings.txt").write_text(
        f"exe {exe}\nsha256 {sha(exe)}\ncwd {exe.parent}\nsuite {args.suite}\n"
        f"ordered workload {args.fens} sha256 {sha(args.fens)}\n{ref_print}\n"
        + (f"net file sha256 {sha(args.net)}\n" if args.net else "evaluation built-in\n")
        + settings_text + "\n")
    mismatches = [0] * len(refs)
    nodes = []
    first_mate = None
    with (args.out / "rows.tsv").open("x") as rows, (args.out / "run.log").open("x") as log, (
        args.out / "differences.tsv").open("x") as diffs:
        difference = csv.writer(diffs, delimiter="\t", lineterminator="\n")
        difference.writerow(("reference", "position", "side", *columns))
        writer = csv.DictWriter(rows, columns, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        proc = subprocess.Popen([str(exe)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                cwd=exe.parent, text=True, bufsize=1)
        try:
            send(proc, log, "uci")
            declarations = receive(proc, log, "uciok")
            options = {match[1] for line in declarations if (match := re.match(r"^option name (.+?) type ", line))}
            if not all(name in options for name, _ in settings):
                raise ValueError(f"UCI list missing one or more settings: {set(name for name, _ in settings)-options}")
            if "option name NullMateGuard type spin default 0 min 0 max 2" not in declarations:
                raise ValueError("wrong NullMateGuard declaration")
            if "NullChildFloor" in options:
                raise ValueError("unexpected floor option")
            for command in settings_text.splitlines():
                send(proc, log, command)
            send(proc, log, "isready")
            ready = receive(proc, log, "readyok")
            if args.net:
                for phrase in ("NNUE v3 loaded", "NNUE v3 active"):
                    marker = next((line for line in ready if phrase in line and "checksum " + CHECKSUM in line), None)
                    if marker is None:
                        raise ValueError("missing checked network marker " + phrase)
                    print(marker, file=checks, flush=True)
            for i, input_row in enumerate(source, 1):
                fen = P_FEN if ladder else input_row["fen"]
                if not ladder and int(input_row["index"]) != i:
                    raise ValueError("input indexes out of order")
                depth = i if ladder else 12
                send(proc, log, "ucinewgame")
                send(proc, log, "isready")
                receive(proc, log, "readyok")
                send(proc, log, "position fen " + fen)
                send(proc, log, f"go depth {depth}")
                response = receive(proc, log, "bestmove")
                last = next(line for line in reversed(response) if line.startswith("info depth ") and " nodes " in line)
                log.write("final " + last + "\n")
                actual_depth = re.search(r"\bdepth (\d+)", last)[1]
                if int(actual_depth) != depth:
                    raise ValueError(f"requested depth {depth} but engine reported {actual_depth}")
                node = re.search(r"\bnodes (\d+)", last)[1]
                bestmove = response[-1].split()[1]
                if ladder:
                    kind, score = re.search(r"\bscore (mate|cp) ([+-]?\d+)", last).groups()
                    mate = bestmove == "g3g6" and kind == "mate" and int(score) > 0
                    if mate and first_mate is None:
                        first_mate = (depth, int(node))
                    row = dict(requested_depth=str(i), info_depth=actual_depth, bestmove=bestmove, score_type=kind,
                               score=score, nodes=node, mate_found=str(int(mate)), info=last)
                else:
                    row = dict(index=str(i), fen=fen, nodes=node, bestmove=bestmove)
                writer.writerow(row)
                nodes.append(int(node))
                for refidx, (path, data) in enumerate(refs):
                    expected = data[i - 1]
                    if not compare(row, expected, columns):
                        mismatches[refidx] += 1
                        if mismatches[refidx] <= 5:
                            for side, rec in (("expected", expected), ("observed", row)):
                                difference.writerow((path, i, side, *(rec[key] for key in columns)))
                rows.flush()
                diffs.flush()
                log.flush()
            send(proc, log, "quit")
            if proc.wait(timeout=10):
                raise ValueError(f"engine exit code {proc.returncode}")
        finally:
            if proc.poll() is None:
                proc.kill()
            proc.wait()
            proc.stdin.close()
            proc.stdout.close()
    for (path, _), count in zip(refs, mismatches):
        print(f"matched {size-count}/{size}; differences {count}; reference {path}", file=checks)
    print(f"node sum {sum(nodes)}; first three {' '.join(map(str, nodes[:3]))}", file=checks)
    if ladder:
        print(f"first g3g6 mate {first_mate}; depth 20 {nodes[-1]}", file=checks)
    return int(any(mismatches))


def main():
    import calendar
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("exe", type=Path)
    p.add_argument("suite", choices=("O", "G", "P"))
    p.add_argument("guard", type=int, choices=(0, 1, 2))
    p.add_argument("fens", type=Path)
    p.add_argument("reference", type=Path)
    p.add_argument("out", type=Path)
    p.add_argument("--net", type=Path)
    p.add_argument("--also-ref", action="append", type=Path, default=[])
    p.add_argument("--deadline", default=DEFAULT_DEADLINE)
    args = p.parse_args()
    deadline = calendar.timegm(time.strptime(args.deadline, "%Y-%m-%dT%H:%M:%SZ"))
    remaining = deadline - time.time()
    if remaining <= 0:
        p.exit(2, "minute 50 reached; no work started\n")
    def stop(signum, frame):
        raise TimeoutError("received stop signal or reached job 7 minute 50")
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGALRM, stop)
    signal.setitimer(signal.ITIMER_REAL, remaining)
    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out / "checks.txt").open("x") as checks:
        try:
            return run(args, checks)
        except (RuntimeError, ValueError, OSError, StopIteration, TimeoutError) as error:
            print("incomplete", str(error), file=checks)
            return 2


if __name__ == "__main__":
    raise SystemExit(main())
