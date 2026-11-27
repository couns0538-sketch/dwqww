"""Opus 26 Nov 2026: home/loop.py, sections E to H of Fable's text KNOWN_ANSWERS_home_loop_by_fable.md
(9df6ef51b417): the decision, the state's alarms, the end of the day and the hourly line. My known answers were
written before this file (in the lab: tmp/opus_scratch/v17/loop_b/KNOWN_ANSWERS_loop_EH_by_opus.md). Sections A to D,
LX and LS are Fable's harness (tmp/fable_scratch/loop_harness/harness.py); this file is its part 2 in her form: the
REAL loop, and her stand-in for every program the loop starts (tests/loop_standin.py, her standin.py byte for byte).
Cases N1 to N4 (added 26 Nov evening, before the fixed loop ran): Neon's four findings, R19 to R22 of
tmp/opus_scratch/v17/loop_c/KA_loop_c.md; each fails on the loop before (loop_b's e985350618ce).
    test_loop.py <NEW work folder> <a python with python-chess 1.11.2> [loop=<the loop.py under test>] [only=<case>,..]
Each case builds its own world and starts the loop ONCE without --once (--pass-seconds 0, --stall-passes 3); the
(N+1)th call of clock measure writes home/loop/STOP, so N whole passes run. Exit 0 when every answer is as known.
"""
import calendar
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zlib
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
STANDIN = HERE / "loop_standin.py"
HOME_PROGS = ("clock", "fetch", "custody", "content", "credit", "publish", "deliver", "state", "drain")
HEADER = json.dumps({"lease_end_utc": "2026-12-01T06:00:00Z", "test": "test_loop"}, sort_keys=True,
                    separators=(",", ":")).encode("ascii") + b"\n"
FP = hashlib.sha256(HEADER).hexdigest()
LEASE_END_S = calendar.timegm((2026, 12, 1, 6, 0, 0))
T = "1796019405.200"
READING = {"server_now": T, "lag_s": "80.000", "n": 2}
R11 = sorted(["alarms", "c4_rows", "now_s", "outcome", "outcome_exit", "pass", "pilot", "programs", "run", "seen_k",
              "sent_k", "state_k", "t", "upper_ms"])

if len(sys.argv) < 3:
    print(__doc__)
    sys.exit(2)
WORK, CHESS_PY = Path(sys.argv[1]).resolve(), Path(sys.argv[2])
LOOP, ONLY = HERE.parent / "home" / "loop.py", None
for x in sys.argv[3:]:
    if x.startswith("loop="):
        LOOP = Path(x[5:]).resolve()
    elif x.startswith("only="):
        ONLY = set(x[5:].split(","))
    else:
        print(f"STOP: not understood: {x}")
        sys.exit(2)
if WORK.exists():
    print(f"STOP: the work folder must be NEW: {WORK}")
    sys.exit(2)
for need in (LOOP, STANDIN, CHESS_PY):
    if not need.exists():
        print(f"STOP: missing {need}")
        sys.exit(2)
WORK.mkdir(parents=True)
STANDIN_BYTES = STANDIN.read_bytes()
RES: list = []
TRACEBACKS: list = []


def check(name, got, want):
    ok = got == want
    RES.append((name, ok))
    print(f"{'PASS' if ok else 'FAIL'} {name}: got {str(got)[:400]}" + ("" if ok else f"; want {str(want)[:400]}"),
          flush=True)


def opt(argv, flag):
    return argv[argv.index(flag) + 1] if flag in argv and argv.index(flag) + 1 < len(argv) else None


def state_spec(c4=0, pilot="waiting: 0 of 2 rounds whole", pr=0, pg=0):
    return {"exit": 0, "last": f"state: k @@K@@, now_s 1086, c4_rows {c4}; pilot: {pilot}",
            "do": [{"op": "write", "at": "home", "path": "state/state.@@K@@.json", "create_only": True,
                    "text": json.dumps({"c4_rows": c4, "now_s": 1086, "partial_games": pg, "partial_rounds": pr,
                                        "pilot": pilot, "run_fingerprint": FP}, sort_keys=True)}]}


def bud(outcome, reason, code=0):
    return {"exit": code, "last": json.dumps({"outcome": outcome, "reason": reason}, sort_keys=True)}


