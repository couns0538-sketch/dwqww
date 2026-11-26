"""Opus 2026-11-23: the test of run/guard.py version 2 (A3a; A5: the repairs R1 to R12, cases V1 to V11, T1). Known answers written BEFORE the guard ran once, from
FORMATS 2.9 1.2 and 1.8, SETUP_PLAN D2 and D5, and Astra 160235Z, 161634Z, 171134Z, 171332Z, 172109Z. Standard
library only; run it with a PLAIN interpreter (it starts python processes itself).

    test_guard.py <run/guard.py> <a NEW folder> [exe=<engine> net=<net file>] [only=C,P,E] [plant1 ... plant44]

The run folder of <run/guard.py> is copied into the new folder (a plant changes the copy only) and imported from
there. C and P need nothing else; E needs the engine and its net and the tree's workloads/ and known/ (the folder
above run/); without exe= and net= it prints NOT RUN and counts in neither.

C  THE CONTROL RECORD, in-process, no process started (take_controls, extend and replay called directly). A root with
   slots 1 and 2, pilot rows of round 1 (counters 1 to 4), D = now + 2 h, the lease started 600 s ago, one sealed
   piece (4 games, 4,000 bytes; every key of worker.py's piece seal, chained to the slot's genesis), floor 0. The policy
   is a plan.json written with indent=1 (NOT canonical: the guard reads it as json), owner_choice action "stop". A
   report is a canonical record with outcome, cutoff_floor_s = D - 600 s - lease start, dispatch_end_floor_s 300 s
   less, matches [], inputs {plan_sha256 = the policy's}. Known answers:
   C1  control 1 SELF_PLAY, scope {highest_round 9, target_rows 1000}: accepted; control/CONTROL.1.json and
       control/EVIDENCE.<sha>.json hold the sent bytes decoded; SCHEDULE.1.json: n 1, prev "first", evidence =
       sha256 of the control, its cutoff and dispatch end, this run, schema 2; its rows = the pilot rows unchanged +
       rounds 2 and 3 (horizon 2) for both slots: round 2 counters 5 to 8, round 3 9 to 12, schedule 1, short false.
   C2  the same inbox again: nothing new (no SCHEDULE.2.json, 1 control, no new alarm).
   C3  control 2 whose prev is not control 1's sha256: HELD ("prev does not link"), nothing written.
   C5  control 2 whose evidence file holds other bytes than the sha256 it is named by: HELD ("does not have the
       sha256").
   C6  Astra 161634Z: the report says STOP with a matching sha256, the control says SELF_PLAY: HELD ("is not the
       report's outcome"), zero new schedules, no fence.
   C7  owner_policy not the package's: HELD ("owner_policy").
   C7b the report's inputs.plan_sha256 is another plan's: HELD ("inputs.plan_sha256").
   C8  a cutoff later than the one in force (the header's D, while schedule 1's is 600 s earlier): HELD ("later than
       the one in force").
   C9  bounds one second off the report's whole seconds: HELD ("not the report's whole seconds").
   C15 an evidence that carries local_only (the full local report, Astra 172109Z): HELD ("local_only").
   C4  a valid control 2 (kind target, SELF_PLAY, scope highest 9) WITHOUT its evidence: HELD ("is not there");
       the evidence arrives: at the next look accepted, SCHEDULE.2.json adds rounds 4 and 5 (counters 13 to 16 and
       17 to 20), evidence = control 2's sha256, prev = sha256 of SCHEDULE.1.json.
   C11 control 3 STOP: FENCE.json with exactly at_utc, cutoff_utc, run_fingerprint, schema, why; cutoff_utc = the D
       in force (schedule 2's, 600 s before the header's), why names control 3's sha256; no SCHEDULE.3.json.
   C16 a conflict: the inbox's CONTROL.1.json.zz replaced by other bytes after its acceptance: an ALARM "other bytes
       than the accepted control 1", control/CONTROL.1.json unchanged.
   C10 (Astra 171332Z) a new root: control 1 UNQUALIFIED (scope null): accepted, no schedule, no fence; control 2
       SELF_PLAY linked to control 1: accepted, SCHEDULE.1.json naming control 2.
   C12 a guard started again on that root: the replay finds 2 controls, nothing owed, the next is 3; with
       control/CONTROL.1.json changed (on a copy of the root): the start stops with code 4.
   C13 OWNER_CHOICE, the action from the hashed policy alone (Astra 171134Z), the report's owner_choice a label that
       is NOT the action: (a) action "stop": the fence; (b) "reduced_target" 1500 rows, covered, scope 1500: a
       schedule; (c) the same with scope 1600: HELD ("more rows"); (d) uncovered and if_uncovered "stop": the fence;
       (e) uncovered and no if_uncovered: HELD ("names no action"); (f) an action the guard does not know: HELD.
   C14 kind matches, decision = the report's matches: accepted, no schedule, an ALARM "no match runner"; the
       decision other than the report's matches: HELD ("pairs").
   C14b kind fence: the fence, why names that control.
   C17 the room: (a) no sealed piece: HELD ("no sealed piece"); (b) a floor above the free bytes: HELD ("room:").
   C18 the rolling extension (control 1 SELF_PLAY, scope highest 5: SCHEDULE.1 holds rounds 2 and 3): no range seal:
       none; the seal of round 1 only: none; the seal r0002.w002: SCHEDULE.2 adds round 4 alone, with schedule 1's
       bounds and control 1's sha256 as evidence; again with nothing new: none; r0003.w001: SCHEDULE.3 adds round 5;
       then none (round 6 is above the scope).
   C19 an owed effect: a root whose control/ holds an accepted SELF_PLAY control 1 and no schedule (a stop between
       the acceptance and the schedule): a new guard; one pass with the STOP file: no schedule; one pass without it
       (every slot ended already, so no worker starts): SCHEDULE.1.json naming control 1.
   C19b the same with NO sealed piece (G5 holds for the owed schedule too) and a valid control 2 of kind fence in
       the inbox: a pass: no schedule, an ALARM "pending" naming the room, control 2 NOT taken (no control/CONTROL.2
       .json, no fence: a control taken while an earlier effect is owed would make the next start stop with exit 4);
       the seal arrives: the next pass makes SCHEDULE.1.json naming control 1, then takes control 2: FENCE.json whose
       why names control 2 and whose cutoff_utc is schedule 1's cutoff.

P  THE PROCESSES, stand-in worker and packer scripts started by the guard's own Group code (on Windows a job object,
   on Linux a session of its own), the retry waits cut to 0.5 s, --end-grace 2, --allowance 2.
   PA  a day of 8 s with slots 1 to 4. Slot 1 sleeps 1 s and ends; slot 2 exits 4 (a named fault), then ends when
       started again; slot 3 leaves a child behind (an orphaned engine: Astra 160235Z) and ends; slot 4 exits 6,
       then hangs. Known: the guard closes the day within 60 s; FENCE.json at D with cutoff_utc = the header's D,
       why "D", exactly its five keys; slot 1: 1 start; slot 2: 2 starts, the first without the fence, the second
       with it (the finalizer), FAULTED in between; slot 3: 1 start, its child NOT alive right after the pass that
       reaped slot 3; slot 4: 2 starts, the alarm late4, UNRECONCILED; STOP_PACKER canonical with unreconciled [4];
       CLOSED.json slots_ended [1, 2, 3], slots_unreconciled [4], terminal = the inventory on disk {lines, sha256,
       zz_sha256} (R10), packer "ended"; the stand-in terminal writer started once, after the packer's last pass; the
       packer started once and made its last pass; groups.jsonl 8 lines (6 workers, 1 packer, 1 terminal writer) of
       this boot; hourly.jsonl's first
       line state "play"; the recorded processes carry their creation time; no process of the day alive at the end
       (a process is its number AND its creation time: R11).
   T1  (first in part P, R11) a process of the test's own (sleep 60): its creation time an integer; alive by number and
       creation time; NOT alive by number and another creation time (the stand-in for a number Windows gives
       again); a kill by the other creation time leaves it alive; a kill by its own ends it within 5 s.
   PB  the STOP file: three passes start nothing (no worker, no packer) and raise the alarm "stop"; removed: the slot
       starts once and ends. Another boot id in the header: three passes start nothing, the alarm "boot"; a
       RESUME.1.json naming this boot: the slot starts.
   PC  a slot that exits 6 at every start (retry 0.2 s): 5 starts, then FAULTED ("five starts within one hour"),
       no sixth start in the next second.
   PD  the slot's lock held by another process (a worker of an earlier guard lives on in its own session; the
       stand-in worker takes the lock as the real one does and exits 3 when it is held): three seconds of passes
       start nothing, nothing is FAULTED, the ALARM held1 stands; released: one start, the slot ended, held1 gone.
   PE  out/LOCK held by another packer: while the slot plays and ends, no packer start and the ALARM packer_held;
       released: the packer starts.
   PF  a day of 4 s whose slot lock is held all the time: no worker start at all; at D + grace the slot is
       UNRECONCILED (its lock still held), STOP_PACKER names [1], CLOSED.json slots_unreconciled [1], within 30 s.

E  ONE DAY WITH THE REAL WORKER, ENGINE AND PACKER (slots 0 and 1, piece_games 1, pilot round 1 = counters 1 and 2,
   D = now + 15 min, the openings of N12, the manifest's game line, a converter that is not there so every piece is
   offered raw). Known: both pilot ranges sealed; control 1 SELF_PLAY, scope highest 4: SCHEDULE.1.json adds rounds
   2 and 3 (counters 3-4 and 5-6) with control 1's bounds and sha256; when a round-2 range seal is there the rolling
   extension writes SCHEDULE.2.json with round 4 alone (counters 7-8), the same bounds, control 1's sha256; no
   SCHEDULE.3.json; the workers play all four rounds (each range seal r0001 to r0004 of each slot counts 2 games);
   control 2 kind fence: FENCE.json, cutoff_utc = control 1's cutoff, why naming control 2; each journal's last line
   is `ended` with why "ranges done"; every worker exit 0 (no FAULTED, no UNRECONCILED, no STOP_PACKER); CLOSED.json
   slots_ended [0, 1], its terminal the real TERMINAL.jsonl (footer: 16 pieces, slots ended 2, unreconciled 0); the
   packer's last pass with 8 offers in each slot's out folder.

V  VERSION 2 (the seats' NOT YET on version 1; tmp/opus_scratch/guard_v2/KNOWN_ANSWERS_guard_v2_by_opus.md, written
   before the code). The fixtures are the real programs' forms: worker.py's piece and range seals, its ended line and
   IDENTITY.json, bootguard.py's RESUME keys, a fence report with inputs.plan_sha256.
   V1a/b a 0-byte and another run's guard/CLOSED.json: run() Stop 4 naming it, nothing started (part C); V1c PA's
       closed day started again: exit 0 at once, no file changed (part P).
   V2a a 0-byte FENCE.json and bare {"t":"ended"} journals (Neon 223800Z): the pass raises Stop 4 naming FENCE.json,
       no packer, no worker, no CLOSED.json; V2b/c another run's fence, a fence of another D: Stop 4; V2d control.
   V3  slot_ended: a bare line, the full line without IDENTITY.json, another run's IDENTITY.json, a last_seal that
       is not its seal's sha256: not ended; the genesis end and the end at seal 0: ended.
   V4a another run's piece seal (games 1,000,000, raw 0): not counted, HELD "no sealed piece", ALARM seal1; V4b an
       index that is not its name's: none; V4c a seal off the chain: only the one before; V4d control.
   V5a-d (C18's setting) r0002.w002 0 bytes, another run's, last + 1, through_index 0 with no seal on disk: no
       SCHEDULE.2, ALARM range2.2; V5e the genuine seal: round 4 alone.
   V6  orphan_groups on a stand-in process table (Linux behaviour; the kill itself runs only on Linux, the seats'):
       a live leader: left; a dead worker's engine: ended; a dead packer's converter: ended; gone: dropped; an unknown
       kind: left. V6b a group number this guard starts is dropped from the earlier guards' list.
   V7  boot_ok over RESUME chains: the header's boot alone, a linked RESUME to this boot, a chain of two: admitted; a
       RESUME away from the header's boot, prev not "first", old_boot_id not the header's, a broken chain,
       instance_provable false: not.
   V8  a policy without target_rows, with target_rows true, declaring 2 pilot rounds for a pilot of 1: Stop 4.
   V9  a kind fence control whose report names another plan: HELD inputs.plan_sha256, no FENCE.json.
   V10a/b/c the stand-in terminal writer exits 4 / writes a .zz of other bytes / no footer: no CLOSED.json, the ALARM
       terminal naming why, one start in the next seconds (it is tried again after 60 s).
   V11 (Linux only, R12) end_exact: ours() False: nothing sent, the child lives; True: ended within 5 s; a child that
       has exited and is not reaped (its pidfd readable), ours() True: nothing sent.
   V12 (G-A, Fable 25 Nov; known answer written before the change, in-process) new_schedule on a stand-in guard with
       998 schedules: the bytes of schedule n 999 (round 2 added); with 999: Held naming SCHEDULE.999 (no 1000th).

G11 THE CLOCK FILE (v16; the clock known answers G, ADDENDUM 3's S5, ADDENDUM 4's G1' and G1b; part C in-process,
   the guard's Bounds reading a stand-in clock the test sets, write_clock called directly; G1 also in part P):
   G1  the first write: CLOCK.json canonical, exactly n, run_fingerprint, schema, state, utc_ms: n 1, schema 1, this
       run, play, utc_ms = anchor UTC + run (within 1 ms). In part P after PA's day (the guard's REAL pass wrote it):
       this run's record, n >= 1, a state of the four, utc_ms inside the day.
   G1b UTC 25,170 s ahead, steady and boot normal, no bound crossed (D a day away): utc_ms = anchor + run (within
       1 ms), state play; UTC 30 s BEHIND: utc_ms = that UTC.
   G2  50 writes: each read back is the whole record, n rising by 1; no .CLOCK.json.*.part left.
   G3  CLOCK_EVERY is 60.0; after a write, readings 30 s and 59.9 s later write nothing, 60 s later and 125 s later
       write (n +1 each).
   G4  a guard started again on the root continues n (its first write is n + 1); a CLOCK.json of another run, and
       one that is not a record, are replaced from n 1.
   G5  (S5) state is the clocks' alone: play, dispatch_end (an earlier dispatch end), cutoff; after the fence at D
       still cutoff; UTC alone 7,300 s ahead: hold (utc_ms still anchor + run); a fence before D while the clocks
       say play: play.
   G6  (ADDENDUM 9, Fable's proof) CLOCK.json a FOLDER: the write returns, alarm "clock" names it, n 0, clock_at
       None; the next pass tries again (a second alarm call, at most one scratch); the folder gone: written n 1, the
       alarm cleared; a leftover scratch of this process, 60 s later: written n 2, no scratch left.

PLANTS (each must make the test fail; the check expected to fail is named):
  plant1 no decision-vs-outcome check (C6)          plant2 prev not checked (C3)
  plant3 the evidence's sha256 not checked (C5)     plant4 owner_policy not checked (C7)
  plant5 a later bound taken (C8)                   plant6 UNQUALIFIED makes a schedule (C10)
  plant7 the group not ended before the reap (PA)   plant8 the next k from the schedules (C10)
  plant9 OWNER_CHOICE from the report's label (C13) plant10 the fence copies the header's D (C11)
  plant11 a faulted slot restarted in play (PA)     plant12 no STOP_PACKER (PA)
  plant13 the extension ignores the scope (C18)     plant14 no room test (C17)
  plant15 local_only accepted (C15)                 plant16 bounds not compared with the report (C9)
  plant17 an owed effect dropped (C19)              plant18 no boot check (PB)
  plant19 the STOP file ignored (PB)                plant20 no five-starts rule (PC)
  plant21 D + grace never comes (PA)                plant22 the report's plan sha not checked (C7b)
  plant23 the owed schedule without the room test (C19b)
  plant24 a control taken while an effect is owed (C19b)
  plant25 no probe of the slot's lock (PD)          plant26 no probe of out/LOCK (PE)
  plant27 a held slot never UNRECONCILED at the end (PF)
  plant28 CLOSED.json not read (V1a)                plant29 FENCE.json's content not checked (V2a)
  plant30 a bare ended line counts (V3)             plant31 a piece seal's fingerprint not checked (V4a)
  plant32 a range seal counts by its name (V5)      plant33 the range's interval not compared (V5)
  plant34 the through seal not looked at (V5)       plant35 no leader check before an orphan is ended (V6)
  plant36 the RESUME chain's prev not walked (V7)   plant37 old_boot_id not linked (V7)
  plant38 target_rows not demanded (V8)             plant39 the pilot rounds not compared (V8)
  plant40 a fence control exempt from the plan (V9) plant41 no terminal writer (PA, V10a)
  plant42 the terminal's footer not checked (V10c)
  plant43 ours() not asked (V11a, Linux)          plant44 the pidfd not polled (V11c, Linux)
  plant45 the schedule chain without its end (V12)
  plant46 the clock file never written by the pass (G1 in PA)
  plant47 utc_ms from UTC alone (G1b)              plant48 no spacing of the writes (G3)
  plant49 n not continued on a restart (G4)
  plant50 a failed write lets its error out (G6)   plant51 a failed write counted as a write, not tried again (G6)
"""
import ctypes
import hashlib
import json
import os
import select
import shutil
import signal
import subprocess
import sys
import time
import traceback
import zlib
from pathlib import Path
from types import SimpleNamespace

