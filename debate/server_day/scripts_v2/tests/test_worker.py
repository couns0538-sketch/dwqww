"""Opus 2026-11-23: the test of run/worker.py version 2 (FORMATS 2.2 sections 0, 0.1 and 1.1 to 1.8; SETUP_PLAN
2.2 D5), with the real engine and the frozen texts of <tree>/workloads and /known. Standard library only.

    test_worker.py <engine exe> <net file> <tree> <NEW work folder> [only=V1,V4a,...]

<tree> holds run/ (worker.py, record.py, uciproc.py, engine_lines.py), workloads/ and known/, so that a copy with
one change is tested the same way. Every case has its own root under the work folder. Three groups of cases, each
group's workers at once (at most six engines at a time, one thread each, four of them for seconds; run it behind
the build gate).

Known answers, written before the first run. Sources: N12's six games (known/n12_batch.json: 462 rows in all);
Astra's 135234Z for the two zero-row controls (FORMATS 1.4 names both as fixtures); FORMATS 1.3 to 1.8 for the files.
 V1   N12's six openings as a list rule (count 6), slot 1, piece_games 4, one range (round 1, counters 1 to 6),
      dispatch end in 30 s: exit 0; every game as n12_batch.json (rows, end line, digest), 462 rows in all;
      closed/p000000.raw = games 1 to 4, p000001.raw = games 5 and 6, open/ empty; both seals equal, byte for
      byte, to the record recomputed here (1.5); the journal is exactly epoch, done x4, closed, done x2, closed,
      ended; the epoch line {1, prev 0, last_index -1, genesis, this machine's boot id, resume null}; the ended line
      {epoch 1, last_index 1, seal 1's sha256, why "ranges done"}; every done line names its record's end, bind
      and rows; every record's bind is record.bind of its own fields; the range seal r0001.w001 (1.7): complete,
      done 6, games 6, rows 462, raw_bytes of both pieces, pieces 0 to 1; IDENTITY.json; the heartbeat canonical
      with 6 games and no .part left; no .tmp file; no engine left.
 V2   Astra's case 8: a copy of V1's slot folder under ANOTHER run's header (run "other"): exit 4 naming
      IDENTITY.json; the slot folder unchanged byte for byte.
 V2b  a copy of V1's slot folder without its IDENTITY.json, under V1's header: exit 4 naming the missing
      identity; unchanged byte for byte.
 V3   Astra's case 9: dispatch end 60 s ago: exit 0, no engine started, the journal is epoch + ended
      ("finalizer"), the range seal never_dispatched 3 with the three ids listed, complete false; dispatch_unknown 0
      (FORMATS 2.4, Astra 150955Z's never-started control: the slot's FIRST start is the finalizer).
 V4a  root seed edge2649, run edge, slot 0, counter 1: noselfgame, plies 5, opening d2d4 g7g5 e2e4 f7f5 d1h5,
      sent none, end `openingend plies 5 reason nomoves`.
 V4b  root seed edge2715: done with rows 0, opening g2g4 d7d6 b2b3 h7h6 f2f3 e7e6 b1c3 d8h4, the end line begins
      `sgend result -1 reason mate plies 8 run 0 searches 0 nodes 0 `.
 V4c  root seed edge3146, run d10 (Astra 144008Z: her id d10-w000-g00000001; the seed opening hashes the whole id):
      mate at ply 7: noselfgame, 7 opening moves, sent none, `openingend plies 7 reason nomoves`.
 V4d  root seed edge4013, run d10 (GUESS: the same run name for her control): mate exactly at ply 8: the game line IS
      sent, zero rows, the end line begins `sgend result -1 reason mate plies 8 run 0 searches 0 nodes 0 `.
 V5   the slot's lock held by this test: exit 3 naming the lock, no journal and no IDENTITY.json written.
 V6   RUN.json names another engine_sha256: exit 5 naming engine_sha256, no slot folder made.
 V7   a REAL kill of the worker after two of V1's games, then an unfinished line appended to the journal and
      garbage to the open piece; the restart drops the line and cuts the garbage off (both named in worker.log):
      exit 0, every id once, the pieces byte for byte V1's, ended "ranges done", no engine left.
 V7b  Fable's reading 9 (a softer 1.8.3, 23 Nov): a REAL kill after three of V1's games (counter 4, 127 rows, is
      being played), the start of g4's record (`game n12-w001-g00000004 opening <its moves>` + its sent line)
      appended to the open piece, FENCE.json: the restart is a finalizer start: exit 0, worker.log names the cut
      and g4's failed line; after the epoch-2 line the journal is failed g4 (why "its bytes lay beyond the
      journal's end and were cut at a restart"), closed 0, ended "finalizer"; the range seal: done 3, unfinished 1
      (g4), dispatch_unknown 0, never_dispatched 2 (g5, g6), not complete; p000000 holds g1 to g3 byte for byte as
      V1's p000000 begins.
 V7c  the control: as V7b with garbage that names no game: no failed line; the seal (2.4: a finalizer at epoch 2
      doubts the lowest open id) dispatch_unknown 1 (g4), never_dispatched 2 (g5, g6), unfinished 0.
 (Every FENCE.json of these cases copies the D in force, as 1.8.1 and 2.4 have it: SCHEDULE.1's cutoff_utc. V7b
 and V7c are Astra's two cases of FORMATS 2.5 1.8.3 in a range of six: the FIRST counter without a final state is
 the one in doubt; with its failed line it is unfinished and no id is dispatch_unknown; never_dispatched_first 5.)
 V8   V1's journal with line 3 damaged: exit 4 naming journal line 3, the journal unchanged.
 V9   V1's journal cut after the sixth game (the second piece moved and sealed, its closed line lost): exit 0, the
      seal kept byte for byte (no second seal), the journal ends: epoch 2, closed 1 with that seal's sha256, ended
      "finalizer".
 V9b  as V9 with one digit of a row in the moved piece changed: exit 4 naming p000001.raw, only the epoch line
      added, the seal unchanged.
 V10  a game line of 4,000,000 soft nodes, dispatch end in 20 s, cutoff in 30 s: game 1 is cut by the cutoff:
      exit 0, the journal is epoch, unfinished g1 (cutoff), ended "cutoff"; range seal unfinished 1,
      never_dispatched 2, not complete; 2.9: the watch decides at D less the 2 s allowance, not late, and finds
      the native process gone before D; the worker ends within 3 s of the cutoff; no engine left.
 V11a SCHEDULE.2 with a wrong prev: exit 4 naming SCHEDULE.2.json, no slot folder made.
 V11b while the worker waits after its range, a SCHEDULE.2 that lengthens the started range: exit 4 naming the
      started range; both games played before.
 V12  plant swap_final at counter 2 (A23): exit 7, the journal is epoch, done g1, refused g2 (binding).
 V13  plant kill_engine at counter 4 (127 rows; counter 3 is N12's zero-row game, which ends before any kill can
      reach it: the first run, 13:31): exit 0, one failed line for g4 then its done line, the pieces V1's.
 V13b plant bad_row at counter 4 (Fable 13:59: a record.text / bind refusal is a game failure): g4's first row gets
      " x" appended, the record module refuses it: exit 0, g4 failed once (why begins "row: a row of
      n12-w001-g00000004 is not in its shape") then done, the pieces V1's byte for byte.
 V14  the header's boot id is another one: exit 4 naming the boot id, no slot folder made.
 V14b the same with RESUME.1.json admitting this boot (this slot: last_index -1, genesis): exit 0, the epoch
      line's resume is the sha256 of RESUME.1.json, the game played (edge2649: noselfgame).
 V14c the same with a RESUME that names last_index 5 for this slot: exit 4 naming RESUME.1.json, no journal.
 V15  FENCE.json of this run present at the start, dispatch end in 30 s: exit 0, no engine started, the journal
      is epoch + ended ("finalizer").
FORMATS 2.4 (Fable 14:13 from Astra 150955Z / 151303Z and Neon 151130Z; known answers from those texts):
 V16  Astra's before-first-record stop: the slow game line, the worker killed the moment worker.log (--trace)
      shows `>>> selfgame` (the game line went out), then its engine: the journal is the epoch line alone and no
      piece holds a byte; FENCE.json; the restart: exit 0, epoch 1, epoch 2, ended "finalizer", no second engine;
      the range seal: dispatch_unknown 1 (g1), never_dispatched 2 (g2, g3), unfinished 0, not complete, no piece.
 V17  Astra's recovery sequence (boot ids given to each process by the test; one machine has one boot id): under
      boot A (the header's) the slot plays g1 to g3, one game a piece, and closes piece 2; the STOP file ends it;
      RESUME.1 anchors piece 2 for boot B; SCHEDULE.1 adds round 2 (g4); the first start under B: its epoch line
      {2, prev 1, last_index 2, piece 2's seal, boot B, resume = RESUME.1's sha256}, g4 into piece 3; SCHEDULE.2
      adds round 3 (g5); the second start under B: epoch {3, prev 2, last_index 3, piece 3's seal, boot B, resume
      null}, g5 into piece 4. Exit 0 each time.
 V17b a copy after the first B start with RESUME.2 for boot B anchoring piece 3 (today's head: a changed anchor)
      and a torn last journal line: exit 4 naming "a changed anchor", the journal unchanged, the torn line still
      there (2.4: a refused start changes nothing; the unfinished last line is cut only after every check).
 V17d a copy after the first B start with RESUME.2 for boot C (FORMATS 2.4: the HIGHEST RESUME must name this
      machine's boot): the process on boot B: exit 4 naming "no RESUME record admits it", the journal unchanged.
 V17c a copy with piece 3's seal rewritten with another prev_seal and its closed line naming the new sha256 (a
      break between 2 and 3): exit 4 naming "p000003.seal.json does not descend", the journal unchanged.
 V18  a fence in the pilot (no SCHEDULE.1), its cutoff_utc RUN.json's hard_cutoff_utc copied: exit 0, epoch +
      ended (finalizer), no engine started, never_dispatched 2, dispatch_unknown 0 (zero new reservations).
 V18b the same with a cutoff one hour earlier (a new time): exit 4 naming FENCE.json, no slot folder made.
 V19  utc(): 2026-11-31, hour 24, minute 60, second 60 and month 13 refused with Stop 4 (Fable's B: timegm moves
      31 November to 1 December); 2026-11-30T23:59:59Z read as calendar.timegm gives it.
Group 5, FORMATS 2.7 (Fable's FABLE-2311-FORMATS-27-AND-PACKER-READ, items A1, A2, A3, A5; known answers from
FORMATS 1.2, 1.4 and 1.8 point 3 as 2.7 words them, written before the first run). A kill right after a journal
line is made by cutting the lines after it and the slot's range seals from a finished run: a finalizer, and a
worker after its `unfinished` line, writes nothing else in between (no open game, so close_piece writes nothing).
 V20  A1 (2.6: an `unfinished` id is a barrier): V10's slow game, range 1 to 4; run 1 ends `unfinished` g1 at D;
      killed before its range seal (cut); the restart is a finalizer: exit 0, the journal epoch 1 (play),
      unfinished g1 (cutoff), epoch 2 (seal_only), ended (finalizer); the range seal unfinished 1, dispatch_unknown
      0, never_dispatched 3 from 2, not_done [g1 unfinished]; the restart starts no engine. (Before 2.6/2.7 the
      finalizer doubted g2: dispatch_unknown 1, never_dispatched 2 from 3.)
 V21  A2 a (2.7: only an EARLIER play epoch can leave an unknown id): the fence first; the finalizer, then cut back
      to its epoch line (killed after it) and started again, twice: each start exit 0, epochs 1 to k all seal_only,
      ended (finalizer); each range seal never_dispatched 3 from 1, dispatch_unknown 0, not_done []; no engine.
 V22  A2 b: V16's root after its finalizer, cut back to that finalizer's epoch line (killed after it), started
      again: exit 0, epoch 1 (play), epochs 2 and 3 (seal_only), ended (finalizer); the SAME one unknown id as V16:
      g1 dispatch_unknown, never_dispatched 2 from 2.
 V23  A3 (2.6: a worker reads each schedule once): two ranges (round 1: 1 to 3, round 2: 4 to 6), a schedule 2
      written after g1 is done that shortens round 2 (not started) to 4 to 5 (short true, schedule 2): exit 0;
      done g1 to g5 and never g6, ended (ranges done); the five records as n12_batch.json's first five; round 2's
      range seal 4 to 5, complete, short; SCHEDULE.1.json opened exactly ONCE by the worker process (an audit hook
      in that process counts every open of that file; the worker before 2.6 opened it twice at every look).
 V24  A3 (2.7): schedules 2 and 3 written together (3 first), 3's dispatch end 5 s ago: exit 0, ended (cutoff), no
      game reserved after they appeared (done at the end <= done when 2 was written + 1, the game in flight), and
      fewer than 6 done then; the range seal names schedule 3.
 V25  A3 (2.6): a schedule 2 whose prev does not hold, written mid-play: exit 4 naming SCHEDULE.2.json, no game
      reserved after it, no `ended` line.
 V26  A5 (2.7, Neon 153430Z): V20's journal after the cut (epoch, unfinished g1) plus a `failed` line for g2, a
      counter AFTER the first one not passed: exit 4 naming "after bar-w000-g00000001"; the journal unchanged byte
      for byte; no range seal.
 V27  A5, the worker's reading (an id no range holds cannot have been dispatched): the same with g9 (range 1 to 4):
      exit 4 naming "lies in no range"; the journal unchanged; no range seal.
Group 6, FORMATS 2.9 1.8 point 1 (item A4; Fable's 14:56 Q2 and 15:23; run/clockwatch.py). Known answers from
FORMATS 2.9 and the plants' definitions, written before the first run. A plant switches on once the engine
searches the planted game, the driver's cutoff taken before (as before a suspension). Every case: no engine left.
 V28  clock_forward at g2 of a fast range 1 to 3 (dispatch end 120 s, D 135 s ahead): exit 8 naming "ALARM clock:";
      the journal epoch (play), done g1, failed g2 (why "clock"), closed (g1's piece, index 0), NO ended line;
      worker.log names the plant and then the ALARM line. V28b, a start with right clocks: exit 0, epoch 2 (play),
      done g2 and g3, closed, ended "ranges done"; the three records as n12_batch.json's first three (the retry
      gives g2's record back); the range seal complete with done 3.
 V29  clock_suspend at the slow g1 (D 60 s ahead): exit 8 naming "ALARM watch: decided after D"; epoch, unfinished
      g1 (cutoff), NO ended line, no range seal (Fable 15:54 and 16:02: D itself had come at the decision); the
      watch decided with reason cutoff, late and decided_after_cutoff, and found the process gone; the worker ended
      20 s or more before the real D.
 V30  clock_back at the slow g1 (D 25 s ahead): the same journal; the watch decided at D less the allowance, not
      late, the process gone before D; the worker ended within 3 s of D (not an hour later); the worker outlived
      its engine's stop (that process alone, never a group: the stop line names its handle, the worker's own end
      line comes after it).
 V31  watch_nostop at the slow g1 (D 25 s ahead): exit 8 naming "ALARM watch:"; epoch, unfinished g1 (cutoff), NO
      ended line; worker.log names the native process still there at D; the worker ended within 5 s after D.
 V32  clock_forward at the slow g1 (D 60 s ahead): exit 8 naming "ALARM clock:"; epoch, failed g1 (clock), NO
      ended line; the watch decided with reason clock and found the process gone; the worker ended 20 s or more
      before D.
 V33  SCHEDULE.2 written one second into the slow g1 (no plant), D 10 s from then (the old D 60 s): exit 0, epoch,
      unfinished g1 (cutoff), ended "cutoff"; the watch took the tighter D while the engine searched (decided not
      late: late, late_discovery and decided_after_cutoff False; the process gone before D); the worker ended
      within 3 s of the NEW D; the range seal names schedule 2 (d929f1cadbfb named 1: the schedule the watch took
      was not applied by the worker before its range seals).
 V34a as V33, the write made just after a whole second and D the whole second 2 s on (about 1.7 to 2 s after the
      write: its trigger, D less the allowance, had passed when it was found): exit 0, epoch, unfinished g1
      (cutoff), ended "cutoff" (Fable 16:02: stopped and gone before D is the normal end); the decision late and
      late_discovery, not decided_after_cutoff, after the write with 0 to 2 s left to D; the process gone before D
      (its reading's utc before D); the range seal names schedule 2.
 V34  as V33 with D 3 s BEFORE the write (found after D): exit 8 naming "ALARM watch: decided after D"; epoch,
      unfinished g1 (cutoff), NO ended line, no range seal; the watch acted at once and recorded it with the real
      readings (late, late_discovery and decided_after_cutoff True, left_to_cutoff_s negative, its utc = D less
      that, after the write); the process gone after D; the worker ended within 4 s after the write.
 V35  SCHEDULE.2 written one second into g1 of 100,000 soft nodes, its dispatch end 2 s in the past, D unchanged
      (120 s): exit 0, epoch, done g1 (the game kept its normal end), closed, ended "cutoff"; the watch never
      decided; range seal schedule 2, done 1, never_dispatched 2 from 2. A clockwatch that takes the dispatch end
      for a reason must fail it (the mutant run beside the both-ways run).
 V36  watch_lategone at the slow g1 (D 25 s ahead): the watch fires at D less the allowance, the exit is confirmed
      only once D has come (clockwatch 4 raises its own alarm for that, "first confirmed gone after D"): exit 8
      naming "ALARM watch: gone after D"; epoch, unfinished g1 (cutoff), NO ended line, no range seal; the decision
      not late (late_discovery and decided_after_cutoff False), the process gone after D, the module's alarm in
      worker.log; the worker ended within 3 s after D and not before D less 0.5 s.
 V37  in-process, no engine (Fable 16:02, point 3: the watch's refresh runs in a thread of its own and may outlive
      the watch): the refresh the watch gets is Worker.refresh, not follow_next; its code stores nothing (no
      attribute or item stored or deleted, no method that changes its object); with a snapshot and a SCHEDULE.2 of
      V33's kind on disk it gives that D and dispatch end to the clocks (Bounds.set, in this order) and leaves every
      attribute of the worker as it was; a SCHEDULE.2 that does not follow (a later D) is left: nothing set, no
      raise. watch_end with a watch whose reader_stalled is true logs "watch reader_stalled=True", and not when it
      is false.
SECOND READ (Opus 2026-11-24; KNOWN_ANSWERS_worker_v2_by_opus.md, written before the code; the seats' 215331Z,
223800Z 1 and 231830Z, Fable's FABLE-2311-PDEATHSIG-ANSWER). The test's own processes and the worker's engines are
known by number AND creation time (alive(pid, created), kill(pid, created): one handle or pidfd checked before the
end; nothing is ended by its number alone); fence() writes the guard's record (schema 2).
 T1a-e a stand-in process: alive by number and creation time; its creation time an int; alive with another creation
      time False; a kill with another creation time leaves it alive 1 s later; a kill with its own ends it in 10 s.
 V38a V3's root after its run, its journal cut back to the epoch line, the range seal kept: exit 0, the seal byte for
      byte as before, journal epoch, epoch, ended (finalizer). V38b the seal of another run (run, run_fingerprint),
      V38c 0 bytes, V38d this run's claiming complete with done 3, V38e epoch 7: exit 4 naming
      r0001.w000.seal.json, the seal unchanged, journal epoch, epoch, NO ended.
 V39a the header's boot and RESUME.1 from it to "bootb": exit 4 "no RESUME record admits it", no slot folder.
 V39b the header's boot and RESUME.1 = 5 bytes that are not a record: exit 4 naming RESUME.1.json, no slot folder.
 V40a header boot "otherboot", RESUME.1 old_boot_id "WRONG-BOOT-ID": exit 4 naming RESUME.1.json, no slot folder.
 V40b RESUME.1 otherboot -> bootb, RESUME.2 bootb -> this boot: exit 0, the epoch line's resume = RESUME.2's sha256.
 V40c as V40b with RESUME.2's old_boot_id "boot9": exit 4 naming RESUME.2.json, no slot folder.
 V40d V14b's RESUME.1 with "n": true: exit 4 naming RESUME.1.json, no slot folder.
 V41a w000 holding closed/p000001.seal.json, no IDENTITY.json, no journal: exit 4 naming "no IDENTITY.json", the
      folder as before (no LOCK, no IDENTITY.json). V41b w000 holding LOCK only, V41c LOCK and IDENTITY.json.tmp:
      exit 0, the finalizer's journal epoch, ended; no .tmp left.
 V42a lease_end_utc 2026-11-31T00:00:00Z, V42b hard_cutoff_utc one hour after lease_end_utc, V42c lease_start_utc one
      minute after lease_end_utc: exit 4 naming that field, no slot folder.
 V43a FENCE.json with schema 1, V43b with a key "x" more, V43c `[]`: exit 4 naming FENCE.json, no traceback, no slot
      folder.
 V45  V16: the engine line names pid N created C; while the worker lives created_of(N) == C; after the worker's kill,
      kill(N, C) ends the orphan: alive(N, C) False.
 V47  in-process: start_engine inside a second thread raises StartRefused naming "main thread"; eng stays None.
 V48  in-process (W10, 24 Nov 00:48): check_identity on a slot folder that does not exist returns None and makes
      nothing (the boot guard reads every slot). V48b, the control: a folder holding a stray file and no
      IDENTITY.json: Stop 4 naming "no IDENTITY.json".
 Linux only (the seats run them; on Windows SKIP): V44 ProcHandle's how "popen": exit 5 naming "pidfd", journal
      epoch only. V46 the slow game, the worker SIGKILLed at `>>> selfgame`: its engine (N, C) gone within 1 s.
      V46b the same with the launcher switched off: the engine still lives 1 s later (the instrument sees an
      orphan). V46c a stand-in guard holding the worker, both SIGKILLed: no engine left within 1 s. V46d
      bind_exec.py with parent 1: exit 1, no output. V46e 200 starts of /bin/true through bind_exec.py while 3
      threads run: every Popen returns within 10 s, every exit 0.
"""
import calendar
import ctypes
import hashlib
import json
import os
import select
import shutil
import signal
import subprocess
import sys
import threading
import time
import types
from pathlib import Path

