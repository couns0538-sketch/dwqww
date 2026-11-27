"""Opus 26 Nov 2026: home/loop.py, THE HOME LOOP of the server day (v17; Fable's B of FABLE-2611-TAKE-OVER). Its known
answers were written before this code: tmp/fable_scratch/reads_2611/KNOWN_ANSWERS_home_loop_by_fable.md 9df6ef51b417
(sections A to J; LA5 in the agreed wording; the call FIXED in OPUS-2611-LOOPCALL-FIXED). Where that text leaves a
choice, my reading stands in tmp/opus_scratch/v17/loop_b/READINGS.md (R1 to R11, written before the first run).
Standard library only; nothing is installed.

    loop.py --home DIR --fingerprint HEX64 --fetch-config FILE --config FILE --pipeline DIR --tables DIR
            --tables-list FILE --converter FILE [--openings FILE] --chess-python FILE --plan FILE
            --pass-seconds N --stall-passes N [--once]

THE PASS (LP1), every program its own process (-I -B, stdin closed), judged by its exit code and its last stdout line
only: (1) clock.py measure; (2) fetch.py; (3) custody.py; the c3 line; (4) content.py; (5) credit.py; (6) publish.py;
the c4 line; (7) deliver.py observe; (8) state.py; (9) tools/budget.py; (10) the control (E); (11) the end of the day
(G). The programs are the loop's own package: home/<name>.py beside this file, tools/ one folder up. content.py and
publish.py run under --chess-python, every other program under this Python. The next pass begins --pass-seconds
after the last began, or at once when that one took longer. Before the header wire/RUN.json.zz is at home a pass runs
clock and fetch only (LS6); once it is, the loop writes home/loop/RUN.json, the decoded header, create-only (its
sha256 must be the fingerprint, else exit 3): make_control's --header.
THE JOURNAL home/loop/journal.jsonl (state.py's input; LP7): only start lines {"empty","run","t":"start","why"} and
pass lines {"kind","ms","moved","new_reports","run","t":"pass","upper_ms"}, canonical, one write each, flushed. A
part's line is written when its last program ran, whatever it exited (LP6, LP8, R2): ms from fetch's start to
custody's end (c3) or from content's start to publish's end (c4), whole milliseconds rounded up; moved: the names
whose existence or size changed (c3: wire/ and custody/; c4: content/, stage/, rounds/); new_reports (c4): the rounds
with rounds/r<NNNN>/report.json named in no earlier line of this run, rising; upper_ms: ceil(1000 x (server_now +
lag_s)) of home/clock.py's reading() at the part's end, null when it refuses. Never the PC's wall clock.
THE START: the OS lock home/loop/LOCK (held by another loop: exit 8, nothing written); a person's home/loop/STOP:
exit 0 (R8); every file of MANIFEST.sha256 at its sha256 (LS9); --chess-python imports python-chess 1.11.2 (LS7);
home/loop/FROZEN.json (HL3: written at the first start, the same inputs at every later one). A failed check: exit 4,
a line naming it, no start line. Then the start line (empty: wire/, custody/, content/, stage/ and rounds/ hold no
file), the hourly line, the passes.
EXITS AND ALARMS (section D under J and LX5, R1): the loop ends only on a 2 or 3 of fetch.py or custody.py (the STOP
class: its alarm, ALARM.txt, the last line "loop: STOP (<code>): <program>: <its last line>", that exit code). A 2
or 3 of content, credit, publish, state or drain, a 2 of deliver observe, probe or send write home/loop/HOLD_LOCAL:
while it stands every pass runs clock, fetch and custody only. A 6 writes home/loop/HOLD_CONNECT: while it stands
nothing connects (measure, fetch, probe, send). A person removes either file after looking. An alarm (one line in
home/loop/alarms.jsonl when it starts, changes or ends; home/loop/ALARM.txt while one stands) never stops the loop;
one raised by an exit code ends when that program exits 0 again (unreachable: when fetch does); the others by their
own rule (R6). A code in no cell: the alarm "<program> crashed", the pass goes on.
THE DECISION (E): the pilot_decision once, from the first state beside home/pilot/pilot.json (budget's stdout byte for
byte as home/loop/decisions/<k>/report.json, make_control into decisions/<k>/made, deliver send); after it only a
target on REACHED, once; OWNER_CHOICE, STOP or SHORT after a pilot decision with a schedule: the alarm "behind", no
control; a person's fence: home/loop/FENCE_REQUEST. A made folder whose control is not in deliver/sent/ is sent first
(held: again at the next pass; never a second folder); nothing is made after a control with the fence's effect.
THE END OF THE DAY (G): drain.py --why "lease ended" once a pass when wire/TERMINAL.jsonl.zz is at home or upper_ms is
at or past the header's lease_end_utc; --why "declared stop" while home/loop/DECLARED_STOP stands. With home/DRAIN.json
at home, the first whole pass begun after it with moved 0 in both lines and credit and publish at 0 closes the day:
exit 0, "loop: the day is closed at home; c4_rows <n>". home/loop/STOP ends the loop between two programs: exit 0.
--once: one pass, exit 0; no drain, no closing hourly line. home/loop/hourly.jsonl: one line at every start, when the
server's hour changes (every 60 passes without a clock), and at the end (R11).
Exit codes: 0 the day closed, a STOP file or --once; 2 a wrong call (and fetch's or custody's 2); 3 the header is not
this run's (and their 3); 4 a start check; 8 another loop holds the lock.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import time
import zlib
from datetime import datetime, timezone
from decimal import ROUND_CEILING, Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = HERE.parent
HEX64 = re.compile(r"[0-9a-f]{64}")
ROW = re.compile(r"([0-9a-f]{64})  (\S.*)")
ROUND_DIR = re.compile(r"r(\d{4})")
CONTROL = re.compile(r"CONTROL\.(\d+)\.json")
STATE_LINE = re.compile(r"state: k (\d+), now_s (-?\d+), c4_rows (\d+); pilot: (.*)")
FETCH_LEFT = re.compile(r"; partial (\d+); .*; incomplete (\d+); .*; budget binds (yes|no)$")    # R23: fetch.py's last line
PILOT_STOP = ("cannot qualify", "refused", "no server record")
CONNECTS = ("clock measure", "fetch", "deliver probe", "deliver send")
CHESS = "1.11.2"
QUIET = ("wire", "custody", "content", "stage", "rounds")          # LS2: empty when these hold no file
# section D under J and LX5 (R1): code -> (what, alarm key)
D = {
    "clock measure": {0: ("ok",), 8: ("note",), 9: ("note",), 2: ("alarm", "clock"), 4: ("alarm", "clock"),
                      7: ("alarm", "unreachable"), 6: ("login",)},
    "fetch": {0: ("ok",), 8: ("note",), 4: ("alarm", "fetch"), 5: ("alarm", "fetch"), 7: ("alarm", "unreachable"),
              6: ("login",), 2: ("stop",), 3: ("stop",)},
    "custody": {0: ("ok",), 4: ("alarm", "custody"), 5: ("alarm", "custody"), 2: ("stop",), 3: ("stop",)},
    "content": {0: ("ok",), 4: ("alarm", "content"), 2: ("hold",), 3: ("hold",)},
    "credit": {0: ("ok",), 4: ("alarm", "credit"), 5: ("alarm", "credit holds"), 2: ("hold",), 3: ("hold",)},
    "publish": {0: ("ok",), 4: ("alarm", "publish"), 5: ("alarm", "publish holds"), 6: ("alarm", "publish failed"),
                2: ("hold",), 3: ("hold",)},
    "deliver observe": {0: ("ok",), 8: ("note",), 3: ("alarm", "observe"), 4: ("alarm", "observe"), 2: ("hold",)},
    "state": {0: ("ok",), 9: ("note",), 4: ("alarm", "state"), 2: ("hold",), 3: ("hold",)},
    "budget": {0: ("ok",), 3: ("ok",), 4: ("ok",), 5: ("ok",), 6: ("ok",), 2: ("alarm", "budget")},
    "make_control": {0: ("ok",), 2: ("alarm", "control"), 4: ("alarm", "control")},
    "deliver probe": {0: ("ok",), 3: ("alarm", "probe"), 4: ("alarm", "probe"), 7: ("alarm", "unreachable"),
                      6: ("login",), 2: ("hold",)},
    "deliver send": {0: ("ok",), 8: ("note",), 4: ("alarm", "control"), 7: ("alarm", "unreachable"), 6: ("login",),
                     2: ("hold",)},                     # 3: HELD (a note) or CONFLICT (an alarm), by its last line
    "drain": {0: ("ok",), 5: ("alarm", "drain holds"), 2: ("hold",), 3: ("hold",)},   # 4: by its last line
}
HOLD_KEY = {"content": "content", "credit": "credit", "publish": "publish", "state": "state",
            "deliver observe": "observe", "deliver probe": "probe", "deliver send": "control", "drain": "drain"}


class End(Exception):
    """The loop ends with this exit code and last line."""

    def __init__(self, code: int, line: str):
        super().__init__(line)
        self.code, self.line = code, line


class Hold(Exception):
    """A hold began (HOLD_LOCAL): the pass ends after the program that holds."""


def canon(obj) -> bytes:
    """The package's canonical form (run/worker.py's canon, the same bytes; the loop imports nothing from run/)."""
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
            + "\n").encode("ascii")


def printable(text: str, n: int = 300) -> str:
    return "".join(c if " " <= c <= "~" else "?" for c in text)[:n]


def last_line(out: bytes) -> str:
    lines = [x.strip() for x in out.decode("utf-8", "replace").splitlines() if x.strip()]
    return printable(lines[-1]) if lines else ""


def sha_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def create_only(p: Path, data: bytes) -> bool:
    """False when p exists (nothing written)."""
    try:
        fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0), 0o644)
    except FileExistsError:
        return False
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    return True


def append(p: Path, data: bytes) -> None:
    """One write of whole bytes, flushed to disk; a file whose last byte is not a line end gets one first."""
    lead = b""
    try:
        if p.stat().st_size:
            with open(p, "rb") as f:
                f.seek(-1, os.SEEK_END)
                lead = b"" if f.read(1) == b"\n" else b"\n"
    except FileNotFoundError:
        pass
    with open(p, "ab") as f:
        f.write(lead + data)
        f.flush()
        os.fsync(f.fileno())


def utc_ms(text: str) -> int:
    return int(datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()) * 1000


def take_lock(p: Path):
    """HL5: an OS lock held for the loop's life; None when another process holds it."""
    fd = os.open(p, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(fd)
        return None
    return fd


def prog_path(key: str) -> Path:
    base = key.split()[0]
    return TREE / "tools" / f"{base}.py" if base in ("budget", "make_control") else HERE / f"{base}.py"


class Loop:
    def __init__(self, a):
        self.a, self.fp = a, a.fingerprint
        self.home = Path(a.home).resolve()
        self.ld = self.home / "loop"
        self.f = {n: self.ld / n for n in ("journal.jsonl", "loop.log", "alarms.jsonl", "ALARM.txt", "hourly.jsonl",
                                          "FROZEN.json", "RUN.json", "STOP", "FENCE_REQUEST", "DECLARED_STOP",
                                          "HOLD_CONNECT", "HOLD_LOCAL")}
        self.dec = self.ld / "decisions"
        self.sent_dir = self.home / "deliver" / "sent"
        self.plan_path = Path(a.plan).resolve()
        self.plan: dict = {}
        self.chess_py = str(Path(a.chess_python))
        self.alarms: dict = {}          # key -> {"text", "program"} (program None: ended only by its own rule, R6)
        self.last: dict = {}            # program key -> (exit code, last line)
        self.named: set = set()         # the rounds named in new_reports of this run's lines
        self.npass = 0
        self.upper = None
        self.state = None               # (k, now_s, c4_rows, pilot text) of the newest state.py exit 0
        self.report = None              # (k, stdout bytes, outcome, exit, with pilot) of this pass's budget, else None
        self.newest_report = None       # the same of the newest budget run of this start (LD8)
        self.probe_ok, self.probe_again = False, True
        self.resend = None              # R4: a folder to send again within this start
        self.refused_k = None           # R5
        self.stall_c4, self.stall_n, self.la5_n = None, 0, 0
        self.hour, self.quiet_passes = None, 0
        self.lines: dict = {}           # this pass: kind -> moved, for LE3

    # ---- small helpers ------------------------------------------------------------------------------------------
    def log(self, msg: str) -> None:
        append(self.f["loop.log"], f"{datetime.now():%Y-%m-%d %H:%M:%S} {printable(msg, 2000)}\n".encode("ascii"))

    def out(self, code: int, line: str, log: bool = True) -> int:
        if log:
            self.log(line)
        try:
            print(printable(line, 2000), flush=True)
        except (OSError, ValueError, AttributeError):
            pass
        return code

    def alarm(self, key: str, text: str, program=None) -> None:
        text = printable(text)
        old = self.alarms.get(key)
        if old is not None and old["text"] == text:
            return
        self.alarms[key] = {"text": text, "program": program, "pass": self.npass}     # pass: R13
        append(self.f["alarms.jsonl"], canon({"alarm": key, "pass": self.npass, "program": program, "run": self.fp,
                                              "t": "start" if old is None else "change", "text": text}))
        self.log(f"ALARM {key}: {text}")
        self.alarm_file()

    def end_alarm(self, key: str) -> None:
        old = self.alarms.pop(key, None)
        if old is None:
            return
        append(self.f["alarms.jsonl"], canon({"alarm": key, "pass": self.npass, "program": old["program"],
                                              "run": self.fp, "t": "end", "text": old["text"]}))
        self.log(f"alarm {key} ends")
        self.alarm_file()

    def alarm_file(self) -> None:
        p = self.f["ALARM.txt"]
        if not self.alarms:
            if p.exists():
                p.unlink()
            return
        text = "".join(f"{k}: {v['text']}\n" for k, v in sorted(self.alarms.items()))
        tmp = p.with_name("ALARM.txt.new")
        tmp.write_bytes(text.encode("ascii", "replace"))
        os.replace(tmp, p)

    def rebuild_alarms(self) -> None:
        """R6: the standing alarms of this run, from alarms.jsonl."""
        p = self.f["alarms.jsonl"]
        if not p.exists():
            return
        for raw in p.read_bytes().split(b"\n"):
            try:
                r = json.loads(raw)
            except ValueError:
                continue
            if not isinstance(r, dict) or r.get("run") != self.fp or not isinstance(r.get("alarm"), str):
                continue
            if r.get("t") == "end":
                self.alarms.pop(r["alarm"], None)
            else:
                self.alarms[r["alarm"]] = {"text": str(r.get("text", "")), "program": r.get("program"), "pass": 0}
        self.alarm_file()

    def upper_now(self):
        """LP5: ceil(1000 x (server_now + lag_s)) from home/clock.py's reading(); None when it refuses."""
        try:
            if str(HERE) not in sys.path:
                sys.path.insert(0, str(HERE))
            import clock as ck  # noqa: E402   the server's time, as drain.py and deliver.py read it
            now, lag, _line = ck.reading(self.home, self.fp)
            v = int((Decimal(1000) * (Decimal(now) + Decimal(lag))).to_integral_value(rounding=ROUND_CEILING))
        except Exception:  # noqa: BLE001   the helper refuses (ClockRefused) or cannot be read: no reading
            return None
        self.upper = v
        return v

    def listing(self, subs) -> dict:
        got = {}
        for s in subs:
            for dp, _dn, fn in os.walk(self.home / s):
                for n in fn:
                    p = os.path.join(dp, n)
                    try:
                        got[os.path.relpath(p, self.home)] = os.stat(p).st_size
                    except OSError:
                        pass
        return got

    @staticmethod
    def moved(before: dict, after: dict) -> int:
        return len(before.keys() ^ after.keys()) + sum(1 for k in before.keys() & after.keys() if before[k] != after[k])

    def pass_line(self, kind: str, t0: float, moved: int, new: list) -> None:
        ms = math.ceil((time.monotonic() - t0) * 1000)
        append(self.f["journal.jsonl"], canon({"kind": kind, "ms": ms, "moved": moved, "new_reports": new,
                                               "run": self.fp, "t": "pass", "upper_ms": self.upper_now()}))
        self.lines[kind] = moved

    def hourly(self, t: str) -> None:
        sent, seen = self.sent(), self.seen_k()
        st, rp = self.state, self.report
        append(self.f["hourly.jsonl"], canon({
            "alarms": sorted(self.alarms), "c4_rows": st[2] if st else None, "now_s": st[1] if st else None,
            "outcome": rp[2] if rp else None, "outcome_exit": rp[3] if rp else None, "pass": self.npass,
            "pilot": st[3] if st else None, "programs": {k: {"exit": c, "last": ln} for k, (c, ln) in self.last.items()},
            "run": self.fp, "seen_k": seen, "sent_k": sent[-1][0] if sent else None, "state_k": st[0] if st else None,
            "t": t, "upper_ms": self.upper}))
        self.quiet_passes = 0

    # ---- one program ----------------------------------------------------------------------------------------------
    def step(self, key: str, args: list, py=None):
        """Start one program (the STOP file looked at first, LP8) and judge it (section D). (exit, last line, stdout)."""
        if self.f["STOP"].exists():
            raise End(0, "loop: stopped by STOP")
        cmd = [py or sys.executable, "-I", "-B", str(prog_path(key))] + key.split()[1:] + [str(x) for x in args]
        try:
            r = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True)
            code, out, err = r.returncode, r.stdout, r.stderr
        except OSError as e:
            code, out, err = -1, b"", str(e).encode()
        last = last_line(out)
        self.last[key] = (code, last)
        self.judge(key, code, last, err)
        return code, last, out

    def judge(self, key: str, code: int, last: str, err: bytes) -> None:
        if key == "deliver send" and code == 3:
            act = ("note",) if "HELD" in last else ("alarm", "conflict" if "CONFLICT" in last else "control")
        elif key == "deliver send" and code == 4:
            return                                      # send() raises "control" once, naming the folder (LD7, R5)
        elif key == "drain" and code == 4:
            act = ("note",) if "the lease ends at" in last else ("alarm", "drain")
        else:
            act = D[key].get(code, ("crash",))
        if act[0] == "ok":          # LX3 (R15: the ok class of D; budget 0, 3-6): its alarms end; unreachable: R13
            for k, v in list(self.alarms.items()):
                if (k == "unreachable" and key == "fetch" and v.get("pass", 0) < self.npass) \
                        or (k != "unreachable" and v["program"] == key):
                    self.end_alarm(k)
        what, akey = act[0], (act[1] if len(act) > 1 else "")
        if what == "ok":
            if key == "content":
                self.content_alarms(last)
            return
        if what == "note":
            self.log(f"note: {key} exit {code}: {last}")
        elif what == "alarm":
            # R21 (LX3): deliver send's CONFLICT never ends by itself, as content's "conflict" does not
            self.alarm(akey, f"{key} exit {code}: {last}",
                       None if akey == "conflict" else "fetch" if akey == "unreachable" else key)
        elif what == "crash":
            tail = printable(err.decode("utf-8", "replace").strip().replace("\n", " | ")[-200:])
            self.alarm(f"{key} crashed", f"exit {code}: {last or tail}", key)
        elif what == "login":                           # LX0, LX2: nothing connects while HOLD_CONNECT stands
            create_only(self.f["HOLD_CONNECT"], canon({"code": code, "last": last, "program": key}))
            self.alarm("login", f"{key} exit 6: {last}; HOLD_CONNECT written: nothing connects until a person "
                                f"removes home/loop/HOLD_CONNECT")
        elif what == "hold":                            # LX5 (R1): the local stages hold, the fetch goes on
            create_only(self.f["HOLD_LOCAL"], canon({"code": code, "last": last, "program": key}))
            self.alarm(HOLD_KEY[key], f"HOLD_LOCAL: {key} exit {code}: {last}; every pass runs clock, fetch and "
                                      f"custody only until a person removes home/loop/HOLD_LOCAL", key)
            raise Hold()
        elif what == "stop":                            # LX4: fetch's or custody's own STOP class
            self.alarm(key, f"STOP ({code}): {last}", key)
            raise End(code, f"loop: STOP ({code}): {key}: {last}")

    def content_alarms(self, last: str) -> None:
        """LA1 and D's content cell: set_aside, refused and conflicts above 0 in the last line of an exit 0."""
        for rx, key in ((r"set_aside (\d+)", "set_aside"), (r"\((\d+) refused\)", "refused"),
                        (r"conflicts (\d+)", "conflict")):
            m = re.search(rx, last)
            if m and int(m.group(1)) > 0:
                self.alarm(key, last)

    # ---- the start ------------------------------------------------------------------------------------------------
    def manifest_fault(self) -> str:
        """LS9: every file named in MANIFEST.sha256 at the sha256 the list names."""
        m = TREE / "MANIFEST.sha256"
        try:
            rows = m.read_text(encoding="ascii").splitlines()
        except (OSError, ValueError) as e:
            return f"MANIFEST.sha256 cannot be read ({e})"
        n = 0
        for row in rows:
            x = ROW.fullmatch(row)
            if not x:
                continue
            n += 1
            p = TREE / x.group(2)
            try:
                if sha_file(p) != x.group(1):
                    return f"{x.group(2)} is not the file MANIFEST.sha256 names (sha256)"
            except OSError:
                return f"{x.group(2)}, named in MANIFEST.sha256, cannot be read"
        return "" if n else "MANIFEST.sha256 names no file"

    def chess_fault(self) -> str:
        """LS7: the Python of content.py and publish.py imports python-chess 1.11.2."""
        try:
            r = subprocess.run([self.chess_py, "-I", "-B", "-c", "import chess; print(chess.__version__)"],
                               stdin=subprocess.DEVNULL, capture_output=True, timeout=300)
        except (OSError, subprocess.TimeoutExpired) as e:
            return f"--chess-python {self.chess_py} cannot be run ({e})"
        if r.returncode != 0 or last_line(r.stdout) != CHESS:
            return f"--chess-python {self.chess_py} does not give python-chess {CHESS} (exit {r.returncode}, " \
                   f"{last_line(r.stdout) or last_line(r.stderr)})"
        return ""

    def frozen_now(self) -> dict:
        a, pipe = self.a, Path(self.a.pipeline)
        files = {"1 MANIFEST.sha256": TREE / "MANIFEST.sha256", "2 plan": a.plan, "3 fetch config": a.fetch_config,
                 "4 config": a.config, "5 nnloop/filterqc.py": pipe / "nnloop" / "filterqc.py",
                 "5 nnloop/datagen_uci.py": pipe / "nnloop" / "datagen_uci.py",
                 "5 nnloop/common.py": pipe / "nnloop" / "common.py", "6 tables list": a.tables_list,
                 "7 converter": a.converter}
        return {k: {"path": str(Path(p).resolve()), "sha256": sha_file(Path(p))} for k, p in files.items()}

    def frozen_fault(self) -> str:
        """HL3: FROZEN.json at the first start; at every later start the same seven inputs."""
        try:
            now = self.frozen_now()
        except OSError as e:
            return f"a frozen input cannot be read ({e})"
        p = self.f["FROZEN.json"]
        if not p.exists():
            create_only(p, canon({"files": now, "run": self.fp, "schema": 1}))
            self.log("FROZEN.json written: " + ", ".join(k + " " + v["sha256"][:12] for k, v in now.items()))
            return ""
        try:
            old = json.loads(p.read_bytes())
        except (OSError, ValueError) as e:
            return f"home/loop/FROZEN.json cannot be read ({e})"
        if not isinstance(old, dict) or old.get("run") != self.fp or not isinstance(old.get("files"), dict):
            return "home/loop/FROZEN.json is not this run's"
        for k, v in now.items():
            was = old["files"].get(k)
            if not isinstance(was, dict) or was.get("sha256") != v["sha256"]:
                return f"the frozen input {k} ({v['path']}) is not the file of the first start (sha256)"
        return ""

    def home_empty(self) -> bool:
        return not any(fn for s in QUIET for _dp, _dn, fn in os.walk(self.home / s))

    def take_header(self) -> None:
        """LS6: home/loop/RUN.json, the decoded wire/RUN.json.zz, create-only; its sha256 is the fingerprint."""
        p = self.f["RUN.json"]
        if p.exists():
            return
        try:
            data = zlib.decompress((self.home / "wire" / "RUN.json.zz").read_bytes())
        except (OSError, zlib.error) as e:
            self.log(f"note: wire/RUN.json.zz cannot be decoded yet ({e})")
            return
        if hashlib.sha256(data).hexdigest() != self.fp:
            self.alarm("header", "wire/RUN.json.zz is not this run's header (its sha256 is not the fingerprint)")
            raise End(3, "loop: STOP (3): the header wire/RUN.json.zz is not this run's")
        create_only(p, data)
        self.log("RUN.json written (the decoded header)")

    def lease_end_ms(self):
        try:
            return utc_ms(json.loads(self.f["RUN.json"].read_bytes())["lease_end_utc"])
        except (OSError, ValueError, KeyError, TypeError):
            return None

    # ---- the decision (E) ------------------------------------------------------------------------------------------
    def sent(self) -> list:
        """[(k, control)] of deliver/sent, by k."""
        got = []
        if self.sent_dir.is_dir():
            for e in self.sent_dir.iterdir():
                m = CONTROL.fullmatch(e.name)
                if m:
                    try:
                        got.append((int(m.group(1)), json.loads(e.read_bytes())))
                    except (OSError, ValueError):
                        pass
        return sorted(got, key=lambda x: x[0])

    def seen_k(self):
        d = self.home / "control"
        ks = [int(m.group(1)) for e in d.iterdir() if (m := CONTROL.fullmatch(e.name))] if d.is_dir() else []
        return max(ks) if ks else None

    def effect(self, c: dict, made: Path | None = None) -> str:
        """make_control.effect's rule (R3), from the control, the plan and, for reduced_target, its evidence: in
        deliver/sent/, or (R20) in `made`, the control's own made/ folder, before it was sent."""
        kind, dec = c.get("kind"), c.get("decision")
        if kind == "fence":
            return "fence"
        if kind == "matches" or dec == "UNQUALIFIED":
            return "none"
        if dec in ("REACHED", "STOP", "SHORT"):
            return "fence"
        if dec in ("SELF_PLAY", "SELF_PLAY_AND_MATCHES"):
            return "schedule"
        oc = self.plan.get("owner_choice")
        oc = oc if isinstance(oc, dict) else {}
        act = oc.get("action")
        if act == "stop":
            return "fence"
        if act == "self_play":
            return "schedule"
        try:
            ev = json.loads(((made or self.sent_dir) / f"EVIDENCE.{c.get('evidence')}.json").read_bytes())
            red = ev.get("reduced") or {}
        except (OSError, ValueError, AttributeError):
            red = {}
        return "schedule" if red.get("covered") or oc.get("if_uncovered") == "self_play" else "fence"

    def folders(self) -> list:
        """The decision folders, oldest first (decisions/<k>, then <k>.2, <k>.3, ...)."""
        if not self.dec.is_dir():
            return []
        fs = [e for e in self.dec.iterdir() if e.is_dir() and re.fullmatch(r"\d+(\.\d+)?", e.name)]
        return sorted(fs, key=lambda e: tuple(int(x) for x in e.name.split(".")))

    def made_control(self, folder: Path):
        cs = [e for e in (folder / "made").iterdir() if CONTROL.fullmatch(e.name)] if (folder / "made").is_dir() else []
        return cs[0] if len(cs) == 1 else None

    def pending(self):
        """R4, R5: the oldest made folder whose control is not in deliver/sent/ with the same bytes, else None."""
        for f in self.folders():
            c = self.made_control(f)
            if c is None or (f / "REFUSED").exists():
                continue
            s = self.sent_dir / c.name
            if not s.exists() or f == self.resend:
                if s.exists() and s.read_bytes() != c.read_bytes():
                    continue                            # another control was sent under this k: not this folder's
                return f
        return None

    def new_folder(self, k: int) -> Path:
        n, f = 1, self.dec / str(k)
        while f.exists():
            n += 1
            f = self.dec / f"{k}.{n}"
        f.mkdir(parents=True)
        return f

    def make(self, kind: str, with_state: bool):
        """make_control into a new decision folder from this pass's report; the folder, or None when refused."""
        if self.report is None:
            return None
        k, rb = self.report[0], self.report[1]
        # R5: a refused make is tried again only when its inputs can have changed: a new state (pilot_decision,
        # fence), or a new sent or seen control (target: make_control's M5 waits for the pilot decision's acceptance)
        key = (kind, len(self.sent()), self.seen_k()) if kind == "target" else (kind, k)
        if self.refused_k == key:
            return None
        f = self.new_folder(k)
        create_only(f / "report.json", rb)
        self.sent_dir.mkdir(parents=True, exist_ok=True)   # make_control's --accepted: empty before the first send
        args = ["--report", f / "report.json", "--header", self.f["RUN.json"], "--policy", self.plan_path,
                "--accepted", self.sent_dir, "--kind", kind, "--out", f / "made"]
        if with_state:
            args += ["--state", self.home / "state" / f"state.{k}.json", "--pilot", self.home / "pilot" / "pilot.json"]
        code, _last, _out = self.step("make_control", args)
        if code != 0:
            self.refused_k = key
            return None
        return f

    def connect_ok(self) -> bool:
        """LX2, R14: nothing connects while home/loop/HOLD_CONNECT stands (looked at before every such program)."""
        return not self.f["HOLD_CONNECT"].exists()

    def newest_state_k(self):
        d = self.home / "state"
        ks = [int(m.group(1)) for e in d.iterdir() if (m := re.fullmatch(r"state\.(\d+)\.json", e.name))] \
            if d.is_dir() else []
        return max(ks) if ks else None

    def send(self, f: Path) -> None:
        if not self.connect_ok():
            return                                      # LX2: no send while the hold stands; it waits in its folder
        code, last, _out = self.step("deliver send", ["--home", self.home, "--fingerprint", self.fp, "--config",
                                                      self.a.fetch_config, "--made", f / "made"])
        if code == 0:
            self.resend = None
        elif code == 4:                                 # LD7, R5: the folder stays as it lies and is not sent again
            create_only(f / "REFUSED", canon({"code": code, "last": last}))
            self.alarm("control", f"deliver send refused {f.name}/made (exit 4: {last}); the decision is made again "
                                  f"from the newest state", "deliver send")
            self.resend = None
        elif code not in (2, 3):                        # R4, R19: after 6, 7, 8 or a crash the same folder is sent
            self.resend = f                             # again (after a 6 once a person removed HOLD_CONNECT, LX2)

    def decide(self) -> None:
        sent = self.sent()
        fence_sent = any(self.effect(c) == "fence" for _k, c in sent)
        p = self.pending()
        if p is not None:                               # LD6, LD7: never a second folder while one waits
            self.send(p)
            return
        if fence_sent:                                  # LD9
            return
        if self.f["FENCE_REQUEST"].exists():            # LD8
            if self.report is None:
                self.alarm("fence", "fence waits: no report yet")
                return
            f = self.make("fence", with_state=False)
            if f is not None:
                self.end_alarm("fence")
                self.send(f)
            return
        if self.report is None:
            return
        _k, _rb, outcome, _code, with_pilot = self.report
        try:
            reason = printable(str(json.loads(self.report[1]).get("reason", "")), 200)
        except (ValueError, AttributeError):
            reason = ""
        if not sent:                                    # LD3: the pilot decision, once
            if not with_pilot:
                return                                  # LD2: waiting for the pilot is the normal first hour
            f = self.make("pilot_decision", with_state=True)
            if f is None:
                return
            c = self.made_control(f)
            eff = self.effect(json.loads(c.read_bytes()), c.parent) if c is not None else "none"     # R20
            if outcome == "UNQUALIFIED":
                self.alarm("unqualified", f"{reason}; nothing starts by script")
            elif eff == "fence":
                self.alarm("day stops", f"{outcome}: {reason}")
            self.send(f)
            return
        pilots = [c for _k, c in sent if c.get("kind") == "pilot_decision"]
        if not pilots:
            return
        if outcome == "REACHED":                        # LD4: the target, once (then the fence's effect is sent)
            f = self.make("target", with_state=True)
            if f is not None:
                self.send(f)
        elif outcome in ("OWNER_CHOICE", "STOP", "SHORT") and self.effect(pilots[-1]) == "schedule":
            self.alarm("behind", f"{outcome}: {reason}")    # LD5: never a control by script

    # ---- the state's alarms (F) --------------------------------------------------------------------------------------
    def state_alarms(self, last: str) -> None:
        m = STATE_LINE.fullmatch(last)
        if not m:
            self.log(f"note: state's last line is not 'state: k K, now_s N, c4_rows C; pilot: TEXT': {last}")
            return
        k, now_s, c4, pilot = int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4)
        self.state = (k, now_s, c4, pilot)
        try:                                            # LA2: the file names the partial rounds
            st = json.loads((self.home / "state" / f"state.{k}.json").read_bytes())
            pr, pg = int(st.get("partial_rounds", 0)), int(st.get("partial_games", 0))
        except (OSError, ValueError, TypeError, AttributeError):
            pr = pg = 0
        if pr > 0:
            self.alarm("partial", f"partial_rounds {pr}, partial_games {pg} (state {k})")
        else:
            self.end_alarm("partial")
        if pilot.startswith(PILOT_STOP):                # LA3
            self.la5_n = 0
            self.alarm("pilot", pilot)
        elif pilot.startswith("waiting:") and "no publish moment" in pilot:     # LA5, agreed wording
            standing = self.alarms.get("pilot")
            if standing is not None and standing["text"] != printable(pilot):
                self.end_alarm("pilot")
                self.la5_n = 0
            self.la5_n += 1
            if self.la5_n >= 3:
                self.alarm("pilot", pilot)
        else:
            self.la5_n = 0
            self.end_alarm("pilot")
        effs = [self.effect(c) for _k, c in self.sent()]
        sched = "schedule" in effs and "fence" not in effs     # LA4, R22: a schedule in force; a sent fence ends it
        if sched and not (self.home / "DRAIN.json").exists():                    # LA4
            if self.stall_c4 is None or c4 > self.stall_c4:
                if self.stall_c4 is not None:
                    self.end_alarm("stalled")
                self.stall_c4, self.stall_n = c4, 1
            else:
                self.stall_n += 1
            if self.stall_n >= self.a.stall_passes:
                self.alarm("stalled", f"c4_rows {c4} has not grown over {self.stall_n} passes; credit: "
                                      f"{self.last.get('credit', (None, ''))[1]}")
        else:
            self.stall_c4, self.stall_n = None, 0

    # ---- one pass ---------------------------------------------------------------------------------------------------
    def one_pass(self):
        """One pass (LP1); the exit code when the day closed, else None."""
        self.npass, self.lines, self.report = self.npass + 1, {}, None
        if self.f["STOP"].exists():
            raise End(0, "loop: stopped by STOP")
        h, hf = self.home, self.fp
        base = ["--home", h, "--fingerprint", hf]
        if self.connect_ok():
            self.end_alarm("login")                     # LX2: a person removed HOLD_CONNECT
        hl = self.f["HOLD_LOCAL"].exists()
        header = (h / "wire" / "RUN.json.zz").exists()
        drained = (h / "DRAIN.json").exists()
        if header:
            self.take_header()
        try:
            if self.connect_ok():
                self.step("clock measure", base + ["--config", self.a.fetch_config])
            before, t0, ran, fetched = self.listing(("wire", "custody")), None, False, False
            if self.connect_ok():
                t0 = time.monotonic()
                self.step("fetch", base + ["--config", self.a.fetch_config])
                ran, fetched = not header, True         # LS6: fetch is the c3 part's last program then
            if header:
                t0 = t0 if t0 is not None else time.monotonic()
                self.step("custody", base)
                ran = True
            if ran and t0 is not None:
                self.pass_line("c3", t0, self.moved(before, self.listing(("wire", "custody"))), [])
            if not header:
                if (h / "wire" / "RUN.json.zz").exists():
                    self.take_header()
                return None
            if hl:
                return None                             # LX5: clock, fetch and custody only
            if not self.probe_ok and self.probe_again and self.connect_ok():     # LS5, R7
                code, _l, _o = self.step("deliver probe", base + ["--config", self.a.fetch_config])
                if code == 0:
                    self.probe_ok = True
                    self.log(f"probe passed (run {self.fp})")
                elif code in (3, 4):
                    self.probe_again = False
            before, t0 = self.listing(("content", "stage", "rounds")), time.monotonic()
            opn = ["--openings", self.a.openings] if self.a.openings else []
            self.step("content", base + ["--converter", self.a.converter] + opn, py=self.chess_py)
            self.step("credit", base)
            self.step("publish", base + ["--config", self.a.config, "--pipeline", self.a.pipeline, "--tables",
                                         self.a.tables, "--tables-list", self.a.tables_list, "--converter",
                                         self.a.converter] + opn, py=self.chess_py)
            self.pass_line("c4", t0, self.moved(before, self.listing(("content", "stage", "rounds"))),
                           self.new_reports())
            self.step("deliver observe", base)
            code, last, _o = self.step("state", base)
            sk = None
            if code == 0:
                self.state = None
                self.state_alarms(last)
                sk = self.state[0] if self.state is not None else None
            elif code != 9:
                sk = self.newest_state_k()              # R12: LD1 literally
            sf = h / "state" / f"state.{sk}.json"
            if sk is not None and sf.is_file():
                pj = h / "pilot" / "pilot.json"
                with_pilot = pj.is_file()
                bcode, _bl, bout = self.step("budget", [self.plan_path, sf] + ([pj] if with_pilot else []))
                if bcode in (0, 3, 4, 5, 6):
                    try:
                        outcome = json.loads(bout).get("outcome")
                    except (ValueError, AttributeError):
                        outcome = None
                    self.report = (sk, bout, outcome, bcode, with_pilot)
                    self.newest_report = self.report
            elif self.f["FENCE_REQUEST"].exists() and self.newest_report is not None:
                self.report = self.newest_report        # LD8: a person's fence from the newest report
            self.decide()
            if self.a.once:
                return None
            if drained:                                 # LE3: the first whole pass after DRAIN.json
                if (self.lines.get("c3") == 0 and self.lines.get("c4") == 0 and self.last.get("credit", (1,))[0] == 0
                        and self.last.get("publish", (1,))[0] == 0
                        and all(self.last.get(p, (1,))[0] == 0 for p in ("custody", "content"))):     # R24
                    c4 = self.state[2] if self.state else 0
                    self.hourly("end")
                    raise End(0, f"loop: the day is closed at home; c4_rows {c4}")
            elif self.f["DECLARED_STOP"].exists():       # LE2
                self.step("drain", base + ["--why", "declared stop"])
            else:
                end = self.lease_end_ms()
                past = self.upper is not None and end is not None and self.upper >= end
                if (h / "wire" / "TERMINAL.jsonl.zz").exists() or past:    # LE1
                    wait = self.drain_waits(fetched, past)                    # R23
                    if wait:
                        self.log(f"note: drain waits: {wait}")
                    else:
                        self.step("drain", base + ["--why", "lease ended"])
        except Hold:
            return None
        return None

    def drain_waits(self, fetched: bool, past: bool) -> str:
        """R23: drain.py is called only after a fetch pass that left no member still receiving (drain.py's own
        contract); a server given back is still drained at the lease's end (LE1: its fetch exits 7 then). Why the
        "lease ended" drain waits in this pass, or "" when it may be called."""
        if not fetched:
            return "no fetch ran in this pass (HOLD_CONNECT)"
        code, last = self.last.get("fetch", (None, ""))
        if code == 7 and past:
            return ""
        if code != 0:
            return f"fetch exited {code} in this pass"
        m = FETCH_LEFT.search(last)
        if m is None:
            return f"fetch's last line names no partial, incomplete and budget binds: {last}"
        if m.group(1) != "0" or m.group(2) != "0" or m.group(3) != "no":
            return f"fetch still receives: partial {m.group(1)}, incomplete {m.group(2)}, budget binds {m.group(3)}"
        return ""

    def new_reports(self) -> list:
        """LP4: the rounds with rounds/r<NNNN>/report.json named in no earlier line of this run, rising."""
        d, have = self.home / "rounds", set()
        if d.is_dir():
            for e in d.iterdir():
                m = ROUND_DIR.fullmatch(e.name)
                if m and (e / "report.json").is_file():
                    have.add(int(m.group(1)))
        new = sorted(have - self.named)
        self.named |= set(new)
        return new

    def read_journal(self) -> None:
        """The rounds already named in this run's pass lines (LP4 after a restart)."""
        p = self.f["journal.jsonl"]
        if not p.exists():
            return
        for raw in p.read_bytes().split(b"\n"):
            try:
                r = json.loads(raw)
            except ValueError:
                continue
            if isinstance(r, dict) and r.get("run") == self.fp and r.get("t") == "pass" \
                    and isinstance(r.get("new_reports"), list):
                self.named |= {x for x in r["new_reports"] if type(x) is int}

    def resend_at_start(self) -> None:
        """R4: the newest sent control with a visible effect and not seen: its made folder is sent once more."""
        sent, seen = self.sent(), self.seen_k()
        if not sent or (seen is not None and seen >= sent[-1][0]) or self.effect(sent[-1][1]) == "none":
            return
        name = f"CONTROL.{sent[-1][0]}.json"
        for f in self.folders():
            c = self.made_control(f)
            if c is not None and c.name == name and c.read_bytes() == (self.sent_dir / name).read_bytes():
                self.resend = f
                return

    # ---- the loop ---------------------------------------------------------------------------------------------------
    def run(self) -> int:
        self.ld.mkdir(parents=True, exist_ok=True)
        fd = take_lock(self.ld / "LOCK")
        if fd is None:
            return self.out(8, "loop: another loop holds home/loop/LOCK; nothing written", log=False)
        try:
            return self.locked()
        finally:
            os.close(fd)

    def locked(self) -> int:
        if self.f["STOP"].exists():                     # R8: a person removes home/loop/STOP to start
            return self.out(0, "loop: stopped by STOP")
        first = not self.f["FROZEN.json"].exists()
        why = self.manifest_fault() or self.chess_fault()
        if not why:
            try:
                plan = json.loads(self.plan_path.read_bytes())
                self.plan = plan if isinstance(plan, dict) else {}
            except (OSError, ValueError) as e:
                why = f"the plan {self.plan_path} cannot be read ({e})"
        why = why or self.frozen_fault()
        if why:
            return self.out(4, f"loop: start check: {why}; no program started")
        self.rebuild_alarms()
        self.read_journal()
        self.probe_ok = f"probe passed (run {self.fp})" in (self.f["loop.log"].read_text(encoding="ascii", errors="replace")
                                                             if self.f["loop.log"].exists() else "")
        empty = self.home_empty()
        append(self.f["journal.jsonl"], canon({"empty": empty, "run": self.fp, "t": "start",
                                               "why": "first start" if first else "start again"}))
        if first and not empty:
            self.log("the pilot of this home cannot qualify: the home was not empty at the first start")
        self.log(f"start: run {self.fp[:12]}, home {self.home}, empty {empty}, pass every {self.a.pass_seconds} s")
        self.resend_at_start()
        self.hourly("start")
        try:
            while True:
                began = time.monotonic()
                self.one_pass()
                if self.a.once:
                    return self.out(0, "loop: one pass done (--once)")
                hour = None if self.upper is None else self.upper // 3600000
                self.quiet_passes += 1
                if hour is not None and self.hour is None:
                    self.hour = hour                    # the first reading: the start line stands for it
                elif (hour is not None and hour != self.hour) or (hour is None and self.quiet_passes >= 60):
                    self.hour = hour
                    self.hourly("hour")
                while time.monotonic() < began + self.a.pass_seconds:
                    if self.f["STOP"].exists():
                        raise End(0, "loop: stopped by STOP")
                    time.sleep(min(1.0, max(0.01, began + self.a.pass_seconds - time.monotonic())))
        except End as e:
            if not self.a.once and not e.line.startswith("loop: the day is closed"):
                self.hourly("end")
            return self.out(e.code, e.line)


