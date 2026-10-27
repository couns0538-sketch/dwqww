#!/usr/bin/env python3
"""S40 cross-folder datagen dedupe + merge tool (Opus 5.5 for Sol's S40, 2026-10-27).

Dedupes a SECOND self-play output folder (ordered text `FEN | STM score | WHITE result`, as written by the PC's
forge_selfplay.py) against the MAIN training shards and the 013/014 HOLDOUT, by position and by game, and writes NEW
sealed shards in the trainer's exact record format (FPOS v1 `.pos` as tools/fen2bin.cpp writes it, FHCE v1 `.hce` as
tools/hce_dump.cpp writes it, plus the kept text lines) with an md5 manifest. Existing files are never changed: every
input is opened read-only, outputs are created exclusively ('x' mode), nothing is deleted, and the NEW output directory
may not lie inside (or contain) any input directory or a protected PC data directory.

Identity of a position = board32 + side to move (what the v3b trainer sees; FPOS stores no castling, e.p. or clocks).
Matching is exact: a 64-bit key finds candidates, every candidate is confirmed on all 33 identity bytes.

Game groups in the second folder: authoritative row-aligned game IDs (`--game-id-sidecars`: `<text name>.gameid`, one
ID per text line) or, by default, Sol's conservative ordered-text rule (a new game starts when the fullmove number
decreases, the piece count increases or the WHITE result changes; no reset at file boundaries, so a game that
continues into the next file stays one group; more than 20 boundaries in a rolling 100-row window fails closed as
suspected interleaving). The game ID of an inferred group is its content fingerprint (sha256/128 over the group's
rows: board32, side to move, score, result). Reference game-ID lists (`--main-game-ids`, `--holdout-game-ids`) are
plain text, one ID per line; the `gameids` subcommand computes fingerprint lists from reference text files.

Every second-folder row gets exactly one reason, first match wins:
  holdout_position  its position occurs in a holdout shard
  holdout_game      its game contains a holdout_position row, or its game ID is in the holdout ID list
  main_game         its game ID is in the main ID list
  dup_main          its position occurs in a main shard
  dup_second        its position occurs in an EARLIER surviving row of the second folder (the first survivor is kept)
  kept              written to the output
Inclusive counts (rows in main / in holdout / earlier in second, whatever reason won), label conflicts (same
position, different score or result) and rejected 64-bit key collisions are reported too.

Subcommands: merge (default), gameids, verify. Exit codes: 0 completed, 1 failed (bad input, mismatch, interleaving),
2 usage, 3 stopped by a guard (free RAM, wall budget). A failed or stopped merge leaves STOPPED.txt and no manifest;
only a directory whose manifest verifies (`verify`) is sealed. Needs numpy (on the PC: the read-only NNUE venv,
Python 3.10.22, numpy 1.26.4). Runs single-threaded at Idle priority.
"""
from __future__ import annotations

import argparse
import array
import ctypes
import gzip
import hashlib
import json
import os
import platform
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
import numpy as np

DATE = "20261027"
TOOL = "forge_sol_S40_merge_datagen_" + DATE
HEADER = 16
TRIPWIRE_WINDOW, TRIPWIRE_LIMIT = 100, 20
REASONS = ("holdout_position", "holdout_game", "main_game", "dup_main", "dup_second", "kept")
R_HOLD_POS, R_HOLD_GAME, R_MAIN_GAME, R_DUP_MAIN, R_DUP_SECOND, R_KEPT = range(6)
U64 = np.uint64
PIECE = [0] * 256
for _i, _c in enumerate("PNBRQKpnbrqk"):
    PIECE[ord(_c)] = _i + 1
SCORE_RE = re.compile(rb"[ \t\n\v\f\r]*([+-]?[0-9]+)")                                   # strtol(..., 10)
RESULT_RE = re.compile(rb"[ \t\n\v\f\r]*([+-]?(?:[0-9]+\.?[0-9]*|\.[0-9]+)(?:[eE][+-]?[0-9]+)?)")  # strtod, decimal forms
SELFPLAY_RE = re.compile(r"^forge_selfplay_(\d+)\.txt$")
PART_RE = re.compile(r"^forge_selfplay_(\d+)\.txt\.part$")
PREFIX_RE = re.compile(r"^[A-Za-z0-9_.-]{1,80}$")
GAMEID_RE = re.compile(r"^[!-~]{1,200}$")  # printable ASCII, no whitespace
DEFAULT_PROTECTED = [r"D:\grok-pc-data\forge_push", r"D:\grok-pc-data\selfplay_out", r"F:\forge_nnue_train",
                     r"C:\Users\Administrator\grok-pc"]
FP_DOMAIN = b"forge-s40-game-v1\x00"
MANIFEST = f"forge_sol_S40_manifest_{DATE}.md5"
SUMMARY = f"forge_sol_S40_summary_{DATE}.json"
LEDGER = f"forge_sol_S40_row_ledger_{DATE}.csv.gz"
RUN_INFO = "run_info.json"
STOPPED = "STOPPED.txt"
_OUT_DIR = None  # the NEW output directory once created (for the STOPPED.txt note)


class ToolError(Exception):
    """Bad input or a failed check: exit 1."""


class GuardStop(Exception):
    """A resource guard stopped the run: exit 3."""


# ------------------------------------------------------------------------------------------------ environment
def lower_priority():
    """Idle priority class (Windows) / nice 19 (POSIX); never raised."""
    try:
        if os.name == "nt":
            k = ctypes.windll.kernel32
            k.SetPriorityClass(k.GetCurrentProcess(), 0x40)  # IDLE_PRIORITY_CLASS
            return "idle"
        os.nice(19)
        return "nice19"
    except Exception as exc:  # pragma: no cover - best effort
        return f"unchanged ({exc})"


def free_ram_bytes():
    if os.name == "nt":
        class MS(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong), ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong), ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong), ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong), ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        m = MS(); m.dwLength = ctypes.sizeof(MS)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
        return int(m.ullAvailPhys)
    try:
        for line in open("/proc/meminfo"):
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) * 1024
    except OSError:
        pass
    return 1 << 62


class Guard:
    def __init__(self, min_free_gib, max_wall):
        self.min_free = float(min_free_gib) * (1 << 30); self.max_wall = float(max_wall); self.t0 = time.monotonic()
        self.lowest_free = None

    def __call__(self, where):
        free = free_ram_bytes()
        self.lowest_free = free if self.lowest_free is None else min(self.lowest_free, free)
        if free < self.min_free:
            raise GuardStop(f"STOPPED_LOW_RAM at {where}: free {free / (1 << 30):.2f} GiB < {self.min_free / (1 << 30):.2f}")
        if self.max_wall and time.monotonic() - self.t0 > self.max_wall:
            raise GuardStop(f"STOPPED_WALL_BUDGET at {where}: > {self.max_wall:.0f} s")