if len(sys.argv) < 5:
    print(__doc__)
    sys.exit(2)
EXE, NET, TREE, WORK = (Path(x).resolve() for x in sys.argv[1:5])
ONLY = set()
for extra in sys.argv[5:]:
    if not extra.startswith("only="):
        print(f"STOP: not understood: {extra}")
        sys.exit(2)
    ONLY |= set(extra[5:].split(","))
if WORK.exists():
    print(f"STOP: {WORK} exists already (a NEW work folder)")
    sys.exit(2)
WORK.mkdir(parents=True)
sys.path.insert(0, str(TREE / "run"))
import record  # noqa: E402   the reader's side of the record, from the tree under test
try:
    import worker as W  # noqa: E402   its SlotLock (V5), boot_id and utc (V19)
    BOOT = W.boot_id()
    SlotLock = W.SlotLock
except Exception as e:  # noqa: BLE001   an old tree without them: the cases that need them fail, the rest run
    print(f"(the tree's worker has no SlotLock / boot_id: {type(e).__name__}: {e})")
    W, BOOT, SlotLock = None, "none:" + os.name, None

MAN_PATH, KNOWN = TREE / "workloads" / "MANIFEST.json", TREE / "known" / "startup.json"
MAN = json.loads(MAN_PATH.read_bytes())
results = []


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canon(obj) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")


def check(name, ok, detail="") -> bool:
    results.append((name, bool(ok)))
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + (f": {str(detail)[:300]}" if detail != "" and not ok else ""), flush=True)
    return bool(ok)


def want(*cases) -> bool:
    return not ONLY or bool(ONLY & set(cases))


def T(t: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))


N12 = [ln.split()[3:] for ln in (TREE / "workloads" / "n12_batch.uci").read_text(encoding="ascii").splitlines()
       if ln.startswith("position startpos moves ")]
assert len(N12) == 6 and all(len(o) == 8 for o in N12), N12
OPENINGS = WORK / "n12_openings.txt"
OPENINGS.write_bytes("".join(" ".join(o) + "\n" for o in N12).encode("ascii"))
K_BATCH = json.loads((TREE / "known" / "n12_batch.json").read_text(encoding="ascii"))["games"]
assert sum(g[0] for g in K_BATCH) == 462, "n12_batch.json is not the file of 462 rows"
EXE_SHA = sha(EXE.read_bytes())
SLOW_LINE = MAN["selfgame_line"].replace("softnodes 2000 ", "softnodes 4000000 ")
assert SLOW_LINE != MAN["selfgame_line"]
SLOW_MAN = WORK / "manifest_slow.json"
SLOW_MAN.write_bytes(json.dumps(dict(MAN, selfgame_line=SLOW_LINE)).encode("ascii"))


def row(first, last, rnd=1, slot=0, sched=0):
    return {"slot": slot, "round": rnd, "first": first, "last": last, "short": False, "schedule": sched}


def put(path: Path, data: bytes) -> None:
    """A whole file at once for the worker that may be reading the folder (a .part name it never reads)."""
    part = path.with_name(path.name + ".part")
    part.write_bytes(data)
    os.replace(part, path)


def make_root(name, run, slot, rows, dispatch_in, cutoff_in, rule="list", seed="", piece_games=4,
              engine_sha=None, game_line=None, boot=None, hdr=None):
    root = WORK / name
    root.mkdir()
    now = time.time()
    h = {"schema": 2, "run": run, "lease_start_utc": T(now - 3600), "lease_end_utc": T(now + 86400),
         "hard_cutoff_utc": T(now + 86400), "boot_id": boot or BOOT, "instance": "test-instance", "package": "0" * 64,
         "engine_sha256": engine_sha or EXE_SHA, "net_sha256": MAN["net_sha256"],
         "options_sha256": sha("".join(ln + "\n" for ln in MAN["options"]).encode("ascii")),
         "game_line": game_line or MAN["selfgame_line"],
         "opening_rule": ({"kind": "seed", "plies": 8, "root_seed": seed} if rule == "seed" else
                          {"kind": "list", "sha256": sha(OPENINGS.read_bytes()), "count": len(N12)}),
         "slots": [slot], "piece_games": piece_games, "pilot_ranges": rows}
    h.update(hdr or {})
    put(root / "RUN.json", canon(h))
    if dispatch_in is not None:
        schedule(root, 1, rows, dispatch_in, cutoff_in)
    return root


def schedule(root, n, rows, dispatch_in, cutoff_in, prev=None):
    now = time.time()
    if prev is None:
        prev = "first" if n == 1 else sha((root / f"SCHEDULE.{n - 1}.json").read_bytes())
    put(root / f"SCHEDULE.{n}.json", canon({
        "schema": 2, "run_fingerprint": sha((root / "RUN.json").read_bytes()), "n": n, "prev": prev,
        "evidence": "0" * 64, "cutoff_utc": T(now + cutoff_in), "dispatch_end_utc": T(now + dispatch_in),
        "ranges": rows}))


def start(root, slot, manifest=MAN_PATH, openings=True, plant=None, boot=None, trace=False, audit=None, inject=None,
          dry=False):
    wp = str(TREE / "run" / "worker.py")
    args = ["--root", str(root), "--slot", str(slot), "--exe", str(EXE), "--net", str(NET), "--manifest", str(manifest),
            "--known-startup", str(KNOWN)]
    if openings:
        args += ["--openings", str(OPENINGS)]
    if plant:
        args += ["--rehearsal", "--plant", plant]
    if trace:
        args += ["--trace"]
    cmd = [sys.executable, "-I", "-B", wp, *args]
    if boot is not None or audit is not None or inject is not None:   # in that process only: boot_id() replaced
        pre = (f"worker.boot_id = lambda: {boot!r}; " if boot is not None else "") + (inject or "")   # (this
        # machine's boot id cannot change), a case's code (inject, ending in "; "), or every open
        hook = "" if audit is None else (                                             # of SCHEDULE.1.json counted
            "import atexit; n = [0]; "
            "sys.addaudithook(lambda ev, a: n.__setitem__(0, n[0] + 1) if ev == 'open' and "
            "str(a[0]).replace(chr(92), '/').endswith('/SCHEDULE.1.json') else None); "
            f"atexit.register(lambda: open({str(audit)!r}, 'w').write(str(n[0]))); ")
        cmd = [sys.executable, "-I", "-B", "-c",
               f"import sys; {hook}sys.path.insert(0, {str(TREE / 'run')!r}); import worker; "
               f"{pre}sys.argv = [{wp!r}] + {args!r}; sys.exit(worker.main())"]
    return cmd if dry else subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def d_in_force(root) -> str:
    """The D a fence copies (1.8.1; 2.4): the newest schedule's cutoff_utc, RUN.json's before any schedule."""
    s = sorted(root.glob("SCHEDULE.*.json"), key=lambda p: int(p.name.split(".")[1]))
    return json.loads((s[-1] if s else root / "RUN.json").read_bytes())["cutoff_utc" if s else "hard_cutoff_utc"]


def fence(root, cutoff=None) -> None:
    put(root / "FENCE.json", canon({"run_fingerprint": sha((root / "RUN.json").read_bytes()), "at_utc": T(time.time()),
                                    "cutoff_utc": cutoff or d_in_force(root), "schema": 2, "why": "a test"}))


def finish_all(P: dict, secs=240):
    """{case: (exit code, output)} and {case: the time its process ended}."""
    ends, t_end = {}, time.time() + secs
    while len(ends) < len(P) and time.time() < t_end:
        for k, p in P.items():
            if k not in ends and p.poll() is not None:
                ends[k] = time.time()
        time.sleep(0.1)
    out = {}
    for k, p in P.items():
        killed = k not in ends
        if killed:
            p.kill()
            ends[k] = time.time()
        text, _ = p.communicate()
        out[k] = (-999 if killed else p.returncode, text.strip() + ("\n(killed by the test: no end in time)" if killed else ""))
    return out, ends


def jline(ln: str) -> dict:
    try:
        r = json.loads(ln)
        return r if isinstance(r, dict) else {"t": "?", "raw": ln}
    except ValueError:
        return {"t": "?", "raw": ln}         # a line another worker version wrote: a failed check, never a crash


def jlines(root, slot):
    f = root / f"w{slot:03d}" / "journal.txt"
    return [jline(ln) for ln in f.read_bytes().decode("ascii", "replace").splitlines()] if f.exists() else []


def kinds(root, slot):
    return [r["t"] for r in jlines(root, slot)]


def pieces(root, slot):
    d = root / f"w{slot:03d}" / "closed"
    return {f.name: f.read_bytes() for f in sorted(d.glob("*.raw"))} if d.exists() else {}


def recs(root, slot):
    fp = sha((root / "RUN.json").read_bytes())
    try:
        return [g for data in pieces(root, slot).values() for g in record.parse(data, fp)]
    except Exception as e:  # noqa: BLE001   a piece that does not parse: the checks on it fail
        print(f"(the pieces of {root.name} do not parse: {type(e).__name__}: {e})")
        return []


