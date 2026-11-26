"""test_clock.py: home/clock.py (v16: the server's time for home's decisions) against known answers written BEFORE the
code (tmp/opus_scratch/clock/KNOWN_ANSWERS_clock_by_opus.md on the PC: M1 to M10, C1 to C12 and ADDENDA 1 to 7, read
by Fable). Standard library only; a PLAIN interpreter; Windows (the home PC).

    test_clock.py <tree> <a NEW folder> [plantN] [pythons=PATH;PATH]

<tree> holds home/ (clock.py, fetch.py), run/ (worker.py, packer.py) and tests/fake_transport.py; they are copied into
the new folder and a plant changes the copy's home/clock.py only. measure runs as its own process through the local
transport (tests/fake_transport.py, byte for byte v15's). THE FAKE GUARD is this test: it writes ROOT/CLOCK.json whole
(a dot-named part, then os.replace) with the fake server's clock = the PC's wall - 25,178 s; a watcher thread writes
the next record when measure's journal gains a line. The helper is called in-process with stand-in clocks.
H   C1 the line's S/1000 + the steady time since, whatever the PC's own offset (+25,178 s, -3,600 s); C2 a restart;
    C3 the Windows Update example, 119 s accepted, 121 s refused; C4 no journal, only ok-false lines; C5 only another
    run's lines; C6 another impl, another platform; C7 (with S3) a child's monotonic clock right after its parent's,
    for every pair of the given Pythons; C8 lines that are not the exact record skipped, a whole newer line without its
    line end too; C9 server_text the floor; C11 an ok line before three ok-false lines decides; C12 a line 6 hours old.
M   M1 the lines' form; M2 two looks: exit 0, the last line (n, the server's time, the offset); M2 n unchanged;
    M2c (+25,170 s on the second record); M2b (1 s back); M3; M4 six forms; M5; M6; M7 one look; M7b; the older
    branch's positive (R2: server_now about 200 s behind) and negative (ADDENDUM 5's addition); M7c +300 s on both
    looks, +25,170 s on the first only (server_now still from the old line); M1c and C10 through a stand-in sender
    whose get takes 5 s; S1 a leftover look.part; S2 a journal whose last line was cut; the length race (a longer
    record between the listing and the get); M8 exit 2 (three wrong calls), 6, 7, 8 and 4.
D   ADDENDUM 8 (M7d, Fable's F-CLOCK-1): D1 the same record three times inside 90 s: "clock: unchanged", ONE ok line,
    server_now = a control home's; D2 the same record 100 s after the line: exit 9 "does not write", the old line
    decides; D3 n + 1 inside the window: a new ok line; D4 n equal with utc_ms changed: exit 9.
PLANTS (each must make the test fail; in home/clock.py; the checks each fails, as known before the runs):
plant1 mono and wall read before the get (M1c, C10); plant2 M2c off (M2c, R2's negative, M7c's negative text);
plant3 M2b off (M2b); plant4 n advanced not asked (M2 n unchanged, D2); plant5 M7c's 120 s off (M7c, M7c's negative);
plant6 the older branch off (R2, R2's negative, D2); plant7 M7b off (M7b); plant8 M5 off (M5); plant9 M6 off (M6);
plant10 M4's schema off (M4); plant11 C2 off (C2); plant12 C3 off (C3); plant13 C6 off (C6); plant14 C8's line end
off (C8); plant15 an ok-false line decides (C4, C11, M7b, D1, D2, D4); plant16 S1 off (S1); plant17 S2 off (S2);
plant18 M7d off (D1, D4); plant19 M7d (a) off (D4).
"""
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path

if len(sys.argv) < 3:
    print("usage: test_clock.py <tree> <a NEW folder> [plantN] [pythons=PATH;PATH]")
    sys.exit(2)
SRC_TREE, WORK = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
PLANT, PYTHONS = None, [sys.executable]
for x in sys.argv[3:]:
    if x.startswith("plant"):
        PLANT = x
    elif x.startswith("pythons="):
        PYTHONS = [p for p in x.split("=", 1)[1].split(";") if p]
    else:
        print(f"STOP: not understood: {x}")
        sys.exit(2)
if WORK.exists():
    print(f"STOP: {WORK} exists already (a NEW folder)")
    sys.exit(2)
WORK.mkdir(parents=True)
TREE = WORK / "tree"
for sub in ("home", "run"):
    shutil.copytree(SRC_TREE / sub, TREE / sub, ignore=shutil.ignore_patterns("__pycache__"))
