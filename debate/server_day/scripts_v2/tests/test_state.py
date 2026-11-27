"""test_state.py: home/state.py (v17, the state writer) against Fable's known answers written BEFORE its code
(tmp/fable_scratch/reads_2611/KNOWN_ANSWERS_state_py_by_fable.md on the PC, 5d7d23b6f05b: S1 to S11, P1 to P21) and
Opus's interface note (tmp/opus_scratch/v17/INTERFACE_state_py_by_opus.md). Standard library only; a PLAIN interpreter.

    test_state.py <tree> <a NEW folder> [plantN]

<tree> holds home/, run/ and tools/; they are copied into the new folder and a plant changes the copy's home/state.py
only. state.run(home, fp, mono, wall) is called in-process with planted clocks (the one seam); four calls go through
the command line. THE FIXTURE is Fable's B as real files in the package's formats: the run header wire/RUN.json.zz, a
clock journal whose accepted line has the measured lag 80.000 (look 1 mono0 1000.0, look 2 mono 1080.0; the PC's wall
25,178 s ahead of the server), the home loop journal (a start line and six pass lines with run and moved), the
reports of rounds 1 and 2, the cohort's range seals and the guard's record wire/PILOT.json.zz.
The checks (Fable's numbers; the reader-side cases S10, P13, P14 through budget.py are her test's):
S1 clean state (now_s 1086, c4_rows 101920, the ledger and its source, the other keys); S2 the PC's wall clock 25,178 s
ahead (by the fixture: the wrong way gives 26184); S3 the exact second (1085); S4 no clock journal, no lag bound (exit
9, earlier files keep their bytes); S5 before the lease start; S6 a third round (153031, a new ledger, a folder at a
name skipped); S7 a partial and a waiting round; S8 a published report changed or gone; S9 another run's report and
range seal; S11 a newer clock line with lag 77.250 (1083; cohort_seconds stays 961).
P1 clean pilot (every key, its type and three places; sources); P3 not whole yet, then whole; P4 a partial pilot round
(by its report, by credit's table); P5 written once; P6 restarted packer (RR8: c2 bounded 108.220), its raw_rows 103999
(refused), a range seal that disagrees (refused, RR6); P7 queues not empty: epochs [1, 2], the first line a pass (RR8:
c3 0.832, c4 106.056), empty false, the first line of another run, ranges not contiguous; P8 the moment from a later
line with a clock (991); P8b no moment yet (waiting); P9 no server record; P10 six refused records; P11 RR2 and RR7
(4242.930, 153.394, 971); P12 zeros; P15 a second start line before (RR8: 0.832, 106.056) and after the end line; P16
another run's lines; P17 the reports in the other order; P18 the later moment line with the lower value (961; counted
to the last line; a start line between: RR8); P19 PILOT.1.json names the home loop's bounds and the line; P20 it names
the packer's bound; P21 both restarts at once, also on P11's day (107.106, 0.823, 104.963). P22 (Opus: Fable's R1, her
A8) a PILOT.1.json that is no JSON and no pilot.json: refused, the state written, the evidence kept. P23 (Opus:
Fable's RV1, 26 Nov) evidence with this run's fingerprint whose "values" is null, 5 or a list of the 14 names (three
homes): refused each ("is not this run's evidence"), the state written, the evidence kept, no pilot.json; before
RV1 a TypeError, a TypeError and an AttributeError. CLI exit 0, 2, 3, 9.
PLANTS (each must make the test fail; in home/state.py). EXACTLY the checks each fails, known before the runs (worked
out again 26 Nov 10:00 for RR8 and the new checks; "P1 clean" and "P1 the keys" are the two P1 checks):
plant1 no lag in now: "S1 clean", S2, S3, S6, S7, S11, CLI, P22, P23. plant2 now_s rounded down: "S1 clean", S2,
S6, S7, S11, P22, P23 (the lines of P22 and P23 hold now_s 1086).
plant3 rates rounded to the nearest (c1 151.769, c2 13506.494, P11's 4242.931, the bounds 108.221 and 0.824):
"P1 clean", P3, P6, P7, P8, P11, P12, P15, P16, P17, P18, P21. plant4 RR2 off: P11, P21. plant5 RR7 off: P11, P21.
plant6 N1 off: P7, P15, P18, P19, P21. plant7 another run's journal lines counted: P7, P16. plant8 the end moment is
round K's: P17, P18. plant9 idle passes counted: "P1 clean", "P1 the keys", P3, P6, P7, P8, P11, P12, P15, P16, P17,
P18. plant10 counted only to the FIRST line with the highest value (in fixture B the c3 line before round 2's naming
line: c4 30884.848): "P1 clean", "P1 the keys", P3, P6, P7, P11, P12, P15, P16, P17, P18. plant11 S8 off: S8. plant12
the packer's sum not checked: P6. plant13 contiguity off: P7. plant14 the moment from the naming line itself: P8.
plant15 the range seal cross-check off: P6. plant16 the journal's first line not asked: P7. plant17 RR8 off at home
(c3 = c4 = 0): P7, P15, P18, P19, P21. plant18 RR8 off at the packer (c2 = 0): P6, P20, P21. plant19 R1 off (the
evidence parsed with no refusal: a traceback): P22. plant20 RV1 off (values not checked for a dict): P23.
The old tree (v16: no state.py): one FAIL "home/state.py imports", exit 1. The new tree: 33 of 33, exit 0.
"""
import hashlib
import json
import shutil
import sqlite3
import subprocess
import sys
import time
import traceback
import zlib
from decimal import Decimal
from pathlib import Path

if len(sys.argv) < 3:
    print("usage: test_state.py <tree> <a NEW folder> [plantN]")
    sys.exit(2)
SRC_TREE, WORK = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
PLANT = sys.argv[3] if len(sys.argv) > 3 else None
if WORK.exists():
    print(f"STOP: {WORK} exists already (a NEW folder)")
    sys.exit(2)
