"""test_make_control.py: tools/make_control.py (A3e) against known answers written BEFORE it ran
(tmp/opus_scratch/control/KNOWN_ANSWERS_by_opus.md on the PC; FORMATS 0 and 1.2; the guard's G3; the hand numbers of
test_budget.py's BASE). Standard library only; a PLAIN interpreter (it starts python processes itself).

    test_make_control.py <tools/make_control.py> <a NEW folder> [plantN]

The REAL budget tool (tools/budget.py beside it) makes every report, and the REAL server guard (run/guard.py of the
same package, in-process: no worker is started) takes every control the tool made. make_control.py is copied into
the new folder; a plant changes that copy only.
A  the chain on one root: M (SELF_PLAY_AND_MATCHES, k 1, pilot_decision) -> the guard's SCHEDULE.1; M2 (k 2, kind
   matches, from home's copy of the server's control/ folder); R (REACHED, k 3, kind target) -> FENCE.json.
B  fresh roots, k 1: S (SELF_PLAY), O (OWNER_CHOICE, reduced target covered), O-stop, O-uncovered with
   if_uncovered self_play, STOP, U (UNQUALIFIED), SHORT, LOCAL (local_only in the full output only), a report
   without a pilot as kind fence.
R  refusals (exit 4, nothing written) and arguments (exit 2).
O  the order of the four files (in-process) and the .zz files.
PLANTS: see PLANTS below (each must make the test fail).
"""
import hashlib
import json
import shutil
import subprocess
import sys
import time
import traceback
import zlib
from pathlib import Path
from types import SimpleNamespace

if len(sys.argv) < 3:
    print("usage: test_make_control.py <tools/make_control.py> <a NEW folder> [plantN]")
    sys.exit(2)
MC_SRC, WORK = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
PLANT = sys.argv[3] if len(sys.argv) > 3 else None
TOOLS, RUN = MC_SRC.parent, MC_SRC.parent.parent / "run"
if WORK.exists():
    print(f"STOP: {WORK} exists already (a NEW folder)")
    sys.exit(2)
WORK.mkdir(parents=True)
PLANTS = {
    "plant1": ('        if not whole(rep.get(k)):\n',
               '        rep[k] = int(rep[k]) if isinstance(rep.get(k), float) else rep.get(k)\n'
               '        if not whole(rep.get(k)):\n'),
    "plant2": ('"reason": rep["reason"], "reduced": reduced, "schema": 2}',
               '"reason": rep["reason"], "reduced": reduced, "schema": 2, '
               '**({"local_only": rep["local_only"]} if "local_only" in rep else {})}'),
    "plant3": ("matches = [m[:3] for m in rows]", "matches = [m[:4] for m in rows]"),
    "plant4": ("        cut, disp = cut_in, disp_in\n",
               '        cut = lease + ev["cutoff_floor_s"]\n'
               '        disp = lease + (ev["dispatch_end_floor_s"] or ev["cutoff_floor_s"])\n'),
    "plant5": ('target = cap if cap is not None else policy.get("target_rows")', 'target = policy.get("target_rows")'),
    "plant6": ('"owner_policy": psha, "prev": prev,', '"owner_policy": psha, "prev": "first",'),
    "plant7": ('        if ev["inputs"]["pilot_sha256"] is None:\n', '        if False:\n'),
    "plant8": ('    create_only(out / f"EVIDENCE.{sha(evb)}.json", evb)\n'
               '    create_only(out / f"EVIDENCE.{sha(evb)}.json.zz", zlib.compress(evb, 6))\n'
               '    create_only(out / f"CONTROL.{k}.json", cb)\n'
               '    create_only(out / f"CONTROL.{k}.json.zz", zlib.compress(cb, 6))\n',
               '    create_only(out / f"CONTROL.{k}.json", cb)\n'
               '    create_only(out / f"CONTROL.{k}.json.zz", zlib.compress(cb, 6))\n'
               '    create_only(out / f"EVIDENCE.{sha(evb)}.json", evb)\n'
               '    create_only(out / f"EVIDENCE.{sha(evb)}.json.zz", zlib.compress(evb, 6))\n'),
    "plant9": ('        if ev["inputs"]["plan_sha256"] != psha:\n', '        if False:\n'),
    "plant10": ("        if cut > cut_in or disp > disp_in or disp > cut:\n", "        if disp > cut:\n"),
    "plant11": ('    if reduced["covered"] or oc.get("if_uncovered") == "self_play":\n', "    if True:\n"),
    "plant12": ("    if nums != list(range(1, len(nums) + 1)):\n", "    if False:\n"),
    "plant13": ('    ev["report_sha256"] = sha(report)\n', '    ev["report_sha256"] = sha(canon(strict(report, "r")))\n'),
}
text = MC_SRC.read_bytes().decode("ascii")
if PLANT:
    if PLANT not in PLANTS or text.count(PLANTS[PLANT][0]) != 1:
        print(f"STOP: {PLANT}: no such plant, or its text does not stand exactly once")
        sys.exit(2)
    text = text.replace(*PLANTS[PLANT])
    print(f"PLANT {PLANT} applied to the copy")