(TREE / "tests").mkdir()
shutil.copy2(SRC_TREE / "tests" / "fake_transport.py", TREE / "tests" / "fake_transport.py")
FAKE, CLOCK = TREE / "tests" / "fake_transport.py", TREE / "home" / "clock.py"
PLANTS = {
    "plant1": [("        data = self.get()\n        rec, bad = None, None\n",
                "        mono0, wall0 = time.monotonic(), time.time()\n        data = self.get()\n        rec, bad = None, None\n"),
               ("        mono, wall = time.monotonic(), time.time()\n", "        mono, wall = mono0, wall0\n")],
    "plant2": [("        if abs(du - dm) > AGREE_S:\n", "        if False:\n")],
    "plant3": [("        if u2 <= u1:\n", "        if False:\n")],
    "plant4": [("        if n2 == n1:\n", "        if False:\n")],
    "plant5": [("        if -OLDER_S <= x <= NEWER_S:                    # M7: one look\n",
                "        if -OLDER_S <= x:                    # M7: one look\n")],
    "plant6": [("        if -OLDER_S <= x <= NEWER_S:                    # M7: one look\n",
                "        if x <= NEWER_S:                    # M7: one look\n")],
    "plant7": [("        if a[\"rec\"][\"n\"] < line[\"n\"]:                   # M7b\n", "        if False:                   # M7b\n")],
    "plant8": [("                elif c[\"run_fingerprint\"] != self.fp:\n", "                elif False:\n")],
    "plant9": [("                    if c[\"state\"] == \"hold\":\n", "                    if False:\n")],
    "plant10": [("sorted(c) == CLOCK_KEYS and same(c[\"schema\"], 1)", "sorted(c) == CLOCK_KEYS and True")],
    "plant11": [("    if m < best[\"mono\"]:\n", "    if False:\n")],
    "plant12": [("    if abs((w - best[\"wall\"]) - (m - best[\"mono\"])) > STEADY_S:\n", "    if False:\n")],
    "plant13": [("    if best[\"impl\"] != impl() or best[\"platform\"] != sys.platform:\n", "    if False:\n")],
    "plant14": [("    for raw in data.split(b\"\\n\")[:-1]:", "    for raw in data.split(b\"\\n\"):")],
    "plant15": [("        if rec is not None and rec[\"ok\"] and rec[\"run\"] == fingerprint:\n",
                 "        if rec is not None and rec[\"run\"] == fingerprint:\n")],
    "plant16": [("                self.part.unlink()                      # S1:", "                pass                                    # S1:")],
    "plant17": [("        if self.cut_tail():\n", "        if False:\n")],
    "plant18": [("        if a[\"rec\"][\"n\"] == line[\"n\"]:                  # M7d:", "        if False:  # M7d:")],
    "plant19": [("            if a[\"rec\"][\"utc_ms\"] != line[\"utc_ms\"]:    # M7d (a)",
                 "            if False:    # M7d (a)")],
}
if PLANT:
    text = CLOCK.read_text(encoding="ascii")
    if PLANT not in PLANTS or any(text.count(old) != 1 for old, _ in PLANTS[PLANT]):
        print(f"STOP: {PLANT}: no such plant, or one of its texts does not stand exactly once")
        sys.exit(2)
    for old, new in PLANTS[PLANT]:
        text = text.replace(old, new)
    CLOCK.write_text(text, encoding="ascii", newline="\n")
    print(f"PLANT {PLANT} applied to the copy")
sys.path.insert(0, str(TREE / "home"))
import clock as CK  # noqa: E402
import worker as W  # noqa: E402   (clock imports fetch, which puts run/ on the path)

RESULTS = []
AHEAD = 25178                                           # the PC's clock ahead of the server's (measured 25 Nov)
FP = hashlib.sha256(b"test_clock's run").hexdigest()
IMPL = time.get_clock_info("monotonic").implementation
KEYS12 = sorted(["t", "run", "look", "n", "utc_ms", "state", "mono", "wall", "impl", "platform", "ok", "why"])


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
        check(f"{name} ran to its end", traceback.format_exc().rstrip()[-290:], "no exception")


def T(s):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(math.floor(s)))


# ---- H: the helper, in-process, stand-in clocks -----------------------------------------------------------------
S, M, WL = 1_800_000_000.0, 5000.0, 1_800_025_178.0     # a line: the server's time, the PC's steady and wall clocks


def jline(n=1, utc_s=S, mono=M, wall=WL, ok=True, run=None, impl=None, plat=None, why=None, look=2, state="play"):
    return W.canon({"impl": impl or IMPL, "look": look, "mono": mono, "n": n, "ok": ok, "platform": plat or sys.platform,
                    "run": run or FP, "state": state, "t": "clock",
                    "utc_ms": None if utc_s is None else int(round(utc_s * 1000)), "wall": wall, "why": why})


