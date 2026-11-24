"""test_clockwatch.py <run/clockwatch.py> <a new folder> [plant1 ... plant7]

Known answers, written before the module ran (FORMATS.md 2.9, section 1.8 point 1). Standard library only.
With a plant the test patches ONE line of a copy of the module and must then FAIL (exit 1); a plant whose line is
not found exactly once is exit 3.

K  the rule, with injected clocks. Anchor (utc 1000, steady 50, boot 70); D = 1100 unless said.
  K1  (1050,100,120): 50 s left by all three -> open, left 50.
  K2  (1100,150,170): left 0 -> come.
  K3  a suspension of 1,500 s after 30 s (2530, 80, 1600): UTC and boot say come, steady alone would grant 70 s
      -> come, left -1430.
  K4  UTC jumps 3,600 s ahead alone (4630, 80, 100): UTC alone says come and stands 3,600 > 10 s ahead -> hold.
  K5  UTC 5 s ahead alone at the bound (1101, 146, 166) -> come.     K6a exactly 10 s ahead (1105,145,165) -> come.
  K6b 10.5 s ahead (1105.5,145,165) -> hold.
  K7  UTC set BACK 3,600 s (-2500, 150, 170): steady and boot say come -> come, left 0.
  K8  the latch: (1101,146,166) come; then UTC corrected back, (1096,146,166), every clock 4 s left -> still come.
      Control: a fresh rule that only sees (1096,146,166) -> open, left 4.
  K9  no boot clock, anchor (1000, 50, none): the suspension of K3 shows as UTC alone 1,500 s ahead of the steady
      clock -> hold; (1100,150,none) -> come.
  K10 D tightened to 1060: (1070,120,140) -> come. A LATER D offered (1200): refused, D stays 1100, the refusal is
      kept; (1150,200,220) -> come.
  K11 (1053,100,120): UTC 3 s ahead -> left 47 (the earliest), steady cutoff 100 + 47 = 147; at K2 it is 150.
  K12 the trigger D - 2 at (1098,148,168): come; D itself: open, left 2.
  K13 a hold stays a hold: after K4, (4630, 200, 220) -> hold; hold() true.
  K14 dispatch end 1040, D 1100 at (1050,100,120): dispatch end come, D open, no hold.
  K15 the boot clock alone says come (1030, 80, 1600) -> come.
R  the watch on a real child process (python spinning; steady = the system's, UTC and boot = the system's plus an
   offset the test moves). The witness is the test's own wait for the child, never the watch's record.
  R1  D 1.2 s ahead, allowance 0.5, dispatch end already passed: fired "cutoff", the child gone before D and not
      before the trigger, not late, no alarm; the dispatch end alone was no reason.
  R2  (Astra 161219Z) look 0.5 s, allowance 0.25, D at 0.85: the trigger (0.60) falls just after a look: the child
      is gone before D (a watch that sleeps to its next look stops it at 1.0).
  R3  a wake on the same boot beyond D: after 0.4 s the boot clock jumps 1,500 s: fired "cutoff", recorded late.
  R4  UTC jumps 3,600 s alone after 0.4 s: fired "clock", hold() true.
  R5  a stop that does nothing: fired, the child still there at D -> alarm, no "gone" reading, the watch ends.
  R6  the wait ends by itself (close at 0.3 s, trigger at 0.7): never fires, the child lives on past D.
  R7  D tightened during the wait (30 s -> 1.2 s, read at 0.5 s, 0.2 s before its trigger): the child gone before
      the new D, not late.
  R8  a tighter D found late (seen at 0.5 s, D was 0.2 s): stopped at once, recorded late with the real time.
  R9  a later D offered during the wait: refused, the child gone before the first D.
  R10 the child ends by itself: the watch sees it and ends without firing.
  Version 2 (Astra 165352Z):
  R11 a tighter D found AFTER its trigger and BEFORE D (30 s -> 0.9 s with an allowance of 0.7: the trigger was at
      0.2, the schedule is read at 0.5): stopped at once, gone before D, no alarm; late and late_discovery true,
      decided_after_cutoff and gone_after_cutoff false. (R1: all four false. R8: late and decided_after_cutoff.)
  R12 a schedule read that stalls (every read sleeps 3 s), D at 0.8, allowance 0.3: the child is gone before D,
      and close() returns in under a second with reader_stalled true.
  Version 4 (Astra 170921Z):
  R16 another thread tightens D through the bounds while the watch sleeps a LONG look (look 1.0 s; 30 s -> 0.8 s,
      set at 0.2 s, 0.4 s before its trigger with an allowance of 0.2): the child is gone before the new D and
      the record is not late (a watch that is not woken sleeps to 1.0 s).
  Version 3 (Astra 165616Z, Neon 170114Z):
  R14 the stop works at once, but the handle needs 0.45 s to answer "gone" (D 1.0 s, allowance 0.3): the test's
      own wait sees the child end before D; the watch can first confirm it after D: gone_after_cutoff true, the
      gone reading kept, and the alarm says "first confirmed gone after D".
  K16 a bound of NaN or infinity, a hold limit of NaN or below 0, an infinite allowance or look: each refused
      with ValueError, and no bound is taken.
  R13 a hold at the dispatch end while D is still ahead (dispatch end 1 s, D 16 s, UTC jumps 12 s alone at 0.3 s)
      and a stop that does nothing, allowance 0.4: the alarm says "one allowance after the decision" and the
      watch has ended by itself two seconds after the start (a watch that follows D sits until D, 4 s).
"""
import importlib.util
import os
import subprocess
import sys
import time

src, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
plant = sys.argv[3] if len(sys.argv) > 3 else None
assert not os.path.exists(out), out
os.makedirs(out)

PLANTS = {
    "plant1": ("            left = min(lefts)\n", "            left = lefts[1]\n"),                    # steady only
    "plant2": ("                self._latch[key] = v\n", "                pass\n"),                    # no latch
    "plant3": ("                self._wake.wait(min(self.look_s, left_t))\n",
               "                self._wake.wait(self.look_s)\n"),                                       # sleeps on
    "plant4": ("                v = HOLD if (utc_alone and ahead > self.hold_s) else COME\n",
               "                v = COME\n"),                                                           # no hold
    "plant5": ('                self.alarm = ("the native process is still there %s; stop sent at %s, reason %s"\n',
               '                self.xalarm = ("the native process is still there %s; stop sent at %s, reason %s"\n'),
    # plant5: the alarm is never raised (the verify loop itself still ends: a plant must fail the test, not hang it)
    "plant6": ("            if old is None or utc_s <= old:\n", "            if True:\n"),             # D may move later
    "plant7": ("        with self._lock:\n            self._closed = True\n", "        with self._lock:\n            pass\n"),
    "plant8": ("                vd = b.judge(self.dispatch_end)[0] if b.get(self.dispatch_end) is not None else OPEN\n",
               "                self.refresh() if self.refresh is not None else None\n"
               "                vd = b.judge(self.dispatch_end)[0] if b.get(self.dispatch_end) is not None else OPEN\n"),
    # plant8: the schedule read back on the timer's path
    "plant9": ("            over = d_come if at_d else (d_come or b.clocks.mono() >= grace_end)\n",
               "            over = d_come if vd == OPEN else (b.clocks.mono() >= grace_end)\n"),   # a hold follows D
    "plant13": ("                wake = list(self._wakers) if (old is None or utc_s < old) else []\n",
                "                wake = []\n"),                 # a tightened bound wakes nobody
    "plant11": ('                if past_d or (not at_d and rec["gone"][1] > grace_end):\n',
                '                if False:\n'),                # an exit first confirmed after D is no alarm
    "plant12": ("        if isinstance(utc_s, bool) or not math.isfinite(float(utc_s)):\n",
                "        if False:\n"),                        # a bound of NaN or infinity is taken
    "plant10": ('               "late": after_d or found_late, "late_discovery": found_late,',
                '               "late": after_d, "late_discovery": found_late,'),        # late only when D has come
}
if plant is not None:
    old, new = PLANTS[plant]
    text = open(src, encoding="utf-8").read()
    if text.count(old) != 1:
        print(f"PLANT NOT APPLIED: {plant} finds its line {text.count(old)} times")
        sys.exit(3)
    src = os.path.join(out, f"clockwatch_{plant}.py")
    with open(src, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text.replace(old, new))