def resolved(p):
    return Path(os.path.abspath(os.path.realpath(str(p))))


def is_within(child, parent):
    c, p = os.path.normcase(str(resolved(child))), os.path.normcase(str(resolved(parent)))
    return c == p or c.startswith(p.rstrip("\\/") + os.sep)


def check_out_dir(out, input_paths, protected):
    """The output directory must be NEW (absent or empty), not inside/containing any input or a protected directory."""
    out = resolved(out)
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise ToolError(f"output directory exists and is not empty: {out}")
    for p in input_paths:
        d = resolved(p) if resolved(p).is_dir() else resolved(p).parent
        if is_within(out, d):
            raise ToolError(f"output directory {out} lies inside input directory {d}")
        if is_within(d, out):
            raise ToolError(f"input {p} lies inside the output directory {out}")
    for p in protected:
        if p and is_within(out, p):
            raise ToolError(f"output directory {out} lies inside protected directory {p}")
    return out


def file_md5(path, block=1 << 24):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(block), b""):
            h.update(b)
    return h.hexdigest()


def file_sha256(path, block=1 << 24):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(block), b""):
            h.update(b)
    return h.hexdigest()


# ------------------------------------------------------------------------------------------------ keys
def mix64(x):
    """splitmix64 finalizer (wrapping u64 arithmetic)."""
    x = (x ^ (x >> U64(30))) * U64(0xBF58476D1CE4E5B9)
    x = (x ^ (x >> U64(27))) * U64(0x94D049BB133111EB)
    return x ^ (x >> U64(31))


def keys64(boards, stm):
    """64-bit candidate key of (board32, side to move); candidates are always confirmed on the 33 bytes."""
    with np.errstate(over="ignore"):
        w = np.ascontiguousarray(boards, dtype=np.uint8).view("<u8").reshape(-1, 4)
        h = mix64(w[:, 0] ^ U64(0x9E3779B97F4A7C15))
        for j in (1, 2, 3):
            h = mix64(h ^ w[:, j])
        return mix64(h ^ (np.asarray(stm).astype(U64) + U64(0x632BE59BD9B4E019)))


def identity33(boards, stm):
    return np.concatenate([np.ascontiguousarray(boards, dtype=np.uint8), np.asarray(stm, np.uint8).reshape(-1, 1)], axis=1)


def void33(ident):
    return np.ascontiguousarray(ident, dtype=np.uint8).view(np.dtype((np.void, 33))).ravel()


# ------------------------------------------------------------------------------------------------ text records
def parse_line(line):
    """One text line (without '\\n') -> (board32 bytes, stm, score, result code, fullmove, pieces) or None.
    Accepts exactly what tools/fen2bin.cpp accepts (decimal result forms only; exotic strtod forms are rejected)."""
    p1 = line.find(b"|")
    if p1 < 0:
        return None
    p2 = line.find(b"|", p1 + 1)
    if p2 < 0:
        return None
    b = bytearray(32); rank = 7; file = 0; wk = bk = cnt = 0; i = 0
    while i < p1:
        c = line[i]
        if c == 32:
            break
        if c == 47:                      # '/'
            if file != 8:
                return None
            rank -= 1; file = 0
        elif 49 <= c <= 56:              # '1'..'8'
            file += c - 48
        else:
            pc = PIECE[c]
            if not pc or rank < 0 or file > 7:
                return None
            s = rank * 8 + file; file += 1
            if s & 1:
                b[s >> 1] |= pc << 4
            else:
                b[s >> 1] |= pc
            if pc == 6:
                wk += 1
            elif pc == 12:
                bk += 1
            cnt += 1
        i += 1
    if rank != 0 or file != 8 or wk != 1 or bk != 1 or cnt > 32:
        return None
    while i < p1 and line[i] == 32:
        i += 1
    if i >= p1 or line[i] not in (98, 119):
        return None
    stm = 1 if line[i] == 98 else 0
    m = SCORE_RE.match(line, p1 + 1, p2)
    if not m:
        return None
    v = int(m.group(1))
    if v < -32767 or v > 32767:
        return None
    m2 = RESULT_RE.match(line, p2 + 1)
    if not m2:
        return None
    r = float(m2.group(1))
    rc = 0 if r == 0.0 else 1 if r == 0.5 else 2 if r == 1.0 else -1
    if rc < 0:
        return None
    fields = line[:p1].split()
    fm = int(fields[5]) if len(fields) >= 6 and fields[5].isdigit() else -1
    return bytes(b), stm, v, rc, fm, cnt


def iter_lines(path, limit=None, block=1 << 24, digest=None):
    """Yield (offset, line incl. '\\n') of complete lines; the unterminated tail is the generator's return value."""
    off = 0; pending = b""; read = 0
    with open(path, "rb") as f:
        while True:
            want = block if limit is None else min(block, limit - read)
            if want <= 0:
                break
            chunk = f.read(want)
            if not chunk:
                break
            read += len(chunk)
            if digest is not None:
                digest.update(chunk)
            data = pending + chunk; start = 0
            while True:
                j = data.find(b"\n", start)
                if j < 0:
                    break
                yield off, data[start:j + 1]
                off += j + 1 - start; start = j + 1
            pending = data[start:]
    return pending