def jhome(name, *lines) -> Path:
    h = WORK / f"hj_{name}"
    (h / "clock").mkdir(parents=True)
    (h / "clock" / "journal.jsonl").write_bytes(b"".join(lines))
    return h


def now_at(h, m, w):
    """server_now at steady m and wall w, or the helper's refusal as ('refused', text)."""
    try:
        return CK.server_now(h, FP, mono=lambda: m, wall=lambda: w)
    except CK.ClockRefused as e:
        return ("refused", str(e))
    except Exception as e:  # noqa: BLE001   a plant may make the helper crash: a FAIL of this check, not of part H
        return ("crashed", repr(e)[:150])


def part_h():
    got = [now_at(jhome(f"c1_{i}", jline(wall=w)), M + 100, w + 100) for i, w in enumerate((WL, S + 25178, S - 3600))]
    check("C1 the line's S/1000 + 100 at steady and wall + 100: the same with the PC 25,178 s ahead, and 3,600 s behind",
          got, [S + 100] * 3)
    h = jhome("c2", jline())
    r = now_at(h, M - 1, WL - 1)
    check("C2 the steady clock below the line's: refused, 'the PC restarted since the last clock line'",
          (r[0], "the PC restarted since the last clock line" in r[1]) if isinstance(r, tuple) else r, ("refused", True))
    h = jhome("c3", jline(mono=1800.0))
    r = now_at(h, 7200.0, WL + 19800)
    r119, r121 = now_at(h, 2800.0, WL + 1119), now_at(h, 2800.0, WL + 1121)
    check("C3 the Windows Update example (steady 1,800 -> 7,200, wall + 19,800): refused naming a restart or a set "
          "clock; 119 s apart accepted, 121 s refused",
          ((r[0], "the PC restarted or its clock was set" in r[1]) if isinstance(r, tuple) else r, r119,
           r121[0] if isinstance(r121, tuple) else r121), (("refused", True), S + 1000, "refused"))
    r1 = now_at(WORK / "hj_none", M, WL)
    r2 = now_at(jhome("c4", jline(ok=False), jline(ok=False, utc_s=None, n=None, state=None, look=1)), M + 1, WL + 1)
    r3 = now_at(jhome("c5", jline(run="0" * 64), jline(run="1" * 64, n=2)), M + 1, WL + 1)
    check("C4 no journal, and only ok-false lines; C5 only another run's lines: refused 'no clock line of this run'",
          [x[0] == "refused" and "no clock line of this run" in x[1] if isinstance(x, tuple) else x for x in (r1, r2, r3)],
          [True, True, True])
    r1 = now_at(jhome("c6a", jline(impl="another_clock()")), M + 1, WL + 1)
    r2 = now_at(jhome("c6b", jline(plat="another_os")), M + 1, WL + 1)
    check("C6 a line of another monotonic clock, and of another platform: refused naming both",
          [x[0] == "refused" and ("another_clock()" in x[1] or "another_os" in x[1]) and IMPL in x[1]
           if isinstance(x, tuple) else x for x in (r1, r2)], [True, True])
    bad_spaces = (json.dumps(json.loads(jline(n=7)), sort_keys=True) + "\n").encode("ascii")
    extra = W.canon(dict(json.loads(jline(n=8)), extra=1))
    h = jhome("c8", jline(n=2, utc_s=S - 50), b"garbage\n", bad_spaces, extra,
              jline(n=9, utc_s=None), jline(n=3, utc_s=S), jline(n=4, utc_s=S + 77)[:-1])
    try:
        acc = CK.accepted(h, FP, mono=lambda: M + 1, wall=lambda: WL + 1)[0]["n"]
    except CK.ClockRefused as e:
        acc = str(e)
    check("C8 garbage, a line with spaces, one with an extra key, an ok line without utc_ms are skipped, and a whole "
          "newer line WITHOUT its line end: the newest valid ok line (n 3) decides", acc, 3)
    h = jhome("c9", jline())
    check("C9 server_text is the floor of server_now as YYYY-MM-DDTHH:MM:SSZ",
          CK.server_text(h, FP, mono=lambda: M + 100.7, wall=lambda: WL + 100.7), T(S + 100))
    h = jhome("c11", jline(), jline(ok=False, n=1, utc_s=S + 5000), jline(ok=False, n=1, utc_s=S + 5000),
              jline(ok=False, n=None, utc_s=None, state=None, look=2, why="no CLOCK.json yet"))
    check("C11 an ok line, then three ok-false lines (the guard gone): the ok line decides", now_at(h, M + 100, WL + 100),
          S + 100)
    h = jhome("c12", jline())
    check("C12 a line 6 hours old is used", now_at(h, M + 21600, WL + 21600), S + 21600)
    code = ("import subprocess, sys, time\n"
            "m0 = time.monotonic()\n"
            "o = subprocess.run([sys.argv[1], '-I', '-B', '-c', 'import time; print(repr(time.monotonic()))'],\n"
            "                   capture_output=True, text=True).stdout\n"
            "print(repr(m0), o.strip())\n")
    got = []
    for a in PYTHONS:
        for b in PYTHONS:
            r = subprocess.run([a, "-I", "-B", "-c", code, b], capture_output=True, text=True, timeout=120)
            try:
                m0, m1 = (float(v) for v in r.stdout.split())
                got.append(0 <= m1 - m0 <= 1.0)
            except ValueError:
                got.append(r.stdout + r.stderr)
    check(f"C7 (S3) a child's monotonic clock read right after its parent's is within 1 s and not smaller, for every "
          f"pair of {len(PYTHONS)} Python(s)", got, [True] * len(PYTHONS) ** 2)