if len(sys.argv) < 3:
    print("usage: test_guard.py <run/guard.py> <a NEW folder> [exe=.. net=..] [only=C,P,E] [plantN]")
    sys.exit(2)
GUARD, WORK = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
OPTS, PLANT = {}, None
for x in sys.argv[3:]:
    if x.startswith("plant"):
        PLANT = x
    elif "=" in x and x.split("=", 1)[0] in ("exe", "net", "only"):
        OPTS[x.split("=", 1)[0]] = x.split("=", 1)[1]
    else:
        print(f"STOP: not understood: {x}")
        sys.exit(2)
ONLY = set(OPTS.get("only", "C,P,E").split(","))
if WORK.exists():
    print(f"STOP: {WORK} exists already (a NEW folder)")
    sys.exit(2)
WORK.mkdir(parents=True)
TREE = GUARD.parent.parent
shutil.copytree(GUARD.parent, WORK / "run", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

PLANTS = {
    "plant1": ('                                                         or rep.get("outcome") != c["decision"]):\n',
               '                                                         or False):\n'),
    "plant2": ('        if c["prev"] != prev:\n', '        if False:\n'),
    "plant3": ('        if not HEX64.fullmatch(str(c["evidence"])) or sha256_bytes(evidence) != c["evidence"]:\n',
               '        if not HEX64.fullmatch(str(c["evidence"])):\n'),
    "plant4": ('        if c["owner_policy"] != self.policy_sha:\n', '        if False:\n'),
    "plant5": ('            if cut > c_in or disp > d_in:\n', '            if False:\n'),
    "plant6": ('        elif c["decision"] == "UNQUALIFIED":\n            eff = "none"\n',
               '        elif c["decision"] == "UNQUALIFIED":\n            eff = "schedule"\n'),
    "plant7": ('        if not g.end_and_verify(self.a.allowance):\n', '        if False:\n'),
    "plant8": ('        k = len(self.ctl) + 1\n', '        k = len(self.sched) + 1\n'),
    "plant9": ('            oc = self.policy["owner_choice"]\n',
               '            oc = {"action": rep.get("owner_choice")}\n'),
    "plant10": ('"cutoff_utc": self.d_text(), "run_fingerprint": self.fp,',
                '"cutoff_utc": self.h["hard_cutoff_utc"], "run_fingerprint": self.fp,'),
    "plant11": ('                if s.faulted:\n', '                if False:\n'),
    "plant12": ('        if unrec and not (self.root / "STOP_PACKER").exists():\n', '        if False:\n'),
    "plant13": ('        if top + 1 > c["scope"]["highest_round"]:\n', '        if False:\n'),
    "plant14": ('        if free - need < self.a.floor_bytes:\n', '        if False:\n'),
    "plant15": ('        if "local_only" in rep:\n', '        if False:\n'),
    "plant16": ('            if (c["cutoff_utc"], c["dispatch_end_utc"]) != (T(self.lease_start + fl[0]), '
                'T(self.lease_start + fl[1])):\n', '            if False:\n'),
    "plant17": ('                self.pending = k\n', '                pass\n'),
    "plant18": ('        why = self.resume_why()\n', '        why = None\n'),
    "plant19": ('        stop = (self.root / "STOP").exists()\n', '        stop = False\n'),
    "plant20": ('                if len([t for t in s.starts if now - t < HOUR]) >= 5:\n',
                '                if False:\n'),
    "plant21": ('        return self.B.judge("cutoff", lead=-self.a.end_grace)[0] == cw.COME\n',
                '        return False\n'),
    "plant22": ('                or rep["inputs"].get("plan_sha256") != self.policy_sha):\n',
                '                or False):\n'),
    "plant23": ('                    raise Held(f"the owed schedule: {why}")\n', '                    pass\n'),
    "plant24": ('            if not fenced and st != "cutoff" and self.pending is None:\n',
                '            if not fenced and st != "cutoff":\n'),
    "plant25": ('            if self.lock_held(self.root / f"w{s.k:03d}"):', '            if False:'),
    "plant26": ('        if self.lock_held(self.root / "out"):', '        if False:'),
    "plant27": ('                if end and self.past_d_grace():', '                if False:'),
    "plant28": ('            self.check_closed()\n', '            pass\n'),
    "plant29": ('        except ValueError as e:\n            raise Stop(4, f"FENCE.json: {e}") from None\n',
                '        except ValueError:\n            return {}\n'),
    "plant30": ('        if not (isinstance(ln, dict) and sorted(ln) == ENDED_KEYS and ln["t"] == "ended"):\n'
                '            return False\n', '        if isinstance(ln, dict) and ln.get("t") == "ended":\n'
                '            return True\n'),
    "plant31": ('                if not (isinstance(s, dict) and s.get("schema") == 2 and s.get("run_fingerprint") == '
                'self.fp\n', '                if not (isinstance(s, dict) and s.get("schema") == 2\n'),
    "plant32": ('                why = self.range_fault(Path(f.path), key[0], key[1], rows.get(key))\n',
                '                why = None\n'),
    "plant33": ('                and same(s.get("last"), row["last"])):\n', '                ):\n'),
    "plant34": ('        except OSError:\n            return f"names piece {ti}, whose seal is not in w{k:03d}/closed"\n',
                '        except OSError:\n            return None\n'),
    "plant35": ('        if kind not in LEADER or any(LEADER[kind].encode() in line for _, line in mem):\n',
                '        if kind not in LEADER:\n'),
    "plant36": ('                    and r.get("prev") == ("first" if n == 1 else sha256_bytes(prev))\n', ''),
    "plant37": ('                    and r.get("old_boot_id") == boot and isinstance(r.get("new_boot_id"), str)):\n',
                '                    and isinstance(r.get("new_boot_id"), str)):\n'),
    "plant38": ('        if type(pol.get("target_rows")) is not int or pol["target_rows"] < 1:\n', '        if False:\n'),
    "plant39": ('        if not same(pol.get("pilot_rounds_declared"), pilot):\n', '        if False:\n'),
    "plant40": ('        if (not isinstance(rep.get("inputs"), dict)\n',
                '        if c["kind"] != "fence" and (not isinstance(rep.get("inputs"), dict)\n'),
    "plant41": ('        term = self.terminal()\n        if term is None:\n            return False\n',
                '        term = {"lines": 0, "sha256": "", "zz_sha256": ""}\n'),
    "plant42": ("            return None, \"TERMINAL.jsonl's last line is not its footer (t footer, the fingerprint of "
                "the bytes before it)\"\n", '            pass\n'),
    "plant43": ('        if not ours():\n            return False\n', '        if False:\n            return False\n'),
    "plant44": ('        if p.poll(0):\n            return False\n', '        if False:\n            return False\n'),
    "plant45": ("        if n > 999:  ", "        if False:  "),
    "plant46": ("        self.write_clock(r, st)\n", "        pass\n"),
    "plant47": ("        return math.floor(min(t) * 1000)\n", "        return math.floor(r[0] * 1000)\n"),
    "plant48": ("        if self.clock_at is not None and r[1] - self.clock_at < self.clock_every:\n",
                "        if False:\n"),
    "plant49": ("            return c[\"n\"]\n", "            return 0\n"),
    "plant50": ("            self.alarm(\"clock\", f\"CLOCK.json not written: {e}\")\n            return\n",
                "            raise\n"),
    "plant51": ("            self.alarm(\"clock\", f\"CLOCK.json not written: {e}\")\n",
                "            self.alarm(\"clock\", f\"CLOCK.json not written: {e}\")\n            self.clock_at = r[1]\n"),
}
if PLANT:
    if PLANT not in PLANTS:
        print(f"STOP: no {PLANT}")
        sys.exit(2)
    gp = WORK / "run" / "guard.py"
    text = gp.read_text(encoding="utf-8")
    old, new = PLANTS[PLANT]
    if text.count(old) != 1:
        print(f"STOP: {PLANT}: its text stands {text.count(old)} times in the guard")
        sys.exit(2)
    gp.write_text(text.replace(old, new), encoding="utf-8", newline="\n")
    print(f"PLANT {PLANT} applied to the copy")

sys.path.insert(0, str(WORK / "run"))
import guard as G  # noqa: E402
import worker as W  # noqa: E402

BOOT = W.boot_id()
RESULTS = []
LIVE = []                               # every guard made here: its groups are ended at the end


def check(name, got, want):
    ok = got == want
    RESULTS.append((name, ok))
    print(f"{'PASS' if ok else 'FAIL'} {name}: got {str(got)[:300]}" + ("" if ok else f"; want {str(want)[:300]}"),
          flush=True)
    return ok


def true(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    print(f"{'PASS' if cond else 'FAIL'} {name}" + ("" if cond else f": {str(detail)[:400]}"), flush=True)
    return bool(cond)


def T(t):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(t)))