WORK.mkdir(parents=True)
TREE = WORK / "tree"
for sub in ("home", "run", "tools"):
    shutil.copytree(SRC_TREE / sub, TREE / sub, ignore=shutil.ignore_patterns("__pycache__"))
STATE = TREE / "home" / "state.py"
PLANTS = {
    "plant1": [("        upper = now + lag\n", "        upper = now\n")],
    "plant2": [("now_s = int((upper - self.L).to_integral_value(rounding=ROUND_CEILING))", "now_s = int(upper - self.L)")],
    "plant3": [("    return Rate(math.floor(q * 1000))", "    return Rate(round(q * 1000))")],
    "plant4": [("times = [(s, max(s[\"span_ms\"], s[\"play_ms\"])) for s in rec[\"slots\"]]",
                "times = [(s, s[\"span_ms\"]) for s in rec[\"slots\"]]")],
    "plant5": [("        step = max([0] + [s[\"play_ms\"] - s[\"span_ms\"] for s in rec[\"slots\"]])",
                "        step = 0")],
    "plant6": [("        restarted = home_why is not None", "        restarted = False")],
    "plant7": [("        if not isinstance(r, dict) or r.get(\"run\") != self.fp:\n",
                "        if not isinstance(r, dict):\n")],
    "plant8": [("        end = max(moments.values())\n", "        end = moments[self.prounds[-1]]\n")],
    "plant9": [("x[\"moved\"] > 0:", "x[\"moved\"] >= 0:")],
    "plant10": [("        end_no = lines[last][0]",
                 "        end_no = next(no for no, x in lines if x[\"t\"] == \"pass\" and x[\"upper_ms\"] == end)")],
    "plant11": [("        for row in old:", "        for row in []:")],
    "plant12": [("        if pk[\"restarted\"] == 0 and pk[\"raw_rows\"] != sum(s[\"raw_rows\"] for s in rec[\"slots\"]):",
                 "        if False:")],
    "plant13": [(" and self.contiguous()", " and True")],
    "plant14": [("            at = None if seen is None else next(", "            at = seen if True else next(")],
    "plant15": [("            if (sum(g[0] for g in got), sum(g[1] for g in got)) != (s[\"games\"], s[\"raw_rows\"]):",
                 "            if False:")],
    "plant16": [("                first_empty = r is not None and r[\"t\"] == \"start\" and r[\"empty\"] is True",
                 "                first_empty = True")],
    "plant17": [('            c3 = bound("c3_games_per_s", games, f"the home loop ({home_why})")', "            c3 = 0"),
                ('            c4 = bound("c4_kept_rows_per_s", kept, f"the home loop ({home_why})")', "            c4 = 0")],
    "plant18": [("            c2 = bound(\"c2_raw_rows_per_s\", raw, f\"the packer (restarted {pk['restarted']})\")",
                 "            c2 = 0")],
    "plant19": [('        try:\n            ev = json.loads(eb.decode("ascii"), parse_float=Decimal)\n'
                 '        except ValueError as e:                         # Fable\'s R1: damaged evidence is a refusal, not'
                 ' a traceback\n            return f"refused: home/pilot/PILOT.1.json cannot be read ({e})"\n',
                 '        ev = json.loads(eb.decode("ascii"), parse_float=Decimal)\n')],
    "plant20": [('or not isinstance(ev.get("values"), dict) \\\n                or sorted(ev["values"]) != sorted(VALUE_KEYS):'
                 '     # Fable\'s RV1: values that are no dict, a refusal\n',
                 'or sorted(ev.get("values", {})) \\\n                != sorted(VALUE_KEYS):\n')],
}
if PLANT:
    text = STATE.read_text(encoding="ascii")
    if PLANT not in PLANTS or any(text.count(old) != 1 for old, _ in PLANTS[PLANT]):
        print(f"STOP: {PLANT}: no such plant, or one of its texts does not stand exactly once")
        sys.exit(2)
    for old, new in PLANTS[PLANT]:
        text = text.replace(old, new)
    STATE.write_text(text, encoding="ascii", newline="\n")
    print(f"PLANT {PLANT} applied to the copy")
sys.path.insert(0, str(TREE / "home"))
RESULTS = []


def check(name, got, want):
    ok = got == want
    RESULTS.append((name, ok))
    print(f"{'PASS' if ok else 'FAIL'} {name}: got {str(got)[:400]}" + ("" if ok else f"; want {str(want)[:400]}"),
          flush=True)
    return ok


try:
    import state as ST  # noqa: E402
    import worker as W  # noqa: E402   (state.py puts run/ on the path itself: Fable's R2)
except Exception:  # noqa: BLE001   the old tree has no state.py: every case fails, one line says so
    check("home/state.py imports", traceback.format_exc().rstrip()[-300:], "no exception")
    print("0 of 1 checks pass")
    sys.exit(1)

IMPL = time.get_clock_info("monotonic").implementation
L_TEXT = "2026-11-30T06:00:00Z"
L_S = W.utc(L_TEXT, "L")
L_MS = L_S * 1000
WALL_OFF = L_S + 1000 + 25178 - 1080.0      # the PC's wall at steady 1080.0: the server's L+1000 plus 25,178 s


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def rows_default():
    return [{"first": (r - 1) * 200 + 1, "last": r * 200, "round": r, "schedule": 0, "short": False, "slot": k}
            for r in (1, 2) for k in (0, 1)]


def header(rows=None) -> bytes:
    return W.canon({"schema": 2, "run": "test_state", "lease_start_utc": L_TEXT, "lease_end_utc": "2026-12-01T06:00:00Z",
                    "slots": [0, 1], "pilot_ranges": rows if rows is not None else rows_default()})