def field_digest(g) -> str:
    res = g["end"].split()[2]
    h = hashlib.sha256()
    for r in g["rows"]:
        h.update((r + " " + res + "\n").encode("ascii"))
    return h.hexdigest()


IDENT_SRC = '''
def created_of(pid, h=None):
    # The creation time of the LIVING process of this number (read through handle h when given), or None.
    if os.name == "nt":
        import ctypes
        k = ctypes.WinDLL("kernel32", use_last_error=True)
        k.OpenProcess.restype = ctypes.c_void_p
        own = h is None
        h = k.OpenProcess(0x1000, False, int(pid)) if own else h
        if not h:
            return None
        t, code = [ctypes.c_ulonglong() for _ in range(4)], ctypes.c_ulong()
        try:
            ok = (k.GetProcessTimes(ctypes.c_void_p(h), *[ctypes.byref(x) for x in t])
                  and k.GetExitCodeProcess(ctypes.c_void_p(h), ctypes.byref(code)))
            return t[0].value if ok and code.value == 259 else None
        finally:
            if own:
                k.CloseHandle(ctypes.c_void_p(h))
    try:
        with open(f"/proc/{int(pid)}/stat", "rb") as f:
            s = f.read()
    except OSError:
        return None
    s = s[s.rfind(b")") + 2:].split()
    return int(s[19]) if s[0] != b"Z" else None
'''
exec(IDENT_SRC)


def alive(pid, created):
    "T-a (guard test R11): a process of this number lives AND it is the recorded one (its creation time)."
    return created is not None and created_of(pid) == created


def kill(pid, created):
    "T-a: end the recorded process only, through ONE handle (Windows) or pidfd (Linux) checked before the end."
    if created is None:
        return
    if os.name == "nt":
        k = ctypes.WinDLL("kernel32", use_last_error=True)
        k.OpenProcess.restype = ctypes.c_void_p
        h = k.OpenProcess(0x1001, False, int(pid))
        if h:
            if created_of(pid, h) == created:
                k.TerminateProcess(ctypes.c_void_p(h), 1)
            k.CloseHandle(ctypes.c_void_p(h))
        return
    try:
        fd = os.pidfd_open(int(pid))
    except OSError:
        return
    try:
        p = select.poll()
        p.register(fd, select.POLLIN)
        if created_of(pid) == created and not p.poll(0):
            signal.pidfd_send_signal(fd, signal.SIGKILL)
    except OSError:
        pass
    finally:
        os.close(fd)


def logtext(root, slot) -> str:
    f = root / f"w{slot:03d}" / "worker.log"
    return f.read_text(encoding="ascii", errors="replace") if f.exists() else ""


def started(root, slot) -> list:
    """(N, C) of every engine the worker logged (W9: `engine started: pid N created C,`); C is None when the line
    carries no creation time (an older worker)."""
    out = []
    for t in logtext(root, slot).split("engine started: pid ")[1:]:
        w = t.split()
        c = w[2].rstrip(",") if len(w) > 2 and w[1] == "created" else ""
        out.append((int(w[0].rstrip(",")), int(c) if c.isdigit() else None))
    return out


def engines_left(root, slot, secs=30.0) -> list:
    """The worker's engines that still live, by number AND creation time (T-a). An engine whose line carries no
    creation time is returned at once: nothing can prove it gone."""
    pcs = started(root, slot)
    unknown = [p for p, c in pcs if c is None]
    if unknown:
        return unknown
    end = time.time() + secs
    while time.time() < end and any(alive(p, c) for p, c in pcs):
        time.sleep(0.5)
    return [p for p, c in pcs if alive(p, c)]


def tree_bytes(folder: Path) -> dict:
    return {str(f.relative_to(folder)): f.read_bytes() for f in sorted(folder.rglob("*")) if f.is_file()}


def ended_why(root, slot):
    j = jlines(root, slot)
    return j[-1].get("why") if j and j[-1]["t"] == "ended" else None


def common(name, rc_out, rc_want, text=""):
    rc, out = rc_out
    check(f"{name} no traceback", "Traceback" not in out, out[-300:])
    return check(f"{name} exit {rc_want}" + (f" naming `{text}`" if text else ""), rc == rc_want and text in out, out[-400:])


# ================================================================ V19: utc() alone, no process
if want("V19"):
    def utc_or(text):
        try:
            return W.utc(text, "V19")
        except Exception as e:  # noqa: BLE001   a refusal must be the worker's Stop with code 4
            return None if type(e).__name__ == "Stop" and getattr(e, "code", None) == 4 else type(e).__name__
    V19_TEXTS = ("2026-11-31T00:00:00Z", "2026-11-30T24:00:00Z", "2026-11-30T23:60:00Z", "2026-11-30T23:59:60Z",
                 "2026-13-01T00:00:00Z", "2026-11-30T23:59:59Z")
    got19 = [utc_or(t) for t in V19_TEXTS] if W is not None else "no worker module"
    check("V19 utc refuses 31 November, hour 24, minute 60, second 60 and month 13 with Stop 4, and reads "
          "2026-11-30T23:59:59Z", got19 == [None] * 5 + [calendar.timegm((2026, 11, 30, 23, 59, 59))], got19)

# ================================================================ group 1: V1, V4a, V4b, V10
R1 = make_root("v1", "n12", 1, [row(1, 6, slot=1)], 30, 45) if want("V1", "V2", "V2b", "V7", "V7b", "V7c", "V8", "V9", "V9b", "V13", "V13b") else None
R4a = make_root("v4a", "edge", 0, [row(1, 1)], 20, 35, rule="seed", seed="edge2649") if want("V4a") else None
R4b = make_root("v4b", "edge", 0, [row(1, 1)], 20, 35, rule="seed", seed="edge2715") if want("V4b") else None
R4c = make_root("v4c", "d10", 0, [row(1, 1)], 20, 35, rule="seed", seed="edge3146") if want("V4c") else None
R4d = make_root("v4d", "d10", 0, [row(1, 1)], 20, 35, rule="seed", seed="edge4013") if want("V4d") else None
R10 = make_root("v10", "slow", 0, [row(1, 3)], 20, 30, game_line=SLOW_LINE) if want("V10") else None
P = {}
if R1:
    P["V1"] = start(R1, 1)
if R4a:
    P["V4a"] = start(R4a, 0, openings=False)
if R4b:
    P["V4b"] = start(R4b, 0, openings=False)
if R4c:
    P["V4c"] = start(R4c, 0, openings=False)
if R4d:
    P["V4d"] = start(R4d, 0, openings=False)
if R10:
    P["V10"] = start(R10, 0, manifest=SLOW_MAN)
OUT, ENDS = finish_all(P)

if R1:
    common("V1", OUT["V1"], 0)
    fp = sha((R1 / "RUN.json").read_bytes())
    rs = recs(R1, 1)
    check("V1 six games as n12_batch.json (rows, end line, digest), 462 rows",
          [[len(g["rows"]), g["end"], field_digest(g)] for g in rs] == K_BATCH and sum(len(g["rows"]) for g in rs) == 462,
          [(len(g["rows"]), g["end"][:40]) for g in rs])
    cp = pieces(R1, 1)
    check("V1 p000000.raw holds games 1 to 4 and p000001.raw games 5 and 6; open/ is empty",
          list(cp) == ["p000000.raw", "p000001.raw"]
          and [[g["id"][-2:] for g in record.parse(b, fp)] for b in cp.values()] == [["01", "02", "03", "04"], ["05", "06"]]
          and not list((R1 / "w001" / "open").iterdir()), list(cp))
    j = jlines(R1, 1)
    check("V1 the journal is epoch, done x4, closed, done x2, closed, ended",
          [r["t"] for r in j] == ["epoch"] + ["done"] * 4 + ["closed"] + ["done"] * 2 + ["closed", "ended"], [r["t"] for r in j])
    gen = f"genesis:{fp}:w001"
    check("V1 the epoch line", j[:1] == [{"t": "epoch", "epoch": 1, "prev_epoch": 0, "last_index": -1,
                                          "last_seal": gen, "boot_id": BOOT, "resume": None, "mode": "play"}], j[:1])
    ends = [g["last"] for data in cp.values() for g in record.parse(data, fp)]
    dl = [r for r in j if r["t"] == "done"]
    check("V1 every done line names its record's end, bind and rows",
          [(r["game"], r["end"], r["bind"], r["rows"]) for r in dl] ==
          [(g["id"], e, g["bind"], len(g["rows"])) for g, e in zip(rs, ends)], dl[:2])
    check("V1 every record's bind is record.bind over run fingerprint, id, opening, sent, rows and end",
          len(rs) == 6 and all(record.bind(fp, g["id"], g["opening"], g["sent"], g["rows"], g["end"]) == g["bind"] for g in rs))
    prev, ok_seals, seal_sha = gen, True, []
    for i, data in enumerate(cp.values()):
        sp = R1 / "w001" / "closed" / f"p{i:06d}.seal.json"
        sb = sp.read_bytes() if sp.exists() else b""
        games = record.parse(data, fp)
        ids = hashlib.sha256()
        for g in games:
            ids.update(f"{g['id']}\ndone\n{g['bind']}\n".encode("ascii"))
        ok_seals &= sb == canon({
            "schema": 2, "run": "n12", "run_fingerprint": fp, "slot": 1, "epoch": 1, "index": i, "prev_seal": prev,
            "raw_sha256": sha(data), "raw_bytes": len(data), "games": len(games),
            "rows": sum(len(g["rows"]) for g in games), "first_game": games[0]["id"], "last_game": games[-1]["id"],
            "first_counter": int(games[0]["id"][-8:]), "last_counter": int(games[-1]["id"][-8:]),
            "ids_digest": ids.hexdigest(), "round": 1, "schedule": 1})
        prev = sha(sb)
        seal_sha.append(prev)
    last_seal = seal_sha[-1] if seal_sha else None
    check("V1 both seals are byte for byte the records recomputed here (1.5)", ok_seals and len(seal_sha) == 2)
    check("V1 the closed lines name the seals' sha256",
          len(seal_sha) == 2 and [(r.get("index"), r.get("seal")) for r in j if r["t"] == "closed"] == list(enumerate(seal_sha)))
    check("V1 the ended line", j[-1:] == [{"t": "ended", "epoch": 1, "last_index": 1, "last_seal": last_seal,
                                           "why": "ranges done"}], j[-1:])
    rsp = R1 / "ranges" / "r0001.w001.seal.json"
    check("V1 the range seal (1.7), byte for byte", rsp.exists() and rsp.read_bytes() == canon({
        "schema": 2, "run": "n12", "run_fingerprint": fp, "round": 1, "slot": 1, "epoch": 1, "schedule": 1,
        "first": 1, "last": 6, "short": False, "complete": True, "first_index": 0, "first_prev_seal": gen,
        "through_index": 1, "through_seal": last_seal, "games": 6, "rows": 462,
        "raw_bytes": sum(len(b) for b in cp.values()),
        "dispositions": {"dispatch_unknown": 0, "done": 6, "never_dispatched": 0, "never_dispatched_first": None,
                         "noselfgame": 0, "refused": 0, "unfinished": 0, "not_done": []}}), rsp.read_bytes()[:400] if rsp.exists() else "missing")
    idf = R1 / "w001" / "IDENTITY.json"
    check("V1 IDENTITY.json", idf.exists() and idf.read_bytes() ==
          canon({"run": "n12", "run_fingerprint": fp, "schema": 2, "slot": 1}))
    hb = R1 / "w001" / "heartbeat"
    hbj = json.loads(hb.read_bytes()) if hb.exists() else {}
    check("V1 the heartbeat is canonical with 6 games, no .part left",
          hbj.get("games_this_start") == 6 and hb.read_bytes() == canon(hbj) and not (R1 / "w001" / "heartbeat.part").exists())
    check("V1 no temporary file left", not list(R1.rglob("*.tmp")) and not list(R1.rglob("*.part")))
    check("V1 no engine process left", engines_left(R1, 1) == [])

for name, root, opening, state, plies in (("V4a", R4a, "d2d4 g7g5 e2e4 f7f5 d1h5", "noselfgame", 5),
                                          ("V4b", R4b, "g2g4 d7d6 b2b3 h7h6 f2f3 e7e6 b1c3 d8h4", "done", 8),
                                          ("V4c", R4c, None, "noselfgame", 7),
                                          ("V4d", R4d, None, "done", 8)):
    if not root:
        continue
    common(name, OUT[name], 0)
    j = [r for r in jlines(root, 0) if r["t"] in ("done", "noselfgame")]
    rs = recs(root, 0)
    check(f"{name} one game, journalled as {state}", [r["t"] for r in j] == [state], j)
    check(f"{name} the opening: {opening or f'{plies} moves'}", len(rs) == 1 and len(rs[0]["opening"]) == plies
          and (opening is None or " ".join(rs[0]["opening"]) == opening), rs[:1])
    if state == "noselfgame":
        check(f"{name} sent none, no rows, `openingend plies {plies} reason nomoves`, the journal's plies {plies}",
              len(rs) == 1 and rs[0]["sent"] == "none" and rs[0]["rows"] == []
              and rs[0]["end"] == f"openingend plies {plies} reason nomoves" and bool(j) and j[0].get("plies") == plies,
              rs[:1])
    else:
        check(f"{name} the game line was sent, zero rows, the engine's mate line at ply {plies}, the journal's rows 0",
              len(rs) == 1 and rs[0]["sent"] == "position startpos moves " + " ".join(rs[0]["opening"])
              and rs[0]["rows"] == [] and bool(j) and j[0].get("rows") == 0
              and rs[0]["end"].startswith(f"sgend result -1 reason mate plies {plies} run 0 searches 0 nodes 0 "), rs[:1])

if R10:
    common("V10", OUT["V10"], 0)
    j = jlines(R10, 0)
    check("V10 the journal is epoch, unfinished g1 (cutoff), ended (cutoff)",
          [(r["t"], r.get("game"), r.get("why")) for r in j] ==
          [("epoch", None, None), ("unfinished", "slow-w000-g00000001", "cutoff"), ("ended", None, "cutoff")], j)
    rsp = R10 / "ranges" / "r0001.w000.seal.json"
    rsj = json.loads(rsp.read_bytes()) if rsp.exists() else {}
    check("V10 the range seal: unfinished 1, never_dispatched 2 as one interval from counter 2 (2.4), not complete, "
          "no piece",
          rsj.get("dispositions") == {"dispatch_unknown": 0, "done": 0, "never_dispatched": 2,
                                      "never_dispatched_first": 2, "noselfgame": 0, "refused": 0, "unfinished": 1,
                                      "not_done": [["slow-w000-g00000001", "unfinished"]]}
          and rsj.get("complete") is False and rsj.get("first_index") == -1, rsj)
    cut = json.loads((R10 / "SCHEDULE.1.json").read_bytes())["cutoff_utc"]
    late = ENDS["V10"] - calendar.timegm(time.strptime(cut, "%Y-%m-%dT%H:%M:%SZ"))
    check("V10 (2.9) the worker ended within 3 s of the cutoff (the watch fires at D less the 2 s allowance)",
          -3 <= late < 3, f"{late:.1f} s")
    lg = logtext(R10, 0)
    check("V10 (2.9) the watch decided at D less the allowance, not late, and found the native process gone before D",
          "watch decision reason=cutoff late=False" in lg and "watch native process gone after_cutoff=False" in lg,
          lg[-600:])
    check("V10 no engine process left", engines_left(R10, 0) == [])

