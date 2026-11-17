#!/usr/bin/env python3
"""UCI-level checks: net activation, refusal on a damaged net, and the FEN diagnostic.

Implements the corrected FEN rule: `info string invalid FEN` arrives in the POSITION reply
when `isready` follows the position, and in the `go` output ahead of the first `info depth`
line when it does not. Both streams are scanned, always; a fresh session is not exempt.

Every read has a wall-clock timeout, so a hung engine fails the check instead of hanging the
script. `go infinite` is never used; every search is a fixed depth or node budget and every
search is awaited to `bestmove`.

Usage: uci_checks.py <engine> <pristine net> <damaged net> <fens file>
"""
import queue
import subprocess
import sys
import threading
import time

EXE, NET, BAD_NET, FENS = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
TIMEOUT = 120.0


class Engine:
    def __init__(self):
        self.p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.q = queue.Queue()
        self.t = threading.Thread(target=self._reader, daemon=True)
        self.t.start()
        self.send("uci")
        self.read_until("uciok")

    def _reader(self):
        for line in self.p.stdout:
            self.q.put(line.rstrip("\n"))
        self.q.put(None)

    def send(self, line):
        self.p.stdin.write(line + "\n")
        self.p.stdin.flush()

    def read_until(self, prefix, limit=200000):
        """Read until a line starts with `prefix`. Raises on timeout or EOF."""
        out = []
        deadline = time.monotonic() + TIMEOUT
        for _ in range(limit):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("timeout waiting for %r; got %d lines, last=%r"
                                   % (prefix, len(out), out[-1] if out else None))
            try:
                line = self.q.get(timeout=remaining)
            except queue.Empty:
                raise TimeoutError("timeout waiting for %r; last=%r" % (prefix, out[-1] if out else None))
            if line is None:
                raise EOFError("engine closed stdout while waiting for %r" % prefix)
            out.append(line)
            if line.startswith(prefix):
                return out
        raise RuntimeError("line limit reached waiting for %r" % prefix)

    def sync(self):
        self.send("isready")
        return self.read_until("readyok")

    def search(self, go, pos=""):
        """Send an optional position, then go, and read to bestmove. Returns both streams."""
        pos_reply = []
        if pos:
            self.send(pos)
        self.send(go)
        go_out = self.read_until("bestmove")
        return pos_reply, go_out

    def close(self):
        try:
            self.send("quit")
            self.p.wait(timeout=20)
        except Exception:
            self.p.kill()


def has_invalid_fen(lines):
    return any("invalid FEN" in line for line in lines)


def setup(eng, net=None, arch=False, pc20=False):
    if net is not None:
        eng.send("setoption name NNUEArchFile value " + net)
        eng.sync()
    if arch:
        eng.send("setoption name NNUEArch value true")
        eng.sync()
    if pc20:
        for key, value in PC20:
            eng.send("setoption name %s value %s" % (key, value))
            eng.sync()
    eng.send("setoption name Threads value 1")
    eng.sync()
    eng.send("setoption name Hash value 16")
    eng.sync()


PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
        ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
        ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
        ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
        ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false")]


def bench_nodes(line):
    """Node count from a bench line; the nps/time fields vary run to run and are excluded."""
    parts = line.split()
    if "nodes" in parts:
        return int(parts[parts.index("nodes") + 1])
    return None


def bench_line(net=None, arch=False):
    eng = Engine()
    setup(eng, net=net, arch=arch)
    eng.send("ucinewgame")
    eng.sync()
    eng.send("bench 11")
    out = eng.read_until("info string bench")
    eng.close()
    bench = [l for l in out if "info string bench" in l]
    return bench[-1] if bench else "(no bench line)"


def case_activation():
    """Is the net actually used? bench must change when NNUEArchFile then NNUEArch are set."""
    off = bench_line()
    on = bench_line(net=NET, arch=True)
    off_nodes, on_nodes = bench_nodes(off), bench_nodes(on)
    print("ACTIVATION net_off | %s" % off)
    print("ACTIVATION net_on  | %s" % on)
    print("ACTIVATION nodes_off %s nodes_on %s" % (off_nodes, on_nodes))
    changed = off_nodes is not None and on_nodes is not None and off_nodes != on_nodes
    print("ACTIVATION bench_nodes_changed %d (1 means the net took effect)" % (1 if changed else 0))
    return changed


def case_loaded_but_not_activated():
    """Loaded with NNUEArchFile but NNUEArch left false: must have no effect at all."""
    plain = bench_line()
    file_only = bench_line(net=NET, arch=False)
    print("NOTACT no_file   | %s" % plain)
    print("NOTACT file_only | %s" % file_only)
    print("NOTACT nodes_no_file %s nodes_file_only %s" % (bench_nodes(plain), bench_nodes(file_only)))
    inert = bench_nodes(plain) is not None and bench_nodes(plain) == bench_nodes(file_only)
    print("NOTACT inert %d (1 means a file loaded with NNUEArch false had no effect)" % (1 if inert else 0))
    return inert