# ---- M: measure through the fake transport; this test is the fake guard ---------------------------------------
def srv():
    return time.time() - AHEAD


def rec(n, utc_s, state="play", fp=None, **over):
    d = {"n": n, "run_fingerprint": fp or FP, "schema": 1, "state": state, "utc_ms": int(round(utc_s * 1000))}
    d.update(over)
    return W.canon(d)


def put_clock(root: Path, data: bytes) -> None:
    tmp = root / ".CLOCK.json.test.part"
    tmp.write_bytes(data)
    os.replace(tmp, root / "CLOCK.json")


def case(name, sender=None, gap=2.0, **cfg_over):
    root, home = WORK / f"root_{name}", WORK / f"home_{name}"
    root.mkdir()
    home.mkdir()
    cfg = {"transport": "local", "remote_root": str(root), "idle_s": 30, "transfer_s": 120, "python": sys.executable,
           "sender": str(sender or FAKE), "clock_second_look_s": gap}
    cfg.update(cfg_over)
    cp = WORK / f"cfg_{name}.json"
    cp.write_text(json.dumps({k: v for k, v in cfg.items() if v is not None}), encoding="ascii")
    return home, root, cp


def journal(home):
    j = home / "clock" / "journal.jsonl"
    return [json.loads(x) for x in j.read_bytes().split(b"\n")[:-1]] if j.exists() else []


def measure(home, cp, then=None, fp=FP, timeout=180):
    """clock.py measure as its own process; then(k) runs when the journal gains its k-th line of this measure (the
    fake guard's next write). (exit code, the last line, all the output)."""
    j = home / "clock" / "journal.jsonl"

    def count(otherwise):
        try:
            return j.read_bytes().count(b"\n")
        except OSError:                                 # none yet (0), or a journal that is a folder (case e4)
            return otherwise
    seen0 = count(0)
    stop = threading.Event()

    def watch():
        seen = seen0
        while not stop.is_set():
            n = count(seen)
            for k in range(seen + 1, n + 1):
                if then:
                    then(k - seen0)
            seen = max(seen, n)
            time.sleep(0.01)
    th = threading.Thread(target=watch, daemon=True)
    th.start()
    try:
        p = subprocess.run([sys.executable, "-I", "-B", str(CLOCK), "measure", "--home", str(home), "--fingerprint", fp,
                            "--config", str(cp)], capture_output=True, text=True, timeout=timeout)
    finally:
        stop.set()
        th.join()
    out = (p.stdout + p.stderr).strip()
    return p.returncode, (out.splitlines()[-1] if out else ""), out


def seed(home, n, age_s=0.0, utc_ms=None):
    """An accepted line of this run as measure writes it, taken age_s ago (utc_ms: the server's time then, or the one
    given); returns its utc_ms."""
    (home / "clock").mkdir(exist_ok=True)
    w, m = time.time() - age_s, time.monotonic() - age_s
    u = utc_ms if utc_ms is not None else int(round((w - AHEAD) * 1000))
    with open(home / "clock" / "journal.jsonl", "ab") as f:
        f.write(jline(n=n, utc_s=u / 1000, mono=m, wall=w))
    return u


def oks(home, skip=0):
    return [(x["look"], x["ok"], x["n"]) for x in journal(home)[skip:]]


def later(root, k_at, data_fn):
    def then(k):
        if k == k_at:
            put_clock(root, data_fn())
    return then