class TextSource:
    """One ordered text file of the second folder (sealed `.txt`, or `.part` with --include-part)."""

    def __init__(self, path, kind, limit=None, committed_lines=None):
        self.path = resolved(path); self.name = self.path.name; self.kind = kind; self.limit = limit
        self.committed_lines = committed_lines
        self.stem = self.name[:-len(".txt.part")] if kind == "part" else self.name[:-len(".txt")]

    def parse(self, guard):
        boards = bytearray(); stm = array.array("B"); score = array.array("h"); rc = array.array("B")
        fm = array.array("q"); pcs = array.array("B")
        bad = []; n = 0; used = 0; digest = hashlib.md5()
        gen = iter_lines(self.path, self.limit, digest=digest)
        while True:
            try:
                off, raw = next(gen)
            except StopIteration as stop:
                tail = stop.value or b""
                break
            rec = parse_line(raw[:-1])
            if rec is None:
                bad.append(n)
                if len(bad) <= 5:
                    print(f"bad line {self.name}:{n}: {raw[:120]!r}", file=sys.stderr)
            else:
                b, s, v, r, f, c = rec
                boards += b; stm.append(s); score.append(v); rc.append(r); fm.append(f); pcs.append(c)
            used = off + len(raw); n += 1
            if n % 2_000_000 == 0:
                guard(f"parse {self.name} line {n}")
        self.rows_read = n; self.tail_bytes = len(tail); self.md5_read = digest.hexdigest(); self.complete_bytes = used
        if bad:
            raise ToolError(f"{len(bad)} bad line(s) in {self.name} (first rows {bad[:5]}); fen2bin would write meta 255")
        if self.tail_bytes and (self.kind != "part" or self.limit is not None):
            raise ToolError(f"{self.name}: unterminated line ({self.tail_bytes} bytes) in a sealed file or a committed region")
        if self.committed_lines is not None and n != self.committed_lines:
            raise ToolError(f"{self.name}: {n} complete lines in the committed {self.limit} bytes, generator DB says {self.committed_lines}")
        k = len(stm)
        return dict(boards=np.frombuffer(bytes(boards), np.uint8).reshape(k, 32), stm=np.frombuffer(stm, np.uint8).copy(),
                    score=np.frombuffer(score, np.int16).copy(), rc=np.frombuffer(rc, np.uint8).copy(),
                    fm=np.frombuffer(fm, np.int64).copy(), pcs=np.frombuffer(pcs, np.uint8).astype(np.int16))


# ------------------------------------------------------------------------------------------------ references
def pos_count(path):
    with open(path, "rb") as f:
        head = f.read(HEADER)
    if len(head) != HEADER or head[:4] != b"FPOS" or int.from_bytes(head[4:8], "little") != 1:
        raise ToolError(f"bad FPOS v1 header: {path}")
    n = int.from_bytes(head[8:16], "little")
    if os.path.getsize(path) != HEADER + 35 * n:
        raise ToolError(f"FPOS size mismatch: {path}")
    return n


def hce_count(path):
    with open(path, "rb") as f:
        head = f.read(HEADER)
    if len(head) != HEADER or head[:4] != b"FHCE" or int.from_bytes(head[4:8], "little") != 1:
        raise ToolError(f"bad FHCE v1 header: {path}")
    n = int.from_bytes(head[8:16], "little")
    if os.path.getsize(path) != HEADER + 2 * n:
        raise ToolError(f"FHCE size mismatch: {path}")
    return n


class PosRef:
    """FPOS v1 shard, read-only, sequential chunked reads (boards, scores, metas are columnar)."""
    kind = "pos"

    def __init__(self, path):
        self.path = resolved(path); self.name = self.path.name; self.n = pos_count(self.path)

    def chunks(self, rows):
        n = self.n
        with open(self.path, "rb") as f:
            for a in range(0, n, rows):
                m = min(rows, n - a)
                f.seek(HEADER + 32 * a); boards = np.frombuffer(f.read(32 * m), np.uint8).reshape(m, 32)
                f.seek(HEADER + 32 * n + 2 * a); scores = np.frombuffer(f.read(2 * m), "<i2")
                f.seek(HEADER + 34 * n + a); metas = np.frombuffer(f.read(m), np.uint8)
                if len(metas) != m:
                    raise ToolError(f"short read: {self.path}")
                if (metas == 255).any():
                    raise ToolError(f"bad records (meta 255) in {self.path}")
                yield a, boards, metas & 1, scores, metas >> 1


class TextRef:
    """Ordered text shard used as a reference (e.g. a sealed main shard not yet converted)."""
    kind = "txt"

    def __init__(self, path):
        self.path = resolved(path); self.name = self.path.name; self.n = None

    def chunks(self, rows):
        a = 0; buf = []
        gen = iter_lines(self.path)
        while True:
            try:
                _, raw = next(gen)
            except StopIteration as stop:
                if stop.value:
                    raise ToolError(f"reference text {self.name} ends with an unterminated line")
                break
            rec = parse_line(raw[:-1])
            if rec is None:
                raise ToolError(f"bad line in reference text {self.name}:{a + len(buf)}")
            buf.append(rec)
            if len(buf) == rows:
                yield self._pack(a, buf); a += len(buf); buf = []
        if buf:
            yield self._pack(a, buf); a += len(buf)
        self.n = a

    @staticmethod
    def _pack(a, buf):
        boards = np.frombuffer(b"".join(r[0] for r in buf), np.uint8).reshape(len(buf), 32)
        return (a, boards, np.array([r[1] for r in buf], np.uint8), np.array([r[2] for r in buf], np.int16),
                np.array([r[3] for r in buf], np.uint8))


def make_ref(path):
    p = str(path)
    if p.endswith(".pos"):
        return PosRef(p)
    if p.endswith(".txt"):
        return TextRef(p)
    raise ToolError(f"reference must be .pos (FPOS v1) or .txt (ordered text): {p}")


class Matches:
    """Per second-row match state for one reference role."""

    def __init__(self, n):
        self.count = np.zeros(n, np.int64); self.first_file = np.full(n, -1, np.int32)
        self.first_row = np.full(n, -1, np.int64); self.conflict = np.zeros(n, bool); self.collisions = 0


def scan_role(refs, role, S, guard, chunk_rows, report, timing):
    """Stream every reference row; record exact matches against the second folder's rows."""
    order = np.argsort(S["key"], kind="stable"); skeys = S["key"][order]; ident = S["ident"]
    mt = Matches(len(skeys)); per_file = []
    for fi, ref in enumerate(refs):
        guard(f"before {role} {ref.name}"); t0 = time.monotonic(); rows = 0; hits = 0
        for a, boards, stm, scores, rcs in ref.chunks(chunk_rows):
            m = len(stm); rows += m
            if len(skeys):
                k = keys64(boards, stm)
                lo = np.searchsorted(skeys, k, "left"); hi = np.searchsorted(skeys, k, "right")
                cand = np.nonzero(hi > lo)[0]
                if len(cand):
                    cnt = (hi - lo)[cand]
                    r_rows = np.repeat(cand, cnt)
                    within = np.arange(len(r_rows)) - np.repeat(np.cumsum(cnt) - cnt, cnt)
                    s_rows = order[np.repeat(lo[cand], cnt) + within]
                    ok = (identity33(boards[r_rows], stm[r_rows]) == ident[s_rows]).all(axis=1)
                    mt.collisions += int((~ok).sum())
                    r_ok, s_ok = r_rows[ok], s_rows[ok]
                    if len(s_ok):
                        hits += len(s_ok)
                        np.add.at(mt.count, s_ok, 1)
                        for s, r in zip(s_ok.tolist(), r_ok.tolist()):  # earliest (file, row) per second row
                            if mt.first_file[s] < 0:
                                mt.first_file[s] = fi; mt.first_row[s] = a + r
                        diff = (scores[r_ok] != S["score"][s_ok]) | (rcs[r_ok] != S["rc"][s_ok])
                        if diff.any():
                            mt.conflict[s_ok[diff]] = True
            guard(f"{role} {ref.name} row {a + m}")
        per_file.append({"name": ref.name, "kind": ref.kind, "rows": int(rows), "matched_pairs": int(hits)})
        timing[f"{role}:{ref.name}"] = round(time.monotonic() - t0, 2)
    report[role] = per_file
    return mt