def cline(fp, n, mono0, mono, utc_ms, ok=True, look=2, why=None, run=None):
    return W.canon({"impl": IMPL, "look": look, "mono": mono, "mono0": mono0, "n": n, "ok": ok,
                    "platform": sys.platform, "run": run or fp, "state": "play", "t": "clock", "utc_ms": utc_ms,
                    "wall": mono + WALL_OFF, "why": why})


def clock_b(fp):
    """Fable's B: look 1 (n 5, mono0 1000.0), look 2 accepted (n 6, mono 1080.0, the server's L+1000): lag 80.000."""
    return [cline(fp, 5, 1000.0, 1000.4, L_MS + 920000, ok=False, look=1, why="the first of two looks"),
            cline(fp, 6, 1070.1, 1080.0, L_MS + 1000000)]


def start(fp, empty=True, why="the first start"):
    return W.canon({"empty": empty, "run": fp, "t": "start", "why": why})


def pas(fp, kind, ms, moved, new=(), upper=None):
    return W.canon({"kind": kind, "ms": ms, "moved": moved, "new_reports": list(new), "run": fp, "t": "pass",
                    "upper_ms": None if upper is None else L_MS + upper})


def journal_b(fp, first=None, swap=False, up2=1080400, up1=780000):
    """The fixture's seven lines (Fable's section B); swap: the reports come home in the other order (P17)."""
    a, b = ([2], [1]) if swap else ([1], [2])
    return [start(fp) if first is None else first,
            pas(fp, "c3", 1250, 9, upper=780000), pas(fp, "c4", 3300, 5, a, upper=up1),
            pas(fp, "c3", 400, 0), pas(fp, "c4", 200, 0),
            pas(fp, "c3", 2750, 9, upper=1080400), pas(fp, "c4", 3700, 5, b, upper=up2)]


def report(fp, r, kept, status="complete"):
    return W.canon({"kept_rows": kept, "round": r, "run_fingerprint": fp, "schema": 2, "status": status})


SEALS = {(1, 0): (200, 26200), (2, 0): (200, 26200), (1, 1): (200, 25800), (2, 1): (200, 25800)}


def seal(fp, r, k, games, rows, run=None):
    return zlib.compress(W.canon({"games": games, "round": r, "rows": rows, "run_fingerprint": run or fp,
                                  "schema": 2, "slot": k}), 6)


def slot0(**over):
    d = {"epochs": [1], "first_t0_ms": L_MS + 120000, "games": 400, "last_end_ms": L_MS + 721000, "longest_ms": 4321,
         "play_ms": 590000, "raw_rows": 52400, "slot": 0, "span_ms": 601000}
    d.update(over)
    return d


def slot1(**over):
    d = {"epochs": [1], "first_t0_ms": L_MS + 121500, "games": 400, "last_end_ms": L_MS + 920500, "longest_ms": 9001,
         "play_ms": 780000, "raw_rows": 51600, "slot": 1, "span_ms": 799000}
    d.update(over)
    return d


def pilot_rec(fp, slots=None, packer=None, **over) -> bytes:
    d = {"packer": packer or {"busy_ms": 7700, "pieces": 8, "raw_rows": 104000, "restarted": 0}, "rounds": [1, 2],
         "run_fingerprint": fp, "schema": 1, "slots": slots if slots is not None else [slot0(), slot1()]}
    d.update(over)
    return W.canon(d)


def fn(v, fp):
    return v(fp) if callable(v) else v


def make_home(name, rows=None, clock=clock_b, journal=journal_b, reports=None, seals=None, pilot=pilot_rec,
              credit=None):
    """Fable's fixture B as files; each part may be replaced (a callable gets the fingerprint; None: no such file)."""
    h = WORK / f"h_{name}"
    hb = header(rows)
    fp = sha(hb)
    (h / "wire" / "ranges").mkdir(parents=True)
    (h / "wire" / "RUN.json.zz").write_bytes(zlib.compress(hb, 6))
    c = fn(clock, fp)
    if c is not None:
        (h / "clock").mkdir()
        (h / "clock" / "journal.jsonl").write_bytes(b"".join(c))
    j = fn(journal, fp)
    if j is not None:
        (h / "loop").mkdir()
        (h / "loop" / "journal.jsonl").write_bytes(b"".join(j))
    for r, (kept, status) in (fn(reports, fp) or {1: (50900, "complete"), 2: (51020, "complete")}).items():
        (h / "rounds" / f"r{r:04d}").mkdir(parents=True)
        (h / "rounds" / f"r{r:04d}" / "report.json").write_bytes(report(fp, r, kept, status))
    for (r, k), (g, w) in (fn(seals, fp) or SEALS).items():
        (h / "wire" / "ranges" / f"r{r:04d}.w{k:03d}.seal.json.zz").write_bytes(seal(fp, r, k, g, w))
    p = fn(pilot, fp)
    if p is not None:
        (h / "wire" / "PILOT.json.zz").write_bytes(zlib.compress(p, 6))
    if credit:
        (h / "stage").mkdir()
        con = sqlite3.connect(h / "stage" / "credited.sqlite")
        con.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        con.execute("CREATE TABLE rounds (round INTEGER PRIMARY KEY, status TEXT NOT NULL, games INTEGER, rows INTEGER)")
        con.execute("INSERT INTO meta VALUES ('run_fingerprint', ?)", (fp,))
        for r, s in credit.items():
            con.execute("INSERT INTO rounds VALUES (?, ?, 0, 0)", (r, s))
        con.commit()
        con.close()
    return h, fp


def run_state(h, fp, m=1085.2):
    """One decision at steady m (the PC's wall together with the clock lines'): the last line, or the STOP."""
    try:
        return ST.run(h, fp, mono=lambda: m, wall=lambda: m + WALL_OFF)
    except W.Stop as e:
        return ("STOP", e.code, str(e)[:200])
    except Exception as e:  # noqa: BLE001   a plant may make it crash: a FAIL of this check
        return ("crashed", repr(e)[:200])