spec = importlib.util.spec_from_file_location("clockwatch_under_test", src)
cw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cw)

fails = []


def check(name, got, want):
    ok = got == want
    print(f"{'PASS' if ok else 'FAIL'} {name}: got {got!r}" + ("" if ok else f", want {want!r}"))
    if not ok:
        fails.append(name)


def true(name, cond, shown):
    print(f"{'PASS' if cond else 'FAIL'} {name}: {shown}")
    if not cond:
        fails.append(name)


# ------------------------------------------------------------------------------------------------ K: the rule
class Fake:
    def __init__(self, u=1000.0, m=50.0, b=70.0):
        self.u, self.m, self.b = u, m, b

    def clocks(self, boot=True):
        return cw.Clocks(utc=lambda: self.u, mono=lambda: self.m, boot=(lambda: self.b) if boot else None)


def rule(d=1100.0, boot=True, dispatch=None):
    f = Fake()
    b = cw.Bounds(f.clocks(boot))
    b.set("cutoff", d)
    if dispatch is not None:
        b.set("dispatch_end", dispatch)
    return b


def j(b, r, name="cutoff", lead=0.0):
    v, left, _ = b.judge(name, lead, reading=r)
    return v, left


check("K1", j(rule(), (1050.0, 100.0, 120.0)), ("open", 50.0))
check("K2", j(rule(), (1100.0, 150.0, 170.0)), ("come", 0.0))
check("K3", j(rule(), (2530.0, 80.0, 1600.0)), ("come", -1430.0))
check("K4", j(rule(), (4630.0, 80.0, 100.0))[0], "hold")
check("K5", j(rule(), (1101.0, 146.0, 166.0))[0], "come")
check("K6a", j(rule(), (1105.0, 145.0, 165.0))[0], "come")
check("K6b", j(rule(), (1105.5, 145.0, 165.0))[0], "hold")
check("K7", j(rule(), (-2500.0, 150.0, 170.0)), ("come", 0.0))
b = rule()
check("K8 first", j(b, (1101.0, 146.0, 166.0))[0], "come")
check("K8 after the correction", j(b, (1096.0, 146.0, 166.0))[0], "come")
check("K8 control", j(rule(), (1096.0, 146.0, 166.0)), ("open", 4.0))
check("K9 suspension without a boot clock", j(rule(boot=False), (2530.0, 80.0, None))[0], "hold")
check("K9 at the bound", j(rule(boot=False), (1100.0, 150.0, None))[0], "come")
b = rule()
check("K10 tighter taken", b.set("cutoff", 1060.0), True)
check("K10 tighter judged", j(b, (1070.0, 120.0, 140.0))[0], "come")
b = rule()
check("K10 later refused", b.set("cutoff", 1200.0), False)
check("K10 later: D stays", b.get("cutoff"), 1100.0)
check("K10 later: the refusal is kept", b.refused, [("cutoff", 1100.0, 1200.0)])
check("K10 later judged", j(b, (1150.0, 200.0, 220.0))[0], "come")
check("K11 earliest", j(rule(), (1053.0, 100.0, 120.0)), ("open", 47.0))
f = Fake()
b = cw.Bounds(f.clocks())
b.set("cutoff", 1100.0)
f.u, f.m, f.b = 1053.0, 100.0, 120.0
check("K11 steady cutoff", b.steady_cutoff("cutoff"), 147.0)
f.u, f.m, f.b = 1100.0, 150.0, 170.0
check("K11 steady cutoff at the bound", b.steady_cutoff("cutoff"), 150.0)
b = rule()
check("K12 trigger", j(b, (1098.0, 148.0, 168.0), lead=2.0)[0], "come")
check("K12 D itself", j(b, (1098.0, 148.0, 168.0)), ("open", 2.0))
b = rule()
check("K13 hold", j(b, (4630.0, 80.0, 100.0))[0], "hold")
check("K13 stays", j(b, (4630.0, 200.0, 220.0))[0], "hold")
check("K13 hold()", b.hold(), True)
b = rule(dispatch=1040.0)
check("K14 dispatch end", j(b, (1050.0, 100.0, 120.0), name="dispatch_end")[0], "come")
check("K14 D", j(b, (1050.0, 100.0, 120.0))[0], "open")
check("K14 no hold", b.hold(), False)
check("K15", j(rule(), (1030.0, 80.0, 1600.0))[0], "come")

