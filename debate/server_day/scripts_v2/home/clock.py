"""Opus 2026-11-25, v16: the home CLOCK (tmp/opus_scratch/clock/KNOWN_ANSWERS_clock_by_opus.md with its ADDENDA 1 to 8;
1 to 6 read by Fable before this code, 8 is her F-CLOCK-1). Standard library only; nothing is installed.
v17 (26 Nov, CL1 to CL5 of tmp/opus_scratch/v17/KNOWN_ANSWERS_v17_server_by_opus.md, read by Fable 09:15): every look
line gains mono0, the steady clock read right BEFORE the get; reading() and lag_s() give the MEASURED bound of how far
server_now runs behind the server's clock, as exact decimals (home/state.py's "now" is server_now + lag_s).

    clock.py measure --home DIR --fingerprint HEX64 --config FILE

WHY: the PC's clock runs about 25,178 s (7 hours) AHEAD of real UTC (measured 25 Nov). Home's DECISIONS take the
SERVER's time instead: drain's "lease ended" and "source gone since T" and deliver's D check call server_now or
server_text below. STAMPS for people stay on the PC's clock; tests/test_clock_use.py allow-lists each one.
THE SERVER'S TIME: the server's guard (run/guard.py G11) writes ROOT/CLOCK.json {n, run_fingerprint, schema 1, state,
utc_ms} at most once a minute; its utc_ms is the EARLIEST of the guard's three clocks (a UTC jump ahead never enters).
A LOOK is ONE get of the root's CLOCK.json through fetch.py's own Transport (imported, not copied: the same pinned host
key, the same codes): the root is listed, the get is given the listed length (a file that grew between the two is
fetched once more), into home/clock/look.part, which is read and removed. Each look appends ONE line to
home/clock/journal.jsonl in one write of whole bytes (a journal whose last line was cut gets a line end first, S2):
{"t": "clock", "run", "look": 1|2, "n", "utc_ms", "state", "mono0", "mono", "wall", "impl", "platform", "ok", "why"}.
mono0 is read right BEFORE the get (CL1, v17); mono and wall AFTER the get returned and the record was parsed (M1c: a
slow get makes the line late, never early); a line without mono0, or with mono0 above mono, is not the record (C8). One
measure at a time on a home folder: an OS lock on home/clock/LOCK (else exit 8, nothing done); look.part is removed
before every get (S1: a killed measure's leftover never joins a new get). measure makes home/clock/ in any existing
folder it is given (it runs before the first fetch, so it cannot know the folder is this run's home): lines in a wrong
folder are read by no decider of the right home, which then refuses (the safe side).
  M2  No line of this run is accepted now (the helper refuses): TWO looks, clock_second_look_s apart (the config's,
      default 70); the second is ok when the pair passes THE PAIR RULES.
  M7d (ADDENDUM 8, Fable's F-CLOCK-1) A look whose n EQUALS the accepted line's is the SAME record and never becomes
      an accepted line: utc_ms changed, exit 9; utc_ms equal and at most 90 s behind the line extrapolated, its line
      ok false and exit 0 ("clock: unchanged"; the accepted line stays and server_now runs on from it); more than
      90 s behind, the older branch below (n unchanged at the second look: exit 9).
  M7  A line is accepted: ONE look. After its M3 to M6, M7b (n smaller than the line's) and M7d, ONLY its distance x
      from the line extrapolated (the line's utc_ms + 1000 * (the look's mono - the line's mono)) decides (R1): ok when it
      is at most 90 s older and at most 120 s newer. More than 90 s OLDER (the guard may have stopped writing), or
      more than 120 s NEWER (M7c: one reading of the other machine is not believed on the unsafe side): that look's
      line is ok false and a second look follows, judged against it by THE PAIR RULES. When they fail, the old line
      stays the accepted one (the helper skips ok-false lines, C11).
  THE PAIR RULES, in this order (one text a case): the second look's own M3 to M6; n advanced (else "does not write",
      or "smaller": the root was replaced); M2c |(utc_ms2 - utc_ms1) / 1000 - (mono2 - mono1)| at most 90 s (else
      "not steady"); M2b utc_ms2 greater than utc_ms1 (else "went back"). M2b is a rule of a PAIR only (R1).
  M3 no CLOCK.json, M4 not the guard's record, M5 another run's, M6 state hold: exit 9, no ok line.
  M10 (the runbook): run measure before each fetch pass; its exit 9 is a NOTE, the fetch pass runs all the same.
      fetch needs no clock and never calls measure; measure never calls fetch.
THE HELPER: server_now(home, fingerprint) (seconds) and server_text(home, fingerprint) (YYYY-MM-DDTHH:MM:SSZ of the
floor) read the journal only and never write. The newest ok line of this run decides (C8: a line that is not the exact
record, an unfinished last one too, is skipped: it can lose a reading, never make a time; C11: ok-false lines after
it do not matter): its utc_ms / 1000 + (the monotonic clock now - its mono). ClockRefused (its text, for the decider
to name) when: there is no such line (C4, C5); its impl or platform is not this process's (C6); the monotonic clock
now is below its mono (C2: the PC restarted); its wall and monotonic clocks moved apart by more than 120 s (C3: the
PC restarted or its clock was set; sleep and hibernate fall under C2 or C3, whichever way the tick behaves there).
The PC's own offset never matters (C1), only that its two clocks stayed together; a line 6 hours old is used (C12).
WHICH SIDE: server_now runs BEHIND the server's clock, never ahead (C10). By how much is MEASURED (v17, CL2): lag_s =
mono_j - mono0_p, j the accepted line and p the LATEST earlier look line of this run that saw a SMALLER n (an int), with
the same impl and platform, mono0_p <= mono_j, and its wall and steady clocks moved together with j's (C3's 120 s).
Record n_j was written after look p began its get (p read n_p), so its age at mono_j is below lag_s: the server's clock
lies in [server_now, server_now + lag_s]. No such p: ClockRefused (no lag bound; home/state.py then writes no state).
What C3's 120 s cannot see (Fable's read, 26 Nov): a steady clock that stood still for under two minutes while the
wall clock ran would leave the server's clock up to that much above server_now + lag_s. Windows' tick count (the
GetTickCount64 behind time.monotonic, checked on the home PC 26 Nov) counts sleep as Microsoft documents it (not
measured here), so a stopped steady clock is not expected there.
reading() gives both as exact decimals of the journal's text. drain and deliver keep server_now: they accept "lease
ended" and "source gone since T" late, never early; deliver may let a control leave a little after the real cutoff,
which is harmless: the server's guard takes no control after the cutoff by its own clocks (guard.py, one_pass).
Exit codes of measure: 0 an ok line written, or the same record again (M7d) and the accepted line stays; 2 a wrong
call; 4 a home file that cannot be read or written; 6 the host key or the login failed; 7 the server cannot be
reached; 8 another measure holds home/clock/LOCK; 9 no ok line, the text says why. The last line: "clock: ok n <n>, the
server's time <UTC> (utc_ms <ms>), offset <s> s (the server's minus the PC's; a note for people)", "clock: unchanged
n <n> (the same record as the accepted line, which stays), the server's time <UTC> by it extrapolated, offset <s> s
(...)" or "clock: STOP (<code>): <why>".
"""
import argparse
import json
import math
import os
import re
import sys
import time
from decimal import Decimal, localcontext
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fetch as F  # noqa: E402   the connection; it puts run/ on the path for worker
from worker import SlotLock, Stop, canon, parse_canon, same  # noqa: E402

