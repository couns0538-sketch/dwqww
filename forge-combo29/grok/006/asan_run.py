#!/usr/bin/env python3
"""Same runner for the sanitizer build and the deliberate-bug build."""
import hashlib
import os
import subprocess
import sys

STOP_BITS = ("unknown option", "invalid value", "invalid FEN", "illegal move")
SAN_BITS = ("AddressSanitizer", "UndefinedBehaviorSanitizer", "runtime error:")
S14 = [
    ("LmrQuietBase", "93"),
    ("LmrQuietDivisor", "205"),
    ("LmrNoisyBase", "13"),
    ("LmrNoisyDivisor", "333"),
    ("LmrHistoryDivisor", "5643"),
    ("NullMoveBase", "5"),
    ("LmpBase", "8"),
    ("HistoryPruneMultiplier", "2220"),
    ("HistoryBonusQuadratic", "24"),
    ("HistoryBonusLinear", "54"),
    ("HistoryBonusMax", "2212"),
    ("SingularDepth", "6"),
    ("IirDepth", "2"),
    ("NonPawnCorrection", "true"),
    ("IdeaS34", "true"),
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fen_of(line):
    parts = line.split()
    if len(parts) >= 6:
        return " ".join(parts[:6])
    return line.strip()


def main():
    exe, fen_path, depth_s, out_prefix = sys.argv[1:5]
    depth = int(depth_s)
    fens = []
    with open(fen_path, encoding="utf-8") as handle:
        for raw in handle:
            fen = fen_of(raw.strip())
            if fen:
                fens.append(fen)
    env = os.environ.copy()
    env["ASAN_OPTIONS"] = "halt_on_error=1:abort_on_error=1:detect_leaks=0"
    env["UBSAN_OPTIONS"] = "halt_on_error=1:abort_on_error=1:print_stacktrace=1"
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
    )
    transcript = []
    san_lines = []
    stopped = ""

    def send(line):
        transcript.append(">> " + line)
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def take():
        line = proc.stdout.readline()
        if line == "":
            return None
        line = line.rstrip("\r\n")
        transcript.append(line)
        if any(bit in line for bit in SAN_BITS):
            san_lines.append(line)
        return line

    def until(marker):
        nonlocal stopped
        while True:
            line = take()
            if line is None:
                return None
            for bit in STOP_BITS:
                if bit in line:
                    stopped = line
                    return line
            if marker in line:
                return line

    options = []
    alive = True
    try:
        send("uci")
        if until("uciok") is None:
            alive = False
        if alive and not stopped:
            for name, value in [("Threads", "1"), ("Hash", "16"), *S14]:
                line = f"setoption name {name} value {value}"
                options.append(line)
                send(line)
                send("isready")
                if until("readyok") is None:
                    alive = False
                    break
                if stopped:
                    break
        done = 0
        if alive and not stopped:
            for fen in fens:
                send("ucinewgame")
                send("isready")
                if until("readyok") is None:
                    alive = False
                    break
                send("position fen " + fen)
                send("isready")
                if until("readyok") is None:
                    alive = False
                    break
                if stopped:
                    break
                send(f"go depth {depth}")
                got = False
                while True:
                    line = take()
                    if line is None:
                        alive = False
                        break
                    if line.startswith("bestmove "):
                        got = True
                        break
                    for bit in STOP_BITS:
                        if bit in line:
                            stopped = line
                            break
                    if stopped:
                        break
                if not alive or stopped or not got:
                    break
                done += 1
                if done % 25 == 0:
                    print(f"progress {done}", flush=True)
        if alive:
            try:
                send("quit")
            except BrokenPipeError:
                alive = False
    except BrokenPipeError:
        alive = False
    # Drain whatever the sanitizer still prints.
    while True:
        line = proc.stdout.readline()
        if line == "":
            break
        line = line.rstrip("\r\n")
        transcript.append(line)
        if any(bit in line for bit in SAN_BITS):
            san_lines.append(line)
    proc.wait(timeout=30)
    nm = subprocess.run(["nm", "-C", exe], check=False, capture_output=True, text=True)
    asan_syms = sum(1 for line in nm.stdout.splitlines() if "__asan_" in line)
    with open(out_prefix + ".transcript", "w", encoding="utf-8") as handle:
        handle.write("\n".join(transcript))
        handle.write("\n")
    with open(out_prefix + ".san", "w", encoding="utf-8") as handle:
        handle.write(f"sanitizer_lines={len(san_lines)}\n")
        handle.write(f"positions_finished={done}\n")
        handle.write(f"returncode={proc.returncode}\n")
        handle.write(f"stopped={stopped}\n")
        for line in san_lines:
            handle.write(line + "\n")
    id_name = ""
    for line in transcript:
        if line.startswith("id name "):
            id_name = line[len("id name ") :]
            break
    with open(out_prefix + ".meta", "w", encoding="utf-8") as handle:
        handle.write(f"exe={exe}\n")
        handle.write(f"sha256={sha256(exe)}\n")
        handle.write(f"id_name={id_name}\n")
        handle.write(f"nm_asan_symbols={asan_syms}\n")
        handle.write("nm_command=nm -C <exe> | grep -c __asan_\n")
        handle.write(f"ASAN_OPTIONS={env['ASAN_OPTIONS']}\n")
        handle.write(f"UBSAN_OPTIONS={env['UBSAN_OPTIONS']}\n")
        handle.write("options_sent:\n")
        for line in options:
            handle.write(line + "\n")
    print(f"sanitizer_lines={len(san_lines)} asan_symbols={asan_syms} finished={done} rc={proc.returncode}")


if __name__ == "__main__":
    main()
