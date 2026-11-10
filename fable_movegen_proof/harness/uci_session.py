"""uci_session.py - pinned UCI driver of job 3 for the release executables (standard library only).

Two ways to run an engine, both on cores 3-6 at Idle priority (the child inherits both from this process and
is read back before it gets work):
  Engine      a persistent interactive session with timeouts (pins, divide, warm transcript, soak)
  run_batch   stdin from a file, stdout to a file: no pipe and no driver work between positions (fuzz, edge)

compare_perft() compares two `go perft` batch outputs position by position: the lines of one perft block are
the legal moves in generation order (with the number of legal replies at depth 2), so a block compares
membership, order and counts. The blocks are compared from the start, and a difference found before a damaged
part of the candidate output is reported as a difference.

check_tie() ties a release executable's output to the auxiliary probe: block i must be the probe's legal-move
list at position i, in the same order. It shows that every position was really reached by the executable.

A timeout is reported as TIMEOUT with the CPU time the child had used (a starved Idle process is not a hung
one); the harness then ends its own child. It is never a candidate verdict.
"""
import collections
import queue
import re
import subprocess
import threading
import time

import pinguard3

Result = collections.namedtuple("Result", "status positions detail")
Run = collections.namedtuple("Run", "status detail alive_after exit_code wall cpu pid")
Block = collections.namedtuple("Block", "moves total line")
MOVE_RX = re.compile(r"^([a-h][1-8][a-h][1-8][nbrq]?): (\d+)$")
NODES_RX = re.compile(r"^nodes (\d+)$")
SYNC_EVERY = 500
PREAMBLE = ["uci", "setoption name Threads value 1", "setoption name Hash value 16",
            "setoption name OwnBook value false", "isready"]


class EngineError(Exception):
    pass


class EngineTimeout(EngineError):
    pass


def _cpu_progress(handle, seconds=2.0):
    a = pinguard3.cpu_seconds(handle)
    time.sleep(seconds)
    b = pinguard3.cpu_seconds(handle)
    if a < 0 or b < 0:
        return "cpu time unreadable"
    how = "still computing: starved or slow, not hung" if b - a > 0.01 else "no cpu progress in that time: hung, waiting, or starved at Idle priority"
    return f"cpu time advanced {b - a:.2f} s in {seconds:.0f} s ({how}); total cpu time used {b:.1f} s"


# ---------------------------------------------------------------- batch runs
def write_batch(path, lines, preamble=None):
    """Write a batch input file from alternating 'position ...' / 'go perft D' lines. Returns the number of
    positions (go lines). An isready after every SYNC_EVERY positions lets the parser localise missing output."""
    n = 0
    with open(path, "w", encoding="ascii", newline="\n") as f:
        f.write("\n".join(PREAMBLE if preamble is None else preamble) + "\n")
        for ln in lines:
            f.write(ln + "\n")
            if ln.startswith("go "):
                n += 1
                if n % SYNC_EVERY == 0:
                    f.write("isready\n")
        f.write("isready\nquit\n")
    return n


def run_batch(argv, in_path, out_path, timeout):
    """Run argv with stdin from in_path and stdout to out_path (stderr to out_path + '.err')."""
    pinguard3.ensure()
    start = time.time()
    with open(in_path, "rb") as fin, open(out_path, "wb") as fout, open(out_path + ".err", "wb") as ferr:
        proc = subprocess.Popen(argv, stdin=fin, stdout=fout, stderr=ferr)
        try:
            pinguard3.check_child(proc._handle)
        except SystemExit:
            proc.kill()
            proc.wait()
            raise
        status, detail = "OK", ""
        try:
            code = proc.wait(timeout=timeout)
            if code != 0:
                status, detail = "EXIT", f"exit code {code}"
        except subprocess.TimeoutExpired:
            progress = _cpu_progress(proc._handle)
            proc.kill()                      # this job's own child
            code = proc.wait()
            status, detail = "TIMEOUT", f"timeout after {timeout} s; {progress}; the harness ended its own child"
        cpu = pinguard3.cpu_seconds(proc._handle)
        pid = proc.pid
    alive = pinguard3.pid_alive(pid)         # asked of the operating system by process id
    return Run(status, detail, alive, code, time.time() - start, cpu, pid)