def mc(kind, decision):
    return {"exit": 0, "last": "make_control: CONTROL.@@K@@.json written (stand-in)",
            "do": [{"op": "write", "at": "out", "path": "CONTROL.@@K@@.json",
                    "text": json.dumps({"decision": decision, "kind": kind}, sort_keys=True)}]}


SEND_OK = {"exit": 0, "last": "deliver: sent (stand-in)",
           "do": [{"op": "copytree", "at": "home", "path": "deliver/sent", "from_at": "made", "from": "."}]}
NO_PILOT = bud("UNQUALIFIED", "D3: no pilot record; nothing starts by script", 6)
STOP_AT = {"do": [{"op": "write", "at": "home", "path": "loop/STOP", "text": "test_loop: the passes are done\n"}]}


class World:
    """One case's own stand-in tree, home and day files (Fable's World, harness.py, in this file's form)."""

    def __init__(self, name: str, action: str = "self_play", pilot: bool = True):
        self.name, self.d = name, WORK / name
        self.tree, self.home = self.d / "pkg", self.d / "home"
        for sub in ("home", "tools", "STANDIN"):
            (self.tree / sub).mkdir(parents=True)
        shutil.copyfile(LOOP, self.tree / "home" / "loop.py")
        for n in HOME_PROGS:
            (self.tree / "home" / f"{n}.py").write_bytes(STANDIN_BYTES)
        for n in ("budget", "make_control"):
            (self.tree / "tools" / f"{n}.py").write_bytes(STANDIN_BYTES)
        rows = [f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(self.tree).as_posix()}\n"
                for p in sorted(self.tree.rglob("*.py"))]
        (self.tree / "MANIFEST.sha256").write_text("".join(rows), encoding="ascii", newline="")
        fz = self.d / "frozen"
        (fz / "nnloop").mkdir(parents=True)
        for n in ("filterqc.py", "datagen_uci.py", "common.py"):
            (fz / "nnloop" / n).write_text(f"# stand-in {n}\n", encoding="ascii")
        (fz / "config.forge.toml").write_text("# stand-in frozen config\n", encoding="ascii")
        (self.d / "tables").mkdir()
        for n, text in (("fetch.json", "{}\n"), ("tables.list", "stand-in\n"), ("converter.exe", "stand-in\n")):
            (self.d / n).write_text(text, encoding="ascii")
        self.plan = self.d / "plan.json"
        self.plan.write_text(json.dumps({"owner_choice": {"action": action, "name": "test"}}, sort_keys=True) + "\n",
                             encoding="ascii")
        self.put("wire/RUN.json.zz", zlib.compress(HEADER))
        if pilot:
            self.put("pilot/pilot.json", b"{}\n")

    def put(self, rel: str, data: bytes) -> None:
        p = self.home / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)

    def D(self, n) -> Path:
        return self.home / "loop" / "decisions" / str(n)

    def run(self, passes: int, specs: dict, stall: int = 3, devnull: bool = False):
        """ONE start without --once: `passes` whole passes; (exit code, last stdout line). devnull: stdin, stdout and
        stderr all to DEVNULL (LS8), the last line then ''."""
        plan = {"clock measure": [{}] * passes + [STOP_AT], "clock.reading": [READING], "deliver send": [SEND_OK],
                "state": [state_spec()], "budget": [NO_PILOT]}
        plan.update(specs)
        (self.tree / "STANDIN" / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
        fz = self.d / "frozen"
        a = ["--home", self.home, "--fingerprint", FP, "--fetch-config", self.d / "fetch.json", "--config",
             fz / "config.forge.toml", "--pipeline", fz, "--tables", self.d / "tables", "--tables-list",
             self.d / "tables.list", "--converter", self.d / "converter.exe", "--chess-python", CHESS_PY, "--plan",
             self.plan, "--pass-seconds", 0, "--stall-passes", stall]
        cmd = [sys.executable, "-I", "-B", str(self.tree / "home" / "loop.py")] + [str(x) for x in a]
        if devnull:
            rc = subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                timeout=600).returncode
            return rc, ""
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600, stdin=subprocess.DEVNULL)
        if "Traceback" in r.stderr or "Traceback" in r.stdout:
            TRACEBACKS.append((self.name, r.stderr[-300:]))
        return r.returncode, (r.stdout.strip().splitlines() or [""])[-1]

    def calls(self, key: str) -> list:
        p = self.tree / "STANDIN" / "calls.jsonl"
        rows = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []
        return [x["argv"] for x in rows if x["prog"] == key]

    def jl(self, name: str) -> list:
        p, out = self.home / "loop" / name, []
        if p.exists():
            for raw in p.read_bytes().split(b"\n"):
                try:
                    out.append(json.loads(raw))
                except ValueError:
                    pass
        return out

    def alarm_lines(self, key: str) -> list:
        return [(r["t"], r["pass"]) for r in self.jl("alarms.jsonl") if r.get("alarm") == key]

    def standing(self) -> dict:
        st: dict = {}
        for r in self.jl("alarms.jsonl"):
            if r.get("t") == "end":
                st.pop(r["alarm"], None)
            else:
                st[r["alarm"]] = r.get("text")
        return st

    def log(self) -> str:
        p = self.home / "loop" / "loop.log"
        return p.read_text(encoding="ascii", errors="replace") if p.exists() else ""

    def mc_argv(self, n: int, kind: str, k: int, with_state: bool) -> list:
        a = ["--report", str(self.D(n) / "report.json"), "--header", str(self.home / "loop" / "RUN.json"), "--policy",
             str(self.plan.resolve()), "--accepted", str(self.home / "deliver" / "sent"), "--kind", kind, "--out",
             str(self.D(n) / "made")]
        if with_state:
            a += ["--state", str(self.home / "state" / f"state.{k}.json"), "--pilot",
                  str(self.home / "pilot" / "pilot.json")]
        return a