MC_DIR = WORK / "mc"
MC_DIR.mkdir()
MC = MC_DIR / "make_control.py"
MC.write_bytes(text.encode("ascii"))
sys.path.insert(0, str(RUN))
import guard as G  # noqa: E402
import worker as W  # noqa: E402
sys.path.insert(0, str(MC_DIR))
import make_control as MCM  # noqa: E402

RESULTS = []


def check(name, got, want):
    ok = got == want
    RESULTS.append((name, ok))
    print(f"{'PASS' if ok else 'FAIL'} {name}: got {str(got)[:300]}" + ("" if ok else f"; want {str(want)[:300]}"),
          flush=True)
    return ok


def safe(name, fn):
    try:
        fn()
    except Exception:  # noqa: BLE001   a crash inside a part is one FAIL, and the other parts still run
        check(f"{name} ran to its end", traceback.format_exc()[-600:], "no exception")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def T(t):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(t)))


# ---- the budget tool's inputs: test_budget.py's BASE ---------------------------------------------------------------
PLAN = {"target_rows": 2000000000, "lease_end_s": 90000, "closing_s": 1800, "game_margin_s": 300,
        "pilot_rounds_declared": 1, "floor_fraction": 0.5, "match_margin": 1.10,
        "owner_choice": {"name": "reduced target", "reduced_target_rows": 1546400000, "action": "reduced_target",
                         "if_uncovered": "stop"},
        "match_queue": [["a", 2000], ["b", 2000], ["big", 100000], ["c", 2000]]}
STATE = {"now_s": 7200, "c4_rows": 34400000}
PILOT = {"rounds_whole": 1, "queues_empty_at_start": True, "carry_in_rows": 0, "cohort_games": 125000,
         "cohort_raw_rows": 16000000, "cohort_c4_rows": 15200000, "cohort_seconds": 500, "games_per_h": 2000000,
         "c1_raw_rows_per_s": 100000, "c2_raw_rows_per_s": 100000, "c3_games_per_s": 1000,
         "c4_kept_rows_per_s": 90000, "longest_game_s": 300, "match_games_per_h": 12000}
RAW = WORK / "raw_measurements.txt"
RAW.write_bytes(b"stand-in raw file: every measured input of these cases names it\n")
SRC = {"path": str(RAW), "sha256": sha(RAW.read_bytes())}
NEEDS = {"plan": ("lease_end_s", "closing_s"), "state": ("c4_rows",), "pilot": tuple(PILOT)}
GONE = WORK / "gone_raw_file.txt"


