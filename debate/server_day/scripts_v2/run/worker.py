"""Opus 2026-11-23, version 2 of the server day's worker (Fable's FABLE-2311-V2-SCRIPTS-TO-OPUS; FORMATS 2.2
sections 0, 0.1 and 1.1 to 1.8; SETUP_PLAN 2.2 D5). ONE worker of one slot: one engine process plays game after
game, and what the engine printed goes, unchanged, into sealed pieces. Standard library only; the same file runs
on the PC and on Linux.

    worker.py --root DIR --slot K --exe E --net N --manifest MANIFEST.json --known-startup startup.json
              [--openings FILE] [--game-seconds T = 600] [--trace] [--rehearsal --plant <kind>:<counter>]

DIR holds RUN.json (1.1; its sha256 is the run fingerprint), SCHEDULE.<n>.json (1.2), RESUME.<n>.json (1.3),
FENCE.json (1.8), an operator's STOP file, ranges/ (1.7) and one folder w<NNN> a slot (1.3 to 1.5).

BEFORE IT CHANGES ANYTHING (exit 4, 5 for the engine file, 3 for the lock; the reason named; nothing written):
 - RUN.json and every schedule are canonical records (FORMATS 0: printable ASCII, keys sorted, no spaces, one LF,
   no key twice, integers only); the schedules form their chain (n, prev, run fingerprint, cutoffs never later,
   a range only shortened; that a STARTED range is unchanged is checked again once the journal is read, before
   the epoch line); the manifest is the header's (options_sha256 = sha256 of its option lines each ended by LF,
   placeholders as written; game_line; net_sha256); the engine file is the header's engine_sha256 when this start
   may run it (1.3; again at every engine start);
 - this machine's boot id is the header's, or a RESUME record admits it (1.3: every RESUME on disk in its chain,
   schema 2, n, prev; the newest whose new boot id is this one, with instance_provable true; 2.4: at the FIRST
   start under this boot this slot's row is the journal's last index and seal and the epoch line names the
   RESUME; at a later start under it the boot's first epoch line must name this RESUME and carry that row);
 - FENCE.json is this run's and its cutoff_utc is the D in force copied (RUN.json's in the pilot, 2.4);
 - the slot folder is this run's: its IDENTITY.json is this run's, and a folder with a journal and no identity is
   another run's (Astra's case 8);
 - the slot's lock is free: an OS lock on w<NNN>/LOCK, which the system releases when the process ends.
THEN, UNDER THE LOCK: the journal (1.4): every LF-ended line valid and following the one before it (epochs rising
by one, the games of the open piece with rising ends, a `closed` line naming a seal file with that sha256 whose
index and prev_seal continue the chain, nothing after `ended`); a damaged line that is not the last stops the slot, the journal kept as it is; an unfinished last
line is dropped only when the piece holds the bytes up to the `end` of the line before it. An `epoch` line at
every start, with its `mode` (2.7), decided before the line is written: `seal_only` when the start finds the fence
in force, the dispatch end passed, D come, or the slot's first id that is not passed journalled `unfinished` (a
barrier: no epoch dispatches after D); `play` otherwise. A `seal_only` start hashes no engine file, starts no
engine, follows no schedule and reserves nothing. A journalled id outside the slot's ranges, or one AFTER the
first id that is not passed (2.7, Neon 153430Z), stops the start before its epoch line (unreconciled, exit 4).
The open piece is cut back to the journal's end and its records must be the journal's (ids,
bindings recomputed, rows); a piece moved to closed/ whose `closed` line is missing is finished: its seal written
if it has none, an existing seal checked against the evidence, never a second seal.
THE DAY (D5; FORMATS 2.9 1.8 point 1): D is the earlier of the header's hard_cutoff_utc and the newest schedule's
cutoff_utc; games are reserved until dispatch_end_utc (D - g) and never once FENCE.json exists. THE CLOCKS (2.7,
run/clockwatch.py): UTC, the steady clock and the boot-time clock are read together at the start (the anchor); a
bound has come when the EARLIEST of them says so, and once passed it stays passed (a wall clock set back never
revives play). Where the system has no boot-time clock (Windows) the worker judges by UTC and the steady clock; the
clock plants of a rehearsal emulate it by the steady clock. ONE function, clock_state(), judges the dispatch end and
D before every reservation and after every wait for the engine (a success and an error alike): play, the dispatch
end, D, or the HOLD (UTC alone says a bound has come and stands more than 10 s ahead of the anchor plus the
boot-time clock). THE WATCH (2.9): beside every wait for the engine runs clockwatch.Watch on a handle of the native
engine process that a reused process number cannot confuse; at D less the stop allowance (2 s, the editor's choice
until it is measured) by the earliest clock, or in the hold, it ends that process ALONE (never a group), verifies
that it is gone and notes its reason; its refresh follows a newer valid schedule while the game runs, so a tightened
D is taken at once (the ranges count from the next reservation; the game in flight counts as started for 1.2's
check). The steady cutoff handed to the driver is computed afresh before every wait. A game the watch ended at D,
or one whose wait returns when D has come by any clock (also a game that ended by itself just before D and is
judged after a suspension: the careful side), is thrown away whole and journalled `unfinished`, and the slot ends
("cutoff"); after D nothing is sent. A wait that returns after the dispatch end alone keeps the game's disposition.
THE HOLD, in this order: the game in flight `failed` (why "clock", thrown away whole), the open piece sealed, the
line `ALARM clock: ...` written, flushed and printed, exit 8, no `ended` line (as at the STOP file); a later `play`
start admitted anew plays the id again. THE WATCH'S ALARM (Fable 15:54, corrected 16:02; clockwatch 4): the native
process must be gone AT D. A process never confirmed gone ("still there"), with the reason cutoff a decision made
when D itself had already come ("decided after D"), an exit first confirmed after D ("gone after D") or more than
one allowance after the decision ("gone late"), and an error inside the watch, each end the same way: the game
journalled by the watch's reason (`unfinished` at D, else `failed`), the piece sealed, the line `ALARM watch: <the
word>: ...` with the readings of the decision, the stop and the exit and the module's own alarm text written,
flushed and printed, exit 8, no `ended` line. A tighter D found after its trigger but stopped and gone before D kept
the rule: the normal end, its
lateness recorded in the watch's lines (late=True late_discovery=True), never written as on time. The watch's
refresh only reads (it may outlive the watch: reader_stalled is logged). A `seal_only` start seals what is there
and ends the slot (the finalizer of 1.8; Astra's case 9).
GAMES: the lowest counter of the slot's ranges, in round order, without a final state; the header's pilot_ranges
are schedule 0. Every schedule file is read once (2.6); before every reservation the NEXT number is followed
while one is there (2.7), so only the highest valid schedule authorizes a game; with nothing to play the worker
waits for a new schedule, the dispatch end, the fence or the STOP file. The opening of an id: rule "seed" =
`plies` moves, each among the engine's own legal moves in sorted order, by sha256(root seed|id|ply); rule "list"
= entry (counter - 1) mod count of the list file the header names. An opening after which no legal move exists
sends no game line: `noselfgame` with its plies. Otherwise ucinewgame, the position line, the frozen game line;
every line up to `sgend` is a row of its shape (run/engine_lines.py); a completed game with zero rows is `done`
with rows 0. THE BINDING (A23): exactly one position line between the game's start and its game line, equal token
for token to the reservation; otherwise `refused`, exit 7. An engine that fails (a refusal, sgerror, a timeout,
bad bytes, gone) is killed and never used again; the game is `failed` and played again by a new engine after the
whole start-up check; three in a row: exit 6.
PIECES: a record (0.1, run/record.py) is appended to open/p<i>.raw, the file and (where the system has it) its
folder flushed, THEN the journal line. A piece holds at most piece_games games of ONE round. It is closed when
full, when its range is complete, at a stop and at the end: moved to closed/ (link, folder flush, unlink),
checked against the journal, sealed create-only (1.5; 0: other bytes under the final name = the newcomer kept as
<final>.conflict.<12 hex> and a stop), then the `closed` line. A complete range, and at the end every range of
the slot, gets its range seal (1.7). The end (1.8): the last piece sealed, the range seals, `ended` (why
"finalizer" when this start reserved nothing because the end had come, "ranges done" when every range is
complete, otherwise "cutoff"), the lock released. w<NNN>/heartbeat is replaced by a rename after every game.
DISPOSITIONS (1.7; 2.4: six): a final state as journalled; a `failed` id never played again is unfinished; an id
without any line is never_dispatched, except when a finalizer ends a slot after an EARLIER `play` epoch (2.7):
then the FIRST counter of the slot's ranges that is not passed (2.6: only done, noselfgame and refused are passed)
is dispatch_unknown when it has no line (Astra 150955Z: a search can run and die before the first byte of its
record); with an `unfinished` or `failed` line it is a barrier, unfinished, and no id is in doubt.
Any unfinished, dispatch_unknown or never_dispatched id: not complete. The never_dispatched ids of a range are its
tail, written as never_dispatched_first (2.4: one interval, null when none); not_done lists the other four states.
EXIT CODES: 0 as asked (the slot ended; or the STOP file, then without `ended`); 2 wrong call; 3 the slot's lock
is held; 4 the header, a schedule, a RESUME, the fence, the manifest, the identity, the journal or a piece cannot
be trusted; 5 start-up refused; 6 three engine failures in a row; 7 a binding refused; 8 the clock HOLD or the
watch's ALARM (a hold found while the worker starts: before the epoch line, nothing written). Never a traceback.
PLANTS (only with --rehearsal; named in worker.log), at the game with that counter: no_newgame, writeminply9,
swap_final, mvoes, cut2, kill_engine, bad_row (one row out of its shape: the record module refuses, the game fails);
2.9, switched on once the engine searches that game, the driver's cutoff taken before (as before a suspension):
clock_suspend (UTC and the boot-time clock 30 s past D, the steady clock stood still), clock_forward (UTC alone
60 s past D: the hold), clock_back (UTC an hour back: D comes by the other clocks), watch_nostop (the watch's stop
does nothing: the native process is found alive at D, the alarm "still there"), watch_lategone (after the stop the
watch's look for the exit answers only once D has come: the exit is confirmed after D, the alarm "gone after D").
SECOND READ (Astra 215331Z, Neon 223800Z 1 and 231830Z, Fable FABLE-2311-PDEATHSIG-ANSWER): a range seal that
exists is judged as a piece seal is (an earlier start's is kept, anything else stops); the RESUME chain is walked
at every start with old_boot_id linked (as guard v2 R7); a slot folder without IDENTITY.json may hold only LOCK
and IDENTITY.json.tmp; the lease times are read; FENCE.json is the guard's record; on Linux the engine's handle
is a pidfd and the engine is started through run/bind_exec.py (PR_SET_PDEATHSIG), from the main thread only;
worker.log names each engine by its number AND its creation time.
VERSION 3 (Opus 24 Nov, my bug hunts' targets 78 and 79; known answers first: KNOWN_ANSWERS_worker_v3_by_opus.md
on the PC): the manifest's option lines and selfgame_line must be texts of printable ASCII, the launcher's TEXT
rule (Stop 4 naming the rule; a carriage return or a tab inside a line was bound by the hash and SENT as it was);
and more than one game record beyond the journal's end of the open piece holds (Stop 4, nothing cut): a crash
leaves at most one, so the journal lost lines, and the later games' dispatch would have gone without a word.
25 Nov (W1, Fable's FABLE-2511-READ-WORKER, her repair): a start that died between its range seals and its `ended`
line left a slot no later start could end (the finalizer's seal holds its id in doubt, the kept one, written by the
start that knew, does not: Stop 4 at every start). range_seal() now keeps such a seal when it is the fresh one
without the doubt; test_worker.py V24b to V24d.
v17 (Opus 26 Nov; tmp/opus_scratch/v17/KNOWN_ANSWERS_v17_server_by_opus.md W1 to W6, read by Fable): every done and
noselfgame line also carries t0_ms (the earliest of the three clocks at the reading of the judgement that preceded the
game's reservation, clockwatch.Bounds.earliest_ms, the guard's CLOCK.json rule) and ms (the steady clock from that
reading to right before the line's write). The replay refuses a game line without them or with values outside W4's.
The pieces, piece seals and range seals are unchanged. Rehearsal plant clock_ahead: UTC alone an hour ahead.
NOT HERE: the end line's count rules (rows, moves, searches by reason) are home's (2.2); whether the clock can be
trusted after a restart is the boot guard's (1.3); the wire copies (0) are the packer's.
"""
import argparse
import bisect
import calendar
import collections
import hashlib
import json
import math
import os
import re
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import record  # noqa: E402
from uciproc import Engine, EngineError, EngineRefused  # noqa: E402
import clockwatch  # noqa: E402