# ---- E. the decision -------------------------------------------------------------------------------------------------
def case_E1():
    w = World("E1")
    b1, b2 = bud("SELF_PLAY", "e1 pilot"), bud("REACHED", "e1 reached", 3)
    rc, last = w.run(3, {"budget": [b1, b2], "make_control": [mc("pilot_decision", "SELF_PLAY"),
                                                               mc("target", "REACHED")]})
    mk, sd = w.calls("make_control"), w.calls("deliver send")
    check("E1a make_control is called 2 times, kinds [pilot_decision, target]", [opt(a, "--kind") for a in mk],
          ["pilot_decision", "target"])
    check("E1b its 1st argv exactly (LD3)", mk[0] if mk else None, w.mc_argv(1, "pilot_decision", 1, True))
    check("E1c its 2nd argv exactly (LD4)", mk[1] if len(mk) > 1 else None, w.mc_argv(2, "target", 2, True))
    rep = [(w.D(n) / "report.json").read_bytes() if (w.D(n) / "report.json").exists() else None for n in (1, 2)]
    check("E1d D1 and D2 report.json are budget's stdout bytes of passes 1 and 2", rep,
          [(b1["last"] + os.linesep).encode(), (b2["last"] + os.linesep).encode()])
    check("E1e deliver send is called 2 times, --made D1/made then D2/made", [opt(a, "--made") for a in sd],
          [str(w.D(1) / "made"), str(w.D(2) / "made")])
    check("E1f budget is called 3 times (nothing is made in pass 3: LD9)", len(w.calls("budget")), 3)
    check("E1g no alarm stands; exit 0 'loop: stopped by STOP'; drain never called",
          (w.standing(), rc, last, len(w.calls("drain"))), ({}, 0, "loop: stopped by STOP", 0))


def case_E2():
    w = World("E2")
    w.run(1, {"budget": [bud("UNQUALIFIED", "e2 reason", 5)], "make_control": [mc("pilot_decision", "UNQUALIFIED")]})
    st = w.standing()
    check("E2 'unqualified' stands with its text; no 'day stops'; deliver send called once",
          (st.get("unqualified"), "day stops" in st, len(w.calls("deliver send"))),
          ("e2 reason; nothing starts by script", False, 1))


def case_E3():
    w = World("E3")
    w.run(2, {"budget": [bud("STOP", "e3 stop", 4), bud("REACHED", "e3 reached", 3)],
              "make_control": [mc("pilot_decision", "STOP")]})
    check("E3 'day stops' stands with 'STOP: e3 stop'; make_control once; deliver send once",
          (w.standing().get("day stops"), len(w.calls("make_control")), len(w.calls("deliver send"))),
          ("STOP: e3 stop", 1, 1))