def budget(name, plan=PLAN, state=STATE, pilot=PILOT):
    """The real budget tool on these inputs: (report path, {kind: input path})."""
    paths = {}
    for kind, obj in (("plan", plan), ("state", state), ("pilot", pilot)):
        if obj is None:
            continue
        o = obj if "sources" in obj else dict(obj, sources={k: SRC for k in NEEDS[kind]})
        paths[kind] = WORK / f"{name}.{kind}.json"
        paths[kind].write_text(json.dumps(o), encoding="ascii")
    r = subprocess.run([sys.executable, "-I", "-B", str(TOOLS / "budget.py"),
                        *[str(paths[k]) for k in ("plan", "state", "pilot") if k in paths]], capture_output=True)
    rp = WORK / f"{name}.report.json"
    rp.write_bytes(r.stdout)
    return rp, paths


# ---- the day: header, roots, the real guard -----------------------------------------------------------------------
L = int(time.time()) // 60 * 60 - 600
PILOT_ROWS = [{"first": 1, "last": 4, "round": 1, "schedule": 0, "short": False, "slot": k} for k in (1, 2)]


def header(lease_end=90000, hard=82800):
    return W.canon({"schema": 2, "run": "mc", "lease_start_utc": T(L), "lease_end_utc": T(L + lease_end),
                    "hard_cutoff_utc": T(L + hard), "boot_id": W.boot_id(), "instance": "test-instance",
                    "package": "0" * 64, "engine_sha256": "1" * 64, "net_sha256": "2" * 64,
                    "options_sha256": "3" * 64, "game_line": "go nodes 1",
                    "opening_rule": {"kind": "seed", "plies": 8, "root_seed": "s"}, "slots": [1, 2], "piece_games": 4,
                    "pilot_ranges": PILOT_ROWS})


HB = header()
EMPTY = WORK / "accepted_empty"
EMPTY.mkdir()


def make_root(name, hb=HB):
    """A day's root with one sealed piece of slot 1: the guard's room test (G5) measures a game's bytes from it."""
    root = WORK / name
    root.mkdir()
    (root / "RUN.json").write_bytes(hb)
    (root / "w001" / "closed").mkdir(parents=True)
    (root / "w001" / "closed" / "p000000.seal.json").write_bytes(
        W.canon({"games": 4, "raw_bytes": 4000, "rows": 100, "schema": 2}))
    return root


def guard(root, pol):
    a = SimpleNamespace(root=str(root), exe=str(WORK / "no_engine.exe"), net="n", manifest="m", known_startup="k",
                        converter=str(WORK / "no_converter"), policy=str(pol), floor_bytes=0, openings="",
                        game_seconds=600.0, horizon=2, tick=0.1, allowance=2.0, end_grace=2.0, python=sys.executable)
    g = G.Guard(a)
    g.replay_controls()
    return g


def done(g):
    g.lock.release()
    g.log.close()


