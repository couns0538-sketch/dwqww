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
trigger has already passed is acted on at once and recorded as it happened (`late`, the readings of the decision).
A process that is still there when D comes (or one allowance after a decision made when D had already come, or in
a hold) is `alarm`: the caller writes the alarm and leaves with exit code 8. An error inside the watch ends the
process too (`fired` "error", `error` set): a wait is never left unwatched without a word.
`refresh` is the caller's: it reads a newer valid schedule and calls B.set; its errors are kept in refresh_errors
and the bounds in force go on holding.
"""
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
    return "utc=%.6f steady=%.6f boot=%s" % (r[0], r[1], "none" if r[2] is None else "%.6f" % r[2])


class Bounds:
    """The anchor and the bounds in force, judged by all clocks. Safe to use from two threads."""

    def __init__(self, clocks=None, hold_s=10.0):
        self.clocks = clocks if clocks is not None else Clocks()
        self.hold_s = hold_s
        self.anchor = self.clocks.read()
        self._lock = threading.Lock()
        self._b = {}
        self._latch = {}
        self.refused = []           # (name, the bound kept, the later bound offered)

    def set(self, name, utc_s):
        """Take a bound; never a later one than the bound in force. True when the offered bound is now in force."""
        utc_s = float(utc_s)
        with self._lock:
            old = self._b.get(name)
            if old is None or utc_s <= old:
                self._b[name] = utc_s
                return True
            self.refused.append((name, old, utc_s))
            return False

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
            return (v if v is not None else OPEN), left, r

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
        if not (allowance_s >= 0 and look_s > 0):
            raise ValueError("allowance_s >= 0 and look_s > 0")
        self.handle, self.bounds, self.refresh = handle, bounds, refresh
        self.allowance_s, self.look_s = float(allowance_s), float(look_s)
        self.cutoff, self.dispatch_end = cutoff, dispatch_end
        self.fired = None           # None | "cutoff" | "clock" | "error"
        self.record = None          # the decision, the stop and the process found gone, each with its reading
        self.alarm = None           # text: the process was still there when it had to be gone
        self.error = None           # text: an error inside the watch itself
        self.seen_gone = False      # the process ended by itself while the watch looked
        self.refresh_errors = []
        self._closed = False
        self._lock = threading.Lock()
        self._wake = threading.Event()
        self._t = threading.Thread(target=self._run, name="clockwatch", daemon=True)

    def __enter__(self):
        self._t.start()
        return self

    def __exit__(self, *exc):
        self.close()
        return False

    def close(self):
        """The wait is over. A watch that has not fired never fires after this; one that has is waited for."""
        with self._lock:
            self._closed = True
        self._wake.set()
        if self._t.ident is not None:
            self._t.join()

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
                if self.refresh is not None:
                    try:
                        self.refresh()
                    except Exception as e:
                        self.refresh_errors.append(repr(e))
                vd = b.judge(self.dispatch_end)[0] if b.get(self.dispatch_end) is not None else OPEN
                vt, left_t, r = b.judge(self.cutoff, lead=self.allowance_s)
                reason = "clock" if HOLD in (vd, vt) else ("cutoff" if vt == COME else None)
                if reason is not None:
                    self._fire(reason, r, left_t)
                    return
                self._wake.wait(min(self.look_s, left_t))
        except BaseException as e:
            self.error = repr(e)
            try:
                with self._lock:
                    closed = self._closed
                if self.fired is None and not closed:
                    self.fired = "error"
                    self.handle.stop()
            except BaseException as e2:
                self.error += "; then " + repr(e2)

    def _fire(self, reason, r, left_t):
        with self._lock:
            if self._closed:
                return
            self.fired = reason
        b, h = self.bounds, self.handle
        vd, left_d, _ = b.judge(self.cutoff)
        rec = {"reason": reason, "decided": r, "left_to_trigger_s": left_t, "left_to_cutoff_s": left_d,
               "late": vd == COME, "how": getattr(h, "how", "?"), "stop_error": None, "stopped": None, "gone": None,
               "gone_after_cutoff": None}
        self.record = rec
        rec["stop_error"] = h.stop()
        rec["stopped"] = b.clocks.read()
        by_clock = vd == OPEN                       # D is still ahead: the process must be gone when D comes
        grace_end = b.clocks.mono() + self.allowance_s
        while True:
            if h.gone(0.02):
                rec["gone"] = b.clocks.read()
                rec["gone_after_cutoff"] = b.judge(self.cutoff, reading=rec["gone"])[0] == COME
                return
            over = (b.judge(self.cutoff)[0] != OPEN) if by_clock else (b.clocks.mono() >= grace_end)
            if over:
                self.alarm = ("the native process is still there %s; stop sent at %s, reason %s"
                              % ("at D" if by_clock else "one allowance after the decision",
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
            out.append("watch decision reason=%s late=%s left_to_cutoff_s=%.6f %s"
                       % (rec["reason"], rec["late"], rec["left_to_cutoff_s"], reading_text(rec["decided"])))
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
