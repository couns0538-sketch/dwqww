"""UCI driver: one fresh process per search, reads to `bestmove` before sending anything else.

Trap 1 in the brief: piping `quit` into a live search makes the engine abort and
fabricate a bestmove with no `info` lines. So this never writes `quit` while a
search can be running; it reads the bestmove line first, then closes stdin.

Trap 3: every reply is scanned for `unknown option` / `invalid value`, so a cell
whose option never reached the engine is visible instead of looking identical.
"""
import re
import subprocess
import time

BIN = "/tmp/build-optpairs/forge"


class _Dead(Exception):
    """The engine closed or died while a command was being sent."""

SCORE_RE = re.compile(r"score (cp|mate) (-?\d+)")
DEPTH_RE = re.compile(r"info depth (\d+)")
NODES_RE = re.compile(r" nodes (\d+)")
PV_RE = re.compile(r" pv( .*)?$")


def _parse_info(line):
    out = {}
    m = SCORE_RE.search(line)
    if m:
        out["score_kind"] = m.group(1)
        out["score"] = int(m.group(2))
    m = DEPTH_RE.search(line)
    if m:
        out["depth"] = int(m.group(1))
    m = NODES_RE.search(line)
    if m:
        out["nodes"] = int(m.group(1))
    m = re.search(r" multipv (\d+)", line)
    if m:
        out["multipv"] = int(m.group(1))
    m = PV_RE.search(line.rstrip())
    if m:
        out["pv"] = (m.group(1) or "").split()
    return out


def run(options=(), position="position startpos", go="go depth 12", movelist=None,
        timeout=300, bin_path=None):
    """Run one search in a fresh process.

    options: sequence of (name, value) sent as `setoption name N value V` ("name"
    only when value is None: a button).
    position: full `position ...` string, or a bare FEN (a `fen` line is used).
    Returns dict with per-depth info lines, the final line, bestmove, and every
    `info string` diagnostic the engine emitted (book moves, errors).
    """
    exe = bin_path or BIN
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1)
    diag = []
    infos = []
    bestmove = None

    def send(text):
        if proc.poll() is not None:
            raise _Dead(text)
        try:
            proc.stdin.write(text + "\n")
            proc.stdin.flush()
        except (BrokenPipeError, ValueError):
            raise _Dead(text)

    send("uci")
    for line in proc.stdout:
        if line.startswith("id ") or line.startswith("option name"):
            continue
        if line.strip() == "uciok":
            break
    for name, value in options:
        send(f"setoption name {name}" if value is None else f"setoption name {name} value {value}")
        # setoption replies synchronously with `info string` when it wants to; read
        # whatever is pending by asking for isready.
        send("isready")
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            s = line.rstrip("\n")
            if s.startswith("info string"):
                diag.append(s)
            if s.strip() == "readyok":
                break
        if proc.poll() is not None:
            break
    if position.startswith("position"):
        _try_send(send, position)
    else:
        _try_send(send, "position fen " + position)
    if not _try_send(send, "isready"):
        return _finish(proc, diag, infos, None, options)
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info string"):
            diag.append(s)
        if s.strip() == "readyok":
            break
    if not _try_send(send, go):
        return _finish(proc, diag, infos, None, options)
    # Time the SEARCH only. Process startup, the uci handshake and isready cost
    # ~18-20 ms on this box, which is the same order as the clock floors being
    # measured -- a wall time taken around the whole subprocess run reports
    # 1.3x-4.3x overshoot on plans the engine actually honours.
    search_start = time.monotonic()
    try:
        for line in proc.stdout:
            s = line.rstrip("\n")
            if s.startswith("bestmove"):
                bestmove = s.split()[1] if len(s.split()) > 1 else None
                break
            if s.startswith("info string"):
                diag.append(s)
            elif s.startswith("info depth"):
                infos.append(_parse_info(s))
    finally:
        search_ms = int((time.monotonic() - search_start) * 1000)
        try:
            send("quit")
        except Exception:
            pass
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()

    return _finish(proc, diag, infos, bestmove, options, search_ms)


def _try_send(send, text):
    try:
        send(text)
        return True
    except _Dead:
        return False


def _finish(proc, diag, infos, bestmove, options, search_ms=None):
    last = infos[-1] if infos else {}
    bad = [d for d in diag if "unknown option" in d or "invalid value" in d]
    return {
        "bestmove": bestmove,
        "depth": last.get("depth"),
        "score_kind": last.get("score_kind"),
        "score": last.get("score"),
        "nodes": last.get("nodes"),
        "pv": last.get("pv", []),
        "infos": len(infos),
        "diag": diag,
        "accepted": not bad,
        "rejected": bad,
        "book": [d for d in diag if "book move" in d],
        "exit_code": proc.returncode,
        "search_ms": search_ms,
    }


def sig(cell):
    """The comparison tuple the audit's criterion is defined on."""
    return (cell["bestmove"], cell["score_kind"], cell["score"], cell["depth"], cell["nodes"])


def moved(a, b):
    """Which fields differ between two cells (empty list == identical)."""
    fields = []
    if a["bestmove"] != b["bestmove"]:
        fields.append("bestmove")
    if (a["score_kind"], a["score"]) != (b["score_kind"], b["score"]):
        fields.append("score")
    if a["depth"] != b["depth"]:
        fields.append("depth")
    if a["nodes"] != b["nodes"]:
        fields.append("nodes")
    return fields