Parsed = collections.namedtuple("Parsed", "blocks anomalies segments")


def parse_perft_output(text):
    """Perft blocks of a batch output, anomalies (text, block index) and the block count at each readyok."""
    lines = text.splitlines()
    blocks, anomalies, segments = [], [], []
    i = 0
    seen_uciok = False
    while i < len(lines):                      # the handshake: everything up to the first readyok
        ln = lines[i].strip()
        i += 1
        if ln == "uciok":
            seen_uciok = True
        if ln == "readyok":
            break
    else:
        anomalies.append(("missing output: no readyok after the handshake", 0))
        return Parsed(blocks, anomalies, segments)
    if not seen_uciok:
        anomalies.append(("malformed handshake: readyok without uciok", 0))
    current = []
    for k in range(i, len(lines)):
        ln = lines[k].strip()
        if not ln:
            continue
        m = MOVE_RX.match(ln)
        if m:
            current.append((m.group(1), int(m.group(2))))
            continue
        m = NODES_RX.match(ln)
        if m:
            total = int(m.group(1))
            if sum(c for _, c in current) != total:
                anomalies.append((f"malformed block at output line {k + 1}: the move counts do not add up to nodes {total}", len(blocks)))
            blocks.append(Block(current, total, k + 1))
            current = []
            continue
        if ln == "readyok":
            if current:
                anomalies.append((f"missing output: readyok inside a perft block at output line {k + 1}", len(blocks)))
                current = []
            segments.append(len(blocks))
            continue
        if ln.startswith("info string"):
            anomalies.append((f"engine reported at output line {k + 1}: {ln}", len(blocks)))
            continue
        if k == len(lines) - 1 and not text.endswith("\n"):
            anomalies.append((f"missing output: the output ends in the middle of line {k + 1} ({ln[:30]!r})", len(blocks)))
            continue
        anomalies.append((f"malformed line at output line {k + 1}: {ln[:60]!r}", len(blocks)))
    if current:
        anomalies.append(("missing output: the output ends inside a perft block", len(blocks)))
    return Parsed(blocks, anomalies, segments)


def _unusable(parsed, n_positions):
    """Why a parsed batch output cannot be compared as a whole, or ''."""
    if parsed.anomalies:
        text, idx = parsed.anomalies[0]
        return f"{text} (at position {idx + 1}; {len(parsed.anomalies)} anomalies)"
    if len(parsed.blocks) != n_positions:
        where = ""
        for s, have in enumerate(parsed.segments):
            want = min((s + 1) * SYNC_EVERY, n_positions)
            if have != want:
                where = f"; first shortfall before position {want} (sync point {s + 1} saw {have} blocks)"
                break
        return f"missing output: {len(parsed.blocks)} perft blocks, expected {n_positions}{where}"
    return ""


def _block_difference(i, rb, cb):
    rm, cm = [m for m, _ in rb.moves], [m for m, _ in cb.moves]
    if set(rm) != set(cm) or len(rm) != len(cm):
        missing = [m for m in rm if m not in set(cm)]
        extra = [m for m in cm if m not in set(rm)]
        return (f"legal move set differs at position {i + 1}: missing {missing or '[]'}, extra {extra or '[]'}; "
                f"expected {' '.join(rm)}; got {' '.join(cm)}")
    if rm != cm:
        k = next(j for j in range(len(rm)) if rm[j] != cm[j])
        return (f"legal move order differs at position {i + 1}: index {k} expected {rm[k]}, got {cm[k]}; "
                f"expected {' '.join(rm)}; got {' '.join(cm)}")
    k = next(j for j in range(len(rm)) if rb.moves[j][1] != cb.moves[j][1])
    return (f"reply count differs at position {i + 1} for move {rm[k]}: expected {rb.moves[k][1]}, "
            f"got {cb.moves[k][1]} (nodes {rb.total} / {cb.total})")


