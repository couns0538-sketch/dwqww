"""clockwatch.py: by which clocks a bound has come, and the watch that ends a native engine process at D.

FORMATS.md 2.9, section 1.8 point 1 ([2.7] the three clocks; [2.8], [2.9] the watch). Standard library only.

THE CLOCKS. A program reads UTC, the steady clock (it stands still in a suspension) and the boot-time clock (it
counts through one; where a system has none, the first two) TOGETHER at its start: the anchor. A bound B is a UTC
time in seconds. The time left to B is, by UTC, B - utc; by each of the other two, (B - anchor utc) - (the time
that clock has run since the anchor). ALL are judged and the EARLIEST holds: the bound has come when the least of
them is <= 0. A bound once passed stays passed for this process (a wall clock set back, a correction or a wake
never lengthens what is left). ONE case is a HOLD and not the end: UTC ALONE says the bound has come, and UTC
stands more than hold_s (10; the editor's choice, not measured) seconds ahead of the anchor plus the boot-time
clock's run (the steady clock's where there is no boot-time clock). A bound never moves later: `set` keeps the
earlier of the bound in force and the one offered.

THE WATCH runs beside ONE wait for the engine, in a thread of the program that owns the native process:

    B = Bounds()                                   # once, at the program's start
    B.set("cutoff", d_utc_s); B.set("dispatch_end", e_utc_s)        # after every schedule that was verified
    h = ProcHandle(engine_popen)                   # right after the engine was started; h.close() at the very end
    with Watch(h, B, allowance_s=2.0, refresh=read_next_schedule) as w:
        ...the wait for the engine, its steady limit taken afresh from B.steady_cutoff("cutoff")...
    # here the watch has ended: w.fired is None, "cutoff", "clock" or "error"; w.alarm, w.error, w.lines()

About every look_s seconds, and never later than its trigger, it judges the dispatch end and "D less the stop
allowance" (the trigger). It fires with the reason "cutoff" when the trigger has come by the earliest clock, and
with "clock" when a HOLD applies to the dispatch end or to the trigger. The dispatch end having come is no reason.
Firing ends the native process, THAT PROCESS ALONE (never a process group: the engine shares its worker's group),
through a handle a reused process number cannot confuse; it never touches the driver's pipes. It then verifies
that the process is gone. The allowance covers the whole way from the trigger to the confirmed exit, so each wait
of the watch ends at the earlier of the regular look and the trigger of the bound in force. A tighter D whose
trigger has already passed is acted on at once and recorded as it happened, the kinds kept apart (Astra 165352Z 3):
`late_discovery` (the trigger had passed when this bound was first judged), `decided_after_cutoff` (D itself had
come at the decision), `late` (either of the two), `gone_after_cutoff` (the exit was confirmed after D); each with
the clock readings. A process that is still there when D comes is `alarm`; in a hold, and after a decision made
when D had already come, the limit is one allowance after the decision, and D where D comes first (Astra 2). The
caller writes the alarm and leaves with exit code 8. An exit that the watch could first CONFIRM after its limit
is an alarm too and says so in its own words ("first confirmed gone after D"), with the reading of the
confirmation: the watch does not claim the process was there at D, and does not write the stop as on time
(Astra 165616Z). No wait of the watch's own is asked to cross its limit. A bound, the hold limit, the allowance
and the look are finite numbers, never a bool, or they are refused (Neon 170114Z, 172517Z). An error inside the
watch, in its loop or in its stop, ends the process too and CONFIRMS the exit (version 5; Astra 172124Z, 172227Z,
Neon 172517Z): unless the wait was over before the error, the stop and the look are tried again until the exit is
seen, for at most one allowance after the error by the system's own steady clock (so the watch always returns) and
until D where D was still ahead; an exit not seen by then is the alarm "not confirmed gone", one seen only after
that limit is "first confirmed gone"; `fired` is "error" (or the reason it had fired for), `error` keeps the first
error and, counted, the first of each kind that followed. A wait is never left unwatched without a word.
`refresh` is the caller's: it reads a newer valid schedule and calls B.set. It runs in a thread of its own, NEVER
on the timer's path (Astra 1): a read that is slow or stalls cannot delay the stop for a bound already in force;
a bound it tightens is judged at once, and so is a bound tightened by ANY other thread through B.set (Astra
170921Z: the bounds wake every watch that sleeps under them; a change that races the start of a wait is seen,
because the wait's event is cleared only after it returns and the bound is judged again after that). close()
returns without waiting for a stalled read (`reader_stalled`). Its
errors are kept in refresh_errors and the bounds in force go on holding.
"""
import math
import os
import select
import signal
import threading
import time

