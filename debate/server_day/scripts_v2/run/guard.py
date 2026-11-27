"""Opus 2026-11-23, version 1 of the server day's GUARD (Fable's FABLE-2311-OPUS-18H, A3a; FORMATS 2.9 sections 0,
1.2 and 1.8; SETUP_PLAN 2.7 D2, D5, D15 and rows 11, 17 and 19 to 23 of its section 7; Astra 160235Z, 160610Z,
161634Z, 171134Z, 171332Z, 172109Z). ONE program runs the day on the server: it starts and owns every worker and the
packer, takes home's decision, writes every schedule after the pilot, publishes the fence and closes the day.
Standard library only; the same file runs on Linux (the day) and on the PC (the tests).
VERSION 2 (A5: the repairs of the seats' NOT YET on version 1, 67384d4b5e3d; Astra 215151Z, 220826Z, 225517Z, Neon
223800Z, the agreed spec server_guard_completion.md): no file on disk is trusted by its name or its existence alone.
R1 guard/CLOSED.json is this run's closing record or the guard stops (exit 4); R2 FENCE.json is this run's fence of
the D in force or the guard stops (exit 4); R3 a slot has ended only by the worker's own ended line under this run's
IDENTITY.json, at the end of its seal chain; R4 a piece seal counts in the room test only as this run's seal of its
slot, index and chain; R5 a range seal counts as sealed only as this run's seal of the newest schedule's row whose
through_seal is on disk; R6 (Linux) an earlier guard's group whose leader is gone has every member left ended at
every pass (an orphaned engine never searches on); R7 every RESUME is walked as a chain; R8 the policy holds
target_rows and the header's pilot round count; R9 a fence control is bound to the policy too; R10 the terminal
writer runs after the packer's last pass and CLOSED.json names the inventory it verified; R12 (Linux, Fable's G2) a
process found by a scan is ended only through a pidfd opened first, after /proc was read again and the pidfd shows it
still living (a number given again in between is never ended); without a working pidfd the guard does not start.

    guard.py --root DIR --exe E --net N --manifest M --known-startup S --converter C --policy P --floor-bytes B
             [--openings F] [--game-seconds T = 600] [--horizon H = 2] [--tick S = 1] [--allowance S = 2]
             [--end-grace S = 60] [--python PY = this interpreter]

DIR is the run's folder, the workers' and the packer's. The guard's own files are in DIR/guard/: LOCK, guard.log
(every line flushed; routine lines stop at 64 MiB, alarms never), hourly.jsonl, w<NNN>.out and packer.out (what they
print), groups.jsonl (every process group it started, with the boot), CLOSED.json. What home sends lands in
DIR/inbox/ and only the guard reads it; what the guard accepted is kept in DIR/control/, create-only.

ONE PASS every --tick seconds, in this order:
G1 START (once). One guard: an OS lock on guard/LOCK (else exit 3). RUN.json canonical with the keys of 1.1, its
   slots, piece_games, pilot_ranges (rows of schedule 0), lease_start_utc and hard_cutoff_utc. The policy file is
   the package's plan.json as the budget tool reads it (floor, margin, choice: json with no key twice and no NaN; an
   `owner_choice` object with a `name`; target_rows an integer >= 1; pilot_rounds_declared the header's highest
   pilot round); its sha256 is the package's owner policy. Every
   SCHEDULE.<n>.json on disk walked as a chain (canonical, schema 2, n, prev, this run, evidence, bounds never later,
   rows as 1.2): a break stops the guard (exit 4), since only the guard writes schedules. Then the accepted controls
   are REPLAYED (G3).
G2 THE BOOT. This machine's boot id is the header's, or a RESUME.<n>.json of this run names it as new_boot_id (the
   boot guard writes it, the worker verifies its chain). Otherwise the guard takes no control, writes no schedule and
   starts nothing (an ALARM once); it still ends the groups it started itself.
G3 THE CONTROL RECORD (1.2). inbox/CONTROL.<k>.json.zz for the NEXT k (one more than the controls accepted, never a
   count of schedules: Astra 171332Z), decoded (zlib, at most 16 MiB), is ACCEPTED only when all of this holds;
   otherwise it is HELD: an ALARM names the first check that fails, nothing is written, and it is read again at the
   next pass (a corrected upload, or an evidence file that arrives late, is taken then).
   a. canonical bytes with exactly the keys at_utc, cutoff_utc, decision, dispatch_end_utc, evidence, k, kind,
      owner_policy, prev, run_fingerprint, schema, scope; schema 2; this run; k as in its name; prev = sha256 of the
      accepted control k - 1 (`first` for k = 1); kind one of pilot_decision, target, matches, fence;
   b. inbox/EVIDENCE.<evidence>.json.zz whose DECODED bytes have that sha256 (Astra 172109Z: the public bytes are
      hashed before they are packed) and are a canonical record without `local_only` (the full local report never
      travels: a control resting on it is HELD);
   c. owner_policy = the sha256 of the policy file, and the report's inputs.plan_sha256 too, for every kind (the
      report was computed from that policy; R9);
   d. at_utc, cutoff_utc and dispatch_end_utc are existing UTC times, the dispatch end not after the cutoff, neither
      bound later than the one in force (the newest schedule's; the header's hard cutoff before any);
   e. the report agrees (Astra 161634Z): for pilot_decision and target, decision is the report's outcome; for
      matches, decision equals the report's matches; when a schedule follows, cutoff_utc and dispatch_end_utc are the
      header's lease_start_utc plus the report's whole cutoff_floor_s and dispatch_end_floor_s (the budget tool's
      seconds count from the lease's start);
   f. the effect, from the hashed policy, never from an exit code, a displayed number or a label (Astra 171134Z):
      REACHED, STOP, SHORT: the fence. UNQUALIFIED: nothing, the pilot ranges stay. SELF_PLAY and
      SELF_PLAY_AND_MATCHES: a schedule (no match is played: this package has no match runner; an ALARM says so).
      OWNER_CHOICE: the policy's owner_choice. Action "stop": the fence. Action "self_play" (F2, 26 Nov: the
      owner's 1A of 25 Nov, as many rows as fit into the day): a schedule, capped by the policy's full target_rows.
      Action "reduced_target" with
      reduced_target_rows R needs the report's `reduced` = {"covered": bool, "target_rows": R}: covered, a schedule
      whose scope names at most R rows; not covered, the policy's `if_uncovered` ("stop": the fence; "self_play": a
      schedule), and without it HELD (the missing decision named). Any other action: HELD. Kind fence: the fence.
      Kind matches: nothing (an ALARM: no match runner). A schedule needs scope {"highest_round": R, "target_rows":
      N} with integers, R above the highest round scheduled and at most 9999, N at least 1 and at most the policy's
      target_rows (the reduced target where one applies: a target changes only by a new policy); every other effect
      needs scope null. (owner_choice.action and if_uncovered: since F2 the budget tool refuses a plan without a
      known action, exit 2; a name is a label, not an action. The guard still HOLDS what it does not know.)
   g. a schedule passes the room test (G5).
   Accepted: control/EVIDENCE.<sha256>.json and control/CONTROL.<k>.json written create-only (the decoded bytes, in
   that order), then the effect: the schedule (G4), or the fence, whose `why` names the control's sha256. The same
   bytes again change nothing. A known k with other bytes in the inbox is an ALARM; the accepted copy stays. At
   start every accepted control is checked again (a chain from 1, its evidence copy, a-c, e, f) and its effect found
   (a schedule naming it as evidence; the fence naming it) or, for the LAST one only, owed: it is made at the first
   pass that may act (G2, no STOP, no HOLD; a schedule only before the fence and D, and only when it passes the room
   test: until then an ALARM, it is tried again every pass and no later control is taken). A missing effect of an
   earlier one stops the guard (exit 4). Once the fence is there or D has come the inbox is not read.
G4 THE SCHEDULES. The guard writes every schedule after the pilot, create-only: all rows of the newest one (the
   header's pilot_ranges before any) unchanged, plus one row a slot for each new round r: first = the slot's
   highest counter + 1, last = first + (the length of the slot's highest row) - 1, short false, schedule n (the
   editor's rule: a production round is as long as the slot's last one; a slot without rows gets none). A control's
   schedule adds rounds M + 1 to min(M + H, R) (M the highest round so far, H the horizon, R the scope's highest
   round) with the control's bounds. THE ROLLING EXTENSION (D2 2.4 (2); 1.2 "what survives a home outage") adds
   round M + 1 with the newest schedule's bounds when some slot holds the range seal (ranges/r<NNNN>.w<NNN>
   .seal.json, written when its range is complete) of round M - H + 1 or later; under the LATEST accepted control
   of kind pilot_decision or target, only when its effect was a schedule, up to its scope's highest round, before
   the dispatch end, without a fence and without STOP, and only when the room test passes. Its evidence is that
   control's sha256. It never moves a bound, never starts a match and never changes the target.
   THE CHAIN ENDS AT SCHEDULE.999 (G-A, Fable 25 Nov: the grammar of the worker, packer, terminal, fetch and credit):
   no schedule 1000 is ever written; a control that would need it is HELD, the extension ALARMs, an owed effect is
   tried again each pass, and the day goes on in the rows of SCHEDULE.999 (about 1,000 rounds: pilot rounds +
   horizon + 998 when every later schedule is the extension's one round, up to horizon - 1 more for each later
   control's own schedule; the seats' question with --round-games).
G5 ROOM (D2; row 17). A schedule is written only when (free bytes on DIR's volume) - need >= --floor-bytes, where
   need = (counters of the rows whose range seal is not there yet) x (bytes a game) + (rows) x 13,312 (a range seal,
   its wire copy, its line of the inventory) + 2 x (every schedule's bytes, its own included: the wire copy and the
   inventory) + 3 x (its bytes rounded up to 4 KiB) + 1 MiB, and (bytes a game) = 2 x (the raw bytes of every
   sealed piece + 32 KiB a piece) / (their games), read from the seals (the editor's figures, not measured; the
   pilot's measured peak replaces them). No sealed piece: not admitted. Not admitted: HELD with an ALARM and tried
   again every pass. Free bytes under the floor: an ALARM (once). What is scheduled already is still played: a
   pause of a running worker needs a file the worker reads, which is not built.
G6 THE WORKERS AND THE PACKER. Every slot without its `ended` line (the last complete line of its journal, as the
   packer reads it) gets ONE worker, `python -I -B run/worker.py --root DIR --slot K ...`, in a session and process
   group of its own (Linux; on Windows a job object holds it and everything it starts), its printed lines appended
   to guard/w<NNN>.out. When a worker has exited, every member left in its group (an orphaned engine above all:
   Astra 160235Z) is ended and verified gone within --allowance (else an ALARM) BEFORE the worker is reaped, so the
   group's number is not free meanwhile. Then by its exit code, while the day plays: any code with the `ended`
   line, the slot is done; 0 without it (the STOP file), started again 5 s later when STOP is gone; 6 or a signal,
   again after 30 s or 5 s; 8, again after 10 s when the guard's own clocks say play; 3 (another writer holds the
   slot's lock), looked at again after 30 s; 2, 4, 5, 7 or any other code: a named fault, the slot is FAULTED (no
   start while the day plays). A sixth start of a slot within one hour: FAULTED too. The packer (`python -I -B
   run/packer.py --root DIR --converter C`) in a group of its own, started again 30 s after any exit before its
   last pass, at most five times an hour; its exit 0 when the fence or STOP_PACKER is there is its last pass.
   Before any start the folder's OS lock is probed, taken and released at once (w<NNN>/LOCK; the packer's
   out/LOCK): held by a process this guard did not start (a worker or packer of an earlier guard lives on in its own
   session), nothing is started or counted and it is looked at again after 30 s; such a slot at D + --end-grace is
   UNRECONCILED.
G7 THE END (1.8). The bounds are judged by clockwatch.Bounds (three clocks, the earliest, latched, the hold): D is
   the header's hard cutoff and every schedule's cutoff, the dispatch end the same. At D without a fence: FENCE.json
   (schema 2, run_fingerprint, at_utc, cutoff_utc = the D in force copied, why "D") create-only. Once the fence is
   there or the dispatch end has come, a slot without `ended` and without a live worker gets a start (the worker's
   epoch is then seal_only by itself: the finalizer), a faulted slot included; such a start that ends without the
   slot's `ended` line makes the slot UNRECONCILED, except that 0, 3 and 8 are tried again until D + --end-grace
   (judged by the three clocks; a HOLD is not taken as come). A start made BEFORE the end that ends after it without
   `ended` is not such a start: before D + --end-grace its slot gets the finalizer's start next (v17: Neon's catch,
   26 Nov). A worker still alive at D + --end-grace: its group is
   ended (an ALARM). On Linux the groups that an EARLIER guard of this boot started (guard/groups.jsonl) are ended
   at D + --end-grace too, and a member is touched only when its command line names DIR (a worker) or the engine
   file (an engine). When the fence is there, every slot is ended or unreconciled and no worker lives: STOP_PACKER
   (canonical: at_utc, run_fingerprint, schema, unreconciled) create-only when a slot is unreconciled; the packer's
   last pass; guard/CLOSED.json; exit 0. In a HOLD of the guard's own clocks: no control, no schedule, no start, an
   ALARM; the HOLD is latched for the life of this guard (re-establishing the time and starting the guard again is
   the boot guard's).
G8 THE STOP FILE (row 23). DIR/STOP: no control is taken, no schedule written, no worker or packer started; the
   groups of exited processes are still ended. When it is gone, everything goes on.
G9 THE HOURLY LINE (row 21). At the first pass and then every hour of the steady clock, one canonical line in
   guard/hourly.jsonl, for people (nothing reads it): at_utc, state, schedules, controls accepted, fence, the slots
   ended, live, faulted and unreconciled, free bytes, alarms so far, the alarms standing, STOP.
G10 THE CLOSE (R10). When the fence is there, every slot is ended or unreconciled, no worker lives and the packer has
   made its last pass: the terminal writer (`python -I -B run/terminal.py --root DIR`, a group of its own, its print
   in guard/terminal.out). Exit 0 and TERMINAL.jsonl.zz decoding to TERMINAL.jsonl, its first line RUN.json's bytes,
   its last a canonical footer whose fingerprint is sha256 of every byte before it: guard/CLOSED.json with terminal
   {lines, sha256, zz_sha256}. Anything else: no CLOSED.json, an ALARM naming why, the originals untouched, tried
   again after 60 s.
G11 THE CLOCK FILE (v16; the clock known answers G and ADDENDA 3 and 4 on the PC). ROOT/CLOCK.json, canonical,
   exactly {n, run_fingerprint, schema 1, state, utc_ms}: home's clock.py measure fetches it to take the SERVER's
   time for its decisions (the PC's own clock is never judged). Written whole (create-new .CLOCK.json.<pid>.part,
   flushed, os.replace) at the first pass and then at most once every 60 s of the steady clock, in every state; n
   goes up by 1 a write and continues from this run's CLOCK.json when a guard starts again (another run's file, or
   one that is not the record, is replaced from n 1). utc_ms is the guard's time by its three clocks at ONE
   reading, the same one that gives state: the EARLIEST of UTC, anchor + steady run and anchor + boot run, rounded
   down to the millisecond. A UTC that jumps ahead never enters it; one set back does (home then decides late,
   never early). clockwatch judges a BOUND by the clock furthest AHEAD (stop early); CLOCK.json takes the one
   furthest BEHIND (decide late): two safe sides for two purposes, never to be made the same. Its limit: an anchor
   read inside a jump lets a later jump pass the minimum; such a guard fences at once when the jump is large (its
   steady clocks say every bound within the jump has come: COME, not UTC alone), a small jump is harmless, and the
   boot guard's "clock synchronised" stands before every start. state is state() of the three clocks; a fence
   does not change it (after the fence at D it is cutoff). A write that fails is the ALARM clock and is tried again
   at the next pass; nothing of the guard depends on it.
G12 THE PILOT'S RECORD (v17 GP1 to GP9 and ADDENDUM 1's GP3b to GP3d; home's state.py R3 reads it). ROOT/PILOT.json,
   canonical, create-only, written ONCE at the first pass where (a) every row of RUN.json's pilot_ranges has its range
   seal, this run's seal of THAT row (range_fault against the header's row: a schedule written meanwhile does not
   hide it), and (b) every pilot piece of every slot, 0 to T_k (the highest through_index of the slot's pilot range
   seals), has its offer wire copy out/w<k>/p<i>.offer.json.zz; before that: nothing, no alarm. It holds {packer,
   rounds, run_fingerprint, schema 1, slots}: per slot, in the header's order, from the complete done and noselfgame
   lines of w<k>/journal.txt whose game lies in a pilot row of the slot (read incrementally): games, first_t0_ms (the
   least t0_ms), last_end_ms (the greatest t0_ms + ms), longest_ms, play_ms (the sum of ms), span_ms; from the piece
   seals 0 to T_k (R4's rule): raw_rows (their rows), epochs (rising); the packer, from the complete lines of
   out/PACKER_TIMES.jsonl that are exact R2 records: pieces, busy_ms and raw_rows of the pilot pieces' offered lines,
   restarted = start lines - 1. GP3, each a failure with NO file and the ALARM pilot naming the slot and what differs,
   checked again at every pass: games equal to the pilot range seals' and to the piece seals'; the range seals'
   first_index chain from piece 0 in round order; the done lines' rows equal to the piece seals'; every pilot line
   with t0_ms and ms; at least one pilot piece (home's R3 needs its epochs); last_end_ms not after the guard's own
   utc_ms at the pass (GP3d); the times file begins with a start line (GP3c); no pilot piece offered twice; a pilot
   piece without its offered line only after a restart of the packer (C-R2), else silence for 120 s of the steady
   clock after (a) and (b) first held (GP3b: the line follows the wire copy), then the alarm. A PILOT.json found (a
   restarted guard) is never written again; one not canonical or not this run's is the ALARM pilot, kept as it is
   (GP4). Any fault inside is the ALARM pilot, tried again at the next pass: nothing else depends on it (GP9).
EXIT CODES: 0 the day is closed (CLOSED.json, this run's closing record: a guard started after it exits 0 at once);
2 a wrong call; 3 another guard holds the lock; 4 the header, the policy, the schedule chain, the accepted controls,
FENCE.json, CLOSED.json or a file the guard must write cannot be trusted. Never a traceback.
NOT HERE (version 2): memory (row 20); a pause of running workers at the floor; a match runner; on Windows the groups
an earlier guard started (only a job object of this process can be ended).
"""
import argparse
import ctypes
import json
import math
import os
import re
import select
import shutil
import signal
import subprocess
import sys
import time
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import clockwatch as cw  # noqa: E402
from worker import (HEADER_KEYS, HEX64, SCHEDULE_KEYS, SlotLock, Stop, _not_int, _pairs, boot_id, canon,  # noqa
                    check_rows, create_only, parse_canon, sha256_bytes, utc)