def part_m():
    home, root, cp = case("m2")
    put_clock(root, rec(5, srv()))
    rc, last, out = measure(home, cp, later(root, 1, lambda: rec(6, srv())))
    L, raw = journal(home), (home / "clock" / "journal.jsonl").read_bytes()
    off = re.search(r"offset (-?[0-9.]+) s", last)
    check("M2 no accepted line: two looks, exit 0; look 1 ok false 'the first of two looks', look 2 ok true with n 6; "
          "the last line names n 6, the server's time and the offset (about -25,178 s)",
          (rc, oks(home), L[0]["why"][:22] if L else None, last.startswith("clock: ok n 6, the server's time "),
           off is not None and -25184 < float(off[1]) < -25177),
          (0, [(1, False, 5), (2, True, 6)], "the first of two looks", True, True))
    check("M1 every line canonical with its twelve keys, t clock, this run, this process's impl and platform; one line a "
          "look, each ending in its line end",
          (all(sorted(x) == KEYS12 and x["t"] == "clock" and x["run"] == FP and x["impl"] == IMPL
               and x["platform"] == sys.platform for x in L),
           all(W.canon(json.loads(x)) == x + b"\n" for x in raw.split(b"\n")[:-1]), raw.endswith(b"\n"), len(L)),
          (True, True, True, 2))
    put_clock(root, rec(7, srv()))
    rc, last, out = measure(home, cp)
    check("M7 an accepted line: ONE look, ok, n 7, why null", (rc, oks(home, 2), journal(home)[2:3] and
                                                               journal(home)[2]["why"]), (0, [(2 - 1, True, 7)], None))
    put_clock(root, rec(3, srv()))
    rc, last, out = measure(home, cp)
    check("M7b n 3 smaller than the accepted line's 7: exit 9 naming it, its line ok false, the accepted line stays",
          (rc, last, oks(home, 3), CK.accepted(home, FP)[0]["n"]),
          (9, "clock: STOP (9): n 3 is smaller than the accepted line's 7 (the root was replaced or CLOCK.json lost)",
           [(1, False, 3)], 7))
    home, root, cp = case("m2n")
    put_clock(root, rec(5, srv()))
    rc, last, out = measure(home, cp)
    check("M2 n unchanged after the gap: exit 9, 'does not write CLOCK.json (n 5 unchanged after 2 s)', no ok line",
          (rc, last, [x["ok"] for x in journal(home)]),
          (9, "clock: STOP (9): the server's guard does not write CLOCK.json (n 5 unchanged after 2 s)", [False, False]))
    home, root, cp = case("m2c")
    put_clock(root, rec(5, srv()))
    rc, last, out = measure(home, cp, later(root, 1, lambda: rec(6, srv() + 25170)))
    check("M2c the second record 25,170 s ahead: exit 9 'not steady (it moved ... s while ... s passed here; or its "
          "guard paused before the first look)', no ok line",
          (rc, last.startswith("clock: STOP (9): the server's clock is not steady (it moved 2517"),
           last.endswith("; or its guard paused before the first look)"), [x["ok"] for x in journal(home)]),
          (9, True, True, [False, False]))
    home, root, cp = case("m2b")
    s0 = srv()
    put_clock(root, rec(5, s0))
    rc, last, out = measure(home, cp, later(root, 1, lambda: rec(6, s0 - 1)))
    check("M2b the second record 1 s back, n advanced: exit 9 'went back' (M2c lets it through), no ok line",
          (rc, last.startswith("clock: STOP (9): the server's clock went back (n 5 -> 6, utc_ms "),
           [x["ok"] for x in journal(home)]), (9, True, [False, False]))
    home, root, cp = case("m3")
    rc, last, out = measure(home, cp)
    check("M3 no CLOCK.json: exit 9, 'no CLOCK.json yet (the server's guard has not started)', one line ok false",
          (rc, last, oks(home)),
          (9, "clock: STOP (9): no CLOCK.json yet (the server's guard has not started)", [(1, False, None)]))
    s = srv()
    forms = [("spaces", (json.dumps(json.loads(rec(5, s))) + "\n").encode("ascii")),
             ("an extra key", rec(5, s, extra=1)), ("schema 2", rec(5, s, schema=2)), ("n 0", rec(0, s)),
             ("utc_ms below 1.7e12", rec(5, 1_000_000_000.0)), ("state other", rec(5, s, state="other"))]
    got = []
    for i, (what, data) in enumerate(forms):
        home, root, cp = case(f"m4_{i}")
        put_clock(root, data)
        rc, last, out = measure(home, cp)
        got.append((what, rc, "CLOCK.json is not the guard's record" in last))
    check("M4 six forms that are not the guard's record: exit 9 naming it", got, [(w, 9, True) for w, _ in forms])
    home, root, cp = case("m5")
    put_clock(root, rec(5, srv(), fp="0" * 64))
    rc, last, out = measure(home, cp)
    check("M5 another run's CLOCK.json: exit 9 naming it", (rc, "CLOCK.json is of another run" in last), (9, True))
    home, root, cp = case("m6")
    put_clock(root, rec(5, srv(), state="hold"))
    rc, last, out = measure(home, cp)
    check("M6 state hold: exit 9, 'the server's guard is in a HOLD (its clocks disagree): no clock line'",
          (rc, last, oks(home)),
          (9, "clock: STOP (9): the server's guard is in a HOLD (its clocks disagree): no clock line", [(1, False, 5)]))


