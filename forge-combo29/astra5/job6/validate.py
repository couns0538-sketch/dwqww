"""Compare job 6 value 2 to frozen job 5 value 1. Use EXE REF_DIR OUTPUT_DIR."""
import argparse
import csv
import hashlib
from pathlib import Path
import re
import signal
import subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def send(engine, command, transcript):
    if transcript:
        transcript.write("> " + command + "\n")
    engine.stdin.write(command + "\n")
    engine.stdin.flush()


def until(engine, stop, transcript=None):
    for raw in engine.stdout:
        line = raw.rstrip()
        if transcript:
            transcript.write("< " + raw)
        if any(message in line.lower() for message in ("unknown option", "invalid value", "error")):
            raise RuntimeError(line)
        yield line
        if line == stop or (stop == "bestmove" and line.startswith("bestmove ")):
            return
    raise RuntimeError("unexpected end of engine output awaiting " + stop)


def normalized_info(info):
    return re.sub(r"\b(nps|time) \d+", r"\1 <variable>", info)


def validate(label, exe, ref, out, log):
    expected_path = ref / (label + ".tsv")
    is_ladder = label == "P"
    with expected_path.open() as f:
        expected = list(csv.DictReader(f, delimiter="\t"))
    counts = {"P": 20, "O": 200, "G": 353}
    if len(expected) != counts[label]:
        raise ValueError(f"bad {label} reference count {len(expected)}")
    reference_meta = ref / ("P.meta" if is_ladder else label + ".tsv.meta")
    metadata = reference_meta.read_text().splitlines()
    options = [line for line in metadata if line.startswith("setoption name ")]
    if options.pop() != "setoption name NullMateGuard value 1":
        raise ValueError(f"unexpected {label} reference options")
    options.extend(["setoption name NullChildFloor value 0", "setoption name NullMateGuard value 2"])
    fixed_fen = next((line[4:] for line in metadata if line.startswith("fen ")), None)
    engine = subprocess.Popen([str(exe)], cwd=exe.parent, text=True, bufsize=1, stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    transcript = (out / "P.raw.txt").open("x") if is_ladder else None
    nodes = []
    try:
        send(engine, "uci", transcript)
        declaration = list(until(engine, "uciok", transcript))
        guard = next(line for line in declaration if line.startswith("option name NullMateGuard "))
        if not re.search(r"\bmin 0 max 2\b", guard):
            raise ValueError("unexpected guard declaration " + guard)
        for option in options:
            send(engine, option, transcript)
        send(engine, "isready", transcript)
        list(until(engine, "readyok", transcript))
        (out / (label + ".meta.txt")).write_text(
            f"exe {exe}\nsha256 {sha(exe)}\ncwd {exe.parent}\nreference {expected_path}\n"
            f"reference_sha256 {sha(expected_path)}\n{guard}\n" + "\n".join(options) + "\n")
        with (out / (label + ".tsv")).open("x") as f:
            writer = csv.DictWriter(f, list(expected[0]), delimiter="\t", lineterminator="\n")
            writer.writeheader()
            for i, reference in enumerate(expected, 1):
                fen = fixed_fen if is_ladder else reference["fen"]
                depth = i if is_ladder else 12
                send(engine, "ucinewgame", transcript)
                send(engine, "isready", transcript)
                list(until(engine, "readyok", transcript))
                send(engine, "position fen " + fen, transcript)
                send(engine, f"go depth {depth}", transcript)
                lines = list(until(engine, "bestmove", transcript))
                last = next(line for line in reversed(lines) if re.match(r"info depth \d+", line) and " nodes " in line)
                node = re.search(r"\bnodes (\d+)", last)[1]
                move = lines[-1].split()[1]
                actual_depth = re.search(r"\bdepth (\d+)", last)[1]
                if is_ladder:
                    score_type, score = re.search(r"\bscore (mate|cp) ([+-]?\d+)", last).groups()
                    found = move == "g3g6" and score_type == "mate" and int(score) > 0
                    observed = dict(requested_depth=str(depth), info_depth=actual_depth, bestmove=move,
                                    score_type=score_type, score=score, nodes=node, mate_found=str(int(found)), info=last)
                else:
                    observed = dict(index=str(i), fen=fen, nodes=node, bestmove=move)
                writer.writerow(observed)
                f.flush()
                if actual_depth != str(depth) or any(
                    (normalized_info(observed[k]) != normalized_info(v) if k == "info" else observed[k] != v)
                    for k, v in reference.items()
                ):
                    raise ValueError(f"{label} first difference row {i}\nexpected {reference}\nobserved {observed}\nfinal info {last}")
                nodes.append(int(node))
        send(engine, "quit", transcript)
        if engine.wait(timeout=10):
            raise RuntimeError(f"engine exit {engine.returncode}")
    finally:
        if engine.poll() is None:
            engine.kill()
        engine.wait()
        engine.stdin.close()
        engine.stdout.close()
        if transcript:
            transcript.close()
    if is_ladder:
        first = next(row for row in expected if row["mate_found"] == "1")
        log(f"P: all {len(expected)} ladder rows equal, including scores, moves, nodes, PV, seldepth and hashfull; "
            f"elapsed time and NPS omitted from equality. First g3g6 mate at depth {first['requested_depth']}, "
            f"{first['nodes']} nodes; depth 20 {nodes[-1]} nodes.")
    else:
        log(f"{label}: all {len(expected)} rows equal on index, FEN, nodes and bestmove at depth 12. "
            f"Nodes {sum(nodes)}. First three {' '.join(map(str, nodes[:3]))}.")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("exe", type=Path)
    p.add_argument("reference", type=Path)
    p.add_argument("out", type=Path)
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out / "checks.txt").open("x") as f:
        def log(message):
            print(message, file=f, flush=True)
            print(message, flush=True)
        try:
            for label in ("O", "G", "P"):
                validate(label, args.exe.resolve(strict=True), args.reference.resolve(), args.out, log)
        except (ValueError, OSError, RuntimeError, TimeoutError) as error:
            log("STOP Part B row gate: " + str(error))
            raise SystemExit(1)


def stop(signum, frame):
    raise TimeoutError(f"interrupted by signal {signum}")


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, stop)
    main()