RUN_DIR = Path(__file__).resolve().parent
CONTROL_KEYS = ["at_utc", "cutoff_utc", "decision", "dispatch_end_utc", "evidence", "k", "kind", "owner_policy",
                "prev", "run_fingerprint", "schema", "scope"]
KINDS = ("pilot_decision", "target", "matches", "fence")
OUTCOMES = ("REACHED", "SELF_PLAY", "SELF_PLAY_AND_MATCHES", "OWNER_CHOICE", "STOP", "SHORT", "UNQUALIFIED")
MAX_DECODED = 16 << 20
CLOSE_ROW_BYTES = 13312
LOG_CAP = 64 << 20
HOUR = 3600.0
RANGE_SEAL = re.compile(r"r([0-9]{4})\.w([0-9]{3})\.seal\.json")
RETRY = {6: 30.0, 8: 10.0, 3: 30.0, 0: 5.0}        # after a signal: 5 s; any other code is a named fault
FENCE_KEYS = ["at_utc", "cutoff_utc", "run_fingerprint", "schema", "why"]
ENDED_KEYS = ["epoch", "last_index", "last_seal", "t", "why"]
CLOSED_KEYS = ["at_utc", "packer", "run_fingerprint", "schema", "slots_ended", "slots_unreconciled", "terminal"]
LEADER = {"worker": "worker.py", "packer": "packer.py", "terminal": "terminal.py"}
TERMINAL_RETRY = 60.0
CLOCK_EVERY = 60.0                                  # G11: CLOCK.json at most once a minute of the steady clock
CLOCK_KEYS = ["n", "run_fingerprint", "schema", "state", "utc_ms"]


TIMES_KEYS = ["form", "games", "index", "ms", "raw_rows", "restart", "slot", "t"]    # v17 R2: an offered line
GP3B_WAIT = 120.0                                   # G12 GP3b: steady seconds a pilot offer may wait for its line
GAME_NO = re.compile(r"[0-9]{8}")


def same(v, want) -> bool:
    """v equals want and has its type (a bool is never an int here)."""
    return type(v) is type(want) and v == want


def times_rec(line: bytes):
    """G12 (v17 R2): the record of one complete line of out/PACKER_TIMES.jsonl when it is exact (the start line, or an
    offered line with its eight keys), else None."""
    try:
        x = parse_canon(line, "PACKER_TIMES.jsonl")
    except ValueError:
        return None
    if x == {"t": "start"}:
        return x
    if (isinstance(x, dict) and sorted(x) == TIMES_KEYS and x["t"] == "offered" and x["form"] in ("binpack", "raw")
            and type(x["restart"]) is bool
            and all(type(x[f]) is int and x[f] >= 0 for f in ("games", "index", "ms", "raw_rows", "slot"))):
        return x
    return None


class Held(Exception):
    """A control record that is not taken now (G3): nothing is written, it is read again at the next pass."""


def T(t: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(t)))


def unzz(path: Path) -> bytes:
    """The decoded bytes of a wire file: ONE whole zlib stream, at most 16 MiB decoded."""
    d = zlib.decompressobj()
    try:
        data = d.decompress(path.read_bytes(), MAX_DECODED + 1)
    except zlib.error as e:
        raise ValueError(f"{path.name}: not a zlib stream ({e})") from None
    if len(data) > MAX_DECODED or d.unconsumed_tail:
        raise ValueError(f"{path.name}: more than {MAX_DECODED} bytes decoded")
    if not d.eof or d.unused_data:
        raise ValueError(f"{path.name}: not one whole zlib stream")
    return data


def last_line(path: Path):
    """The last complete (LF-ended) line of an append-only file, parsed; None when there is none or it does not
    parse (the packer's rule for a slot's `ended` line)."""
    try:
        with open(path, "rb") as f:
            size = f.seek(0, 2)
            f.seek(max(0, size - 65536))
            data = f.read()
    except OSError:
        return None
    end = data.rfind(b"\n")
    if end < 0:
        return None
    start = data.rfind(b"\n", 0, end) + 1
    if start == 0 and size > len(data):
        return None                                 # the last line is longer than the window
    try:
        return parse_canon(data[start:end + 1], path.name)
    except ValueError:
        return None


def is_member(pid: int, pgid: int, marks=()) -> bool:
    """Process `pid` lives (not a zombie) in process group `pgid` and, when `marks` are given, its command line
    contains one of them (Linux, /proc)."""
    try:
        with open(f"/proc/{pid}/stat", "rb") as f:
            s = f.read()
        fields = s[s.rfind(b")") + 2:].split()
        if len(fields) < 3 or int(fields[2]) != pgid or fields[0] == b"Z":
            return False
        if marks:
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                line = f.read().replace(b"\0", b" ")
            return any(m.encode() in line for m in marks)
        return True
    except (OSError, ValueError):
        return False


def linux_members(pgid: int, marks=()) -> list:
    """The processes of a process group that are not zombies (Linux, /proc), optionally only those whose command
    line contains one of `marks`."""
    return [int(e.name) for e in os.scandir("/proc") if e.name.isdigit() and is_member(int(e.name), pgid, marks)]