CLOCK_PLANTS = ("clock_suspend", "clock_forward", "clock_back", "clock_ahead")   # 2.9: only the readers' values change
T0_MS_MIN, T0_MS_MAX, MS_MAX = 1_700_000_000_000, 4_100_000_000_000, 86_400_000      # v17 W4 (clock.py's M4 window)


def times_ok(r) -> bool:
    """v17 W4: a game line's t0_ms and ms are ints (never bool); t0_ms lies in M4's window of UTC milliseconds, ms in 0
    to one day."""
    return (type(r["t0_ms"]) is int and T0_MS_MIN <= r["t0_ms"] <= T0_MS_MAX
            and type(r["ms"]) is int and 0 <= r["ms"] <= MS_MAX)



WATCH_PLANTS = CLOCK_PLANTS + ("watch_nostop", "watch_lategone")
PLANTS = ("no_newgame", "writeminply9", "swap_final", "mvoes", "cut2", "kill_engine", "bad_row") + WATCH_PLANTS
ALLOWANCE_S = 2.0               # 2.9: the stop allowance, the editor's choice until it is measured on the server
HEX64 = re.compile(r"[0-9a-f]{64}")
PRINTABLE = bytes(range(0x20, 0x7f))
TEXT = re.compile(r"[\x20-\x7e]+")             # the launcher's text rule (version 3, target 78)
FINAL = ("done", "noselfgame", "refused", "unfinished")
PASSED = ("done", "noselfgame", "refused")          # 2.6: the only states the serial dispatcher can have passed
MODES = ("play", "seal_only")                      # 2.7: the epoch line's mode
STATES = ("dispatch_unknown", "done", "never_dispatched", "noselfgame", "refused", "unfinished")
NOT_COMPLETE = ("dispatch_unknown", "never_dispatched", "unfinished")      # any of them: the range is not complete
HEADER_KEYS = ("schema", "run", "lease_start_utc", "lease_end_utc", "hard_cutoff_utc", "boot_id", "instance",
               "package", "engine_sha256", "net_sha256", "options_sha256", "game_line", "opening_rule", "slots",
               "piece_games", "pilot_ranges")
FENCE_KEYS = ["at_utc", "cutoff_utc", "run_fingerprint", "schema", "why"]     # as both guards write it (2.3)
SCHEDULE_KEYS = ["cutoff_utc", "dispatch_end_utc", "evidence", "n", "prev", "ranges", "run_fingerprint", "schema"]
ROW_KEYS = ["first", "last", "round", "schedule", "short", "slot"]
G = collections.namedtuple("G", "counter gid state bind rows end")


class Stop(Exception):
    """The worker cannot go on; .code is its exit code."""

    def __init__(self, code: int, text: str):
        super().__init__(text)
        self.code = code


class StartRefused(RuntimeError):
    pass


class BindingRefused(RuntimeError):
    pass


# ---- records and durable writes (FORMATS 0) ------------------------------------------------------------------
def canon(obj) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False) + "\n").encode("ascii")


def _pairs(pairs):
    d = {}
    for k, v in pairs:
        if k in d:
            raise ValueError(f"the key {k!r} stands twice")
        d[k] = v
    return d


def _not_int(text):
    raise ValueError(f"a number that is not an integer: {text}")


def parse_canon(data: bytes, what: str):
    if not data.endswith(b"\n") or data[:-1].translate(None, PRINTABLE):
        raise ValueError(f"{what}: a byte outside 0x20..0x7e, or no line end")
    try:
        obj = json.loads(data.decode("ascii"), object_pairs_hook=_pairs, parse_float=_not_int, parse_constant=_not_int)
    except ValueError as e:
        raise ValueError(f"{what}: not a canonical record ({e})") from None
    if canon(obj) != data:
        raise ValueError(f"{what}: not in canonical form (keys sorted, no spaces, one line end)")
    return obj


def read_canon(path: Path):
    try:
        return parse_canon(path.read_bytes(), path.name)
    except ValueError as e:
        raise Stop(4, str(e)) from None


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def fsync_dir(path: Path) -> None:
    """The folder's list of names to the disk, where the system has that (not on Windows)."""
    if os.name == "nt":
        return
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write_new(path: Path, data: bytes) -> None:
    with open(path, "xb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())


def create_only(path: Path, data: bytes) -> None:
    """An immutable file (FORMATS 0): a temporary name, flushed, linked to the final name, the folder flushed, the
    temporary name removed. The same bytes under the final name = done; other bytes = both kept and a stop."""
    if path.exists():
        if path.read_bytes() == data:
            return
        other = path.with_name(f"{path.name}.conflict.{sha256_bytes(data)[:12]}")
        if not other.exists():
            write_new(other, data)
        raise Stop(4, f"{path.name} exists with other bytes; the new ones are kept as {other.name}")
    tmp = path.with_name(path.name + ".tmp")
    if tmp.exists():
        tmp.unlink()                                    # this writer's own scratch name, left by a crash
    write_new(tmp, data)
    try:
        os.link(tmp, path)
    except FileExistsError:
        os.unlink(tmp)
        return create_only(path, data)
    fsync_dir(path.parent)
    os.unlink(tmp)
    fsync_dir(path.parent)


def move_create_only(src: Path, dst: Path) -> None:
    if dst.exists():
        if dst.read_bytes() != src.read_bytes():
            raise Stop(4, f"{dst.parent.name}/{dst.name} exists with other bytes than {src.parent.name}/{src.name}; "
                          f"both are kept")
    else:
        os.link(src, dst)
        fsync_dir(dst.parent)
    os.unlink(src)
    fsync_dir(src.parent)


def utc(text, what: str) -> int:
    """Seconds of a UTC time written YYYY-MM-DDTHH:MM:SSZ; a time that does not exist (30 November + 1, hour 24,
    minute 60) is refused: written back from its seconds it must be the same text (Fable 14:13, B)."""
    m = re.fullmatch(r"([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})Z",
                     text if isinstance(text, str) else "")
    t = None
    try:
        if m:
            t = calendar.timegm(tuple(int(x) for x in m.groups()))
            if time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t)) != text:
                t = None
    except (ValueError, OSError, OverflowError):             # month 0 or 13, year 0, a time before 1970 on Windows
        t = None
    if t is None:
        raise Stop(4, f"{what}: not an existing UTC time YYYY-MM-DDTHH:MM:SSZ: {str(text)[:40]}")
    return t


def same(v, want) -> bool:
    """v equals want and has its type (a bool is never an int here)."""
    return type(v) is type(want) and v == want


def created_of(pid: int):
    """The creation time of process `pid` (Windows: GetProcessTimes through a handle; Linux: /proc stat field 22),
    or None. It names that process and no other only while the caller holds it (its handle, or the child not
    reaped): the worker writes it for its own engine, which it holds."""
    if os.name == "nt":
        import ctypes
        k = ctypes.WinDLL("kernel32", use_last_error=True)
        k.OpenProcess.restype = ctypes.c_void_p
        h = k.OpenProcess(0x1000, False, int(pid))
        if not h:
            return None
        t = [ctypes.c_ulonglong() for _ in range(4)]
        try:
            return t[0].value if k.GetProcessTimes(ctypes.c_void_p(h), *[ctypes.byref(x) for x in t]) else None
        finally:
            k.CloseHandle(ctypes.c_void_p(h))
    try:
        with open(f"/proc/{int(pid)}/stat", "rb") as f:
            s = f.read()
        return int(s[s.rfind(b")") + 2:].split()[19])
    except (OSError, ValueError, IndexError):
        return None


def boot_id() -> str:
    p = Path("/proc/sys/kernel/random/boot_id")
    return p.read_text(encoding="ascii").strip() if p.exists() else "none:" + os.name


def check_rows(rows, slots, n: int, what: str) -> list:
    """Range rows (1.2): one row a slot and round, the counters of a slot disjoint and rising with the round."""
    if not isinstance(rows, list):
        raise Stop(4, f"{what}: the ranges are not a list")
    by_slot: dict = {}
    for r in rows:
        if not (isinstance(r, dict) and sorted(r) == ROW_KEYS
                and all(type(r[k]) is int for k in ("first", "last", "round", "schedule", "slot"))
                and type(r["short"]) is bool and r["slot"] in slots and 1 <= r["round"] <= 9999
                and 0 <= r["schedule"] <= n and 1 <= r["first"] <= r["last"] <= 99999999):
            raise Stop(4, f"{what}: a range row that is not 1.2's: {str(r)[:160]}")
        by_slot.setdefault(r["slot"], []).append(r)
    for k, rs in by_slot.items():
        rs.sort(key=lambda r: r["round"])
        for x, y in zip(rs, rs[1:]):
            if y["round"] == x["round"] or y["first"] <= x["last"]:
                raise Stop(4, f"{what}: slot {k} has two rows of one round, or counters that do not rise with the round")
    return rows


def opening_index(root_seed: str, gid: str, ply: int, n: int) -> int:
    h = hashlib.sha256(f"{root_seed}|{gid}|{ply}".encode("ascii")).digest()
    return int.from_bytes(h[:8], "big") % n