def sha(b):
    return hashlib.sha256(b).hexdigest()


def rows(slots, rnd=1, first=1, length=4, n=0):
    return [{"first": first, "last": first + length - 1, "round": rnd, "schedule": n, "short": False, "slot": k}
            for k in slots]


def header(slots, pilot, hard_in, lease_ago=600, boot=None, piece_games=4, real=None):
    now = int(time.time())
    h = {"schema": 2, "run": "gt", "lease_start_utc": T(now - lease_ago), "lease_end_utc": T(now + 86400),
         "hard_cutoff_utc": T(now + hard_in), "boot_id": boot or BOOT, "instance": "test-instance",
         "package": "0" * 64, "engine_sha256": "1" * 64, "net_sha256": "2" * 64, "options_sha256": "3" * 64,
         "game_line": "go nodes 1", "opening_rule": {"kind": "seed", "plies": 8, "root_seed": "s"},
         "slots": slots, "piece_games": piece_games, "pilot_ranges": pilot}
    h.update(real or {})
    return h


def make_root(name, slots, pilot, hard_in, choice=None, target=1000000, **kw):
    root = WORK / name
    root.mkdir()
    (root / "RUN.json").write_bytes(W.canon(header(slots, pilot, hard_in, **kw)))
    plan = {"target_rows": target, "lease_end_s": 86400, "closing_s": 3600, "game_margin_s": 600,
            "pilot_rounds_declared": 1, "floor_fraction": 0.5, "match_margin": 1.1,
            "owner_choice": choice or {"name": "stop at the owner's choice", "action": "stop"}, "match_queue": []}
    pol = WORK / f"{name}.plan.json"
    pol.write_text(json.dumps(plan, indent=1) + "\n", encoding="ascii")
    return root, pol


def hdr(root):
    return json.loads((root / "RUN.json").read_bytes())


def args(root, pol, **kw):
    a = SimpleNamespace(root=str(root), exe=str(WORK / "no_engine.exe"), net="n", manifest="m", known_startup="k",
                        converter=str(WORK / "no_converter"), policy=str(pol), floor_bytes=0, openings="",
                        game_seconds=600.0, horizon=2, tick=0.1, allowance=2.0, end_grace=2.0, python=sys.executable)
    for k, v in kw.items():
        setattr(a, k, v)
    return a


def guard(root, pol, **kw):
    g = G.Guard(args(root, pol, **kw))
    LIVE.append(g)
    g.replay_controls()
    return g


def done(g):
    """The guard's lock and log released (a second guard may start on the same root)."""
    g.lock.release()
    g.log.close()


def report(root, pol, outcome, cut_before_d=600, disp_before_cut=300, state="4" * 64, **extra):
    h = hdr(root)
    lease, hard = W.utc(h["lease_start_utc"], "l"), W.utc(h["hard_cutoff_utc"], "h")
    cf = hard - cut_before_d - lease
    rep = {"outcome": outcome, "cutoff_floor_s": cf, "dispatch_end_floor_s": cf - disp_before_cut, "matches": [],
           "inputs": {"plan_sha256": sha(Path(pol).read_bytes()), "state_sha256": state, "pilot_sha256": "5" * 64}}
    rep.update(extra)
    return rep


SENT = {}


def control(root, pol, k, rep, kind="pilot_decision", decision=None, scope=None, over=None, evb=None):
    """The control record's bytes for report `rep` (its bounds = the lease start + the report's floors)."""
    h = hdr(root)
    lease = W.utc(h["lease_start_utc"], "l")
    evb = W.canon(rep) if evb is None else evb
    c = {"at_utc": T(time.time()), "cutoff_utc": T(lease + rep.get("cutoff_floor_s", 0)),
         "decision": rep.get("outcome") if decision is None else decision,
         "dispatch_end_utc": T(lease + rep.get("dispatch_end_floor_s", 0)), "evidence": sha(evb), "k": k,
         "kind": kind, "owner_policy": sha(Path(pol).read_bytes()),
         "prev": "first" if k == 1 else sha(SENT[(root.name, k - 1)]),
         "run_fingerprint": sha((root / "RUN.json").read_bytes()), "schema": 2, "scope": scope}
    c.update(over or {})
    return W.canon(c), evb


def send(root, k, cb, evb, evidence=True, ctl=True, ev_name=None):
    inbox = root / "inbox"
    inbox.mkdir(exist_ok=True)
    if evidence:
        (inbox / f"EVIDENCE.{ev_name or sha(evb)}.json.zz").write_bytes(zlib.compress(evb, 6))
    if ctl:
        (inbox / f"CONTROL.{k}.json.zz").write_bytes(zlib.compress(cb, 6))


def accepted(root, k, cb):
    SENT[(root.name, k)] = cb


def fp_of(root):
    return sha((root / "RUN.json").read_bytes())


def clock_rec(root):
    """G11: ROOT/CLOCK.json read as the canonical record, or why not (a text)."""
    try:
        return W.parse_canon((root / "CLOCK.json").read_bytes(), "CLOCK.json")
    except (OSError, ValueError) as e:
        return repr(e)[:160]


def staged(g):
    """G11: the guard's Bounds take a stand-in anchor (its UTC kept; steady 1000.0 and boot 2000.0, so that the
    test's spacings are exact in binary: 60 s is 60.0, not 59.99999999999) and read no clock of their own;
    at(run, utc_off) is a reading run seconds after the anchor on the steady and boot clocks, UTC moved by utc_off."""
    a0 = g.B.anchor
    a = (a0[0], 1000.0, None if a0[2] is None else 2000.0)
    g.B.anchor = a
    g.B.clocks = SimpleNamespace(read=lambda: a)

    def at(run, utc_off=0.0):
        return (a[0] + run + utc_off, a[1] + run, None if a[2] is None else a[2] + run)
    return a, at


def field(x, k):
    """G11: field k of a clock record, or the text that says why there is none."""
    return x.get(k) if isinstance(x, dict) else x


def plan_in(pol):
    """A report's inputs naming the policy (a fence's too: R9)."""
    return {"plan_sha256": sha(Path(pol).read_bytes()), "state_sha256": "4" * 64, "pilot_sha256": "5" * 64}


def seal_piece(root, slot, i, games=4, raw=4000, **over):
    """The worker's piece seal (worker.py, its `fresh` record), chained to p<i-1> or the slot's genesis."""
    d = root / f"w{slot:03d}" / "closed"
    d.mkdir(parents=True, exist_ok=True)
    fp = fp_of(root)
    prev = f"genesis:{fp}:w{slot:03d}" if i == 0 else sha((d / f"p{i - 1:06d}.seal.json").read_bytes())
    rec = {"schema": 2, "run": hdr(root)["run"], "run_fingerprint": fp, "slot": slot, "epoch": 1, "index": i,
           "prev_seal": prev, "raw_sha256": "6" * 64, "raw_bytes": raw, "games": games, "rows": 100,
           "first_game": "g1", "last_game": "g1", "first_counter": 1, "last_counter": games, "ids_digest": "7" * 64,
           "round": 1, "schedule": 0}
    rec.update(over)
    (d / f"p{i:06d}.seal.json").write_bytes(W.canon(rec))


def row_of(root, rnd, slot):
    """The newest schedule's row for (slot, round), or the pilot's (a schedule lists every row before it)."""
    n = len(list(root.glob("SCHEDULE.*.json")))
    rs = json.loads((root / f"SCHEDULE.{n}.json").read_bytes())["ranges"] if n else hdr(root)["pilot_ranges"]
    return next(r for r in rs if r["slot"] == slot and r["round"] == rnd)


def seal_range(root, rnd, slot, **over):
    """The worker's range seal (worker.py range_seal) of the newest schedule's row, with no piece in it."""
    d = root / "ranges"
    d.mkdir(exist_ok=True)
    r = row_of(root, rnd, slot)
    rec = {"schema": 2, "run": hdr(root)["run"], "run_fingerprint": fp_of(root), "round": rnd, "slot": slot,
           "epoch": 1, "schedule": r["schedule"], "first": r["first"], "last": r["last"], "short": r["short"],
           "complete": True, "first_index": -1, "first_prev_seal": None, "through_index": -1, "through_seal": None,
           "games": 2, "rows": 0, "raw_bytes": 0, "dispositions": {}}
    rec.update(over)
    (d / f"r{rnd:04d}.w{slot:03d}.seal.json").write_bytes(W.canon(rec))


def ended_slot(root, slot, last_index=-1, **over):
    """The worker's end of a slot: IDENTITY.json (worker.py claim_slot) and its ended line (worker.py: t, epoch,
    last_index, last_seal, why), at the end of its seal chain (the genesis text without a seal)."""
    d = root / f"w{slot:03d}"
    d.mkdir(parents=True, exist_ok=True)
    fp = fp_of(root)
    if not (d / "IDENTITY.json").exists():
        (d / "IDENTITY.json").write_bytes(W.canon({"run": hdr(root)["run"], "run_fingerprint": fp, "schema": 2,
                                                   "slot": slot}))
    last = f"genesis:{fp}:w{slot:03d}" if last_index == -1 else \
        sha((d / "closed" / f"p{last_index:06d}.seal.json").read_bytes())
    rec = {"epoch": 1, "last_index": last_index, "last_seal": last, "t": "ended", "why": "test"}
    rec.update(over)
    with open(d / "journal.txt", "ab") as f:
        f.write(W.canon(rec))


def resume(root, n, old, new, provable=True, **over):
    """RESUME.<n>.json with the boot guard's keys (bootguard.py), chained to RESUME n-1."""
    prev = "first" if n == 1 else sha((root / f"RESUME.{n - 1}.json").read_bytes())
    rec = {"at_utc": T(time.time()), "checks": [], "instance": None, "instance_provable": provable, "n": n,
           "new_boot_id": new, "old_boot_id": old, "prev": prev, "run_fingerprint": fp_of(root), "schema": 2,
           "slots": []}
    rec.update(over)
    (root / f"RESUME.{n}.json").write_bytes(W.canon(rec))


def sched(root, n):
    p = root / f"SCHEDULE.{n}.json"
    return json.loads(p.read_bytes()) if p.exists() else None


def held(g, text):
    return text in g.alarms.get("control", "")


# R11: a process is its number AND its creation time (Windows gives a freed number again within seconds). The same
# text runs in the test and in the stand-in worker, which records its own and its child's.
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
    "R11: a process of this number lives AND it is the recorded one (its creation time); a number alone is none."
    return created is not None and created_of(pid) == created


def kill(pid, created):
    "R11: end the recorded process only, through ONE handle (Windows) or pidfd (Linux) checked before the end."
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


def cleanup():
    for g in LIVE:
        for grp in [s.g for s in g.slots.values()] + [g.packer, getattr(g, "term", None)]:
            if grp is not None and not grp.done:
                try:
                    grp.end_and_verify(2.0)
                    grp.reap()
                except Exception:  # noqa: BLE001
                    pass
    for f in WORK.glob("*/fake/orphan.*.pid"):
        kill(*map(int, f.read_text().split()))
    for f in WORK.glob("*/fake/starts.*.txt"):
        for ln in f.read_text().splitlines():
            x = json.loads(ln)
            kill(x["pid"], x.get("created"))


def drive(g, until, limit, each=None):
    t_end = time.monotonic() + limit
    while time.monotonic() < t_end:
        closed = g.one_pass()
        if each:
            each(g)
        if closed or until(g):
            return closed or "until"
        time.sleep(0.1)
    return False