def head(r):
    """The state part of the last line ('state: k .., now_s .., c4_rows ..'), or the STOP as it stands."""
    return r.split(";")[0] if isinstance(r, str) else r


def tail(r):
    """The pilot part of the last line ('pilot: ...'), or the STOP as it stands."""
    return r.split("; ", 1)[1] if isinstance(r, str) and "; " in r else r


def bounds_of(name):
    """PILOT.1.json's "bounds" of the home made by make_home(name), or what stands instead."""
    try:
        return json.loads((WORK / f"h_{name}" / "pilot" / "PILOT.1.json").read_text(encoding="ascii"),
                          parse_float=Decimal)["bounds"]
    except Exception as e:  # noqa: BLE001
        return repr(e)[:150]


def state_of(h, k=1):
    return json.loads((h / "state" / f"state.{k}.json").read_text(encoding="ascii"))


def pilot_of(h):
    return json.loads((h / "pilot" / "pilot.json").read_text(encoding="ascii"), parse_float=Decimal)


def names(h, sub):
    d = h / sub
    return sorted(p.name for p in d.iterdir()) if d.is_dir() else []


WANT = {"rounds_whole": ("int", "2"), "queues_empty_at_start": ("bool", "True"), "carry_in_rows": ("int", "0"),
        "cohort_games": ("int", "800"), "cohort_raw_rows": ("int", "104000"), "cohort_c4_rows": ("int", "101920"),
        "cohort_seconds": ("int", "961"), "games_per_h": ("Decimal", "4198.259"),
        "c1_raw_rows_per_s": ("Decimal", "151.768"), "c2_raw_rows_per_s": ("Decimal", "13506.493"),
        "c3_games_per_s": ("Decimal", "200.000"), "c4_kept_rows_per_s": ("Decimal", "14560.000"),
        "longest_game_s": ("int", "10"), "match_games_per_h": ("int", "0")}


def vals(h):
    """The 14 values of pilot.json as (type, text), or what stands instead."""
    try:
        p = pilot_of(h)
        return {k: (type(p[k]).__name__, str(p[k])) for k in WANT}
    except Exception as e:  # noqa: BLE001
        return repr(e)[:150]


def want(**over):
    d = dict(WANT)
    d.update(over)
    return d


def pilot_case(name, **kw):
    """(the pilot text of the state, the 14 values or what stands instead) of one decision on a fresh home."""
    h, fp = make_home(name, **kw)
    r = run_state(h, fp)
    return (state_of(h)["pilot"] if isinstance(r, str) else r), vals(h)