# ================================================================ group 2: V3, V5, V6, V11a, V11b, V12, V14, V14b, V14c, V15
R3 = make_root("v3", "late", 0, [row(1, 3)], -60, -30, rule="seed", seed="late") \
    if want("V3", "V38a", "V38b", "V38c", "V38d", "V38e") else None
R5 = make_root("v5", "lock", 0, [row(1, 2)], 30, 45) if want("V5") else None
R6 = make_root("v6", "hash", 0, [row(1, 2)], 30, 45, engine_sha="f" * 64) if want("V6") else None
R11a = make_root("v11a", "chain", 0, [row(1, 2)], 30, 45) if want("V11a") else None
if R11a:
    schedule(R11a, 2, [row(1, 2)], 30, 45, prev="0" * 64)
R11b = make_root("v11b", "grow", 0, [row(1, 2)], 90, 100) if want("V11b") else None
R12 = make_root("v12", "swap", 1, [row(1, 6, slot=1)], 60, 75) if want("V12") else None
R14 = make_root("v14", "boot", 0, [row(1, 1)], 20, 35, rule="seed", seed="edge2649", boot="otherboot") if want("V14") else None
R14b = make_root("v14b", "edge", 0, [row(1, 1)], 20, 35, rule="seed", seed="edge2649", boot="otherboot") if want("V14b") else None
R14c = make_root("v14c", "edge", 0, [row(1, 1)], 20, 35, rule="seed", seed="edge2649", boot="otherboot") if want("V14c") else None
for root, last in ((R14b, -1), (R14c, 5)):
    if root:
        fp_ = sha((root / "RUN.json").read_bytes())
        put(root / "RESUME.1.json", canon({                # Fable 13:5x: the keys of RESUME.<n>.json in 2.3
            "schema": 2, "run_fingerprint": fp_, "n": 1, "prev": "first", "old_boot_id": "otherboot",
            "new_boot_id": BOOT, "instance": "test-instance", "instance_provable": True, "checks": [],
            "at_utc": T(time.time()), "slots": [{"slot": 0, "last_index": last, "last_seal": f"genesis:{fp_}:w000"}]}))
R15 = make_root("v15", "fence", 0, [row(1, 2)], 30, 45, rule="seed", seed="fence") if want("V15") else None
if R15:
    fence(R15)
R18 = make_root("v18", "pfence", 0, [row(1, 2)], None, None, rule="seed", seed="pfence") if want("V18") else None
R18b = make_root("v18b", "pfence", 0, [row(1, 2)], None, None, rule="seed", seed="pfence") if want("V18b") else None
if R18:
    fence(R18)                                          # in the pilot: RUN.json's hard_cutoff_utc, copied
if R18b:
    hc = json.loads((R18b / "RUN.json").read_bytes())["hard_cutoff_utc"]
    fence(R18b, T(calendar.timegm(time.strptime(hc, "%Y-%m-%dT%H:%M:%SZ")) - 3600))     # a new time: one hour earlier
R16 = make_root("v16", "doubt", 0, [row(1, 3)], 60, 75, game_line=SLOW_LINE) if want("V16", "V22", "V45") else None
SENT16 = J16 = OPEN16 = None
PC16, C16, GONE16 = [], [], []
if R16:                    # Astra 150955Z: the worker killed after its game line went out, before any record byte
    p16 = start(R16, 0, manifest=SLOW_MAN, trace=True)
    t_end = time.time() + 120
    while time.time() < t_end and ">>> selfgame" not in logtext(R16, 0) and p16.poll() is None:
        time.sleep(0.01)
    PC16 = started(R16, 0)                              # V45: read while the worker and its engine live
    C16 = [(p, c, created_of(p)) for p, c in PC16]
    p16.kill()
    p16.communicate()
    SENT16 = ">>> selfgame" in logtext(R16, 0)
    for p, c in PC16:
        kill(p, c)                                      # its engine, orphaned by the kill: a game of 4,000,000 nodes
    time.sleep(1.0)
    GONE16 = [(p, c, alive(p, c)) for p, c in PC16]
    J16 = kinds(R16, 0)
    OPEN16 = [f.name for f in (R16 / "w000" / "open").glob("*.raw") if f.stat().st_size > 0]
    fence(R16)
held = None
if R5:
    (R5 / "w000").mkdir()
    held = SlotLock(R5 / "w000") if SlotLock else None
P = {}
for name, root, kw in (("V3", R3, {"openings": False}), ("V5", R5, {}), ("V6", R6, {}), ("V11a", R11a, {}),
                       ("V11b", R11b, {}), ("V12", R12, {"plant": "swap_final:2"}), ("V14", R14, {"openings": False}),
                       ("V14b", R14b, {"openings": False}), ("V14c", R14c, {"openings": False}),
                       ("V15", R15, {"openings": False}), ("V16", R16, {"manifest": SLOW_MAN}),
                       ("V18", R18, {"openings": False}), ("V18b", R18b, {"openings": False})):
    if root:
        P[name] = start(root, 1 if name == "V12" else 0, **kw)
if R11b:
    t_end = time.time() + 120
    while time.time() < t_end and not (R11b / "ranges" / "r0001.w000.seal.json").exists() and P["V11b"].poll() is None:
        time.sleep(0.2)
    s1 = json.loads((R11b / "SCHEDULE.1.json").read_bytes())
    put(R11b / "SCHEDULE.2.json", canon(dict(s1, n=2, prev=sha((R11b / "SCHEDULE.1.json").read_bytes()),
                                             ranges=[row(1, 3)])))
OUT, ENDS = finish_all(P)
if held is not None:
    held.release()

if R3:
    common("V3", OUT["V3"], 0)
    check("V3 the journal is epoch + ended (finalizer)", kinds(R3, 0) == ["epoch", "ended"] and ended_why(R3, 0) == "finalizer",
          jlines(R3, 0))
    check("V3 no engine was started", "engine started" not in logtext(R3, 0))
    rsp = R3 / "ranges" / "r0001.w000.seal.json"
    rsj = json.loads(rsp.read_bytes()) if rsp.exists() else {}
    check("V3 (Astra's control: the slot's FIRST start is the finalizer) the range seal: never_dispatched 3 as one "
          "interval from counter 1 (2.4), dispatch_unknown 0, not_done empty, not complete",
          rsj.get("dispositions", {}).get("never_dispatched") == 3 and rsj["dispositions"].get("dispatch_unknown") == 0
          and rsj.get("complete") is False
          and rsj["dispositions"].get("never_dispatched_first") == 1 and rsj["dispositions"].get("not_done") == [],
          rsj)
if R5:
    common("V5", OUT["V5"], 3, "lock")
    check("V5 no journal and no IDENTITY.json", not (R5 / "w000" / "journal.txt").exists()
          and not (R5 / "w000" / "IDENTITY.json").exists())
if R6:
    common("V6", OUT["V6"], 5, "engine_sha256")
    check("V6 no slot folder made", not (R6 / "w000").exists())
if R11a:
    common("V11a", OUT["V11a"], 4, "SCHEDULE.2.json")
    check("V11a no slot folder made", not (R11a / "w000").exists())
if R11b:
    common("V11b", OUT["V11b"], 4, "after it started")
    check("V11b both games were played before", kinds(R11b, 0)[:3] == ["epoch", "done", "done"], kinds(R11b, 0))
if R12:
    common("V12", OUT["V12"], 7)
    check("V12 the journal is epoch, done g1, refused g2 (binding)",
          [(r["t"], r.get("game"), r.get("why")) for r in jlines(R12, 1)] ==
          [("epoch", None, None), ("done", "swap-w001-g00000001", None), ("refused", "swap-w001-g00000002", "binding")],
          jlines(R12, 1))
    check("V12 no engine process left", engines_left(R12, 1) == [])
if R14:
    common("V14", OUT["V14"], 4, "boot id")
    check("V14 no slot folder made", not (R14 / "w000").exists())
if R14b:
    common("V14b", OUT["V14b"], 0)
    j = jlines(R14b, 0)
    check("V14b the epoch line names RESUME.1.json by its sha256",
          bool(j) and j[0].get("resume") == sha((R14b / "RESUME.1.json").read_bytes()) and j[0].get("boot_id") == BOOT, j[:1])
    check("V14b the game was played", [r["t"] for r in j if r.get("game")] == ["noselfgame"], j)
if R14c:
    common("V14c", OUT["V14c"], 4, "RESUME.1.json")
    check("V14c no journal", not (R14c / "w000" / "journal.txt").exists())
if R15:
    common("V15", OUT["V15"], 0)
    check("V15 the journal is epoch + ended (finalizer), no engine started",
          kinds(R15, 0) == ["epoch", "ended"] and ended_why(R15, 0) == "finalizer" and "engine started" not in logtext(R15, 0),
          jlines(R15, 0))
if R16:
    check("V16 before the restart: the game line went out, the journal is the epoch line alone, no record byte",
          SENT16 is True and J16 == ["epoch"] and OPEN16 == [], (SENT16, J16, OPEN16))
    common("V16", OUT["V16"], 0)
    check("V16 the restart is a finalizer: epoch, epoch 2, ended (finalizer), no game line, no engine started",
          [(r["t"], r.get("epoch"), r.get("why")) for r in jlines(R16, 0)] ==
          [("epoch", 1, None), ("epoch", 2, None), ("ended", 2, "finalizer")]
          and logtext(R16, 0).count("engine started") == 1, jlines(R16, 0))
    rsp = R16 / "ranges" / "r0001.w000.seal.json"
    rsj = json.loads(rsp.read_bytes()) if rsp.exists() else {}
    check("V16 the range seal (2.4): g1 dispatch_unknown, g2 and g3 never_dispatched, not complete, no piece",
          rsj.get("dispositions") == {"dispatch_unknown": 1, "done": 0, "never_dispatched": 2,
                                      "never_dispatched_first": 2, "noselfgame": 0,
                                      "refused": 0, "unfinished": 0,
                                      "not_done": [["doubt-w000-g00000001", "dispatch_unknown"]]}
          and rsj.get("complete") is False and rsj.get("first_index") == -1, rsj)
    check("V16 no engine process left", engines_left(R16, 0) == [])
if R18:
    common("V18", OUT["V18"], 0)
    rsp = R18 / "ranges" / "r0001.w000.seal.json"
    rsj = json.loads(rsp.read_bytes()) if rsp.exists() else {}
    check("V18 a fence in the pilot (no SCHEDULE.1) copying RUN.json's hard_cutoff_utc: epoch + ended (finalizer), "
          "no engine started, never_dispatched 2, dispatch_unknown 0",
          kinds(R18, 0) == ["epoch", "ended"] and ended_why(R18, 0) == "finalizer"
          and "engine started" not in logtext(R18, 0) and not (R18 / "SCHEDULE.1.json").exists()
          and rsj.get("dispositions", {}).get("never_dispatched") == 2
          and rsj.get("dispositions", {}).get("never_dispatched_first") == 1
          and rsj.get("dispositions", {}).get("not_done") == []
          and rsj.get("dispositions", {}).get("dispatch_unknown") == 0, (jlines(R18, 0), rsj))
if R18b:
    common("V18b", OUT["V18b"], 4, "FENCE.json")
    check("V18b a pilot fence with a new time (one hour before RUN.json's): no slot folder made", not (R18b / "w000").exists())

# ================================================================ group 3: from V1's root: V2, V2b, V7, V8, V9, V9b, V13
G3 = bool(R1) and want("V2", "V2b", "V7", "V7b", "V7c", "V8", "V9", "V9b", "V13", "V13b")
if G3 and not check("group 3: V1's slot folder is there to copy (two closed lines, IDENTITY.json)",
                    [r.get("index") for r in jlines(R1, 1) if r["t"] == "closed"] == [0, 1]
                    and (R1 / "w001" / "IDENTITY.json").exists()):
    G3 = False