def mk(report, root, pol, acc, kind, out):
    """The tool as a process: (exit code, its output)."""
    r = subprocess.run([sys.executable, "-I", "-B", str(MC), "--report", str(report), "--header",
                        str(root / "RUN.json"), "--policy", str(pol), "--accepted", str(acc), "--kind", kind, "--out",
                        str(out)], capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def send(out, root):
    """Home's upload: the evidence first, the control last."""
    inbox = root / "inbox"
    inbox.mkdir(exist_ok=True)
    for p in sorted(out.glob("EVIDENCE.*.json.zz")) + sorted(out.glob("CONTROL.*.json.zz")):
        shutil.copyfile(p, inbox / p.name)


def made(out, k):
    """(control bytes, control record, evidence bytes) the tool wrote, or Nones."""
    cp = out / f"CONTROL.{k}.json"
    if not cp.exists():
        return None, {}, None
    cb = cp.read_bytes()
    c = json.loads(cb)
    ep = out / f"EVIDENCE.{c.get('evidence')}.json"
    return cb, c, ep.read_bytes() if ep.exists() else None


def pub(rp, paths, outcome, reason, c4, deficit, disp, matches, reduced, cut=82800, pilot=True):
    """The public record by hand (FORMATS 0 canonical): the report's own values, the shas of the exact bytes."""
    return W.canon({"c4_rows": c4, "cutoff_floor_s": cut, "deficit_rows": deficit, "dispatch_end_floor_s": disp,
                    "inputs": {"pilot_sha256": sha(paths["pilot"].read_bytes()) if pilot else None,
                               "plan_sha256": sha(paths["plan"].read_bytes()),
                               "state_sha256": sha(paths["state"].read_bytes())},
                    "matches": matches, "outcome": outcome, "reason": reason, "reduced": reduced,
                    "report_sha256": sha(rp.read_bytes()), "schema": 2})


def ctl(c, t0, t1, **want):
    """The control record against the known fields; at_utc must lie inside the tool's run."""
    at = c.get("at_utc", "")
    ok_at = isinstance(at, str) and T(t0) <= at <= T(t1)
    return ok_at, {k: c.get(k) for k in want}, want


def control_case(name, rp, paths, root, acc, tool_kind, out, ev_want, **want):
    t0 = time.time()
    rc, txt = mk(rp, root, paths["plan"], acc, tool_kind, out)
    t1 = time.time() + 1
    check(f"{name} exit 0", (rc, txt[:160] if rc else ""), (0, ""))
    k = want.get("k", 1)
    cb, c, evb = made(out, k)
    check(f"{name} the public record, byte for byte", evb, ev_want)
    ok_at, got, w = ctl(c, t0, t1, **want)
    check(f"{name} CONTROL.{k}.json: the known fields", got, w)
    check(f"{name} at_utc inside the run, canonical bytes, evidence = sha256(public record)",
          (ok_at, cb == W.canon(c) if cb else None, c.get("evidence") == (sha(evb) if evb else None)), (True, True, True))
    check(f"{name} exactly the four files", sorted(p.name for p in out.iterdir()) if out.exists() else None,
          sorted([f"EVIDENCE.{c.get('evidence')}.json", f"EVIDENCE.{c.get('evidence')}.json.zz", f"CONTROL.{k}.json",
                  f"CONTROL.{k}.json.zz"]))
    return cb, evb


SC = {"highest_round": 9999, "target_rows": 2000000000}
R_M = "r > match_margin x n: the declared queue takes the spare above the margin in complete pairs"
R_R = "C4 holds the target: no row needed; the match queue may use the time left before the dispatch end"
M3 = [["a", 2000, 2000], ["b", 2000, 2000], ["big", 100000, 10920]]
M4 = [["a", 2000, 2000], ["b", 2000, 2000], ["big", 100000, 100000], ["c", 2000, 2000]]
HARD = T(L + 82800)


def part_a():
    rp, paths = budget("M")
    root = make_root("root_a")
    g = guard(root, paths["plan"])
    try:
        cb1, evb = control_case(
            "A1 M", rp, paths, root, EMPTY, "pilot_decision", WORK / "out_m",
            pub(rp, paths, "SELF_PLAY_AND_MATCHES", R_M, 34400000, 1965600000, 82200, M3, None),
            k=1, kind="pilot_decision", prev="first", decision="SELF_PLAY_AND_MATCHES", scope=SC,
            cutoff_utc=T(L + 82800), dispatch_end_utc=T(L + 82200), owner_policy=sha(paths["plan"].read_bytes()),
            run_fingerprint=sha(HB), schema=2)
        send(WORK / "out_m", root)
        g.take_controls()
        s1 = json.loads((root / "SCHEDULE.1.json").read_bytes()) if (root / "SCHEDULE.1.json").exists() else {}
        check("A1 the guard accepted it: control/CONTROL.1.json = the tool's bytes, the evidence beside it",
              ((root / "control" / "CONTROL.1.json").read_bytes() == cb1 if cb1 and (
                  root / "control" / "CONTROL.1.json").exists() else g.alarms.get("control"),
               (root / "control" / f"EVIDENCE.{sha(evb or b'')}.json").exists()), (True, True))
        check("A1 SCHEDULE.1 carries the control's bounds and names it as evidence",
              {k: s1.get(k) for k in ("n", "prev", "evidence", "cutoff_utc", "dispatch_end_utc")},
              {"n": 1, "prev": "first", "evidence": sha(cb1 or b""), "cutoff_utc": T(L + 82800),
               "dispatch_end_utc": T(L + 82200)})
        check("A1 the guard's alarm: matches assigned, no match runner", "matches1" in g.alarms, True)
        acc1 = WORK / "accepted_after_1"
        shutil.copytree(root / "control", acc1)
        cb2, _ = control_case(
            "A2 M2", rp, paths, root, acc1, "matches", WORK / "out_m2",
            pub(rp, paths, "SELF_PLAY_AND_MATCHES", R_M, 34400000, 1965600000, 82200, M3, None),
            k=2, kind="matches", prev=sha(cb1 or b""), decision=M3, scope=None, cutoff_utc=T(L + 82800),
            dispatch_end_utc=T(L + 82200))
        send(WORK / "out_m2", root)
        g.take_controls()
        check("A2 the guard accepted it, no SCHEDULE.2, its matches alarm",
              ((root / "control" / "CONTROL.2.json").exists() and (root / "control" / "CONTROL.2.json").read_bytes()
               == cb2, (root / "SCHEDULE.2.json").exists(), "matches2" in g.alarms, g.alarms.get("control")),
              (True, False, True, None))
        rp_r, paths_r = budget("R", state=dict(STATE, c4_rows=2000000000))
        acc2 = WORK / "accepted_after_2"
        shutil.copytree(root / "control", acc2)
        cb3, _ = control_case(
            "A3 R", rp_r, paths_r, root, acc2, "target", WORK / "out_r",
            pub(rp_r, paths_r, "REACHED", R_R, 2000000000, 0, 82200, M4, None),
            k=3, kind="target", prev=sha(cb2 or b""), decision="REACHED", scope=None, cutoff_utc=T(L + 82800),
            dispatch_end_utc=T(L + 82200))
        send(WORK / "out_r", root)
        g.take_controls()
        f = json.loads((root / "FENCE.json").read_bytes()) if (root / "FENCE.json").exists() else {}
        check("A3 the guard accepted it and wrote FENCE.json naming CONTROL.3's sha256",
              ((root / "control" / "CONTROL.3.json").exists(), sha(cb3 or b"x") in str(f.get("why"))), (True, True))
    finally:
        done(g)


def fresh(name, rp, paths, kind, ev_want, guard_sees, **want):
    """A fresh root, k 1: the tool's control, then the guard's verdict (schedule, fence, none or held)."""
    root = make_root(f"root_{name}")
    out = WORK / f"out_{name}"
    cb, _ = control_case(name, rp, paths, root, EMPTY, kind, out, ev_want, k=1, kind=kind, prev="first", **want)
    g = guard(root, paths["plan"])
    try:
        send(out, root)
        g.take_controls()
        seen = ("held: " + g.alarms["control"]) if "control" in g.alarms else (
            "schedule" if (root / "SCHEDULE.1.json").exists() else "fence" if (root / "FENCE.json").exists()
            else "none" if (root / "control" / "CONTROL.1.json").exists() else "nothing")
        check(f"{name} the guard: {guard_sees}", seen, guard_sees)
    finally:
        done(g)
    return cb


def part_b():
    rp, paths = budget("S", pilot=dict(PILOT, cohort_seconds=560))
    fresh("B1_S", rp, paths, "pilot_decision",
          pub(rp, paths, "SELF_PLAY", "n <= r <= match_margin x n: self-play only", 34400000, 1965600000, 82200, [],
              None), "schedule", decision="SELF_PLAY", scope=SC, cutoff_utc=T(L + 82800),
          dispatch_end_utc=T(L + 82200))
    R_O = "floor <= r < n: the owner's predeclared choice, no improvising"
    rp, paths = budget("O", pilot=dict(PILOT, cohort_seconds=760))
    fresh("B2_O", rp, paths, "pilot_decision",
          pub(rp, paths, "OWNER_CHOICE", R_O, 34400000, 1965600000, 82200, [],
              {"covered": True, "target_rows": 1546400000}), "schedule", decision="OWNER_CHOICE",
          scope={"highest_round": 9999, "target_rows": 1546400000}, cutoff_utc=T(L + 82800),
          dispatch_end_utc=T(L + 82200))
    oc_stop = {"name": "stop", "reduced_target_rows": 1546400000, "action": "stop"}
    rp, paths = budget("O_stop", plan=dict(PLAN, owner_choice=oc_stop), pilot=dict(PILOT, cohort_seconds=760))
    fresh("B3_O_stop", rp, paths, "pilot_decision",
          pub(rp, paths, "OWNER_CHOICE", R_O, 34400000, 1965600000, 82200, [],
              {"covered": True, "target_rows": 1546400000}), "fence", decision="OWNER_CHOICE", scope=None,
          cutoff_utc=HARD, dispatch_end_utc=HARD)
    oc_unc = {"name": "uncovered", "reduced_target_rows": 1600000000, "action": "reduced_target",
              "if_uncovered": "self_play"}
    rp, paths = budget("O_unc", plan=dict(PLAN, owner_choice=oc_unc), pilot=dict(PILOT, cohort_seconds=760))
    fresh("B4_O_uncovered", rp, paths, "pilot_decision",
          pub(rp, paths, "OWNER_CHOICE", R_O, 34400000, 1965600000, 82200, [],
              {"covered": False, "target_rows": 1600000000}), "schedule", decision="OWNER_CHOICE",
          scope={"highest_round": 9999, "target_rows": 1600000000}, cutoff_utc=T(L + 82800),
          dispatch_end_utc=T(L + 82200))
    rp, paths = budget("STOP", pilot=dict(PILOT, cohort_seconds=1520))
    fresh("B5_STOP", rp, paths, "pilot_decision",
          pub(rp, paths, "STOP", "r is under the floor: stop in the first hour so the machine can be given back; no "
              "self-play and no match is authorized", 34400000, 1965600000, 82200, [], None), "fence",
          decision="STOP", scope=None, cutoff_utc=HARD, dispatch_end_utc=HARD)
    rp, paths = budget("U", pilot=dict(PILOT, rounds_whole=0))
    fresh("B6_U", rp, paths, "pilot_decision",
          pub(rp, paths, "UNQUALIFIED", "D3: 0 of 1 declared rounds reached durable C4 whole; nothing starts by script",
              34400000, 1965600000, 82200, None, None), "none", decision="UNQUALIFIED", scope=None,
          cutoff_utc=HARD, dispatch_end_utc=HARD)
    rp, paths = budget("SHORT", state=dict(STATE, now_s=82800))
    fresh("B7_SHORT", rp, paths, "target",
          pub(rp, paths, "SHORT", "time used up with 1965600000 C4 rows outstanding", 34400000, 1965600000, 82200,
              None, None), "fence", decision="SHORT", scope=None, cutoff_utc=HARD, dispatch_end_utc=HARD)
    st = dict(STATE, sources={"c4_rows": {"path": str(GONE), "sha256": "0" * 64}})
    rp, paths = budget("LOCAL", state=st)
    full = rp.read_bytes()
    check("B8 LOCAL the instrument: the full output carries local_only and the raw file's name",
          (b"local_only" in full, GONE.name.encode() in full), (True, True))
    fresh("B8_LOCAL", rp, paths, "pilot_decision",
          pub(rp, paths, "UNQUALIFIED", "failure row 3: state.c4_rows: raw file missing; nothing starts by script",
              34400000, 1965600000, 82200, None, None), "none", decision="UNQUALIFIED", scope=None,
          cutoff_utc=HARD, dispatch_end_utc=HARD)
    evb = made(WORK / "out_B8_LOCAL", 1)[2] or b""
    check("B8 LOCAL the public record names no local_only, no raw file, no folder of this machine",
          (b"local_only" in evb, GONE.name.encode() in evb, WORK.name.encode() in evb), (False, False, False))
    rp, paths = budget("NP", pilot=None)
    fresh("B9_no_pilot_fence", rp, paths, "fence",
          pub(rp, paths, "UNQUALIFIED", "D3: no pilot record; nothing starts by script", 34400000, 1965600000, None,
              None, None, pilot=False), "fence", decision="UNQUALIFIED", scope=None, cutoff_utc=HARD,
          dispatch_end_utc=HARD)


def refused(name, rp, pol, kind, acc=None, hb=HB, want_rc=4, out_exists=False):
    root = make_root(f"root_{name.split()[0]}", hb)     # the case's number alone names its folders
    out = WORK / f"out_{name.split()[0]}"
    if out_exists:
        out.mkdir()
    rc, txt = mk(rp, root, pol, acc or EMPTY, kind, out)
    check(f"{name} exit {want_rc}, nothing written", (rc, out.exists() and any(out.iterdir())), (want_rc, False))
    check(f"{name}: the refusal names its own cause", (WHY[name.split()[0]] in txt, txt[-160:]),
          (True, txt[-160:]))
    return txt


WHY = {"R1": "inputs.plan_sha256", "R2": "not a budget decision", "R3": "c4_rows is not a whole number",
       "R4": "matches are not rows", "R5": "names no if_uncovered", "R6": "action pause is not",
       "R7": "names no pilot report", "R8": "assigns no matches", "R9": "stands twice", "R10a": "are not exactly 1 to",
       "R10b": "prev does not link", "R10c": "another run's fingerprint", "R10d": "not a canonical record",
       "R11": "a bound later than the one in force", "R12": "invalid choice", "R13": "exists (a NEW folder)",
       "R14": "does not exist"}


def part_r():
    rp, paths = budget("M_r")
    _, p_stop = budget("O_stop_r", plan=dict(PLAN, owner_choice={"name": "s", "action": "stop"}))
    refused("R1 the report of another policy file", rp, p_stop["plan"], "pilot_decision")
    rp_e, p_e = budget("ERR", plan=dict(PLAN, target_rows=-1))
    check("R2 the instrument: the budget tool's error output", b'"error"' in rp_e.read_bytes(), True)
    refused("R2 the budget tool's error output", rp_e, p_e["plan"], "pilot_decision")
    rep = json.loads(rp.read_bytes())
    for nm, edit in (("R3 c4_rows written 34400000.0", lambda d: d.update(c4_rows=34400000.0)),
                     ("R4 a match's games written 2000.0", lambda d: d["matches"][0].__setitem__(1, 2000.0))):
        d = json.loads(json.dumps(rep))
        edit(d)
        bad = WORK / f"{nm[:2]}.report.json"
        bad.write_text(json.dumps(d), encoding="ascii")
        refused(nm, bad, paths["plan"], "pilot_decision")
    oc_none = {"name": "uncovered", "reduced_target_rows": 1600000000, "action": "reduced_target"}
    rp5, p5 = budget("O_unc_none", plan=dict(PLAN, owner_choice=oc_none), pilot=dict(PILOT, cohort_seconds=760))
    refused("R5 an uncovered reduced target, no if_uncovered", rp5, p5["plan"], "pilot_decision")
    rp6, p6 = budget("O_pause", plan=dict(PLAN, owner_choice={"name": "p", "action": "pause"}),
                     pilot=dict(PILOT, cohort_seconds=760))
    refused("R6 the policy's action pause", rp6, p6["plan"], "pilot_decision")
    rp7, p7 = budget("NP_r", pilot=None)
    refused("R7 kind pilot_decision on a report without a pilot", rp7, p7["plan"], "pilot_decision")
    rp8, p8 = budget("U_r", pilot=dict(PILOT, rounds_whole=0))
    refused("R8 kind matches on a report without matches", rp8, p8["plan"], "matches")
    twice = WORK / "R9.report.json"
    twice.write_bytes(b'{"outcome": "STOP", ' + rp.read_bytes()[1:])
    refused("R9 a key twice in the report", twice, paths["plan"], "pilot_decision")
    # the accepted chain: a control 1 made by the tool on a fresh root, then damaged copies of the folder
    root = make_root("root_chain")
    rc, _ = mk(rp, root, paths["plan"], EMPTY, "pilot_decision", WORK / "out_chain1")
    cb1 = (WORK / "out_chain1" / "CONTROL.1.json").read_bytes() if rc == 0 else b"{}\n"
    c1 = json.loads(cb1)

    def folder(name, files):
        f = WORK / name
        f.mkdir()
        for n, b in files.items():
            (f / n).write_bytes(b)
        return f
    c3 = W.canon(dict(c1, k=3, prev=sha(cb1)))
    refused("R10a a gap: CONTROL.1 and CONTROL.3", rp, paths["plan"], "target",
            acc=folder("acc_gap", {"CONTROL.1.json": cb1, "CONTROL.3.json": c3}))
    refused("R10b CONTROL.2's prev does not link", rp, paths["plan"], "target",
            acc=folder("acc_prev", {"CONTROL.1.json": cb1, "CONTROL.2.json": W.canon(dict(c1, k=2, prev="0" * 64))}))
    refused("R10c CONTROL.1 of another run", rp, paths["plan"], "target",
            acc=folder("acc_run", {"CONTROL.1.json": W.canon(dict(c1, run_fingerprint="f" * 64))}))
    refused("R10d CONTROL.1 not canonical", rp, paths["plan"], "target",
            acc=folder("acc_canon", {"CONTROL.1.json": b"{ " + cb1[1:]}))
    rc, _ = mk(rp, make_root("root_chain_ok"), paths["plan"], folder("acc_ok", {"CONTROL.1.json": cb1}), "target",
               WORK / "out_chain_ok")
    check("R10 the control: the same folder undamaged gives k 2", (rc, (WORK / "out_chain_ok" / "CONTROL.2.json")
                                                                   .exists()), (0, True))
    refused("R11 a schedule later than the hard cutoff (lease end L + 84,600)", rp, paths["plan"], "pilot_decision",
            hb=header(lease_end=84600, hard=81000))
    refused("R12 kind pause", rp, paths["plan"], "pause", want_rc=2)
    refused("R13 the out folder exists", rp, paths["plan"], "pilot_decision", want_rc=2, out_exists=True)
    refused("R14 the accepted folder missing", rp, paths["plan"], "pilot_decision", acc=WORK / "no_such_folder",
            want_rc=2)


def part_o():
    rp, paths = budget("M_o")
    rec, orig = [], MCM.create_only

    def recorder(path, data):
        rec.append(path.name)
        orig(path, data)
    MCM.create_only = recorder
    try:
        MCM.make(SimpleNamespace(report=str(rp), header=str(make_root("root_order") / "RUN.json"),
                                 policy=str(paths["plan"]), accepted=str(EMPTY), kind="pilot_decision",
                                 out=str(WORK / "out_order")))
    finally:
        MCM.create_only = orig
    ev = [n for n in rec if n.startswith("EVIDENCE.") and n.endswith(".json")]
    check("O1 the order: evidence, evidence.zz, control, control.zz",
          rec, [ev[0] if ev else "EVIDENCE.?.json", (ev[0] if ev else "EVIDENCE.?.json") + ".zz", "CONTROL.1.json",
                "CONTROL.1.json.zz"])
    out = WORK / "out_order"
    check("O2 every .zz decodes to its plain file",
          [zlib.decompress((out / (p.name + ".zz")).read_bytes()) == p.read_bytes()
           for p in sorted(out.glob("*.json"))], [True, True])


for nm, fn in (("A", part_a), ("B", part_b), ("R", part_r), ("O", part_o)):
    safe(nm, fn)
failed = [n for n, ok in RESULTS if not ok]
print(f"{len(RESULTS) - len(failed)} of {len(RESULTS)} checks pass")
print("ALL PASS" if not failed and RESULTS else f"{len(failed)} failed: {failed}")
sys.exit(0 if not failed and RESULTS else 1)