def main() -> int:
    argv = sys.argv[1:]
    for bad in ("--policy", "--accepted"):
        if any(x == bad or x.startswith(bad + "=") for x in argv):
            print(f"loop: a wrong call: {bad} is not the loop's (it gives make_control --accepted <home>/deliver/sent; "
                  f"--plan is make_control's --policy); nothing written")
            return 2
    ap = argparse.ArgumentParser(allow_abbrev=False, description="the home loop of the server day")
    for name in ("--home", "--fingerprint", "--fetch-config", "--config", "--pipeline", "--tables", "--tables-list",
                 "--converter", "--chess-python", "--plan"):
        ap.add_argument(name, required=True)
    ap.add_argument("--openings")
    ap.add_argument("--pass-seconds", type=int, required=True)
    ap.add_argument("--stall-passes", type=int, required=True)
    ap.add_argument("--once", action="store_true")
    try:
        a = ap.parse_args(argv)
    except SystemExit:
        return 2
    if not HEX64.fullmatch(a.fingerprint) or a.pass_seconds < 0 or a.stall_passes < 1 or not Path(a.home).is_dir():
        print("loop: a wrong call: --fingerprint 64 hex digits, --pass-seconds 0 or more, --stall-passes 1 or more, "
              "--home an existing folder; nothing written")
        return 2
    return Loop(a).run()


if __name__ == "__main__":
    sys.exit(main())
