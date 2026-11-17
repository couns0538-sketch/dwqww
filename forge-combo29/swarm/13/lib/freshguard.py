"""Runtime guard: a fresh engine process per search, unless the experiment declares it is about warmth.

WHY THIS EXISTS: a docstring saying "fresh process per search" is not a guard. I wrote that rule into my own
traps note and then violated it in job20 (S-F24), where one engine process served 32+ searches. Warm state
shifted scores by up to 80 cp on identical requests and manufactured a "move changed with the clock" that
does not exist in fresh processes; the finding had to be withdrawn. Auditing the rest of my harnesses found
the same fault in job9/mates_run.py and job9/negative_mates.py.

HOW TO USE — the simple, tested form:

    from freshguard import SearchCounter

    counter = SearchCounter()                 # one per experiment
    for fen in fens:
        counter.new_process()                 # records that a process started
        e = Eng()                             # your engine
        r = e.search(fen, ...)
        e.close()
        counter.record_search()               # records that ONE search used that process
    counter.assert_single_use()               # raises if any process ran more than one search

and for an experiment that is genuinely about warm state:

    counter.assert_single_use(allow_reuse=True, reason="S-C7 warm/cold comparison")

The guard cannot inspect your code, so it enforces the one thing that is checkable: **how many searches each
process performed**, asserted before the results are written. A harness that forgets to call `record_search`
gets a clear "0 searches recorded" failure rather than a silent pass.

Deliberately dependency-free and dependency-injected: it counts what you tell it, so there is no way for the
counting itself to alter engine behaviour.
"""
import sys


class SearchCounter:
    def __init__(self, name="harness"):
        self.name = name
        self._current = None
        self._per_process = []

    def new_process(self):
        if self._current is not None:
            self._per_process.append(self._current)
        self._current = 0

    def record_search(self):
        if self._current is None:
            raise RuntimeError("%s: record_search() called before new_process()" % self.name)
        self._current += 1

    def close(self):
        if self._current is not None:
            self._per_process.append(self._current)
            self._current = None

    def searches_per_process(self):
        self.close()
        return list(self._per_process)

    def assert_single_use(self, allow_reuse=False, reason=None):
        """Raise unless every process ran at most one search (or reuse is declared with a reason)."""
        counts = self.searches_per_process()
        if not counts:
            raise RuntimeError(
                "%s: no searches were recorded, so this guard proved nothing. Call new_process() before each "
                "engine start and record_search() after each search." % self.name)
        if allow_reuse:
            if not reason:
                raise ValueError("%s: allow_reuse requires a reason, so the choice is visible in the code"
                                 % self.name)
            return True
        bad = [n for n in counts if n > 1]
        if bad:
            raise RuntimeError(
                "%s: %d process(es) ran more than one search %s without declaring reuse. This is the fault "
                "that withdrew S-F24; see job20/CORRECTION_S-F24.md. Either start a fresh process per search, "
                "or call assert_single_use(allow_reuse=True, reason=...) if warmth is the experiment."
                % (self.name, len(bad), bad))
        return True


def self_test():
    """Prove the guard fails when it should. Run: python3 freshguard.py"""
    ok = True
    # 1. all-single passes
    c = SearchCounter("t1")
    for _ in range(3):
        c.new_process(); c.record_search()
    try:
        c.assert_single_use(); print("1. all-single              PASS (accepted)")
    except RuntimeError as e:
        ok = False; print("1. all-single              FAIL:", e)

    # 2. one reused process is caught
    c = SearchCounter("t2")
    c.new_process(); c.record_search(); c.record_search()
    try:
        c.assert_single_use(); ok = False; print("2. reuse                   FAIL (not caught)")
    except RuntimeError as e:
        print("2. reuse                   PASS (caught)")

    # 3. reuse with a reason passes
    c = SearchCounter("t3")
    c.new_process(); c.record_search(); c.record_search()
    try:
        c.assert_single_use(allow_reuse=True, reason="warm/cold experiment")
        print("3. declared reuse          PASS (accepted)")
    except Exception as e:
        ok = False; print("3. declared reuse          FAIL:", e)

    # 4. reuse without a reason is refused even if declared
    c = SearchCounter("t4")
    c.new_process(); c.record_search(); c.record_search()
    try:
        c.assert_single_use(allow_reuse=True); ok = False; print("4. reuse, no reason        FAIL (not caught)")
    except ValueError:
        print("4. reuse, no reason        PASS (caught)")

    # 5. a harness that records nothing fails rather than passing vacuously
    c = SearchCounter("t5")
    try:
        c.assert_single_use(); ok = False; print("5. nothing recorded        FAIL (passed vacuously)")
    except RuntimeError:
        print("5. nothing recorded        PASS (caught as 'proved nothing')")

    print()
    print("VERDICT:", "guard behaves correctly on all five cases" if ok else "GUARD IS BROKEN")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(self_test())
