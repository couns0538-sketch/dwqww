"""Opus 2026-11-23: the test of run/guard.py version 1 (A3a). Known answers written BEFORE the guard ran once, from
FORMATS 2.9 1.2 and 1.8, SETUP_PLAN D2 and D5, and Astra 160235Z, 161634Z, 171134Z, 171332Z, 172109Z. Standard
library only; run it with a PLAIN interpreter (it starts python processes itself).

    test_guard.py <run/guard.py> <a NEW folder> [exe=<engine> net=<net file>] [only=C,P,E] [plant1 ... plant22]

The run folder of <run/guard.py> is copied into the new folder (a plant changes the copy only) and imported from
there. C and P need nothing else; E needs the engine and its net and the tree's workloads/ and known/ (the folder
above run/); without exe= and net= it prints NOT RUN and counts in neither.

C  THE CONTROL RECORD, in-process, no process started (take_controls, extend and replay called directly). A root with
   slots 1 and 2, pilot rows of round 1 (counters 1 to 4), D = now + 2 h, the lease started 600 s ago, one sealed
   piece (4 games, 4,000 bytes; the seal keys `games` and `raw_bytes` are worker.py's, line 863), floor 0. The policy
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
       CLOSED.json slots_ended [1, 2, 3], slots_unreconciled [4], terminal null, packer "ended"; the packer started
       once and made its last pass; groups.jsonl 7 lines (6 workers, 1 packer) of this boot; hourly.jsonl's first
       line state "play"; no process of the day alive at the end.
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
   slots_ended [0, 1]; the packer's last pass with 8 offers in each slot's out folder.

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
"""
import ctypes
import hashlib
import json
import os
import shutil
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
    "plant18": ('        if self.boot == self.h["boot_id"]:\n', '        if True:\n'),
    "plant19": ('        stop = (self.root / "STOP").exists()\n', '        stop = False\n'),
    "plant20": ('                if len([t for t in s.starts if now - t < HOUR]) >= 5:\n',
                '                if False:\n'),
    "plant21": ('        return self.B.judge("cutoff", lead=-self.a.end_grace)[0] == cw.COME\n',
                '        return False\n'),
    "plant22": ('                                     or rep["inputs"].get("plan_sha256") != self.policy_sha):\n',
                '                                     or False):\n'),
    "plant23": ('                    raise Held(f"the owed schedule: {why}")\n', '                    pass\n'),
    "plant24": ('            if not fenced and st != "cutoff" and self.pending is None:\n',
                '            if not fenced and st != "cutoff":\n'),
    "plant25": ('            if self.lock_held(self.root / f"w{s.k:03d}"):', '            if False:'),
    "plant26": ('        if self.lock_held(self.root / "out"):', '        if False:'),
    "plant27": ('                if end and self.past_d_grace():', '                if False:'),
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


def seal_piece(root, slot, i, games=4, raw=4000):
    d = root / f"w{slot:03d}" / "closed"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"p{i:06d}.seal.json").write_bytes(W.canon({"games": games, "raw_bytes": raw, "rows": 100, "schema": 2}))


def seal_range(root, rnd, slot):
    d = root / "ranges"
    d.mkdir(exist_ok=True)
    (d / f"r{rnd:04d}.w{slot:03d}.seal.json").write_bytes(W.canon({"games": 2, "schema": 2}))


def sched(root, n):
    p = root / f"SCHEDULE.{n}.json"
    return json.loads(p.read_bytes()) if p.exists() else None


def held(g, text):
    return text in g.alarms.get("control", "")


def alive(pid):
    pid = int(pid)
    if os.name == "nt":
        k = ctypes.WinDLL("kernel32", use_last_error=True)
        k.OpenProcess.restype = ctypes.c_void_p
        h = k.OpenProcess(0x1000, False, pid)
        if not h:
            return False
        code = ctypes.c_ulong()
        ok = k.GetExitCodeProcess(ctypes.c_void_p(h), ctypes.byref(code))
        k.CloseHandle(ctypes.c_void_p(h))
        return bool(ok) and code.value == 259
    try:
        with open(f"/proc/{pid}/stat", "rb") as f:
            s = f.read()
        return s[s.rfind(b")") + 2:].split()[0] != b"Z"
    except OSError:
        return False


def kill(pid):
    if not alive(pid):
        return
    if os.name == "nt":
        k = ctypes.WinDLL("kernel32", use_last_error=True)
        k.OpenProcess.restype = ctypes.c_void_p
        h = k.OpenProcess(0x0001, False, int(pid))
        if h:
            k.TerminateProcess(ctypes.c_void_p(h), 1)
            k.CloseHandle(ctypes.c_void_p(h))
    else:
        os.kill(int(pid), 9)