HEX64 = re.compile(r"[0-9a-f]{64}")
CLOCK_KEYS = ["n", "run_fingerprint", "schema", "state", "utc_ms"]
LINE_KEYS = sorted(["t", "run", "look", "n", "utc_ms", "state", "mono0", "mono", "wall", "impl", "platform", "ok",
                    "why"])
STATES = ("play", "dispatch_end", "cutoff", "hold")
UTC_MS_MIN, UTC_MS_MAX = 1_700_000_000_000, 4_100_000_000_000          # M4
OLDER_S, NEWER_S, AGREE_S, STEADY_S = 90.0, 120.0, 90.0, 120.0          # M7, M7c, M2c, C3


class ClockRefused(Exception):
    """The helper gives no time; the text says why (the decider names it)."""


def impl() -> str:
    return time.get_clock_info("monotonic").implementation


def utc_text(s: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(math.floor(s)))


def number(v) -> bool:
    return type(v) in (int, float) and math.isfinite(v)


def _pairs(pairs):
    d = {}
    for k, v in pairs:
        if k in d:
            raise ValueError(f"the key {k!r} stands twice")
        d[k] = v
    return d


def _no_constant(text):
    raise ValueError(f"not a number: {text}")


def parse_line(raw: bytes):
    """C8: the exact journal record (canonical bytes; mono0, mono and wall are the only numbers that may have a
    fraction; mono0 not above mono, CL1), or None."""
    try:
        obj = json.loads(raw.decode("ascii"), object_pairs_hook=_pairs, parse_constant=_no_constant)
        if not isinstance(obj, dict) or sorted(obj) != LINE_KEYS or canon(obj) != raw + b"\n":
            return None
    except ValueError:                                  # UnicodeDecodeError is a ValueError
        return None
    if not (obj["t"] == "clock" and type(obj["run"]) is str and HEX64.fullmatch(obj["run"])
            and type(obj["look"]) is int and obj["look"] in (1, 2) and number(obj["mono"]) and number(obj["wall"])
            and number(obj["mono0"]) and obj["mono0"] <= obj["mono"]
            and type(obj["impl"]) is str and type(obj["platform"]) is str and type(obj["ok"]) is bool
            and (obj["why"] is None or type(obj["why"]) is str)):
        return None
    if obj["ok"] and not (type(obj["n"]) is int and obj["n"] >= 1 and type(obj["utc_ms"]) is int
                          and UTC_MS_MIN <= obj["utc_ms"] <= UTC_MS_MAX and obj["state"] in STATES[:3]):
        return None
    return obj