# ------------------------------------------------------------------------------------------------ games
def boundaries(fm, pc, rc):
    """Sol's conservative rule between consecutive rows: new game if fullmove decreases, pieces increase or result changes."""
    return (fm[1:] < fm[:-1]) | (pc[1:] > pc[:-1]) | (rc[1:] != rc[:-1])


def tripwire(flags, window=TRIPWIRE_WINDOW):
    if len(flags) < window - 1:
        return int(flags.sum())
    c = np.concatenate([[0], np.cumsum(flags, dtype=np.int64)])
    return int((c[window - 1:] - c[:-(window - 1)]).max())


def infer_groups(fm, pcs, rc):
    n = len(fm)
    info = {"rule": "inferred (Sol: fullmove decrease | piece-count increase | WHITE result change; no reset at file boundaries)",
            "window_rows": TRIPWIRE_WINDOW, "limit": TRIPWIRE_LIMIT}
    if n == 0:
        return np.zeros(0, np.int64), {**info, "largest_boundaries_in_window": 0, "result": "PASS"}
    if (fm < 0).any():
        raise ToolError("inferred game groups need the FEN fullmove field on every line (or pass --game-id-sidecars)")
    flags = boundaries(fm, pcs, rc); largest = tripwire(flags)
    info.update({"largest_boundaries_in_window": largest, "result": "PASS" if largest <= TRIPWIRE_LIMIT else "FAIL_SUSPECTED_INTERLEAVING"})
    if largest > TRIPWIRE_LIMIT:
        raise ToolError(f"interleaving tripwire: {largest} boundaries in a {TRIPWIRE_WINDOW}-row window (> {TRIPWIRE_LIMIT}); "
                        "the text is not game-ordered, pass authoritative --game-id-sidecars")
    return np.concatenate([[0], np.cumsum(flags, dtype=np.int64)]), info


def rec36_of(ident, score, rc):
    return np.concatenate([ident, np.ascontiguousarray(score.astype("<i2")).view(np.uint8).reshape(-1, 2),
                           rc.astype(np.uint8).reshape(-1, 1)], axis=1)


def fingerprints(gid, rec36):
    """Content fingerprint per group: sha256/128 over the group's rows in order (board32, stm, score le16, result)."""
    n_groups = int(gid.max()) + 1 if len(gid) else 0
    order = np.argsort(gid, kind="stable"); sg = gid[order]
    starts = np.searchsorted(sg, np.arange(n_groups), "left"); ends = np.searchsorted(sg, np.arange(n_groups), "right")
    return ["g1:" + hashlib.sha256(FP_DOMAIN + rec36[order[starts[g]:ends[g]]].tobytes()).hexdigest()[:32] for g in range(n_groups)]


def read_id_list(path):
    ids = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            t = line.strip()
            if not t or t.startswith("#"):
                continue
            if not GAMEID_RE.match(t):
                raise ToolError(f"bad game ID {t[:40]!r} in {path}")
            ids.add(t)
    return ids


def read_sidecar(path, n):
    ids = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            t = line.rstrip("\r\n")
            if not GAMEID_RE.match(t):
                raise ToolError(f"bad game ID {t[:40]!r} in {path}:{len(ids)}")
            ids.append(t)
    if len(ids) != n:
        raise ToolError(f"{path}: {len(ids)} game IDs for {n} text rows")
    return ids


# ------------------------------------------------------------------------------------------------ inputs of the second folder
def committed_from_db(db_copy, final_name):
    """Committed (bytes, lines) of an active file from a COPY of the generator's forge_seen_hashes.sqlite3."""
    try:
        con = sqlite3.connect(f"file:{resolved(db_copy).as_posix()}?mode=ro", uri=True)
        try:
            row = con.execute("SELECT bytes, lines FROM files WHERE name=?", (final_name,)).fetchone()
        finally:
            con.close()
    except sqlite3.Error as exc:
        raise ToolError(f"cannot read the generator DB copy {db_copy}: {exc}")
    if row is None:
        raise ToolError(f"{final_name} has no committed transaction in {db_copy}")
    return int(row[0]), int(row[1])


def second_sources(args):
    items = []
    for p in args.second:
        p = resolved(p)
        if p.is_dir():
            sealed = sorted(((int(m.group(1)), q) for q in p.iterdir() if (m := SELFPLAY_RE.match(q.name))), key=lambda t: t[0])
            parts = sorted(((int(m.group(1)), q) for q in p.iterdir() if (m := PART_RE.match(q.name))), key=lambda t: t[0])
            items += [(q, "sealed") for _, q in sealed]
            if parts and not args.include_part:
                print(f"note: {len(parts)} unsealed .part file(s) in {p} skipped (use --include-part)", file=sys.stderr)
            elif parts:
                if sealed and parts[0][0] < sealed[-1][0]:
                    raise ToolError(f"a .part file is older than the newest sealed file in {p}")
                items += [(q, "part") for _, q in parts]
        elif p.name.endswith(".txt"):
            items.append((p, "sealed"))
        elif p.name.endswith(".txt.part"):
            if not args.include_part:
                raise ToolError(f"{p.name} is unsealed; pass --include-part")
            items.append((p, "part"))
        else:
            raise ToolError(f"second input must be a folder, .txt or .txt.part: {p}")
    if not items:
        raise ToolError("no second-folder text files found")
    names = [q.name for q, _ in items]
    if len(set(names)) != len(names):
        raise ToolError("duplicate second-folder file names")
    if sum(kind == "part" for _, kind in items) > 1 and args.part_committed_bytes is not None:
        raise ToolError("--part-committed-bytes applies to exactly one .part file")
    sources = []
    for q, kind in items:
        limit = committed = None
        if kind == "part":
            if args.part_committed_bytes is not None:
                limit = int(args.part_committed_bytes)
            elif args.seen_db:
                limit, committed = committed_from_db(args.seen_db, q.name[:-len(".part")])
        sources.append(TextSource(q, kind, limit, committed))
    return sources


