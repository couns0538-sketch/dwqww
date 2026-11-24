"""test_clockwatch.py <run/clockwatch.py> <a new folder> [plant1 ... plant20]

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
  Version 5 (Astra 172124Z and 172227Z, Neon 172517Z): an error inside the watch. The planted handle raises an
  OSError from its look and can answer a stop with an error text that ends nothing; the watch looks every 0.25 s,
  so the first look at or after 0.3 s is the one at about 0.5 s.
  R17 the look raises ONCE (from 0.3 s) and the first stop after it answers with an error (the later stops work);
      D 2.0 s, allowance 0.5: fired "error"; the child is gone (the test's own wait) by 1.05 s, long before D,
      because the stop was tried again (at least 2 stops); no alarm; `error` names the look's OSError and the
      stop's text; the record: reason "error", stop_error the stop's text, a gone reading, gone_after_cutoff
      False. (Clockwatch 4: one stop, its error dropped, the child alive at D, no record.)
  R18 the look raises once (from 0.3 s) and EVERY stop answers with an error; D 30 s, allowance 0.4: the watch
      has ended by itself at 1.5 s (bounded by the allowance, not by D); the alarm says "not confirmed gone"
      and "one allowance after the error"; at least 2 stops; `error` names the stop's text; the lines say "NOT
      found gone"; the child is really still there.
  R19 the look raises at EVERY call from 0.3 s on and the stop works: the child is gone (the test's own wait)
      by 0.8 s; the watch has ended by itself at 1.5 s; the alarm says "not confirmed gone" (it could not look);
      a failed look is followed by a pause: at most 60 looks in all (a loop without one makes thousands).
  R20 control: the wait is over before the error. The first look blocks 0.4 s and then raises; the watch is
      closed at 0.15 s, while it blocks: fired None, the child lives on, `error` names the look's error.
  K17 an allowance of True or False and a look of True are refused with ValueError (a bool is not a number of
      seconds; Neon 172517Z, as Bounds.set does). Clockwatch 4 takes all three.
  P1  Linux only, where the handle is a pidfd (Astra 165531Z, Neon 172517Z, Fable 001731Z): the child's pidfd
      duplicated to the lowest free number at or above 1,100 (the soft limit of open files raised to 4,096 at
      most where it is under 1,200); a live child: gone(0) and gone(0.05) false; a watch with D 1.0 s and
      allowance 0.3 on that handle: fired "cutoff", the child gone before D, no alarm, no error. Without a
      pidfd it prints NOT RUN and counts in neither (it does not run on Windows).
  R21 the exit is judged by when the look SAW it (Opus 17:0x, before the refinement was made): the look raises
      once (from 0.3 s), every stop works, D 30 s, allowance 0.4; the first clock read after the planted handle
      has seen the exit sleeps 0.6 s. The case is reached: the exit was seen less than 0.3 s after the error,
      and the gone reading lies more than 0.5 s after it (beyond one allowance). Known answer: fired "error",
      the child gone (the test's own wait) by 0.85 s, NO alarm (the exit was seen within the allowance),
      gone_after_cutoff False. A watch that judges by the time after the slow read raises "first confirmed gone
      more than one allowance after the error" (plant 20).
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
    # version 5 (the error path): each must make the test FAIL
    "plant14": ("                err = h.stop()\n",
                "                err = h.stop() if rec[\"stopped\"] is None else None\n"),  # the stop is not tried again
    "plant15": ('                self.alarm = ("the native process was not confirmed gone %s, after an error inside "\n',
                '                self.xalarm = ("the native process was not confirmed gone %s, after an error inside "\n'),
    "plant16": ("        if isinstance(allowance_s, bool) or isinstance(look_s, bool):\n",
                "        if False:\n"),                     # a bool taken as seconds
    "plant17": ("        t_end = time.monotonic() + self.allowance_s\n",
                "        t_end = time.monotonic() + 3 * self.allowance_s\n"),   # the error path's limit three times longer
    "plant18": ("            act = self.fired is not None\n",
                "            act = True\n"),                   # a watch closed before the error ends the process
    "plant19": ("                time.sleep(min(0.02, max(0.0, t_end - time.monotonic())))\n",
                "                pass\n"),                     # a failed look is retried at once (a spin)
    "plant20": ("                if past_d or t_seen > t_end:\n",
                "                if past_d or time.monotonic() > t_end:\n"),  # judged after the reads that follow the look
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


class Flaky:
    """Version 5. Planted faults on a real handle: from `after` seconds on, the look sleeps `block` seconds and then
    raises an OSError, once or at every call (`once`); the stop answers with an error text and ends nothing at the
    calls in `bad` (1 = the first stop) or at every call (bad "all"). Every call is counted."""
    how = "planted"

    def __init__(self, h, after, once=True, bad=(), block=0.0):
        self.h, self.after, self.once, self.bad, self.block = h, after, once, bad, block
        self.t0 = time.monotonic()
        self.raised = self.looks = self.stops = 0
        self.t_raise = self.t_gone = None       # R21: when the look raised, when the real look first saw the exit

    def gone(self, timeout=0.0):
        self.looks += 1
        if time.monotonic() - self.t0 >= self.after and (not self.once or self.raised == 0):
            self.raised += 1
            time.sleep(self.block)
            self.t_raise = time.monotonic()
            raise OSError(4, "planted: an interrupted look")
        seen = self.h.gone(timeout)
        if seen and self.t_gone is None:
            self.t_gone = time.monotonic()
        return seen

    def stop(self):
        self.stops += 1
        if self.bad == "all" or self.stops in self.bad:
            return "OSError(11, 'planted: the stop did not go through')"
        return self.h.stop()


def raises(f):
    try:
        f()
    except ValueError:
        return True
    return False


def real(d_after, allowance, look=0.25, acts=(), noop=False, plan=(), limit=None, settle=0.0, slow=0.0, disp=0.05,
         wrap=None, utc_hook=None):
    """One child and one watch. acts: (seconds after the start, "utc"|"boot"|"close"|"kill", value) done by this
    thread; plan: (seconds, new D in seconds after the start) done by the watch's refresh. Returns a dict."""
    p = subprocess.Popen(CHILD)
    h = cw.ProcHandle(p)
    off = Off()
    clocks = cw.Clocks(utc=lambda: (utc_hook and utc_hook(), time.time() + off.du)[1], mono=time.monotonic,
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

STOPTEXT = "OSError(11, 'planted: the stop did not go through')"
r = real(2.0, 0.5, wrap=lambda h: Flaky(h, 0.3, bad=(1,)), limit=3.0)
fl, rec, er = r["w"].handle, r["w"].record or {}, r["w"].error or ""
check("R17 fired", r["w"].fired, "error")
before("R17 the child gone (the test's own wait) long before D", r["t_exit"], 1.05)
true("R17 the stop was tried again", fl.stops >= 2, repr(fl.stops))
check("R17 alarm", r["w"].alarm, None)
true("R17 error names the look's error and the stop's", "an interrupted look" in er and STOPTEXT in er, repr(er))
check("R17 the record: reason, stop_error", (rec.get("reason"), rec.get("stop_error")), ("error", STOPTEXT))
true("R17 the record: a gone reading, not after D", bool(rec.get("gone")) and rec.get("gone_after_cutoff") is False,
     repr((rec.get("gone"), rec.get("gone_after_cutoff"))))

r = real(30.0, 0.4, wrap=lambda h: Flaky(h, 0.3, bad="all"), limit=1.5)
fl, er, al = r["w"].handle, r["w"].error or "", r["w"].alarm or ""
check("R18 fired", r["w"].fired, "error")
check("R18 the watch has ended by itself (bounded by the allowance; D is 30 s away)", r["ended"], True)
true("R18 alarm: not confirmed gone, one allowance after the error", "not confirmed gone" in al
     and "one allowance after the error" in al, repr(al))
true("R18 the stop was tried again", fl.stops >= 2, repr(fl.stops))
true("R18 error names the stop's text", STOPTEXT in er, repr(er))
true("R18 lines say NOT found gone", any("NOT found gone" in x for x in r["w"].lines()), repr(r["w"].lines())[:300])
check("R18 the child was really still there", r["alive"], True)

r = real(30.0, 0.4, wrap=lambda h: Flaky(h, 0.3, once=False), limit=1.5, settle=1.0)
fl, al = r["w"].handle, r["w"].alarm or ""
check("R19 fired", r["w"].fired, "error")
before("R19 the child gone (the test's own wait): the first stop worked", r["t_exit"], 0.8)
check("R19 the watch has ended by itself", r["ended"], True)
true("R19 alarm: not confirmed gone (it could not look)", "not confirmed gone" in al, repr(al))
true("R19 a failed look is followed by a pause: at most 60 looks", fl.looks <= 60, repr(fl.looks))

r = real(30.0, 0.4, wrap=lambda h: Flaky(h, 0.0, block=0.4), acts=[(0.15, "close", None)], limit=1.2)
check("R20 fired (the wait was over before the error)", r["w"].fired, None)
check("R20 the child lives on", r["alive"], True)
true("R20 error names the look's error", "an interrupted look" in (r["w"].error or ""), repr(r["w"].error))

SLOWREAD = {}


def slow_once_after_gone():
    """R21: the first clock read after the planted handle has seen the exit sleeps 0.6 s, once."""
    fl = SLOWREAD.get("fl")
    if fl is not None and fl.t_gone is not None and "at" not in SLOWREAD:
        SLOWREAD["at"] = time.monotonic()
        time.sleep(0.6)


def mark21(h):
    SLOWREAD["fl"] = Flaky(h, 0.3)
    return SLOWREAD["fl"]


r = real(30.0, 0.4, wrap=mark21, limit=2.0, utc_hook=slow_once_after_gone)
fl, rec = r["w"].handle, r["w"].record or {}
check("R21 fired", r["w"].fired, "error")
true("R21 reached: the exit seen less than 0.3 s after the error",
     fl.t_raise is not None and fl.t_gone is not None and 0 <= fl.t_gone - fl.t_raise < 0.3,
     repr((fl.t_raise, fl.t_gone)))
true("R21 reached: the slow read came after the exit was seen, and the gone reading lies beyond one allowance",
     "at" in SLOWREAD and fl.t_gone is not None and SLOWREAD["at"] >= fl.t_gone and bool(rec.get("gone"))
     and fl.t_raise is not None and rec["gone"][1] - fl.t_raise > 0.5, repr((SLOWREAD.get("at"), rec.get("gone"))))
before("R21 the child gone (the test's own wait)", r["t_exit"], 0.85)
check("R21 alarm (the exit was seen within the allowance)", r["w"].alarm, None)
check("R21 gone_after_cutoff", rec.get("gone_after_cutoff"), False)

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
check("K17 an allowance of True is refused", raises(lambda: cw.Watch(None, bq, allowance_s=True)), True)
check("K17 an allowance of False is refused", raises(lambda: cw.Watch(None, bq, allowance_s=False)), True)
check("K17 a look of True is refused", raises(lambda: cw.Watch(None, bq, look_s=True)), True)

P1 = {}


def high_fd(h):
    """Astra 165531Z: the same child's pidfd under a number above 1,024 (fcntl F_DUPFD: the lowest free >= 1,100)."""
    import fcntl
    hi = fcntl.fcntl(h.fd, fcntl.F_DUPFD, 1100)
    os.close(h.fd)
    h.fd = hi
    P1["fd"], P1["live"] = hi, (h.gone(0.0), h.gone(0.05))
    return h


if not (hasattr(os, "pidfd_open") and hasattr(cw.signal, "pidfd_send_signal")):
    print("NOT RUN P1: this system has no pidfd (the Linux case of Astra 165531Z); counted in neither")
else:
    import resource
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    want = 4096 if hard == resource.RLIM_INFINITY else min(4096, hard)
    if soft < 1200 and want < 1200:
        print(f"NOT RUN P1: the hard limit of open files is {hard}; counted in neither")
    else:
        if soft < 1200:
            resource.setrlimit(resource.RLIMIT_NOFILE, (want, hard))
        r = real(1.0, 0.3, wrap=high_fd, limit=2.0)
        check("P1 the handle is a pidfd", r["w"].handle.how, "pidfd")
        true("P1 its number is above 1,024", P1.get("fd", 0) >= 1100, repr(P1.get("fd")))
        check("P1 a live child is not gone (0 s, 0.05 s)", P1.get("live"), (False, False))
        check("P1 fired", r["w"].fired, "cutoff")
        before("P1 the child gone before D", r["t_exit"], 1.0)
        check("P1 alarm, error", (r["w"].alarm, r["w"].error), (None, None))

print("ALL PASS" if not fails else f"{len(fails)} failed: {fails}")
sys.exit(1 if fails else 0)