if G3:
    V1_PIECES = pieces(R1, 1)
    RUN1 = (R1 / "RUN.json").read_bytes()

    def copy_root(name):
        dst = WORK / name
        shutil.copytree(R1, dst)
        return dst

    def cut_after_game6(root):
        jf = root / "w001" / "journal.txt"
        lines = jf.read_bytes().split(b"\n")[:-1]
        k = next(i for i, ln in enumerate(lines) if b'"t":"closed"' in ln and b'"index":1,' in ln)
        jf.write_bytes(b"".join(ln + b"\n" for ln in lines[:k]))

    def fresh_root(name, run_bytes):
        root = WORK / name
        root.mkdir()
        put(root / "RUN.json", run_bytes)
        schedule(root, 1, [row(1, 6, slot=1)], 45, 60)
        return root

    R2 = R2b = R7 = R7b = R7c = R8 = R9 = R9b = R13 = R13b = None
    if want("V13b"):
        R13b = fresh_root("v13b", RUN1)
    if want("V7b"):
        R7b = fresh_root("v7b", RUN1)
    if want("V7c"):
        R7c = fresh_root("v7c", RUN1)
    if want("V2"):
        R2 = fresh_root("v2", canon(dict(json.loads(RUN1), run="other")))
        shutil.copytree(R1 / "w001", R2 / "w001")
        B2 = tree_bytes(R2 / "w001")
    if want("V2b"):
        R2b = fresh_root("v2b", RUN1)
        shutil.copytree(R1 / "w001", R2b / "w001")
        (R2b / "w001" / "IDENTITY.json").unlink()
        B2b = tree_bytes(R2b / "w001")
    if want("V8"):
        R8 = copy_root("v8")
        jf = R8 / "w001" / "journal.txt"
        lines = jf.read_bytes().split(b"\n")
        lines[2] = b"xx damaged"
        jf.write_bytes(b"\n".join(lines))
        J8 = jf.read_bytes()
    if want("V9"):
        R9 = copy_root("v9")
        cut_after_game6(R9)
        SEAL9 = (R9 / "w001" / "closed" / "p000001.seal.json").read_bytes()
    if want("V9b"):
        R9b = copy_root("v9b")
        cut_after_game6(R9b)
        pf = R9b / "w001" / "closed" / "p000001.raw"
        data = bytearray(pf.read_bytes())
        k = data.index(b"\nsg ") + 4                             # the first digit of the first row's ply
        data[k] = ord("1") if data[k] != ord("1") else ord("2")
        pf.write_bytes(bytes(data))
        SEAL9b = (R9b / "w001" / "closed" / "p000001.seal.json").read_bytes()
        J9b = (R9b / "w001" / "journal.txt").read_bytes()
    if want("V7"):
        R7 = fresh_root("v7", RUN1)
    if want("V13"):
        R13 = fresh_root("v13", RUN1)
    P = {}
    for name, root, kw in (("V2", R2, {}), ("V2b", R2b, {}), ("V8", R8, {}), ("V9", R9, {}), ("V9b", R9b, {}),
                           ("V13", R13, {"plant": "kill_engine:4"}), ("V13b", R13b, {"plant": "bad_row:4"})):
        if root:
            P[name] = start(root, 1, **kw)
    GARBAGE = False
    if R7:
        p7 = start(R7, 1)
        t_end = time.time() + 120
        while time.time() < t_end and kinds(R7, 1).count("done") < 2 and p7.poll() is None:
            time.sleep(0.01)
        p7.kill()
        p7.communicate()
        time.sleep(1.0)
        with open(R7 / "w001" / "journal.txt", "ab") as f:
            f.write(b'{"t":"done","game":"n12-w001-g000000')
        opened = list((R7 / "w001" / "open").glob("*.raw"))
        if opened:
            GARBAGE = True
            with open(opened[0], "ab") as f:
                f.write(b"garbage of a game that was never journalled\n")
        P["V7"] = start(R7, 1)
    EVID = (f"game n12-w001-g00000004 opening {' '.join(N12[3])}\n"
            f"sent position startpos moves {' '.join(N12[3])}\n").encode("ascii")
    KILL7 = {name: (root, plant) for name, root, plant in (("V7b", R7b, EVID),
                                                           ("V7c", R7c, b"garbage that names no game\n")) if root}
    if KILL7:
        pk = {name: start(root, 1) for name, (root, _) in KILL7.items()}
        alive7, t_end = set(pk), time.time() + 120
        while alive7:                                  # each killed the moment its third game is journalled
            for name in sorted(alive7):
                if time.time() > t_end or pk[name].poll() is not None or kinds(KILL7[name][0], 1).count("done") >= 3:
                    pk[name].kill()
                    pk[name].communicate()
                    alive7.discard(name)
            time.sleep(0.01)
        time.sleep(1.0)
        for name, (root, plant) in KILL7.items():
            for f in (root / "w001" / "open").glob("*.raw"):
                with open(f, "ab") as fh:
                    fh.write(plant)
            fence(root)
            P[name] = start(root, 1)
    OUT, ENDS = finish_all(P)
    if R2:
        common("V2", OUT["V2"], 4, "IDENTITY.json")
        check("V2 the slot folder is unchanged byte for byte", tree_bytes(R2 / "w001") == B2)
    if R2b:
        common("V2b", OUT["V2b"], 4, "no IDENTITY.json")
        check("V2b the slot folder is unchanged byte for byte", tree_bytes(R2b / "w001") == B2b)
    if R8:
        common("V8", OUT["V8"], 4, "journal line 3")
        check("V8 the journal is kept as it is", (R8 / "w001" / "journal.txt").read_bytes() == J8)
    if R9:
        common("V9", OUT["V9"], 0)
        check("V9 the seal is kept byte for byte, no second seal",
              (R9 / "w001" / "closed" / "p000001.seal.json").read_bytes() == SEAL9
              and sorted(f.name for f in (R9 / "w001" / "closed").iterdir() if "seal" in f.name)
              == ["p000000.seal.json", "p000001.seal.json"])
        j = jlines(R9, 1)
        check("V9 the journal ends: epoch 2, closed 1 with that seal's sha256, ended (finalizer)",
              [r["t"] for r in j[-3:]] == ["epoch", "closed", "ended"] and j[-3]["epoch"] == 2
              and j[-2] == {"t": "closed", "index": 1, "seal": sha(SEAL9)} and j[-1].get("why") == "finalizer", j[-3:])
    if R9b:
        common("V9b", OUT["V9b"], 4, "p000001.raw")
        jb = (R9b / "w001" / "journal.txt").read_bytes()
        check("V9b only the epoch line was added, the seal unchanged",
              jb.startswith(J9b) and [jline(ln)["t"] for ln in jb[len(J9b):].decode("ascii", "replace").splitlines()] == ["epoch"]
              and (R9b / "w001" / "closed" / "p000001.seal.json").read_bytes() == SEAL9b)
    if R7:
        common("V7", OUT["V7"], 0)
        log = logtext(R7, 1)
        check("V7 the unfinished journal line was dropped (worker.log names it)",
              "dropped the unfinished last journal line" in log, log[-300:])
        check("V7 the garbage was cut off (worker.log names it)", GARBAGE and "is cut off" in log, log[-300:])
        ids = [r["game"] for r in jlines(R7, 1) if r["t"] == "done"]
        check("V7 every id once", ids == [f"n12-w001-g{k:08d}" for k in range(1, 7)], ids)
        check("V7 the pieces are V1's byte for byte, ended (ranges done)",
              pieces(R7, 1) == V1_PIECES and ended_why(R7, 1) == "ranges done", list(pieces(R7, 1)))
        check("V7 no engine process left", engines_left(R7, 1) == [])
    for name, root in (("V7b", R7b), ("V7c", R7c)):
        if not root:
            continue
        common(name, OUT[name], 0)
        log, j, un = logtext(root, 1), jlines(root, 1), int(name == "V7b")
        k = max([i for i, r in enumerate(j) if r["t"] == "epoch"] or [0])
        tail = [(r["t"], r.get("game"), r.get("why"), r.get("index")) for r in j[k + 1:]]
        tail_want = [("closed", None, None, 0), ("ended", None, "finalizer", None)]
        if un:
            check("V7b worker.log names the cut and g4's failed line",
                  "is cut off; n12-w001-g00000004 gets a failed line" in log, log[-300:])
            tail_want.insert(0, ("failed", "n12-w001-g00000004",
                                 "its bytes lay beyond the journal's end and were cut at a restart", None))
        else:
            check("V7c worker.log names the cut and no failed line", "is cut off" in log and "failed line" not in log,
                  log[-300:])
        check(f"{name} after the epoch-2 line: {'failed g4, ' if un else ''}closed 0, ended (finalizer)",
              bool(j) and j[k].get("epoch") == 2 and tail == tail_want, j[k:])
        rsp = root / "ranges" / "r0001.w001.seal.json"
        rsj = json.loads(rsp.read_bytes()) if rsp.exists() else {}
        # 2.4: a finalizer at epoch 2 doubts the lowest open id; with the failed line (V7b) it is unfinished
        check(f"{name} the range seal: done 3, {'unfinished' if un else 'dispatch_unknown'} 1 (g4), never_dispatched 2, "
              f"not complete",
              rsj.get("dispositions") == {"dispatch_unknown": 1 - un, "done": 3, "never_dispatched": 2,
                                          "never_dispatched_first": 5, "noselfgame": 0, "refused": 0, "unfinished": un,
                                          "not_done": [["n12-w001-g00000004", "unfinished" if un else "dispatch_unknown"]]}
              and rsj.get("complete") is False, rsj)
        p0 = pieces(root, 1).get("p000000.raw", b"")
        check(f"{name} p000000 holds g1 to g3: V1's p000000 begins with its bytes",
              list(pieces(root, 1)) == ["p000000.raw"] and p0.count(b"\nbind ") + p0.startswith(b"bind ") == 3
              and V1_PIECES.get("p000000.raw", b"").startswith(p0), list(pieces(root, 1)))
        check(f"{name} no engine process left", engines_left(root, 1) == [])
    if R13:
        common("V13", OUT["V13"], 0)
        g4 = [r["t"] for r in jlines(R13, 1) if r.get("game") == "n12-w001-g00000004"]
        check("V13 g4 failed once, then done", g4 == ["failed", "done"], g4)
        check("V13 the pieces are V1's byte for byte", pieces(R13, 1) == V1_PIECES, list(pieces(R13, 1)))
        check("V13 no engine process left", engines_left(R13, 1) == [])
    if R13b:
        common("V13b", OUT["V13b"], 0)
        j4 = [r for r in jlines(R13b, 1) if r.get("game") == "n12-w001-g00000004"]
        check("V13b g4 failed once (the record module's row check), then done",
              [r["t"] for r in j4] == ["failed", "done"]
              and str(j4[0].get("why", "")).startswith("row: a row of n12-w001-g00000004 is not in its shape"), j4)
        check("V13b the pieces are V1's byte for byte", pieces(R13b, 1) == V1_PIECES, list(pieces(R13b, 1)))
        check("V13b no engine process left", engines_left(R13b, 1) == [])

# ================================================================ group 4: V17, V17b, V17c, V17d (one engine at a time)
if want("V17", "V17b", "V17c", "V17d"):
    R17 = make_root("v17", "anch", 0, [row(1, 3)], None, None, piece_games=1, boot="bootA")
    FP17 = sha((R17 / "RUN.json").read_bytes())

    def run_until(root, boot, seal_name, secs=180):
        """A start under `boot` that plays until ranges/<seal_name> exists; the STOP file then ends it (no `ended`)."""
        p = start(root, 0, boot=boot)
        t_end = time.time() + secs
        while time.time() < t_end and not (root / "ranges" / seal_name).exists() and p.poll() is None:
            time.sleep(0.1)
        put(root / "STOP", b"")
        out, _ = finish_all({"x": p}, 60)
        (root / "STOP").unlink()
        return out["x"]

    def seal_of(root, i):
        f = root / "w000" / "closed" / f"p{i:06d}.seal.json"
        return sha(f.read_bytes()) if f.exists() else None

    def write_resume(root, n, prev, old, rows_last, new="bootB"):
        put(root / f"RESUME.{n}.json", canon({
            "schema": 2, "run_fingerprint": FP17, "n": n, "prev": prev, "old_boot_id": old, "new_boot_id": new,
            "instance": "test-instance", "instance_provable": True, "checks": [], "at_utc": T(time.time()),
            "slots": [{"slot": 0, "last_index": rows_last[0], "last_seal": rows_last[1]}]}))

    common("V17 boot A", run_until(R17, "bootA", "r0001.w000.seal.json"), 0)
    j = jlines(R17, 0)
    check("V17 boot A: epoch (bootA, resume null), then g1 to g3 each done and closed (pieces 0 to 2)",
          [(r["t"], r.get("index")) for r in j] == [("epoch", None)] + [(t, i) for i in range(3) for t in ("done", "closed")]
          and j[0].get("boot_id") == "bootA" and j[0].get("resume") is None, j)
    s2 = seal_of(R17, 2)
    write_resume(R17, 1, "first", "bootA", (2, s2))                       # Astra 151303Z: RESUME.1 anchors piece 2 for boot B
    R1SHA = sha((R17 / "RESUME.1.json").read_bytes())
    schedule(R17, 1, [row(1, 3), row(4, 4, rnd=2, sched=1)], 3000, 3600)     # 2.4: an added row carries its n
    common("V17 boot B, first start", run_until(R17, "bootB", "r0002.w000.seal.json"), 0)
    j = jlines(R17, 0)
    check("V17 the first epoch line under boot B names RESUME.1 and piece 2",
          j[7:8] == [{"t": "epoch", "epoch": 2, "prev_epoch": 1, "last_index": 2, "last_seal": s2, "boot_id": "bootB",
                      "resume": R1SHA, "mode": "play"}], j[7:8])
    check("V17 boot B's first start played g4 into piece 3", [(r["t"], r.get("game"), r.get("index")) for r in j[8:]]
          == [("done", "anch-w000-g00000004", 3), ("closed", None, 3)], j[8:])
    s3 = seal_of(R17, 3)
    schedule(R17, 2, [row(1, 3), row(4, 4, rnd=2, sched=1), row(5, 5, rnd=3, sched=2)], 1800, 2400)
    R17b, R17c, R17d = WORK / "v17b", WORK / "v17c", WORK / "v17d"
    for r_ in (R17b, R17c, R17d):
        shutil.copytree(R17, r_)
    write_resume(R17b, 2, R1SHA, "bootB", (3, s3))        # a changed anchor: a newer RESUME for boot B, at today's head
    with open(R17b / "w000" / "journal.txt", "ab") as f:  # and a torn last line: cut only after the checks (2.4)
        f.write(b'{"bind":"')
    write_resume(R17d, 2, R1SHA, "bootB", (3, s3), new="bootC")   # the HIGHEST RESUME names another boot
    sf = R17c / "w000" / "closed" / "p000003.seal.json"
    broken = canon(dict(json.loads(sf.read_bytes()), prev_seal="0" * 64))   # a break between piece 2 and piece 3
    put(sf, broken)
    jf = R17c / "w000" / "journal.txt"
    assert jf.read_bytes().count(s3.encode()) == 1
    jf.write_bytes(jf.read_bytes().replace(s3.encode(), sha(broken).encode()))
    V17X = (("V17b", R17b), ("V17c", R17c), ("V17d", R17d))
    J17 = {name: (root / "w000" / "journal.txt").read_bytes() for name, root in V17X}
    P = {}
    for name, root in V17X:
        put(root / "STOP", b"")                         # a worker that is not stopped by the check ends at once
        P[name] = start(root, 0, boot="bootB")
    OUT, ENDS = finish_all(P, 120)
    common("V17b", OUT["V17b"], 4, "a changed anchor")
    common("V17c", OUT["V17c"], 4, "p000003.seal.json does not descend")
    common("V17d", OUT["V17d"], 4, "no RESUME record admits it")
    for name, root in V17X:
        check(f"{name} the journal is kept as it is (no epoch line" + (", the torn last line still there)" if
                                                                       name == "V17b" else ")"),
              (root / "w000" / "journal.txt").read_bytes() == J17[name])
    common("V17 boot B, second start", run_until(R17, "bootB", "r0003.w000.seal.json"), 0)
    j = jlines(R17, 0)
    check("V17 the second start under boot B: its epoch line carries resume null and piece 3, then g5 into piece 4",
          j[10:] == [{"t": "epoch", "epoch": 3, "prev_epoch": 2, "last_index": 3, "last_seal": s3, "boot_id": "bootB",
                      "resume": None, "mode": "play"}] + j[11:]
          and [(r["t"], r.get("game"), r.get("index")) for r in j[11:]] == [("done", "anch-w000-g00000005", 4),
                                                                             ("closed", None, 4)], j[10:])
    check("V17 no engine process left", engines_left(R17, 0) == [])

# ================================================================ group 5 (FORMATS 2.7: A1, A2, A3, A5): V20 to V27
def cut_kill(root, slot, lines):
    """The state a kill leaves right before the journal's last `lines` lines and the slot's range seals were written."""
    j = root / f"w{slot:03d}" / "journal.txt"
    keep = j.read_bytes().split(b"\n")[:-1][:-lines]
    put(j, b"".join(ln + b"\n" for ln in keep))
    for f in (root / "ranges").glob(f"*.w{slot:03d}.seal.json"):
        f.unlink()


def seal_of_round(root, slot, rnd=1):
    f = root / "ranges" / f"r{rnd:04d}.w{slot:03d}.seal.json"
    return json.loads(f.read_bytes()) if f.exists() else {}


def wait_done(root, slot, n, secs=120):
    t_end = time.time() + secs
    while time.time() < t_end and kinds(root, slot).count("done") < n:
        time.sleep(0.05)
    return kinds(root, slot).count("done")


def sched_bytes(root, n, rows, dispatch_text, cutoff_text, prev_bytes):
    return canon({"schema": 2, "run_fingerprint": sha((root / "RUN.json").read_bytes()), "n": n,
                  "prev": "first" if n == 1 else sha(prev_bytes), "evidence": "0" * 64, "cutoff_utc": cutoff_text,
                  "dispatch_end_utc": dispatch_text, "ranges": rows})


R20 = make_root("v20", "bar", 0, [row(1, 4)], 20, 30, game_line=SLOW_LINE) if want("V20", "V26", "V27") else None
R21 = make_root("v21", "fin", 0, [row(1, 3)], 30, 45, rule="seed", seed="fin") if want("V21") else None
R23 = make_root("v23", "cnt", 0, [row(1, 3), row(4, 6, rnd=2)], 40, 55) if want("V23") else None
R24 = make_root("v24", "two", 0, [row(1, 6)], 60, 75) if want("V24") else None
R25 = make_root("v25", "brk", 0, [row(1, 6)], 60, 75) if want("V25") else None
OPENS23 = WORK / "v23_schedule1_opens.txt"
P = {}
if R20:
    P["V20a"] = start(R20, 0, manifest=SLOW_MAN)
if R23:
    P["V23"] = start(R23, 0, audit=OPENS23)
if R24:
    P["V24"] = start(R24, 0)
if R25:
    P["V25"] = start(R25, 0)