def _accepted(home, fingerprint: str, mono, wall):
    """(the deciding line, the monotonic clock now, the journal's exact records in order, the deciding line's place
    among them), or ClockRefused: C2 to C6, C8, C11."""
    j = Path(home) / "clock" / "journal.jsonl"
    try:
        data = j.read_bytes()
    except FileNotFoundError:
        raise ClockRefused("no clock line of this run: run clock.py measure first") from None
    except OSError as e:
        raise ClockRefused(f"home/clock/journal.jsonl cannot be read ({e})") from None
    best, lines, at = None, [], -1
    for raw in data.split(b"\n")[:-1]:                  # only lines with their line end: a cut last line is skipped
        rec = parse_line(raw)
        if rec is not None:
            lines.append(rec)
        if rec is not None and rec["ok"] and rec["run"] == fingerprint:
            best, at = rec, len(lines) - 1              # appended in time order: the last one is the newest
    if best is None:
        raise ClockRefused("no clock line of this run: run clock.py measure first")
    if best["impl"] != impl() or best["platform"] != sys.platform:
        raise ClockRefused(f"the clock line was measured with the monotonic clock {best['impl']} on {best['platform']};"
                           f" this process has {impl()} on {sys.platform}: run clock.py measure with this Python")
    m, w = mono(), wall()
    if m < best["mono"]:
        raise ClockRefused("the PC restarted since the last clock line: run clock.py measure again")
    if abs((w - best["wall"]) - (m - best["mono"])) > STEADY_S:
        raise ClockRefused(f"the PC restarted or its clock was set (its wall clock moved {w - best['wall']:.1f} s "
                           f"while its steady clock moved {m - best['mono']:.1f} s): run clock.py measure again")
    return best, m, lines, at


def accepted(home, fingerprint: str, mono=time.monotonic, wall=time.time):
    """(the deciding line, the monotonic clock now), or ClockRefused: C2 to C6, C8, C11."""
    return _accepted(home, fingerprint, mono, wall)[:2]


def exact(x) -> Decimal:
    """A number of the journal exactly as its text stands (a float's shortest form, which canon wrote)."""
    return Decimal(repr(x)) if type(x) is float else Decimal(x)