# ---- the stand-in worker and packer -----------------------------------------------------------------------------
FAKE = WORK / "fake_run"
FAKE.mkdir()
(FAKE / "worker.py").write_text('''import hashlib, json, os, subprocess, sys, time
from pathlib import Path
''' + IDENT_SRC + '''
a = sys.argv[1:]
root = Path(a[a.index("--root") + 1]); slot = int(a[a.index("--slot") + 1]); fk = root / "fake"
plan = json.loads((fk / f"plan.{slot}.json").read_text())
log = fk / f"starts.{slot}.txt"
n = len(log.read_text().splitlines()) if log.exists() else 0
with open(log, "a") as f:
    f.write(json.dumps({"n": n, "t": time.time(), "fence": (root / "FENCE.json").exists(), "pid": os.getpid(), "created": created_of(os.getpid())}) + "\\n")
def lock(folder):
    folder.mkdir(exist_ok=True)
    f = open(folder / "LOCK", "a+b")
    try:
        if os.name == "nt":
            import msvcrt
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        sys.exit(3)
    return f
L = lock(root / ("w%03d" % slot))                  # as the real worker: exit 3 when another holds it
act = plan[min(n, len(plan) - 1)]
def canon(o):
    return (json.dumps(o, sort_keys=True, separators=(",", ":")) + "\\n").encode("ascii")
def ended():
    d = root / ("w%03d" % slot); d.mkdir(exist_ok=True)
    head = (root / "RUN.json").read_bytes(); fp = hashlib.sha256(head).hexdigest()
    if not (d / "IDENTITY.json").exists():
        (d / "IDENTITY.json").write_bytes(canon({"run": json.loads(head)["run"], "run_fingerprint": fp, "schema": 2,
                                                 "slot": slot}))
    with open(d / "journal.txt", "ab") as f:
        f.write(canon({"epoch": 1, "last_index": -1, "last_seal": "genesis:%s:w%03d" % (fp, slot), "t": "ended",
                       "why": "test"}))
if act == "ended":
    ended(); sys.exit(0)
if act.startswith("exit:"):
    sys.exit(int(act[5:]))
if act.startswith("sleep:"):
    time.sleep(float(act[6:])); ended(); sys.exit(0)
if act == "orphan":
    c = subprocess.Popen([sys.executable, "-I", "-B", "-c", "import time; time.sleep(120)"])
    (fk / f"orphan.{slot}.pid").write_text(f"{c.pid} {created_of(c.pid)}"); ended(); sys.exit(0)
if act == "hang":
    time.sleep(600); sys.exit(0)
sys.exit(99)
''', encoding="ascii")
(FAKE / "packer.py").write_text('''import json, os, sys, time
from pathlib import Path
a = sys.argv[1:]
root = Path(a[a.index("--root") + 1]); fk = root / "fake"
with open(fk / "packer.starts.txt", "a") as f:
    f.write("%f\\n" % time.time())
def lock(folder):
    folder.mkdir(exist_ok=True)
    f = open(folder / "LOCK", "a+b")
    try:
        if os.name == "nt":
            import msvcrt
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        sys.exit(3)
    return f
L = lock(root / "out")                             # as the real packer: exit 3 when another holds it
slots = json.loads((root / "RUN.json").read_text())["slots"]
def ended(k):
    p = root / ("w%03d" % k) / "journal.txt"
    last = p.read_bytes().splitlines()[-1:] if p.exists() else []
    try:
        return bool(last) and json.loads(last[0]).get("t") == "ended"
    except ValueError:
        return False
t_end = time.time() + 120
while time.time() < t_end:
    if (fk / "END").exists():
        sys.exit(0)
    if (root / "STOP_PACKER").exists() or ((root / "FENCE.json").exists() and all(ended(k) for k in slots)):
        (fk / "packer.final").write_text("%f" % time.time()); sys.exit(0)
    time.sleep(0.1)
sys.exit(0)
''', encoding="ascii")
(FAKE / "terminal.py").write_text('''import hashlib, sys, time, zlib
from pathlib import Path
a = sys.argv[1:]
root = Path(a[a.index("--root") + 1]); fk = root / "fake"
with open(fk / "terminal.starts.txt", "a") as f:
    f.write("%f\\n" % time.time())
mode = (fk / "terminal.mode").read_text().strip() if (fk / "terminal.mode").exists() else "ok"
if mode == "exit4":
    sys.exit(4)
body = (root / "RUN.json").read_bytes() + b'{"t":"slot"}\\n'
foot = b'{"fingerprint":"%s","t":"footer"}\\n' % hashlib.sha256(body).hexdigest().encode("ascii")
full = body + (b'{"t":"slot"}\\n' if mode == "nofooter" else foot)
(root / "TERMINAL.jsonl").write_bytes(full)
(root / "TERMINAL.jsonl.zz").write_bytes(zlib.compress(full + (b"x" if mode == "badzz" else b""), 6))
sys.exit(0)
''', encoding="ascii")
REAL_RUN = G.RUN_DIR


def fake_root(name, slots, plans, hard_in, **kw):
    root, pol = make_root(name, slots, rows(slots, length=2), hard_in, **kw)
    (root / "fake").mkdir()
    for k, p in plans.items():
        (root / "fake" / f"plan.{k}.json").write_text(json.dumps(p), encoding="ascii")
    return root, pol


def starts(root, k):
    p = root / "fake" / f"starts.{k}.txt"
    return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []


def end_packer(g, root):
    (root / "fake" / "END").write_text("end", encoding="ascii")
    if g.packer is not None:
        t_end = time.monotonic() + 10
        while not g.packer.exited() and time.monotonic() < t_end:
            time.sleep(0.05)
        g.packer.end_and_verify(2.0)
        g.packer.reap()
        g.packer = None