def part_m7():
    home, root, cp = case("r2")
    seed(home, 10)
    put_clock(root, rec(11, srv() - 200))
    rc, last, out = measure(home, cp, later(root, 1, lambda: rec(12, srv() - 200)))
    L = journal(home)[1:]
    w1 = re.fullmatch(r"([0-9]+) s behind the last line extrapolated: a second look is taken", L[0]["why"] or "") \
        if L else None
    w2 = re.fullmatch(r"a second look: the first was ([0-9]+) s behind the last line extrapolated", L[1]["why"] or "") \
        if len(L) > 1 else None
    sn = CK.server_now(home, FP) - srv() if rc == 0 else None
    check("R2 the older branch's positive: the first look 200 s older, the second 200 s older too: exit 0; look 1 ok "
          "false '200 s behind ...: a second look is taken', look 2 ok 'a second look: the first was 200 s behind ...'; "
          "server_now about 200 s behind (199 to 205 s: the second record is about the gap old when it is read)",
          (rc, oks(home, 1), bool(w1) and 199 <= int(w1[1]) <= 202, bool(w2) and 199 <= int(w2[1]) <= 202,
           sn is not None and -205 <= sn <= -199), (0, [(1, False, 11), (2, True, 12)], True, True, True))
    home, root, cp = case("r2n")
    seed(home, 10)
    put_clock(root, rec(11, srv() - 200))
    rc, last, out = measure(home, cp, later(root, 1, lambda: rec(12, srv() + 25170)))
    check("M7 the older branch's negative (ADDENDUM 5's addition): the first look 200 s older, the second 25,170 s "
          "ahead: exit 9 with M2c's text, no new ok line",
          (rc, last.startswith("clock: STOP (9): the server's clock is not steady"), oks(home, 1)),
          (9, True, [(1, False, 11), (2, False, 12)]))
    home, root, cp = case("m7c")
    seed(home, 20)
    put_clock(root, rec(21, srv() + 300))
    rc, last, out = measure(home, cp, later(root, 1, lambda: rec(22, srv() + 300)))
    L = journal(home)[1:]
    w1 = re.fullmatch(r"([0-9]+) s ahead of the last line extrapolated: a second look is taken", L[0]["why"] or "") \
        if L else None
    w2 = re.fullmatch(r"the server's clock is ([0-9]+) s ahead of the last line extrapolated, confirmed by a second "
                      r"look", L[1]["why"] or "") if len(L) > 1 else None
    check("M7c +300 s on both looks: exit 0; look 1 ok false '... s ahead ...: a second look is taken'; look 2 ok, "
          "'the server's clock is x s ahead ..., confirmed by a second look', x between 295 and 302 (the second record "
          "is about the gap old when it is read)",
          (rc, oks(home, 1), bool(w1), bool(w2) and 295 <= int(w2[1]) <= 302),
          (0, [(1, False, 21), (2, True, 22)], True, True))
    home, root, cp = case("m7cn")
    s0 = seed(home, 30) / 1000
    m0 = time.monotonic()
    put_clock(root, rec(31, srv() + 25170))
    rc, last, out = measure(home, cp, later(root, 1, lambda: rec(32, srv())))
    sn = CK.server_now(home, FP)
    check("M7c +25,170 s on the first look only (the second at the line extrapolated): exit 9 with M2c's text; "
          "server_now still answers from the old line (within 2 s of it extrapolated)",
          (rc, last.startswith("clock: STOP (9): the server's clock is not steady"),
           abs(sn - (s0 + time.monotonic() - m0)) <= 2), (9, True, True))


SLOW = '''import json, os, subprocess, sys, time
FAKE, AHEAD, SIDE, RACE = {fake!r}, {ahead!r}, {side!r}, {race!r}
op, root, rel = sys.argv[1], sys.argv[2], sys.argv[3]
p = os.path.join(root, "CLOCK.json")
first = not os.path.exists(SIDE)
if op == "get" and rel == "CLOCK.json" and (not RACE or first):
    if not RACE:
        time.sleep(5)
    c = json.loads(open(p, "rb").read())
    c["n"] = c["n"] + (1 if not RACE else 1000)
    c["utc_ms"] = int((time.time() - AHEAD) * 1000)
    if RACE:
        c["state"] = "dispatch_end"
    tmp = os.path.join(root, ".slow.part")
    with open(tmp, "wb") as f:
        f.write((json.dumps(c, sort_keys=True, separators=(",", ":")) + "\\n").encode("ascii"))
    os.replace(tmp, p)
r = subprocess.run([sys.executable, "-I", "-B", FAKE] + sys.argv[1:])
if op == "get" and rel == "CLOCK.json":
    with open(SIDE, "a") as f:
        f.write(repr(time.monotonic()) + "\\n")
sys.exit(r.returncode)
'''