D_AFTER = {}
for root, name in ((R23, "V23"), (R24, "V24"), (R25, "V25")):
    if not root:
        continue
    wait_done(root, 0, 1)
    s1b = (root / "SCHEDULE.1.json").read_bytes()
    s1 = json.loads(s1b)
    if name == "V23":               # round 2 has not started: shortened to 4 to 5 by schedule 2
        put(root / "SCHEDULE.2.json", sched_bytes(root, 2, [row(1, 3), dict(row(4, 5, rnd=2, sched=2), short=True)],
                                                  s1["dispatch_end_utc"], s1["cutoff_utc"], s1b))
    elif name == "V24":             # 3 first: whenever the worker finds 2, 3 is there too
        s2b = sched_bytes(root, 2, [row(1, 6)], s1["dispatch_end_utc"], s1["cutoff_utc"], s1b)
        put(root / "SCHEDULE.3.json", sched_bytes(root, 3, [row(1, 6)], T(time.time() - 5), s1["cutoff_utc"], s2b))
        put(root / "SCHEDULE.2.json", s2b)
    else:                           # a link that does not hold
        put(root / "SCHEDULE.2.json", sched_bytes(root, 2, [row(1, 6)], s1["dispatch_end_utc"], s1["cutoff_utc"],
                                                  b"not schedule 1"))
    D_AFTER[name] = kinds(root, 0).count("done")
OUT, ENDS = finish_all(P)

P2, BAD, J20 = {}, {}, None
if R20:
    cut_kill(R20, 0, 1)                         # killed before its range seal: epoch (play), unfinished g1
    J20 = (R20 / "w000" / "journal.txt").read_bytes()
    for name, g in (("V26", 2), ("V27", 9)):
        if want(name):
            r = WORK / name.lower()
            shutil.copytree(R20, r)
            BAD[name] = canon({"game": f"bar-w000-g{g:08d}", "t": "failed", "why": "a test"})
            put(r / "w000" / "journal.txt", J20 + BAD[name])
            P2[name] = start(r, 0, manifest=SLOW_MAN)
    if want("V20"):
        P2["V20"] = start(R20, 0, manifest=SLOW_MAN)
R22 = None
if R16 and want("V22"):
    R22 = WORK / "v22"
    shutil.copytree(R16, R22)
    cut_kill(R22, 0, 1)                         # V16's finalizer killed after its epoch line
    P2["V22"] = start(R22, 0, manifest=SLOW_MAN)
V21_RUNS = []
if R21:
    fence(R21)
    for k in range(3):                          # the finalizer; then killed after its epoch line, twice
        if k:
            cut_kill(R21, 0, 1)
        o, _ = finish_all({"x": start(R21, 0, openings=False)}, 60)
        V21_RUNS.append((o["x"], jlines(R21, 0), seal_of_round(R21, 0)))
OUT2, _ = finish_all(P2)

if R20 and want("V20"):
    common("V20 run 1", OUT["V20a"], 0)
    common("V20", OUT2["V20"], 0)
    j = jlines(R20, 0)
    check("V20 (A1) epoch 1 (play), unfinished g1 (cutoff), epoch 2 (seal_only), ended (finalizer)",
          [(r["t"], r.get("epoch"), r.get("mode"), r.get("game"), r.get("why")) for r in j] ==
          [("epoch", 1, "play", None, None), ("unfinished", None, None, "bar-w000-g00000001", "cutoff"),
           ("epoch", 2, "seal_only", None, None), ("ended", 2, None, None, "finalizer")], j)
    d = seal_of_round(R20, 0).get("dispositions")
    check("V20 (A1, 2.6) g1 unfinished is a BARRIER: unfinished 1, dispatch_unknown 0, never_dispatched 3 from 2",
          d == {"dispatch_unknown": 0, "done": 0, "never_dispatched": 3, "never_dispatched_first": 2, "noselfgame": 0,
                "refused": 0, "unfinished": 1, "not_done": [["bar-w000-g00000001", "unfinished"]]}, d)
    check("V20 the restart started no engine", logtext(R20, 0).count("engine started") == 1, logtext(R20, 0)[-300:])
    check("V20 no engine process left", engines_left(R20, 0) == [])
for name, text in (("V26", "after bar-w000-g00000001"), ("V27", "lies in no range")):
    if name in P2:
        r = WORK / name.lower()
        common(name, OUT2[name], 4, text)
        check(f"{name} (A5) the journal is kept byte for byte, no range seal",
              (r / "w000" / "journal.txt").read_bytes() == J20 + BAD[name]
              and not list((r / "ranges").glob("*.seal.json")), kinds(r, 0))
if R21:
    for k, (o, j, s) in enumerate(V21_RUNS, 1):
        common(f"V21 start {k}", o, 0)
        check(f"V21 (A2 a) start {k}: epochs 1 to {k} all seal_only, then ended (finalizer)",
              [(r["t"], r.get("epoch"), r.get("mode"), r.get("why")) for r in j] ==
              [("epoch", e, "seal_only", None) for e in range(1, k + 1)] + [("ended", k, None, "finalizer")], j)
        check(f"V21 start {k}: never_dispatched 3 from 1, dispatch_unknown 0 (2.7: no earlier play epoch)",
              s.get("dispositions") == {"dispatch_unknown": 0, "done": 0, "never_dispatched": 3,
                                        "never_dispatched_first": 1, "noselfgame": 0, "refused": 0, "unfinished": 0,
                                        "not_done": []}, s.get("dispositions"))
    check("V21 no engine was started", "engine started" not in logtext(R21, 0))
if R22:
    common("V22", OUT2["V22"], 0)
    j = jlines(R22, 0)
    check("V22 (A2 b) epoch 1 (play), epochs 2 and 3 (seal_only), ended (finalizer)",
          [(r["t"], r.get("epoch"), r.get("mode"), r.get("why")) for r in j] ==
          [("epoch", 1, "play", None), ("epoch", 2, "seal_only", None), ("epoch", 3, "seal_only", None),
           ("ended", 3, None, "finalizer")], j)
    d = seal_of_round(R22, 0).get("dispositions")
    check("V22 the SAME one unknown id as V16's single finalizer: g1 dispatch_unknown, never_dispatched 2 from 2",
          d == {"dispatch_unknown": 1, "done": 0, "never_dispatched": 2, "never_dispatched_first": 2, "noselfgame": 0,
                "refused": 0, "unfinished": 0, "not_done": [["doubt-w000-g00000001", "dispatch_unknown"]]}, d)
if R23:
    common("V23", OUT["V23"], 0)
    j = jlines(R23, 0)
    check("V23 (A3) round 2 shortened: done g1 to g5, never g6, ended (ranges done)",
          [r["game"] for r in j if r["t"] == "done"] == [f"cnt-w000-g{k:08d}" for k in range(1, 6)]
          and ended_why(R23, 0) == "ranges done", j)
    check("V23 the five records as n12_batch.json's first five (rows, end line, digest)",
          [[len(g["rows"]), g["end"], field_digest(g)] for g in recs(R23, 0)] == K_BATCH[:5])
    s2 = seal_of_round(R23, 0, 2)
    check("V23 round 2's range seal: 4 to 5, complete, short",
          s2.get("first") == 4 and s2.get("last") == 5 and s2.get("complete") is True and s2.get("short") is True, s2)
    n = OPENS23.read_text(encoding="ascii") if OPENS23.exists() else "no count written"
    check("V23 (2.6) SCHEDULE.1.json opened exactly once by the worker process", n == "1", n)
    check("V23 no engine process left", engines_left(R23, 0) == [])
if R24:
    common("V24", OUT["V24"], 0)
    n = kinds(R24, 0).count("done")
    check("V24 (A3, 2.7) schedules 2 and 3 together, 3's dispatch end past: no game reserved after them, ended (cutoff)",
          D_AFTER["V24"] < 6 and n <= D_AFTER["V24"] + 1 and ended_why(R24, 0) == "cutoff", (D_AFTER["V24"], n, kinds(R24, 0)))
    check("V24 the range seal names schedule 3", seal_of_round(R24, 0).get("schedule") == 3, seal_of_round(R24, 0))
    check("V24 no engine process left", engines_left(R24, 0) == [])
if R25:
    common("V25", OUT["V25"], 4, "SCHEDULE.2.json")
    n = kinds(R25, 0).count("done")
    check("V25 (A3, 2.6) a broken link authorizes nothing: no game reserved after it, no ended line",
          D_AFTER["V25"] < 6 and n <= D_AFTER["V25"] + 1 and "ended" not in kinds(R25, 0),
          (D_AFTER["V25"], n, kinds(R25, 0)))
    check("V25 no engine process left", engines_left(R25, 0) == [])

# ================================================================ group 6 (FORMATS 2.9, A4: the clocks and the watch)
def d_of(root):
    return calendar.timegm(time.strptime(json.loads((root / "SCHEDULE.1.json").read_bytes())["cutoff_utc"],
                                         "%Y-%m-%dT%H:%M:%SZ"))


def tgw(lines):
    return [(r["t"], r.get("game"), r.get("why")) for r in lines]


MID_LINE = MAN["selfgame_line"].replace("softnodes 2000 ", "softnodes 100000 ")
assert MID_LINE != MAN["selfgame_line"]
MID_MAN = WORK / "manifest_mid.json"
MID_MAN.write_bytes(json.dumps(dict(MAN, selfgame_line=MID_LINE)).encode("ascii"))
W6 = {}


def engine_up(root, secs=60):
    """True once the worker logged its engine's start: game 1 is reserved then and goes to the engine next."""
    t_end = time.time() + secs
    while time.time() < t_end:
        if "engine started: pid " in logtext(root, 0):
            return True
        time.sleep(0.05)
    return False


def tighten(root, name, dispatch_in, cutoff_in, keep_cutoff=False, align=False):
    """SCHEDULE.2.json written one second into game 1, the same range, its bounds in seconds from now (2.9: the
    watch's refresh takes it while the engine searches); with align the write is made just after a whole second
    (the bounds' texts are whole seconds). W6[name] = (the time it was written, D after it, the engine was up,
    games done at the write)."""
    up = engine_up(root)
    time.sleep(1.0)
    if align:
        time.sleep(1.02 - time.time() % 1.0)
    s1b = (root / "SCHEDULE.1.json").read_bytes()
    s1 = json.loads(s1b)
    now = time.time()
    cut = s1["cutoff_utc"] if keep_cutoff else T(now + cutoff_in)
    done = kinds(root, 0).count("done")
    put(root / "SCHEDULE.2.json", sched_bytes(root, 2, [row(1, 3)], T(now + dispatch_in), cut, s1b))
    W6[name] = (time.time(), calendar.timegm(time.strptime(cut, "%Y-%m-%dT%H:%M:%SZ")), up, done)


R28 = make_root("v28", "hold", 0, [row(1, 3)], 120, 135) if want("V28") else None
R29 = make_root("v29", "susp", 0, [row(1, 3)], 40, 60, game_line=SLOW_LINE) if want("V29") else None
R30 = make_root("v30", "back", 0, [row(1, 3)], 15, 25, game_line=SLOW_LINE) if want("V30") else None
R31 = make_root("v31", "nost", 0, [row(1, 3)], 15, 25, game_line=SLOW_LINE) if want("V31") else None
R33 = make_root("v33", "tigh", 0, [row(1, 3)], 40, 60, game_line=SLOW_LINE) if want("V33") else None
R34 = make_root("v34", "past", 0, [row(1, 3)], 40, 60, game_line=SLOW_LINE) if want("V34") else None
R34a = make_root("v34a", "ldis", 0, [row(1, 3)], 40, 60, game_line=SLOW_LINE) if want("V34a") else None
R36 = make_root("v36", "lgon", 0, [row(1, 3)], 15, 25, game_line=SLOW_LINE) if want("V36") else None
P = {}
if R28:
    P["V28"] = start(R28, 0, plant="clock_forward:2")
for name, root, plant in (("V29", R29, "clock_suspend:1"), ("V30", R30, "clock_back:1"),
                          ("V31", R31, "watch_nostop:1"), ("V33", R33, None), ("V34", R34, None),
                          ("V34a", R34a, None), ("V36", R36, "watch_lategone:1")):
    if root:
        P[name] = start(root, 0, manifest=SLOW_MAN, plant=plant)
if R33:
    tighten(R33, "V33", 4, 10)          # D 10 s from now: the watch ends the search at that D less the allowance
if R34a:
    tighten(R34a, "V34a", -8, 2, align=True)    # D the whole second 2 s on: its trigger passed when found, D not
if R34:
    tighten(R34, "V34", -8, -3)         # D 3 s ago: found after D, acted on at once, the alarm
OUT6, ENDS6 = finish_all(P)
P, J28 = {}, b""
R32 = make_root("v32", "hfwd", 0, [row(1, 3)], 40, 60, game_line=SLOW_LINE) if want("V32") else None
R35 = make_root("v35", "disp", 0, [row(1, 3)], 100, 120, game_line=MID_LINE) if want("V35") else None
if R28:
    J28 = (R28 / "w000" / "journal.txt").read_bytes() if (R28 / "w000" / "journal.txt").exists() else b""
    P["V28b"] = start(R28, 0)
if R32:
    P["V32"] = start(R32, 0, manifest=SLOW_MAN, plant="clock_forward:1")
if R35:
    P["V35"] = start(R35, 0, manifest=MID_MAN)
    tighten(R35, "V35", -2, 0, keep_cutoff=True)    # the dispatch end 2 s ago, D unchanged, game 1 in flight
OUT6b, ENDS6b = finish_all(P, secs=300)

if R28:
    common("V28", OUT6["V28"], 8, "ALARM clock:")
    j1 = [jline(ln) for ln in J28.decode("ascii").splitlines()]
    check("V28 (A4, the hold) epoch (play), done g1, failed g2 (why clock), closed (g1's piece), NO ended line",
          tgw(j1) == [("epoch", None, None), ("done", "hold-w000-g00000001", None),
                      ("failed", "hold-w000-g00000002", "clock"), ("closed", None, None)]
          and j1[0].get("mode") == "play" and j1[3].get("index") == 0, j1)
    lg = logtext(R28, 0)
    check("V28 worker.log names the plant and holds the ALARM clock line after it",
          "PLANT clock_forward" in lg and "ALARM clock:" in lg.split("PLANT clock_forward")[-1], lg[-500:])
    common("V28b", OUT6b["V28b"], 0)
    j2 = jlines(R28, 0)[len(j1):]
    check("V28b a start with right clocks: epoch 2 (play), done g2 and g3, closed, ended (ranges done)",
          tgw(j2) == [("epoch", None, None), ("done", "hold-w000-g00000002", None),
                      ("done", "hold-w000-g00000003", None), ("closed", None, None), ("ended", None, "ranges done")]
          and j2[0].get("epoch") == 2 and j2[0].get("mode") == "play", j2)
    check("V28b the three records as n12_batch.json's first three (the retry gives g2's record back)",
          [[len(g["rows"]), g["end"], field_digest(g)] for g in recs(R28, 0)] == K_BATCH[:3])
    s = seal_of_round(R28, 0)
    check("V28b the range seal: done 3, complete", s.get("complete") is True and (s.get("dispositions") or {}).get(
        "done") == 3, s)
    check("V28 no engine process left", engines_left(R28, 0) == [])