OPEN, COME, HOLD = "open", "come", "hold"
SYSTEM = "system"


def _system_boot():
    cid = getattr(time, "CLOCK_BOOTTIME", None)
    if cid is None:
        return None
    try:
        time.clock_gettime(cid)
    except OSError:
        return None
    return lambda: time.clock_gettime(cid)


class Clocks:
    """The three readers. boot=None: this system has no boot-time clock (the first two are judged)."""

    def __init__(self, utc=time.time, mono=time.monotonic, boot=SYSTEM):
        self.utc, self.mono = utc, mono
        self.boot = _system_boot() if isinstance(boot, str) and boot == SYSTEM else boot

    def read(self):
        return (self.utc(), self.mono(), self.boot() if self.boot is not None else None)


def reading_text(r):
    if r is None:
        return "none"
    return "utc=%.6f steady=%.6f boot=%s" % (r[0], r[1], "none" if r[2] is None else "%.6f" % r[2])


def _secs(x):
    return "none" if x is None else "%.6f" % x


class Bounds:
    """The anchor and the bounds in force, judged by all clocks. Safe to use from two threads."""

    def __init__(self, clocks=None, hold_s=10.0):
        self.clocks = clocks if clocks is not None else Clocks()
        if isinstance(hold_s, bool) or not math.isfinite(float(hold_s)) or hold_s < 0:
            raise ValueError("hold_s is a finite number of seconds, not negative; got %r" % (hold_s,))
        self.hold_s = hold_s
        self.anchor = self.clocks.read()
        self._lock = threading.Lock()
        self._b = {}
        self._latch = {}
        self.refused = []           # (name, the bound kept, the later bound offered)
        self._seen_open = {}        # (name, lead) -> the bound last judged OPEN with that lead
        self._wakers = []           # the events of the watches that sleep under these bounds

    def set(self, name, utc_s):
        """Take a bound; never a later one than the bound in force. True when the offered bound is now in force."""
        if isinstance(utc_s, bool) or not math.isfinite(float(utc_s)):
            raise ValueError("a bound is a finite number of seconds; got %r" % (utc_s,))
        utc_s = float(utc_s)
        with self._lock:
            old = self._b.get(name)
            if old is None or utc_s <= old:
                self._b[name] = utc_s
                wake = list(self._wakers) if (old is None or utc_s < old) else []
            else:
                self.refused.append((name, old, utc_s))
                return False
        for ev in wake:                 # a watch asleep under the old bound judges the new one at once
            ev.set()
        return True

    def wake_on_change(self, event, on=True):
        """A watch gives its event: set whenever a bound is first taken or tightened, from whatever thread."""
        with self._lock:
            if on and event not in self._wakers:
                self._wakers.append(event)
            elif not on and event in self._wakers:
                self._wakers.remove(event)

    def get(self, name):
        with self._lock:
            return self._b.get(name)

    def hold(self):
        with self._lock:
            return HOLD in self._latch.values()

    def judge(self, name, lead=0.0, reading=None):
        """(OPEN | COME | HOLD, the least time left by any clock to bound - lead, the reading used)."""
        r = reading if reading is not None else self.clocks.read()
        a = self.anchor
        with self._lock:
            bound = self._b[name] - lead
            span = bound - a[0]
            lefts = [bound - r[0], span - (r[1] - a[1])]
            boot = r[2] is not None and a[2] is not None
            if boot:
                lefts.append(span - (r[2] - a[2]))
            left = min(lefts)
            key = (name, lead)
            v = self._latch.get(key)
            if v is None and left <= 0:
                utc_alone = lefts[0] <= 0 and all(x > 0 for x in lefts[1:])
                run = (r[2] - a[2]) if boot else (r[1] - a[1])
                ahead = r[0] - (a[0] + run)
                v = HOLD if (utc_alone and ahead > self.hold_s) else COME
                self._latch[key] = v
            if v is None:
                self._seen_open[key] = self._b[name]
            return (v if v is not None else OPEN), left, r

    def found_late(self, name, lead=0.0):
        """True when the bound in force was never judged OPEN with this lead: its trigger had already passed when
        it was first judged (a tighter bound that was found late, or a program that began after the trigger)."""
        with self._lock:
            return self._seen_open.get((name, lead)) != self._b.get(name)

    def steady_cutoff(self, name="cutoff", lead=0.0):
        """The steady-clock time a wait may last to: now plus the least time left by any clock (now, once passed)."""
        v, left, r = self.judge(name, lead)
        return r[1] + (max(0.0, left) if v == OPEN else 0.0)