def reading(home, fingerprint: str, mono=time.monotonic, wall=time.time):
    """(server_now, lag_s, the deciding line), both exact decimals (CL2): the server's clock now lies in
    [server_now, server_now + lag_s]. ClockRefused as server_now's, and when no earlier look gives a lag bound."""
    best, m, lines, at = _accepted(home, fingerprint, mono, wall)
    with localcontext() as ctx:
        ctx.prec = 60                                   # every sum here is exact
        now = exact(best["utc_ms"]) / 1000 + (exact(m) - exact(best["mono"]))
        for p in reversed(lines[:at]):                  # the LATEST earlier look that saw an older record
            if (p["run"] == fingerprint and type(p["n"]) is int and p["n"] < best["n"] and p["impl"] == best["impl"]
                    and p["platform"] == best["platform"] and p["mono0"] <= best["mono"]
                    and abs((best["wall"] - best["mono"]) - (p["wall"] - p["mono"])) <= STEADY_S):
                return now, exact(best["mono"]) - exact(p["mono0"]), best
    raise ClockRefused("no look before the accepted line saw an older record: no lag bound (run clock.py measure "
                       "again; its next ok line has one)")


def lag_s(home, fingerprint: str, mono=time.monotonic, wall=time.time) -> Decimal:
    """CL2: the measured bound of how far server_now runs behind the server's clock, in seconds (exact)."""
    return reading(home, fingerprint, mono, wall)[1]


def server_now(home, fingerprint: str, mono=time.monotonic, wall=time.time) -> float:
    """The server's time in seconds, by the newest accepted clock line (never ahead of the server's clock, C10)."""
    rec, m = accepted(home, fingerprint, mono, wall)
    return rec["utc_ms"] / 1000 + (m - rec["mono"])


def server_text(home, fingerprint: str, mono=time.monotonic, wall=time.time) -> str:
    """C9: server_now's floor as YYYY-MM-DDTHH:MM:SSZ, the form of the package's UTC texts."""
    return utc_text(server_now(home, fingerprint, mono, wall))