if R29:
    common("V29", OUT6["V29"], 8, "ALARM watch: decided after D:")
    check("V29 (A4, a suspension past D) epoch, unfinished g1 (cutoff), NO ended line, no range seal",
          tgw(jlines(R29, 0)) == [("epoch", None, None), ("unfinished", "susp-w000-g00000001", "cutoff")]
          and seal_of_round(R29, 0) == {}, (jlines(R29, 0), seal_of_round(R29, 0)))
    lg = logtext(R29, 0)
    check("V29 the watch decided with reason cutoff, late and decided_after_cutoff (D had come), and found the "
          "native process gone", "PLANT clock_suspend" in lg and "watch decision reason=cutoff late=True" in lg
          and " decided_after_cutoff=True" in lg and "watch native process gone" in lg, lg[-700:])
    check("V29 the worker ended 20 s or more before the real D", ENDS6["V29"] < d_of(R29) - 20,
          f"{ENDS6['V29'] - d_of(R29):.1f} s")
    check("V29 no engine process left", engines_left(R29, 0) == [])
if R30:
    common("V30", OUT6["V30"], 0)
    check("V30 (A4, UTC set back an hour) epoch, unfinished g1 (cutoff), ended (cutoff)",
          tgw(jlines(R30, 0)) == [("epoch", None, None), ("unfinished", "back-w000-g00000001", "cutoff"),
                                  ("ended", None, "cutoff")], jlines(R30, 0))
    lg = logtext(R30, 0)
    check("V30 the watch decided at D less the allowance, not late, the native process gone before D",
          "PLANT clock_back" in lg and "watch decision reason=cutoff late=False" in lg
          and "watch native process gone after_cutoff=False" in lg, lg[-700:])
    late = ENDS6["V30"] - d_of(R30)
    check("V30 the cutoff holds: the worker ended within 3 s of D (not an hour later)", -3 <= late < 3, f"{late:.1f} s")
    check("V30 the worker outlived its engine's stop (that process alone, never a group): the stop line names its "
          "handle, the worker's own end line comes after it",
          "watch stop sent how=" in lg and "the slot has ended" in lg.split("watch stop sent how=")[-1], lg[-700:])
    check("V30 no engine process left", engines_left(R30, 0) == [])
if R31:
    common("V31", OUT6["V31"], 8, "ALARM watch:")
    check("V31 (A4, a watch whose stop does nothing) epoch, unfinished g1 (cutoff), NO ended line",
          tgw(jlines(R31, 0)) == [("epoch", None, None), ("unfinished", "nost-w000-g00000001", "cutoff")],
          jlines(R31, 0))
    lg = logtext(R31, 0)
    check("V31 worker.log names the native process still there at D",
          "PLANT watch_nostop" in lg and "ALARM watch: the native process is still there at D" in lg, lg[-700:])
    check("V31 the worker's alarm line names the kind: still there, with the readings of decision, stop and exit",
          "ALARM watch: still there: " in OUT6["V31"][1] and " decision utc=" in OUT6["V31"][1]
          and " stop utc=" in OUT6["V31"][1] and " gone none" in OUT6["V31"][1], OUT6["V31"][1][-500:])
    late = ENDS6["V31"] - d_of(R31)
    check("V31 the alarm came at D: the worker ended within 5 s after D, not before D less 1 s", -1 <= late < 5,
          f"{late:.1f} s")
    check("V31 no engine process left (the worker ends it)", engines_left(R31, 0) == [])
if R32:
    common("V32", OUT6b["V32"], 8, "ALARM clock:")
    check("V32 (A4, the hold in a long game) epoch, failed g1 (why clock), NO ended line",
          tgw(jlines(R32, 0)) == [("epoch", None, None), ("failed", "hfwd-w000-g00000001", "clock")], jlines(R32, 0))
    lg = logtext(R32, 0)
    check("V32 the watch decided with reason clock and found the native process gone",
          "watch decision reason=clock" in lg and "watch native process gone" in lg, lg[-700:])
    check("V32 the worker ended 20 s or more before D", ENDS6b["V32"] < d_of(R32) - 20,
          f"{ENDS6b['V32'] - d_of(R32):.1f} s")
    check("V32 no engine process left", engines_left(R32, 0) == [])
for name, root in (("V33", R33), ("V34a", R34a), ("V34", R34), ("V36", R36)):
    if not root:
        continue
    alarm = {"V33": "", "V34a": "", "V34": "ALARM watch: decided after D:", "V36": "ALARM watch: gone after D:"}[name]
    common(name, OUT6[name], 8 if alarm else 0, alarm)
    wt, d_new, up, _ = W6.get(name, (None, None, True, None))
    run = json.loads((root / "RUN.json").read_bytes())["run"]
    want_j = [("epoch", None, None), ("unfinished", f"{run}-w000-g00000001", "cutoff")]
    s = seal_of_round(root, 0)
    if alarm:
        check(f"{name} (A4) epoch, unfinished g1 (cutoff), NO ended line, no range seal",
              tgw(jlines(root, 0)) == want_j and s == {}, (jlines(root, 0), s))
    else:
        check(f"{name} (A4) epoch, unfinished g1 (cutoff), ended (cutoff); the range seal names schedule 2",
              tgw(jlines(root, 0)) == want_j + [("ended", None, "cutoff")] and s.get("schedule") == 2,
              (jlines(root, 0), s))
    lg = logtext(root, 0)
    dec = next((ln for ln in lg.splitlines() if "watch decision " in ln), "")
    kv = dict(x.split("=", 1) for x in dec.split() if "=" in x)
    try:
        left, utc_dec = float(kv["left_to_cutoff_s"]), float(kv["utc"])
    except (KeyError, ValueError):
        left, utc_dec = None, None
    if name == "V33":
        check("V33 the watch took the tighter D while the engine searched: decided not late, the process gone before D",
              up and kv.get("reason") == "cutoff" and kv.get("late") == "False" and kv.get("late_discovery") == "False"
              and kv.get("decided_after_cutoff") == "False" and "watch native process gone after_cutoff=False" in lg,
              lg[-700:])
        late = ENDS6[name] - d_new
        check("V33 the worker ended within 3 s of the NEW D (the old one was 50 s later)", -3 <= late < 3,
              f"{late:.1f} s")
    elif name == "V36":
        check("V36 the watch decided at D less the allowance, not late; the exit confirmed only after D; the module's "
              "alarm says so", "PLANT watch_lategone" in lg and kv.get("reason") == "cutoff" and kv.get("late") ==
              "False" and kv.get("late_discovery") == "False" and kv.get("decided_after_cutoff") == "False"
              and "watch native process gone after_cutoff=True" in lg
              and "ALARM watch: the native process was first confirmed gone after D" in lg, lg[-700:])
        late = ENDS6[name] - d_of(root)
        check("V36 the worker ended within 3 s after D and not before D less 0.5 s", -0.5 <= late < 3,
              f"{late:.1f} s")
    elif name == "V34a":
        g = next((ln for ln in lg.splitlines() if "watch native process gone " in ln), "")
        try:
            utc_gone = float(dict(x.split("=", 1) for x in g.split() if "=" in x)["utc"])
        except (KeyError, ValueError):
            utc_gone = None
        check("V34a the tighter D found after its trigger and before D: decided at once, late and late_discovery, "
              "not decided_after_cutoff, after the write with 0 to 2 s left to D",
              up and kv.get("reason") == "cutoff" and kv.get("late") == "True" and kv.get("late_discovery") == "True"
              and kv.get("decided_after_cutoff") == "False" and left is not None and 0 < left < 2
              and wt - 0.05 <= utc_dec <= wt + 2, (dec, wt, d_new))
        check("V34a the process gone before D (the gone reading's utc before D)", "watch native process gone "
              "after_cutoff=False" in lg and utc_gone is not None and utc_gone < d_new, (g, d_new))
    else:
        check("V34 the tighter D found after D: decided at once, late, late_discovery and decided_after_cutoff, with "
              "the real readings (left negative, its utc = D less left, after the write and within 2 s of it)",
              up and kv.get("reason") == "cutoff" and kv.get("late") == "True" and kv.get("late_discovery") == "True"
              and kv.get("decided_after_cutoff") == "True" and left is not None and left < 0
              and abs(utc_dec - d_new + left) < 1 and wt - 0.05 <= utc_dec <= wt + 2, (dec, wt, d_new))
        check("V34 the process found gone after D", "watch native process gone after_cutoff=True" in lg, lg[-700:])
        check("V34 the worker ended within 4 s after the write", ENDS6[name] - wt < 4, f"{ENDS6[name] - wt:.1f} s")
    check(f"{name} no engine process left", engines_left(root, 0) == [])
if R35:
    common("V35", OUT6b["V35"], 0)
    wt, d_in, up, done_at_write = W6["V35"]
    j = jlines(R35, 0)
    check("V35 (A4, the dispatch end alone) game 1 keeps its normal end: epoch, done g1, closed, ended (cutoff)",
          tgw(j) == [("epoch", None, None), ("done", "disp-w000-g00000001", None), ("closed", None, None),
                     ("ended", None, "cutoff")], j)
    check("V35 game 1 was in flight when SCHEDULE.2 moved the dispatch end into the past (the engine up, no game "
          "done at the write)", up and done_at_write == 0, (up, done_at_write))
    lg = logtext(R35, 0)
    check("V35 the watch never decided (the dispatch end alone is no reason)", "watch decision" not in lg, lg[-700:])
    s = seal_of_round(R35, 0)
    check("V35 the range seal: schedule 2, done 1, never_dispatched 2 from 2",
          s.get("schedule") == 2 and s.get("dispositions") == {
              "dispatch_unknown": 0, "done": 1, "never_dispatched": 2, "never_dispatched_first": 2, "noselfgame": 0,
              "refused": 0, "unfinished": 0, "not_done": []}, s)
    check("V35 no engine process left", engines_left(R35, 0) == [])

# ================================================================ V37: the watch's refresh only reads (in-process)
if want("V37"):
    import dis
    import inspect
    import types
    fn = getattr(getattr(W, "Worker", None), "refresh", None)
    ws = inspect.getsource(W.Worker.watch_start) if W is not None and hasattr(W, "Worker") else ""
    check("V37 the watch's refresh is Worker.refresh, not follow_next", fn is not None
          and "refresh=self.refresh" in ws and "refresh=self.follow_next" not in ws, ws[-300:])
    CHANGING = {"append", "extend", "insert", "pop", "remove", "clear", "update", "setdefault", "add", "discard",
                "popitem", "sort", "reverse"}
    ops = [(i.opname, i.argval) for i in dis.get_instructions(fn)] if fn is not None else []
    stores = [(o, a) for o, a in ops if o in ("STORE_ATTR", "DELETE_ATTR", "STORE_SUBSCR", "DELETE_SUBSCR",
                                              "STORE_GLOBAL", "DELETE_GLOBAL")
              or (o in ("LOAD_ATTR", "LOAD_METHOD") and a in CHANGING)]
    check("V37 Worker.refresh stores nothing: no attribute or item stored or deleted, no method that changes its "
          "object", fn is not None and ops and not stores, stores)
    R37 = make_root("v37", "rfsh", 0, [row(1, 3)], 40, 60)

    class FakeB:
        def __init__(self):
            self.calls = []

        def set(self, name, v):
            self.calls.append((name, v))
    try:
        h = json.loads((R37 / "RUN.json").read_bytes())
        s1b = (R37 / "SCHEDULE.1.json").read_bytes()
        fs = types.SimpleNamespace(run_fp=sha((R37 / "RUN.json").read_bytes()), h=h, slot=0, root=R37, states={},
                                   top=0, B=FakeB())
        fs.follow = types.MethodType(W.Worker.follow, fs)
        hc = W.utc(h["hard_cutoff_utc"], "RUN.json")
        fs.snap = (fs.follow(1, s1b, (h["pilot_ranges"], hc, hc, 0, b"", h["hard_cutoff_utc"]), 0), 0)
        now = time.time()
        dt, ct = T(now + 4), T(now + 10)
        put(R37 / "SCHEDULE.2.json", sched_bytes(R37, 2, [row(1, 3)], dt, ct, s1b))
        before = {k: repr(v) for k, v in vars(fs).items() if k != "B"}
        fn(fs)
        after = {k: repr(v) for k, v in vars(fs).items() if k != "B"}
        got1 = (fs.B.calls == [("cutoff", W.utc(ct, "c")), ("dispatch_end", W.utc(dt, "d"))] and before == after,
                (fs.B.calls, [k for k in before if before[k] != after.get(k)]))
        fs.B.calls.clear()
        put(R37 / "SCHEDULE.2.json", sched_bytes(R37, 2, [row(1, 3)], dt, T(now + 3600), s1b))
        try:
            fn(fs)
            raised = None
        except Exception as e:  # noqa: BLE001
            raised = f"{type(e).__name__}: {e}"
        got2 = (raised is None and fs.B.calls == [], (raised, fs.B.calls))
    except Exception as e:  # noqa: BLE001   an old tree without refresh() or follow()'s arguments
        got1 = got2 = (False, f"{type(e).__name__}: {e}")
    check("V37 SCHEDULE.2 on disk: the refresh gives its D and dispatch end to the clocks, in this order, and no "
          "attribute of the worker changes", *got1)
    check("V37 a SCHEDULE.2 that does not follow (a later D) is left: nothing given to the clocks, no raise", *got2)
    for stalled in (True, False):
        said = []
        fw = types.SimpleNamespace(close=lambda: None, lines=lambda: ["watch decision reason=cutoff late=False"],
                                   reader_stalled=stalled)
        try:
            W.Worker.watch_end(types.SimpleNamespace(say=said.append), fw)
            err = None
        except Exception as e:  # noqa: BLE001
            err = f"{type(e).__name__}: {e}"
        check(f"V37 watch_end with reader_stalled {stalled}: " + ("the line `watch reader_stalled=True`" if stalled
              else "no reader_stalled line"), err is None and stalled == any("watch reader_stalled=True" in x
                                                                            for x in said), (err, said))

# ================================================================ group 7 (version 2): T1, V38 to V47
if want("T1a", "T1b", "T1c", "T1d", "T1e"):
    # T-a: a process of the test's own is known by number AND creation time; another creation time stands in for a
    # number Windows has given again: neither counted nor ended
    sp = subprocess.Popen([sys.executable, "-I", "-B", "-c", "import time; time.sleep(60)"])
    c1 = created_of(sp.pid)
    check("T1a a stand-in: alive by its number and creation time", alive(sp.pid, c1), c1)
    check("T1b its creation time is an integer", type(c1) is int, c1)
    check("T1c alive by its number and ANOTHER creation time: False", not alive(sp.pid, (c1 or 0) + 1))
    kill(sp.pid, (c1 or 0) + 1)
    time.sleep(1.0)
    check("T1d a kill by its number and another creation time: it still lives 1 s later", sp.poll() is None, sp.poll())
    kill(sp.pid, c1)
    try:
        code1 = sp.wait(10)
    except subprocess.TimeoutExpired:
        code1 = None
    check("T1e a kill by its number and creation time: ended within 10 s", code1 is not None, code1)
    sp.kill()
    sp.wait()


def resume_rec(root, n, prev, old, new, last=-1, **extra):
    fp_ = sha((root / "RUN.json").read_bytes())
    return dict({"schema": 2, "run_fingerprint": fp_, "n": n, "prev": prev, "old_boot_id": old, "new_boot_id": new,
                 "instance": "test-instance", "instance_provable": True, "checks": [], "at_utc": T(time.time()),
                 "slots": [{"slot": 0, "last_index": last, "last_seal": f"genesis:{fp_}:w000"}]}, **extra)


def fence_rec(root, **extra):
    return dict({"run_fingerprint": sha((root / "RUN.json").read_bytes()), "at_utc": T(time.time()),
                 "cutoff_utc": d_in_force(root), "schema": 2, "why": "a test"}, **extra)