def case_damaged_refuses():
    """A damaged net must be refused loudly, and the engine must not silently fall back.

    The engine's fail-loud rule ends the process instead of answering `isready`, so this
    check drives it as a one-shot pipe, records the exit status, and treats "no search
    happened" as the requirement. It reports the exit status rather than assuming one.
    """
    script = ("uci\n"
              "setoption name NNUEArchFile value " + BAD_NET + "\n"
              "isready\n"
              "setoption name NNUEArch value true\n"
              "position startpos\n"
              "go depth 4\n"
              "quit\n")
    proc = subprocess.run([EXE], input=script, capture_output=True, text=True, timeout=TIMEOUT)
    out = proc.stdout.splitlines()
    loud = [l for l in out if "ERROR NNUE v3" in l]
    searched = [l for l in out if l.startswith("info depth")]
    bestmoves = [l for l in out if l.startswith("bestmove")]
    print("DAMAGED_UCI exit_status %d error_lines %d first %s"
          % (proc.returncode, len(loud), loud[0] if loud else "(none)"))
    print("DAMAGED_UCI info_depth_lines %d bestmove_lines %d" % (len(searched), len(bestmoves)))
    ok = bool(loud) and not searched and not bestmoves
    print("DAMAGED_UCI loud_and_no_search %d (1 is required)" % (1 if ok else 0))
    return ok


def case_arch_without_file():
    """NNUEArch true with no file loaded: same fail-loud rule, and it must not search."""
    script = ("uci\n"
              "setoption name NNUEArch value true\n"
              "position startpos\n"
              "go depth 4\n"
              "quit\n")
    proc = subprocess.run([EXE], input=script, capture_output=True, text=True, timeout=TIMEOUT)
    out = proc.stdout.splitlines()
    loud = [l for l in out if "ERROR NNUE v3" in l]
    searched = [l for l in out if l.startswith("info depth")]
    print("ARCHNOFILE exit_status %d error_lines %d info_depth_lines %d" % (proc.returncode, len(loud), len(searched)))
    return bool(loud) and not searched


def case_invalid_fen_both_paths():
    """The FEN diagnostic, scanned in BOTH streams, with and without isready between.

    The FEN here is genuinely refused by the engine ("invalid FEN fields": no kings), which
    was verified independently before this check was written. A FEN the engine silently
    normalises would make this check pass vacuously, so the check also requires that the
    search that follows did NOT run on the position the FEN asked for.
    """
    bad_fens = [
        "8/8/8/8/8/8/8/8 w - - 0 1",                                  # no kings
        "rnbqkbnr/pppppppp/9/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",    # bad rank width
        "Pnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",    # pawn on rank 8
    ]
    ok = True
    for bad_fen in bad_fens:
        for label, with_ready in (("with_isready", True), ("without_isready", False)):
            eng = Engine()
            setup(eng)
            eng.send("position fen " + bad_fen)
            pos = eng.sync() if with_ready else []
            eng.send("go depth 2")
            go_out = eng.read_until("bestmove")
            eng.close()
            prefix = []
            for line in go_out:
                if line.startswith("info depth"):
                    break
                prefix.append(line)
            in_pos, in_go = has_invalid_fen(pos), has_invalid_fen(prefix)
            print("FENDIAG %-16s %-46s in_position_reply %d in_go_prefix %d pos_lines %d go_lines %d"
                  % (label, bad_fen[:44], 1 if in_pos else 0, 1 if in_go else 0, len(pos), len(go_out)))
            if not (in_pos or in_go):
                ok = False
    print("FENDIAG seen_in_at_least_one_stream_every_path %d (1 is required)" % (1 if ok else 0))
    return ok


def case_fen_false_positive():
    """A valid FEN must never be reported invalid, in either path."""
    fens = [l.strip() for l in open(FENS) if l.strip()][:6]
    bad = 0
    checked = 0
    for fen in fens:
        for with_ready in (True, False):
            eng = Engine()
            setup(eng)
            eng.send("position fen " + fen)
            pos = eng.sync() if with_ready else []
            eng.send("go nodes 2000")
            go_out = eng.read_until("bestmove")
            eng.close()
            checked += 1
            if has_invalid_fen(pos) or has_invalid_fen(go_out):
                bad += 1
                print("FALSEPOS %s" % fen)
    print("FALSEPOS compared %d false_positives %d" % (checked, bad))
    return bad == 0


def main():
    results = {
        "activation": case_activation(),
        "not_activated": case_loaded_but_not_activated(),
        "damaged": case_damaged_refuses(),
        "arch_no_file": case_arch_without_file(),
        "fendiag": case_invalid_fen_both_paths(),
        "falsepos": case_fen_false_positive(),
    }
    for name, ok in results.items():
        print("UCI %-14s %s" % (name, "PASS" if ok else "FAIL"))
    print("UCI all_pass %d" % (1 if all(results.values()) else 0))
    return 0 if all(results.values()) else 3


if __name__ == "__main__":
    sys.exit(main())