# ------------------------------------------------------------------------------------------------ outputs
def write_new(path, data):
    with open(path, "xb") as f:
        f.write(data)


def write_fpos(path, boards, scores, metas):
    n = len(metas)
    with open(path, "xb") as f:
        f.write(b"FPOS" + (1).to_bytes(4, "little") + n.to_bytes(8, "little"))
        f.write(np.ascontiguousarray(boards, np.uint8).tobytes())
        f.write(np.ascontiguousarray(scores, "<i2").tobytes())
        f.write(np.ascontiguousarray(metas, np.uint8).tobytes())


def write_fhce(path, values):
    n = len(values)
    with open(path, "xb") as f:
        f.write(b"FHCE" + (1).to_bytes(4, "little") + n.to_bytes(8, "little"))
        f.write(np.ascontiguousarray(values, "<i2").tobytes())


def run_hce_dump(exe, out_dir, txt_name, hce_name, n):
    kw = {"creationflags": 0x40} if os.name == "nt" else {"preexec_fn": lambda: os.nice(19)}  # IDLE_PRIORITY_CLASS
    p = subprocess.run([str(exe), txt_name, hce_name], cwd=str(out_dir), capture_output=True, text=True, **kw)
    if p.returncode != 0:
        raise ToolError(f"hce_dump failed ({p.returncode}) on {txt_name}: {p.stdout.strip()} {p.stderr.strip()}")
    if hce_count(out_dir / hce_name) != n:
        raise ToolError(f"hce_dump wrote a wrong row count for {txt_name}")
    if (np.fromfile(out_dir / hce_name, "<i2", offset=HEADER) == -32768).any():
        raise ToolError(f"hce_dump marked unparsable FENs in {txt_name}")
    return p.stdout.strip()


