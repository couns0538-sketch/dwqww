"""Opus 2026-11-26, v17: THE STATE WRITER. Standard library only; nothing is installed.

    state.py --home DIR --fingerprint HEX64

Called by the home guard loop before every decision. It writes home/state/state.<k>.json (budget.py's state) and,
ONCE, when the pilot's K rounds are whole, home/pilot/pilot.json (budget.py's pilot) with its evidence
home/pilot/PILOT.1.json. KNOWN ANSWERS, written before this code: Fable's
tmp/fable_scratch/reads_2611/KNOWN_ANSWERS_state_py_by_fable.md (5d7d23b6f05b: S1 to S11, P1 to P21, RR1 to RR8; P22 is
Opus's case for her remark R1 of 26 Nov: evidence that is no JSON is a refusal, never a traceback; P23 for her RV1:
evidence of this run whose "values" is no dict is a refusal too); the
interface: tmp/opus_scratch/v17/INTERFACE_state_py_by_opus.md (the home loop journal, N1, N2); the server's record:
tmp/opus_scratch/v17/KNOWN_ANSWERS_v17_server_by_opus.md (R3 with C-R1, C-R2; the clock bound C-F1).

THE RULE OF NUMBERS (RR1): counts are ints. Seconds are ints rounded UP (now_s, cohort_seconds, longest_game_s). A
rate is the exact quotient (a Fraction) rounded DOWN to three places and written as a decimal with exactly three
places, never through a float; a sum over slots is rounded once, after the exact sum; a rate that is not measured is
the int 0. Every rounding is to the safe side: a later now, a longer cohort, a longer game, a lower rate.
TIME: the server's, by home/clock.py's reading() (server_now, never ahead; lag_s, the measured bound of how far it runs
behind, C-F1). Their sum, the UPPER bound of the server's time, is "now". Never the PC's wall clock.

THE STATE, state.<k>.json (canonical):
- now_s = ceil(upper - L), where L is RUN.json's lease_start_utc.
- c4_rows = the sum of kept_rows of every report.json in rounds/ (a partial round's is 0). It is taken from the ledger
  C4.<k>.json, which is written FIRST, create-only, listing [round, sha256 of its report.json, kept_rows]; the state
  names the ledger under sources by absolute path and sha256.
- The other keys, which budget.py prints back and never counts: run_fingerprint, clock_n, clock_server_text,
  server_now and lag_s (decimal texts, 3 places), partial_rounds, partial_games, partial_raw_rows (rounds credit.py
  decided partial), waiting_rounds, waiting_games, waiting_raw_rows (rounds with a range seal at home, no report and
  not partial; F9: the games and rows of their range seals at home), and pilot (one of five texts, P4b):
  "waiting: w of K rounds whole", "cannot qualify: round r is partial", "no server record", "refused: <why>",
  "written: <sha12 of pilot.json>".
- k = 1 + the highest k among the names state.<k>.json and C4.<k>.json in home/state/, files or folders. A name that
  exists is never written over.
REFUSED, no state (exit 9, the line says why), and the files of earlier decisions keep their bytes:
- no accepted clock line of this run, or no lag bound (S4);
- the upper bound before the lease start (S5);
- a published report whose bytes changed, or that is gone, since the newest ledger named it (S8);
- a report, a range seal or stage/credited.sqlite of another run (S9).

THE PILOT, written once, when every pilot round has a COMPLETE report at home and the guard's record wire/PILOT.json.zz
passes its checks; the evidence PILOT.1.json comes first, then pilot.json, whose 14 keys all name PILOT.1.json under
sources. The 14 keys:
- rounds_whole: K.
- queues_empty_at_start (N2): true only when the home loop journal FILE's first complete line is THIS run's start
  line with empty true, every slot's epochs are [1], and every slot's pilot ranges are contiguous from counter 1.
THE HOME LOOP JOURNAL home/loop/journal.jsonl (its writer is the home loop): {"empty","run","t":"start","why"} at every
start before the first fetch; {"kind":"c3"|"c4","ms","moved","new_reports","run","t":"pass","upper_ms"} after every
pass (moved: the names whose existence or size the pass changed; upper_ms: ceil(1000 x (server_now + lag_s)) at the
pass's end, or null without an accepted clock reading). Only exact lines of THIS run count; another line is skipped.
- carry_in_rows: 0 when the queues were empty, else cohort_raw_rows.
- cohort_games, cohort_raw_rows: the slots' sums in the record, each slot cross-checked against the cohort's range
  seals at home (RR6).
- cohort_c4_rows: the pilot reports' kept_rows.
- cohort_seconds = ceil((the END MOMENT - the earliest first_t0_ms + the largest play_ms - span_ms above 0 over the
  slots, RR7) / 1000). A round's moment is upper_ms of the first pass line, at or after the one whose new_reports
  first names the round, that has one (F8, P8); the end moment is the LATEST of the K moments (P17), and "the end
  line" is the last of the K moment lines in the file.
- games_per_h and c1_raw_rows_per_s: sums over the slots, each slot's time max(span_ms, play_ms) (RR2); a slot with
  games and a time of 0 makes both 0.
- c2_raw_rows_per_s: packer raw_rows / busy_ms; 0 when busy_ms is 0 (P12).
- c3_games_per_s: the cohort's games / the ms of the c3 passes with moved above 0 from the journal's start up to and
  including the end line; c4_kept_rows_per_s: the cohort's kept rows / the ms of such c4 passes (no schedule exists
  before the pilot's decision, so every unit moved before the end moment is the cohort's). Both are 0 when no such
  pass exists (P12).
- RR8, a restart BOUNDS a rate (Fable's, agreed 26 Nov 09:52): every cohort unit went through each stage between the
  cohort's first game and its end moment, so a stage's busy time on them is at most cohort_seconds. When the packer
  restarted (restarted above 0, C-R2: its busy_ms misses time), c2 = floor3(cohort_raw_rows / cohort_seconds); when
  the home loop restarted (N1: this run's lines do not begin with a start line, or another start line of this run
  stands at or before the end line; a crash inside a pass loses that pass's line and time), c3 =
  floor3(cohort_games / cohort_seconds) and c4 = floor3(cohort_c4_rows / cohort_seconds), whether or not a counted
  pass exists (the cut pass may have been the one). A bound with no units or no seconds is 0. PILOT.1.json names
  every bound under "bounds": "bounded by the cohort's span: <which> was started again (...)".
- longest_game_s: ceil(the longest game / 1000). match_games_per_h: 0.
Not written, with the pilot's text saying why:
- a pilot round decided partial: "cannot qualify" (RR3);
- no wire/PILOT.json.zz: "no server record";
- a record that is not this run's or not its form (P10), or one that disagrees with the range seals or the packer's
  sum (RR6): "refused";
- a pilot round without a publish moment yet: "waiting".
pilot.json and state.<k>.json are budget.py's inputs: plain JSON, sorted keys, no spaces, one line end. A rate is a
decimal with three places, which the package's canonical form (ints only) does not take, so pilot.json is not read
back with parse_canon.
Exit codes: 0 a state written; 2 a wrong call; 3 the run header at home is not this run's; 4 a file that cannot be
read or written; 9 no state, the reason named. The last line: "state: k <k>, now_s <n>, c4_rows <n>; pilot: <text>" or
"state: STOP (<code>): <why>".
"""
import argparse
import json
import math
import re
import sqlite3
import sys
import time
from decimal import ROUND_CEILING, Decimal
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "run"))    # Fable's R2: worker.py is found by this file itself (as credit.py)
sys.path.insert(0, str(HERE))
import clock as CK  # noqa: E402   the server's time: reading() (v17, C-F1)
from deliver import record, unzz  # noqa: E402   the run header as deliver.py reads it
from worker import Stop, canon, check_rows, create_only, parse_canon, sha256_bytes, utc  # noqa: E402