PROCS2, ROOTS2 = {}, {}
# V38: a range seal that exists is judged as a piece seal is (W1); from V3's root after its run
if R3:
    seal3 = R3 / "ranges" / "r0001.w000.seal.json"
    if seal3.exists():
        s3 = json.loads(seal3.read_bytes())
        first3 = (R3 / "w000" / "journal.txt").read_bytes().split(b"\n")[0] + b"\n"
        for name, data in (("V38a", seal3.read_bytes()),
                           ("V38b", canon(dict(s3, run="other", run_fingerprint="e" * 64))),
                           ("V38c", b""),
                           ("V38d", canon(dict(s3, complete=True, dispositions=dict(s3.get("dispositions") or {}, done=3,
                                                                                    never_dispatched=0)))),
                           ("V38e", canon(dict(s3, epoch=7)))):
            if want(name):
                r_ = WORK / name.lower()
                shutil.copytree(R3, r_)
                (r_ / "w000" / "journal.txt").write_bytes(first3)
                (r_ / "ranges" / "r0001.w000.seal.json").write_bytes(data)
                ROOTS2[name] = (r_, data)
                PROCS2[name] = start(r_, 0, openings=False)
    else:
        for name in ("V38a", "V38b", "V38c", "V38d", "V38e"):
            if want(name):
                check(f"{name} V3's range seal exists to start from", False, "no ranges/r0001.w000.seal.json")


def edge_root(name, boot=None):
    return make_root(name, "edge", 0, [row(1, 1)], 20, 35, rule="seed", seed="edge2649", boot=boot)


# V39, V40: the RESUME chain walked at every start, old_boot_id linked, n type-strict (W2, W3)
if want("V39a"):
    r_ = edge_root("v39a")
    put(r_ / "RESUME.1.json", canon(resume_rec(r_, 1, "first", BOOT, "bootb")))
    ROOTS2["V39a"], PROCS2["V39a"] = (r_, None), start(r_, 0, openings=False)
if want("V39b"):
    r_ = edge_root("v39b")
    put(r_ / "RESUME.1.json", b"junk\n")
    ROOTS2["V39b"], PROCS2["V39b"] = (r_, None), start(r_, 0, openings=False)
if want("V40a"):
    r_ = edge_root("v40a", "otherboot")
    put(r_ / "RESUME.1.json", canon(resume_rec(r_, 1, "first", "WRONG-BOOT-ID", BOOT)))
    ROOTS2["V40a"], PROCS2["V40a"] = (r_, None), start(r_, 0, openings=False)
for name, old2 in (("V40b", "bootb"), ("V40c", "boot9")):
    if want(name):
        r_ = edge_root(name.lower(), "otherboot")
        put(r_ / "RESUME.1.json", canon(resume_rec(r_, 1, "first", "otherboot", "bootb")))
        put(r_ / "RESUME.2.json", canon(resume_rec(r_, 2, sha((r_ / "RESUME.1.json").read_bytes()), old2, BOOT)))
        ROOTS2[name], PROCS2[name] = (r_, sha((r_ / "RESUME.2.json").read_bytes())), start(r_, 0, openings=False)
if want("V40d"):
    r_ = edge_root("v40d", "otherboot")
    put(r_ / "RESUME.1.json", canon(resume_rec(r_, True, "first", "otherboot", BOOT)))   # n = true, not 1
    ROOTS2["V40d"], PROCS2["V40d"] = (r_, None), start(r_, 0, openings=False)


def late_root(name, hdr=None):
    return make_root(name, "late", 0, [row(1, 3)], -60, -30, rule="seed", seed="late", hdr=hdr)


def listing(folder: Path) -> list:
    return sorted((str(p.relative_to(folder)), p.read_bytes() if p.is_file() else None) for p in folder.rglob("*"))


# V41: a slot folder without IDENTITY.json holds only what claim_slot leaves before it (W4)
for name, files in (("V41a", {"closed/p000001.seal.json": b"x\n"}), ("V41b", {"LOCK": b""}),
                    ("V41c", {"LOCK": b"", "IDENTITY.json.tmp": b"half"})):
    if want(name):
        r_ = late_root(name.lower())
        for rel, data in files.items():
            (r_ / "w000" / rel).parent.mkdir(parents=True, exist_ok=True)
            (r_ / "w000" / rel).write_bytes(data)
        ROOTS2[name], PROCS2[name] = (r_, listing(r_ / "w000")), start(r_, 0, openings=False)
# V42: the lease times are read (W5)
if want("V42a", "V42b", "V42c"):
    t0 = time.time()
    for name, hdr in (("V42a", {"lease_end_utc": "2026-11-31T00:00:00Z"}),
                      ("V42b", {"hard_cutoff_utc": T(t0 + 86400 + 3600), "lease_end_utc": T(t0 + 86400)}),
                      ("V42c", {"lease_start_utc": T(t0 + 86400 + 60), "lease_end_utc": T(t0 + 86400)})):
        if want(name):
            r_ = late_root(name.lower(), hdr)
            ROOTS2[name], PROCS2[name] = (r_, None), start(r_, 0, openings=False)
# V43: FENCE.json is the guard's record (W6)
for name, rec in (("V43a", "schema1"), ("V43b", "extra"), ("V43c", "list")):
    if want(name):
        r_ = make_root(name.lower(), "fence", 0, [row(1, 2)], 30, 45, rule="seed", seed="fence")
        put(r_ / "FENCE.json", canon([] if rec == "list" else fence_rec(r_, schema=1) if rec == "schema1"
                                     else fence_rec(r_, x=1)))
        ROOTS2[name], PROCS2[name] = (r_, None), start(r_, 0, openings=False)
OUT2, _ = finish_all(PROCS2, 180) if PROCS2 else ({}, {})

for name in ("V38a", "V38b", "V38c", "V38d", "V38e"):
    if name in ROOTS2:
        r_, data = ROOTS2[name]
        sp_ = r_ / "ranges" / "r0001.w000.seal.json"
        k = kinds(r_, 0)
        if name == "V38a":
            common(name, OUT2[name], 0)
            check("V38a the seal kept byte for byte; journal epoch, epoch, ended (finalizer)", sp_.read_bytes() == data
                  and k == ["epoch", "epoch", "ended"] and ended_why(r_, 0) == "finalizer", k)
        else:
            common(name, OUT2[name], 4, "r0001.w000.seal.json")
            check(f"{name} the seal unchanged; journal epoch, epoch, NO ended", sp_.read_bytes() == data
                  and k == ["epoch", "epoch"], k)
for name, text in (("V39a", "no RESUME record admits it"), ("V39b", "RESUME.1.json"), ("V40a", "RESUME.1.json"),
                   ("V40c", "RESUME.2.json"), ("V40d", "RESUME.1.json"), ("V41a", "no IDENTITY.json"),
                   ("V42a", "lease_end_utc"), ("V42b", "hard_cutoff_utc"), ("V42c", "lease_start_utc"),
                   ("V43a", "FENCE.json"), ("V43b", "FENCE.json"), ("V43c", "FENCE.json")):
    if name in ROOTS2:
        r_, before = ROOTS2[name]
        common(name, OUT2[name], 4, text)
        if name == "V41a":
            check("V41a the slot folder as before (no LOCK, no IDENTITY.json)", listing(r_ / "w000") == before,
                  [x[0] for x in listing(r_ / "w000")])
        else:
            check(f"{name} no slot folder", not (r_ / "w000").exists())
if "V40b" in ROOTS2:
    r_, sha2 = ROOTS2["V40b"]
    common("V40b", OUT2["V40b"], 0)
    j = jlines(r_, 0)
    check("V40b the epoch line's resume is RESUME.2's sha256", bool(j) and j[0].get("t") == "epoch"
          and j[0].get("resume") == sha2 and j[0].get("boot_id") == BOOT, j[:1])
for name in ("V41b", "V41c"):
    if name in ROOTS2:
        r_, _ = ROOTS2[name]
        common(name, OUT2[name], 0)
        check(f"{name} the finalizer's journal epoch, ended; no .tmp left", kinds(r_, 0) == ["epoch", "ended"]
              and ended_why(r_, 0) == "finalizer" and not list((r_ / "w000").rglob("*.tmp")), kinds(r_, 0))
if R16 and want("V45"):
    check("V45 the engine line names pid N created C (W9)", len(C16) == 1 and C16[0][1] is not None, C16)
    check("V45 while the worker lived, created_of(N) == C", len(C16) == 1 and C16[0][1] is not None
          and C16[0][1] == C16[0][2], C16)
    check("V45 kill(N, C) ended the orphan: alive(N, C) False", len(GONE16) == 1 and GONE16[0][1] is not None
          and GONE16[0][2] is False, GONE16)
if want("V47"):
    got47 = {}
    fake47 = types.SimpleNamespace(eng=None, ph=None, kill_engine=lambda: None)

    def second():
        try:
            W.Worker.start_engine(fake47)
            got47["e"] = None
        except Exception as e:  # noqa: BLE001
            got47["e"] = e

    th47 = threading.Thread(target=second)
    th47.start()
    th47.join(30)
    e47 = got47.get("e")
    check("V47 start_engine inside a second thread: StartRefused naming `main thread`", W is not None
          and isinstance(e47, getattr(W, "StartRefused", ())) and "main thread" in str(e47), repr(e47))
    check("V47 eng stays None", fake47.eng is None, fake47.eng)

if want("V48"):                                         # W10 (24 Nov 00:48): the combined package, test_bootguard E2
    gone48 = WORK / "v48" / "w002"
    try:
        r48 = W.Worker.check_identity(types.SimpleNamespace(dir=gone48, name="w002"), b"{}\n")
    except Exception as e:  # noqa: BLE001
        r48 = e
    check("V48 check_identity on a slot folder that does not exist (a slot never started, as the boot guard reads "
          "it): returns None, the folder still absent", r48 is None and not gone48.exists(), repr(r48))
if want("V48b"):
    stray48 = WORK / "v48b" / "w002"
    stray48.mkdir(parents=True)
    (stray48 / "stray.txt").write_bytes(b"x")
    try:
        W.Worker.check_identity(types.SimpleNamespace(dir=stray48, name="w002"), b"{}\n")
        e48b = None
    except Exception as e:  # noqa: BLE001
        e48b = e
    check("V48b control: a folder holding a stray file and no IDENTITY.json: Stop 4 naming `no IDENTITY.json`",
          W is not None and isinstance(e48b, W.Stop) and e48b.code == 4 and "no IDENTITY.json" in str(e48b),
          repr(e48b))

# ---- Linux only (the seats run them): V44, V46 to V46e
LINUX = ("V44", "V46", "V46b", "V46c", "V46d", "V46e")
if os.name == "nt":
    for name in LINUX:
        if want(name):
            print(f"SKIP {name} (Linux only: the seats run it)")
else:
    BIND = TREE / "run" / "bind_exec.py"
    if want("V44"):
        r_ = make_root("v44", "pfd", 0, [row(1, 2)], 30, 45)
        p44 = start(r_, 0, inject="worker.clockwatch.ProcHandle = type('Q', (worker.clockwatch.ProcHandle,), "
                                  "{'__init__': lambda s, p, _P=worker.clockwatch.ProcHandle: "
                                  "(_P.__init__(s, p), setattr(s, 'how', 'popen'))[0]}); ")
        o44, _ = finish_all({"x": p44}, 120)
        common("V44", o44["x"], 5, "pidfd")
        check("V44 journal epoch only, no game", kinds(r_, 0) == ["epoch"], kinds(r_, 0))
        check("V44 no engine process left", engines_left(r_, 0) == [])

    def slow_kill(name, inject=None, via_guard=False):
        """The slow game of V16; the worker (or a stand-in guard and its worker) SIGKILLed at `>>> selfgame`; then
        [(N, C, alive 1 s later)] of its engines; the test itself ends nothing before that look."""
        r_ = make_root(name, "doubt", 0, [row(1, 3)], 60, 75, game_line=SLOW_LINE)
        if not via_guard:
            p = start(r_, 0, manifest=SLOW_MAN, trace=True, inject=inject)
            wpid, wc = p.pid, created_of(p.pid)
        else:
            cmd = start(r_, 0, manifest=SLOW_MAN, trace=True, dry=True)      # its command, run by the stand-in
            pidf = WORK / f"{name}.worker.pid"
            p = subprocess.Popen([sys.executable, "-I", "-B", "-c",
                                  "import subprocess, sys, time; w = subprocess.Popen(sys.argv[2:]); "
                                  "open(sys.argv[1], 'w').write(str(w.pid)); w.wait(); time.sleep(600)",
                                  str(pidf), *cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            t_end = time.time() + 30
            while time.time() < t_end and not pidf.exists():
                time.sleep(0.05)
            wpid = int(pidf.read_text()) if pidf.exists() else None
            wc = created_of(wpid) if wpid else None
        t_end = time.time() + 120
        while time.time() < t_end and ">>> selfgame" not in logtext(r_, 0) and p.poll() is None:
            time.sleep(0.01)
        pcs = started(r_, 0)
        if via_guard:
            p.kill()                                    # the stand-in guard: the test's own child, by its Popen
        kill(wpid, wc)
        p.communicate(timeout=10)
        time.sleep(1.0)
        res = [(n, c, alive(n, c)) for n, c in pcs]
        for n, c in pcs:
            kill(n, c)                                  # only after the look
        return res

    if want("V46"):
        res = slow_kill("v46")
        check("V46 the worker SIGKILLed: its engine (N, C) gone within 1 s", len(res) == 1 and res[0][1] is not None
              and res[0][2] is False, res)
    if want("V46b"):
        res = slow_kill("v46b", inject="worker.Worker.launcher = lambda self: None; ")
        check("V46b the launcher off: the engine still lives 1 s after the worker's kill (an orphan is seen)",
              len(res) == 1 and res[0][1] is not None and res[0][2] is True, res)
    if want("V46c"):
        res = slow_kill("v46c", via_guard=True)
        check("V46c a stand-in guard and its worker SIGKILLed: no engine left within 1 s", len(res) == 1
              and res[0][1] is not None and res[0][2] is False, res)
    if want("V46d"):
        r46 = subprocess.run([sys.executable, "-I", "-B", str(BIND), "1", str(EXE)], capture_output=True, timeout=60)
        check("V46d bind_exec.py with parent 1: exit 1, no output", r46.returncode == 1 and r46.stdout == b""
              and r46.stderr == b"", (r46.returncode, r46.stdout[:200], r46.stderr[:200]))
    if want("V46e"):
        stop46 = threading.Event()
        busy = [threading.Thread(target=lambda: [time.sleep(0.001) for _ in iter(stop46.is_set, True)])
                for _ in range(3)]
        for b in busy:
            b.start()
        slow, codes = [], []
        for i in range(200):
            t0 = time.time()
            q = subprocess.Popen([sys.executable, "-I", "-B", str(BIND), str(os.getpid()), "/bin/true"])
            if time.time() - t0 > 10:
                slow.append(i)
            codes.append(q.wait(30))
        stop46.set()
        for b in busy:
            b.join()
        check("V46e 200 starts through bind_exec.py beside 3 threads: every Popen within 10 s, every exit 0",
              not slow and codes == [0] * 200, (slow[:5], sorted(set(codes))))

bad = [n for n, ok in results if not ok]
print(f"{len(results) - len(bad)} of {len(results)} checks pass" + (f"; FAILED: {bad}" if bad else ""))
sys.exit(1 if bad else 0)