def cleanup():
    for g in LIVE:
        for grp in [s.g for s in g.slots.values()] + [g.packer]:
            if grp is not None and not grp.done:
                try:
                    grp.end_and_verify(2.0)
                    grp.reap()
                except Exception:  # noqa: BLE001
                    pass
    for f in WORK.glob("*/fake/orphan.*.pid"):
        kill(f.read_text())
    for f in WORK.glob("*/fake/starts.*.txt"):
        for ln in f.read_text().splitlines():
            kill(json.loads(ln)["pid"])


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
(FAKE / "worker.py").write_text('''import json, os, subprocess, sys, time
from pathlib import Path
a = sys.argv[1:]
root = Path(a[a.index("--root") + 1]); slot = int(a[a.index("--slot") + 1]); fk = root / "fake"
plan = json.loads((fk / f"plan.{slot}.json").read_text())
log = fk / f"starts.{slot}.txt"
n = len(log.read_text().splitlines()) if log.exists() else 0
with open(log, "a") as f:
    f.write(json.dumps({"n": n, "t": time.time(), "fence": (root / "FENCE.json").exists(), "pid": os.getpid()}) + "\\n")
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
def ended():
    d = root / ("w%03d" % slot); d.mkdir(exist_ok=True)
    with open(d / "journal.txt", "ab") as f:
        f.write(b'{"t":"ended","why":"test"}\\n')
if act == "ended":
    ended(); sys.exit(0)
if act.startswith("exit:"):
    sys.exit(int(act[5:]))
if act.startswith("sleep:"):
    time.sleep(float(act[6:])); ended(); sys.exit(0)
if act == "orphan":
    c = subprocess.Popen([sys.executable, "-I", "-B", "-c", "import time; time.sleep(120)"])
    (fk / f"orphan.{slot}.pid").write_text(str(c.pid)); ended(); sys.exit(0)
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
    return p.exists() and p.read_bytes().splitlines()[-1:] == [b'{"t":"ended","why":"test"}']
t_end = time.time() + 120
while time.time() < t_end:
    if (fk / "END").exists():
        sys.exit(0)
    if (root / "STOP_PACKER").exists() or ((root / "FENCE.json").exists() and all(ended(k) for k in slots)):
        (fk / "packer.final").write_text("%f" % time.time()); sys.exit(0)
    time.sleep(0.1)
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
    cf, evf = control(root, pol, 2, {"outcome": "STOP", "why": "the owner's word"}, kind="fence", decision="STOP")
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
    (root / "w001" / "journal.txt").write_bytes(b'{"t":"ended","why":"test"}\n')
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
    (root / "w001" / "journal.txt").write_bytes(b'{"t":"ended","why":"test"}\n')
    (root / "fake").mkdir()
    cb, evb = control(root, pol, 1, report(root, pol, "SELF_PLAY"), scope={"highest_round": 9, "target_rows": 9})
    (root / "control").mkdir()
    (root / "control" / f"EVIDENCE.{sha(evb)}.json").write_bytes(evb)
    (root / "control" / "CONTROL.1.json").write_bytes(cb)
    accepted(root, 1, cb)
    cf, evf = control(root, pol, 2, {"outcome": "STOP", "why": "the owner's word"}, kind="fence", decision="STOP")
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


# ---- P ---------------------------------------------------------------------------------------------------------------
def part_p():
    G.RUN_DIR = FAKE
    G.RETRY = {6: 0.5, 8: 0.5, 3: 0.5, 0: 0.5}
    root, pol = fake_root("pa", [1, 2, 3, 4], {1: ["sleep:1"], 2: ["exit:4", "ended"], 3: ["orphan"],
                                               4: ["exit:6", "hang"]}, 8)
    g = guard(root, pol)
    seen = {}
    faulted2 = []

    def each(g):
        if g.slots[2].faulted and not (root / "FENCE.json").exists():
            faulted2.append(True)
        pid = root / "fake" / "orphan.3.pid"
        if "orphan" not in seen and g.slots[3].g is None and g.slots[3].ended and pid.exists():
            seen["orphan"] = alive(pid.read_text())

    closed = drive(g, lambda g: False, 60, each)
    check("PA the day closed", closed, True)
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
    check("PA CLOSED.json", (cl.get("slots_ended"), cl.get("slots_unreconciled"), cl.get("terminal"),
                             cl.get("packer")), ([1, 2, 3], [4], None, "ended"))
    ps = (root / "fake" / "packer.starts.txt")
    check("PA the packer: one start, its last pass",
          (len(ps.read_text().splitlines()) if ps.exists() else 0, (root / "fake" / "packer.final").exists()),
          (1, True))
    gl = (root / "guard" / "groups.jsonl").read_bytes().splitlines() if (root / "guard" / "groups.jsonl").exists() \
        else []
    kinds = sorted(json.loads(x)["kind"] for x in gl)
    check("PA groups.jsonl", (kinds, all(json.loads(x)["boot_id"] == BOOT for x in gl)),
          (["packer"] + ["worker"] * 6, True))
    hl = (root / "guard" / "hourly.jsonl").read_bytes().splitlines() if (root / "guard" / "hourly.jsonl").exists() \
        else []
    first = json.loads(hl[0]) if hl else {}
    check("PA hourly.jsonl first line", (first.get("t"), first.get("state"), first.get("schedules"),
                                         first.get("controls")), ("hour", "play", 0, 0))
    pids = [x["pid"] for k in (1, 2, 3, 4) for x in starts(root, k)]
    op = root / "fake" / "orphan.3.pid"
    if op.exists():
        pids.append(int(op.read_text()))
    check("PA no process of the day alive", [p for p in pids if alive(p)], [])
    done(g)

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
    (root / "RESUME.1.json").write_bytes(W.canon({"new_boot_id": BOOT, "old_boot_id": "another-boot",
                                                  "run_fingerprint": sha((root / "RUN.json").read_bytes()),
                                                  "schema": 2}))
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
    cf, ef = control(root, pol, 2, {"outcome": "STOP", "why": "the test's end"}, kind="fence", decision="STOP",
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