HEX64 = re.compile(r"[0-9a-f]{64}")
ROUND_DIR = re.compile(r"r([0-9]{4})\Z")
RANGE_WIRE = re.compile(r"r([0-9]{4})\.w([0-9]{3})\.seal\.json\.zz\Z")
NUMBERED = re.compile(r"(state|C4)\.([1-9][0-9]{0,8})\.json\Z")
PILOT_KEYS = sorted(["packer", "rounds", "run_fingerprint", "schema", "slots"])
SLOT_KEYS = sorted(["epochs", "first_t0_ms", "games", "last_end_ms", "longest_ms", "play_ms", "raw_rows", "slot",
                    "span_ms"])
PACKER_KEYS = sorted(["busy_ms", "pieces", "raw_rows", "restarted"])
START_KEYS = sorted(["empty", "run", "t", "why"])
PASS_KEYS = sorted(["kind", "ms", "moved", "new_reports", "run", "t", "upper_ms"])
VALUE_KEYS = ["rounds_whole", "queues_empty_at_start", "carry_in_rows", "cohort_games", "cohort_raw_rows",
              "cohort_c4_rows", "cohort_seconds", "games_per_h", "c1_raw_rows_per_s", "c2_raw_rows_per_s",
              "c3_games_per_s", "c4_kept_rows_per_s", "longest_game_s", "match_games_per_h"]