# ------------------------------------------------------------------------------------------------ merge
def merge(args):
    global _OUT_DIR
    _OUT_DIR = None
    t_start = time.monotonic(); priority = lower_priority(); guard = Guard(args.min_free_ram_gib, args.max_wall_seconds)
    timing = {}
    if not PREFIX_RE.match(args.prefix):
        raise ToolError("--prefix may contain only letters, digits, '_', '.', '-'")
    if bool(args.hce_dump) + bool(args.second_hce_dir) + bool(args.no_hce) != 1:
        raise ToolError("choose exactly one of --hce-dump EXE, --second-hce-dir DIR, --no-hce")
    if args.rows_per_file <= 0 or args.chunk_rows <= 0:
        raise ToolError("--rows-per-file and --chunk-rows must be positive")
    protected = ([] if args.no_protected_defaults else list(DEFAULT_PROTECTED)) + list(args.protected or [])
    if args.seen_db:  # checked before anything opens it: the live generator DB is never opened
        for p in args.second:
            d = resolved(p) if resolved(p).is_dir() else resolved(p).parent
            if is_within(args.seen_db, d):
                raise ToolError("--seen-db must be a COPY outside the second folder (the live generator DB is never opened)")
    sources = second_sources(args)
    if args.second_hce_dir and any(s.kind == "part" for s in sources):
        raise ToolError("an unsealed .part has no .hce in --second-hce-dir; use --hce-dump")
    refs_main = [make_ref(p) for p in args.main or []]
    refs_hold = [make_ref(p) for p in args.holdout or []]
    inputs = [s.path for s in sources] + [r.path for r in refs_main + refs_hold]
    inputs += [Path(p) for p in list(args.main_game_ids or []) + list(args.holdout_game_ids or [])]
    inputs += [Path(p) for p in ([args.second_hce_dir] if args.second_hce_dir else []) + ([args.seen_db] if args.seen_db else [])]
    if args.hce_dump:
        inputs.append(Path(args.hce_dump))
    out = check_out_dir(args.out, inputs, protected)
    norm = lambda refs: {os.path.normcase(str(r.path)) for r in refs}
    if norm(refs_main) & norm(refs_hold):
        raise ToolError("a file is listed as both main and holdout")
    names_m = [r.name for r in refs_main]; names_h = [r.name for r in refs_hold]
    guard("start")
    out.mkdir(parents=True, exist_ok=True); _OUT_DIR = out

    # ---- 1. parse the second folder
    parts = []; src_info = []
    for s in sources:
        guard(f"before parse {s.name}"); t0 = time.monotonic()
        d = s.parse(guard); parts.append(d); timing[f"parse:{s.name}"] = round(time.monotonic() - t0, 2)
        size = os.path.getsize(s.path)
        src_info.append({"name": s.name, "kind": s.kind, "rows": int(len(d["stm"])), "file_bytes": int(size),
                         "bytes_used": int(s.complete_bytes), "md5_of_bytes_read": s.md5_read,
                         "incomplete_tail_bytes": int(s.tail_bytes),
                         "bytes_after_committed_offset": int(size - s.limit) if s.limit is not None else None,
                         "committed_offset": ("sealed file" if s.kind == "sealed" else "generator DB copy" if s.committed_lines is not None
                                              else "--part-committed-bytes" if s.limit is not None else "UNVERIFIED (complete lines only)")})
    nrows = [len(d["stm"]) for d in parts]; offs_src = np.concatenate([[0], np.cumsum(nrows)]).astype(np.int64); N = int(offs_src[-1])
    S = {k: np.concatenate([d[k] for d in parts]) for k in ("stm", "score", "rc", "fm", "pcs")}
    S["boards"] = np.concatenate([d["boards"] for d in parts]).reshape(N, 32)
    S["ident"] = identity33(S["boards"], S["stm"]); S["key"] = keys64(S["boards"], S["stm"])
    src_of = np.repeat(np.arange(len(parts)), nrows); row_of = np.arange(N) - offs_src[src_of]

    # ---- 2. game groups and game IDs
    if args.game_id_sidecars:
        raw_ids = []
        for s, d in zip(sources, parts):
            raw_ids += read_sidecar(s.path.with_name(s.name + ".gameid"), len(d["stm"]))
        uniq = {}
        gid = np.array([uniq.setdefault(t, len(uniq)) for t in raw_ids], np.int64)
        game_ids = list(uniq)
        ginfo = {"rule": "explicit row-aligned game IDs (<text name>.gameid)"}
    else:
        gid, ginfo = infer_groups(S["fm"], S["pcs"], S["rc"])
        game_ids = fingerprints(gid, rec36_of(S["ident"], S["score"], S["rc"]))
    n_groups = len(game_ids); ginfo["groups"] = n_groups
    ids_main = set().union(*[read_id_list(p) for p in args.main_game_ids]) if args.main_game_ids else set()
    ids_hold = set().union(*[read_id_list(p) for p in args.holdout_game_ids]) if args.holdout_game_ids else set()

    # ---- 3. reference scans (exact position matches)
    scan_report = {}
    mt_hold = scan_role(refs_hold, "holdout", S, guard, args.chunk_rows, scan_report, timing)
    mt_main = scan_role(refs_main, "main", S, guard, args.chunk_rows, scan_report, timing)

    # ---- 4. decisions (first applicable reason wins)
    in_hold = mt_hold.count > 0; in_main = mt_main.count > 0
    g_touch = np.zeros(n_groups, bool)
    if in_hold.any() and args.holdout_game_rule == "drop-group":
        g_touch[np.unique(gid[in_hold])] = True
    g_hold_id = np.array([g in ids_hold for g in game_ids], bool)
    g_main_id = np.array([g in ids_main for g in game_ids], bool)
    reason = np.full(N, R_KEPT, np.uint8); free = np.ones(N, bool)

    def assign(mask, code):
        sel = free & mask; reason[sel] = code; free[sel] = False

    assign(in_hold, R_HOLD_POS)
    if N:
        assign((g_touch | g_hold_id)[gid], R_HOLD_GAME)
        assign(g_main_id[gid], R_MAIN_GAME)
    assign(in_main, R_DUP_MAIN)
    dup_inclusive = np.zeros(N, bool); dup_conflict = np.zeros(N, bool); dup_first = np.full(N, -1, np.int64)
    if N:
        v = void33(S["ident"])
        _, first_all, inv_all = np.unique(v, return_index=True, return_inverse=True)
        dup_inclusive = first_all[inv_all.ravel()] != np.arange(N)
        surv = np.nonzero(free)[0]
        if len(surv):
            _, first_s, inv_s = np.unique(v[surv], return_index=True, return_inverse=True)
            inv_s = inv_s.ravel(); later = first_s[inv_s] != np.arange(len(surv))
            rows = surv[later]; firsts = surv[first_s[inv_s]][later]
            dup_first[rows] = firsts
            dup_conflict[rows] = (S["score"][rows] != S["score"][firsts]) | (S["rc"][rows] != S["rc"][firsts])
            reason[rows] = R_DUP_SECOND; free[rows] = False
    kept = np.nonzero(reason == R_KEPT)[0]

    # ---- 5. outputs (NEW files only, exclusive create); text is one sequential pass with the md5 re-checked
    guard("before outputs"); t0 = time.monotonic()
    hce_all = None
    if args.second_hce_dir:
        vals = []
        for s in sources:
            hp = resolved(args.second_hce_dir) / (s.stem + ".hce")
            if hce_count(hp) != s.rows_read:
                raise ToolError(f"{hp.name}: row count differs from {s.name}")
            vals.append(np.fromfile(hp, "<i2", offset=HEADER))
        hce_all = np.concatenate(vals) if vals else np.zeros(0, np.int16)
        if (hce_all == -32768).any():
            raise ToolError("bad hce values (-32768) in the second folder's .hce")
    rpf = args.rows_per_file; n_out = (len(kept) + rpf - 1) // rpf
    out_file = np.full(N, -1, np.int32); out_row = np.full(N, -1, np.int64)
    out_file[kept] = np.arange(len(kept)) // rpf; out_row[kept] = np.arange(len(kept)) % rpf
    stems = [f"{args.prefix}_{k + 1:03d}" for k in range(n_out)]
    cur = -1; fh = None; is_kept = reason == R_KEPT
    try:
        for si, s in enumerate(sources):
            digest = hashlib.md5(); base = int(offs_src[si]); r = 0
            gen = iter_lines(s.path, s.limit, digest=digest)
            while True:
                try:
                    _, raw = next(gen)
                except StopIteration:
                    break
                g = base + r
                if is_kept[g]:
                    k = int(out_file[g])
                    if k != cur:
                        if fh is not None:
                            fh.close()
                        fh = open(out / f"{stems[k]}.txt", "xb"); cur = k
                    fh.write(raw)
                r += 1
            if digest.hexdigest() != s.md5_read or r != s.rows_read:
                raise ToolError(f"{s.name} changed while the merge ran")
    finally:
        if fh is not None:
            fh.close()
    outputs = []
    for k, stem in enumerate(stems):
        sel = kept[k * rpf:(k + 1) * rpf]
        write_fpos(out / f"{stem}.pos", S["boards"][sel], S["score"][sel], (S["stm"][sel] | (S["rc"][sel] << 1)).astype(np.uint8))
        write_new(out / f"{stem}.pos.info", f"source={stem}.txt\nlines={len(sel)}\nrecords={len(sel)}\nbad=0\n".encode())
        rec = {"stem": stem, "rows": int(len(sel))}
        if args.hce_dump:
            rec["hce_dump_stdout"] = run_hce_dump(resolved(args.hce_dump), out, f"{stem}.txt", f"{stem}.hce", len(sel))
        elif hce_all is not None:
            write_fhce(out / f"{stem}.hce", hce_all[sel])
            write_new(out / f"{stem}.hce.info", f"source={stem}.txt\nlines={len(sel)}\nrecords={len(sel)}\nfrom=row subset of the second folder's .hce\n".encode())
        outputs.append(rec)
        guard(f"after output {stem}")
    timing["outputs"] = round(time.monotonic() - t0, 2)

    # ---- 6. ledger (streamed, gzip mtime 0), summary, manifest, SHA256SUMS
    with open(out / LEDGER, "xb") as raw_f, gzip.GzipFile(filename="", mode="wb", fileobj=raw_f, mtime=0) as z:
        z.write(b"source,row,group,game_id,reason,match_role,match_file,match_row,label_conflict,out_file,out_row\n")
        for a in range(0, N, 100_000):
            lines = []
            for i in range(a, min(N, a + 100_000)):
                rs = int(reason[i]); role = mf = mr = ""; conflict = 0
                if rs == R_HOLD_POS:
                    role, mf, mr, conflict = "holdout", names_h[mt_hold.first_file[i]], int(mt_hold.first_row[i]), int(mt_hold.conflict[i])
                elif rs == R_DUP_MAIN:
                    role, mf, mr, conflict = "main", names_m[mt_main.first_file[i]], int(mt_main.first_row[i]), int(mt_main.conflict[i])
                elif rs == R_DUP_SECOND:
                    f0 = int(dup_first[i]); role, mf, mr, conflict = "second", sources[src_of[f0]].name, int(row_of[f0]), int(dup_conflict[i])
                of = stems[out_file[i]] if out_file[i] >= 0 else ""
                orow = int(out_row[i]) if out_row[i] >= 0 else ""
                lines.append(f"{sources[src_of[i]].name},{int(row_of[i])},{int(gid[i])},{game_ids[gid[i]]},{REASONS[rs]},{role},{mf},{mr},{conflict},{of},{orow}\n")
            z.write("".join(lines).encode())
    gsize = np.bincount(gid, minlength=n_groups) if N else np.zeros(0, np.int64)
    gkept = np.bincount(gid[kept], minlength=n_groups) if N else np.zeros(0, np.int64)
    counts = {r: int((reason == i).sum()) for i, r in enumerate(REASONS)}
    for rec in outputs:
        for ext in ("txt", "pos", "hce"):
            p = out / f"{rec['stem']}.{ext}"
            if p.exists():
                rec[ext] = {"bytes": os.path.getsize(p), "md5": file_md5(p)}
    summary = {
        "tool": TOOL, "tool_sha256": file_sha256(__file__), "status": "COMPLETED",
        "identity": "board32 + side to move (FPOS view: castling, e.p. and clocks ignored); exact 33-byte confirmation of every 64-bit candidate",
        "reason_order": list(REASONS),
        "parameters": {"prefix": args.prefix, "rows_per_file": rpf, "holdout_game_rule": args.holdout_game_rule,
                       "game_ids": "sidecars" if args.game_id_sidecars else "inferred groups + content fingerprint",
                       "hce": "hce_dump" if args.hce_dump else "second_hce_dir" if args.second_hce_dir else "none",
                       "include_part": bool(args.include_part)},
        "inputs": {"second": src_info, "main": scan_report.get("main", []), "holdout": scan_report.get("holdout", []),
                   "main_game_id_lists": [Path(p).name for p in args.main_game_ids or []], "main_game_ids": len(ids_main),
                   "holdout_game_id_lists": [Path(p).name for p in args.holdout_game_ids or []], "holdout_game_ids": len(ids_hold),
                   "hce_dump_sha256": file_sha256(args.hce_dump) if args.hce_dump else None},
        "second_rows": N, "reasons": counts, "dropped": N - counts["kept"],
        "inclusive": {"rows_with_position_in_holdout": int(in_hold.sum()), "rows_with_position_in_main": int(in_main.sum()),
                      "rows_with_position_earlier_in_second": int(dup_inclusive.sum()),
                      "distinct_holdout_positions_hit": int(len(np.unique(void33(S["ident"][in_hold])))) if in_hold.any() else 0,
                      "distinct_main_positions_hit": int(len(np.unique(void33(S["ident"][in_main])))) if in_main.any() else 0},
        "label_conflicts": {"holdout_position": int((mt_hold.conflict & (reason == R_HOLD_POS)).sum()),
                            "dup_main": int((mt_main.conflict & (reason == R_DUP_MAIN)).sum()),
                            "dup_second": int((dup_conflict & (reason == R_DUP_SECOND)).sum())},
        "key_collisions_rejected": {"holdout": mt_hold.collisions, "main": mt_main.collisions},
        "groups": {**ginfo, "touching_holdout": int(g_touch.sum()), "in_holdout_id_list": int(g_hold_id.sum()),
                   "in_main_id_list": int(g_main_id.sum()), "fully_dropped": int(((gkept == 0) & (gsize > 0)).sum()),
                   "partially_kept": int(((gkept > 0) & (gkept < gsize)).sum()), "fully_kept": int(((gkept == gsize) & (gsize > 0)).sum())},
        "per_source": [{"name": s.name, **{r: int(((src_of == si) & (reason == i)).sum()) for i, r in enumerate(REASONS)}}
                       for si, s in enumerate(sources)],
        "outputs": outputs,
        "record_format": {"pos": "FPOS v1 = tools/fen2bin.cpp layout ('FPOS', u32 1, u64 n, boards[n][32], int16 score[n], u8 meta[n]; meta = stm | 2*WHITE result code)",
                          "hce": ("FHCE v1 = tools/hce_dump.cpp layout ('FHCE', u32 1, u64 n, int16[n])" if not args.no_hce else
                                  "not written (--no-hce): v3b needs .hce, these outputs are NOT loadable"),
                          "txt": "the kept source lines, byte for byte, in source order"},
    }
    write_new(out / SUMMARY, (json.dumps(summary, indent=1) + "\n").encode())
    names = sorted(q.name for q in out.iterdir() if q.is_file() and q.name not in (MANIFEST, RUN_INFO, "SHA256SUMS"))
    run_info = {"tool": TOOL, "argv": sys.argv, "out": str(out), "second": [str(s.path) for s in sources],
                "main": [str(r.path) for r in refs_main], "holdout": [str(r.path) for r in refs_hold],
                "seconds": round(time.monotonic() - t_start, 2), "step_seconds": timing, "priority": priority,
                "python": sys.version.split()[0], "numpy": np.__version__, "platform": platform.platform(),
                "lowest_free_ram_gib": round((guard.lowest_free or 0) / (1 << 30), 2),
                "input_size_mtime_after": {str(p): [os.path.getsize(p), os.path.getmtime(p)] for p in inputs if Path(p).is_file()}}
    write_new(out / RUN_INFO, (json.dumps(run_info, indent=1) + "\n").encode())
    write_new(out / MANIFEST, "".join(f"{file_md5(out / n)}  {n}\n" for n in names).encode())  # written last but one: the seal
    allf = sorted(q.name for q in out.iterdir() if q.is_file() and q.name != "SHA256SUMS")
    write_new(out / "SHA256SUMS", "".join(f"{file_sha256(out / n)}  {n}\n" for n in allf).encode())
    print(json.dumps({"status": "COMPLETED", "out": str(out), "second_rows": N, "reasons": counts, "groups": n_groups,
                      "outputs": [(o["stem"], o["rows"]) for o in outputs], "seconds": run_info["seconds"]}, indent=1))
    return 0