# ------------------------------------------------------------------------------- R: the watch on a real child
CHILD = [sys.executable, "-I", "-c", "while True: pass"]


class Off:
    du = 0.0
    db = 0.0


class NoStop:
    how = "planted"

    def __init__(self, h):
        self.h = h

    def stop(self):
        return None

    def gone(self, timeout=0.0):
        return self.h.gone(timeout)


class SlowSee:
    """The stop works at once; the answer "gone" takes `delay` seconds to arrive."""
    how = "planted"

    def __init__(self, h, delay):
        self.h, self.delay = h, delay

    def stop(self):
        return self.h.stop()

    def gone(self, timeout=0.0):
        if self.h.gone(timeout):
            time.sleep(self.delay)
            return True
        return False


def raises(f):
    try:
        f()
    except ValueError:
        return True
    return False


def real(d_after, allowance, look=0.25, acts=(), noop=False, plan=(), limit=None, settle=0.0, slow=0.0, disp=0.05,
         wrap=None):
    """One child and one watch. acts: (seconds after the start, "utc"|"boot"|"close"|"kill", value) done by this
    thread; plan: (seconds, new D in seconds after the start) done by the watch's refresh. Returns a dict."""
    p = subprocess.Popen(CHILD)
    h = cw.ProcHandle(p)
    off = Off()
    clocks = cw.Clocks(utc=lambda: time.time() + off.du, mono=time.monotonic,
                       boot=lambda: time.monotonic() + off.db)
    b = cw.Bounds(clocks)
    u0, m0 = b.anchor[0], b.anchor[1]
    b.set("cutoff", u0 + d_after)
    b.set("dispatch_end", u0 + disp)
    todo = list(plan)

    def refresh():
        if slow:
            time.sleep(slow)
        while todo and time.monotonic() - m0 >= todo[0][0]:
            b.set("cutoff", u0 + todo.pop(0)[1])

    w = cw.Watch(wrap(h) if wrap else (NoStop(h) if noop else h), b, allowance_s=allowance, look_s=look,
                 refresh=refresh)
    w.__enter__()
    limit = limit if limit is not None else d_after + 1.0
    t_exit, closed = None, False
    for at, what, val in list(acts) + [(limit, "end", None)]:
        try:
            p.wait(timeout=max(0.0, at - (time.monotonic() - m0)))
            t_exit = time.monotonic() - m0
            break
        except subprocess.TimeoutExpired:
            pass
        if what == "utc":
            off.du = val
        elif what == "boot":
            off.db = val
        elif what == "close":
            w.close()
            closed = True
        elif what == "kill":
            p.kill()
        elif what == "set":
            b.set("cutoff", u0 + val)
    if settle:
        time.sleep(settle)
    ended = not w._t.is_alive()
    t_close = time.monotonic()
    if not closed:
        w.close()
    t_close = time.monotonic() - t_close
    alive = p.poll() is None
    if alive:
        p.kill()
    p.wait()
    h.close()
    return {"w": w, "b": b, "t_exit": t_exit, "alive": alive, "u0": u0, "ended": ended, "close_s": t_close}


def before(name, x, limit):
    true(name, x is not None and x <= limit, f"{x!r} <= {limit}")