def case_E4():
    w = World("E4", action="self_play")
    w.run(2, {"budget": [bud("OWNER_CHOICE", "e4 choice", 5), bud("SHORT", "e4 short", 4)],
              "make_control": [mc("pilot_decision", "OWNER_CHOICE")]})
    check("E4a 'day stops' was never raised (R3: the owner's self_play is a schedule)", w.alarm_lines("day stops"), [])
    check("E4b 'behind' stands with 'SHORT: e4 short'; make_control once (LD5)",
          (w.standing().get("behind"), len(w.calls("make_control"))), ("SHORT: e4 short", 1))


def case_E5():
    w = World("E5", action="stop")
    w.run(1, {"budget": [bud("OWNER_CHOICE", "e5 choice", 5)], "make_control": [mc("pilot_decision", "OWNER_CHOICE")]})
    check("E5 with the plan's action stop 'day stops' stands with 'OWNER_CHOICE: e5 choice'",
          w.standing().get("day stops"), "OWNER_CHOICE: e5 choice")


def case_E6():
    w = World("E6")
    w.run(2, {"budget": [bud("SELF_PLAY", "e6")], "make_control": [mc("pilot_decision", "SELF_PLAY")],
              "deliver send": [{"exit": 3, "last": "deliver: HELD: CONTROL.1.json waits (stand-in)"}, SEND_OK]})
    check("E6a make_control is called once", len(w.calls("make_control")), 1)
    check("E6b deliver send is called 2 times, both --made D1/made", [opt(a, "--made") for a in w.calls("deliver send")],
          [str(w.D(1) / "made")] * 2)
    check("E6c loop.log holds the note 'note: deliver send exit 3'", "note: deliver send exit 3" in w.log(), True)
    check("E6d no alarm stands", w.standing(), {})


def case_E7():
    w = World("E7")
    w.run(2, {"budget": [bud("SELF_PLAY", "e7")], "make_control": [mc("pilot_decision", "SELF_PLAY")],
              "deliver send": [{"exit": 4, "last": "deliver: REFUSED (4): stand-in"}, SEND_OK]})
    check("E7a D1/REFUSED exists", (w.D(1) / "REFUSED").is_file(), True)
    check("E7b make_control is called 2 times, --out D1/made then D2/made",
          [opt(a, "--out") for a in w.calls("make_control")], [str(w.D(1) / "made"), str(w.D(2) / "made")])
    check("E7c deliver send --made D1/made then D2/made", [opt(a, "--made") for a in w.calls("deliver send")],
          [str(w.D(1) / "made"), str(w.D(2) / "made")])
    check("E7d 'control' lines [start 1, end 2]; nothing stands", (w.alarm_lines("control"), w.standing()),
          ([("start", 1), ("end", 2)], {}))


def case_E8():
    w = World("E8")
    w.put("loop/FENCE_REQUEST", b"test_loop: a person's fence\n")
    w.run(2, {"budget": [bud("SELF_PLAY", "e8")], "make_control": [mc("fence", "FENCE")]})
    check("E8a make_control is called once, argv exactly (kind fence, no --state, no --pilot)",
          w.calls("make_control"), [w.mc_argv(1, "fence", 1, False)])
    check("E8b deliver send is called once", len(w.calls("deliver send")), 1)
    check("E8c 'fence' was never raised; nothing stands", (w.alarm_lines("fence"), w.standing()), ([], {}))


def case_E9():
    w = World("E9")
    w.put("loop/FENCE_REQUEST", b"test_loop: a person's fence\n")
    w.run(1, {"state": [{"exit": 9, "last": "state: STOP (9): no clock line of this run: run clock.py measure first"}]})
    check("E9a budget and make_control are not called", (len(w.calls("budget")), len(w.calls("make_control"))), (0, 0))
    check("E9b 'fence' stands with 'fence waits: no report yet'", w.standing().get("fence"), "fence waits: no report yet")