def part_slow():
    side = WORK / "side_m1c.txt"
    sender = WORK / "slow_sender.py"
    sender.write_text(SLOW.format(fake=str(FAKE), ahead=float(AHEAD), side=str(side), race=False), encoding="ascii")
    home, root, cp = case("m1c", sender=sender)
    put_clock(root, rec(5, srv()))
    rc, last, out = measure(home, cp)
    sn, fake_now = CK.server_now(home, FP) if rc == 0 else None, srv()
    L = journal(home)
    gets = [float(x) for x in side.read_text(encoding="ascii").split()] if side.exists() else []
    check("M1c each look's mono is read after its get returned (gets of 5 s through a stand-in sender): every line's "
          "mono is not smaller than the get's own return; exit 0",
          (rc, len(gets), [x["mono"] >= g for x, g in zip(L, gets)]), (0, 2, [True, True]))
    check("C10 right after the measure, server_now is not ahead of the fake server's clock and not more than 6 s behind",
          sn is not None and fake_now - 6 <= sn <= fake_now, True)
    side2 = WORK / "side_race.txt"
    sender2 = WORK / "race_sender.py"
    sender2.write_text(SLOW.format(fake=str(FAKE), ahead=float(AHEAD), side=str(side2), race=True), encoding="ascii")
    home, root, cp = case("race", sender=sender2)
    put_clock(root, rec(5, srv()))
    rc, last, out = measure(home, cp, later(root, 1, lambda: rec(1006, srv(), state="dispatch_end")))
    check("the length race: CLOCK.json replaced by a longer record between the listing and the get: fetched once more; "
          "exit 0, look 1 names the longer record (n 1005), look 2 ok (n 1006)",
          (rc, oks(home)), (0, [(1, False, 1005), (2, True, 1006)]))


def part_s():
    home, root, cp = case("s1")
    (home / "clock").mkdir()
    (home / "clock" / "look.part").write_bytes(b"a leftover of other bytes")
    put_clock(root, rec(5, srv()))
    rc, last, out = measure(home, cp, later(root, 1, lambda: rec(6, srv())))
    check("S1 a leftover look.part with other bytes: exit 0, the measure's own line decides (n 6), no look.part left",
          (rc, CK.accepted(home, FP)[0]["n"] if rc == 0 else last, (home / "clock" / "look.part").exists()),
          (0, 6, False))
    home, root, cp = case("s2")
    seed(home, 10)
    with open(home / "clock" / "journal.jsonl", "ab") as f:
        f.write(b'{"half a line')
    put_clock(root, rec(11, srv()))
    rc, last, out = measure(home, cp)
    raw = (home / "clock" / "journal.jsonl").read_bytes()
    check("S2 a journal whose last line was cut: the new line gets a line end first; exit 0, it decides (n 11), the "
          "half line stays a line of its own",
          (rc, CK.accepted(home, FP)[0]["n"] if rc == 0 else last, b'{"half a line\n{' in raw), (0, 11, True))


def part_e():
    got = []
    home, root, cp = case("e2a", remote_root=None)
    got.append(measure(home, cp)[0])
    home, root, cp = case("e2b")
    got.append(measure(WORK / "home_does_not_exist", cp)[0])
    got.append(measure(home, cp, fp="NOT HEX")[0])
    check("M8 exit 2: a config without remote_root, a --home that is no folder (still not there), a fingerprint that is "
          "not 64 hex digits", (got, (WORK / "home_does_not_exist").exists()), ([2, 2, 2], False))
    got = []
    for name, say, want in (("e6", "Host key verification failed.", 6), ("e7", "ssh: connect to host x: Connection "
                                                                              "refused", 7)):
        home, root, cp = case(name)
        put_clock(root, rec(5, srv()))
        root.with_name(root.name + ".plan.json").write_text(json.dumps({"list ": [{"say": say, "exit": 255}]}),
                                                           encoding="ascii")
        rc, last, out = measure(home, cp)
        got.append((rc, last.startswith(f"clock: STOP ({want}): "), journal(home)))
    check("M8 the host key (exit 6) and an unreachable server (exit 7) keep fetch's codes; no line written", got,
          [(6, True, []), (7, True, [])])
    home, root, cp = case("e8")
    put_clock(root, rec(5, srv()))
    (home / "clock").mkdir()
    lock = W.SlotLock(home / "clock")
    try:
        rc, last, out = measure(home, cp)
    finally:
        lock.release()
    check("M8 another measure holds home/clock/LOCK: exit 8, nothing done", (rc, last, journal(home)),
          (8, "clock: STOP (8): another measure holds home/clock/LOCK: nothing done", []))
    home, root, cp = case("e4")
    put_clock(root, rec(5, srv()))
    (home / "clock" / "journal.jsonl").mkdir(parents=True)
    rc, last, out = measure(home, cp)
    check("M8 a home file that cannot be written (the journal is a folder): exit 4", (rc, last.startswith(
        "clock: STOP (4): ")), (4, True))