class ProcHandle:
    """One native process, held so that a reused process number cannot be mistaken for it: a pidfd where the system
    has one, else the Popen object's own handle. `stop` ends that process alone; `gone` only looks."""

    def __init__(self, popen):
        self.p = popen
        self.fd = None
        self.how = "popen"
        if hasattr(os, "pidfd_open") and hasattr(signal, "pidfd_send_signal"):
            try:
                self.fd = os.pidfd_open(popen.pid)
                self.how = "pidfd"
            except OSError:
                self.fd = None

    def stop(self):
        """None, or the text of the error. A process that has already ended is no error."""
        try:
            if self.fd is not None:
                signal.pidfd_send_signal(self.fd, signal.SIGKILL)
            else:
                self.p.kill()
        except ProcessLookupError:
            return None
        except OSError as e:
            return repr(e)
        return None

    def gone(self, timeout=0.0):
        """True when the process has ended; waits at most `timeout` seconds for that."""
        timeout = max(0.0, timeout)
        if self.fd is not None:
            if hasattr(select, "poll"):             # no limit on the descriptor's number (select ends at 1,024)
                po = select.poll()
                po.register(self.fd, select.POLLIN)
                return bool(po.poll(int(timeout * 1000)))
            return bool(select.select([self.fd], [], [], timeout)[0])
        end = time.monotonic() + timeout
        while True:
            if self.p.poll() is not None:
                return True
            if time.monotonic() >= end:
                return False
            time.sleep(0.002)

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None