r = real(1.2, 0.5)
check("R1 fired", r["w"].fired, "cutoff")
before("R1 gone before D (the test's own wait)", r["t_exit"], 1.2)
true("R1 not before the trigger", r["t_exit"] is not None and r["t_exit"] >= 0.65, repr(r["t_exit"]))
check("R1 late", r["w"].record and r["w"].record["late"], False)
check("R1 late_discovery, decided_after_cutoff", r["w"].record and (r["w"].record["late_discovery"],
                                                               r["w"].record["decided_after_cutoff"]), (False, False))
check("R1 alarm", r["w"].alarm, None)
true("R1 gone reading", bool(r["w"].record and r["w"].record["gone"]), "the watch found it gone")
check("R1 gone after D", r["w"].record and r["w"].record["gone_after_cutoff"], False)
true("R1 lines", len(r["w"].lines()) == 3 and all("utc=" in x for x in r["w"].lines()), repr(r["w"].lines())[:200])

r = real(0.85, 0.25, look=0.5)
check("R2 fired", r["w"].fired, "cutoff")
before("R2 gone before D although the trigger fell just after a look", r["t_exit"], 0.85)

r = real(30.0, 0.5, acts=[(0.4, "boot", 1500.0)], limit=3.0)
check("R3 fired", r["w"].fired, "cutoff")
check("R3 late", r["w"].record and r["w"].record["late"], True)
before("R3 stopped at the next look", r["t_exit"], 1.2)
check("R3 alarm", r["w"].alarm, None)

r = real(30.0, 0.5, acts=[(0.4, "utc", 3600.0)], limit=3.0)
check("R4 fired", r["w"].fired, "clock")
check("R4 hold()", r["b"].hold(), True)
before("R4 stopped at the next look", r["t_exit"], 1.2)

r = real(0.9, 0.4, noop=True, limit=1.6)
check("R5 fired", r["w"].fired, "cutoff")
true("R5 alarm", r["w"].alarm is not None and "still there at D" in r["w"].alarm, repr(r["w"].alarm))
check("R5 no gone reading", r["w"].record and r["w"].record["gone"], None)
check("R5 the child was really still there", r["alive"], True)
true("R5 lines name it", any("NOT found gone" in x for x in r["w"].lines()), repr(r["w"].lines())[:200])

r = real(1.0, 0.3, acts=[(0.3, "close", None)], limit=1.4)
check("R6 fired", r["w"].fired, None)
check("R6 the child lived on", r["alive"], True)

r = real(30.0, 0.5, plan=[(0.3, 1.2)], limit=3.0)
check("R7 fired", r["w"].fired, "cutoff")
before("R7 gone before the new D", r["t_exit"], 1.2)
check("R7 late, late_discovery", r["w"].record and (r["w"].record["late"], r["w"].record["late_discovery"]),
      (False, False))
check("R7 late", r["w"].record and r["w"].record["late"], False)

r = real(30.0, 0.5, plan=[(0.5, 0.2)], limit=3.0)
check("R8 fired", r["w"].fired, "cutoff")
check("R8 late", r["w"].record and r["w"].record["late"], True)
check("R8 decided_after_cutoff", r["w"].record and r["w"].record["decided_after_cutoff"], True)
true("R8 the real time of the decision is kept", bool(r["w"].record) and r["w"].record["decided"][0] - r["u0"] >= 0.5,
     repr(r["w"].record and r["w"].record["decided"][0] - r["u0"]))
true("R8 left to D is negative", bool(r["w"].record) and r["w"].record["left_to_cutoff_s"] < 0,
     repr(r["w"].record and r["w"].record["left_to_cutoff_s"]))
before("R8 stopped at once", r["t_exit"], 1.3)

r = real(0.9, 0.4, plan=[(0.2, 60.0)])
check("R9 fired", r["w"].fired, "cutoff")
before("R9 gone before the first D", r["t_exit"], 0.9)
true("R9 the later D was refused", len(r["b"].refused) == 1, repr(r["b"].refused))