# ---- C ---------------------------------------------------------------------------------------------------------------
def part_c():
    G.RUN_DIR = FAKE
    root, pol = make_root("ca", [1, 2], rows([1, 2]), 7200)
    seal_piece(root, 1, 0)
    g = guard(root, pol)
    rep = report(root, pol, "SELF_PLAY")
    c1, e1 = control(root, pol, 1, rep, scope={"highest_round": 9, "target_rows": 1000})
    send(root, 1, c1, e1)
    g.take_controls()
    accepted(root, 1, c1)
    check("C1 control/CONTROL.1.json", (root / "control" / "CONTROL.1.json").read_bytes() if (
        root / "control" / "CONTROL.1.json").exists() else None, c1)
    check("C1 control/EVIDENCE", (root / "control" / f"EVIDENCE.{sha(e1)}.json").exists(), True)
    s1 = sched(root, 1) or {}
    h = hdr(root)
    lease = W.utc(h["lease_start_utc"], "l")
    check("C1 SCHEDULE.1 head", {k: s1.get(k) for k in ("n", "prev", "evidence", "cutoff_utc", "dispatch_end_utc",
                                                          "run_fingerprint", "schema")},
          {"n": 1, "prev": "first", "evidence": sha(c1), "cutoff_utc": T(lease + rep["cutoff_floor_s"]),
           "dispatch_end_utc": T(lease + rep["dispatch_end_floor_s"]),
           "run_fingerprint": sha((root / "RUN.json").read_bytes()), "schema": 2})
    want = rows([1, 2]) + rows([1, 2], 2, 5, 4, 1) + rows([1, 2], 3, 9, 4, 1)
    key = lambda r: (r["slot"], r["round"])  # noqa: E731
    check("C1 SCHEDULE.1 rows", sorted(s1.get("ranges", []), key=key), sorted(want, key=key))
    n_al = g.n_alarms
    g.take_controls()
    check("C2 the same inbox again: no SCHEDULE.2, one control, no new alarm",
          (sched(root, 2), len(g.ctl), g.n_alarms), (None, 1, n_al))

    def try2(name, cb, evb, text, ev_name=None, evidence=True):
        send(root, 2, cb, evb, ev_name=ev_name, evidence=evidence)
        g.take_controls()
        true(f"{name} HELD ({text})", held(g, text) and not (root / "control" / "CONTROL.2.json").exists()
             and sched(root, 2) is None and not (root / "FENCE.json").exists(), g.alarms.get("control"))

    rep2 = report(root, pol, "SELF_PLAY", state="8" * 64)      # a later state: other bytes than control 1's
    sc = {"highest_round": 9, "target_rows": 1000}
    cb, evb = control(root, pol, 2, rep2, kind="target", scope=sc, over={"prev": "0" * 64})
    try2("C3", cb, evb, "prev does not link")
    cb, evb = control(root, pol, 2, rep2, kind="target", scope=sc)
    try2("C5", cb, W.canon(dict(rep2, outcome="REACHED")), "does not have the sha256", ev_name=sha(evb))
    rs = report(root, pol, "STOP")
    cb, evb = control(root, pol, 2, rs, kind="target", decision="SELF_PLAY", scope=sc)
    try2("C6", cb, evb, "is not the report's outcome")
    cb, evb = control(root, pol, 2, rep2, kind="target", scope=sc, over={"owner_policy": "6" * 64})
    try2("C7", cb, evb, "owner_policy")
    r7 = report(root, pol, "SELF_PLAY", inputs={"plan_sha256": "7" * 64, "state_sha256": "4" * 64,
                                                "pilot_sha256": "5" * 64})
    cb, evb = control(root, pol, 2, r7, kind="target", scope=sc)
    try2("C7b", cb, evb, "inputs.plan_sha256")
    r8 = report(root, pol, "SELF_PLAY", cut_before_d=0)
    cb, evb = control(root, pol, 2, r8, kind="target", scope=sc)
    try2("C8", cb, evb, "later than the one in force")
    cb, evb = control(root, pol, 2, rep2, kind="target", scope=sc,
                      over={"cutoff_utc": T(lease + rep2["cutoff_floor_s"] - 1)})
    try2("C9", cb, evb, "not the report's whole seconds")
    r15 = report(root, pol, "SELF_PLAY", local_only={"raw_files": [["pilot.x", "missing", "/home/x"]]})
    cb, evb = control(root, pol, 2, r15, kind="target", scope=sc)
    try2("C15", cb, evb, "local_only")
    cb, evb = control(root, pol, 2, rep2, kind="target", scope=sc)
    for f in (root / "inbox").glob("EVIDENCE.*"):
        if f.name != f"EVIDENCE.{sha(e1)}.json.zz":
            f.unlink()
    try2("C4 without its evidence", cb, evb, "is not there", evidence=False)
    send(root, 2, cb, evb)
    g.take_controls()
    accepted(root, 2, cb)
    s2 = sched(root, 2) or {}
    check("C4 the evidence arrived: accepted, SCHEDULE.2 head", (s2.get("evidence"), s2.get("prev"), s2.get("n")),
          (sha(cb), sha((root / "SCHEDULE.1.json").read_bytes()), 2))
    check("C4 SCHEDULE.2 rows", sorted(s2.get("ranges", []), key=key),
          sorted(want + rows([1, 2], 4, 13, 4, 2) + rows([1, 2], 5, 17, 4, 2), key=key))
    r3 = report(root, pol, "STOP")
    cb3, evb3 = control(root, pol, 3, r3, kind="target")
    send(root, 3, cb3, evb3)
    g.take_controls()
    f = json.loads((root / "FENCE.json").read_bytes()) if (root / "FENCE.json").exists() else {}
    check("C11 FENCE.json keys", sorted(f), ["at_utc", "cutoff_utc", "run_fingerprint", "schema", "why"])
    check("C11 FENCE.json cutoff_utc = the D in force (schedule 2's)", f.get("cutoff_utc"),
          T(W.utc(h["hard_cutoff_utc"], "h") - 600))
    true("C11 why names control 3", sha(cb3) in str(f.get("why")), f.get("why"))
    check("C11 no SCHEDULE.3", sched(root, 3), None)
    (root / "inbox" / "CONTROL.1.json.zz").write_bytes(zlib.compress(c1 + b" ", 6))
    g.take_controls()
    true("C16 a conflict: ALARM, the accepted copy unchanged",
         "other bytes than the accepted control 1" in g.alarms.get("conflict1", "")
         and (root / "control" / "CONTROL.1.json").read_bytes() == c1, g.alarms)
    done(g)

    # C10, C12
    root, pol = make_root("cb", [1, 2], rows([1, 2]), 7200)
    seal_piece(root, 1, 0)
    g = guard(root, pol)
    ru = report(root, pol, "UNQUALIFIED")
    cb1, evb1 = control(root, pol, 1, ru)
    send(root, 1, cb1, evb1)
    g.take_controls()
    accepted(root, 1, cb1)
    check("C10 UNQUALIFIED control 1: accepted, no schedule, no fence",
          ((root / "control" / "CONTROL.1.json").exists(), sched(root, 1), (root / "FENCE.json").exists()),
          (True, None, False))
    rp = report(root, pol, "SELF_PLAY")
    cb2, evb2 = control(root, pol, 2, rp, scope={"highest_round": 9, "target_rows": 1000})
    send(root, 2, cb2, evb2)
    g.take_controls()
    accepted(root, 2, cb2)
    check("C10 control 2 linked to 1: SCHEDULE.1 names control 2", (sched(root, 1) or {}).get("evidence"), sha(cb2))
    done(g)
    g2 = guard(root, pol)
    check("C12 the replay: 2 controls, nothing owed", (len(g2.ctl), g2.pending), (2, None))
    done(g2)
    copy = WORK / "cb_copy"
    shutil.copytree(root, copy, ignore=shutil.ignore_patterns("LOCK", "guard.log"))
    p = copy / "control" / "CONTROL.1.json"
    p.write_bytes(p.read_bytes().replace(b'"k":1', b'"k":1 '))
    try:
        guard(copy, pol)
        code = 0
    except W.Stop as e:
        code = e.code
    check("C12 a changed accepted control stops the start", code, 4)

    # C13
    def oc(name, choice, decision_rep, scope, want_eff, text=None):
        root, pol = make_root(name, [1], rows([1]), 7200, choice=choice)
        seal_piece(root, 1, 0)
        g = guard(root, pol)
        cb, evb = control(root, pol, 1, decision_rep(root, pol), scope=scope)
        send(root, 1, cb, evb)
        g.take_controls()
        got = ("fence" if (root / "FENCE.json").exists() else "schedule" if sched(root, 1) else
               "held" if g.alarms.get("control") else "none")
        ok = check(f"{name} effect", got, want_eff)
        if text:
            true(f"{name} HELD names it ({text})", held(g, text), g.alarms.get("control"))
        done(g)
        return ok

    label = lambda r, p, red=None: report(r, p, "OWNER_CHOICE", owner_choice="use the reduced target",  # noqa
                                          **({"reduced": red} if red else {}))
    oc("c13a", {"name": "use the reduced target", "action": "stop"}, label, None, "fence")
    red_ok = {"name": "stop now", "action": "reduced_target", "reduced_target_rows": 1500, "if_uncovered": "stop"}
    oc("c13b", red_ok, lambda r, p: report(r, p, "OWNER_CHOICE", owner_choice="stop",
                                           reduced={"covered": True, "target_rows": 1500}),
       {"highest_round": 9, "target_rows": 1500}, "schedule")
    oc("c13c", red_ok, lambda r, p: report(r, p, "OWNER_CHOICE", owner_choice="stop",
                                           reduced={"covered": True, "target_rows": 1500}),
       {"highest_round": 9, "target_rows": 1600}, "held", "more rows")
    oc("c13d", red_ok, lambda r, p: report(r, p, "OWNER_CHOICE", owner_choice="self_play",
                                           reduced={"covered": False, "target_rows": 1500}), None, "fence")
    red_no = {"name": "1.7B", "action": "reduced_target", "reduced_target_rows": 1500}
    oc("c13e", red_no, lambda r, p: report(r, p, "OWNER_CHOICE", owner_choice="stop",
                                           reduced={"covered": False, "target_rows": 1500}), None, "held",
       "names no action")
    oc("c13f", {"name": "stop", "action": "hope"}, lambda r, p: report(r, p, "OWNER_CHOICE", owner_choice="stop"),
       None, "held", "not one the guard knows")

    # C14
    root, pol = make_root("cm", [1], rows([1]), 7200)
    seal_piece(root, 1, 0)
    g = guard(root, pol)
    pairs = [["m1", 2, 2, 600]]
    rm = report(root, pol, "SELF_PLAY_AND_MATCHES", matches=pairs)
    cb, evb = control(root, pol, 1, rm, kind="matches", decision=[["m1", 2, 2, 601]])
    send(root, 1, cb, evb)
    g.take_controls()
    true("C14 pairs other than the report's: HELD", held(g, "pairs"), g.alarms.get("control"))
    cb, evb = control(root, pol, 1, rm, kind="matches", decision=pairs)
    send(root, 1, cb, evb)
    g.take_controls()
    accepted(root, 1, cb)
    check("C14 matches: accepted, no schedule", ((root / "control" / "CONTROL.1.json").exists(), sched(root, 1)),
          (True, None))
    true("C14 an ALARM: no match runner", "no match runner" in g.alarms.get("matches1", ""), g.alarms)
    cf, evf = control(root, pol, 2, {"outcome": "STOP", "why": "the owner's word", "inputs": plan_in(pol)},
                      kind="fence", decision="STOP")
    send(root, 2, cf, evf)
    g.take_controls()
    f = json.loads((root / "FENCE.json").read_bytes()) if (root / "FENCE.json").exists() else {}
    true("C14b kind fence: the fence names control 2", sha(cf) in str(f.get("why")), f)
    done(g)

    # C17
    root, pol = make_root("cr", [1], rows([1]), 7200)
    g = guard(root, pol)
    cb, evb = control(root, pol, 1, report(root, pol, "SELF_PLAY"), scope={"highest_round": 9, "target_rows": 9})
    send(root, 1, cb, evb)
    g.take_controls()
    true("C17a no sealed piece: HELD", held(g, "no sealed piece") and sched(root, 1) is None, g.alarms)
    done(g)
    seal_piece(root, 1, 0)
    g = guard(root, pol, floor_bytes=shutil.disk_usage(root).free + 10 ** 12)
    g.take_controls()
    true("C17b a floor above the free bytes: HELD", held(g, "bytes free") and sched(root, 1) is None, g.alarms)
    done(g)

    # C18
    root, pol = make_root("ce", [1, 2], rows([1, 2]), 7200)
    seal_piece(root, 1, 0)
    g = guard(root, pol)
    cb, evb = control(root, pol, 1, report(root, pol, "SELF_PLAY"), scope={"highest_round": 5, "target_rows": 9})
    send(root, 1, cb, evb)
    g.take_controls()
    g.extend()
    check("C18 no range seal: no extension", sched(root, 2), None)
    seal_range(root, 1, 1)
    g.extend()
    check("C18 the seal of round 1 only: no extension", sched(root, 2), None)
    seal_range(root, 2, 2)
    g.extend()
    s1, s2 = sched(root, 1) or {}, sched(root, 2) or {}
    check("C18 r0002.w002: SCHEDULE.2 adds round 4 alone",
          sorted((r["slot"], r["round"], r["first"], r["last"], r["schedule"]) for r in s2.get("ranges", [])
                 if r["round"] == 4), [(1, 4, 13, 16, 2), (2, 4, 13, 16, 2)])
    check("C18 SCHEDULE.2 rounds and head", (max((r["round"] for r in s2.get("ranges", [])), default=None),
                                             s2.get("cutoff_utc"), s2.get("dispatch_end_utc"), s2.get("evidence")),
          (4, s1.get("cutoff_utc"), s1.get("dispatch_end_utc"), sha(cb)))
    g.extend()
    check("C18 nothing new: no SCHEDULE.3", sched(root, 3), None)
    seal_range(root, 3, 1)
    g.extend()
    check("C18 r0003.w001: SCHEDULE.3 adds round 5", max((r["round"] for r in (sched(root, 3) or {}).get(
        "ranges", [])), default=None), 5)
    seal_range(root, 4, 1)
    seal_range(root, 5, 2)
    g.extend()
    check("C18 round 6 is above the scope: no SCHEDULE.4", sched(root, 4), None)
    done(g)

    # C19
    root, pol = make_root("co", [1], rows([1]), 7200)
    seal_piece(root, 1, 0)
    (root / "w001").mkdir(exist_ok=True)
    ended_slot(root, 1)
    (root / "fake").mkdir()
    cb, evb = control(root, pol, 1, report(root, pol, "SELF_PLAY"), scope={"highest_round": 9, "target_rows": 9})
    (root / "control").mkdir()
    (root / "control" / f"EVIDENCE.{sha(evb)}.json").write_bytes(evb)
    (root / "control" / "CONTROL.1.json").write_bytes(cb)
    (root / "STOP").write_text("stop", encoding="ascii")
    g = guard(root, pol)
    g.one_pass()
    check("C19 with the STOP file: no schedule", sched(root, 1), None)
    (root / "STOP").unlink()
    g.one_pass()
    check("C19 without it: SCHEDULE.1 names control 1", (sched(root, 1) or {}).get("evidence"), sha(cb))
    end_packer(g, root)
    done(g)

    # C19b
    root, pol = make_root("cp", [1], rows([1]), 7200)
    (root / "w001").mkdir()
    ended_slot(root, 1)
    (root / "fake").mkdir()
    cb, evb = control(root, pol, 1, report(root, pol, "SELF_PLAY"), scope={"highest_round": 9, "target_rows": 9})
    (root / "control").mkdir()
    (root / "control" / f"EVIDENCE.{sha(evb)}.json").write_bytes(evb)
    (root / "control" / "CONTROL.1.json").write_bytes(cb)
    accepted(root, 1, cb)
    cf, evf = control(root, pol, 2, {"outcome": "STOP", "why": "the owner's word", "inputs": plan_in(pol)},
                      kind="fence", decision="STOP")
    send(root, 2, cf, evf)
    g = guard(root, pol)
    g.one_pass()
    true("C19b no sealed piece: no schedule, the ALARM pending names the room",
         sched(root, 1) is None and "room" in g.alarms.get("pending", ""), g.alarms)
    check("C19b control 2 not taken while control 1's effect is owed",
          ((root / "control" / "CONTROL.2.json").exists(), (root / "FENCE.json").exists()), (False, False))
    seal_piece(root, 1, 0)
    g.one_pass()
    s1 = sched(root, 1) or {}
    f = json.loads((root / "FENCE.json").read_bytes()) if (root / "FENCE.json").exists() else {}
    check("C19b the seal arrived: SCHEDULE.1 names control 1", s1.get("evidence"), sha(cb))
    true("C19b then control 2: the fence names it, cutoff = schedule 1's",
         sha(cf) in str(f.get("why")) and f.get("cutoff_utc") == s1.get("cutoff_utc") is not None, f)
    end_packer(g, root)
    done(g)

    # V1a, V1b: the closing record (R1)
    got = []
    for x in ("a", "b"):
        root, pol = make_root(f"v1{x}", [1], rows([1]), 7200)
        (root / "guard").mkdir()
        rec = b"" if x == "a" else W.canon({
            "at_utc": T(time.time()), "packer": "ended", "run_fingerprint": "f" * 64, "schema": 2, "slots_ended": [1],
            "slots_unreconciled": [], "terminal": {"lines": 3, "sha256": "8" * 64, "zz_sha256": "9" * 64}})
        (root / "guard" / "CLOSED.json").write_bytes(rec)
        g = guard(root, pol)
        try:
            got.append(("exit", g.run()))
        except G.Stop as e:
            got.append((e.code, "CLOSED.json" in str(e)))
        got.append((g.packer is None, g.slots[1].g is None))
        done(g)
    check("V1a, V1b a 0-byte and another run's CLOSED.json: Stop 4 naming it, nothing started", got,
          [(4, True), (True, True), (4, True), (True, True)])

    # V2: the fence (R2)
    root, pol = make_root("v2a", [1, 2], rows([1, 2]), 7200)
    (root / "FENCE.json").write_bytes(b"")
    for k in (1, 2):
        (root / f"w{k:03d}").mkdir()
        (root / f"w{k:03d}" / "journal.txt").write_bytes(b'{"t":"ended"}\n')
    g = guard(root, pol)
    try:
        g.one_pass()
        rc = None
    except G.Stop as e:
        rc = (e.code, "FENCE.json" in str(e))
    check("V2a a 0-byte FENCE.json and bare ended lines (Neon's repro): Stop 4 naming FENCE.json, nothing started "
          "or closed", (rc, g.packer is None, [g.slots[k].g is None for k in (1, 2)],
                        (root / "guard" / "CLOSED.json").exists()), ((4, True), True, [True, True], False))
    done(g)
    got = []
    for x, over in (("b", {"run_fingerprint": "f" * 64}), ("c", {"cutoff_utc": "2026-01-01T00:00:00Z"})):
        root, pol = make_root(f"v2{x}", [1], rows([1]), 7200)
        g = guard(root, pol)
        f = {"at_utc": T(time.time()), "cutoff_utc": g.d_text(), "run_fingerprint": fp_of(root), "schema": 2,
             "why": "D"}
        f.update(over)
        (root / "FENCE.json").write_bytes(W.canon(f))
        try:
            g.one_pass()
            got.append(None)
        except G.Stop as e:
            got.append(e.code)
        done(g)
    check("V2b, V2c another run's fence, a fence of another D: Stop 4", got, [4, 4])
    root, pol = make_root("v2d", [1], rows([1]), 7200)
    g = guard(root, pol)
    (root / "FENCE.json").write_bytes(W.canon({"at_utc": T(time.time()), "cutoff_utc": g.d_text(),
                                               "run_fingerprint": fp_of(root), "schema": 2, "why": "D"}))
    fd = getattr(g, "fenced", None)
    check("V2d this run's fence of the D in force: fenced (control)", fd() if fd else (root / "FENCE.json").exists(),
          True)
    done(g)

    # V3: an ended slot (R3)
    root, pol = make_root("v3", [1, 2, 3, 4, 5, 6], rows([1, 2, 3, 4, 5, 6]), 7200)
    fp = fp_of(root)
    ident = lambda k, f=fp: W.canon({"run": "gt", "run_fingerprint": f, "schema": 2, "slot": k})  # noqa: E731
    full = lambda k, i=-1, s=None: W.canon({"epoch": 1, "last_index": i,  # noqa: E731
                                            "last_seal": s or f"genesis:{fp}:w{k:03d}", "t": "ended", "why": "test"})
    for k in (1, 2, 3, 4):
        (root / f"w{k:03d}").mkdir()
    (root / "w001" / "IDENTITY.json").write_bytes(ident(1))
    (root / "w001" / "journal.txt").write_bytes(b'{"t":"ended"}\n')
    (root / "w002" / "journal.txt").write_bytes(full(2))
    (root / "w003" / "IDENTITY.json").write_bytes(ident(3, "f" * 64))
    (root / "w003" / "journal.txt").write_bytes(full(3))
    seal_piece(root, 4, 0)
    (root / "w004" / "IDENTITY.json").write_bytes(ident(4))
    (root / "w004" / "journal.txt").write_bytes(full(4, 0, "0" * 64))
    ended_slot(root, 5)
    seal_piece(root, 6, 0)
    ended_slot(root, 6, last_index=0)
    g = guard(root, pol)
    check("V3 ended only by the worker's own end: a bare line, no IDENTITY, another run's IDENTITY, a last_seal off "
          "its chain: not ended; the genesis end and the end at its seal: ended",
          [g.slot_ended(k) for k in range(1, 7)], [False, False, False, False, True, True])
    done(g)

    # V4: the piece seals of the room test (R4)
    root, pol = make_root("v4a", [1, 2], rows([1, 2]), 7200)
    seal_piece(root, 1, 0, games=1000000, raw=0, run_fingerprint="f" * 64)
    g = guard(root, pol)
    cb, evb = control(root, pol, 1, report(root, pol, "SELF_PLAY"), scope={"highest_round": 9, "target_rows": 9})
    send(root, 1, cb, evb)
    g.take_controls()
    true("V4a another run's piece seal (Neon's repro): not counted, HELD no sealed piece, the ALARM seal1 names it",
         held(g, "no sealed piece") and sched(root, 1) is None and "p000000.seal.json" in g.alarms.get("seal1", ""),
         g.alarms)
    done(g)
    got = []
    for x in ("b", "c", "d"):
        root, pol = make_root(f"v4{x}", [1], rows([1]), 7200)
        if x == "b":
            seal_piece(root, 1, 0, index=5)
        else:
            seal_piece(root, 1, 0)
            seal_piece(root, 1, 1, **({"prev_seal": "0" * 64} if x == "c" else {}))
        g = guard(root, pol)
        g.read_seals()
        got.append((g.games_total, g.pieces_total, "seal1" in g.alarms))
        done(g)
    check("V4b, V4c, V4d a seal whose index is not its name's: none; a seal off the chain: only the one before; two "
          "of the chain: both (control)", got, [(0, 0, True), (4, 1, True), (8, 2, False)])

    # V5: the range seals (R5), C18's setting
    root, pol = make_root("v5", [1, 2], rows([1, 2]), 7200)
    seal_piece(root, 1, 0)
    g = guard(root, pol)
    cb, evb = control(root, pol, 1, report(root, pol, "SELF_PLAY"), scope={"highest_round": 5, "target_rows": 9})
    send(root, 1, cb, evb)
    g.take_controls()
    (root / "ranges").mkdir(exist_ok=True)
    got = []
    (root / "ranges" / "r0002.w002.seal.json").write_bytes(b"")
    g.extend()
    got.append(sched(root, 2) is None)
    seal_range(root, 2, 2, run_fingerprint="f" * 64)
    g.extend()
    got.append(sched(root, 2) is None)
    seal_range(root, 2, 2, last=row_of(root, 2, 2)["last"] + 1)
    g.extend()
    got.append(sched(root, 2) is None)
    seal_range(root, 2, 2, first_index=0, first_prev_seal=f"genesis:{fp_of(root)}:w002", through_index=0,
               through_seal="0" * 64)
    g.extend()
    got.append(sched(root, 2) is None)
    check("V5a-d r0002.w002 0 bytes, another run's, another interval's, its through seal not on disk: no "
          "SCHEDULE.2, the ALARM range2.2", (got, "range2.2" in g.alarms), ([True] * 4, True))
    seal_range(root, 2, 2)
    g.extend()
    s2 = sched(root, 2) or {}
    check("V5e the genuine seal: SCHEDULE.2 adds round 4 alone (control)",
          sorted((r["slot"], r["round"]) for r in s2.get("ranges", []) if r["schedule"] == 2), [(1, 4), (2, 4)])
    done(g)

    # V6: an orphan of an earlier guard (R6): the decision without a process touched, and a number taken over
    og = getattr(G, "orphan_groups", None)
    table = {100: [(100, b"python -I -B /r/run/worker.py --root R"), (101, b"/e/forge.exe")],
             200: [(201, b"/e/forge.exe")], 300: [(301, b"vim notes.txt")], 400: [], 600: [(601, b"/e/forge.exe")],
             700: [(701, b"python -I -B /c/conv.py")]}
    foreign = [(100, "worker"), (200, "worker"), (300, "worker"), (400, "packer"), (500, "worker"),
               (600, "mystery"), (700, "packer")]
    check("V6 the leader lives: left; its worker gone: the engine; nothing of the day: none; gone: dropped; a kind "
          "not known: left; the packer gone: its converter",
          og(foreign, table, ("R", "/e/forge.exe", "/c/conv.py")) if og else None,
          ([(100, "worker"), (200, "worker"), (300, "worker"), (600, "mystery"), (700, "packer")],
           [(200, "worker", [201]), (700, "packer", [701])]))
    root, pol = make_root("v6b", [1], rows([1]), 7200)
    g = guard(root, pol)
    g.foreign = [(4242, "packer"), (4343, "worker")]
    g.record_group(SimpleNamespace(pid=4242), "worker", 1)
    check("V6b a group number this guard starts is no earlier guard's any more", g.foreign, [(4343, "worker")])
    done(g)

    # V11 (R12, Linux only: the seats run it): the guard's own end goes through a pidfd and asks again first
    if os.name != "nt":
        ee = getattr(G, "end_exact", None)
        true("V11 end_exact exists (R12)", callable(ee), ee)
        if callable(ee):
            p = subprocess.Popen([sys.executable, "-I", "-B", "-c", "import time; time.sleep(60)"])
            sent = ee(p.pid, lambda: False)
            time.sleep(0.5)
            check("V11a ours() False: nothing sent, the process lives", (sent, p.poll()), (False, None))
            sent = ee(p.pid, lambda: True)
            try:
                code = p.wait(5)
            except subprocess.TimeoutExpired:
                code = None
            check("V11b ours() True: sent, ended within 5 s", (sent, code is not None), (True, True))
            p.kill()
            p.wait()
            z = subprocess.Popen([sys.executable, "-I", "-B", "-c", "pass"])
            while not os.waitid(os.P_PID, z.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT):
                time.sleep(0.01)
            check("V11c a child that has exited, not reaped (its pidfd readable), ours() True: nothing sent",
                  ee(z.pid, lambda: True), False)
            z.wait()

    # V7: the boot (R7)
    got = []
    for x, hb, res in (("a", None, []), ("b", None, [(BOOT, "other-boot")]),
                       ("c", "another-boot", [("another-boot", BOOT)]),
                       ("d", "another-boot", [("another-boot", BOOT, {"prev": "0" * 64})]),
                       ("e", "another-boot", [("x-boot", BOOT)]),
                       ("f1", "another-boot", [("another-boot", "b2-boot"), ("b2-boot", BOOT)]),
                       ("f2", "another-boot", [("another-boot", "b2-boot"), ("b9-boot", BOOT)]),
                       ("g", "another-boot", [("another-boot", BOOT, {"instance_provable": False})])):
        root, pol = make_root(f"v7{x}", [1], rows([1]), 7200, **({"boot": hb} if hb else {}))
        for n, r in enumerate(res, 1):
            resume(root, n, r[0], r[1], **(r[2] if len(r) > 2 else {}))
        g = guard(root, pol)
        got.append(g.boot_ok())
        done(g)
    check("V7 admitted: the header's boot alone, a linked RESUME to this boot, a chain of two; not: a RESUME away "
          "from the header's boot, prev not first, old_boot_id not the header's, a broken chain, not provable",
          got, [True, False, True, False, False, True, False, False])

    # V8: the policy (R8)
    got = []
    for x, change in (("a", lambda q: q.pop("target_rows")), ("b", lambda q: q.update(target_rows=True)),
                      ("c", lambda q: q.update(pilot_rounds_declared=2))):
        root, pol = make_root(f"v8{x}", [1], rows([1]), 7200)
        plan = json.loads(pol.read_bytes())
        change(plan)
        pol.write_text(json.dumps(plan, indent=1) + "\n", encoding="ascii")
        try:
            g = guard(root, pol)
            got.append(None)
            done(g)
        except G.Stop as e:
            got.append(e.code)
    check("V8 a policy without target_rows, with target_rows true, declaring 2 pilot rounds for a pilot of 1: Stop 4",
          got, [4, 4, 4])

    # V9: a fence control bound to the plan (R9)
    root, pol = make_root("v9", [1], rows([1]), 7200)
    g = guard(root, pol)
    cf, evf = control(root, pol, 1, {"outcome": "STOP", "why": "x", "inputs": dict(plan_in(pol), plan_sha256="0" * 64)},
                      kind="fence", decision="STOP")
    send(root, 1, cf, evf)
    g.take_controls()
    true("V9 a fence control computed from another plan: HELD inputs.plan_sha256, no FENCE.json",
         held(g, "inputs.plan_sha256") and not (root / "FENCE.json").exists(), g.alarms)
    done(g)

    # V12 (G-A, Fable 25 Nov): the schedule chain ends at SCHEDULE.999 (every program's grammar); SimpleNamespace is the
    # module's import (an import here made the name local to all of part_c: UnboundLocalError at its first use, 12:45)
    rws =[{"first": 1, "last": 4, "round": 1, "schedule": 0, "short": False, "slot": 1}]

    def stand(n_before):
        return SimpleNamespace(rows=lambda: rws, sched=[(b"s\n", {})] * n_before, h={"slots": [1]}, fp="f" * 64)
    cut, disp = T(time.time() + 60), T(time.time() + 30)
    try:
        s999 = json.loads(G.Guard.new_schedule(stand(998), "e" * 64, 2, cut, disp))
        got999 = (s999.get("n"), max(r["round"] for r in s999["ranges"]))
    except Exception as e:  # noqa: BLE001   the case fails with its reason
        got999 = repr(e)[:160]
    try:
        G.Guard.new_schedule(stand(999), "e" * 64, 2, cut, disp)
        got1000 = "schedule 1000 made"
    except G.Held as e:
        got1000 = "SCHEDULE.999" in str(e)
    check("V12 (G-A) the chain ends at SCHEDULE.999: schedule 999 is made (n 999, round 2), a 1000th is HELD naming "
          "it", (got999, got1000), ((999, 2), True))

    # G11 (v16): the clock file, written by write_clock from readings the test sets
    root, pol = make_root("g11", [1], rows([1]), 86400)
    g = guard(root, pol)
    a, at = staged(g)

    def put(run, utc_off=0.0):
        r = at(run, utc_off)
        g.write_clock(r, g.state(r))
        return clock_rec(root)
    c = put(5.0)
    check("G1 the first write: CLOCK.json canonical with exactly its five keys; n 1, schema 1, this run, play, utc_ms "
          "= anchor UTC + run (within 1 ms)",
          (sorted(c) if isinstance(c, dict) else c, isinstance(c, dict) and (c["n"], c["schema"], c["run_fingerprint"]
           == g.fp, c["state"], abs(c["utc_ms"] - (a[0] + 5.0) * 1000) <= 1)), (G.CLOCK_KEYS, (1, 1, True, "play", True)))
    c1, c2 = put(70.0, 25170.0), put(140.0, -30.0)
    check("G1b UTC 25,170 s ahead (no bound crossed): utc_ms = anchor + run, play; UTC 30 s behind: utc_ms = that UTC",
          [isinstance(x, dict) and (x["n"], x["state"], abs(x["utc_ms"] - want * 1000) <= 1) for x, want in
           ((c1, a[0] + 70.0), (c2, a[0] + 110.0))], [(2, "play", True), (3, "play", True)])
    ns = []
    for i in range(50):
        x = put(200.0 + 60 * i)
        ns.append(x["n"] if isinstance(x, dict) and sorted(x) == G.CLOCK_KEYS else x)
    check("G2 50 writes: every read is the whole record, n rising by 1; no .CLOCK.json.*.part left",
          (ns, sorted(q.name for q in root.glob(".CLOCK.json.*"))), (list(range(4, 54)), []))
    last = 200.0 + 60 * 49
    got = [field(put(last + d), "n") for d in (30.0, 59.9, 60.0, 125.0)]
    check("G3 CLOCK_EVERY 60.0; 30 s and 59.9 s after a write nothing, 60 s and 125 s after it a write each",
          (G.CLOCK_EVERY, got), (60.0, [53, 53, 54, 55]))
    done(g)
    g = guard(root, pol)
    a, at = staged(g)
    g4 = [g.clock_n, field(put(1.0), "n")]          # n at the start, then the first write
    done(g)
    for name, data in (("another run's", W.canon({"n": 7, "run_fingerprint": "0" * 64, "schema": 1,
                                                  "state": "play", "utc_ms": 1800000000000})),
                       ("not a record", b"not a record\n")):
        (root / "CLOCK.json").write_bytes(data)
        g = guard(root, pol)
        a, at = staged(g)
        n0 = g.clock_n
        c = put(1.0)
        g4.append((name, n0, isinstance(c, dict) and (c["n"], c["run_fingerprint"] == g.fp)))
        done(g)
    check("G4 a guard started again continues n (56 after 55); another run's CLOCK.json and one that is not a "
          "record are replaced from n 1", g4,
          [55, 56, ("another run's", 0, (1, True)), ("not a record", 0, (1, True))])
    root, pol = make_root("g11s", [1], rows([1]), 7200)
    g = guard(root, pol)
    a, at = staged(g)
    g.B.set("dispatch_end", a[0] + 3600)
    sts = [field(put(100.0), "state"), field(put(3700.0), "state"), field(put(7300.0), "state")]
    g.fence("D")
    sts.append(field(put(7400.0), "state"))
    done(g)
    root, pol = make_root("g11h", [1], rows([1]), 7200)
    g = guard(root, pol)
    a, at = staged(g)
    c = put(100.0, 7300.0)
    sts.append(isinstance(c, dict) and (c["state"], abs(c["utc_ms"] - (a[0] + 100.0) * 1000) <= 1))
    done(g)
    root, pol = make_root("g11f", [1], rows([1]), 7200)
    g = guard(root, pol)
    a, at = staged(g)
    g.fence("control 3: a stop before D")
    sts.append(field(put(100.0), "state"))
    done(g)
    check("G5 (S5) state is the clocks' alone: play, dispatch_end, cutoff, cutoff after the fence at D, hold with "
          "UTC alone 7,300 s ahead (utc_ms still anchor + run), play after a fence before D", sts,
          ["play", "dispatch_end", "cutoff", "cutoff", ("hold", True), "play"])
    # G6 (ADDENDUM 9, Fable's proof of 18:14 on the real guard): a write that fails is the ALARM clock, tried again
    root, pol = make_root("g11w", [1], rows([1]), 86400)
    (root / "CLOCK.json").mkdir()
    g = guard(root, pol)
    a, at = staged(g)
    calls, real_alarm = [], g.alarm

    def counted(key, text):                         # the guard writes a repeated alarm text once: the count shows a try
        calls.append((key, "CLOCK.json not written" in text))
        real_alarm(key, text)
    g.alarm = counted

    def tries(run):
        r = at(run)
        try:
            g.write_clock(r, g.state(r))
            return "returned"
        except BaseException as e:  # noqa: BLE001   the answer of a method that lets its error out
            return f"{type(e).__name__} escaped"

    def scratch():
        return sorted(q.name for q in root.glob(".CLOCK.json.*"))
    w = [(tries(5.0), list(calls), g.clock_n, g.clock_at, (root / "CLOCK.json").is_dir())]
    w.append((tries(6.0), list(calls), g.clock_n, g.clock_at, len(scratch()) <= 1, "clock" in g.alarms))
    (root / "CLOCK.json").rmdir()
    w.append((tries(7.0), field(clock_rec(root), "n"), "clock" in g.alarms, g.clock_n, g.clock_at == a[1] + 7.0,
              scratch()))
    (root / f".CLOCK.json.{os.getpid()}.part").write_bytes(b"left by a crash\n")
    w.append((tries(67.0), field(clock_rec(root), "n"), scratch()))
    done(g)
    check("G6 (Fable's proof) CLOCK.json a folder: the write returns, alarm 'clock' names it, n 0, clock_at None, "
          "still a folder; the next pass tries again (a second alarm call, at most one scratch, the alarm standing); "
          "the folder gone: written n 1, the alarm cleared, clock_at the reading's; a leftover scratch of this "
          "process, 60 s later: written n 2, no scratch left", w,
          [("returned", [("clock", True)], 0, None, True),
           ("returned", [("clock", True), ("clock", True)], 0, None, True, True),
           ("returned", 1, False, 1, True, []), ("returned", 2, [])])