class Watch:
    def __init__(self, handle, bounds, allowance_s=2.0, look_s=0.25, refresh=None, cutoff="cutoff",
                 dispatch_end="dispatch_end"):
        if bounds.get(cutoff) is None:
            raise ValueError("the watch needs the bound %r" % cutoff)
        if isinstance(allowance_s, bool) or isinstance(look_s, bool):
            raise ValueError("allowance_s and look_s are numbers of seconds, not True or False")
        if not (math.isfinite(float(allowance_s)) and math.isfinite(float(look_s))
                and allowance_s >= 0 and look_s > 0):
            raise ValueError("allowance_s >= 0 and look_s > 0, both finite")
        self.handle, self.bounds, self.refresh = handle, bounds, refresh
        self.allowance_s, self.look_s = float(allowance_s), float(look_s)
        self.cutoff, self.dispatch_end = cutoff, dispatch_end
        self.fired = None           # None | "cutoff" | "clock" | "error"
        self.record = None          # the decision, the stop and the process found gone, each with its reading
        self.alarm = None           # text: the process was still there when it had to be gone
        self.error = None           # text: an error inside the watch itself
        self.seen_gone = False      # the process ended by itself while the watch looked
        self.refresh_errors = []
        self.reader_stalled = False  # close() did not wait for a schedule read that had not returned
        self._closed = False
        self._lock = threading.Lock()
        self._wake = threading.Event()
        self._stop_read = threading.Event()
        self._t = threading.Thread(target=self._run, name="clockwatch", daemon=True)
        self._r = (threading.Thread(target=self._read, name="clockwatch-read", daemon=True)
                   if refresh is not None else None)

    def __enter__(self):
        self.bounds.wake_on_change(self._wake)
        self._t.start()
        if self._r is not None:
            self._r.start()
        return self

    def __exit__(self, *exc):
        self.close()
        return False

    def close(self):
        """The wait is over. A watch that has not fired never fires after this; one that has is waited for."""
        with self._lock:
            self._closed = True
        self._wake.set()
        self._stop_read.set()
        if self._t.ident is not None:
            self._t.join()
        self.bounds.wake_on_change(self._wake, False)
        if self._r is not None and self._r.ident is not None:
            self._r.join(min(self.look_s, 0.25))
            self.reader_stalled = self._r.is_alive()

    def _read(self):
        """The schedule reader: apart from the timer, so that no read can delay a stop."""
        while True:
            with self._lock:
                if self._closed or self.fired is not None:
                    return
            try:
                self.refresh()
            except Exception as e:
                self.refresh_errors.append(repr(e))
            self._wake.set()                        # a bound that was tightened is judged at once
            if self._stop_read.wait(self.look_s):
                return

    def _run(self):
        try:
            b = self.bounds
            while True:
                with self._lock:
                    if self._closed:
                        return
                if self.handle.gone():
                    self.seen_gone = True
                    return
                vd = b.judge(self.dispatch_end)[0] if b.get(self.dispatch_end) is not None else OPEN
                vt, left_t, r = b.judge(self.cutoff, lead=self.allowance_s)
                reason = "clock" if HOLD in (vd, vt) else ("cutoff" if vt == COME else None)
                if reason is not None:
                    self._fire(reason, r, left_t)
                    return
                self._wake.wait(min(self.look_s, left_t))
                self._wake.clear()
        except BaseException as e:
            self._after_error(e)

    def _after_error(self, e):
        """An error inside the watch, in its loop or in _fire (Astra 172124Z, 172227Z; Neon 172517Z). A watch that
        was closed before it fired is left alone: its wait is over. Otherwise the native process is ended and its
        exit confirmed by _end_after_error; `error` is the first error and, counted, the first of each kind that
        followed (stop, look, clock)."""
        self.error = repr(e)
        more = {}                                   # kind -> [how many, the first text]
        with self._lock:
            if self.fired is None and not self._closed:
                self.fired = "error"
            act = self.fired is not None
        try:
            if act:
                self._end_after_error(more)
        except BaseException as e2:
            more.setdefault("watch", [0, repr(e2)])[0] += 1
            if self.alarm is None:
                self.alarm = "the native process was not confirmed gone: the confirmation itself failed"
        finally:
            self.error = repr(e) + "".join("; then the %s failed %d time(s), first: %s" % (k, n, x)
                                           for k, (n, x) in sorted(more.items()))

    def _end_after_error(self, more):
        """The stop and a look of at most 20 ms each, in turn, until the exit is seen; a look that fails is followed
        by a pause of 20 ms (no spin). The limit: one allowance after the error by the system's own steady clock,
        which no plant replaces, and D where D was still ahead at the error. Not seen by then: the alarm "not
        confirmed gone"; seen only after its limit: "first confirmed gone". Every reading is the clocks' own, or,
        where they fail, the system's (then nothing is judged with it). The record is the one _fire made, or a new
        one with the reason "error"."""
        h, b = self.handle, self.bounds
        t_end = time.monotonic() + self.allowance_s

        def note(kind, x):
            more.setdefault(kind, [0, x])[0] += 1

        def tried(kind, f, *a):
            try:
                return f(*a), True
            except BaseException as x:
                note(kind, repr(x))
                return None, False

        def reading():
            got, ok = tried("clock", b.clocks.read)
            return (got, True) if ok else ((time.time(), time.monotonic(), None), False)

        r, ok = reading()
        vd = tried("clock", lambda: b.judge(self.cutoff, reading=r)[0])[0] if ok else None
        rec = self.record
        if rec is None:
            rec = {"reason": self.fired, "decided": r, "left_to_trigger_s": None, "left_to_cutoff_s": None,
                   "late": None, "late_discovery": None, "decided_after_cutoff": None if vd is None else vd == COME,
                   "how": getattr(h, "how", "?"), "stop_error": None, "stopped": None, "gone": None,
                   "gone_after_cutoff": None}
            self.record = rec
        while True:
            try:
                err = h.stop()
            except BaseException as x:
                err = repr(x)
            if err:
                note("stop", err)
                rec["stop_error"] = err
            if rec["stopped"] is None:
                rec["stopped"] = reading()[0]
            room = t_end - time.monotonic()
            if vd == OPEN:
                left_d, ok = tried("clock", lambda: b.judge(self.cutoff)[1])
                room = min(room, left_d) if ok else room
            seen, ok = tried("look", h.gone, min(0.02, max(0.0, room)))
            if seen:
                t_seen = time.monotonic()           # the exit is judged by when the look saw it, as in _fire
                g, real = reading()
                rec["gone"] = g
                if real:
                    rec["gone_after_cutoff"] = tried("clock", lambda: b.judge(self.cutoff, reading=g)[0] == COME)[0]
                past_d = vd == OPEN and rec["gone_after_cutoff"] is True
                if past_d or t_seen > t_end:
                    self.alarm = ("the native process was first confirmed gone %s, after an error inside the watch; "
                                  "stop sent at %s, confirmed at %s, reason %s"
                                  % ("after D" if past_d else "more than one allowance after the error",
                                     reading_text(rec["stopped"]), reading_text(g), rec["reason"]))
                return
            if not ok:
                time.sleep(min(0.02, max(0.0, t_end - time.monotonic())))
            v, ok = tried("clock", lambda: b.judge(self.cutoff)[0]) if vd == OPEN else (None, False)
            d_come = ok and v != OPEN
            if d_come or time.monotonic() >= t_end:
                self.alarm = ("the native process was not confirmed gone %s, after an error inside "
                              "the watch; stop sent at %s, reason %s"
                              % ("at D" if d_come else "one allowance after the error",
                                 reading_text(rec["stopped"]), rec["reason"]))
                return

    def _fire(self, reason, r, left_t):
        with self._lock:
            if self._closed:
                return
            self.fired = reason
        b, h = self.bounds, self.handle
        vd, left_d, _ = b.judge(self.cutoff)
        after_d = vd == COME                        # D itself had come when the watch decided
        found_late = reason == "cutoff" and b.found_late(self.cutoff, self.allowance_s)
        rec = {"reason": reason, "decided": r, "left_to_trigger_s": left_t, "left_to_cutoff_s": left_d,
               "late": after_d or found_late, "late_discovery": found_late, "decided_after_cutoff": after_d,
               "how": getattr(h, "how", "?"), "stop_error": None, "stopped": None, "gone": None,
               "gone_after_cutoff": None}
        self.record = rec
        rec["stop_error"] = h.stop()
        rec["stopped"] = b.clocks.read()
        at_d = reason == "cutoff" and vd == OPEN    # an ordinary stop before D: gone when D comes
        grace_end = r[1] + self.allowance_s         # one allowance after the DECISION's own reading
        while True:
            room = b.judge(self.cutoff)[1] if vd == OPEN else float("inf")
            if not at_d:
                room = min(room, grace_end - b.clocks.mono())
            if h.gone(min(0.02, max(0.0, room))):   # no wait of the watch's own is asked to cross its limit
                rec["gone"] = b.clocks.read()
                rec["gone_after_cutoff"] = b.judge(self.cutoff, reading=rec["gone"])[0] == COME
                past_d = vd == OPEN and rec["gone_after_cutoff"]
                if past_d or (not at_d and rec["gone"][1] > grace_end):
                    self.alarm = ("the native process was first confirmed gone %s; stop sent at %s, confirmed at "
                                  "%s, reason %s"
                                  % ("after D" if past_d else "more than one allowance after the decision",
                                     reading_text(rec["stopped"]), reading_text(rec["gone"]), reason))
                return
            d_come = vd == OPEN and b.judge(self.cutoff)[0] != OPEN
            over = d_come if at_d else (d_come or b.clocks.mono() >= grace_end)
            if over:
                self.alarm = ("the native process is still there %s; stop sent at %s, reason %s"
                              % ("at D" if d_come else "one allowance after the decision",
                                 reading_text(rec["stopped"]), reason))
                return
            err = h.stop()
            if err:
                rec["stop_error"] = err

    def lines(self):
        """The lines for the caller's log: the decision, the stop and the process found gone, each with the three
        clock readings; then any alarm."""
        out = []
        rec = self.record
        if rec is not None:
            out.append("watch decision reason=%s late=%s late_discovery=%s decided_after_cutoff=%s "
                       "left_to_trigger_s=%s left_to_cutoff_s=%s %s"
                       % (rec["reason"], rec["late"], rec["late_discovery"], rec["decided_after_cutoff"],
                          _secs(rec["left_to_trigger_s"]), _secs(rec["left_to_cutoff_s"]), reading_text(rec["decided"])))
            if rec["stopped"] is not None:
                out.append("watch stop sent how=%s error=%s %s"
                           % (rec["how"], rec["stop_error"], reading_text(rec["stopped"])))
            if rec["gone"] is not None:
                out.append("watch native process gone after_cutoff=%s %s"
                           % (rec["gone_after_cutoff"], reading_text(rec["gone"])))
            else:
                out.append("watch native process NOT found gone")
        if self.alarm is not None:
            out.append("ALARM watch: " + self.alarm)
        if self.error is not None:
            out.append("ALARM watch: error inside the watch: " + self.error)
        for e in self.refresh_errors[:3]:
            out.append("watch refresh error (%d in all): %s" % (len(self.refresh_errors), e))
        return out