def case_E10():
    ctl = json.dumps({"decision": "SELF_PLAY", "kind": "pilot_decision"}, sort_keys=True).encode()
    for sub, seen in (("a", False), ("b", True)):
        w = World(f"E10{sub}", pilot=False)
        w.put("loop/decisions/1/made/CONTROL.1.json", ctl)
        w.put("deliver/sent/CONTROL.1.json", ctl)
        if seen:
            w.put("control/CONTROL.1.json", ctl)
        w.run(2, {"budget": [bud("SELF_PLAY", "e10")]})
        sd = [opt(a, "--made") for a in w.calls("deliver send")]
        if seen:
            check("E10b a sent control that home has SEEN is not sent again at the start", sd, [])
        else:
            check("E10a a sent control not seen: its folder is sent once more at the start (R4), nothing made",
                  (sd, len(w.calls("make_control"))), ([str(w.D(1) / "made")], 0))


def case_E11():
    w = World("E11")
    st = [state_spec(), state_spec()]
    for s in st:   # the same k in passes 1 and 2: the stand-in's @@K@@ would count the calls
        s["last"] = s["last"].replace("@@K@@", "1")
        s["do"][0]["path"] = "state/state.1.json"
    w.run(3, {"state": st + [dict(state_spec(), last=state_spec()["last"].replace("@@K@@", "2"),
                                  do=[dict(state_spec()["do"][0], path="state/state.2.json")])],
              "budget": [bud("SELF_PLAY", "e11")],
              "make_control": [{"exit": 4, "last": "make_control: REFUSED (nothing written): e11"},
                               mc("pilot_decision", "SELF_PLAY")]})
    check("E11 a refused make is not tried again for the same k (R5): --out D1/made then D2/made; 'control' lines "
          "[start 1, end 3]", ([opt(a, "--out") for a in w.calls("make_control")], w.alarm_lines("control")),
          ([str(w.D(1) / "made"), str(w.D(2) / "made")], [("start", 1), ("end", 3)]))


# ---- F. the state's alarms -------------------------------------------------------------------------------------------
def case_F1():
    w = World("F1", pilot=False)
    w.run(2, {"state": [state_spec(pr=1, pg=7), state_spec()]})
    texts = [r.get("text") for r in w.jl("alarms.jsonl") if r.get("alarm") == "partial" and r.get("t") == "start"]
    check("F1 'partial' lines [start 1, end 2], the start's text names the file's numbers",
          (w.alarm_lines("partial"), texts), ([("start", 1), ("end", 2)], ["partial_rounds 1, partial_games 7 (state 1)"]))


def case_F2():
    w = World("F2", pilot=False)
    text = "cannot qualify: the home was not empty at the first start"
    w.run(1, {"state": [state_spec(pilot=text)]})
    check("F2 'pilot' stands with the pilot text (LA3)", w.standing().get("pilot"), text)


def case_F3():
    w = World("F3", pilot=False)
    npm = "waiting: no publish moment yet (f3)"
    w.run(6, {"state": [state_spec(pilot="waiting: 0 of 2 rounds whole")] + [state_spec(pilot=npm)] * 4
              + [state_spec(pilot="waiting: 1 of 2 rounds whole")]})
    check("F3 'pilot' lines [start 4, end 6] (LA5: the 3rd pass in a row)", w.alarm_lines("pilot"),
          [("start", 4), ("end", 6)])


def case_F4():
    w = World("F4", pilot=False)
    w.put("deliver/sent/CONTROL.1.json", json.dumps({"decision": "SELF_PLAY", "kind": "pilot_decision"}).encode())
    w.run(5, {"state": [state_spec(c4=5)] * 3 + [state_spec(c4=9)] * 2})
    check("F4 'stalled' lines [start 3, end 4] (LA4, --stall-passes 3); nothing made",
          (w.alarm_lines("stalled"), len(w.calls("make_control"))), ([("start", 3), ("end", 4)], 0))


# ---- G. the end of the day -------------------------------------------------------------------------------------------
def case_G1():
    w = World("G1", pilot=False)
    w.put("wire/TERMINAL.jsonl.zz", zlib.compress(b""))
    w.run(2, {})
    check("G1 drain is called 2 times with --why 'lease ended'; the note 'drain exit 4'; nothing stands",
          (w.calls("drain"), "note: drain exit 4" in w.log(), w.standing()),
          ([["--home", str(w.home), "--fingerprint", FP, "--why", "lease ended"]] * 2, True, {}))


def case_G2():
    w = World("G2", pilot=False)
    w.put("loop/DECLARED_STOP", b"test_loop: a declared stop\n")
    w.run(1, {})
    check("G2 drain is called once with --why 'declared stop'", [opt(a, "--why") for a in w.calls("drain")],
          ["declared stop"])