class SlotLock:
    """The slot's folder is locked for the life of the worker (1.4)."""

    def __init__(self, folder: Path):
        self.f = open(folder / "LOCK", "a+b")
        try:
            if os.name == "nt":
                import msvcrt
                self.f.seek(0)
                msvcrt.locking(self.f.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.f.close()
            raise Stop(3, f"another worker holds the lock of {folder.name}") from None

    def release(self) -> None:
        if self.f.closed:
            return
        if os.name == "nt":
            import msvcrt
            try:
                self.f.seek(0)
                msvcrt.locking(self.f.fileno(), msvcrt.LK_UNLCK, 1)
            except OSError:
                pass
        self.f.close()                                  # closing releases a flock


# ---- the worker --------------------------------------------------------------------------------------------------
class Worker:
    def __init__(self, a):
        self.a = a
        self.plant = (None, 0)
        self.plant_used = False
        if a.plant:
            kind, _, idx = a.plant.partition(":")
            if not a.rehearsal or kind not in PLANTS or not idx.isdigit():
                raise Stop(2, f"--plant <{' | '.join(PLANTS)}>:<counter>, and only together with --rehearsal")
            self.plant = (kind, int(idx))
        self.off = [0.0, 0.0]           # the clock plants: seconds added to what UTC and the boot-time clock read
        clocks = clockwatch.Clocks()
        if self.plant[0] in CLOCK_PLANTS:               # the plants replace the readers, nothing else; where the
            boot = clocks.boot or time.monotonic        # system has no boot-time clock it is emulated by the steady one
            clocks = clockwatch.Clocks(utc=lambda: time.time() + self.off[0], boot=lambda: boot() + self.off[1])
        self.B = clockwatch.Bounds(clocks)              # 2.7: the anchor, the three clocks read together at the start
        self.reading = None                             # v17 W2: the reading of the newest clock_state() call
        self.root = Path(a.root)
        hb = (self.root / "RUN.json").read_bytes()
        self.run_fp = sha256_bytes(hb)
        try:
            self.h = parse_canon(hb, "RUN.json")
        except ValueError as e:
            raise Stop(4, str(e)) from None
        self.slot = a.slot
        self.name = f"w{a.slot:03d}"
        self.dir = self.root / self.name
        self.genesis = f"genesis:{self.run_fp}:{self.name}"
        self.check_header()
        self.read_manifest()
        self.eng = None
        self.log = None
        self.lock = None
        self.epoch, self.last_index, self.last_seal = 0, -1, self.genesis
        self.open_index, self.open_games = 0, []
        self.states: dict = {}           # counter -> its last state in the journal
        self.piece_of: dict = {}         # counter -> the index of the piece that holds it
        self.seal_sha: dict = {}         # index -> sha256 of its seal file
        self.piece_sums: dict = {}       # index -> (games, rows, raw bytes) of a closed piece
        self.boot_first: dict = {}       # boot id -> (resume, last_index, last_seal) of its FIRST epoch line (2.4)
        self.in_doubt = None             # the one counter a finalizer after an earlier start cannot call (2.4)
        self.low, self.sched_n = 0, -1   # next_counter() starts at self.low: every counter below it is final
        self.ended = False
        self.sched_files = None          # 2.6: the bytes of every schedule, each read from disk ONCE
        self.held = None                 # (rows, cutoff, dispatch end, n, bytes, cutoff text) of the schedule in force
        self.mode = None                 # 2.7: play or seal_only, decided before the epoch line
        self.play_epochs = 0             # 2.7: epoch lines of EARLIER starts whose mode is play
        self.ph = None                   # 2.9: the handle of the engine's native process (clockwatch.ProcHandle)
        self.w = None                    # 2.9: the watch of the last wait for the engine
        self.top = 0                     # the highest counter this start reserved: a game in flight has started
        self.sched_stop = None           # a schedule that could not be followed: Stop 4 at the next reservation

    # ---- inputs ----------------------------------------------------------------------------------------------
    def check_header(self) -> None:
        h, a = self.h, self.a
        miss = [k for k in HEADER_KEYS if k not in h]
        if miss:
            raise Stop(4, f"RUN.json lacks {', '.join(miss)}")
        if h["schema"] != 2 or not isinstance(h["run"], str) or not re.fullmatch(r"[a-z0-9]{1,32}", h["run"]):
            raise Stop(4, "RUN.json: schema 2 and a run name of 1 to 32 letters a-z or digits")
        for k in ("engine_sha256", "net_sha256", "options_sha256", "package"):
            if not isinstance(h[k], str) or not HEX64.fullmatch(h[k]):
                raise Stop(4, f"RUN.json: {k} is not a sha256")
        if not isinstance(h["boot_id"], str) or not isinstance(h["game_line"], str):
            raise Stop(4, "RUN.json: boot_id and game_line are texts")
        slots = h["slots"]
        if not (isinstance(slots, list) and slots and all(type(s) is int and 0 <= s <= 999 for s in slots)
                and all(x < y for x, y in zip(slots, slots[1:]))):
            raise Stop(4, "RUN.json: slots is a rising list of integers 0 to 999")
        if a.slot not in slots:
            raise Stop(4, f"slot {a.slot} is not one of the run's slots")
        if type(h["piece_games"]) is not int or h["piece_games"] < 1:
            raise Stop(4, "RUN.json: piece_games is an integer >= 1")
        self.hard_cutoff = utc(h["hard_cutoff_utc"], "RUN.json hard_cutoff_utc")
        start, end = utc(h["lease_start_utc"], "RUN.json lease_start_utc"), utc(h["lease_end_utc"],
                                                                             "RUN.json lease_end_utc")
        if not start < end:                             # the launcher's own rule (run/launcher.py)
            raise Stop(4, "RUN.json: lease_start_utc is not before lease_end_utc")
        if self.hard_cutoff > end:                      # Neon 223800Z 1: D lies inside the lease
            raise Stop(4, "RUN.json: hard_cutoff_utc lies after lease_end_utc")
        rule, self.fixed = h["opening_rule"], None
        if isinstance(rule, dict) and sorted(rule) == ["kind", "plies", "root_seed"] and rule["kind"] == "seed":
            if type(rule["plies"]) is not int or not 0 <= rule["plies"] <= 64 or not isinstance(rule["root_seed"], str) \
                    or not re.fullmatch(r"[A-Za-z0-9_]{1,64}", rule["root_seed"]):
                raise Stop(4, "RUN.json: the seed rule needs plies 0 to 64 and a root_seed of letters, digits and _")
            if a.openings:
                raise Stop(2, "an openings file is given and the run's opening rule is seed")
        elif isinstance(rule, dict) and sorted(rule) == ["count", "kind", "sha256"] and rule["kind"] == "list":
            if not a.openings:
                raise Stop(2, "the run's opening rule is a list and no --openings file is given")
            data = Path(a.openings).read_bytes()
            if sha256_bytes(data) != rule["sha256"]:
                raise Stop(4, "the openings file is not the one RUN.json names (opening_rule sha256)")
            self.fixed = [ln.split(" ") if ln else [] for ln in data.decode("ascii").split("\n")[:-1]]
            if not data.endswith(b"\n") or len(self.fixed) != rule["count"] or rule["count"] < 1 or not all(
                    all(record.MOVE.fullmatch(m) for m in o) for o in self.fixed):
                raise Stop(4, "the openings file does not hold `count` lines of moves, each ended by LF")
        else:
            raise Stop(4, "RUN.json: opening_rule is {kind seed, plies, root_seed} or {kind list, sha256, count}")
        check_rows(h["pilot_ranges"], slots, 0, "RUN.json pilot_ranges")

    def read_manifest(self) -> None:
        man = json.loads(Path(self.a.manifest).read_bytes().decode("ascii"))
        opts, line = man["options"], man["selfgame_line"]
        if not (isinstance(opts, list) and all(isinstance(ln, str) and TEXT.fullmatch(ln) for ln in opts)):
            raise Stop(4, "the manifest's option lines are not all texts of printable ASCII (0x20 to 0x7e, no line "
                          "end inside)")
        if not (isinstance(line, str) and TEXT.fullmatch(line)):
            raise Stop(4, "the manifest's selfgame_line is not a text of printable ASCII")
        self.options = list(man["options"])
        if sha256_bytes("".join(ln + "\n" for ln in self.options).encode("ascii")) != self.h["options_sha256"]:
            raise Stop(4, "the manifest's option lines are not the run's (options_sha256)")
        if man["selfgame_line"] != self.h["game_line"]:
            raise Stop(4, "the manifest's game line is not the run's game_line")
        if man["net_sha256"] != self.h["net_sha256"]:
            raise Stop(4, "the manifest's net is not the run's net_sha256")
        self.selfgame = man["selfgame_line"]
        self.probes = list(man["startup_probes"])
        self.depth = int(man["startup_depth"])
        self.net_want = (int(man["net_bytes"]), man["net_sha256"])
        self.known = json.loads(Path(self.a.known_startup).read_text(encoding="ascii"))
        self.net = str(Path(self.a.net).resolve()).replace("\\", "/")

    def load_schedules(self, start: bool = False) -> None:
        """FORMATS 1.2 (2.6, 2.7; Astra 153200Z, 153602Z). At a start every schedule file on disk is read ONCE and its
        bytes kept (the names 1 to N in the grammar), and the chain is walked from schedule 0, the header's pilot
        ranges; the start's second walk, once the journal says which ranges have started, uses the kept bytes.
        Before every reservation only the NEXT number is looked for and, while one is there, it is verified against
        the one held and applied, again until the next number is absent: only the highest valid schedule
        authorizes a game (numbers 2 and 3 both new and 3's dispatch end past: none is started). A schedule that
        does not follow the one held never authorizes work: Stop 4."""
        before = self.sched_n
        if start:
            if self.sched_files is None:
                names = [p.name for p in self.root.glob("SCHEDULE.*.json")]
                if any(not re.fullmatch(r"SCHEDULE\.[1-9][0-9]{0,2}\.json", x) for x in names):
                    raise Stop(4, f"a schedule file name outside the grammar: {sorted(names)[:5]}")
                files = []
                for k in range(1, len(names) + 1):
                    p = self.root / f"SCHEDULE.{k}.json"
                    if not p.exists():
                        raise Stop(4, f"there are {len(names)} schedules and SCHEDULE.{k}.json is not one of them")
                    files.append(p.read_bytes())
                self.sched_files = files
            self.held = (self.h["pilot_ranges"], self.hard_cutoff, self.hard_cutoff, 0, b"", self.h["hard_cutoff_utc"])
            for k, data in enumerate(self.sched_files, 1):
                self.held = self.follow(k, data)
        else:
            self.follow_next()
        rows, cut, disp, n, _, d_text = self.held
        if n != before:
            self.low = 0                                # other ranges: next_counter() walks from the start once
        self.sched_n, self.d_text = n, d_text           # d_text: the D in force as written (a fence must copy it)
        self.my_rows = sorted((r for r in rows if r["slot"] == self.slot), key=lambda r: r["round"])
        self.B.set("cutoff", cut)                       # 2.9: never later (the earlier bound in force is kept)
        self.B.set("dispatch_end", min(disp, cut))

    def follow_next(self) -> None:
        """2.7: while the NEXT schedule number is there, verify it against the one held and apply it; its bounds go to
        the clocks at once (2.9). The worker's own read, in the main thread only (the watch reads with refresh()).
        A schedule that cannot be followed is remembered, never read again, and stops the worker at the next
        reservation."""
        if self.sched_stop is not None:
            raise self.sched_stop
        try:
            while self.held[3] < 999:                   # the grammar ends at 999
                try:
                    data = (self.root / f"SCHEDULE.{self.held[3] + 1}.json").read_bytes()
                except FileNotFoundError:
                    break
                self.held = self.follow(self.held[3] + 1, data)
                self.sched_files.append(data)
                self.B.set("cutoff", self.held[1])
                self.B.set("dispatch_end", min(self.held[2], self.held[1]))
        except Stop as e:
            self.sched_stop = e
            raise

    def follow(self, k: int, data: bytes, held=None, started_to=None) -> tuple:
        """Schedule k checked against the one held: canonical, schema 2, n = k, this run's, prev = sha256 of the held
        one's bytes (`first` for 1), its bounds never later, a STARTED range unchanged (counters are reserved in
        rising order, the lowest first: the journal's highest counter says which have started), any other range
        kept or shortened. Returns the new held tuple (rows, cutoff, dispatch end, n, bytes, cutoff text). `held` and
        `started_to` are refresh()'s snapshot; by default the worker's own."""
        rows, cut, disp, _, prev_bytes, _ = self.held if held is None else held
        name = f"SCHEDULE.{k}.json"
        try:
            s = parse_canon(data, name)
        except ValueError as e:
            raise Stop(4, str(e)) from None
        if not isinstance(s, dict) or sorted(s) != SCHEDULE_KEYS or s["schema"] != 2 or s["n"] != k \
                or s["run_fingerprint"] != self.run_fp \
                or s["prev"] != ("first" if k == 1 else sha256_bytes(prev_bytes)) \
                or not HEX64.fullmatch(str(s["evidence"])):
            raise Stop(4, f"{name}: not schedule {k} of this run (schema, n, run_fingerprint, prev, evidence)")
        c2, d2 = utc(s["cutoff_utc"], name), utc(s["dispatch_end_utc"], name)
        if not d2 <= c2 <= cut or d2 > disp:
            raise Stop(4, f"{name}: a cutoff or dispatch end later than the one before, or after its own cutoff")
        new_rows = check_rows(s["ranges"], self.h["slots"], k, name)
        if started_to is None:
            started_to = max(max(self.states, default=0), self.top)    # 2.9: the game in flight has started too
        now = {r["round"]: r for r in new_rows if r["slot"] == self.slot}
        for r in rows:
            if r["slot"] != self.slot:
                continue
            q = now.get(r["round"])
            if r["first"] <= started_to:
                if q != r:
                    raise Stop(4, f"{name}: the range of round {r['round']} of slot {self.slot} is changed after it "
                                  f"started")
            elif q is None or q["first"] != r["first"] or q["last"] > r["last"]:
                raise Stop(4, f"{name}: the range of round {r['round']} of slot {self.slot} is removed, moved or "
                              f"lengthened")
        return (new_rows, c2, d2, k, data, s["cutoff_utc"])

    def refresh(self) -> None:
        """2.9, the watch's refresh, in a thread of the watch's own that may still run after the watch has closed
        (clockwatch 2, reader_stalled): it only READS. The schedules after the one held at the watch's start
        (self.snap, that schedule and the highest counter started then, a tuple nobody changes) are verified as the
        worker's own read verifies them, and their bounds go to the clocks (Bounds.set is locked and keeps the
        earlier). The worker's own read applies them before the next reservation; one that cannot be followed is
        left to it (it stops the worker there)."""
        held, started_to = self.snap
        while held[3] < 999:                            # the grammar ends at 999
            try:
                data = (self.root / f"SCHEDULE.{held[3] + 1}.json").read_bytes()
            except FileNotFoundError:
                return
            try:
                held = self.follow(held[3] + 1, data, held, started_to)
            except Stop:
                return
            self.B.set("cutoff", held[1])
            self.B.set("dispatch_end", min(held[2], held[1]))

    def admitting_resume(self):
        """(name, sha256, record) of the HIGHEST RESUME record when it admits this boot; None when there is no RESUME
        and this boot is the header's (FORMATS 1.3, 2.4). Walked at EVERY start, on the header's boot too, as guard
        v2's R7 walks it (Neon 223800Z 1): every RESUME from 1 to n is there, canonical, schema 2, this run's, n = its
        name, prev = sha256 of RESUME n - 1 (`first` for 1), old_boot_id = the header's boot for 1 and RESUME n - 1's
        new_boot_id after it, new_boot_id a text; the highest names this boot with instance_provable true. Anything
        else: Stop 4, nothing changed."""
        names = [p.name for p in self.root.glob("RESUME.*.json")]
        if any(not re.fullmatch(r"RESUME\.[1-9][0-9]{0,2}\.json", x) for x in names):
            raise Stop(4, f"a RESUME file name outside the grammar: {sorted(names)[:5]}")
        top, prev, boot = None, b"", self.h["boot_id"]
        for k in range(1, len(names) + 1):
            p = self.root / f"RESUME.{k}.json"
            if not p.exists():
                raise Stop(4, f"there are {len(names)} RESUME files and RESUME.{k}.json is not one of them")
            data = p.read_bytes()
            try:
                r = parse_canon(data, p.name)
            except ValueError as e:
                raise Stop(4, str(e)) from None
            if not isinstance(r, dict) or not same(r.get("schema"), 2) or not same(r.get("n"), k) \
                    or r.get("run_fingerprint") != self.run_fp \
                    or r.get("prev") != ("first" if k == 1 else sha256_bytes(prev)) \
                    or r.get("old_boot_id") != boot or not isinstance(r.get("new_boot_id"), str):
                raise Stop(4, f"{p.name}: not RESUME {k} of this run's chain (schema, n, run_fingerprint, prev, "
                              f"old_boot_id, new_boot_id)")
            top, prev, boot = (p.name, sha256_bytes(data), r), data, r["new_boot_id"]
        if boot != self.boot:
            raise Stop(4, (f"this machine's boot id ({self.boot}) is not the header's ({self.h['boot_id']}) and no "
                           f"RESUME record admits it; nothing was changed") if top is None else
                          (f"this machine's boot id ({self.boot}) is not the one the highest RESUME names "
                           f"({boot[:40]}): no RESUME record admits it; nothing was changed"))
        if top is not None and top[2].get("instance_provable") is not True:
            raise Stop(4, f"{top[0]} admits this boot without instance_provable true: held for a person")
        return top

    def fenced(self) -> bool:
        """FENCE.json of this run whose cutoff_utc is the D in force copied (1.8.1; 2.4: in the pilot, before any
        schedule, RUN.json's hard_cutoff_utc): it stops reservations; any other fence stops the worker."""
        p = self.root / "FENCE.json"
        if not p.exists():
            return False
        f = read_canon(p)
        if not isinstance(f, dict) or sorted(f) != FENCE_KEYS or not same(f["schema"], 2):
            raise Stop(4, "FENCE.json is not a fence record as the guard writes it (at_utc, cutoff_utc, "
                          "run_fingerprint, schema 2, why)")
        if f.get("run_fingerprint") != self.run_fp:
            raise Stop(4, "FENCE.json is not this run's")
        if f.get("cutoff_utc") != self.d_text:
            raise Stop(4, f"FENCE.json's cutoff_utc {str(f.get('cutoff_utc'))[:40]} is not the D in force "
                          f"({self.d_text}, schedule {self.sched_n}): a fence copies it, never a new time")
        return True

    # ---- the clocks (FORMATS 2.7, 2.9; run/clockwatch.py) ------------------------------------------------------
    def clock_state(self) -> str:
        """The ONE judgement of the bounds by all clocks, before every reservation and after every wait for the engine
        (a success and an error alike): "hold" (UTC alone says a bound has come and stands more than 10 s ahead of
        the anchor plus the boot-time clock), "cutoff" (D has come), "dispatch_end" (no reservation) or "play". The
        latch (a bound once passed stays passed) is clockwatch.Bounds'; the plants replace the readers, nothing else."""
        r = self.B.clocks.read()
        self.reading = r                                # v17 W2: the reading a reservation's t0_ms is taken from
        vd = self.B.judge("dispatch_end", reading=r)[0]
        vc = self.B.judge("cutoff", reading=r)[0]
        if clockwatch.HOLD in (vd, vc):
            return "hold"
        return "cutoff" if vc == clockwatch.COME else "dispatch_end" if vd == clockwatch.COME else "play"

    def cut(self) -> float:
        """The steady cutoff of ONE wait, computed afresh: now plus the least time left to D by any clock (2.9)."""
        return self.B.steady_cutoff("cutoff")

    def hold_text(self) -> str:
        return ("ALARM clock: the hold (UTC alone says a bound has come and stands more than 10 s ahead of the anchor "
                f"plus the boot-time clock): anchor {clockwatch.reading_text(self.B.anchor)}, now "
                f"{clockwatch.reading_text(self.B.clocks.read())}; nothing more is reserved; exit 8")

    def no_hold(self, kept: str) -> None:
        """A hold found while the worker starts (a clock that jumped then): exit 8 before the epoch line."""
        if self.clock_state() == "hold":
            raise Stop(8, f"{self.hold_text()}; {kept}")

    # ---- the slot, its lock and its journal --------------------------------------------------------------------
    def claim_slot(self) -> None:
        ident = canon({"run": self.h["run"], "run_fingerprint": self.run_fp, "schema": 2, "slot": self.slot})
        if self.dir.exists():
            self.check_identity(ident)
        else:
            self.dir.mkdir()
            fsync_dir(self.root)
        self.lock = SlotLock(self.dir)
        self.check_identity(ident)                      # again under the lock: another first worker may have won
        if not (self.dir / "IDENTITY.json").exists():
            create_only(self.dir / "IDENTITY.json", ident)
        for sub in ("open", "closed"):
            (self.dir / sub).mkdir(exist_ok=True)
        (self.root / "ranges").mkdir(exist_ok=True)
        self.log = open(self.dir / "worker.log", "a", encoding="ascii", errors="backslashreplace", buffering=1)

    def check_identity(self, ident: bytes) -> None:
        p = self.dir / "IDENTITY.json"
        if not p.exists():                              # only what claim_slot leaves before it (Neon 223800Z 1)
            if not self.dir.exists():                   # W10: the boot guard reads a slot never started
                return
            other = sorted(x.name for x in self.dir.iterdir() if x.name not in ("LOCK", "IDENTITY.json.tmp"))
            if other:
                raise Stop(4, f"{self.name} holds {', '.join(other[:5])} and no IDENTITY.json: not this run's slot; "
                              f"nothing was changed")
            return
        if p.read_bytes() != ident:
            raise Stop(4, f"{self.name}/IDENTITY.json belongs to another run or slot; nothing was changed")

    def say(self, text: str) -> None:
        if self.log is not None:
            self.log.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {text}\n")

    def append(self, obj) -> None:
        j = self.dir / "journal.txt"
        new = not j.exists()
        with open(j, "ab") as f:
            f.write(canon(obj))
            f.flush()
            os.fsync(f.fileno())
        if new:
            fsync_dir(self.dir)

    def gid(self, counter: int) -> str:
        return f"{self.h['run']}-{self.name}-g{counter:08d}"

    def counter_of(self, gid) -> int:
        m = re.fullmatch(re.escape(f"{self.h['run']}-{self.name}-g") + r"([0-9]{8})", gid if isinstance(gid, str) else "")
        if not m or int(m[1]) < 1:
            raise ValueError(f"the id {str(gid)[:60]} is not one of this run's and slot's")
        return int(m[1])

    def replay(self, r: dict, k: int) -> None:
        t = r.get("t")
        if k == 1 and t != "epoch":
            raise ValueError("journal line 1 is not an epoch line")
        if self.ended:
            raise ValueError(f"journal line {k} follows the `ended` line")
        if t == "epoch":
            want = {"t": "epoch", "epoch": self.epoch + 1, "prev_epoch": self.epoch, "last_index": self.last_index,
                    "last_seal": self.last_seal}
            if sorted(r) != ["boot_id", "epoch", "last_index", "last_seal", "mode", "prev_epoch", "resume", "t"] \
                    or {x: r[x] for x in want} != want or not isinstance(r["boot_id"], str) \
                    or not (r["resume"] is None or HEX64.fullmatch(str(r["resume"]))) or r["mode"] not in MODES:
                raise ValueError(f"journal line {k}: an epoch line that does not follow the lines before it")
            self.epoch += 1
            self.play_epochs += r["mode"] == "play"
            self.boot_first.setdefault(r["boot_id"], (r["resume"], r["last_index"], r["last_seal"]))
        elif t in ("done", "noselfgame"):
            extra = "rows" if t == "done" else "plies"
            last_end = self.open_games[-1].end if self.open_games else 0
            if sorted(r) != sorted(("t", "game", "index", "end", "bind", extra, "t0_ms", "ms")) \
                    or r["index"] != self.open_index or type(r["end"]) is not int or r["end"] <= last_end \
                    or type(r[extra]) is not int or r[extra] < 0 or not HEX64.fullmatch(str(r["bind"])) \
                    or not times_ok(r):
                raise ValueError(f"journal line {k}: a game line that does not follow the lines before it")
            c = self.counter_of(r["game"])
            if self.states.get(c) in FINAL or (self.open_games and c <= self.open_games[-1].counter):
                raise ValueError(f"journal line {k}: {r['game']} is final already or does not rise in its piece")
            self.open_games.append(G(c, r["game"], t, r["bind"], r.get("rows", 0), r["end"]))
            self.states[c], self.piece_of[c] = t, self.open_index
        elif t in ("failed", "refused", "unfinished"):
            if sorted(r) != ["game", "t", "why"] or not isinstance(r["why"], str):
                raise ValueError(f"journal line {k}: a {t} line that cannot be read")
            c = self.counter_of(r["game"])
            if self.states.get(c) in FINAL:
                raise ValueError(f"journal line {k}: {r['game']} has a final state already")
            self.states[c] = t
        elif t == "closed":
            seal = self.dir / "closed" / f"p{self.open_index:06d}.seal.json"
            if sorted(r) != ["index", "seal", "t"] or r["index"] != self.open_index or not self.open_games \
                    or not HEX64.fullmatch(str(r["seal"])) or not seal.exists() or file_sha256(seal) != r["seal"]:
                raise ValueError(f"journal line {k}: a closed line without its piece's games or without its seal file")
            s = parse_canon(seal.read_bytes(), seal.name)  # 2.4 (Astra 151303Z): every seal descends from the one before
            if not isinstance(s, dict) or s.get("run_fingerprint") != self.run_fp or s.get("slot") != self.slot \
                    or s.get("index") != self.open_index or s.get("prev_seal") != self.last_seal:
                raise ValueError(f"journal line {k}: {seal.name} does not descend from the seal before it (run, slot, "
                                 f"index, prev_seal)")
            self.note_closed(r["seal"])
        elif t == "ended":
            want = {"t": "ended", "epoch": self.epoch, "last_index": self.last_index, "last_seal": self.last_seal}
            if sorted(r) != ["epoch", "last_index", "last_seal", "t", "why"] or {x: r[x] for x in want} != want \
                    or r["why"] not in ("cutoff", "ranges done", "finalizer") or self.open_games:
                raise ValueError(f"journal line {k}: an ended line that does not follow the lines before it")
            self.ended = True
        else:
            raise ValueError(f"journal line {k}: a line of no known kind")

    def note_closed(self, sha: str) -> None:
        g = self.open_games
        self.seal_sha[self.open_index] = sha
        self.piece_sums[self.open_index] = (len(g), sum(x.rows for x in g), g[-1].end)
        self.last_index, self.last_seal = self.open_index, sha
        self.open_index, self.open_games = self.open_index + 1, []

    def read_journal(self) -> None:
        j = self.dir / "journal.txt"
        data = j.read_bytes() if j.exists() else b""
        cut = data.rfind(b"\n") + 1
        for k, ln in enumerate(data[:cut].split(b"\n")[:-1], 1):
            try:
                self.replay(parse_canon(ln + b"\n", f"journal line {k}"), k)
            except ValueError as e:
                raise Stop(4, f"{e}; the journal is kept as it is") from None
        self.drop = None
        if cut < len(data):
            want = self.open_games[-1].end if self.open_games else 0
            piece = self.piece_file()
            have = piece.stat().st_size if piece is not None else 0
            if have < want:
                raise Stop(4, f"the journal's last line is unfinished and the piece holds {have} bytes, not the {want} "
                              f"the line before it names; the journal is kept as it is")
            self.drop = (cut, data[cut:cut + 80], want)    # cut only after every check of this start (2.4)

    def drop_unfinished_line(self) -> None:
        """The unfinished last journal line read_journal found, cut off: after every check of the start, before
        its epoch line (2.4: a refused start changes nothing but its lock and IDENTITY.json)."""
        if self.drop is None:
            return
        cut, tail, want = self.drop
        with open(self.dir / "journal.txt", "r+b") as f:
            f.truncate(cut)
            f.flush()
            os.fsync(f.fileno())
        self.drop = None
        self.say(f"recover: dropped the unfinished last journal line {tail!r}; the piece holds the {want} bytes the "
                 f"line before it names")

    def piece_file(self):
        for sub in ("open", "closed"):
            p = self.dir / sub / f"p{self.open_index:06d}.raw"
            if p.exists():
                return p
        return None

    def check_piece(self, data: bytes, games: list, name: str) -> None:
        """The piece holds exactly the journal's games: ids, rows, and bindings computed again from the bytes."""
        try:
            got = [(g["id"], record.bind(self.run_fp, g["id"], g["opening"], g["sent"], g["rows"], g["end"]),
                    g["bind"], len(g["rows"])) for g in record.parse(data, self.run_fp)]
        except ValueError as e:
            raise Stop(4, f"{name} cannot be read as records: {e}") from None
        if got != [(g.gid, g.bind, g.bind, g.rows) for g in games] or len(data) != games[-1].end:
            raise Stop(4, f"{name} does not hold the journal's games (ids, bindings, rows, bytes)")

    def repair_open_piece(self) -> None:
        i = self.open_index
        op, cl = self.dir / "open" / f"p{i:06d}.raw", self.dir / "closed" / f"p{i:06d}.raw"
        want = self.open_games[-1].end if self.open_games else 0
        if op.exists() and cl.exists():                 # a crash inside the move: finished when the bytes are equal
            move_create_only(op, cl)
        if (self.dir / "closed" / f"p{i:06d}.seal.json").exists() and not cl.exists():
            raise Stop(4, f"p{i:06d} has a seal and its raw file is not in closed/")
        if op.exists():
            size = op.stat().st_size
            if size < want:
                raise Stop(4, f"the journal names {want} bytes in {op.name} and the file holds {size}")
            if size > want:
                with open(op, "rb") as f:
                    f.seek(want)
                    tail = f.read()
                records = sum(1 for ln in tail.split(b"\n") if ln.startswith(b"game "))
                if records > 1:                         # a crash leaves at most one (written, fsynced, then its line)
                    raise Stop(4, f"{op.name}: {records} game records lie beyond the journal's end ({want} bytes); a "
                                  f"crash leaves at most one, so the journal lost lines: nothing is cut")
                first = tail[:120].split(b"\n", 1)[0].split(b" ")
                try:                                    # the id judged by the record module, never by a pattern here
                    run, slot, c = record.id_parts(first[1].decode("ascii")) if first[0] == b"game" and len(first) > 1 \
                        else (None, None, None)
                except ValueError:
                    run = slot = c = None
                named = ""
                # reading 9 (a softer 1.8.3): bytes of a game beyond the journal's end are evidence of its dispatch; its
                # `failed` line, durable BEFORE the bytes go, has it played again or counted unfinished in its range
                if run == self.h["run"] and slot == self.slot and any(r["first"] <= c <= r["last"] for r in self.my_rows) \
                        and self.states.get(c) not in FINAL + ("failed",):
                    self.append({"t": "failed", "game": self.gid(c),
                                 "why": "its bytes lay beyond the journal's end and were cut at a restart"})
                    self.states[c], named = "failed", f"; {self.gid(c)} gets a failed line (evidence of its dispatch)"
                self.say(f"recover: {op.name} is {size} bytes and the journal ends at {want}: a game written but not "
                         f"journalled is cut off{named}")
                with open(op, "r+b") as f:
                    f.truncate(want)
                    f.flush()
                    os.fsync(f.fileno())
            if want:
                self.check_piece(op.read_bytes(), self.open_games, op.name)
        elif cl.exists():
            if not self.open_games:
                raise Stop(4, f"closed/{cl.name} exists and the journal names no game in it")
            self.say(f"recover: {cl.name} was moved to closed/ and its closed line is missing: the closing is finished")
            self.close_piece()
        elif want:
            raise Stop(4, f"the journal names {want} bytes in p{i:06d}.raw and the file is missing")

    # ---- pieces and ranges -------------------------------------------------------------------------------------
    def round_of(self, counter: int) -> int:
        for r in self.my_rows:
            if r["first"] <= counter <= r["last"]:
                return r["round"]
        raise Stop(4, f"{self.gid(counter)} lies in no range of the newest schedule")

    def kept_seal(self, path: Path, fresh: dict) -> bool:
        """A seal written before a crash, a piece's or a range's: True when it is `fresh` but for the epoch and the
        schedule that wrote it (an earlier start's: an int from 1 to this epoch, from 0 to this schedule); False
        when there is none; anything else Stop 4, the file kept as it is (Astra 215331Z, Neon 223800Z 1)."""
        if not path.exists():
            return False
        try:
            old = parse_canon(path.read_bytes(), path.name)
        except ValueError:
            old = None
        drop = ("epoch", "schedule")
        if not isinstance(old, dict) or {k: v for k, v in old.items() if k not in drop} != \
                {k: v for k, v in fresh.items() if k not in drop} \
                or type(old.get("epoch")) is not int or not 1 <= old["epoch"] <= self.epoch \
                or type(old.get("schedule")) is not int or not 0 <= old["schedule"] <= self.sched_n:
            raise Stop(4, f"{path.parent.name}/{path.name} exists and is not the seal of the journal's games and ids "
                          f"(another run's, other counts, or not readable); it is kept as it is")
        return True

    def close_piece(self) -> None:
        i, games = self.open_index, self.open_games
        if not games:
            return
        name = f"p{i:06d}.raw"
        src, dst = self.dir / "open" / name, self.dir / "closed" / name
        if src.exists():
            move_create_only(src, dst)
        data = dst.read_bytes()
        self.check_piece(data, games, name)
        ids = hashlib.sha256()
        for g in games:
            ids.update(f"{g.gid}\n{g.state}\n{g.bind}\n".encode("ascii"))
        fresh = {"schema": 2, "run": self.h["run"], "run_fingerprint": self.run_fp, "slot": self.slot,
                 "epoch": self.epoch, "index": i, "prev_seal": self.last_seal, "raw_sha256": sha256_bytes(data),
                 "raw_bytes": len(data), "games": len(games), "rows": sum(g.rows for g in games),
                 "first_game": games[0].gid, "last_game": games[-1].gid, "first_counter": games[0].counter,
                 "last_counter": games[-1].counter, "ids_digest": ids.hexdigest(),
                 "round": self.round_of(games[0].counter), "schedule": self.sched_n}
        seal = self.dir / "closed" / f"p{i:06d}.seal.json"
        if self.kept_seal(seal, fresh):                 # written before a crash: checked, never a second one
            sha = file_sha256(seal)
        else:
            body = canon(fresh)
            create_only(seal, body)
            sha = sha256_bytes(body)
        self.append({"t": "closed", "index": i, "seal": sha})
        self.note_closed(sha)

    def dispositions(self, row: dict):
        """Six counts, never_dispatched_first (2.4: the never-dispatched ids are the range's tail, one interval) and
        not_done: the ids of the four other states that are not done, in counter order."""
        counts = dict.fromkeys(STATES, 0)
        not_done, idx, nd_first = [], set(), None
        for c in range(row["first"], row["last"] + 1):
            s = self.states.get(c)
            if s is None:                               # 2.4: no evidence; the one id in doubt is not called either way
                s = "dispatch_unknown" if c == self.in_doubt else "never_dispatched"
            elif s == "failed":                         # evidence of a dispatch, never played again (2.3 reading 7)
                s = "unfinished"
            counts[s] += 1
            if s == "never_dispatched":
                nd_first = c if nd_first is None else nd_first
            elif s != "done":
                not_done.append([self.gid(c), s])
            if c in self.piece_of:
                idx.add(self.piece_of[c])
        if nd_first is not None and counts["never_dispatched"] != row["last"] - nd_first + 1:
            raise Stop(4, f"round {row['round']}: the never-dispatched ids are not the range's tail from "
                          f"{self.gid(nd_first)} (1.7 2.4); nothing more is written")
        return dict(counts, never_dispatched_first=nd_first, not_done=not_done), sorted(idx)

    def complete(self, row: dict) -> bool:
        counts = self.dispositions(row)[0]
        return not any(counts[s] for s in NOT_COMPLETE)

    def range_seal(self, row: dict) -> None:
        path = self.root / "ranges" / f"r{row['round']:04d}.{self.name}.seal.json"
        counts, idx = self.dispositions(row)
        sums = [self.piece_sums[i] for i in idx]
        fresh = {
            "schema": 2, "run": self.h["run"], "run_fingerprint": self.run_fp, "round": row["round"],
            "slot": self.slot, "epoch": self.epoch, "schedule": self.sched_n, "first": row["first"],
            "last": row["last"], "short": row["short"],
            "complete": not any(counts[s] for s in NOT_COMPLETE),
            "first_index": idx[0] if idx else -1,
            "first_prev_seal": (self.genesis if idx[0] == 0 else self.seal_sha[idx[0] - 1]) if idx else None,
            "through_index": idx[-1] if idx else -1, "through_seal": self.seal_sha[idx[-1]] if idx else None,
            "games": sum(s[0] for s in sums), "rows": sum(s[1] for s in sums), "raw_bytes": sum(s[2] for s in sums),
            "dispositions": counts}
        doubt = self.in_doubt
        if doubt is not None and row["first"] <= doubt <= row["last"] and path.exists():
            # W1 (Fable 25 Nov, FABLE-2511-READ-WORKER: her repair, read by Opus): a `play` start that ended its own day
            # wrote this seal and died before its `ended` line. It knew that the id this finalizer holds in doubt was
            # never dispatched, so its seal is kept when it is the fresh one WITHOUT the doubt; any other seal is
            # judged against the fresh one below, as before (Stop 4 when it is neither).
            self.in_doubt = None
            try:
                sure = self.dispositions(row)[0]
            finally:
                self.in_doubt = doubt
            try:
                if self.kept_seal(path, dict(fresh, dispositions=sure,
                                             complete=not any(sure[s] for s in NOT_COMPLETE))):
                    return
            except Stop:
                pass
        if not self.kept_seal(path, fresh):             # an earlier start's seal is kept; other bytes: Stop 4
            create_only(path, canon(fresh))

    def range_done(self, counter: int):
        """The range of `counter` when every id of it is final: the lowest open id lies beyond it (rising counters)."""
        for r in self.my_rows:
            if r["first"] <= counter <= r["last"]:
                nxt = self.next_counter()
                return r if nxt is None or nxt > r["last"] else None
        return None

    def next_counter(self):
        """The lowest counter of the slot's ranges, in round order, without a final state. A state never leaves
        FINAL, so the walk starts at self.low and never looks at a counter twice (Fable 14:13, C1); a new schedule
        sets self.low back to 0."""
        for r in self.my_rows:
            c = max(r["first"], self.low)
            while c <= r["last"] and self.states.get(c) in FINAL:
                c += 1
            if c <= r["last"]:
                self.low = c
                return c
        return None

    def first_not_passed(self):
        """2.6 / 2.7: the FIRST counter of the slot's ranges, in dispatch order (the ranges are disjoint and rise
        with the round, 2.1), that the serial dispatcher cannot have passed: only done, noselfgame and refused are
        skipped (an unfinished or failed id is a barrier). None when every counter is passed."""
        for r in self.my_rows:
            for c in range(r["first"], r["last"] + 1):
                if self.states.get(c) not in PASSED:
                    return c
        return None

    def check_serial_order(self) -> None:
        """2.7 (Neon 153430Z): every journalled id lies in a range of the slot, and none lies AFTER the first counter
        the serial dispatcher cannot have passed. Otherwise the journal contradicts the serial order: nothing is
        sealed over it and the slot is unreconciled (Stop 4 before the epoch line, the journal kept as it is)."""
        firsts = [r["first"] for r in self.my_rows]
        for c in sorted(self.states):
            i = bisect.bisect_right(firsts, c) - 1
            if i < 0 or c > self.my_rows[i]["last"]:
                raise Stop(4, f"the journal names {self.gid(c)}, which lies in no range of the slot: unreconciled, "
                              f"nothing is sealed over it; the journal is kept as it is")
        f = self.first_not_passed()
        late = [c for c in self.states if f is not None and c > f]
        if late:
            raise Stop(4, f"the journal names {self.gid(min(late))} after {self.gid(f)}, the first id the serial "
                          f"dispatcher cannot have passed (2.7): unreconciled, nothing is sealed over it; the journal "
                          f"is kept as it is")

    def hash_engine(self, kept: str) -> None:
        """1.3: the engine file is hashed at every start that may run it (2.7: a seal_only start hashes none)."""
        exe = Path(self.a.exe)
        if not exe.is_file() or file_sha256(exe) != self.h["engine_sha256"]:
            raise Stop(5, f"the engine file {exe.name} is missing or is not the run's engine_sha256; {kept}")

    # ---- the engine --------------------------------------------------------------------------------------------
    def kill_engine(self) -> None:
        if self.eng is not None:
            self.eng.kill()
            self.eng = None
        if self.ph is not None:                         # 2.9: the handle is closed after the process has ended
            self.ph.close()
            self.ph = None

    def watch_start(self):
        """2.9: a WATCH beside the waits for the engine that follow (clockwatch.Watch on the handle of the native
        process; its refresh, refresh(), gives a newer schedule's bounds to the clocks); kept in self.w for the
        judgement after the wait."""
        self.snap = (self.held, max(max(self.states, default=0), self.top))   # refresh()'s, never changed
        self.w = clockwatch.Watch(self.ph, self.B, allowance_s=ALLOWANCE_S, refresh=self.refresh)
        self.w.__enter__()
        return self.w

    def watch_end(self, w) -> None:
        """The wait is over: the watch is closed (one that has fired is waited for); its lines go to worker.log, and a
        refresh still running after the close is named (clockwatch 2: reader_stalled)."""
        w.close()
        for ln in w.lines():
            self.say(ln)
        if w.reader_stalled:
            self.say("watch reader_stalled=True: the schedule read was still running when the watch closed")

    def watched(self, fn, *args):
        """fn(*args) with every wait for the engine inside it under a watch."""
        w = self.watch_start()
        try:
            return fn(*args)
        finally:
            self.watch_end(w)

    def launcher(self):
        """W8 (Linux): the engine is started through run/bind_exec.py, which binds its life to this process
        (PR_SET_PDEATHSIG) and then becomes the engine under the same number; None on Windows."""
        if os.name == "nt":
            return None
        return [sys.executable, "-I", "-B", str(Path(__file__).resolve().parent / "bind_exec.py"), str(os.getpid())]

    def start_engine(self) -> None:
        if threading.current_thread() is not threading.main_thread():   # the binding follows the starting thread
            raise StartRefused("an engine is started only from the main thread (the parent-death binding follows "
                               "the thread that starts it)")
        self.kill_engine()
        exe = Path(self.a.exe)
        if not exe.is_file() or file_sha256(exe) != self.h["engine_sha256"]:
            raise StartRefused(f"the engine file {exe.name} is missing or is not the run's engine_sha256")
        net = Path(self.net)
        if not net.is_file() or net.stat().st_size != self.net_want[0] or file_sha256(net) != self.net_want[1]:
            raise StartRefused(f"the net file {net.name} is missing or is not the manifest's ({self.net_want[0]} bytes, "
                               f"sha256 {self.net_want[1][:16]}...)")
        self.eng = eng = Engine(self.a.exe, log=self.log if self.a.trace else None, launcher=self.launcher())
        self.ph = clockwatch.ProcHandle(eng.p)          # 2.9: right after the start, before any wait
        if os.name != "nt" and self.ph.how != "pidfd":  # Neon 223800Z 1: the stop at D through a pidfd
            raise StartRefused(f"the engine's handle is {self.ph.how!r}, not a pidfd: its stop at D is not exact")
        w = self.watch_start()                          # the whole start-up check under a watch
        try:
            have = eng.uci_options(60.0, cutoff=self.cut())
            names = []
            for ln in self.options:
                m = re.fullmatch(r"setoption name (\S+) value (\S+)", ln)
                if not m:
                    raise StartRefused(f"not an option line: {ln[:80]}")
                name, val = m[1], m[2]
                names.append(name)
                if name not in have:
                    raise StartRefused(f"the engine's uci list has no option {name}")
                o = have[name]
                if o["type"] == "spin":
                    if not re.fullmatch(r"-?\d+", val) or not int(o["min"]) <= int(val) <= int(o["max"]):
                        raise StartRefused(f"{name} = {val} is outside {o.get('min')} .. {o.get('max')}")
                elif o["type"] == "check" and val not in ("true", "false"):
                    raise StartRefused(f"{name} = {val} is neither true nor false")
                if name == "UseNNUE" and val != "true":
                    raise StartRefused("UseNNUE false together with a net file")
            if len(set(names)) != len(names):
                raise StartRefused("an option stands twice in the list")
            if "NNUEArchFile" not in names or "NNUEArch" not in names or names.index("NNUEArchFile") > names.index("NNUEArch"):
                raise StartRefused("the list does not hold NNUEArchFile before NNUEArch")
            if have.get("UseNNUE", {}).get("default") != "true" and "UseNNUE" not in names:
                raise StartRefused("UseNNUE is not on by default and the list does not switch it on")
            want_sent = [ln.replace("@@NET@@", self.net) for ln in self.options]
            mark = len(eng.sent)
            answers = []
            for ln in want_sent:
                answers += eng.command(ln, cutoff=self.cut())
            answers += eng.ready(cutoff=self.cut())
            if [s for s in eng.sent[mark:] if s != "isready"] != want_sent:
                raise StartRefused("the option lines that were sent are not the manifest's list")
            active = [ln for ln in answers if ln.startswith("info string NNUE v3 active:")]
            want_net = self.known["net"][0]
            m = re.search(r" hidden (\d+) king_buckets (\d+).* checksum ([0-9a-f]+) ", active[-1]) if active else None
            got_net = [int(m[1]), int(m[2]), m[3]] if m else None
            if got_net is None or got_net != want_net:
                raise StartRefused(f"the net that is active is {got_net}, the frozen one is {want_net}")
            evals = []
            for probe in self.probes:
                ev = [ln for ln in eng.command(probe, cutoff=self.cut()) + eng.command("eval", cutoff=self.cut())
                      if ln.startswith("info string eval ")]
                m = re.fullmatch(r"info string eval hce (-?\d+) nnue (-?\d+) total (-?\d+)", ev[0]) if len(ev) == 1 else None
                if not m or m[1] != "0" or m[2] != m[3]:
                    raise StartRefused(f"`eval` after `{probe[:50]}` does not read `hce 0 nnue X total X`: {ev}")
                evals.append([int(m[1]), int(m[2]), int(m[3])])
            if evals != self.known["eval"]:
                raise StartRefused(f"the probe positions evaluate to {evals}, the known answers are {self.known['eval']}")
            want = self.known["search"][0]                       # [depth, nodes, hashfull, bestmove]
            if want[0] != self.depth:
                raise StartRefused(f"the known answers are for depth {want[0]}, the manifest asks for depth {self.depth}")
            eng.command("ucinewgame", cutoff=self.cut())
            eng.command("position startpos", cutoff=self.cut())
            last, best = None, None
            for ln in eng.run(f"go depth {self.depth}", lambda s: s.startswith("bestmove"), 600, "the start-up search",
                              cutoff=self.cut()):
                if ln.startswith("info ") and " depth " in ln and " nodes " in ln and " hashfull " in ln:
                    t = ln.split()
                    last = [int(t[t.index("depth") + 1]), int(t[t.index("nodes") + 1]), int(t[t.index("hashfull") + 1])]
                if ln.startswith("bestmove"):
                    best = ln.split()[1]
            got = [*(last or [None, None, None]), best]
            if got != want:
                raise StartRefused(f"the start-up search gave {got}, the known answers are {want}")
            self.say(f"engine started: pid {eng.p.pid} created {created_of(eng.p.pid)}, engine sha256 {self.h['engine_sha256'][:16]}, net {got_net}, "
                     f"evals {evals}, search {got}")
            eng.sent.clear()
        except EngineRefused as e:
            if w.fired is not None:                     # the watch ended the process: judged by its reason
                raise
            raise StartRefused(str(e)) from None
        finally:
            self.watch_end(w)
        if w.fired is not None:                         # it fired after the start-up's last answer was read
            raise EngineError(f"the watch ended the engine at the end of its start-up ({w.fired})")

    # ---- one game ----------------------------------------------------------------------------------------------
    def legal_moves(self, moves: list) -> list:
        eng = self.eng
        assert eng is not None
        lines = eng.command(record.position_line(moves), cutoff=self.cut()) \
            + eng.command("go perft 1", cutoff=self.cut())
        return sorted(ln.split(":")[0] for ln in lines if re.fullmatch(r"[a-h][1-8][a-h][1-8][qrbn]?: 1", ln))

    def opening(self, gid: str, counter: int):
        """(moves, whole): the opening reserved for this id; whole is False when no legal move is left inside it."""
        moves: list = []
        fixed = self.fixed[(counter - 1) % len(self.fixed)] if self.fixed is not None else None
        plies = len(fixed) if fixed is not None else self.h["opening_rule"]["plies"]
        for ply in range(plies):
            legal = self.legal_moves(moves)
            if not legal:                                       # mate or stalemate inside the opening
                return moves, False
            if fixed is not None:
                if fixed[ply] not in legal:
                    raise Stop(4, f"the listed opening {' '.join(fixed)} holds an illegal move at ply {ply}")
                moves.append(fixed[ply])
            else:
                moves.append(legal[opening_index(self.h["opening_rule"]["root_seed"], gid, ply, len(legal))])
        return moves, True

    def play(self, gid: str, counter: int):
        """(state, opening, sent, rows, end). Raises EngineError or BindingRefused."""
        eng = self.eng
        assert eng is not None
        eng.sent.clear()                                        # nothing of an earlier game is kept (memory, and A23)
        moves, whole = self.opening(gid, counter)
        if not whole:
            return "noselfgame", moves, "none", [], f"openingend plies {len(moves)} reason nomoves"
        line = record.position_line(moves)
        planted = self.plant[0] if self.plant[1] == counter and not self.plant_used else None
        if planted:
            self.say(f"PLANT {planted} at {gid} (a rehearsal: this piece is not data)")
        if planted == "swap_final":
            line = record.position_line(self.opening(self.gid(counter + 1), counter + 1)[0])
        elif planted == "mvoes":
            line = line.replace(" moves ", " mvoes ")
        elif planted == "cut2":
            line = record.position_line(moves[:-2])
        sg = self.selfgame
        if planted == "writeminply9":
            sg = re.sub(r"writeminply \d+", "writeminply 9", sg)
        mark = len(eng.sent)
        if planted != "no_newgame":
            eng.command("ucinewgame", cutoff=self.cut())
        eng.command(line, cutoff=self.cut())
        ends = (lambda s: s.startswith("sgend ")), self.a.game_seconds, f"game {gid}"
        if planted == "kill_engine":
            self.plant_used = True
            eng.send(sg, cutoff=self.cut())
            time.sleep(0.02)
            eng.p.kill()
            lines = eng.read_until(*ends, cutoff=self.cut())
        elif planted in WATCH_PLANTS:                   # 2.9: switched on while the engine searches this game, the
            self.plant_used = True                      # driver's cutoff taken before (as before a suspension)
            cut = self.cut()
            eng.send(sg, cutoff=cut)
            self.plant_watch(planted)
            lines = eng.read_until(*ends, cutoff=cut)
        else:
            lines = eng.run(sg, *ends, cutoff=self.cut())
        rows = [ln for ln in lines if ln.startswith("sg ")]
        end = lines[-1]
        if planted == "bad_row" and rows:
            self.plant_used = True
            rows[0] += " x"                             # a row out of its shape: the record module must refuse it
        if len(rows) + 1 != len(lines):
            raise EngineError(f"game {gid}: a line that is neither a row nor the game's end line")
        # A23: what was REALLY written for this game, against the reservation, spelt out a second time
        written = eng.sent[mark:]
        pos = [s for s in written if s.split(" ", 1)[0] == "position"]
        if len(pos) != 1 or not written or written[-1].split(" ", 1)[0] != "selfgame":
            raise BindingRefused(f"{len(pos)} position lines between the game's start and its game line")
        if pos[0].split(" ") != record.position_tokens(moves):
            raise BindingRefused(f"reserved `{' '.join(record.position_tokens(moves))}`, written `{pos[0]}`")
        return "done", moves, pos[0], rows, end

    def plant_watch(self, kind: str) -> None:
        """Rehearsal plants of 2.9, switched on while the engine searches: the clock plants change only what the
        readers return (Fable 14:56, Q2); watch_nostop makes the watch's stop do nothing (the alarm at D)."""
        d = self.B.get("cutoff") - time.time()          # seconds to D by the wall clock now
        if kind == "clock_suspend":                     # a suspension past D: UTC and the boot-time clock ran on to
            self.off[0] = self.off[1] = d + 30.0        # 30 s past it, the steady clock stood still
        elif kind == "clock_forward":                   # UTC alone 60 s past D: the boot-time and steady clocks say
            self.off[0] = d + 60.0                      # there is time (the hold)
        elif kind == "clock_back":                      # UTC set back an hour: D comes by the other clocks
            self.off[0] = -3600.0
        elif kind == "clock_ahead":                     # v17 W2: UTC alone an hour AHEAD with no bound near: the
            self.off[0] = 3600.0                        # games go on, t0_ms follows anchor + steady (the earliest)
        elif kind == "watch_nostop":
            self.ph.stop = lambda: None
        else:                                           # watch_lategone: once the watch has fired, its look for the
            gone = self.ph.gone                         # exit blocks until D has come, then answers truly

            def late_gone(timeout=0.0):
                if self.w is not None and self.w.fired is not None:
                    while self.B.judge("cutoff")[0] == clockwatch.OPEN:
                        time.sleep(0.005)
                return gone(timeout)
            self.ph.gone = late_gone
        self.say(f"PLANT {kind}: utc {self.off[0]:+.3f} s, boot {self.off[1]:+.3f} s")

    def write_game(self, counter: int, state: str, moves, sent: str, rows, end: str, r0) -> None:
        """v17 W1 to W3: the game line also carries t0_ms (the earliest clock at the reading r0 of the judgement that
        preceded the reservation, C-R1) and ms (the steady clock from r0 to right before the line's write: the engine's
        start for the slot's first game, the game and the record's write)."""
        if self.open_index > 999999:
            raise Stop(4, "the slot has used all 1,000,000 piece indices")
        gid = self.gid(counter)
        text = record.text(self.run_fp, gid, moves, sent, rows, end).encode("ascii")
        bind = record.bind(self.run_fp, gid, moves, sent, rows, end)
        piece = self.dir / "open" / f"p{self.open_index:06d}.raw"
        new = not piece.exists()
        with open(piece, "ab") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
            end_b = f.tell()
        if new:
            fsync_dir(piece.parent)
        line = {"t": state, "game": gid, "index": self.open_index, "end": end_b, "bind": bind}
        if state == "done":
            line["rows"] = len(rows)
        else:
            line["plies"] = len(moves)
        line["t0_ms"] = self.B.earliest_ms(r0)
        line["ms"] = math.floor(1000 * (self.B.clocks.mono() - r0[1]))
        self.append(line)
        self.open_games.append(G(counter, gid, state, bind, len(rows), end_b))
        self.states[counter], self.piece_of[counter] = state, self.open_index

    def heartbeat(self, games: int, rows: int, gid: str) -> None:
        part = self.dir / "heartbeat.part"
        part.write_bytes(canon({"at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "epoch": self.epoch,
                                "games_this_start": games, "last_game": gid, "rows_this_start": rows}))
        os.replace(part, self.dir / "heartbeat")

    # ---- the run -----------------------------------------------------------------------------------------------
    def finish_day(self, why=None) -> str:
        self.kill_engine()
        self.close_piece()
        if why == "finalizer" and self.play_epochs:     # 2.7: only an EARLIER start that may play can have sent an
            f = self.first_not_passed()                 # id to an engine and died before its first byte (2.4); 2.6:
            self.in_doubt = f if f is not None and f not in self.states else None   # a line there is a barrier
        for row in self.my_rows:
            self.range_seal(row)
        if why is None:
            why = "ranges done" if all(self.complete(row) for row in self.my_rows) else "cutoff"
        self.append({"t": "ended", "epoch": self.epoch, "last_index": self.last_index, "last_seal": self.last_seal,
                     "why": why})
        self.say(f"the slot has ended ({why})")
        return why

    def watch_alarm(self, w):
        """None, or the alarm line of the watch of the last wait (2.9; FABLE-2311-LATE-IS-ALARM, -LATE-FIELDS and
        clockwatch 4): an error inside it (the module's line); else, when the module raised its alarm or, with the
        reason cutoff, D itself had come at the decision or the exit was confirmed after D, ONE fixed word from the
        record, so the guard can tell a failed stop from a bound that came late from a slow stop: "still there"
        (never confirmed gone), "decided after D", "gone after D", "gone late" (confirmed more than one allowance
        after the decision), with the readings and the module's own alarm text. A tighter D found after its trigger
        (late_discovery) and gone before D is no alarm."""
        if w is None or w.fired is None:
            return None
        if w.error is not None:
            return next(ln for ln in w.lines() if ln.startswith("ALARM"))
        rec = w.record or {}
        cut = w.fired == "cutoff"
        if w.alarm is None and not (cut and (rec.get("decided_after_cutoff") or rec.get("gone_after_cutoff"))):
            return None
        word = ("still there" if rec.get("gone") is None else "decided after D" if cut and
                rec.get("decided_after_cutoff") else "gone after D" if rec.get("gone_after_cutoff") else "gone late")

        def rd(k):
            return clockwatch.reading_text(rec[k]) if rec.get(k) is not None else "none"
        return (f"ALARM watch: {word}: the native process was not gone in time (reason {w.fired}); decision "
                f"{rd('decided')}; stop {rd('stopped')}; gone {rd('gone')}" + (f"; {w.alarm}" if w.alarm else ""))

    def stop_alarm(self, line, counter, text: str) -> int:
        """2.7 / 2.9, the HOLD or the watch's ALARM, in this order exactly (Fable 14:56, Q1): the game in flight
        journalled (`failed` why "clock" in the hold), the open piece sealed, the alarm line written, flushed and
        printed; exit 8, WITHOUT an `ended` line (as at the STOP file): the guard establishes the time (D5)."""
        self.kill_engine()
        if line is not None:
            self.append(line)
            self.states[counter] = line["t"]
        self.close_piece()
        self.say(text)
        self.log.flush()
        os.fsync(self.log.fileno())
        print(text)
        return 8

    def run(self) -> int:
        self.boot = boot_id()
        resume = self.admitting_resume()                # walked at every start (Neon 223800Z 1; guard v2 R7)
        self.load_schedules(start=True)                 # the chain, before anything is changed
        self.no_hold("nothing was changed")             # 2.9: the clocks, before anything is changed
        first_start = not (self.dir / "journal.txt").exists()
        if first_start and not self.fenced() and self.clock_state() == "play":
            self.hash_engine("nothing was changed")     # 1.3: a first start that may play, before the slot is touched
        self.claim_slot()
        try:
            self.read_journal()
            if self.ended:
                self.say("started after the slot's `ended` line: nothing to do")
                print(f"worker {self.slot}: the slot has ended already; nothing was done")
                return 0
            self.load_schedules(start=True)             # again (the kept bytes): the journal says which ranges started
            self.check_serial_order()                   # 2.7 (Neon 153430Z): unreconciled = Stop 4, nothing written
            self.no_hold("no journal line and no piece were written")
            f = self.first_not_passed()                 # 2.7: the mode, before the epoch line; an unfinished first id
            self.mode = "play" if (not self.fenced() and self.clock_state() == "play"            # is a barrier (2.6)
                                   and (f is None or self.states.get(f) != "unfinished")) else "seal_only"
            if self.mode == "play" and not first_start:
                self.hash_engine("no journal line and no piece were written")
            if self.epoch >= 9999:
                raise Stop(4, "the slot has used all 9,999 epochs")
            named = None
            if resume is not None:                      # FORMATS 2.4 (Neon 151130Z, Astra 151303Z)
                mine = [s for s in resume[2].get("slots", []) if isinstance(s, dict) and s.get("slot") == self.slot]
                first = self.boot_first.get(self.boot)
                if first is None:                       # the first start under this boot: the journal must be where
                    if mine != [{"last_index": self.last_index, "last_seal": self.last_seal, "slot": self.slot}]:
                        raise Stop(4, f"{resume[0]} does not name this slot's last piece as the journal has it "
                                      f"(index {self.last_index})")       # the RESUME found it, and it is named
                    named = resume[1]
                elif len(mine) != 1 or first != (resume[1], mine[0].get("last_index"), mine[0].get("last_seal")):
                    raise Stop(4, f"the first epoch line under this boot does not name {resume[0]} and its anchor for "
                                  f"this slot (a changed anchor); the journal is kept as it is")
            self.drop_unfinished_line()
            self.epoch += 1
            self.append({"t": "epoch", "epoch": self.epoch, "prev_epoch": self.epoch - 1, "last_index": self.last_index,
                         "last_seal": self.last_seal, "boot_id": self.boot, "resume": named, "mode": self.mode})
            self.repair_open_piece()
            self.say(f"worker {self.slot} of run {self.h['run']}: epoch {self.epoch} ({self.mode}), schedule {self.sched_n}, "
                     f"{sum(1 for s in self.states.values() if s in FINAL)} games final; plant {self.plant}")
            stop_file = self.root / "STOP"
            fails = played = rows_total = 0
            first_look = True
            while True:
                if stop_file.exists():
                    self.kill_engine()
                    self.close_piece()
                    self.say(f"the STOP file: {played} games this start; the open piece is sealed, the slot goes on")
                    print(f"worker {self.slot}: stopped by the STOP file after {played} games")
                    return 0
                st = None
                if self.mode == "play":                 # 2.7: a seal_only epoch follows no schedule, reserves nothing
                    self.load_schedules()
                    st = self.clock_state()             # 2.9: the ONE judgement, before every reservation
                    if st == "hold":                    # nothing in flight: the open piece sealed, the alarm, exit 8
                        return self.stop_alarm(None, None, self.hold_text())
                if self.mode == "seal_only" or self.fenced() or st != "play":
                    why = self.finish_day("finalizer" if first_look else None)
                    print(f"worker {self.slot}: the slot has ended ({why}); {played} games, {rows_total} rows this start")
                    return 0
                first_look = False
                counter = self.next_counter()
                if counter is None:
                    time.sleep(1.0)                             # a new schedule, the dispatch end, the fence or STOP
                    continue
                r0 = self.reading                               # v17 W2: the judgement that preceded this reservation
                if self.open_games and self.round_of(self.open_games[0].counter) != self.round_of(counter):
                    self.close_piece()
                gid = self.gid(counter)
                self.top = max(self.top, counter)               # reserved: its range has started (follow(), 1.2)
                self.w, err = None, None
                try:
                    if self.eng is None:
                        self.start_engine()                     # its start-up check under a watch of its own
                    state, moves, sent, rows, end = self.watched(self.play, gid, counter)
                    record.bind(self.run_fp, gid, moves, sent, rows, end)   # the record module's one judge, BEFORE
                except StartRefused as e:                                    # a byte is written: a refusal fails the game
                    if self.w is None or self.w.fired is None:
                        self.say(f"START REFUSED: {e}")
                        raise Stop(5, f"start-up refused: {e}") from None
                    err = e                                     # the watch ended the process: judged by its reason
                except BindingRefused as e:
                    self.kill_engine()
                    self.append({"t": "refused", "game": gid, "why": "binding"})
                    self.states[counter] = "refused"
                    self.say(f"game {gid} NOT CREDITED, binding refused: {e}")
                    raise Stop(7, f"binding refused for {gid}: {e}") from None
                except (EngineError, record.RecordError) as e:
                    err = e
                w = self.w                                      # 2.9: the watch's reason first, then the clocks judged
                text = self.watch_alarm(w)                      # again (also when the game ended by itself in that
                if text is not None:                            # same moment)
                    t = "unfinished" if w.fired == "cutoff" else "failed"
                    return self.stop_alarm({"t": t, "game": gid, "why": "cutoff" if t == "unfinished" else
                                            "clock" if w.fired == "clock" else "the watch failed"}, counter, text)
                st = w.fired if w is not None and w.fired in ("clock", "cutoff") else self.clock_state()
                if st in ("clock", "hold"):                     # the hold: the game in flight failed (why "clock")
                    return self.stop_alarm({"t": "failed", "game": gid, "why": "clock"}, counter, self.hold_text())
                if st == "cutoff":                              # D: the game thrown away whole, the slot ends
                    self.kill_engine()
                    self.append({"t": "unfinished", "game": gid, "why": "cutoff"})
                    self.states[counter] = "unfinished"
                    self.load_schedules()                       # the schedule whose D the watch took (refresh() only
                    self.finish_day("cutoff")                   # read it): the range seals name it and its ranges
                    print(f"worker {self.slot}: the cutoff ended {gid} and the slot; {played} games this start")
                    return 0
                if err is not None:
                    self.kill_engine()                          # never used again (the driver's rule)
                    fails += 1
                    self.append({"t": "failed", "game": gid, "why": str(err)[:200]})
                    self.states[counter] = "failed"
                    self.say(f"game {gid} thrown away ({fails} in a row): {err}")
                    if fails >= 3:
                        raise Stop(6, f"three engine failures in a row, the last at {gid}: {err}") from None
                    continue
                fails = 0
                self.write_game(counter, state, moves, sent, rows, end, r0)
                played, rows_total = played + 1, rows_total + len(rows)
                self.heartbeat(played, rows_total, gid)
                if len(self.open_games) >= self.h["piece_games"]:
                    self.close_piece()
                row = self.range_done(counter)
                if row is not None:
                    self.close_piece()
                    self.range_seal(row)
        finally:
            self.kill_engine()
            if self.lock is not None:
                self.lock.release()


def main() -> int:
    ap = argparse.ArgumentParser()
    for name in ("root", "exe", "net", "manifest", "known-startup"):
        ap.add_argument("--" + name, required=True)
    ap.add_argument("--slot", type=int, required=True)
    ap.add_argument("--openings", default="")
    ap.add_argument("--game-seconds", type=float, default=600.0)
    ap.add_argument("--trace", action="store_true", help="every line to and from the engine into worker.log")
    ap.add_argument("--rehearsal", action="store_true")
    ap.add_argument("--plant", default="")
    a = ap.parse_args()
    if not 0 <= a.slot <= 999 or not 0 < a.game_seconds < 1e6:
        print("STOP: --slot is 0 to 999 and --game-seconds above 0")
        return 2
    w = None
    try:
        w = Worker(a)
        return w.run()
    except Stop as e:
        print(f"worker {a.slot}: STOP ({e.code}): {e}")
        if w is not None:
            w.say(f"STOP ({e.code}): {e}")
        return e.code
    except Exception as e:  # noqa: BLE001   never a traceback (Fable 14:13, C3): every other fault is a 4
        print(f"worker {a.slot}: STOP (4): an input or the spool cannot be read: {type(e).__name__}: {e}")
        if w is not None:
            w.say(f"STOP (4): {type(e).__name__}: {e}")
        return 4


if __name__ == "__main__":
    sys.exit(main())