# ------------------------------------------------------------------------------------------------ gameids / verify
def gameids(args):
    lower_priority(); guard = Guard(args.min_free_ram_gib, 0)
    out = resolved(args.out)
    if out.exists():
        raise ToolError(f"{out} exists (never overwritten)")
    for p in args.text:
        if is_within(out, resolved(p).parent):
            raise ToolError("the ID list may not be written into an input directory")
    fm, pcs, rc, ident, score = [], [], [], [], []
    for p in args.text:
        d = TextSource(p, "sealed").parse(guard)
        fm.append(d["fm"]); pcs.append(d["pcs"]); rc.append(d["rc"]); ident.append(identity33(d["boards"], d["stm"])); score.append(d["score"])
    fm, pcs, rc, ident, score = map(np.concatenate, (fm, pcs, rc, ident, score))
    gid, info = infer_groups(fm, pcs, rc)
    n_groups = int(gid.max()) + 1 if len(gid) else 0
    ids = sorted(set(fingerprints(gid, rec36_of(ident, score, rc))))
    body = (f"# {TOOL} game ids v1: fingerprint sha256/128 of (board32, stm, score le16, result) per row; groups by "
            f"Sol's ordered-text rule; sources: {' '.join(Path(p).name for p in args.text)}; rows {len(fm)}; groups {n_groups}\n")
    with open(out, "x", encoding="utf-8", newline="\n") as f:
        f.write(body + "".join(i + "\n" for i in ids))
    print(json.dumps({"out": str(out), "rows": int(len(fm)), "groups": n_groups, "unique_ids": len(ids), "tripwire": info}))
    return 0