# ---- C: the state ---------------------------------------------------------------------------------------------
def part_s():
    h, fp = make_home("s1")
    r = run_state(h, fp)
    led = (h / "state" / "C4.1.json").read_bytes()
    pj = (h / "pilot" / "pilot.json").read_bytes()
    st = state_of(h)
    reps = [(h / "rounds" / f"r000{i}" / "report.json").read_bytes() for i in (1, 2)]
    check("S1 clean: the line; now_s 1086 and c4_rows 101920 (ints); sources.c4_rows names C4.1.json by absolute path "
          "and sha256; the ledger [[1, sha, 50900], [2, sha, 51020]] and its sum; lag_s 80.000, server_now L+1005.200, "
          "clock_n 6, the server's text; the pilot written",
          (r, st["now_s"], type(st["c4_rows"]), st["c4_rows"],
           st["sources"] == {"c4_rows": {"path": str((h / "state" / "C4.1.json").resolve()), "sha256": sha(led)}},
           json.loads(led) == {"c4_rows": 101920, "k": 1, "rounds": [[1, sha(reps[0]), 50900], [2, sha(reps[1]), 51020]],
                               "run_fingerprint": fp, "schema": 1},
           st["lag_s"], st["server_now"], st["clock_n"], st["clock_server_text"], st["pilot"], st["run_fingerprint"]),
          (f"state: k 1, now_s 1086, c4_rows 101920; pilot: written: {sha(pj)[:12]}", 1086, int, 101920, True, True,
           "80.000", f"{L_S + 1005}.200", 6, "2026-11-30T06:16:45Z", f"written: {sha(pj)[:12]}", fp))
    check("S1 the other keys, each an int or a text: partial and waiting counts 0; the state's key set",
          sorted(st), sorted(["now_s", "c4_rows", "sources", "run_fingerprint", "clock_n", "clock_server_text",
                              "server_now", "lag_s", "partial_rounds", "partial_games", "partial_raw_rows",
                              "waiting_rounds", "waiting_games", "waiting_raw_rows", "pilot"]))
    check("S2 the PC's wall clock 25,178 s ahead of the server (the fixture): now_s 1086, not 26184",
          (st["now_s"], round(1085.2 + WALL_OFF - L_S - 1000 + 1080.0 - 1085.2 + 1005.2, 1)), (1086, 26183.2))
    h, fp = make_home("s3")
    check("S3 exactly on a whole second (raw L+1005.000, lag 80.000): now_s 1085; the texts rounded up",
          (head(run_state(h, fp, m=1085.0)), state_of(h)["now_s"], state_of(h)["server_now"]),
          ("state: k 1, now_s 1085, c4_rows 101920", 1085, f"{L_S + 1005}.000"))
    h, fp = make_home("s4")
    run_state(h, fp)
    before = {n: (h / "state" / n).read_bytes() for n in names(h, "state")}
    (h / "clock" / "journal.jsonl").unlink()
    r1 = run_state(h, fp)
    h2, fp2 = make_home("s4b", clock=lambda f: clock_b(f)[1:])
    r2 = run_state(h2, fp2)
    check("S4 no clock journal (after a first decision), and no lag bound (the accepted line alone): exit 9 naming the "
          "clock; no new file; the earlier files keep their bytes",
          (r1[:2], "no clock line of this run" in r1[2], r2[:2], "no lag bound" in r2[2],
           {n: (h / "state" / n).read_bytes() for n in names(h, "state")} == before, names(h2, "state")),
          (("STOP", 9), True, ("STOP", 9), True, True, []))
    h, fp = make_home("s5", clock=lambda f: [clock_b(f)[0], cline(f, 6, 1070.1, 1080.0, L_MS - 200000)])
    r = run_state(h, fp)
    check("S5 the server's time plus the lag before the lease start: exit 9 naming it; no state",
          (r[:2], "before the lease start" in r[2], names(h, "state")), (("STOP", 9), True, []))
    h, fp = make_home("s6")
    run_state(h, fp)
    k1 = {n: (h / "state" / n).read_bytes() for n in names(h, "state")}
    (h / "rounds" / "r0003").mkdir()
    (h / "rounds" / "r0003" / "report.json").write_bytes(report(fp, 3, 51111))
    r2 = run_state(h, fp)
    (h / "state" / "state.3.json").mkdir()
    r3 = run_state(h, fp)
    check("S6 a third round COMPLETE (51111): k 2, c4_rows 153031, a new ledger; k 1's files keep their bytes; a FOLDER "
          "named state.3.json is passed over (k 4)",
          (head(r2), json.loads((h / "state" / "C4.2.json").read_bytes())["c4_rows"],
           {n: (h / "state" / n).read_bytes() for n in k1} == k1, head(r3), (h / "state" / "state.3.json").is_dir()),
          ("state: k 2, now_s 1086, c4_rows 153031", 153031, True, "state: k 4, now_s 1086, c4_rows 153031", True))

    def s7_seals(f):
        d = dict(SEALS)
        d.update({(3, 0): (200, 26000), (3, 1): (200, 25000), (4, 0): (200, 26100)})
        return d
    h, fp = make_home("s7", reports=lambda f: {1: (50900, "complete"), 2: (51020, "complete"), 3: (0, "partial")},
                      seals=s7_seals, credit={3: "partial"})
    r = run_state(h, fp)
    st = state_of(h) if isinstance(r, str) else {}
    check("S7 round 3 decided PARTIAL (report kept_rows 0, credit's table) and round 4 WAITS (a range seal, no report): "
          "c4_rows 101920; partial 1 round, 400 games, 51000 rows; waiting 1 round, 200 games, 26100 rows",
          (r[:40] if isinstance(r, str) else r, [st.get(k) for k in ("partial_rounds", "partial_games", "partial_raw_rows",
                                                                     "waiting_rounds", "waiting_games",
                                                                     "waiting_raw_rows")]),
          ("state: k 1, now_s 1086, c4_rows 101920; ", [1, 400, 51000, 1, 200, 26100]))
    h, fp = make_home("s8")
    run_state(h, fp)
    (h / "rounds" / "r0001" / "report.json").write_bytes(report(fp, 1, 50901))
    r1 = run_state(h, fp)
    h2, fp2 = make_home("s8b")
    run_state(h2, fp2)
    shutil.rmtree(h2 / "rounds" / "r0002")
    r2 = run_state(h2, fp2)
    check("S8 a published report whose bytes changed, and one that is gone, since the ledger named it: exit 9 naming "
          "the round; no second ledger, no second state",
          (r1[:2], "rounds/r0001/report.json changed or went" in r1[2], r2[:2], "rounds/r0002/report.json" in r2[2],
           names(h, "state"), names(h2, "state")),
          (("STOP", 9), True, ("STOP", 9), True, ["C4.1.json", "state.1.json"], ["C4.1.json", "state.1.json"]))
    h, fp = make_home("s9")
    (h / "rounds" / "r0002" / "report.json").write_bytes(report("0" * 64, 2, 51020))
    r1 = run_state(h, fp)
    h2, fp2 = make_home("s9b")
    (h2 / "wire" / "ranges" / "r0003.w000.seal.json.zz").write_bytes(seal(fp2, 3, 0, 200, 1, run="0" * 64))
    r2 = run_state(h2, fp2)
    check("S9 a report of another run, a range seal of another run: exit 9 naming each; no state",
          (r1[:2], "r0002/report.json is not this run's" in r1[2], r2[:2], "r0003.w000.seal.json.zz" in r2[2],
           names(h, "state"), names(h2, "state")), (("STOP", 9), True, ("STOP", 9), True, [], []))
    h, fp = make_home("s11", clock=lambda f: clock_b(f) + [cline(f, 7, 1140.0, 1147.35, L_MS + 1002550)])
    r = run_state(h, fp, m=1150.0)
    check("S11 a newer accepted line with lag 77.250 at the decision: now_s 1083, lag_s 77.250; cohort_seconds stays "
          "961 (the pass line's upper_ms; the wrong way gives 958)",
          (head(r), state_of(h)["lag_s"] if isinstance(r, str) else None,
           vals(h).get("cohort_seconds") if isinstance(vals(h), dict) else vals(h)),
          ("state: k 1, now_s 1083, c4_rows 101920", "77.250", ("int", "961")))