def control_of(home, name):
    """A control home: the same journal, no measure."""
    ctl = WORK / f"home_{name}_control"
    (ctl / "clock").mkdir(parents=True)
    shutil.copy2(home / "clock" / "journal.jsonl", ctl / "clock" / "journal.jsonl")
    return ctl


def apart(home, ctl):
    """server_now of the two homes at one reading of the steady clock."""
    m = time.monotonic()
    return CK.server_now(home, FP, mono=lambda: m) - CK.server_now(ctl, FP, mono=lambda: m)


def part_d():
    same_why = "the same record as the accepted line (n 100): the line stays"
    home, root, cp = case("d1")
    u = seed(home, 100, age_s=60)
    ctl = control_of(home, "d1")
    put_clock(root, rec(100, u / 1000))
    runs = [measure(home, cp) for _ in range(3)]
    check("D1 (M7d b) a line n 100 taken 60 s ago, CLOCK.json the same record: three measures, each exit 0 'clock: "
          "unchanged n 100 (the same record'; ONE ok line and three ok-false lines with (b)'s why; server_now equals "
          "the control home's within 1 s",
          ([(rc, last.startswith("clock: unchanged n 100 (the same record")) for rc, last, _ in runs],
           [(x["ok"], x["why"]) for x in journal(home)], abs(apart(home, ctl)) <= 1.0),
          ([(0, True)] * 3, [(True, None)] + [(False, same_why)] * 3, True))
    home, root, cp = case("d2")
    u = seed(home, 100, age_s=100)
    ctl = control_of(home, "d2")
    put_clock(root, rec(100, u / 1000))
    rc, last, out = measure(home, cp)
    check("D2 (M7d c) the same record with the line taken 100 s ago: exit 9 'does not write CLOCK.json (n 100 "
          "unchanged after 2 s)', two ok-false lines, the old line decides (its mono); server_now equals the "
          "control's within 1 s",
          (rc, last, [x["ok"] for x in journal(home)], CK.accepted(home, FP)[0]["mono"] == journal(ctl)[0]["mono"],
           abs(apart(home, ctl)) <= 1.0),
          (9, "clock: STOP (9): the server's guard does not write CLOCK.json (n 100 unchanged after 2 s)",
           [True, False, False], True, True))
    home, root, cp = case("d3")
    seed(home, 100, age_s=30)
    put_clock(root, rec(101, srv()))
    rc, last, out = measure(home, cp)
    check("D3 n 101 inside the window (the line 30 s ago): exit 0 'clock: ok n 101', the accepted line is n 101",
          (rc, last.startswith("clock: ok n 101,"), CK.accepted(home, FP)[0]["n"]), (0, True, 101))
    home, root, cp = case("d4")
    u = seed(home, 100, age_s=30)
    put_clock(root, rec(100, u / 1000 + 5))
    rc, last, out = measure(home, cp)
    check("D4 (M7d a) n 100 again with utc_ms + 5,000 (the line 30 s ago): exit 9 with (a)'s text, one ok-false line, "
          "the old line decides",
          (rc, last, [x["ok"] for x in journal(home)], CK.accepted(home, FP)[0]["utc_ms"]),
          (9, f"clock: STOP (9): n 100 unchanged but utc_ms changed ({u} -> {u + 5000}): not one guard's chain (the "
              f"root was replaced)", [True, False], u))


for nm, fn in (("H", part_h), ("M", part_m), ("M7", part_m7), ("SLOW", part_slow), ("S", part_s), ("D", part_d),
               ("E", part_e)):
    safe(nm, fn)
leftover = [str(p) for p in TREE.rglob("__pycache__")]
check("no __pycache__ in the copied tree", leftover, [])
failed = [n for n, ok in RESULTS if not ok]
print(f"{len(RESULTS) - len(failed)} of {len(RESULTS)} checks pass")
print("ALL PASS" if not failed and RESULTS else f"{len(failed)} failed: {failed}")
sys.exit(0 if not failed and RESULTS else 1)