def verify(args):
    out = resolved(args.dir); problems = []
    man = out / MANIFEST
    if not man.exists():
        raise ToolError(f"no manifest: {man} (not sealed)")
    if (out / STOPPED).exists():
        problems.append(f"{STOPPED} present")
    listed = {}
    for line in man.read_text(encoding="utf-8").splitlines():
        h, n = line.split("  ", 1); listed[n] = h
        if not (out / n).exists():
            problems.append(f"missing {n}")
        elif file_md5(out / n) != h:
            problems.append(f"md5 mismatch {n}")
    summ = json.loads((out / SUMMARY).read_text(encoding="utf-8"))
    for rec in summ["outputs"]:
        st = rec["stem"]; n = rec["rows"]
        if pos_count(out / f"{st}.pos") != n:
            problems.append(f"{st}.pos rows")
        if (np.fromfile(out / f"{st}.pos", np.uint8, offset=HEADER + 34 * n) == 255).any():
            problems.append(f"{st}.pos meta 255")
        with open(out / f"{st}.txt", "rb") as f:
            if sum(1 for _ in f) != n:
                problems.append(f"{st}.txt lines")
        if (out / f"{st}.hce").exists():
            if hce_count(out / f"{st}.hce") != n:
                problems.append(f"{st}.hce rows")
            elif (np.fromfile(out / f"{st}.hce", "<i2", offset=HEADER) == -32768).any():
                problems.append(f"{st}.hce bad value")
        elif summ["parameters"]["hce"] != "none":
            problems.append(f"{st}.hce missing")
    if sum(r["rows"] for r in summ["outputs"]) != summ["reasons"]["kept"]:
        problems.append("output rows != kept")
    print(json.dumps({"dir": str(out), "files_in_manifest": len(listed), "problems": problems, "result": "PASS" if not problems else "FAIL"}))
    return 0 if not problems else 1


# ------------------------------------------------------------------------------------------------ CLI
def build_parser():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    m = sub.add_parser("merge", help="dedupe the second folder and write NEW sealed shards")
    m.add_argument("--second", nargs="+", required=True, help="second self-play folder(s) or its text files, chronological")
    m.add_argument("--include-part", action="store_true", help="also read unsealed forge_selfplay_NNN.txt.part (complete/committed lines only)")
    m.add_argument("--seen-db", help="a COPY of the second folder's forge_seen_hashes.sqlite3 (+ -wal): committed offset of the .part")
    m.add_argument("--part-committed-bytes", type=int, help="committed byte offset of the one .part file")
    m.add_argument("--main", nargs="*", default=[], help="main training shards (.pos FPOS v1 or .txt)")
    m.add_argument("--holdout", nargs="*", default=[], help="holdout shards (.pos or .txt), e.g. 013 and 014")
    m.add_argument("--main-game-ids", nargs="*", default=[], help="game-ID list files of the main folder")
    m.add_argument("--holdout-game-ids", nargs="*", default=[], help="game-ID list files of the holdout")
    m.add_argument("--game-id-sidecars", action="store_true", help="read authoritative <text name>.gameid sidecars (one ID per line)")
    m.add_argument("--holdout-game-rule", choices=["drop-group", "off"], default="drop-group",
                   help="drop every row of a game that contains a holdout position (default)")
    m.add_argument("--hce-dump", help="hce_dump executable (tools/hce_dump.cpp build) run on each NEW text shard")
    m.add_argument("--second-hce-dir", help="directory with <stem>.hce for each sealed second text file (rows are subset)")
    m.add_argument("--no-hce", action="store_true", help="write no .hce (counting only; v3b cannot load such output)")
    m.add_argument("--out", required=True, help="NEW output directory (absent or empty)")
    m.add_argument("--prefix", default="forge_s40_merged", help="output stem prefix (default forge_s40_merged)")
    m.add_argument("--rows-per-file", type=int, default=10_000_000)
    m.add_argument("--chunk-rows", type=int, default=500_000)
    m.add_argument("--min-free-ram-gib", type=float, default=6.0)
    m.add_argument("--max-wall-seconds", type=float, default=0.0)
    m.add_argument("--protected", nargs="*", default=[], help="extra directories the output may never lie in")
    m.add_argument("--no-protected-defaults", action="store_true", help=argparse.SUPPRESS)
    g = sub.add_parser("gameids", help="fingerprint game-ID list of ordered reference text files")
    g.add_argument("--text", nargs="+", required=True)
    g.add_argument("--out", required=True)
    g.add_argument("--min-free-ram-gib", type=float, default=6.0)
    v = sub.add_parser("verify", help="check a sealed output directory")
    v.add_argument("dir")
    return ap


def note_stop(msg):
    if _OUT_DIR is not None and _OUT_DIR.is_dir() and not (_OUT_DIR / STOPPED).exists():
        try:
            write_new(_OUT_DIR / STOPPED, (msg + "\nthis directory is NOT sealed (no manifest); nothing in it may be used\n").encode())
        except OSError:
            pass


def main(argv=None):
    global _OUT_DIR
    _OUT_DIR = None  # only the current merge's own NEW directory may receive a STOPPED.txt note
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] not in ("merge", "gameids", "verify", "-h", "--help"):
        argv = ["merge"] + argv
    args = build_parser().parse_args(argv)
    try:
        if args.cmd == "gameids":
            return gameids(args)
        if args.cmd == "verify":
            return verify(args)
        if args.cmd == "merge":
            return merge(args)
        build_parser().print_help()
        return 2
    except GuardStop as exc:
        print(str(exc), file=sys.stderr); note_stop(str(exc)); return 3
    except ToolError as exc:
        print(f"FAILED: {exc}", file=sys.stderr); note_stop(f"FAILED: {exc}"); return 1


if __name__ == "__main__":
    raise SystemExit(main())