# ---- P ---------------------------------------------------------------------------------------------------------------
def part_p():
    # T1 (R11): a process of the test's own is known by number AND creation time; another creation time stands in for
    # a number Windows has given again: neither counted nor ended
    p = subprocess.Popen([sys.executable, "-I", "-B", "-c", "import time; time.sleep(60)"])
    c = created_of(p.pid)
    true("T1a a process of the test's own: its creation time is an integer", type(c) is int, c)
    other = (c or 0) + 1
    check("T1b alive by its number and creation time", alive(p.pid, c), True)
    check("T1c alive by its number and another creation time", alive(p.pid, other), False)
    kill(p.pid, other)
    time.sleep(1.0)
    check("T1d a kill by its number and another creation time: it still lives", p.poll(), None)
    kill(p.pid, c)
    try:
        code = p.wait(5)
    except subprocess.TimeoutExpired:
        code = None
    true("T1e a kill by its number and creation time: it has ended within 5 s", code is not None, code)
    p.kill()
    p.wait()
    G.RUN_DIR = FAKE
    G.RETRY = {6: 0.5, 8: 0.5, 3: 0.5, 0: 0.5}
    root, pol = fake_root("pa", [1, 2, 3, 4], {1: ["sleep:1"], 2: ["exit:4", "ended"], 3: ["orphan"],
                                               4: ["exit:6", "hang"]}, 8)
    t_pa0 = time.time()
    g = guard(root, pol)
    seen = {}
    faulted2 = []

    def each(g):
        if g.slots[2].faulted and not (root / "FENCE.json").exists():
            faulted2.append(True)
        pid = root / "fake" / "orphan.3.pid"
        if "orphan" not in seen and g.slots[3].g is None and g.slots[3].ended and pid.exists():
            seen["orphan"] = alive(*map(int, pid.read_text().split()))

    closed = drive(g, lambda g: False, 60, each)
    check("PA the day closed", closed, True)
    ck = clock_rec(root)
    true("G1 (PA: the guard's REAL pass wrote it) CLOCK.json is this run's record, n >= 1, a state of the four, "
         "utc_ms inside the day",
         isinstance(ck, dict) and sorted(ck) == G.CLOCK_KEYS and ck["schema"] == 1 and ck["run_fingerprint"] ==
         fp_of(root) and type(ck["n"]) is int and ck["n"] >= 1 and ck["state"] in ("play", "dispatch_end",
         "cutoff", "hold") and t_pa0 * 1000 - 1000 <= ck["utc_ms"] <= time.time() * 1000 + 1000, ck)
    h = hdr(root)
    f = json.loads((root / "FENCE.json").read_bytes()) if (root / "FENCE.json").exists() else {}
    check("PA FENCE.json", {k: f.get(k) for k in ("cutoff_utc", "why", "schema", "run_fingerprint")} | {
        "keys": sorted(f)}, {"cutoff_utc": h["hard_cutoff_utc"], "why": "D", "schema": 2,
                             "run_fingerprint": sha((root / "RUN.json").read_bytes()),
                             "keys": ["at_utc", "cutoff_utc", "run_fingerprint", "schema", "why"]})
    true("PA the fence written at D (whole seconds: D - 1 to D + 10)",
         f and -1 <= W.utc(f["at_utc"], "a") - W.utc(h["hard_cutoff_utc"], "h") <= 10, f)
    check("PA slot 1: one start", len(starts(root, 1)), 1)
    s2 = starts(root, 2)
    check("PA slot 2: two starts, the second with the fence", [x["fence"] for x in s2], [False, True])
    true("PA slot 2 FAULTED while the day played", bool(faulted2), g.alarms)
    check("PA slot 3: one start", len(starts(root, 3)), 1)
    check("PA slot 3's child not alive after the reap", seen.get("orphan"), False)
    s4 = starts(root, 4)
    check("PA slot 4: two starts, both before the fence", [x["fence"] for x in s4], [False, False])
    true("PA slot 4: the alarm late4 and UNRECONCILED", "late4" in g.alarms and bool(g.slots[4].unreconciled),
         (g.alarms, g.slots[4].unreconciled))
    sp = (root / "STOP_PACKER").read_bytes() if (root / "STOP_PACKER").exists() else b""
    try:
        spr = W.parse_canon(sp, "STOP_PACKER")
    except ValueError:
        spr = {}
    check("PA STOP_PACKER", (sorted(spr), spr.get("unreconciled")),
          (["at_utc", "run_fingerprint", "schema", "unreconciled"], [4]))
    cl = json.loads((root / "guard" / "CLOSED.json").read_bytes()) if (root / "guard" / "CLOSED.json").exists() else {}
    tj = (root / "TERMINAL.jsonl").read_bytes() if (root / "TERMINAL.jsonl").exists() else b""
    tz = (root / "TERMINAL.jsonl.zz").read_bytes() if (root / "TERMINAL.jsonl.zz").exists() else b""
    check("PA CLOSED.json", (cl.get("slots_ended"), cl.get("slots_unreconciled"), cl.get("terminal"),
                             cl.get("packer")), ([1, 2, 3], [4], {"lines": len(tj.splitlines()), "sha256": sha(tj),
                                                                  "zz_sha256": sha(tz)}, "ended"))
    ts = root / "fake" / "terminal.starts.txt"
    tst = [float(x) for x in ts.read_text().split()] if ts.exists() else []
    pf = root / "fake" / "packer.final"
    true("PA the terminal writer: one start, after the packer's last pass",
         len(tst) == 1 and pf.exists() and tst[0] >= float(pf.read_text()), (tst, pf.exists()))
    ps = (root / "fake" / "packer.starts.txt")
    check("PA the packer: one start, its last pass",
          (len(ps.read_text().splitlines()) if ps.exists() else 0, (root / "fake" / "packer.final").exists()),
          (1, True))
    gl = (root / "guard" / "groups.jsonl").read_bytes().splitlines() if (root / "guard" / "groups.jsonl").exists() \
        else []
    kinds = sorted(json.loads(x)["kind"] for x in gl)
    check("PA groups.jsonl", (kinds, all(json.loads(x)["boot_id"] == BOOT for x in gl)),
          (["packer", "terminal"] + ["worker"] * 6, True))
    hl = (root / "guard" / "hourly.jsonl").read_bytes().splitlines() if (root / "guard" / "hourly.jsonl").exists() \
        else []
    first = json.loads(hl[0]) if hl else {}
    check("PA hourly.jsonl first line", (first.get("t"), first.get("state"), first.get("schedules"),
                                         first.get("controls")), ("hour", "play", 0, 0))
    pids = [(x["pid"], x.get("created")) for k in (1, 2, 3, 4) for x in starts(root, k)]
    op = root / "fake" / "orphan.3.pid"
    if op.exists():
        pids.append(tuple(map(int, op.read_text().split())))
    true("PA the recorded processes carry their creation time (R11)",
         bool(pids) and all(type(c) is int for _, c in pids), pids)
    check("PA no process of the day alive", [p for p, c in pids if alive(p, c)], [])
    done(g)

    # V1c: the closed day started again (R1)
    def snap(r):
        return sorted((str(q.relative_to(r)), q.stat().st_size) for q in r.rglob("*") if q.is_file() and q.name != "LOCK")
    before = snap(root)
    g2 = guard(root, pol)
    try:
        rc = g2.run()
    except G.Stop as e:
        rc = ("stop", e.code, str(e)[:200])
    check("V1c the closed day started again: exit 0 at once, nothing written", (rc, snap(root) == before), (0, True))
    done(g2)

    # PB
    root, pol = fake_root("pb", [1], {1: ["ended"]}, 3600)
    (root / "STOP").write_text("stop", encoding="ascii")
    g = guard(root, pol)
    for _ in range(3):
        g.one_pass()
        time.sleep(0.1)
    check("PB the STOP file: nothing started", (len(starts(root, 1)), (root / "fake" / "packer.starts.txt").exists(),
                                                "stop" in g.alarms), (0, False, True))
    (root / "STOP").unlink()
    drive(g, lambda g: g.slots[1].ended, 10)
    check("PB STOP removed: one start, ended", (len(starts(root, 1)), g.slots[1].ended), (1, True))
    end_packer(g, root)
    done(g)
    root, pol = fake_root("pb2", [1], {1: ["ended"]}, 3600, boot="another-boot")
    g = guard(root, pol)
    for _ in range(3):
        g.one_pass()
        time.sleep(0.1)
    check("PB another boot: nothing started, the alarm boot", (len(starts(root, 1)), "boot" in g.alarms), (0, True))
    resume(root, 1, "another-boot", BOOT)
    drive(g, lambda g: g.slots[1].ended, 10)
    check("PB a RESUME naming this boot: the slot starts", len(starts(root, 1)), 1)
    end_packer(g, root)
    done(g)

    # PC
    G.RETRY = {6: 0.2, 8: 0.5, 3: 0.5, 0: 0.5}
    root, pol = fake_root("pc", [1], {1: ["exit:6"]}, 3600)
    g = guard(root, pol)
    drive(g, lambda g: bool(g.slots[1].faulted), 15)
    t_end = time.monotonic() + 1.0
    while time.monotonic() < t_end:
        g.one_pass()
        time.sleep(0.1)
    check("PC five starts, then FAULTED", (len(starts(root, 1)), g.slots[1].faulted),
          (5, "five starts within one hour"))
    end_packer(g, root)
    done(g)

    # PD
    G.RETRY = {6: 0.5, 8: 0.5, 3: 0.2, 0: 0.5}
    root, pol = fake_root("pd", [1], {1: ["ended"]}, 3600)
    (root / "w001").mkdir()
    lk = W.SlotLock(root / "w001")
    g = guard(root, pol)
    t_end = time.monotonic() + 3.0
    while time.monotonic() < t_end:
        g.one_pass()
        time.sleep(0.1)
    check("PD the slot's lock held by another process: no start, not FAULTED, the ALARM held1",
          (len(starts(root, 1)), g.slots[1].faulted, "held1" in g.alarms), (0, None, True))
    lk.release()
    drive(g, lambda g: g.slots[1].ended, 10)
    check("PD released: one start, ended, held1 gone", (len(starts(root, 1)), g.slots[1].ended, "held1" in g.alarms),
          (1, True, False))
    end_packer(g, root)
    done(g)

    # PE
    root, pol = fake_root("pe", [1], {1: ["ended"]}, 3600)
    (root / "out").mkdir()
    lk = W.SlotLock(root / "out")
    g = guard(root, pol)
    drive(g, lambda g: g.slots[1].ended, 10)
    t_end = time.monotonic() + 1.0
    while time.monotonic() < t_end:
        g.one_pass()
        time.sleep(0.1)
    ps = root / "fake" / "packer.starts.txt"
    n_ps = lambda: len(ps.read_text().splitlines()) if ps.exists() else 0  # noqa: E731
    check("PE out/LOCK held by another packer: the slot ended, no packer start, the ALARM packer_held",
          (g.slots[1].ended, n_ps(), "packer_held" in g.alarms), (True, 0, True))
    lk.release()
    drive(g, lambda g: n_ps() > 0, 10)
    check("PE released: the packer starts", n_ps(), 1)
    end_packer(g, root)
    done(g)

    # PF
    root, pol = fake_root("pf", [1], {1: ["ended"]}, 4)
    (root / "w001").mkdir()
    lk = W.SlotLock(root / "w001")
    g = guard(root, pol)
    closed = drive(g, lambda g: False, 30)
    sp = (root / "STOP_PACKER").read_bytes() if (root / "STOP_PACKER").exists() else b""
    cl = json.loads((root / "guard" / "CLOSED.json").read_bytes()) if (root / "guard" / "CLOSED.json").exists() else {}
    check("PF a lock held all day: closed, no start, UNRECONCILED, STOP_PACKER [1], CLOSED unreconciled [1]",
          (closed, len(starts(root, 1)), bool(g.slots[1].unreconciled), json.loads(sp).get("unreconciled") if sp
           else None, cl.get("slots_unreconciled")), (True, 0, True, [1], [1]))
    lk.release()
    done(g)

    # V10: the terminal writer fails (R10)
    for x, mode, text in (("a", "exit4", "exited with 4"), ("b", "badzz", "does not decode"),
                          ("c", "nofooter", "footer")):
        root, pol = fake_root(f"v10{x}", [1], {1: ["ended"]}, 4)
        (root / "fake" / "terminal.mode").write_text(mode, encoding="ascii")
        g = guard(root, pol)
        closed = drive(g, lambda g: "terminal" in g.alarms, 25) is True
        t_end = time.monotonic() + 2.0
        while time.monotonic() < t_end and not closed:
            closed = g.one_pass()
            time.sleep(0.1)
        ts = root / "fake" / "terminal.starts.txt"
        check(f"V10{x} the terminal writer {mode}: no CLOSED.json, the ALARM terminal ({text}), one start",
              (closed, (root / "guard" / "CLOSED.json").exists(), text in g.alarms.get("terminal", ""),
               len(ts.read_text().split()) if ts.exists() else 0), (False, False, True, 1))
        done(g)
    G.RETRY = {6: 30.0, 8: 10.0, 3: 30.0, 0: 5.0}