def compare_perft(ref_text, cand_text, n_positions):
    pr = parse_perft_output(ref_text)
    bad = _unusable(pr, n_positions)
    if bad:
        return Result("HARNESS_ERROR", 0, f"the reference output is not usable: {bad}")
    pc = parse_perft_output(cand_text)
    bad = _unusable(pc, n_positions)
    # The blocks before the first damaged place are compared first: a difference there is a difference.
    # "Before the damage" means: before the first anomaly, and not beyond the last sync point (readyok) at which
    # the candidate had printed exactly the right number of blocks. Past a wrong count the blocks no longer
    # line up with the positions, and comparing them would turn missing output into a false move-list difference.
    aligned = 0
    for s, have in enumerate(pc.segments):
        want = min((s + 1) * SYNC_EVERY, n_positions)
        if have != want:
            break
        aligned = want
    sound = min(aligned, len(pc.blocks), n_positions, pc.anomalies[0][1] if pc.anomalies else n_positions)
    for i in range(sound):
        rb, cb = pr.blocks[i], pc.blocks[i]
        if rb.moves != cb.moves:
            later = f" | the candidate output is also damaged later: {bad}" if bad else ""
            return Result("MISMATCH", i, _block_difference(i, rb, cb) + f" (output line {cb.line})" + later)
    if bad:
        return Result("MALFORMED", sound, f"the candidate output is not usable: {bad}; the {sound} positions before it are identical")
    return Result("EQUAL", n_positions, f"{n_positions} perft blocks identical in members, order and counts")


def compare_perft_bound(ref_text, ref_input_sha, cand_text, cand_input_sha, n_positions):
    if ref_input_sha != cand_input_sha:
        return Result("HARNESS_ERROR", 0, f"inputs differ: reference input sha256 {ref_input_sha}, candidate input sha256 "
                      f"{cand_input_sha}; the outputs are not comparable")
    return compare_perft(ref_text, cand_text, n_positions)


def check_tie(text, expect_lines, n_positions):
    """Block i of a release executable's perft output must be the probe's legal-move list at position i, in order
    (expect_lines: one line per position, moves separated by spaces, as `mgprobe uciscript --expect` writes them)."""
    parsed = parse_perft_output(text)
    bad = _unusable(parsed, n_positions)
    if bad:
        return Result("HARNESS_ERROR", 0, f"the output is not usable for the tie: {bad}")
    if len(expect_lines) < n_positions:
        return Result("HARNESS_ERROR", 0, f"the probe gave {len(expect_lines)} move lists for {n_positions} positions")
    for i in range(n_positions):
        want = expect_lines[i].split()
        got = [m for m, _ in parsed.blocks[i].moves]
        if want != got:
            return Result("MISMATCH", i, f"the executable's move list at position {i + 1} is not the probe's: probe {' '.join(want) or '(none)'}; "
                          f"executable {' '.join(got) or '(none)'} (output line {parsed.blocks[i].line}): the position was not reached, or the "
                          f"two builds list the moves differently")
    return Result("EQUAL", n_positions, f"{n_positions} perft blocks are the probe's legal lists, in order")