def case_G3():
    w = World("G3", pilot=False)
    w.put("wire/TERMINAL.jsonl.zz", zlib.compress(b""))
    rc, last = w.run(10, {"drain": [{"exit": 0, "last": "drain: DRAIN.json written (stand-in)",
                                     "do": [{"op": "write", "at": "home", "path": "DRAIN.json", "text": "{}\n"}]}],
                          "fetch": [{}, {"do": [{"op": "write", "at": "home", "path": "wire/g3.bin", "size": 5}]}, {}]})
    check("G3a exit 0, the last line 'loop: the day is closed at home; c4_rows 0'", (rc, last),
          (0, "loop: the day is closed at home; c4_rows 0"))
    check("G3b clock measure is called 3 times (pass 2 moved a file)", len(w.calls("clock measure")), 3)
    check("G3c drain is called once", len(w.calls("drain")), 1)
    check("G3d hourly.jsonl t: [start, end]", [r.get("t") for r in w.jl("hourly.jsonl")], ["start", "end"])


def case_G4():
    w = World("G4a", pilot=False)
    w.run(1, {"clock.reading": [{"server_now": f"{LEASE_END_S}.000", "lag_s": "0.000", "n": 2}]})
    check("G4a the server's time exactly at the lease end: drain once, --why 'lease ended'",
          [opt(a, "--why") for a in w.calls("drain")], ["lease ended"])
    w = World("G4b", pilot=False)
    w.run(1, {"clock.reading": [{"server_now": f"{LEASE_END_S - 1}.000", "lag_s": "0.500", "n": 2}]})
    check("G4b half a second before the lease end: drain not called", len(w.calls("drain")), 0)


# ---- H. the hourly line ----------------------------------------------------------------------------------------------
def case_H1():
    w = World("H1", pilot=False)
    later = dict(READING, server_now=str(Decimal(T) + 3600))
    w.run(3, {"clock.reading": [READING, READING, later]})
    h = w.jl("hourly.jsonl")
    check("H1a hourly.jsonl t: [start, hour, end]", [r.get("t") for r in h], ["start", "hour", "end"])
    check("H1b the hour line's pass is 2", [r.get("pass") for r in h if r.get("t") == "hour"], [2])
    check("H1c every hourly line has exactly R11's 14 keys", [sorted(r) for r in h if sorted(r) != R11], [])


# ---- LS8: how the loop is started -----------------------------------------------------------------------------------
def case_L1():
    w = World("L1", pilot=False)
    rc, _last = w.run(2, {}, devnull=True)
    kinds = [r.get("kind") for r in w.jl("journal.jsonl") if r.get("t") == "pass"]
    check("L1 stdin, stdout and stderr to DEVNULL (LS8): exit 0, the pass lines [c3, c4, c3, c4], loop.log 'start: run'",
          (rc, kinds, "start: run" in w.log()), (0, ["c3", "c4", "c3", "c4"], True))


# ---- N. Neon's four findings of 26 Nov 2026 (neon/BUGS_FOR_OPUS.md; R19 to R22 of loop_c/KA_loop_c.md) -------------
SENT_COPY = [{"op": "copytree", "at": "home", "path": "deliver/sent", "from_at": "made", "from": "."}]


def case_N1():
    w = World("N1")
    unhold = dict(state_spec(), do=state_spec()["do"] + [{"op": "remove", "at": "home", "path": "loop/HOLD_CONNECT"}])
    w.run(2, {"budget": [bud("SELF_PLAY", "n1")], "make_control": [mc("pilot_decision", "SELF_PLAY")],
              "deliver send": [{"exit": 6, "last": "deliver: STOP (6): the host key or the login failed (stand-in)",
                                "do": SENT_COPY}, SEND_OK],
              "state": [state_spec(), unhold, state_spec()]})
    check("N1 a send that ends 6 after deliver wrote its sent copy is sent again once a person removed HOLD_CONNECT "
          "(LX2, R19): deliver send --made [D1, D1]; make_control once; 'login' lines [start 1, end 3]",
          ([opt(a, "--made") for a in w.calls("deliver send")], len(w.calls("make_control")), w.alarm_lines("login")),
          ([str(w.D(1) / "made")] * 2, 1, [("start", 1), ("end", 3)]))