# ---- E ---------------------------------------------------------------------------------------------------------------
def part_e():
    if "exe" not in OPTS or "net" not in OPTS:
        print("NOT RUN E: no exe= and net= given; counted in neither")
        return
    G.RUN_DIR = REAL_RUN
    exe, net = Path(OPTS["exe"]).resolve(), Path(OPTS["net"]).resolve()
    man_path, known = TREE / "workloads" / "MANIFEST.json", TREE / "known" / "startup.json"
    man = json.loads(man_path.read_bytes())
    n12 = [ln.split()[3:] for ln in (TREE / "workloads" / "n12_batch.uci").read_text(encoding="ascii").splitlines()
           if ln.startswith("position startpos moves ")]
    openings = WORK / "n12_openings.txt"
    openings.write_bytes("".join(" ".join(o) + "\n" for o in n12).encode("ascii"))
    real = {"engine_sha256": sha(exe.read_bytes()), "net_sha256": man["net_sha256"],
            "options_sha256": sha("".join(ln + "\n" for ln in man["options"]).encode("ascii")),
            "game_line": man["selfgame_line"],
            "opening_rule": {"kind": "list", "sha256": sha(openings.read_bytes()), "count": len(n12)}}
    root, pol = make_root("ea", [0, 1], rows([0, 1], length=2), 900, lease_ago=60, piece_games=1, real=real)
    g = guard(root, pol, exe=str(exe), net=str(net), manifest=str(man_path), known_startup=str(known),
              openings=str(openings), floor_bytes=1, end_grace=60.0, tick=0.2)
    rs = root / "ranges"
    sealed = lambda *names: all((rs / n).exists() for n in names)  # noqa: E731
    ok = drive(g, lambda g: sealed("r0001.w000.seal.json", "r0001.w001.seal.json"), 240)
    true("E both pilot ranges sealed", ok, sorted(p.name for p in rs.glob("*")) if rs.is_dir() else None)
    rep = report(root, pol, "SELF_PLAY", cut_before_d=300, disp_before_cut=60)
    c1, e1 = control(root, pol, 1, rep, scope={"highest_round": 4, "target_rows": 1000})
    send(root, 1, c1, e1)
    accepted(root, 1, c1)
    ok = drive(g, lambda g: sealed(*[f"r{r:04d}.w{k:03d}.seal.json" for r in (2, 3, 4) for k in (0, 1)]), 420)
    true("E rounds 2 to 4 sealed in both slots", ok, sorted(p.name for p in rs.glob("*")) if rs.is_dir() else None)
    s1, s2 = sched(root, 1) or {}, sched(root, 2) or {}
    lease = W.utc(hdr(root)["lease_start_utc"], "l")
    cut, disp = T(lease + rep["cutoff_floor_s"]), T(lease + rep["dispatch_end_floor_s"])
    added = lambda s, n: sorted((r["slot"], r["round"], r["first"], r["last"]) for r in s.get("ranges", [])  # noqa
                                if r["schedule"] == n)
    check("E SCHEDULE.1", (s1.get("evidence"), s1.get("cutoff_utc"), s1.get("dispatch_end_utc"), added(s1, 1)),
          (sha(c1), cut, disp, [(0, 2, 3, 4), (0, 3, 5, 6), (1, 2, 3, 4), (1, 3, 5, 6)]))
    check("E SCHEDULE.2 (the rolling extension)", (s2.get("evidence"), s2.get("cutoff_utc"),
                                                   s2.get("dispatch_end_utc"), added(s2, 2)),
          (sha(c1), cut, disp, [(0, 4, 7, 8), (1, 4, 7, 8)]))
    check("E no SCHEDULE.3", sched(root, 3), None)
    seals = [json.loads((rs / f"r{r:04d}.w{k:03d}.seal.json").read_bytes()) for r in (1, 2, 3, 4) for k in (0, 1)
             if (rs / f"r{r:04d}.w{k:03d}.seal.json").exists()]
    check("E every range seal: 2 games, complete", [(s.get("games"), s.get("complete")) for s in seals],
          [(2, True)] * 8)
    cf, ef = control(root, pol, 2, {"outcome": "STOP", "why": "the test's end", "inputs": plan_in(pol)},
                     kind="fence", decision="STOP",
                     over={"cutoff_utc": cut, "dispatch_end_utc": disp})
    send(root, 2, cf, ef)
    closed = drive(g, lambda g: False, 240)
    check("E the day closed", closed, True)
    f = json.loads((root / "FENCE.json").read_bytes()) if (root / "FENCE.json").exists() else {}
    true("E FENCE.json: the D in force, why names control 2", f.get("cutoff_utc") == cut and sha(cf) in str(
        f.get("why")), f)
    lasts = []
    for k in (0, 1):
        jl = (root / f"w{k:03d}" / "journal.txt").read_bytes().splitlines()
        last = json.loads(jl[-1]) if jl else {}
        lasts.append((last.get("t"), last.get("why")))
    check("E each journal ends `ended` with why ranges done", lasts, [("ended", "ranges done")] * 2)
    log = (root / "guard" / "guard.log").read_text(encoding="ascii", errors="replace")
    codes = sorted({ln.rsplit(" ", 1)[1] for ln in log.splitlines() if " exited with " in ln and "worker" in ln})
    check("E every worker exit 0; no FAULTED, UNRECONCILED or STOP_PACKER",
          (codes, "FAULTED" in log, "UNRECONCILED" in log, (root / "STOP_PACKER").exists()), (["0"], False, False,
                                                                                            False))
    cl = json.loads((root / "guard" / "CLOSED.json").read_bytes()) if (root / "guard" / "CLOSED.json").exists() else {}
    check("E CLOSED.json", (cl.get("slots_ended"), cl.get("slots_unreconciled")), ([0, 1], []))
    tj = (root / "TERMINAL.jsonl").read_bytes() if (root / "TERMINAL.jsonl").exists() else b""
    foot = json.loads(tj.splitlines()[-1]) if tj else {}
    check("E CLOSED.json's terminal: the real inventory, 16 pieces, 2 slots ended",
          ((cl.get("terminal") or {}).get("sha256"), foot.get("pieces"), foot.get("slots")),
          (sha(tj), 16, {"ended": 2, "unreconciled": 0}))
    offers = [len(list((root / "out" / f"w{k:03d}").glob("p*.offer.json.zz"))) for k in (0, 1)]
    check("E the packer's last pass: 8 offers a slot", ("the packer made its last pass" in log, offers),
          (True, [8, 8]))
    done(g)


try:
    for part, fn in (("C", part_c), ("P", part_p), ("E", part_e)):
        if part in ONLY:
            try:
                fn()
            except Exception as e:  # noqa: BLE001   one failed check, its traceback printed, the next part runs
                traceback.print_exc()
                true(f"part {part} ended by {type(e).__name__}: {str(e)[:200]}", False)
finally:
    cleanup()
failed = [n for n, ok in RESULTS if not ok]
print(f"{len(RESULTS) - len(failed)} of {len(RESULTS)} checks pass")
print("ALL PASS" if not failed and RESULTS else f"{len(failed)} failed: {failed}")
sys.exit(0 if not failed and RESULTS else 1)