r = real(5.0, 0.5, acts=[(0.2, "kill", None)], limit=2.0, settle=0.6)
check("R10 fired", r["w"].fired, None)
check("R10 seen gone", r["w"].seen_gone, True)

r = real(30.0, 0.7, plan=[(0.4, 0.9)], limit=3.0)
check("R11 fired", r["w"].fired, "cutoff")
before("R11 gone before D", r["t_exit"], 0.9)
rec = r["w"].record or {}
check("R11 late, late_discovery", (rec.get("late"), rec.get("late_discovery")), (True, True))
check("R11 decided_after_cutoff, gone_after_cutoff", (rec.get("decided_after_cutoff"), rec.get("gone_after_cutoff")),
      (False, False))
check("R11 alarm", r["w"].alarm, None)
true("R11 behind its trigger", rec.get("left_to_trigger_s", 1.0) < -0.1, repr(rec.get("left_to_trigger_s")))

r = real(0.8, 0.3, slow=3.0, limit=2.0)
check("R12 fired", r["w"].fired, "cutoff")
before("R12 gone before D although every schedule read stalls", r["t_exit"], 0.8)
true("R12 close() does not wait for the stalled read", r["close_s"] < 1.0, repr(r["close_s"]))
check("R12 reader_stalled", r["w"].reader_stalled, True)

r = real(16.0, 0.4, acts=[(0.3, "utc", 12.0)], noop=True, limit=2.0, disp=1.0)
check("R13 fired", r["w"].fired, "clock")
check("R13 the watch has ended by itself", r["ended"], True)
true("R13 alarm one allowance after the decision", r["w"].alarm is not None
     and "one allowance after the decision" in r["w"].alarm, repr(r["w"].alarm))

r = real(1.0, 0.3, wrap=lambda h: SlowSee(h, 0.45), limit=2.0)
check("R14 fired", r["w"].fired, "cutoff")
before("R14 the child itself ended before D (the test's own wait)", r["t_exit"], 1.0)
rec = r["w"].record or {}
check("R14 gone_after_cutoff", rec.get("gone_after_cutoff"), True)
true("R14 the gone reading is kept", bool(rec.get("gone")), repr(rec.get("gone")))
true("R14 alarm: first confirmed gone after D", r["w"].alarm is not None
     and "first confirmed gone after D" in r["w"].alarm, repr(r["w"].alarm))

r = real(30.0, 0.2, look=1.0, acts=[(0.2, "set", 0.8)], limit=2.0)
check("R16 fired", r["w"].fired, "cutoff")
before("R16 gone before the D another thread set while the watch slept", r["t_exit"], 0.8)
rec = r["w"].record or {}
check("R16 late, late_discovery", (rec.get("late"), rec.get("late_discovery")), (False, False))
check("R16 alarm", r["w"].alarm, None)

bq = cw.Bounds()
check("K16 a NaN bound is refused", raises(lambda: bq.set("cutoff", float("nan"))), True)
check("K16 an infinite bound is refused", raises(lambda: bq.set("cutoff", float("inf"))), True)
check("K16 no bound was taken", bq.get("cutoff"), None)
check("K16 a NaN hold limit is refused", raises(lambda: cw.Bounds(hold_s=float("nan"))), True)
check("K16 a negative hold limit is refused", raises(lambda: cw.Bounds(hold_s=-1.0)), True)
check("K16 a finite bound is taken", bq.set("cutoff", bq.anchor[0] + 100.0), True)
check("K16 an infinite allowance is refused", raises(lambda: cw.Watch(None, bq, allowance_s=float("inf"))), True)
check("K16 an infinite look is refused", raises(lambda: cw.Watch(None, bq, look_s=float("inf"))), True)
check("K16 finite values are taken", raises(lambda: cw.Watch(None, bq, allowance_s=2.0, look_s=0.25)), False)

print("ALL PASS" if not fails else f"{len(fails)} failed: {fails}")
sys.exit(1 if fails else 0)