def case_N2():
    e = "e" * 64
    for sub, covered in (("a", True), ("b", False)):
        w = World(f"N2{sub}", action="reduced_target")
        w.plan.write_text(json.dumps({"owner_choice": {"action": "reduced_target", "if_uncovered": "stop",
                                                       "name": "test", "reduced_target_rows": 1000}},
                                     sort_keys=True) + "\n", encoding="ascii")
        made = {"exit": 0, "last": "make_control: CONTROL.@@K@@.json written (stand-in)",
                "do": [{"op": "write", "at": "out", "path": f"EVIDENCE.{e}.json",
                        "text": json.dumps({"reduced": {"covered": covered, "target_rows": 1000}}, sort_keys=True)},
                       {"op": "write", "at": "out", "path": "CONTROL.@@K@@.json",
                        "text": json.dumps({"decision": "OWNER_CHOICE", "evidence": e, "kind": "pilot_decision"},
                                           sort_keys=True)}]}
        w.run(1, {"budget": [bud("OWNER_CHOICE", "n2 choice", 5)], "make_control": [made]})
        if covered:
            check("N2a reduced_target, covered, if_uncovered stop: 'day stops' never raised (R20: before the send the "
                  "evidence in its made/ folder decides: a schedule); deliver send once",
                  (w.alarm_lines("day stops"), len(w.calls("deliver send"))), ([], 1))
        else:
            check("N2b reduced_target, NOT covered, if_uncovered stop: 'day stops' stands with 'OWNER_CHOICE: n2 "
                  "choice' (a fence; N2a's positive control)", w.standing().get("day stops"), "OWNER_CHOICE: n2 choice")


def case_N3():
    w = World("N3")
    conflict = {"exit": 3, "last": "deliver: STOP (3): CONFLICT: the inbox's CONTROL.1.json.zz holds other bytes than "
                                   "the ones sent; nothing replaced (stand-in)", "do": SENT_COPY}
    w.run(2, {"budget": [bud("SELF_PLAY", "n3"), bud("REACHED", "n3 reached", 3)],
              "make_control": [mc("pilot_decision", "SELF_PLAY"), mc("target", "REACHED")],
              "deliver send": [conflict, SEND_OK]})
    check("N3 deliver send's CONFLICT (exit 3) stands after a later send exits 0 (LX3, R21): deliver send --made "
          "[D1, D2]; 'conflict' lines [start 1]; it stands",
          ([opt(a, "--made") for a in w.calls("deliver send")], w.alarm_lines("conflict"), "conflict" in w.standing()),
          ([str(w.D(1) / "made"), str(w.D(2) / "made")], [("start", 1)], True))


def case_N4():
    for sub, b2, want in (("a", bud("REACHED", "n4 reached", 3), []), ("b", bud("SELF_PLAY", "n4"), [("start", 4)])):
        w = World(f"N4{sub}")
        w.run(4, {"budget": [bud("SELF_PLAY", "n4"), b2],
                  "make_control": [mc("pilot_decision", "SELF_PLAY"), mc("target", "REACHED")]})
        what = ("the target REACHED (a fence) sent in pass 2, c4_rows flat: 'stalled' never raised (LA4, R22); "
                "make_control 2 times" if sub == "a" else
                "no fence, c4_rows flat from pass 2: 'stalled' lines [start 4] (N4a's positive control); make_control "
                "once")
        check(f"N4{sub} {what}", (w.alarm_lines("stalled"), len(w.calls("make_control"))),
              (want, 2 if sub == "a" else 1))


FETCH_LINE = ("fetch: listing 642 bytes; control 0 files 0 bytes; offers 0 files 0 bytes; members 0 files 0 bytes; "
              "sent again 0 bytes; partial {p}; confirmations 0; forks 0; refused 0; incomplete {i}; ignored 0; "
              "budget binds {b}")


def case_N5():
    w = World("N5", pilot=False)
    w.put("wire/TERMINAL.jsonl.zz", zlib.compress(b""))
    w.run(4, {"fetch": [{"exit": 0, "last": FETCH_LINE.format(p=p, i=i, b=b)}
                        for p, i, b in ((1, 0, "no"), (0, 0, "yes"), (0, 1, "no"), (0, 0, "no"))]})
    waits = [ln for ln in w.log().splitlines() if "note: drain waits: fetch still receives" in ln]
    check("N5 TERMINAL at home while fetch still receives (partial 1, then budget binds yes, then incomplete 1): "
          "drain waits 3 passes (R23) and is called once, in pass 4; 3 notes",
          ([opt(a, "--why") for a in w.calls("drain")], len(waits)), (["lease ended"], 3))