# ---------------------------------------------------------------- interactive session
class Engine:
    """One engine process with a reader thread. Every wait has a timeout. After a timeout or a closed output the
    session refuses further use, so a late answer can never be taken for the answer to a later command."""

    def __init__(self, argv, log_path=None):
        pinguard3.ensure()
        self.argv = argv
        self.dead = ""
        self.proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0)
        try:
            self.pin = pinguard3.check_child(self.proc._handle)
        except SystemExit:
            self.proc.kill()
            self.proc.wait()
            raise
        self.log = open(log_path, "w", encoding="ascii", errors="replace", newline="\n") if log_path else None
        self.log_lock = threading.Lock()
        self.lines = queue.Queue()
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _log(self, text):
        with self.log_lock:
            if self.log and not self.log.closed:
                self.log.write(text + "\n")

    def _read(self):
        for raw in self.proc.stdout:
            line = raw.decode("ascii", "replace").rstrip("\r\n")
            self._log(line)
            self.lines.put(line)
        self.lines.put(None)

    def _usable(self):
        if self.dead:
            raise EngineError(f"the session is not usable after {self.dead}")

    def send(self, line):
        self._usable()
        self._log("> " + line)
        try:
            self.proc.stdin.write((line + "\n").encode("ascii"))
            self.proc.stdin.flush()
        except OSError as e:
            self.dead = f"a failed write ({e})"
            raise EngineError(f"the engine does not take input any more ({e}); exit code {self.proc.poll()}") from None

    def read_until(self, pred, timeout, what):
        """Lines up to and including the first one for which pred is true."""
        self._usable()
        got = []
        deadline = time.time() + timeout
        while True:
            left = deadline - time.time()
            try:
                if left <= 0:
                    raise queue.Empty
                line = self.lines.get(timeout=left)
            except queue.Empty:
                self.dead = f"a timeout ({what})"
                raise EngineTimeout(f"timeout after {timeout} s waiting for {what}; {_cpu_progress(self.proc._handle)}") from None
            if line is None:
                self.dead = "the engine closed its output"
                raise EngineError(f"the engine closed its output while the harness waited for {what} (exit code {self.proc.poll()})")
            got.append(line)
            if pred(line):
                return got

    def handshake(self, options, timeout=120):
        self.send("uci")
        head = self.read_until(lambda s: s == "uciok", timeout, "uciok")
        for kv in options:
            name, _, value = kv.partition("=")
            self.send(f"setoption name {name}" + (f" value {value}" if value != "" else ""))
        self.isready(timeout)
        return head

    def isready(self, timeout=120):
        self.send("isready")
        return self.read_until(lambda s: s == "readyok", timeout, "readyok")

    def position(self, fen=None, moves=None):
        cmd = "position startpos" if fen is None else "position fen " + fen
        if moves:
            cmd += " moves " + " ".join(moves)
        self.send(cmd)

    def perft(self, depth, timeout=1800):
        """([(move, count)], total, other lines) of go perft. An `info string` line (a refused FEN or move) or
        counts that do not add up are errors: the block would not be the perft of the position that was sent."""
        self.send(f"go perft {depth}")
        lines = self.read_until(lambda s: s.startswith("nodes "), timeout, f"the end of go perft {depth}")
        moves, other = [], []
        for ln in lines[:-1]:
            m = MOVE_RX.match(ln)
            if m:
                moves.append((m.group(1), int(m.group(2))))
            else:
                other.append(ln)
        total = int(lines[-1].split()[1])
        refused = [ln for ln in other if ln.startswith("info string")]
        if refused:
            raise EngineError(f"the engine reported before the perft block: {refused[0]}")
        if sum(c for _, c in moves) != total:
            raise EngineError(f"malformed perft block: the move counts do not add up to nodes {total}")
        return moves, total, other

    def go(self, args, timeout=1800):
        """(info lines, bestmove line) of a search."""
        self.send("go " + args)
        lines = self.read_until(lambda s: s.startswith("bestmove"), timeout, "bestmove")
        return lines[:-1], lines[-1]

    def bench(self, depth, timeout=1800):
        self.send(f"bench {depth}")
        mark = f"bench depth {depth} nodes "
        line = self.read_until(lambda s: mark in s, timeout, f"bench {depth}")[-1]
        return int(line.split(mark)[1].split()[0])

    def cpu(self):
        return pinguard3.cpu_seconds(self.proc._handle)

    def _close_log(self):
        with self.log_lock:
            if self.log and not self.log.closed:
                self.log.close()

    def close(self, timeout=30):
        """quit, wait for the exit, return the exit code. A survivor is ended by the harness and reported."""
        try:
            if not self.dead:
                self.send("quit")
            self.proc.stdin.close()
        except (OSError, EngineError):
            pass
        try:
            code = self.proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait()
            self._close_log()
            raise EngineError(f"the engine did not exit {timeout} s after quit; the harness ended its own child") from None
        self.reader.join(timeout=5)
        self._close_log()
        return code

    def kill(self):
        try:
            self.proc.kill()
        except OSError:
            pass
        self.proc.wait()
        self.reader.join(timeout=5)
        self._close_log()