# ---- D: the pilot ---------------------------------------------------------------------------------------------
def part_p():
    h, fp = make_home("p1")
    run_state(h, fp)
    pj, ev = (h / "pilot" / "pilot.json").read_bytes(), (h / "pilot" / "PILOT.1.json").read_bytes()
    src = {"path": str((h / "pilot" / "PILOT.1.json").resolve()), "sha256": sha(ev)}
    p = pilot_of(h)
    check("P1 clean: the 14 values with their types (three places for every rate)", vals(h), WANT)
    check("P1 the keys (14, run_fingerprint, sources); every key names PILOT.1.json by absolute path and sha256; the "
          "bytes sorted, no spaces, one line end; the rates written with three places",
          (sorted(p) == sorted(list(WANT) + ["run_fingerprint", "sources"]), p["run_fingerprint"] == fp,
           p["sources"] == {k: src for k in WANT}, pj.endswith(b"}\n") and b" " not in pj and pj.count(b"\n") == 1,
           [x in pj for x in (b'"games_per_h":4198.259,', b'"c3_games_per_s":200.000,', b'"c4_kept_rows_per_s":14560.000,')]),
          (True, True, True, True, [True, True, True]))
    h, fp = make_home("p3", reports=lambda f: {1: (50900, "complete")})
    r1 = run_state(h, fp)
    t1, n1 = state_of(h)["pilot"], names(h, "pilot")
    (h / "rounds" / "r0002").mkdir()
    (h / "rounds" / "r0002" / "report.json").write_bytes(report(fp, 2, 51020))
    run_state(h, fp)
    check("P3 round 2 not published: the state's pilot 'waiting: 1 of 2 rounds whole', no pilot files; the next call "
          "with round 2: P1's values, the state's pilot 'written: <sha12>'",
          (tail(r1), t1, n1, vals(h), state_of(h, 2)["pilot"] == f"written: {sha((h / 'pilot' / 'pilot.json').read_bytes())[:12]}"),
          ("pilot: waiting: 1 of 2 rounds whole", "waiting: 1 of 2 rounds whole", [], WANT, True))
    got = [pilot_case("p4a", reports=lambda f: {1: (50900, "complete"), 2: (0, "partial")}),
           pilot_case("p4b", reports=lambda f: {1: (50900, "complete")}, credit={2: "partial"})]
    check("P4 a pilot round decided partial (by its report; by credit's table before its report): 'cannot qualify: "
          "round 2 is partial', no pilot.json",
          [(t, isinstance(v, str)) for t, v in got], [("cannot qualify: round 2 is partial", True)] * 2)
    h, fp = make_home("p5")
    run_state(h, fp)
    before = {n: (h / "pilot" / n).read_bytes() for n in names(h, "pilot")}
    (h / "rounds" / "r0003").mkdir()
    (h / "rounds" / "r0003" / "report.json").write_bytes(report(fp, 3, 51111))
    run_state(h, fp)
    run_state(h, fp)
    check("P5 written once: two more calls, a third round published: pilot.json and PILOT.1.json byte for byte the same",
          ({n: (h / "pilot" / n).read_bytes() for n in names(h, "pilot")} == before, sorted(before)),
          (True, ["PILOT.1.json", "pilot.json"]))
    t1, v1 = pilot_case("p6a", pilot=lambda f: pilot_rec(f, packer={"busy_ms": 7700, "pieces": 8, "raw_rows": 104000,
                                                                     "restarted": 1}))
    t2, v2 = pilot_case("p6b", pilot=lambda f: pilot_rec(f, packer={"busy_ms": 7700, "pieces": 8, "raw_rows": 103999,
                                                                     "restarted": 0}))

    def p6c(f):
        d = dict(SEALS)
        d[(2, 1)] = (200, 25799)
        return d
    t3, v3 = pilot_case("p6c", seals=p6c)
    check("P6 the packer restarted: c2 bounded by the span, floor3(104000 / 961) = 108.220 (RR8, Fable's P20), the rest "
          "as P1; packer raw_rows 103999: refused naming both sums; a range seal with 25799 rows: refused naming slot 1 "
          "(RR6); no pilot.json in either",
          (v1, t2, isinstance(v2, str), t3.startswith("refused: slot 1: "), isinstance(v3, str)),
          (want(c2_raw_rows_per_s=("Decimal", "108.220")),
           "refused: the packer's raw_rows 103999 are not the slots' 104000", True, True, True))
    other = W.canon({"empty": True, "run": "0" * 64, "t": "start", "why": "a rehearsal"})
    gap = rows_default()
    gap[2] = dict(gap[2], first=202)            # slot 0 round 2 starts at 202: a gap after 200
    got = [pilot_case("p7a", pilot=lambda f: pilot_rec(f, slots=[slot0(), slot1(epochs=[1, 2])]))[1],
           pilot_case("p7b", journal=lambda f: [pas(f, "c3", 10, 0)] + journal_b(f))[1],
           pilot_case("p7c", journal=lambda f: journal_b(f, first=start(f, empty=False)))[1],
           pilot_case("p7d", journal=lambda f: [other] + journal_b(f))[1],
           pilot_case("p7e", rows=gap)[1]]
    q = ("bool", "False")
    check("P7 queues_empty_at_start false (carry_in_rows 104000): slot 1 epochs [1, 2]; the journal's first line a "
          "pass (N1, RR8: c3 0.832, c4 106.056); a first start with empty false; the first line of ANOTHER run (c3 and "
          "c4 as P1); slot 0's ranges with a gap",
          got, [want(queues_empty_at_start=q, carry_in_rows=("int", "104000")),
                want(queues_empty_at_start=q, carry_in_rows=("int", "104000"), c3_games_per_s=("Decimal", "0.832"),
                     c4_kept_rows_per_s=("Decimal", "106.056")),
                want(queues_empty_at_start=q, carry_in_rows=("int", "104000")),
                want(queues_empty_at_start=q, carry_in_rows=("int", "104000")),
                want(queues_empty_at_start=q, carry_in_rows=("int", "104000"))])

    def p8(f, later=True):
        j = journal_b(f)
        j[-1] = pas(f, "c4", 3700, 5, [2])                 # round 2's naming line without a reading
        return j + ([pas(f, "c3", 500, 0, upper=1110400)] if later else [])
    t1, v1 = pilot_case("p8", journal=p8)
    t2, v2 = pilot_case("p8b", journal=lambda f: p8(f, later=False))
    check("P8 round 2's naming line without a reading, the next pass line with one (L+1110400): cohort_seconds 991, the "
          "rest as P1; P8b no line with a reading after it: 'waiting: ...' naming round 2's moment, no pilot.json",
          (v1, t2, isinstance(v2, str)),
          (want(cohort_seconds=("int", "991")), "waiting: 2 of 2 rounds whole; round 2 has no publish moment yet", True))
    t, v = pilot_case("p9", pilot=None)
    check("P9 no wire/PILOT.json.zz: the state's pilot 'no server record', no pilot.json", (t, isinstance(v, str)),
          ("no server record", True))
    bad = {"another run": lambda f: pilot_rec("0" * 64), "schema 2": lambda f: pilot_rec(f, schema=2),
           "a slot missing": lambda f: pilot_rec(f, slots=[slot0()]),
           "slots out of order": lambda f: pilot_rec(f, slots=[slot1(), slot0()]),
           "not canonical": lambda f: (json.dumps(json.loads(pilot_rec(f)), sort_keys=True) + "\n").encode("ascii"),
           "a key more": lambda f: pilot_rec(f, extra=1)}
    got = {k: pilot_case(f"p10_{i}", pilot=v) for i, (k, v) in enumerate(bad.items())}
    check("P10 a record of another run, schema 2, a slot missing, the slots out of order, bytes not canonical, a key "
          "more: each 'refused: ...', no pilot.json",
          {k: (t.startswith("refused: "), isinstance(v, str)) for k, (t, v) in got.items()},
          {k: (True, True) for k in bad})
    t, v = pilot_case("p11", pilot=lambda f: pilot_rec(f, slots=[slot0(span_ms=580000, last_end_ms=L_MS + 700000),
                                                                 slot1()]))
    check("P11 slot 0's span 580000 below its play 590000 (UTC stepped back): games_per_h 4242.930, c1 153.394 (RR2), "
          "cohort_seconds 971 (RR7)",
          v, want(games_per_h=("Decimal", "4242.930"), c1_raw_rows_per_s=("Decimal", "153.394"),
                  cohort_seconds=("int", "971")))
    got = [pilot_case("p12a", pilot=lambda f: pilot_rec(f, slots=[slot0(span_ms=0, play_ms=0, longest_ms=0,
                                                                         last_end_ms=L_MS + 120000), slot1()]))[1],
           pilot_case("p12b", pilot=lambda f: pilot_rec(f, packer={"busy_ms": 0, "pieces": 8, "raw_rows": 104000,
                                                                   "restarted": 0}))[1],
           pilot_case("p12c", journal=lambda f: [x.replace(b'"moved":9', b'"moved":0').replace(b'"moved":5', b'"moved":0')
                                                 for x in journal_b(f)])[1]]
    z = ("int", "0")
    check("P12 zeros, each the int 0 and no traceback: a slot with games and time 0 (games_per_h, c1); busy_ms 0 (c2); "
          "no pass that moved a unit (c3, c4)",
          got, [want(games_per_h=z, c1_raw_rows_per_s=z, longest_game_s=("int", "10")),
                want(c2_raw_rows_per_s=z), want(c3_games_per_s=z, c4_kept_rows_per_s=z)])

    def p15(f, at):
        j = journal_b(f)
        j.insert(at, start(f, empty=False, why="a restart"))
        return j
    got = [pilot_case("p15a", journal=lambda f: p15(f, 6))[1], pilot_case("p15b", journal=lambda f: p15(f, 7))[1]]
    hb = dict(c3_games_per_s=("Decimal", "0.832"), c4_kept_rows_per_s=("Decimal", "106.056"))    # RR8, Fable's P19
    check("P15 a second start line of this run before the end line: c3 floor3(800 / 961) = 0.832 and c4 "
          "floor3(101920 / 961) = 106.056 (RR8, Fable's P19), the rest as P1 (queues true); after the end line: P1",
          got, [want(**hb), WANT])

    def p16(f):
        j = journal_b(f)
        j[3:3] = [other, W.canon({"kind": "c3", "ms": 99000, "moved": 9, "new_reports": [], "run": "0" * 64,
                                  "t": "pass", "upper_ms": None})]
        return j
    check("P16 a start line and a pass line (ms 99000, moved 9) of another run inside the pilot: never counted, never a "
          "restart (P1)", pilot_case("p16", journal=p16)[1], WANT)
    check("P17 the reports in the other order (round 2 named first): the end moment is the latest: P1 (the wrong way "
          "gives 660)", pilot_case("p17", journal=lambda f: journal_b(f, swap=True))[1], WANT)
    t, v = pilot_case("p18", journal=lambda f: journal_b(f, up1=1080400, up2=1012000))

    def p18b(f):
        j = journal_b(f, up1=1080400, up2=1012000)
        j.insert(4, start(f, empty=False, why="a restart"))
        return j
    check("P18 the later moment line with the LOWER value (L+1012000 after L+1080400): cohort_seconds 961, counted to the "
          "LAST line (c3 200.000, c4 14560.000); a start line between the two lines: the bounds over 961 (RR8, P19)",
          [v, pilot_case("p18b", journal=p18b)[1]], [WANT, want(**hb)])
    home = {k: "bounded by the cohort's span: the home loop (journal line 7) was started again"
            for k in ("c3_games_per_s", "c4_kept_rows_per_s")}
    first = {k: ("bounded by the cohort's span: the home loop (its first line of this run, journal line 1, is not a "
                 "start line) was started again") for k in ("c3_games_per_s", "c4_kept_rows_per_s")}
    check("P19 PILOT.1.json names the home loop's bounds and the line: the start line at journal line 7 (P15); this "
          "run's first line a pass (P7); none in P1",
          (bounds_of("p15a"), bounds_of("p7b"), bounds_of("p1")), (home, first, {}))
    check("P20 PILOT.1.json names the packer's bound (P6: restarted 1); none for the home loop there",
          bounds_of("p6a"), {"c2_raw_rows_per_s": "bounded by the cohort's span: the packer (restarted 1) was started "
                                                  "again"})
    both = {"busy_ms": 7700, "pieces": 8, "raw_rows": 104000, "restarted": 1}
    stepped = [slot0(span_ms=580000, last_end_ms=L_MS + 700000), slot1()]
    got = [pilot_case("p21a", journal=lambda f: p15(f, 6), pilot=lambda f: pilot_rec(f, packer=both))[1],
           pilot_case("p21b", journal=lambda f: p15(f, 6), pilot=lambda f: pilot_rec(f, slots=stepped, packer=both))[1]]
    check("P21 both restarts at once: c2 108.220, c3 0.832, c4 106.056; on P11's stepped-back day every bound over "
          "RR7's 971, never 961: c2 107.106, c3 0.823, c4 104.963 (Fable's P21)",
          got, [want(c2_raw_rows_per_s=("Decimal", "108.220"), **hb),
                want(games_per_h=("Decimal", "4242.930"), c1_raw_rows_per_s=("Decimal", "153.394"),
                     cohort_seconds=("int", "971"), c2_raw_rows_per_s=("Decimal", "107.106"),
                     c3_games_per_s=("Decimal", "0.823"), c4_kept_rows_per_s=("Decimal", "104.963"))])
    h, fp = make_home("p22")
    bad = b"not json\n"
    (h / "pilot").mkdir()
    (h / "pilot" / "PILOT.1.json").write_bytes(bad)
    r = run_state(h, fp)
    try:
        sp = state_of(h)["pilot"]
    except Exception as e:  # noqa: BLE001   the code before R1 crashes and writes no state
        sp = repr(e)[:150]
    lead = "refused: home/pilot/PILOT.1.json cannot be read ("
    check("P22 (Opus: Fable's R1, her A8) a PILOT.1.json that is no JSON, no pilot.json: a refusal, never a traceback; "
          "the state written with it; the evidence's bytes kept; no pilot.json",
          (head(r), str(tail(r)).startswith(f"pilot: {lead}"), str(sp).startswith(lead), names(h, "pilot"),
           (h / "pilot" / "PILOT.1.json").read_bytes() == bad),
          ("state: k 1, now_s 1086, c4_rows 101920", True, True, ["PILOT.1.json"], True))
    got = {}
    for tag, bad_values in (("null", None), ("5", 5), ("list", sorted(WANT))):
        h, fp = make_home(f"p23_{tag}")
        evb = json.dumps({"run_fingerprint": fp, "values": bad_values}).encode("ascii")
        (h / "pilot").mkdir()
        (h / "pilot" / "PILOT.1.json").write_bytes(evb)
        r = run_state(h, fp)
        try:
            sp = state_of(h)["pilot"]
        except Exception as e:  # noqa: BLE001   the code before RV1 crashes and writes no state
            sp = repr(e)[:150]
        got[tag] = (head(r), tail(r), sp, names(h, "pilot"), (h / "pilot" / "PILOT.1.json").read_bytes() == evb)
    no = "refused: home/pilot/PILOT.1.json is not this run's evidence"
    check("P23 (Opus: Fable's RV1) this run's evidence whose values is null, 5 or a list of the 14 names: a refusal "
          "each, never a traceback; the state written; the evidence's bytes kept; no pilot.json",
          got, {t: ("state: k 1, now_s 1086, c4_rows 101920", f"pilot: {no}", no, ["PILOT.1.json"], True)
                for t in ("null", "5", "list")})