class Rate:
    """A rate in thousandths, written as a decimal with exactly three places."""

    def __init__(self, thousandths: int):
        assert type(thousandths) is int and thousandths >= 0
        self.n = thousandths

    def text(self) -> str:
        return f"{self.n // 1000}.{self.n % 1000:03d}"


def floor3(q: Fraction) -> Rate:
    return Rate(math.floor(q * 1000))


def ceil_div(a: int, b: int) -> int:
    return -((-a) // b)


def jdump(obj) -> bytes:
    """Sorted keys, no spaces, ASCII, one line end; a Rate as its decimal text (never through a float)."""
    marks = {}

    def sub(x):
        if isinstance(x, Rate):
            key = f"@@RATE{len(marks)}@@"
            marks[key] = x.text()
            return key
        if isinstance(x, dict):
            return {k: sub(v) for k, v in x.items()}
        if isinstance(x, list):
            return [sub(v) for v in x]
        return x
    text = json.dumps(sub(obj), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    for key, val in marks.items():
        assert text.count(f'"{key}"') == 1, key
        text = text.replace(f'"{key}"', val)
    return (text + "\n").encode("ascii")


def dec3(d: Decimal, rounding) -> str:
    return str(d.quantize(Decimal("0.001"), rounding=rounding))


def is_count(v) -> bool:
    return type(v) is int and v >= 0


class State:
    def __init__(self, home: Path, fp: str, mono, wall):
        self.home, self.fp, self.mono, self.wall = home, fp, mono, wall
        if not home.is_dir():
            raise Stop(2, f"{home}: no such home folder")
        p = home / "wire" / "RUN.json.zz"
        data = unzz(p.read_bytes(), "wire/RUN.json.zz") if p.is_file() else b""
        if sha256_bytes(data) != fp:
            raise Stop(3, "DIR/wire/RUN.json.zz is not this run's header (the fingerprint)")
        self.h = record(data, "RUN.json")
        self.L = utc(self.h.get("lease_start_utc"), "RUN.json lease_start_utc")
        if not (isinstance(self.h.get("slots"), list) and self.h["slots"]
                and all(type(k) is int and 0 <= k <= 999 for k in self.h["slots"])):
            raise Stop(4, "RUN.json at home has no slots as 1.1 says")
        self.slots = list(self.h["slots"])
        self.prows = list(check_rows(self.h.get("pilot_ranges"), self.slots, 0, "RUN.json pilot_ranges"))
        self.prounds = sorted({r["round"] for r in self.prows})
        self.sdir, self.pdir = home / "state", home / "pilot"

    # ---- the files home holds -------------------------------------------------------------------------------------
    def reports(self) -> dict:
        """{round: (sha256, status, kept_rows)} of every report.json in rounds/ (S9: another run's refuses)."""
        out = {}
        d = self.home / "rounds"
        if not d.is_dir():
            return out
        for e in sorted(d.iterdir()):
            m = ROUND_DIR.fullmatch(e.name)
            if not m or not e.is_dir():
                continue
            try:
                data = (e / "report.json").read_bytes()
            except FileNotFoundError:
                continue                                # publish renames a whole folder: none is half there
            try:
                rep = parse_canon(data, f"rounds/{e.name}/report.json")
            except ValueError as x:
                raise Stop(9, f"no state: {x}") from None
            if not isinstance(rep, dict) or rep.get("run_fingerprint") != self.fp:
                raise Stop(9, f"no state: rounds/{e.name}/report.json is not this run's")
            if rep.get("round") != int(m.group(1)) or rep.get("status") not in ("complete", "partial") \
                    or not is_count(rep.get("kept_rows")):
                raise Stop(9, f"no state: rounds/{e.name}/report.json is not a report of its round")
            out[int(m.group(1))] = (sha256_bytes(data), rep["status"], rep["kept_rows"])
        return out

    def range_seals(self, rounds) -> dict:
        """{round: {slot: (games, rows)}} of the range seals at home of the given rounds (S9: another run's refuses)."""
        out = {}
        d = self.home / "wire" / "ranges"
        if not d.is_dir():
            return out
        want = set(rounds)
        for e in sorted(d.iterdir()):
            m = RANGE_WIRE.fullmatch(e.name)
            if not m or int(m.group(1)) not in want:
                continue
            s = record(unzz(e.read_bytes(), f"wire/ranges/{e.name}"), e.name)
            if s.get("run_fingerprint") != self.fp or s.get("round") != int(m.group(1)) \
                    or s.get("slot") != int(m.group(2)):
                raise Stop(9, f"no state: wire/ranges/{e.name} is not this run's seal of its round and slot")
            if not (is_count(s.get("games")) and is_count(s.get("rows"))):
                raise Stop(9, f"no state: wire/ranges/{e.name} has no games and rows")
            out.setdefault(int(m.group(1)), {})[int(m.group(2))] = (s["games"], s["rows"])
        return out

    def credit_status(self) -> dict:
        """{round: status} from stage/credited.sqlite, read only (none yet: {})."""
        p = self.home / "stage" / "credited.sqlite"
        if not p.is_file():
            return {}
        con = sqlite3.connect(f"file:{p.resolve().as_posix()}?mode=ro", uri=True, timeout=30)
        try:
            row = con.execute("SELECT value FROM meta WHERE key = 'run_fingerprint'").fetchone()
            if row is not None and row[0] != self.fp:
                raise Stop(9, "no state: stage/credited.sqlite belongs to another run")
            return {int(r): str(s) for r, s in con.execute("SELECT round, status FROM rounds")}
        except sqlite3.Error as e:
            raise Stop(4, f"stage/credited.sqlite cannot be read: {e}") from None
        finally:
            con.close()

    def journal(self):
        """(whether the FILE's first complete line is this run's start line with empty true, this run's exact records
        in file order as (line number, record)). A cut line, a line that is not an exact record and a line of another
        run are skipped: never counted (a rehearsal's journal left in a cleaned home, Fable's point 4)."""
        p = self.home / "loop" / "journal.jsonl"
        try:
            data = p.read_bytes()
        except FileNotFoundError:
            return False, []
        first_empty, out = False, []
        for no, raw in enumerate(data.split(b"\n")[:-1], 1):          # only lines with their line end
            r = self.journal_line(raw)
            if no == 1:
                first_empty = r is not None and r["t"] == "start" and r["empty"] is True
            if r is not None:
                out.append((no, r))
        return first_empty, out

    def journal_line(self, raw: bytes):
        """The exact start or pass record of this run, or None."""
        try:
            r = parse_canon(raw + b"\n", "home/loop/journal.jsonl")
        except ValueError:
            return None
        if not isinstance(r, dict) or r.get("run") != self.fp:
            return None
        if r.get("t") == "start" and sorted(r) == START_KEYS and type(r["empty"]) is bool and isinstance(r["why"], str):
            return r
        if r.get("t") == "pass" and sorted(r) == PASS_KEYS and r["kind"] in ("c3", "c4") and is_count(r["ms"]) \
                and is_count(r["moved"]) \
                and isinstance(r["new_reports"], list) and all(is_count(x) for x in r["new_reports"]) \
                and (r["upper_ms"] is None or is_count(r["upper_ms"])):
            return r
        return None

    def contiguous(self) -> bool:
        """N2's third condition: every slot's pilot ranges, in round order, run from counter 1 without a gap."""
        for k in self.slots:
            nxt = 1
            for x in sorted((x for x in self.prows if x["slot"] == k), key=lambda x: x["round"]):
                if x["first"] != nxt:
                    return False
                nxt = x["last"] + 1
        return True

    def newest_ledger(self):
        """(k, its rows) of the highest-numbered C4 ledger FILE, or (0, [])."""
        best = (0, [])
        if not self.sdir.is_dir():
            return best
        for e in self.sdir.iterdir():
            m = NUMBERED.fullmatch(e.name)
            if not m or m.group(1) != "C4" or not e.is_file() or int(m.group(2)) <= best[0]:
                continue
            try:
                led = parse_canon(e.read_bytes(), f"state/{e.name}")
            except ValueError as x:
                raise Stop(9, f"no state: {x}") from None
            if not isinstance(led, dict) or led.get("run_fingerprint") != self.fp or not isinstance(led.get("rounds"),
                                                                                                    list):
                raise Stop(9, f"no state: state/{e.name} is not a ledger of this run")
            best = (int(m.group(2)), led["rounds"])
        return best

    def next_k(self) -> int:
        top = 0
        if self.sdir.is_dir():
            for e in self.sdir.iterdir():
                m = NUMBERED.fullmatch(e.name)
                if m:
                    top = max(top, int(m.group(2)))
        return top + 1

    # ---- the pilot ------------------------------------------------------------------------------------------------
    def pilot(self, reps: dict, status: dict) -> str:
        """The pilot's text; writes PILOT.1.json and pilot.json when they are due (once)."""
        pj, ev = self.pdir / "pilot.json", self.pdir / "PILOT.1.json"
        if pj.exists():
            try:
                obj = json.loads(pj.read_bytes().decode("ascii"))
            except (OSError, ValueError) as e:
                return f"refused: home/pilot/pilot.json cannot be read ({e})"
            if not isinstance(obj, dict) or obj.get("run_fingerprint") != self.fp:
                return "refused: home/pilot/pilot.json is not this run's"
            return f"written: {sha256_bytes(pj.read_bytes())[:12]}"
        if ev.is_file():                                # a stop between the two files: pilot.json from the evidence
            return self.write_pilot(ev.read_bytes())
        for r in self.prounds:
            if status.get(r) == "partial" or (r in reps and reps[r][1] == "partial"):
                return f"cannot qualify: round {r} is partial"
        whole = sum(1 for r in self.prounds if r in reps and reps[r][1] == "complete")
        K = len(self.prounds)
        if whole < K:
            return f"waiting: {whole} of {K} rounds whole"
        p = self.home / "wire" / "PILOT.json.zz"
        if not p.is_file():
            return "no server record"
        try:
            data = unzz(p.read_bytes(), "wire/PILOT.json.zz")
            rec = parse_canon(data, "PILOT.json")
        except (Stop, ValueError) as e:
            return f"refused: {e}"
        why = self.record_fault(rec)
        if why:
            return f"refused: {why}"
        seals = self.range_seals(self.prounds)
        for s in rec["slots"]:
            k = s["slot"]
            got = [seals.get(r, {}).get(k) for r in self.prounds if any(x["slot"] == k and x["round"] == r
                                                                       for x in self.prows)]
            if any(g is None for g in got):
                return f"refused: a range seal of slot {k}'s pilot is not at home"
            if (sum(g[0] for g in got), sum(g[1] for g in got)) != (s["games"], s["raw_rows"]):
                return (f"refused: slot {k}: the record's games {s['games']} and raw_rows {s['raw_rows']} are not "
                        f"the range seals' {sum(g[0] for g in got)} and {sum(g[1] for g in got)}")
        pk = rec["packer"]
        if pk["restarted"] == 0 and pk["raw_rows"] != sum(s["raw_rows"] for s in rec["slots"]):
            return (f"refused: the packer's raw_rows {pk['raw_rows']} are not the slots' "
                    f"{sum(s['raw_rows'] for s in rec['slots'])}")
        first_empty, lines = self.journal()
        recs = [x for _, x in lines]
        moments, last = {}, 0
        for r in self.prounds:                          # P8: the first pass line with a clock, at or after the one
            seen = next((i for i, x in enumerate(recs) if x["t"] == "pass" and r in x["new_reports"]), None)
            at = None if seen is None else next((i for i in range(seen, len(recs)) if recs[i]["t"] == "pass"
                                                 and recs[i]["upper_ms"] is not None), None)
            if at is None:
                return f"waiting: {whole} of {K} rounds whole; round {r} has no publish moment yet"
            moments[r] = recs[at]["upper_ms"]
            last = max(last, at)
        first_t0 = min(s["first_t0_ms"] for s in rec["slots"])
        end = max(moments.values())
        if end < first_t0:
            return "refused: a publish moment lies before the cohort's first game"
        if recs[0]["t"] != "start":                                                                # N1
            home_why = f"its first line of this run, journal line {lines[0][0]}, is not a start line"
        else:
            again = next((no for no, x in lines[1:last + 1] if x["t"] == "start"), None)
            home_why = None if again is None else f"journal line {again}"
        restarted = home_why is not None
        end_no = lines[last][0]                         # the end line: the last of the K moment lines
        counted = {"c3": [], "c4": []}
        for no, x in lines:                             # every busy pass up to the end line is the cohort's work
            if no <= end_no and x["t"] == "pass" and x["moved"] > 0:
                counted[x["kind"]].append([no, x["ms"], x["moved"]])
        empty = first_empty and all(s["epochs"] == [1] for s in rec["slots"]) and self.contiguous()     # N2
        games = sum(s["games"] for s in rec["slots"])
        raw = sum(s["raw_rows"] for s in rec["slots"])
        kept = sum(reps[r][2] for r in self.prounds)
        times = [(s, max(s["span_ms"], s["play_ms"])) for s in rec["slots"]]                       # RR2
        step = max([0] + [s["play_ms"] - s["span_ms"] for s in rec["slots"]])                    # RR7
        if any(t == 0 and s["games"] > 0 for s, t in times):
            gph, c1 = 0, 0
        else:
            gph = floor3(sum((Fraction(3_600_000 * s["games"], t) for s, t in times if t > 0), Fraction(0)))
            c1 = floor3(sum((Fraction(1000 * s["raw_rows"], t) for s, t in times if t > 0), Fraction(0)))
        secs = ceil_div(end - first_t0 + step, 1000)                                               # RR7
        bounds = {}

        def bound(key, units, which):                                                              # RR8
            bounds[key] = f"bounded by the cohort's span: {which} was started again"
            return floor3(Fraction(units, secs)) if units > 0 and secs > 0 else 0

        if pk["restarted"] > 0:
            c2 = bound("c2_raw_rows_per_s", raw, f"the packer (restarted {pk['restarted']})")
        else:
            c2 = floor3(Fraction(1000 * pk["raw_rows"], pk["busy_ms"])) if pk["busy_ms"] > 0 else 0
        ms3, ms4 = sum(x[1] for x in counted["c3"]), sum(x[1] for x in counted["c4"])
        if restarted:
            c3 = bound("c3_games_per_s", games, f"the home loop ({home_why})")
            c4 = bound("c4_kept_rows_per_s", kept, f"the home loop ({home_why})")
        else:
            c3 = floor3(Fraction(1000 * games, ms3)) if ms3 > 0 else 0
            c4 = floor3(Fraction(1000 * kept, ms4)) if ms4 > 0 else 0
        values = {"rounds_whole": K, "queues_empty_at_start": empty, "carry_in_rows": 0 if empty else raw,
                  "cohort_games": games, "cohort_raw_rows": raw, "cohort_c4_rows": kept,
                  "cohort_seconds": secs, "games_per_h": gph, "c1_raw_rows_per_s": c1,
                  "c2_raw_rows_per_s": c2, "c3_games_per_s": c3, "c4_kept_rows_per_s": c4,
                  "longest_game_s": ceil_div(max(s["longest_ms"] for s in rec["slots"]), 1000), "match_games_per_h": 0}
        evidence = {"schema": 1, "run_fingerprint": self.fp, "rounds": self.prounds,
                    "server_record": {"sha256": sha256_bytes(data), "record": rec},
                    "reports": [[r, reps[r][0], reps[r][2], moments[r]] for r in self.prounds],
                    "slot_ms": [[s["slot"], t, "play_ms" if s["play_ms"] > s["span_ms"] else "span_ms"]
                                for s, t in times],
                    "step_ms": step, "first_t0_ms": first_t0, "end_ms": end,
                    "passes": counted, "home_restarted": restarted, "bounds": bounds, "values": values}
        self.pdir.mkdir(exist_ok=True)
        eb = jdump(evidence)
        create_only(ev, eb)
        return self.write_pilot(eb)

    def record_fault(self, rec) -> str:
        """'' when rec is this run's PILOT.json of R3 in the header's slot order (P10), else why not."""
        if not isinstance(rec, dict) or sorted(rec) != PILOT_KEYS:
            return "PILOT.json does not hold exactly the keys of R3"
        if rec["schema"] != 1 or type(rec["schema"]) is not int or rec["run_fingerprint"] != self.fp:
            return "PILOT.json is not this run's (schema 1, run_fingerprint)"
        if rec["rounds"] != self.prounds:
            return f"PILOT.json names the rounds {str(rec['rounds'])[:40]}, not the pilot's {self.prounds}"
        if not isinstance(rec["slots"], list) or [s.get("slot") if isinstance(s, dict) else None
                                                  for s in rec["slots"]] != self.slots:
            return "PILOT.json's slots are not the header's slots in their order"
        for s in rec["slots"]:
            if sorted(s) != SLOT_KEYS or not all(is_count(s[x]) for x in SLOT_KEYS if x != "epochs"):
                return f"PILOT.json's slot {s.get('slot')} is not R3's form"
            if not (isinstance(s["epochs"], list) and s["epochs"] and all(type(e) is int and e >= 1 for e in s["epochs"])
                    and s["epochs"] == sorted(set(s["epochs"]))):
                return f"PILOT.json's slot {s['slot']} has no epochs rising"
            if s["span_ms"] != s["last_end_ms"] - s["first_t0_ms"] or s["longest_ms"] > s["play_ms"]:
                return f"PILOT.json's slot {s['slot']}: span_ms, longest_ms and play_ms do not agree"
        pk = rec["packer"]
        if not isinstance(pk, dict) or sorted(pk) != PACKER_KEYS or not all(is_count(pk[x]) for x in PACKER_KEYS):
            return "PILOT.json's packer is not R3's form"
        return ""

    def write_pilot(self, eb: bytes) -> str:
        """pilot.json from the evidence's bytes: the 14 values, run_fingerprint, every key sourced to PILOT.1.json."""
        try:
            ev = json.loads(eb.decode("ascii"), parse_float=Decimal)
        except ValueError as e:                         # Fable's R1: damaged evidence is a refusal, not a traceback
            return f"refused: home/pilot/PILOT.1.json cannot be read ({e})"
        if not isinstance(ev, dict) or ev.get("run_fingerprint") != self.fp or not isinstance(ev.get("values"), dict) \
                or sorted(ev["values"]) != sorted(VALUE_KEYS):     # Fable's RV1: values that are no dict, a refusal
            return "refused: home/pilot/PILOT.1.json is not this run's evidence"
        values = {k: (Rate(int(v * 1000)) if isinstance(v, Decimal) else v) for k, v in ev["values"].items()}
        src = {"path": str((self.pdir / "PILOT.1.json").resolve()), "sha256": sha256_bytes(eb)}
        pilot = dict(values, run_fingerprint=self.fp, sources={k: dict(src) for k in VALUE_KEYS})
        pb = jdump(pilot)
        create_only(self.pdir / "pilot.json", pb)
        return f"written: {sha256_bytes(pb)[:12]}"

    # ---- one decision -----------------------------------------------------------------------------------------------
    def run(self) -> str:
        try:
            now, lag, line = CK.reading(self.home, self.fp, self.mono, self.wall)
        except CK.ClockRefused as e:
            raise Stop(9, f"no state: the clock: {e}") from None
        upper = now + lag
        if upper < self.L:
            raise Stop(9, f"no state: the server's time {dec3(upper, ROUND_CEILING)} is before the lease start {self.L}")
        now_s = int((upper - self.L).to_integral_value(rounding=ROUND_CEILING))
        reps = self.reports()
        k_old, old = self.newest_ledger()
        for row in old:                                 # S8: a published report never changes
            if not (isinstance(row, list) and len(row) == 3 and row[0] in reps and reps[row[0]][0] == row[1]):
                raise Stop(9, f"no state: rounds/r{str(row[0] if isinstance(row, list) and row else '?'):0>4}"
                              f"/report.json changed or went since state/C4.{k_old}.json named it")
        status = self.credit_status()
        partial = sorted({r for r, s in status.items() if s == "partial"} | {r for r, v in reps.items()
                                                                             if v[1] == "partial"})
        seals = self.range_seals(sorted(self._unreported(reps)))
        waiting = sorted(r for r in seals if r not in reps and r not in partial)
        pseals = self.range_seals(partial) if partial else {}
        pilot_text = self.pilot(reps, status)
        k = self.next_k()
        self.sdir.mkdir(exist_ok=True)
        rows = [[r, reps[r][0], reps[r][2]] for r in sorted(reps)]
        c4 = sum(x[2] for x in rows)
        lb = canon({"schema": 1, "run_fingerprint": self.fp, "k": k, "rounds": rows, "c4_rows": c4})
        lp = self.sdir / f"C4.{k}.json"
        create_only(lp, lb)
        st = {"now_s": now_s, "c4_rows": c4, "sources": {"c4_rows": {"path": str(lp.resolve()),
                                                                      "sha256": sha256_bytes(lb)}},
              "run_fingerprint": self.fp, "clock_n": line["n"], "clock_server_text": CK.utc_text(math.floor(now)),
              "server_now": dec3(now, ROUND_CEILING), "lag_s": dec3(lag, ROUND_CEILING),
              "partial_rounds": len(partial), "partial_games": sum(g for r in partial for g, _ in pseals.get(r, {}).values()),
              "partial_raw_rows": sum(w for r in partial for _, w in pseals.get(r, {}).values()),
              "waiting_rounds": len(waiting), "waiting_games": sum(g for r in waiting for g, _ in seals[r].values()),
              "waiting_raw_rows": sum(w for r in waiting for _, w in seals[r].values()), "pilot": pilot_text}
        create_only(self.sdir / f"state.{k}.json", canon(st))
        return f"state: k {k}, now_s {now_s}, c4_rows {c4}; pilot: {pilot_text}"

    def _unreported(self, reps: dict) -> set:
        """The rounds that have a range seal at home and no report (read by name only)."""
        d = self.home / "wire" / "ranges"
        if not d.is_dir():
            return set()
        return {int(m.group(1)) for e in d.iterdir() if (m := RANGE_WIRE.fullmatch(e.name))} - set(reps)


def run(home, fp: str, mono=time.monotonic, wall=time.time) -> str:
    """One decision's state. mono and wall are read ONCE (the one seam a test plants)."""
    m, w = mono(), wall()
    return State(Path(home), fp, lambda: m, lambda: w).run()


def main() -> int:
    ap = argparse.ArgumentParser(description="the state writer of a decision (budget.py's state.json and pilot.json)")
    ap.add_argument("--home", required=True)
    ap.add_argument("--fingerprint", required=True)
    try:
        a = ap.parse_args()
    except SystemExit:
        return 2
    if not HEX64.fullmatch(a.fingerprint):
        print("state: STOP (2): --fingerprint must be 64 lowercase hex digits")
        return 2
    try:
        print(run(a.home, a.fingerprint))
        return 0
    except Stop as e:
        print(f"state: STOP ({e.code}): {e}")
        return e.code
    except OSError as e:
        print(f"state: STOP (4): a file cannot be read or written: {e}")
        return 4


if __name__ == "__main__":
    sys.exit(main())