def end_exact(pid: int, ours) -> bool:
    """R12 (Linux, Fable's G2): end a process found by a scan only while it is still that process. A pidfd first; then
    ours() reads /proc again; then the pidfd is polled (readable: the process it holds has exited, so what ours() read
    may be another process of the same number); only then the signal goes through the pidfd. True when sent."""
    try:
        fd = os.pidfd_open(pid)
    except OSError:
        return False
    try:
        if not ours():
            return False
        p = select.poll()
        p.register(fd, select.POLLIN)
        if p.poll(0):
            return False
        signal.pidfd_send_signal(fd, signal.SIGKILL)
        return True
    except OSError:
        return False
    finally:
        os.close(fd)


def proc_table() -> dict:
    """Linux: process group -> [(pid, command line bytes)] of every process that is not a zombie (one walk of /proc)."""
    out = {}
    for e in os.scandir("/proc"):
        if not e.name.isdigit():
            continue
        try:
            with open(f"/proc/{e.name}/stat", "rb") as f:
                s = f.read()
            fields = s[s.rfind(b")") + 2:].split()
            if len(fields) < 3 or fields[0] == b"Z":
                continue
            with open(f"/proc/{e.name}/cmdline", "rb") as f:
                line = f.read().replace(b"\0", b" ")
            out.setdefault(int(fields[2]), []).append((int(e.name), line))
        except (OSError, ValueError):
            continue
    return out


def orphan_groups(foreign, table, marks):
    """R6's decision, without a process touched: (the earlier groups that still have a member, [(pgid, kind, pids)]
    of those whose leader is gone, no member naming its script, with members naming one of `marks`). A group of a
    kind the guard does not know is left to G7. `table` as proc_table() gives it (a stand-in in the tests)."""
    live, orphans = [], []
    for pgid, kind in foreign:
        mem = table.get(pgid, [])
        if not mem:
            continue
        live.append((pgid, kind))
        if kind not in LEADER or any(LEADER[kind].encode() in line for _, line in mem):
            continue
        left = [pid for pid, line in mem if any(m.encode() in line for m in marks)]
        if left:
            orphans.append((pgid, kind, left))
    return live, orphans


class _Acct(ctypes.Structure):
    _fields_ = [("user", ctypes.c_int64), ("kernel", ctypes.c_int64), ("puser", ctypes.c_int64),
                ("pkernel", ctypes.c_int64), ("faults", ctypes.c_uint32), ("total", ctypes.c_uint32),
                ("active", ctypes.c_uint32), ("terminated", ctypes.c_uint32)]


def _kernel32():
    from ctypes import wintypes
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.CreateJobObjectW.restype = wintypes.HANDLE
    k.CreateJobObjectW.argtypes = (ctypes.c_void_p, wintypes.LPCWSTR)
    k.AssignProcessToJobObject.restype = wintypes.BOOL
    k.AssignProcessToJobObject.argtypes = (wintypes.HANDLE, wintypes.HANDLE)
    k.TerminateJobObject.restype = wintypes.BOOL
    k.TerminateJobObject.argtypes = (wintypes.HANDLE, wintypes.UINT)
    k.CloseHandle.argtypes = (wintypes.HANDLE,)
    k.QueryInformationJobObject.restype = wintypes.BOOL
    k.QueryInformationJobObject.argtypes = (wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD,
                                            ctypes.c_void_p)
    return k