def case_N6():
    w = World("N6", pilot=False)
    w.run(1, {"clock.reading": [{"server_now": f"{LEASE_END_S}.000", "lag_s": "0.000", "n": 2}],
              "fetch": [{"exit": 7, "last": "fetch: STOP 7: the server cannot be reached (stand-in)"}]})
    check("N6 at the lease end with fetch 7 (a server given back, LE1): drain is called once with --why 'lease ended' "
          "(R23's one exception; the positive control of N5 and N7)",
          [opt(a, "--why") for a in w.calls("drain")], ["lease ended"])


def case_N7():
    w = World("N7", pilot=False)
    w.put("wire/TERMINAL.jsonl.zz", zlib.compress(b""))
    w.put("loop/HOLD_CONNECT", b"test_loop: a login failed before this start\n")
    stop2 = dict(state_spec(), do=state_spec()["do"] + [{"op": "write", "at": "home", "path": "loop/STOP",
                                                         "text": "test_loop: the passes are done\n"}])
    rc, last = w.run(0, {"state": [state_spec(), stop2]})
    check("N7 TERMINAL at home, HOLD_CONNECT stands, so no fetch in the pass: drain is not called (R23), the note "
          "names it; exit 0 'loop: stopped by STOP' in pass 2",
          (len(w.calls("drain")), "note: drain waits: no fetch ran in this pass" in w.log(), rc, last),
          (0, True, 0, "loop: stopped by STOP"))


def case_N8():
    w = World("N8", pilot=False)
    w.put("wire/TERMINAL.jsonl.zz", zlib.compress(b""))
    rc, last = w.run(10, {"drain": [{"exit": 0, "last": "drain: DRAIN.json written (stand-in)",
                                     "do": [{"op": "write", "at": "home", "path": "DRAIN.json", "text": "{}\n"}]}],
                          "fetch": [{}, {"do": [{"op": "write", "at": "home", "path": "wire/n8.bin", "size": 5}]}, {}],
                          "content": [{}, {}, {"exit": 4, "last": "content: STOP 4: a home file cannot be read "
                                                                  "(stand-in)"}, {}]})
    check("N8 G3's day with content exit 4 in pass 3: the day is not closed in pass 3 (R24) but in pass 4: exit 0, "
          "the closing line; clock measure 4 times",
          (rc, last, len(w.calls("clock measure"))), (0, "loop: the day is closed at home; c4_rows 0", 4))


CASES = [("E1", case_E1), ("E2", case_E2), ("E3", case_E3), ("E4", case_E4), ("E5", case_E5), ("E6", case_E6),
         ("E7", case_E7), ("E8", case_E8), ("E9", case_E9), ("E10", case_E10), ("E11", case_E11), ("F1", case_F1), ("F2", case_F2), ("F3", case_F3),
         ("F4", case_F4), ("G1", case_G1), ("G2", case_G2), ("G3", case_G3), ("G4", case_G4), ("H1", case_H1),
         ("L1", case_L1), ("N1", case_N1), ("N2", case_N2), ("N3", case_N3), ("N4", case_N4), ("N5", case_N5),
         ("N6", case_N6), ("N7", case_N7), ("N8", case_N8)]
for nm, fn in CASES:
    if ONLY is None or nm in ONLY:
        try:
            fn()
        except Exception as e:  # noqa: BLE001   a crash inside a case is one FAIL; the others still run
            check(f"{nm} ran to its end", repr(e)[:300], "no exception")
check("no Traceback in any start of the loop", TRACEBACKS, [])
check("no __pycache__ anywhere in the worlds", [str(p) for p in WORK.rglob("__pycache__")], [])
bad = [n for n, ok in RES if not ok]
print(f"{len(RES) - len(bad)} of {len(RES)} as known")
print("ALL AS KNOWN" if not bad else f"{len(bad)} NOT as known: {bad}")
sys.exit(0 if not bad and RES else 1)