# ---- the command line -----------------------------------------------------------------------------------------
def part_cli():
    def cli(h, fp):
        p = subprocess.run([sys.executable, "-I", "-B", str(STATE), "--home", str(h), "--fingerprint", fp],
                           capture_output=True, text=True, timeout=120)
        out = (p.stdout + p.stderr).strip().splitlines()
        return p.returncode, (out[-1] if out else "")

    tm, tw = time.monotonic(), time.time()
    off = tw - tm

    def live(f):
        return [W.canon({"impl": IMPL, "look": 1, "mono": tm - 99.5, "mono0": tm - 100.0, "n": 5, "ok": False,
                         "platform": sys.platform, "run": f, "state": "play", "t": "clock", "utc_ms": L_MS + 930000,
                         "wall": tm - 99.5 + off, "why": "the first of two looks"}),
                W.canon({"impl": IMPL, "look": 2, "mono": tm - 30.0, "mono0": tm - 30.5, "n": 6, "ok": True,
                         "platform": sys.platform, "run": f, "state": "play", "t": "clock", "utc_ms": L_MS + 1000000,
                         "wall": tm - 30.0 + off, "why": None})]
    h, fp = make_home("cli0", clock=live)
    r0 = cli(h, fp)
    r2 = cli(h, "XYZ")
    r3 = cli(h, "0" * 64)
    h9, fp9 = make_home("cli9", clock=None)
    r9 = cli(h9, fp9)
    check("CLI exit 0 'state: k 1, now_s ...'; exit 2 a fingerprint that is not 64 hex; exit 3 another run's "
          "fingerprint; exit 9 no clock journal",
          (r0[0], r0[1].startswith("state: k 1, now_s 11"), r2, r3[0], r3[1].startswith("state: STOP (3): "),
           r9[0], r9[1].startswith("state: STOP (9): no state: the clock: no clock line of this run")),
          (0, True, (2, "state: STOP (2): --fingerprint must be 64 lowercase hex digits"), 3, True, 9, True))


for nm, f in (("S", part_s), ("P", part_p), ("CLI", part_cli)):
    try:
        f()
    except Exception:  # noqa: BLE001   a crash inside a part is one FAIL, and the other parts still run
        check(f"{nm} ran to its end", traceback.format_exc().rstrip()[-300:], "no exception")
leftover = [str(p) for p in (TREE / "home").rglob("__pycache__")]
failed = [n for n, ok in RESULTS if not ok]
print(f"{len(RESULTS) - len(failed)} of {len(RESULTS)} checks pass")
print("ALL PASS" if not failed and RESULTS else f"{len(failed)} failed: {failed}")
sys.exit(0 if not failed and RESULTS else 1)