class Measure:
    def __init__(self, home: Path, fp: str, cfg: dict):
        if not home.is_dir():
            raise Stop(2, f"--home {home} is not a folder")
        self.home, self.fp = home, fp
        self.cdir = home / "clock"
        self.cdir.mkdir(exist_ok=True)
        try:
            self.lock = SlotLock(self.cdir)
        except Stop:
            raise Stop(8, "another measure holds home/clock/LOCK: nothing done") from None
        try:
            gap = cfg.get("clock_second_look_s", 70)
            if type(gap) not in (int, float) or not math.isfinite(gap) or gap < 0:
                raise Stop(2, "the config's clock_second_look_s must be a number of seconds, not negative")
            self.gap = float(gap)
            self.journal, self.part = self.cdir / "journal.jsonl", self.cdir / "look.part"
            self.t = F.Transport(cfg, self.cdir)
        except BaseException:
            self.lock.release()
            raise

    def get(self):
        """The bytes of the root's CLOCK.json, or None when the root has none (M3)."""
        for _ in (1, 2):
            listed, _n = self.t.list("")
            if "CLOCK.json" not in listed:
                return None
            whole = listed["CLOCK.json"]
            try:
                self.part.unlink()                      # S1: a killed measure's (under the LOCK only a dead one's),
            except FileNotFoundError:                   # or this measure's own first try: every get starts at byte 0
                pass
            code, text, _silent = self.t.get("CLOCK.json", self.part, whole)
            if code == "long" or F.size(self.part) > whole:
                continue                                # replaced by a longer one between the listing and the get
            if code != 0:
                if code not in ("idle", "slow"):
                    F.judge(text)
                raise Stop(7, f"the get of CLOCK.json failed ({code}): {text.strip()[-200:]}")
            data = self.part.read_bytes()
            self.part.unlink()
            return data
        raise Stop(9, "CLOCK.json grew between the listing and the get twice in a row: no clock line")

    def look(self, k: int) -> dict:
        """One look, judged by M3 to M6; mono0 read right BEFORE the get (CL1), mono and wall AFTER the get returned
        and the record was parsed (M1c)."""
        mono0 = time.monotonic()
        data = self.get()
        rec, bad = None, None
        if data is None:
            bad = "no CLOCK.json yet (the server's guard has not started)"
        else:
            try:
                c = parse_canon(data, "CLOCK.json")
            except ValueError as e:
                c, bad = None, f"CLOCK.json is not the guard's record ({e})"
            if bad is None:
                if not (isinstance(c, dict) and sorted(c) == CLOCK_KEYS and same(c["schema"], 1)
                        and type(c["run_fingerprint"]) is str and type(c["n"]) is int and c["n"] >= 1
                        and type(c["utc_ms"]) is int and UTC_MS_MIN <= c["utc_ms"] <= UTC_MS_MAX
                        and c["state"] in STATES):
                    bad = ("CLOCK.json is not the guard's record (its five keys, schema 1, n a whole number >= 1, "
                           "utc_ms a whole number of milliseconds between 1.7e12 and 4.1e12, state one of four)")
                elif c["run_fingerprint"] != self.fp:
                    bad = f"CLOCK.json is of another run ({c['run_fingerprint'][:12]}..., not {self.fp[:12]}...)"
                else:
                    rec = c
                    if c["state"] == "hold":
                        bad = "the server's guard is in a HOLD (its clocks disagree): no clock line"
        mono, wall = time.monotonic(), time.time()
        return {"look": k, "rec": rec, "bad": bad, "mono0": mono0, "mono": mono, "wall": wall}

    def cut_tail(self) -> bool:
        try:
            with open(self.journal, "rb") as f:
                if f.seek(0, os.SEEK_END) == 0:
                    return False
                f.seek(-1, os.SEEK_END)
                return f.read(1) != b"\n"
        except FileNotFoundError:
            return False

    def write(self, lk: dict, ok: bool, why) -> None:
        r = lk["rec"]
        line = canon({"t": "clock", "run": self.fp, "look": lk["look"], "n": r["n"] if r else None,
                      "utc_ms": r["utc_ms"] if r else None, "state": r["state"] if r else None, "mono0": lk["mono0"],
                      "mono": lk["mono"],
                      "wall": lk["wall"], "impl": impl(), "platform": sys.platform, "ok": ok, "why": why})
        if self.cut_tail():
            line = b"\n" + line                         # S2: the cut line stays a line of its own, skipped (C8)
        with open(self.journal, "ab") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())

    def stop(self, lk: dict, why: str):
        self.write(lk, False, why)
        raise Stop(9, why)

    def done(self, lk: dict) -> str:
        r = lk["rec"]
        s = r["utc_ms"] / 1000
        return (f"clock: ok n {r['n']}, the server's time {utc_text(s)} (utc_ms {r['utc_ms']}), offset "
                f"{s - lk['wall']:.1f} s (the server's minus the PC's; a note for people)")

    @staticmethod
    def unchanged(lk: dict, line: dict) -> str:
        s = line["utc_ms"] / 1000 + (lk["mono"] - line["mono"])
        return (f"clock: unchanged n {line['n']} (the same record as the accepted line, which stays), the server's time "
                f"{utc_text(s)} by it extrapolated, offset {s - lk['wall']:.1f} s (the server's minus the PC's; a note "
                f"for people)")

    @staticmethod
    def distance(lk: dict, line: dict) -> float:
        """The look's utc_ms against the line extrapolated to the look's mono, in seconds (+ newer, - older)."""
        return lk["rec"]["utc_ms"] / 1000 - (line["utc_ms"] / 1000 + (lk["mono"] - line["mono"]))

    def pair(self, a: dict, b: dict):
        """THE PAIR RULES after b's own M3 to M6: None when b is ok against a, else the STOP text."""
        n1, n2, u1, u2 = a["rec"]["n"], b["rec"]["n"], a["rec"]["utc_ms"], b["rec"]["utc_ms"]
        if n2 == n1:
            return f"the server's guard does not write CLOCK.json (n {n1} unchanged after {self.gap:g} s)"
        if n2 < n1:
            return f"n {n2} is smaller than the first look's {n1} (the root was replaced or CLOCK.json lost)"
        du, dm = (u2 - u1) / 1000, b["mono"] - a["mono"]
        if abs(du - dm) > AGREE_S:
            return (f"the server's clock is not steady (it moved {du:.1f} s while {dm:.1f} s passed here; or its "
                    f"guard paused before the first look)")
        if u2 <= u1:
            return f"the server's clock went back (n {n1} -> {n2}, utc_ms {u1} -> {u2})"
        return None

    def second(self, a: dict, line, kind: str) -> str:
        time.sleep(self.gap)
        b = self.look(2)
        if b["bad"]:
            self.stop(b, b["bad"])
        bad = self.pair(a, b)
        if bad:
            self.stop(b, bad)
        if kind == "newer":
            why = (f"the server's clock is {round(self.distance(b, line))} s ahead of the last line extrapolated, "
                   f"confirmed by a second look")
        elif kind == "older":
            why = f"a second look: the first was {round(-self.distance(a, line))} s behind the last line extrapolated"
        else:
            why = None
        self.write(b, True, why)
        return self.done(b)

    def run(self) -> str:
        try:
            line, _m = accepted(self.home, self.fp)
        except ClockRefused:
            line = None
        a = self.look(1)
        if a["bad"]:
            self.stop(a, a["bad"])
        if line is None:                                # M2
            self.write(a, False, "the first of two looks (no clock line of this run is accepted now)")
            return self.second(a, None, "two")
        if a["rec"]["n"] < line["n"]:                   # M7b
            self.stop(a, f"n {a['rec']['n']} is smaller than the accepted line's {line['n']} (the root was replaced "
                         f"or CLOCK.json lost)")
        x = self.distance(a, line)
        if a["rec"]["n"] == line["n"]:                  # M7d: the same record never becomes an accepted line
            if a["rec"]["utc_ms"] != line["utc_ms"]:    # M7d (a)
                self.stop(a, f"n {line['n']} unchanged but utc_ms changed ({line['utc_ms']} -> {a['rec']['utc_ms']}): "
                             f"not one guard's chain (the root was replaced)")
            if x >= -OLDER_S:                           # M7d (b); else (c): the older branch below
                self.write(a, False, f"the same record as the accepted line (n {line['n']}): the line stays")
                return self.unchanged(a, line)
        if -OLDER_S <= x <= NEWER_S:                    # M7: one look
            self.write(a, True, None)
            return self.done(a)
        if x < 0:                                       # the older branch (R4)
            self.write(a, False, f"{round(-x)} s behind the last line extrapolated: a second look is taken")
            return self.second(a, line, "older")
        self.write(a, False, f"{round(x)} s ahead of the last line extrapolated: a second look is taken")   # M7c
        return self.second(a, line, "newer")


def main() -> int:
    ap = argparse.ArgumentParser(description="The home clock: the server's time, measured (v17).")
    ap.add_argument("what", choices=["measure"])
    ap.add_argument("--home", required=True)
    ap.add_argument("--fingerprint", required=True)
    ap.add_argument("--config", required=True)
    a = ap.parse_args()
    if not HEX64.fullmatch(a.fingerprint):
        print("clock: STOP (2): --fingerprint must be 64 hex digits")
        return 2
    m = None
    try:
        try:
            cfg = json.loads(Path(a.config).read_text(encoding="ascii"))
        except (OSError, ValueError) as e:
            raise Stop(2, f"the config cannot be read: {e}") from None
        if not isinstance(cfg, dict):
            raise Stop(2, "the config is not one JSON object")
        m = Measure(Path(a.home).resolve(), a.fingerprint, cfg)
        print(m.run())
        return 0
    except Stop as e:
        print(f"clock: STOP ({e.code}): {e}")
        return e.code
    except OSError as e:
        print(f"clock: STOP (4): a home file cannot be read or written: {e}")
        return 4
    finally:
        if m is not None:
            m.lock.release()


if __name__ == "__main__":
    sys.exit(main())