class Group:
    """One process in a session and process group of its own (Linux), or in a job object with everything it starts
    (Windows: assigned right after its start, while the worker still reads its files and has started no engine)."""

    def __init__(self, cmd, out_path: Path, name: str):
        self.name, self.code, self.done = name, None, False
        self.out = open(out_path, "ab")
        if os.name == "nt":
            self.p = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=self.out, stderr=subprocess.STDOUT,
                                      creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            self.k = _kernel32()
            self.job = self.k.CreateJobObjectW(None, None)
            if not self.job or not self.k.AssignProcessToJobObject(self.job, int(self.p._handle)):
                err = ctypes.get_last_error()
                self.p.kill()
                raise OSError(f"{name}: no job object for the new process (error {err})")
        else:
            self.p = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=self.out, stderr=subprocess.STDOUT,
                                      start_new_session=True)
        self.pid = self.p.pid

    def exited(self) -> bool:
        """The leader has exited. On Linux it is NOT reaped here (WNOWAIT): its number stays taken until reap()."""
        if self.code is not None or self.done:
            return True
        if os.name == "nt":
            return self.p.poll() is not None
        try:
            return os.waitid(os.P_PID, self.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is not None
        except ChildProcessError:
            return True

    def members(self) -> int:
        """How many processes of the group live (the leader's zombie not counted)."""
        if os.name == "nt":
            a = _Acct()
            if not self.k.QueryInformationJobObject(self.job, 1, ctypes.byref(a), ctypes.sizeof(a), None):
                raise OSError(f"{self.name}: the job object cannot be read (error {ctypes.get_last_error()})")
            return a.active
        return len(linux_members(self.pid))

    def end(self) -> None:
        """Every member of the group is sent the end (SIGKILL; TerminateJobObject)."""
        if os.name == "nt":
            self.k.TerminateJobObject(self.job, 1)
            return
        try:
            os.killpg(self.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass

    def end_and_verify(self, allowance: float) -> bool:
        """End the group and look until no member lives; False when one still lives after `allowance` seconds."""
        t_end = time.monotonic() + allowance
        while True:
            if self.members() == 0:
                return True
            self.end()
            if time.monotonic() >= t_end:
                return self.members() == 0
            time.sleep(0.02)

    def reap(self):
        """The exit code (negative: a signal), the leader reaped, the output file closed."""
        self.p.wait()
        self.code, self.done = self.p.returncode, True
        self.out.close()
        if os.name == "nt":
            self.k.CloseHandle(self.job)
        return self.code


class Slot:
    def __init__(self, k: int):
        self.k, self.g, self.starts = k, None, []
        self.ended = False
        self.faulted = None             # text: a named fault, no start while the day plays
        self.unreconciled = None        # text
        self.next_try = 0.0
        self.last_code = None
        self.end_start = False          # G7: the live or last start was made once the end had come (the finalizer)


class Guard:
    def __init__(self, a):
        self.a = a
        self.root = Path(a.root).resolve()
        self.gdir = self.root / "guard"
        self.gdir.mkdir(exist_ok=True)
        self.log = open(self.gdir / "guard.log", "ab")
        self.alarms, self.n_alarms = {}, 0
        try:
            self.lock = SlotLock(self.gdir)
        except Stop:
            raise Stop(3, "another guard holds guard/LOCK") from None
        self.inbox, self.cdir = self.root / "inbox", self.root / "control"
        self.load_header()
        self.load_policy()
        self.B = cw.Bounds()
        self.B.set("cutoff", self.hard)
        self.B.set("dispatch_end", self.hard)
        self.load_schedules()
        self.ctl = []                   # (bytes, record, effect) of every accepted control, k = 1, 2, ...
        self.pending = None             # the k of an accepted control whose effect a restart found missing
        self.slots = {k: Slot(k) for k in self.h["slots"]}
        self.packer, self.packer_starts, self.packer_next, self.packer_done = None, [], 0.0, False
        self.seal_next = {k: 0 for k in self.h["slots"]}
        self.seal_prev = {k: self.genesis(k) for k in self.h["slots"]}
        self.range_ok = {}              # (slot, round) -> the (size, mtime_ns, inode) of the range seal verified (R5)
        self.term, self.term_next, self.term_rec = None, 0.0, None
        self.raw_total = self.games_total = self.pieces_total = 0
        self.next_hour = 0.0
        self.boot = boot_id()
        self.foreign = self.earlier_groups()
        self.clock_every, self.clock_at = CLOCK_EVERY, None      # G11: the steady reading of the last write
        self.clock_n = self.clock_start()
        self.pilot_done, self.pilot_ready_at = False, None      # G12: PILOT.json written or found; GP3b's start
        self.pilot_ok, self.pilot_pieces = {}, {}               # verified pilot range seals; slot -> pieces' sums
        self.pilot_off = {k: 0 for k in self.h["slots"]}         # GP1 (b): the next offer wire copy to look for
        self.pj = {k: [0, b"", []] for k in self.h["slots"]}     # each journal: bytes read, a cut tail, pilot lines
        self.pt = [0, b"", []]                                  # out/PACKER_TIMES.jsonl: the same, its records

    # ---- the log ------------------------------------------------------------------------------------------------
    def say(self, text: str, alarm: bool = False) -> None:
        line = f"{T(time.time())} {'ALARM ' if alarm else ''}{text}\n".encode("ascii", "replace")
        if alarm or self.log.tell() < LOG_CAP:
            self.log.write(line)
            self.log.flush()
        if alarm:
            print(line.decode("ascii").rstrip(), flush=True)

    def alarm(self, key: str, text: str) -> None:
        """An alarm is written when it is new or its text changed; clear() lets the same one be written again."""
        if self.alarms.get(key) != text:
            self.alarms[key] = text
            self.n_alarms += 1
            self.say(text, alarm=True)

    def clear(self, key: str) -> None:
        self.alarms.pop(key, None)

    # ---- G1: the header, the policy, the schedules ----------------------------------------------------------------
    def load_header(self) -> None:
        data = (self.root / "RUN.json").read_bytes()
        try:
            h = parse_canon(data, "RUN.json")
        except ValueError as e:
            raise Stop(4, str(e)) from None
        if not isinstance(h, dict) or any(k not in h for k in HEADER_KEYS) or h["schema"] != 2:
            raise Stop(4, "RUN.json: not a header of FORMATS 1.1 (schema 2 and its keys)")
        slots = h["slots"]
        if not (isinstance(slots, list) and slots and all(type(s) is int and 0 <= s <= 999 for s in slots)
                and all(x < y for x, y in zip(slots, slots[1:]))):
            raise Stop(4, "RUN.json: slots is a rising list of integers 0 to 999")
        if type(h["piece_games"]) is not int or h["piece_games"] < 1:
            raise Stop(4, "RUN.json: piece_games is an integer >= 1")
        check_rows(h["pilot_ranges"], slots, 0, "RUN.json pilot_ranges")
        if any(r["schedule"] != 0 for r in h["pilot_ranges"]):
            raise Stop(4, "RUN.json: a pilot range carries a schedule number other than 0")
        self.h, self.fp = h, sha256_bytes(data)
        self.hard = utc(h["hard_cutoff_utc"], "RUN.json hard_cutoff_utc")
        self.lease_start = utc(h["lease_start_utc"], "RUN.json lease_start_utc")

    def load_policy(self) -> None:
        data = Path(self.a.policy).read_bytes()
        try:
            pol = json.loads(data.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_not_int)
        except ValueError as e:
            raise Stop(4, f"the policy file is not json without a key twice or a NaN ({e})") from None
        oc = pol.get("owner_choice") if isinstance(pol, dict) else None
        if not isinstance(oc, dict) or not isinstance(oc.get("name"), str):
            raise Stop(4, "the policy file: an owner_choice object with a name (the budget tool's plan.json)")
        if type(pol.get("target_rows")) is not int or pol["target_rows"] < 1:
            raise Stop(4, "the policy file: target_rows an integer >= 1 (the cap of every schedule's scope)")
        pilot = max(r["round"] for r in self.h["pilot_ranges"])
        if not same(pol.get("pilot_rounds_declared"), pilot):
            raise Stop(4, f"the policy file declares {str(pol.get('pilot_rounds_declared'))[:20]} pilot rounds and the "
                          f"header's pilot has {pilot} (Astra 225517Z: the cohort is the policy's)")
        self.policy, self.policy_sha = pol, sha256_bytes(data)

    def load_schedules(self) -> None:
        names = [p.name for p in self.root.glob("SCHEDULE.*.json")]
        if any(not re.fullmatch(r"SCHEDULE\.[1-9][0-9]{0,2}\.json", x) for x in names):
            raise Stop(4, f"a schedule file name outside the grammar: {sorted(names)[:5]}")
        self.sched = []                 # (bytes, record) of SCHEDULE.1 ... n
        for k in range(1, len(names) + 1):
            p = self.root / f"SCHEDULE.{k}.json"
            if not p.exists():
                raise Stop(4, f"there are {len(names)} schedules and SCHEDULE.{k}.json is not one of them")
            self.follow(k, p.read_bytes())

    def follow(self, k: int, data: bytes) -> None:
        """Schedule k against the one before (1.2; the worker's own rules but the started ranges): kept, its bounds
        to the clocks."""
        name = f"SCHEDULE.{k}.json"
        try:
            s = parse_canon(data, name)
        except ValueError as e:
            raise Stop(4, str(e)) from None
        prev = "first" if k == 1 else sha256_bytes(self.sched[-1][0])
        if not isinstance(s, dict) or sorted(s) != SCHEDULE_KEYS or s["schema"] != 2 or s["n"] != k \
                or s["run_fingerprint"] != self.fp or s["prev"] != prev or not HEX64.fullmatch(str(s["evidence"])):
            raise Stop(4, f"{name}: not schedule {k} of this run (schema, n, run_fingerprint, prev, evidence)")
        c2, d2 = utc(s["cutoff_utc"], name), utc(s["dispatch_end_utc"], name)
        cut, disp = self.bounds_in_force()
        if not d2 <= c2 <= cut or d2 > disp:
            raise Stop(4, f"{name}: a cutoff or dispatch end later than the one before, or after its own cutoff")
        check_rows(s["ranges"], self.h["slots"], k, name)
        before = {(r["slot"], r["round"]): r for r in self.rows()}
        now = {(r["slot"], r["round"]): r for r in s["ranges"]}
        for key, r in before.items():
            q = now.get(key)
            if q is None or q["first"] != r["first"] or q["last"] > r["last"]:
                raise Stop(4, f"{name}: the range of round {key[1]} of slot {key[0]} is removed, moved or lengthened")
        self.sched.append((data, s))
        self.B.set("cutoff", c2)
        self.B.set("dispatch_end", min(d2, c2))

    def rows(self) -> list:
        return self.sched[-1][1]["ranges"] if self.sched else self.h["pilot_ranges"]

    def bounds_in_force(self):
        if not self.sched:
            return self.hard, self.hard
        s = self.sched[-1][1]
        return utc(s["cutoff_utc"], "schedule"), utc(s["dispatch_end_utc"], "schedule")

    def d_text(self) -> str:
        return self.sched[-1][1]["cutoff_utc"] if self.sched else self.h["hard_cutoff_utc"]

    def state(self, r=None) -> str:
        """play | dispatch_end | cutoff | hold, by all three clocks (the worker's clock_state). r: a reading the caller
        took (one_pass: the same reading gives CLOCK.json's utc_ms); without one, it is taken here."""
        r = r if r is not None else self.B.clocks.read()
        vd = self.B.judge("dispatch_end", reading=r)[0]
        vc = self.B.judge("cutoff", reading=r)[0]
        if cw.HOLD in (vd, vc):
            return "hold"
        if vc == cw.COME:
            return "cutoff"
        return "dispatch_end" if vd == cw.COME else "play"

    # ---- G11: the clock file (v16) -------------------------------------------------------------------------------
    def clock_start(self) -> int:
        """G4: the n of ROOT/CLOCK.json when it is this run's clock record (the next write is n + 1); else 0, so the
        next write is 1 (another run's file, or one that is not the record, is replaced by it)."""
        try:
            c = parse_canon((self.root / "CLOCK.json").read_bytes(), "CLOCK.json")
        except FileNotFoundError:
            return 0
        except (OSError, ValueError) as e:
            self.say(f"CLOCK.json is not read ({e}): it is written again, n begins at 1")
            return 0
        if (isinstance(c, dict) and sorted(c) == CLOCK_KEYS and same(c["schema"], 1)
                and c["run_fingerprint"] == self.fp and type(c["n"]) is int and c["n"] >= 1):
            return c["n"]
        self.say("CLOCK.json is not this run's clock record: it is written again, n begins at 1")
        return 0

    def clock_utc_ms(self, r) -> int:
        """G1': the guard's time by its three clocks at ONE reading, the EARLIEST of UTC, anchor + steady run and
        anchor + boot run, in whole milliseconds rounded down (the furthest BEHIND: home decides late, never early).
        v17: the rule lives in clockwatch.Bounds.earliest_ms, the worker's t0_ms (C-R1) uses the same."""
        return self.B.earliest_ms(r)

    def write_clock(self, r, st: str) -> None:
        """G11: ROOT/CLOCK.json, whole, at most once every clock_every seconds of the steady clock (r[1]), in every
        state; a failed write is the ALARM clock and is tried again at the next pass."""
        if self.clock_at is not None and r[1] - self.clock_at < self.clock_every:
            return
        rec = canon({"n": self.clock_n + 1, "run_fingerprint": self.fp, "schema": 1, "state": st,
                     "utc_ms": self.clock_utc_ms(r)})
        tmp = self.root / f".CLOCK.json.{os.getpid()}.part"
        try:
            try:
                tmp.unlink()                            # this guard's own scratch name, left by a crash
            except FileNotFoundError:
                pass
            with open(tmp, "xb") as f:
                f.write(rec)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, self.root / "CLOCK.json")
        except OSError as e:
            self.alarm("clock", f"CLOCK.json not written: {e}")
            return
        self.clear("clock")
        self.clock_n += 1
        self.clock_at = r[1]

    # ---- G12: the pilot's record (v17) ----------------------------------------------------------------------------
    def pilot_pass(self, r) -> None:
        """G12: ROOT/PILOT.json once (GP1, GP4); a fault is the ALARM pilot and nothing else (GP9: never a stop)."""
        if self.pilot_done:
            return
        p = self.root / "PILOT.json"
        try:
            if p.exists():                              # GP4: written before (a restarted guard): never again
                self.pilot_done = True
                why = self.pilot_file_fault(p)
                if why:
                    self.alarm("pilot", f"PILOT.json {why}: it is kept as it is and not written again")
                return
            why, rec = self.pilot_record(r)
            if rec is None:
                if why:
                    self.alarm("pilot", f"PILOT.json not written: {why}")
                return
            data = canon(rec)
            create_only(p, data)
        except Exception as e:  # noqa: BLE001   GP9: the ALARM, tried again at the next pass; the day goes on
            self.alarm("pilot", f"PILOT.json not written: {type(e).__name__}: {str(e)[:300]}")
            return
        self.pilot_done = True
        self.clear("pilot")
        self.say(f"PILOT.json written ({sha256_bytes(data)[:12]}): slots {len(rec['slots'])}, rounds {rec['rounds']}, "
                 f"packer {rec['packer']}")

    def pilot_file_fault(self, p: Path) -> str:
        """GP4: '' when ROOT/PILOT.json is canonical and this run's (schema 1, run_fingerprint), else why not."""
        try:
            rec = parse_canon(p.read_bytes(), "PILOT.json")
        except OSError as e:
            return f"cannot be read ({e})"
        except ValueError as e:
            return f"is not canonical ({e})"
        if not (isinstance(rec, dict) and same(rec.get("schema"), 1) and rec.get("run_fingerprint") == self.fp):
            return "is not this run's (schema 1, run_fingerprint)"
        return ""

    def pilot_record(self, r):
        """GP1 to GP3d: ('', None) not yet, no alarm; (why, None) GP3's alarm; ('', the record) to be written."""
        prows = self.h["pilot_ranges"]
        mine = {k: sorted((x for x in prows if x["slot"] == k), key=lambda x: x["round"]) for k in self.h["slots"]}
        seals, top = {}, {}
        for k in self.h["slots"]:                       # GP1 (a): this run's range seal of every pilot row
            seals[k] = []
            for row in mine[k]:
                f = self.root / "ranges" / f"r{row['round']:04d}.w{k:03d}.seal.json"
                try:
                    st = f.stat()
                except OSError:
                    return "", None
                stamp = (st.st_size, st.st_mtime_ns, st.st_ino)
                got = self.pilot_ok.get((k, row["round"]))
                if got is None or got[0] != stamp:
                    if self.range_fault(f, k, row["round"], row) is not None:
                        return "", None                 # R5 names such a seal (sealed_rounds); it is not counted
                    got = self.pilot_ok[(k, row["round"])] = (stamp, parse_canon(f.read_bytes(), f.name))
                seals[k].append(got[1])
            top[k] = max([s["through_index"] for s in seals[k]], default=-1)
        for k in self.h["slots"]:                       # GP1 (b): every pilot piece's offer wire copy
            while self.pilot_off[k] <= top[k]:
                if not (self.root / "out" / f"w{k:03d}" / f"p{self.pilot_off[k]:06d}.offer.json.zz").exists():
                    return "", None
                self.pilot_off[k] += 1
        if self.pilot_ready_at is None:
            self.pilot_ready_at = r[1]
        utc = self.clock_utc_ms(r)
        slots = []
        for k in self.h["slots"]:
            why, s = self.pilot_slot(k, mine[k], seals[k], top[k], utc)
            if s is None:
                return why, None
            slots.append(s)
        why, packer = self.pilot_packer(r, top)
        if packer is None:
            return why, None
        return "", {"packer": packer, "rounds": sorted({x["round"] for x in prows}), "run_fingerprint": self.fp,
                    "schema": 1, "slots": slots}

    def pilot_slot(self, k: int, mine: list, seals: list, top: int, utc: int):
        """GP2 and GP3 for slot k: (why, its values), why '' or the values None."""
        got = self.pilot_pieces.get(k)
        if got is None or got[0] != top:                # the piece seals 0 to T_k by R4's rule, with rows and epoch
            games = rows = 0
            epochs, prev = set(), self.genesis(k)
            for i in range(top + 1):
                p = self.root / f"w{k:03d}" / "closed" / f"p{i:06d}.seal.json"
                try:
                    data = p.read_bytes()
                    s = parse_canon(data, p.name)
                except (OSError, ValueError) as e:
                    return f"slot {k}: w{k:03d}/closed/{p.name} cannot be read ({e})", None
                if not (isinstance(s, dict) and same(s.get("schema"), 2) and s.get("run_fingerprint") == self.fp
                        and same(s.get("slot"), k) and same(s.get("index"), i) and s.get("prev_seal") == prev
                        and type(s.get("games")) is int and s["games"] >= 1 and type(s.get("rows")) is int
                        and s["rows"] >= 0 and type(s.get("epoch")) is int and s["epoch"] >= 1):
                    return (f"slot {k}: w{k:03d}/closed/{p.name} is not this run's seal {i} of the slot (schema, "
                            f"run_fingerprint, slot, index, prev_seal, games, rows, epoch)"), None
                games, rows, prev = games + s["games"], rows + s["rows"], sha256_bytes(data)
                epochs.add(s["epoch"])
            got = self.pilot_pieces[k] = (top, games, rows, sorted(epochs))
        games, rows, epochs = got[1:]
        lines = self.pilot_lines(k, mine)
        for x in lines:
            if not (type(x.get("t0_ms")) is int and x["t0_ms"] >= 0 and type(x.get("ms")) is int and x["ms"] >= 0):
                return f"slot {k}: the pilot game {x.get('game')} has no t0_ms or ms (a journal line of v16's form)", None
            if x["t"] == "done" and not (type(x.get("rows")) is int and x["rows"] >= 0):
                return f"slot {k}: the pilot game {x.get('game')} has no rows", None
        rg = sum(s["games"] for s in seals) if all(type(s.get("games")) is int for s in seals) else None
        if not len(lines) == rg == games:
            return (f"slot {k}: the journal holds {len(lines)} pilot games, the pilot range seals {rg}, the piece "
                    f"seals 0 to {top} {games}"), None
        nxt = 0
        for s in seals:                                 # the first_index chain: pieces 0 to T_k, the pilot's alone
            fi, ti = s.get("first_index"), s["through_index"]
            if same(fi, -1) and same(ti, -1):
                continue
            if not (same(fi, nxt) and type(ti) is int and ti >= fi):
                return (f"slot {k}: the pilot range seal of round {s.get('round')} begins at piece {fi}, not {nxt} (the "
                        f"pilot's pieces are 0 to {top}, in round order)"), None
            nxt = ti + 1
        done_rows = sum(x["rows"] for x in lines if x["t"] == "done")
        if done_rows != rows:
            return f"slot {k}: the done lines' rows sum to {done_rows}, the piece seals 0 to {top} hold {rows}", None
        if not epochs:
            return f"slot {k}: no pilot piece (home's R3 needs the slot's epochs)", None
        first, last = min(x["t0_ms"] for x in lines), max(x["t0_ms"] + x["ms"] for x in lines)
        if last > utc:
            return f"slot {k}: its last pilot game ends at {last} ms, after the guard's clock {utc} (GP3d)", None
        return "", {"epochs": epochs, "first_t0_ms": first, "games": len(lines), "last_end_ms": last,
                    "longest_ms": max(x["ms"] for x in lines), "play_ms": sum(x["ms"] for x in lines),
                    "raw_rows": rows, "slot": k, "span_ms": last - first}

    def pilot_lines(self, k: int, mine: list) -> list:
        """GP2: the slot's done and noselfgame lines (complete, canonical) whose game lies in one of its pilot rows,
        from w<k>/journal.txt read incrementally (only the bytes new since the last pass; a cut last line waits)."""
        st = self.pj[k]
        new = self.tail_read(self.root / f"w{k:03d}" / "journal.txt", st)
        pre = f"{self.h['run']}-w{k:03d}-g"
        for line in new:
            try:
                x = parse_canon(line, "journal line")
            except ValueError:
                continue                                # a line that is no record: the count check names the slot
            if not (isinstance(x, dict) and x.get("t") in ("done", "noselfgame") and isinstance(x.get("game"), str)
                    and x["game"].startswith(pre) and GAME_NO.fullmatch(x["game"][len(pre):])):
                continue
            c = int(x["game"][len(pre):])
            if any(row["first"] <= c <= row["last"] for row in mine):
                st[2].append(x)
        return st[2]

    @staticmethod
    def tail_read(path: Path, st: list) -> list:
        """The complete lines appended to path since st = [bytes read, cut tail, ...] was last read (st is updated);
        a file that shrank is read again from its start (st[2] emptied)."""
        try:
            size = path.stat().st_size
        except FileNotFoundError:
            size = 0
        if size < st[0]:
            st[:] = [0, b"", []]
        if size == st[0]:
            return []
        with open(path, "rb") as f:
            f.seek(st[0])
            chunk = f.read(size - st[0])
        st[0] += len(chunk)
        data = st[1] + chunk
        cut = data.rfind(b"\n") + 1
        st[1] = data[cut:]
        return data[:cut].splitlines(keepends=True)

    def pilot_packer(self, r, top: dict):
        """GP2's packer values from the complete exact lines of out/PACKER_TIMES.jsonl, GP3's packer checks, GP3b and
        GP3c: (why, the values), why '' or the values None."""
        st = self.pt
        st[2].extend(times_rec(line) for line in self.tail_read(self.root / "out" / "PACKER_TIMES.jsonl", st))
        lines = st[2]
        if not lines or lines[0] != {"t": "start"}:      # GP3c (no start line would give restarted -1)
            return "the packer's times file out/PACKER_TIMES.jsonl does not begin with a start line", None
        starts = sum(1 for x in lines if x == {"t": "start"})
        seen = {}
        for x in lines:
            if x is not None and x["t"] == "offered" and x["slot"] in top and x["index"] <= top[x["slot"]]:
                if (x["slot"], x["index"]) in seen:
                    return (f"the packer's times file holds two offered lines for slot {x['slot']} piece "
                            f"{x['index']}"), None
                seen[(x["slot"], x["index"])] = x
        missing = [(k, i) for k in self.h["slots"] for i in range(top[k] + 1) if (k, i) not in seen]
        if missing and starts == 1:                     # restarted 0: C-R2 does not explain a missing line
            if r[1] - self.pilot_ready_at < GP3B_WAIT:
                return "", None                         # GP3b: the line follows its wire copy
            return (f"the packer's times file holds no offered line for slot {missing[0][0]} piece {missing[0][1]} "
                    f"({len(missing)} pilot pieces without one; restarted 0; {GP3B_WAIT:.0f} s after the pilot's "
                    f"offers stood)"), None
        return "", {"busy_ms": sum(x["ms"] for x in seen.values()), "pieces": len(seen),
                    "raw_rows": sum(x["raw_rows"] for x in seen.values()), "restarted": starts - 1}

    # ---- G3: the control record --------------------------------------------------------------------------------
    def check_control(self, k: int, data: bytes, evidence: bytes, replay: bool):
        """(record, effect, report) or Held (the reason)."""
        try:
            c = parse_canon(data, f"CONTROL.{k}.json")
        except ValueError as e:
            raise Held(str(e)) from None
        if not isinstance(c, dict) or sorted(c) != CONTROL_KEYS:
            raise Held(f"CONTROL.{k}.json: not the keys of a control record (FORMATS 1.2)")
        prev = "first" if k == 1 else sha256_bytes(self.ctl[k - 2][0])
        if c["schema"] != 2 or c["k"] != k or c["run_fingerprint"] != self.fp:
            raise Held(f"CONTROL.{k}.json: schema 2, k {k} and this run's fingerprint")
        if c["prev"] != prev:
            raise Held(f"CONTROL.{k}.json: prev does not link to the accepted control {k - 1}")
        if c["kind"] not in KINDS:
            raise Held(f"CONTROL.{k}.json: kind {str(c['kind'])[:40]} is none of {', '.join(KINDS)}")
        if not HEX64.fullmatch(str(c["evidence"])) or sha256_bytes(evidence) != c["evidence"]:
            raise Held(f"CONTROL.{k}.json: the evidence file does not have the sha256 the record names")
        try:
            rep = parse_canon(evidence, "the evidence")
        except ValueError as e:
            raise Held(str(e)) from None
        if not isinstance(rep, dict):
            raise Held("the evidence is not a record")
        if "local_only" in rep:
            raise Held("the evidence carries local_only: the full local report never travels, only its public part "
                       "(Astra 172109Z)")
        if c["owner_policy"] != self.policy_sha:
            raise Held(f"CONTROL.{k}.json: owner_policy is not the package's policy")
        if (not isinstance(rep.get("inputs"), dict)
                or rep["inputs"].get("plan_sha256") != self.policy_sha):
            raise Held(f"CONTROL.{k}.json: the report was not computed from the package's policy file "
                       f"(inputs.plan_sha256)")
        try:
            cut, disp = utc(c["cutoff_utc"], "cutoff_utc"), utc(c["dispatch_end_utc"], "dispatch_end_utc")
            utc(c["at_utc"], "at_utc")
        except Stop as e:
            raise Held(f"CONTROL.{k}.json: {e}") from None
        if disp > cut:
            raise Held(f"CONTROL.{k}.json: the dispatch end is after the cutoff")
        if not replay:
            c_in, d_in = self.bounds_in_force()
            if cut > c_in or disp > d_in:
                raise Held(f"CONTROL.{k}.json: a bound later than the one in force ({self.d_text()})")
        if c["kind"] in ("pilot_decision", "target") and (c["decision"] not in OUTCOMES
                                                         or rep.get("outcome") != c["decision"]):
            raise Held(f"CONTROL.{k}.json: decision {str(c['decision'])[:40]} is not the report's outcome "
                       f"{str(rep.get('outcome'))[:40]}")
        if c["kind"] == "matches" and c["decision"] != rep.get("matches"):
            raise Held(f"CONTROL.{k}.json: the pairs are not the report's matches")
        eff = self.effect(k, c, rep)
        if eff == "schedule":
            fl = (rep.get("cutoff_floor_s"), rep.get("dispatch_end_floor_s"))
            if any(type(x) is not int for x in fl):
                raise Held("the report has no whole cutoff_floor_s and dispatch_end_floor_s")
            if (c["cutoff_utc"], c["dispatch_end_utc"]) != (T(self.lease_start + fl[0]), T(self.lease_start + fl[1])):
                raise Held(f"CONTROL.{k}.json: the bounds are not the report's whole seconds after the lease start")
        return c, eff, rep

    def effect(self, k: int, c: dict, rep: dict) -> str:
        """G3 f: "schedule", "fence" or "none", from the record's kind, the report's outcome and the policy."""
        cap = None
        if c["kind"] == "fence":
            eff = "fence"
        elif c["kind"] == "matches":
            eff = "none"
        elif c["decision"] == "UNQUALIFIED":
            eff = "none"
        elif c["decision"] in ("REACHED", "STOP", "SHORT"):
            eff = "fence"
        elif c["decision"] in ("SELF_PLAY", "SELF_PLAY_AND_MATCHES"):
            eff = "schedule"
        else:                                           # OWNER_CHOICE: the hashed policy alone decides
            oc = self.policy["owner_choice"]
            act = oc.get("action")
            if act == "stop":
                eff = "fence"
            elif act == "self_play":                    # F2: the owner's 1A, as many rows as fit (the full target)
                eff = "schedule"
            elif act == "reduced_target":
                cap, red = oc.get("reduced_target_rows"), rep.get("reduced")
                if type(cap) is not int or not isinstance(red, dict) or red.get("target_rows") != cap \
                        or type(red.get("covered")) is not bool:
                    raise Held(f"CONTROL.{k}.json: the report's reduced target is not the policy's "
                               f"reduced_target_rows {cap}")
                if red["covered"]:
                    eff = "schedule"
                elif oc.get("if_uncovered") == "stop":
                    eff = "fence"
                elif oc.get("if_uncovered") == "self_play":
                    eff = "schedule"
                else:
                    raise Held(f"CONTROL.{k}.json: OWNER_CHOICE with an uncovered reduced target, and the policy "
                               f"names no action for it (owner_choice.if_uncovered): no new production")
            else:
                raise Held(f"CONTROL.{k}.json: OWNER_CHOICE, and the policy's action {str(act)[:40]} is not one "
                           f"the guard knows: no new production")
        sc = c["scope"]
        if eff == "schedule":
            if not (isinstance(sc, dict) and sorted(sc) == ["highest_round", "target_rows"]
                    and type(sc["highest_round"]) is int and type(sc["target_rows"]) is int
                    and sc["highest_round"] <= 9999 and sc["target_rows"] >= 1):
                raise Held(f"CONTROL.{k}.json: a schedule needs scope {{highest_round, target_rows}}")
            limit = cap if cap is not None else self.policy.get("target_rows")
            if type(limit) is int and sc["target_rows"] > limit:
                raise Held(f"CONTROL.{k}.json: the scope names more rows ({sc['target_rows']}) than the target "
                           f"{limit} of the policy (a target changes only by a new policy)")
        elif sc is not None:
            raise Held(f"CONTROL.{k}.json: scope must be null when nothing is scheduled")
        return eff

    def take_controls(self) -> None:
        """G3, at every pass before the end."""
        for k, (data, _, _) in enumerate(self.ctl, 1):
            p = self.inbox / f"CONTROL.{k}.json.zz"
            try:
                same = unzz(p) == data if p.exists() else True
            except (OSError, ValueError):
                same = False
            if not same:
                self.alarm(f"conflict{k}", f"inbox/CONTROL.{k}.json.zz holds other bytes than the accepted control "
                                           f"{k}: HELD, the accepted one stays")
        k = len(self.ctl) + 1
        p = self.inbox / f"CONTROL.{k}.json.zz"
        if k > 999999999 or not p.exists():
            return
        try:
            data = unzz(p)
            try:
                ev_name = parse_canon(data, p.name).get("evidence")
            except (ValueError, AttributeError) as e:
                raise Held(f"{p.name}: {e}") from None
            if not HEX64.fullmatch(str(ev_name)):
                raise Held(f"{p.name}: evidence is not a sha256")
            ep = self.inbox / f"EVIDENCE.{ev_name}.json.zz"
            if not ep.exists():
                raise Held(f"{p.name}: its evidence file EVIDENCE.{ev_name[:12]}... is not there (it travels first)")
            evidence = unzz(ep)
            c, eff, _ = self.check_control(k, data, evidence, replay=False)
            sched = None
            if eff == "schedule":
                top = max(r["round"] for r in self.rows())
                if c["scope"]["highest_round"] <= top:
                    raise Held(f"{p.name}: the scope's highest round {c['scope']['highest_round']} is not above the "
                               f"rounds scheduled ({top})")
                sched = self.new_schedule(sha256_bytes(data), min(top + self.a.horizon, c["scope"]["highest_round"]),
                                          c["cutoff_utc"], c["dispatch_end_utc"])
                ok, why = self.room(sched)
                if not ok:
                    raise Held(f"{p.name}: {why}")
        except Held as e:
            self.alarm("control", f"control {k} HELD: {e}")
            return
        except (OSError, ValueError) as e:
            self.alarm("control", f"control {k} HELD: {e}")
            return
        self.clear("control")
        self.cdir.mkdir(exist_ok=True)
        create_only(self.cdir / f"EVIDENCE.{c['evidence']}.json", evidence)
        create_only(self.cdir / f"CONTROL.{k}.json", data)
        self.ctl.append((data, c, eff))
        self.say(f"control {k} accepted ({sha256_bytes(data)}): kind {c['kind']}, decision "
                 f"{str(c['decision'])[:60]}, effect {eff}")
        self.make_effect(k, sched)

    def make_effect(self, k: int, sched=None) -> None:
        data, c, eff = self.ctl[k - 1]
        csha = sha256_bytes(data)
        if eff == "schedule":
            if sched is None:                           # the owed effect after a restart: G5 like every schedule
                top = max(r["round"] for r in self.rows())
                sched = self.new_schedule(csha, min(top + self.a.horizon, c["scope"]["highest_round"]),
                                          c["cutoff_utc"], c["dispatch_end_utc"])
                ok, why = self.room(sched)
                if not ok:
                    raise Held(f"the owed schedule: {why}")
            self.write_schedule(sched)
        elif eff == "fence":
            self.fence(f"control {k} {csha}: {c['kind']} {str(c['decision'])[:60]}")
        if c["kind"] == "matches" or c["decision"] == "SELF_PLAY_AND_MATCHES":
            self.alarm(f"matches{k}", f"control {k} assigns matches: this package has no match runner, none is played")

    def replay_controls(self) -> None:
        """G3 at start (Astra 171332Z): the accepted controls are the chain, never the schedules."""
        names = [p.name for p in self.cdir.glob("CONTROL.*.json")] if self.cdir.is_dir() else []
        if any(not re.fullmatch(r"CONTROL\.[1-9][0-9]{0,8}\.json", x) for x in names):
            raise Stop(4, f"control/: a file name outside the grammar: {sorted(names)[:5]}")
        for k in range(1, len(names) + 1):
            p = self.cdir / f"CONTROL.{k}.json"
            if not p.exists():
                raise Stop(4, f"control/: there are {len(names)} accepted controls and CONTROL.{k}.json is missing")
            data = p.read_bytes()
            try:
                ev = parse_canon(data, p.name).get("evidence")
                if not HEX64.fullmatch(str(ev)):
                    raise Held("evidence is not a sha256")
                c, eff, _ = self.check_control(k, data, (self.cdir / f"EVIDENCE.{ev}.json").read_bytes(), True)
            except (Held, ValueError, AttributeError, OSError) as e:
                raise Stop(4, f"the accepted control {k} does not hold any more: {e}") from None
            self.ctl.append((data, c, eff))
            csha = sha256_bytes(data)
            found = (eff == "none" or (eff == "schedule" and any(s["evidence"] == csha for _, s in self.sched))
                     or (eff == "fence" and self.fence_names(csha)))
            if not found:
                if k != len(names):
                    raise Stop(4, f"the accepted control {k} has no {eff} and a later control was accepted after it")
                self.say(f"replay: the {eff} of the accepted control {k} is owed (a stop came in between): it is made "
                         f"at the first pass that may act")
                self.pending = k
        if self.ctl:
            self.say(f"replay: {len(self.ctl)} accepted control(s), the next is {len(self.ctl) + 1}")

    # ---- G4, G5: the schedules and the room ------------------------------------------------------------------
    def new_schedule(self, evidence: str, upto: int, cut_text: str, disp_text: str) -> bytes:
        rows, n = list(self.rows()), len(self.sched) + 1
        if n > 999:                                     # G-A (Fable 25 Nov): every program's grammar ends at 999
            raise Held(f"the schedule chain ends at SCHEDULE.999.json (the grammar of the worker, packer, terminal, "
                       f"fetch and credit): no schedule {n}; the day goes on in the rows of the last one")
        top = max(r["round"] for r in rows)
        for rnd in range(top + 1, upto + 1):
            for k in self.h["slots"]:
                mine = [r for r in rows if r["slot"] == k]
                if not mine:
                    continue
                hi = max(mine, key=lambda r: r["round"])
                first = hi["last"] + 1
                last = first + hi["last"] - hi["first"]
                if last > 99999999:
                    raise Held(f"slot {k}: round {rnd} would pass counter 99,999,999")
                rows.append({"first": first, "last": last, "round": rnd, "schedule": n, "short": False, "slot": k})
        return canon({"cutoff_utc": cut_text, "dispatch_end_utc": disp_text, "evidence": evidence, "n": n,
                      "prev": "first" if n == 1 else sha256_bytes(self.sched[-1][0]), "ranges": rows,
                      "run_fingerprint": self.fp, "schema": 2})

    def write_schedule(self, data: bytes) -> None:
        n = len(self.sched) + 1
        before = len(self.sched)
        self.follow(n, data)                            # the guard's own bytes pass the chain's rules first
        try:
            create_only(self.root / f"SCHEDULE.{n}.json", data)
        except BaseException:
            del self.sched[before:]
            raise
        s = self.sched[-1][1]
        self.say(f"SCHEDULE.{n}.json written: rounds up to {max(r['round'] for r in s['ranges'])}, cutoff "
                 f"{s['cutoff_utc']}, dispatch end {s['dispatch_end_utc']}, evidence {s['evidence'][:12]}")

    def genesis(self, k: int) -> str:
        return f"genesis:{self.fp}:w{k:03d}"

    def sealed_rounds(self) -> set:
        """R5: (slot, round) of every range seal that is this run's seal of the newest schedule's row (a verified
        file is not read again while its size, time and inode stay)."""
        d = self.root / "ranges"
        if not d.is_dir():
            return set()
        rows = {(r["slot"], r["round"]): r for r in self.rows()}
        out = set()
        for f in os.scandir(d):
            m = RANGE_SEAL.fullmatch(f.name)
            if not m:
                continue
            key = (int(m.group(2)), int(m.group(1)))
            try:
                st = f.stat()
                stamp = (st.st_size, st.st_mtime_ns, st.st_ino)
            except OSError:
                continue
            if self.range_ok.get(key) != stamp:
                why = self.range_fault(Path(f.path), key[0], key[1], rows.get(key))
                if why:
                    self.range_ok.pop(key, None)
                    self.alarm(f"range{key[0]}.{key[1]}", f"ranges/{f.name} {why}: not counted as sealed (no "
                                                          f"extension rests on it, its games count as unplayed)")
                    continue
                self.range_ok[key] = stamp
                self.clear(f"range{key[0]}.{key[1]}")
            out.add(key)
        return out

    def range_fault(self, p: Path, k: int, rnd: int, row):
        """None when the range seal at p is this run's seal of the schedule row `row` (R5), else why not."""
        if row is None:
            return "names a range the newest schedule does not hold"
        try:
            s = parse_canon(p.read_bytes(), p.name)
        except (OSError, ValueError) as e:
            return f"cannot be read as a record ({e})"
        if not isinstance(s, dict) or s.get("schema") != 2 or s.get("run_fingerprint") != self.fp:
            return "is not this run's (schema 2, run_fingerprint)"
        if not (same(s.get("slot"), k) and same(s.get("round"), rnd) and same(s.get("first"), row["first"])
                and same(s.get("last"), row["last"])):
            return "is not the seal of its schedule row (slot, round, first, last)"
        ti, ts = s.get("through_index"), s.get("through_seal")
        if same(ti, -1):
            return None if ts is None else "holds no piece and names a through_seal"
        if type(ti) is not int or ti < 0:
            return "has no through_index"
        try:
            ok = sha256_bytes((self.root / f"w{k:03d}" / "closed" / f"p{ti:06d}.seal.json").read_bytes()) == ts
        except OSError:
            return f"names piece {ti}, whose seal is not in w{k:03d}/closed"
        return None if ok else f"names a through_seal that is not the sha256 of piece {ti}'s seal"

    def read_seals(self) -> None:
        """R4: the pieces of the room test, each this run's seal of its slot, index and chain."""
        for k in self.h["slots"]:
            closed = self.root / f"w{k:03d}" / "closed"
            while True:
                i = self.seal_next[k]
                p = closed / f"p{i:06d}.seal.json"
                try:
                    data = p.read_bytes()
                except OSError:
                    break
                try:
                    s = parse_canon(data, p.name)
                except ValueError:
                    s = None
                if not (isinstance(s, dict) and s.get("schema") == 2 and s.get("run_fingerprint") == self.fp
                        and same(s.get("slot"), k) and same(s.get("index"), i)
                        and s.get("prev_seal") == self.seal_prev[k]
                        and type(s.get("games")) is int and s["games"] >= 1
                        and type(s.get("raw_bytes")) is int and s["raw_bytes"] >= 0):
                    self.alarm(f"seal{k}", f"w{k:03d}/closed/{p.name} is not this run's seal {i} of slot {k} (schema, "
                                           f"run_fingerprint, slot, index, prev_seal, games, raw_bytes): not counted, "
                                           f"the slot's later seals neither")
                    break
                self.clear(f"seal{k}")
                self.games_total += s["games"]
                self.raw_total += s["raw_bytes"]
                self.pieces_total += 1
                self.seal_prev[k] = sha256_bytes(data)
                self.seal_next[k] += 1

    def room(self, data: bytes):
        """G5: (True, "") or (False, why)."""
        self.read_seals()
        if self.games_total == 0:
            return False, "room: no sealed piece yet, the bytes of a game are not measured"
        s = parse_canon(data, "the new schedule")
        sealed = self.sealed_rounds()
        unplayed = sum(r["last"] - r["first"] + 1 for r in s["ranges"] if (r["slot"], r["round"]) not in sealed)
        per_game = math.ceil(2 * (self.raw_total + self.pieces_total * 32768) / self.games_total)
        hist = sum(len(d) for d, _ in self.sched) + len(data)
        need = (unplayed * per_game + len(s["ranges"]) * CLOSE_ROW_BYTES + 2 * hist
                + 3 * (-(-len(data) // 4096) * 4096) + (1 << 20))
        free = shutil.disk_usage(self.root).free
        if free - need < self.a.floor_bytes:
            return False, (f"room: {free} bytes free, the schedule needs {need} ({unplayed} games not played at "
                           f"{per_game} bytes, {len(s['ranges'])} rows to close) above the floor {self.a.floor_bytes}")
        return True, ""

    def authority(self):
        """The latest accepted control of kind pilot_decision or target, when its effect was a schedule."""
        for data, c, eff in reversed(self.ctl):
            if c["kind"] in ("pilot_decision", "target"):
                return (sha256_bytes(data), c) if eff == "schedule" else None
        return None

    def extend(self) -> None:
        """G4: the rolling extension."""
        auth = self.authority()
        if auth is None or not self.sched:
            return
        csha, c = auth
        rows = self.rows()
        top = max(r["round"] for r in rows)
        if top + 1 > c["scope"]["highest_round"]:
            return
        sealed = self.sealed_rounds()
        if not any(rnd >= top - self.a.horizon + 1 for _, rnd in sealed):
            return
        s = self.sched[-1][1]
        try:
            data = self.new_schedule(csha, top + 1, s["cutoff_utc"], s["dispatch_end_utc"])
        except Held as e:
            self.alarm("extend", f"no extension: {e}")
            return
        ok, why = self.room(data)
        if not ok:
            self.alarm("extend", f"no extension (round {top + 1}): {why}")
            return
        self.clear("extend")
        self.write_schedule(data)

    # ---- G7: the fence -----------------------------------------------------------------------------------------
    def fence_record(self):
        """R2: None when there is no FENCE.json; this run's fence of the D in force; anything else Stop 4 (a root
        whose fence cannot be trusted decides and starts nothing)."""
        p = self.root / "FENCE.json"
        try:
            data = p.read_bytes()
        except FileNotFoundError:
            return None
        except OSError as e:
            raise Stop(4, f"FENCE.json cannot be read ({e})") from None
        try:
            f = parse_canon(data, "FENCE.json")
        except ValueError as e:
            raise Stop(4, f"FENCE.json: {e}") from None
        if not isinstance(f, dict) or sorted(f) != FENCE_KEYS or not same(f["schema"], 2) \
                or f["run_fingerprint"] != self.fp or f["cutoff_utc"] != self.d_text():
            raise Stop(4, "FENCE.json is not this run's fence of the D in force (its keys, schema 2, run_fingerprint, "
                          "cutoff_utc): the root cannot be trusted, nothing is decided or started")
        return f

    def fenced(self) -> bool:
        return self.fence_record() is not None

    def fence_names(self, csha: str) -> bool:
        f = self.fence_record()
        return f is not None and csha in str(f["why"])

    def fence(self, why: str) -> None:
        p = self.root / "FENCE.json"
        if self.fenced():
            return
        create_only(p, canon({"at_utc": T(time.time()), "cutoff_utc": self.d_text(), "run_fingerprint": self.fp,
                              "schema": 2, "why": why}))
        self.say(f"FENCE.json written: cutoff_utc {self.d_text()}, why {why}")

    # ---- G6: workers, packer, groups ---------------------------------------------------------------------------
    def slot_ended(self, k: int) -> bool:
        """R3: the worker's own end of this run's slot k: its IDENTITY.json, its ended line, the end of its chain."""
        d = self.root / f"w{k:03d}"
        ident = canon({"run": self.h["run"], "run_fingerprint": self.fp, "schema": 2, "slot": k})
        try:
            if (d / "IDENTITY.json").read_bytes() != ident:
                return False
        except OSError:
            return False
        ln = last_line(d / "journal.txt")
        if not (isinstance(ln, dict) and sorted(ln) == ENDED_KEYS and ln["t"] == "ended"):
            return False
        i, s = ln["last_index"], ln["last_seal"]
        if type(i) is not int or i < -1:
            return False
        if i == -1:
            return s == self.genesis(k)
        try:
            return sha256_bytes((d / "closed" / f"p{i:06d}.seal.json").read_bytes()) == s
        except OSError:
            return False

    @staticmethod
    def lock_held(folder: Path) -> bool:
        """Another process holds the folder's OS lock (taken and released at once). A folder that is not there, or a
        lock file that cannot be opened, is not held: the worker or packer then names its own error."""
        if not folder.is_dir():
            return False
        try:
            SlotLock(folder).release()
        except Stop:
            return True
        except OSError:
            return False
        return False

    def record_group(self, g: Group, kind: str, slot) -> None:
        self.foreign = [(p, k) for p, k in self.foreign if p != g.pid]     # that number is ours now (R6)
        with open(self.gdir / "groups.jsonl", "ab") as f:
            f.write(canon({"at_utc": T(time.time()), "boot_id": self.boot, "kind": kind, "pid": g.pid,
                           "slot": slot}))
            f.flush()
            os.fsync(f.fileno())

    def earlier_groups(self) -> list:
        """The process groups an earlier guard of THIS boot started (Linux only: G7)."""
        out = []
        try:
            lines = (self.gdir / "groups.jsonl").read_bytes().splitlines(keepends=True)
        except OSError:
            return out
        for ln in lines:
            try:
                r = parse_canon(ln, "groups.jsonl")
            except ValueError:
                continue
            if isinstance(r, dict) and r.get("boot_id") == self.boot and type(r.get("pid")) is int:
                out.append((r["pid"], r.get("kind")))
        return out

    def py(self, script: str) -> list:
        return [self.a.python, "-I", "-B", str(RUN_DIR / script)]

    def start_worker(self, s: Slot, now: float) -> None:
        a = self.a
        cmd = self.py("worker.py") + ["--root", str(self.root), "--slot", str(s.k), "--exe", a.exe, "--net", a.net,
                                      "--manifest", a.manifest, "--known-startup", a.known_startup,
                                      "--game-seconds", repr(a.game_seconds)]
        if a.openings:
            cmd += ["--openings", a.openings]
        s.starts = [t for t in s.starts if now - t < HOUR] + [now]
        s.g = Group(cmd, self.gdir / f"w{s.k:03d}.out", f"worker {s.k}")
        self.record_group(s.g, "worker", s.k)
        self.say(f"worker {s.k} started (pid {s.g.pid}), start {len(s.starts)} this hour")

    def finish_group(self, g: Group) -> int:
        """G6: an exited process: every member left in its group ended and verified gone, then reaped."""
        if not g.end_and_verify(self.a.allowance):
            self.alarm(f"group{g.pid}", f"{g.name}: a member of its group still lives {self.a.allowance} s after "
                                        f"the end was sent")
        code = g.reap()
        self.say(f"{g.name} exited with {code}")
        return code

    def manage_workers(self, st: str, fenced: bool, stop: bool, now: float) -> None:
        end = fenced or st in ("dispatch_end", "cutoff")
        late = st == "cutoff" and self.past_d_grace()
        for s in self.slots.values():
            if s.g is not None:
                if not s.g.exited():
                    if late:
                        self.alarm(f"late{s.k}", f"worker {s.k} still lives {self.a.end_grace} s after D: its "
                                                 f"group is ended")
                        s.g.end()
                    continue
                code = self.finish_group(s.g)
                s.g, s.last_code = None, code
                self.after_exit(s, code, end, now)
            if s.ended or s.unreconciled or stop or st == "hold" or now < s.next_try:
                continue
            if self.slot_ended(s.k):
                s.ended = True
                continue
            if not end:
                if s.faulted:
                    continue
                if len([t for t in s.starts if now - t < HOUR]) >= 5:
                    s.faulted = "five starts within one hour"
                    self.alarm(f"fault{s.k}", f"slot {s.k} FAULTED: {s.faulted}")
                    continue
            if self.lock_held(self.root / f"w{s.k:03d}"):      # a worker this guard did not start (an earlier
                if end and self.past_d_grace():                # guard's lives on in its own session)
                    s.unreconciled = "its lock is still held by a process this guard did not start at D + end grace"
                    self.alarm(f"unrec{s.k}", f"slot {s.k} UNRECONCILED: {s.unreconciled}")
                else:
                    self.alarm(f"held{s.k}", f"slot {s.k}: its lock is held by a process this guard did not start: "
                                             f"nothing started or counted, looked at again in 30 s")
                    s.next_try = now + RETRY.get(3, 30.0)
                continue
            self.clear(f"held{s.k}")
            s.end_start = end
            self.start_worker(s, now)

    def after_exit(self, s: Slot, code: int, end: bool, now: float) -> None:
        if self.slot_ended(s.k):
            s.ended = True
            self.say(f"slot {s.k} has ended")
            return
        again = RETRY.get(code, 5.0 if code < 0 else None)
        if end:                                         # the finalizer's start: 0, 3 and 8 are tried again until
            if code in (0, 3, 8) and not self.past_d_grace():               # D + --end-grace; anything else is a
                s.next_try = now + again                                    # slot whose end is not reconciled
                return
            if not s.end_start and not self.past_d_grace():   # G7: a start made BEFORE the end is not the finalizer's
                s.next_try = now
                self.say(f"slot {s.k}: its start before the end exited with {code} after it: the finalizer's start next")
                return
            s.unreconciled = (f"a start {'after' if s.end_start else 'before'} the end exited with {code} and the slot "
                              f"has no ended line")
            self.alarm(f"unrec{s.k}", f"slot {s.k} UNRECONCILED: {s.unreconciled}")
            return
        if again is None:
            s.faulted = f"exit {code}"
            self.alarm(f"fault{s.k}", f"slot {s.k} FAULTED: the worker exited with {code} (a named fault)")
            return
        s.next_try = now + again

    def past_d_grace(self) -> bool:
        """D + --end-grace has come by all three clocks (a HOLD is not taken as come)."""
        return self.B.judge("cutoff", lead=-self.a.end_grace)[0] == cw.COME

    def manage_packer(self, stop: bool, now: float) -> None:
        if self.packer is not None:
            if not self.packer.exited():
                return
            code = self.finish_group(self.packer)
            self.packer = None
            last = self.fenced() or (self.root / "STOP_PACKER").exists()
            if code == 0 and last:
                self.packer_done = True
                self.say("the packer made its last pass")
                return
            self.alarm("packer", f"the packer exited with {code} before its last pass: started again in 30 s")
            self.packer_next = now + 30.0
        if self.packer_done or stop or now < self.packer_next:
            return
        if self.lock_held(self.root / "out"):              # a packer this guard did not start: not started, not counted
            self.alarm("packer_held", "out/LOCK is held by a packer this guard did not start: looked at again in 30 s")
            self.packer_next = now + RETRY.get(3, 30.0)
            return
        self.clear("packer_held")
        self.packer_starts = [t for t in self.packer_starts if now - t < HOUR]
        if len(self.packer_starts) >= 5:
            self.alarm("packer5", "the packer was started five times within one hour: not again this hour")
            return
        self.packer_starts.append(now)
        self.packer = Group(self.py("packer.py") + ["--root", str(self.root), "--converter", self.a.converter],
                            self.gdir / "packer.out", "packer")
        self.record_group(self.packer, "packer", None)
        self.say(f"packer started (pid {self.packer.pid})")

    def sweep_foreign(self, st: str) -> None:
        """G7, Linux: the groups an earlier guard of this boot started, ended at D + --end-grace."""
        if os.name == "nt" or not self.foreign or st != "cutoff" or not self.past_d_grace():
            return
        marks = (str(self.root), self.a.exe)       # a worker names the root; its engine names the exe
        for pgid, _ in self.foreign:
            pids = linux_members(pgid, marks)
            for pid in pids:
                end_exact(pid, lambda: is_member(pid, pgid, marks))     # called at once: the loop's own pid
            if pids:
                self.alarm(f"foreign{pgid}", f"group {pgid} of an earlier guard still had {len(pids)} process(es) "
                                             f"{self.a.end_grace} s after D: ended")

    def marks(self) -> tuple:
        """What a process of the day names: DIR (worker, packer), the engine file, the converter."""
        return (str(self.root), self.a.exe, self.a.converter, str(Path(self.a.converter).resolve()))

    def sweep_orphans(self) -> None:
        """R6, Linux, every pass (before any worker is started): the groups of earlier guards of this boot are looked
        at in one walk of /proc. A group with no member left is dropped from the list for good (a group that is gone
        never gains a member, so its number can never point at another group of ours); a group whose leader is gone
        has every member left that names DIR, the engine or the converter ended and verified gone (Astra 220826Z:
        the engine of a dead worker searched on past D, beside the new worker of its slot). A group whose leader
        lives is left to G7."""
        if os.name == "nt" or not self.foreign:
            return
        marks = self.marks()
        self.foreign, orphans = orphan_groups(self.foreign, proc_table(), marks)
        for pgid, kind, pids in orphans:
            t_end = time.monotonic() + self.a.allowance
            while pids:
                for pid in pids:
                    end_exact(pid, lambda: is_member(pid, pgid, marks))     # called at once: the loop's own pid
                if time.monotonic() >= t_end:
                    break
                time.sleep(0.02)
                pids = linux_members(pgid, marks)
            self.alarm(f"orphan{pgid}", f"group {pgid} of an earlier guard ({kind}) had process(es) left without its "
                                        f"leader: ended" + (f"; {len(pids)} still live after {self.a.allowance} s"
                                                            if pids else ""))

    # ---- G9 and the pass ---------------------------------------------------------------------------------------
    def hourly(self, st: str, now: float) -> None:
        if now < self.next_hour:
            return
        self.next_hour = now + HOUR
        sl = self.slots.values()
        line = canon({"alarms": self.n_alarms, "at_utc": T(time.time()), "controls": len(self.ctl),
                      "fenced": self.fenced(), "free_bytes": shutil.disk_usage(self.root).free,
                      "schedules": len(self.sched), "slots_ended": sum(s.ended for s in sl),
                      "slots_faulted": sum(bool(s.faulted) for s in sl), "slots_live": sum(s.g is not None for s in sl),
                      "slots_unreconciled": sum(bool(s.unreconciled) for s in sl), "standing": sorted(self.alarms),
                      "state": st, "stop": (self.root / "STOP").exists(), "t": "hour"})
        with open(self.gdir / "hourly.jsonl", "ab") as f:
            f.write(line)
            f.flush()

    def boot_ok(self) -> bool:
        why = self.resume_why()
        if why is None:
            self.clear("boot")
            return True
        self.alarm("boot", f"this machine's boot id {self.boot} is not admitted ({why}): nothing is decided or "
                           f"started (the boot guard writes RESUME)")
        return False

    def resume_why(self):
        """R7: None when this boot is admitted, else why not. Every RESUME.<n>.json from 1 to n is walked as a chain
        (canonical, schema 2, n, this run, prev, old_boot_id = the header's boot for 1 else RESUME n-1's
        new_boot_id); admitted: no RESUME and the header's boot, or the highest names this boot with
        instance_provable true."""
        names = [p.name for p in self.root.glob("RESUME.*.json")]
        if any(not re.fullmatch(r"RESUME\.[1-9][0-9]{0,2}\.json", x) for x in names):
            return f"a RESUME file name outside the grammar: {sorted(names)[:3]}"
        prev, boot, top = b"", self.h["boot_id"], None
        for n in range(1, len(names) + 1):
            p = self.root / f"RESUME.{n}.json"
            try:
                data = p.read_bytes()
                r = parse_canon(data, p.name)
            except FileNotFoundError:
                return f"there are {len(names)} RESUME files and RESUME.{n}.json is not one of them"
            except (OSError, ValueError) as e:
                return f"{p.name}: {e}"
            if not (isinstance(r, dict) and same(r.get("schema"), 2) and same(r.get("n"), n)
                    and r.get("run_fingerprint") == self.fp
                    and r.get("prev") == ("first" if n == 1 else sha256_bytes(prev))
                    and r.get("old_boot_id") == boot and isinstance(r.get("new_boot_id"), str)):
                return (f"{p.name} is not RESUME {n} of this run's chain (schema, n, run_fingerprint, prev, "
                        f"old_boot_id, new_boot_id)")
            prev, boot, top = data, r["new_boot_id"], r
        if boot != self.boot:
            return ("it is not the header's and no RESUME names it" if top is None
                    else f"the highest RESUME names boot {boot[:40]}")
        if top is not None and top.get("instance_provable") is not True:
            return "the highest RESUME names this boot without instance_provable true: held for a person"
        return None

    def one_pass(self) -> bool:
        """True when the day is closed."""
        now = time.monotonic()
        stop = (self.root / "STOP").exists()
        boot = self.boot_ok()
        r = self.B.clocks.read()
        st = self.state(r)
        self.write_clock(r, st)
        self.pilot_pass(r)                              # G12: the pilot's record, once; never a stop (GP9)
        if st == "hold":
            self.alarm("hold", "the guard's clocks are in a HOLD (UTC alone ahead): no control, schedule or start")
        if stop:
            self.alarm("stop", "the STOP file: no control is taken, no schedule written, nothing started")
        else:
            self.clear("stop")
        fenced = self.fenced()
        if boot and not stop and st != "hold":
            if self.pending is not None:
                eff = self.ctl[self.pending - 1][2]
                if eff == "fence" or not (fenced or st == "cutoff"):
                    try:
                        self.make_effect(self.pending)
                        self.pending = None
                        self.clear("pending")
                    except Held as e:                   # tried again at every pass; no later control meanwhile
                        self.alarm("pending", f"the effect of the accepted control {self.pending} is owed: {e}")
                else:
                    self.alarm("pending", f"the schedule of the accepted control {self.pending} is not made: the day "
                                          f"has ended")
                    self.pending = None
                fenced = self.fenced()
            if not fenced and st != "cutoff" and self.pending is None:
                self.take_controls()
                fenced = self.fenced()
            if st == "cutoff" and not fenced:
                self.fence("D")
                fenced = True
            if not fenced and st == "play":
                self.extend()
        free = shutil.disk_usage(self.root).free
        if free < self.a.floor_bytes:
            self.alarm("floor", f"{free} bytes free, under the floor {self.a.floor_bytes}: no schedule is written")
        else:
            self.clear("floor")
        self.sweep_orphans()
        self.manage_workers(st, fenced, stop or not boot, now)
        self.sweep_foreign(st)
        self.manage_packer(stop or not boot, now)
        self.hourly(st, now)
        return self.close(fenced)

    def close(self, fenced: bool) -> bool:
        sl = self.slots.values()
        if not fenced or any(s.g is not None or not (s.ended or s.unreconciled) for s in sl):
            return False
        unrec = [s.k for s in sl if s.unreconciled]
        if unrec and not (self.root / "STOP_PACKER").exists():
            create_only(self.root / "STOP_PACKER", canon({"at_utc": T(time.time()), "run_fingerprint": self.fp,
                                                          "schema": 2, "unreconciled": unrec}))
            self.say(f"STOP_PACKER written: slots {unrec} are unreconciled")
        if not self.packer_done:
            return False
        term = self.terminal()
        if term is None:
            return False
        create_only(self.gdir / "CLOSED.json", canon({
            "at_utc": T(time.time()), "packer": "ended", "run_fingerprint": self.fp, "schema": 2,
            "slots_ended": [s.k for s in sl if s.ended], "slots_unreconciled": unrec, "terminal": term}))
        self.say(f"the day is closed: {sum(s.ended for s in sl)} slot(s) ended, {len(unrec)} unreconciled, terminal "
                 f"{term['sha256'][:12]} ({term['lines']} lines)")
        return True

    def terminal(self):
        """G10 (R10): the verified terminal record once the writer has run, else None (it runs, waits or failed)."""
        if self.term_rec is not None:
            return self.term_rec
        now = time.monotonic()
        if self.term is None:
            if now >= self.term_next:
                self.term = Group(self.py("terminal.py") + ["--root", str(self.root)], self.gdir / "terminal.out",
                                  "terminal writer")
                self.record_group(self.term, "terminal", None)
                self.say(f"terminal writer started (pid {self.term.pid})")
            return None
        if not self.term.exited():
            return None
        code = self.finish_group(self.term)
        self.term = None
        rec, why = self.terminal_check() if code == 0 else (None, f"the terminal writer exited with {code}")
        if rec is None:
            self.alarm("terminal", f"{why}: no CLOSED.json, the originals untouched, tried again in "
                                   f"{TERMINAL_RETRY:.0f} s")
            self.term_next = now + TERMINAL_RETRY
            return None
        self.clear("terminal")
        self.term_rec = rec
        return rec

    def terminal_check(self):
        """(record, None) or (None, why): TERMINAL.jsonl and its .zz as G10 wants them."""
        try:
            full = (self.root / "TERMINAL.jsonl").read_bytes()
            zz = (self.root / "TERMINAL.jsonl.zz").read_bytes()
            head = (self.root / "RUN.json").read_bytes()
        except OSError as e:
            return None, f"the terminal inventory cannot be read ({e})"
        try:
            if zlib.decompress(zz) != full:
                return None, "TERMINAL.jsonl.zz does not decode to TERMINAL.jsonl"
        except zlib.error as e:
            return None, f"TERMINAL.jsonl.zz cannot be decoded ({e})"
        lines = full.splitlines(keepends=True)
        if len(lines) < 2 or not full.endswith(b"\n") or lines[0] != head:
            return None, "TERMINAL.jsonl does not begin with RUN.json's bytes"
        try:
            foot = parse_canon(lines[-1], "the terminal footer")
        except ValueError as e:
            return None, f"TERMINAL.jsonl's last line is not a footer ({e})"
        if not isinstance(foot, dict) or foot.get("t") != "footer" \
                or foot.get("fingerprint") != sha256_bytes(full[:len(full) - len(lines[-1])]):
            return None, "TERMINAL.jsonl's last line is not its footer (t footer, the fingerprint of the bytes before it)"
        return {"lines": len(lines), "sha256": sha256_bytes(full), "zz_sha256": sha256_bytes(zz)}, None

    def check_closed(self) -> None:
        """R1: guard/CLOSED.json is this run's closing record, or Stop 4 (held for a person)."""
        try:
            c = parse_canon((self.gdir / "CLOSED.json").read_bytes(), "guard/CLOSED.json")
        except (OSError, ValueError) as e:
            raise Stop(4, f"guard/CLOSED.json is not this run's closing record ({e}): held for a person") from None
        se, su = (c.get("slots_ended"), c.get("slots_unreconciled")) if isinstance(c, dict) else (None, None)
        if not (isinstance(c, dict) and sorted(c) == CLOSED_KEYS and same(c["schema"], 2)
                and c["run_fingerprint"] == self.fp and c["packer"] == "ended"
                and isinstance(se, list) and isinstance(su, list) and all(type(x) is int for x in se + su)
                and se == sorted(se) and su == sorted(su) and sorted(se + su) == self.h["slots"]):
            raise Stop(4, "guard/CLOSED.json is not this run's closing record (its keys, schema 2, run_fingerprint, "
                          "packer, the header's slots): held for a person")
        if not self.fenced():
            raise Stop(4, "guard/CLOSED.json stands without this run's FENCE.json: held for a person")
        bad = [k for k in se if not self.slot_ended(k)]
        if bad:
            raise Stop(4, f"guard/CLOSED.json names slot(s) {bad} ended whose journal does not end: held for a person")
        if su:
            try:
                sp = parse_canon((self.root / "STOP_PACKER").read_bytes(), "STOP_PACKER")
            except (OSError, ValueError):
                sp = None
            if not isinstance(sp, dict) or sp.get("run_fingerprint") != self.fp or sp.get("unreconciled") != su:
                raise Stop(4, "guard/CLOSED.json names unreconciled slots and STOP_PACKER does not: held for a person")
        rec, why = self.terminal_check()
        if rec is None or c["terminal"] != rec:
            raise Stop(4, f"guard/CLOSED.json's terminal is not the inventory on disk ({why or 'other hashes'}): "
                          f"held for a person")

    def run(self) -> int:
        if (self.gdir / "CLOSED.json").exists():
            self.check_closed()
            print("guard: the day is closed already (guard/CLOSED.json)")
            return 0
        self.replay_controls()
        self.say(f"guard of run {self.h['run']} ({self.fp[:12]}): slots {self.h['slots']}, "
                 f"schedules {len(self.sched)}, "
                 f"controls {len(self.ctl)}, D {self.d_text()}, boot {self.boot}")
        while True:
            if self.one_pass():
                print("guard: the day is closed")
                return 0
            time.sleep(self.a.tick)


def main() -> int:
    ap = argparse.ArgumentParser()
    for name in ("root", "exe", "net", "manifest", "known-startup", "converter", "policy"):
        ap.add_argument("--" + name, required=True)
    ap.add_argument("--floor-bytes", type=int, required=True)
    ap.add_argument("--openings", default="")
    ap.add_argument("--game-seconds", type=float, default=600.0)
    ap.add_argument("--horizon", type=int, default=2)
    ap.add_argument("--tick", type=float, default=1.0)
    ap.add_argument("--allowance", type=float, default=2.0)
    ap.add_argument("--end-grace", type=float, default=60.0)
    ap.add_argument("--python", default=sys.executable)
    a = ap.parse_args()
    if a.horizon < 2 or a.floor_bytes < 0 or not all(math.isfinite(x) and x > 0 for x in
                                                     (a.tick, a.allowance, a.end_grace, a.game_seconds)):
        print("STOP: --horizon is at least 2 (D2), --floor-bytes at least 0, the times finite and above 0")
        return 2
    if os.name != "nt":                                 # R12: every end on Linux goes through a pidfd
        try:
            os.close(os.pidfd_open(os.getpid()))
            signal.pidfd_send_signal  # noqa: B018
        except (AttributeError, OSError) as e:
            print(f"STOP: this guard ends processes only through a pidfd (Linux 5.3, Python 3.9): {e}")
            return 2
    g = None
    try:
        g = Guard(a)
        return g.run()
    except Stop as e:
        print(f"guard: STOP ({e.code}): {e}")
        if g is not None:
            g.say(f"STOP ({e.code}): {e}", alarm=True)
        return e.code
    except Exception as e:  # noqa: BLE001   never a traceback: every other fault is a 4
        print(f"guard: STOP (4): {type(e).__name__}: {e}")
        if g is not None:
            g.say(f"STOP (4): {type(e).__name__}: {e}", alarm=True)
        return 4


if __name__ == "__main__":
    sys.exit(main())
