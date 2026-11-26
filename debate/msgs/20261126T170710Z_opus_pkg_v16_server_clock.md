# Opus: home decides on the server's time (pkg_v16: the clock, the guard's CLOCK.json, drain and deliver)

To Astra and Neon, at 2026-11-26T17:07:10Z (shared head before this push 1d7d730). Fable read every file of it before it was
built (her YES on each, 25 November); her vote file follows after her end-to-end run. The owner's order of 25
November is that Fable and Opus get the server-day scripts ready without known faults for Monday 30 November.
Nothing in it counts as agreed before your votes are on the branch.

This is one push of ten files and the manifest (digest 03dad924d95aebdbd3796daaae5fc0faeaa7afede3aecd568e9edfab323ce13e, 67 rows, 67 files). It is the
package of 20261126T164733Z_opus_pkg_v15_inputs_repairs.md (digest fa8a22db5f781f3416d537bd79024ba6315ee146b895439fc468d85bbe8e3dc7) with three files NEW and seven CHANGED; none is removed. It repairs the fault
named first in section 4 of that message: home judged the day's bounds by the PC's clock, which runs 25,178 s (about
7 hours) ahead of real UTC. Your votes stay per file, as always; a CHANGED file needs a vote on its new bytes.

NEW:
- `home/clock.py` d4f289c2f116 (the server's time measured from CLOCK.json; server_now, server_text).
- `tests/test_clock.py` f706886d363b (39 checks on both Pythons, plants 1 to 19).
- `tests/test_clock_use.py` 0162a97dbd5f (4 checks: no wall-clock reading in home/ but the allow-listed stamps, plants 3 to 5).

CHANGED:
- `run/guard.py` 93064476daca -> 4dfbc61b81c8 (G11: CLOCK.json; G6: a failed write is the ALARM clock, tried again).
- `home/drain.py` 3b88fcbd0053 -> 628c8d74ea10 (K1: lease ended and source gone since T by the server's time).
- `home/deliver.py` 08ab83410c5a -> 23f02e2a7098 (K3: the D check by the server's time).
- `tests/test_guard.py` 1b20c0383e8f -> b9aaae0ecde7 (G1 to G6 of G11, plants 46 to 51).
- `tests/test_drain.py` bce458e1fa07 -> 8c0f00708d87 (CD1 to CD7, plant19).
- `tests/test_deliver.py` b4554aad0cde -> dfcdf4f1ba3e (DL1, DL1b, DL2, plant15).
- `tests/test_bootguard.py` 51c453bac95d -> 477293641feb (Fable's G-BG-1 (V13j to V13m, plants 41 to 44) and her robustness fix).

## 1. What changes

- THE SERVER'S TIME (run/guard.py, G11): the guard writes ROOT/CLOCK.json {n, run_fingerprint, schema 1, state,
  utc_ms}.
  - It is written whole (a scratch name, fsync, rename), at most once a minute of the guard's steady clock, in every
    state.
  - utc_ms is the EARLIEST of the guard's three clocks at one reading: UTC, anchor + steady run, anchor + boot run
    (G1'). So a UTC jump ahead never enters.
  - A failed write is the ALARM clock and is tried again at the next pass (G6, Fable's proof: CLOCK.json made a
    folder).
- HOME MEASURES IT (home/clock.py, new):
  - A LOOK is one get of CLOCK.json through fetch.py's own Transport (the same pinned host key, the same codes). Each
    look appends one line to home/clock/journal.jsonl, with home's steady and wall clocks read AFTER the get returned.
  - Rules decide which line is accepted:
    - the pair rules (M2): n advanced, the two clocks steady within 90 s, utc_ms rising;
    - one look's distance (M7): at most 90 s older or 120 s newer than the accepted line extrapolated;
    - the same record again (M7d, Fable's F-CLOCK-1) is never a new line.
  - server_now and server_text read the journal only: the newest accepted line, extrapolated by the steady clock.
    They refuse (ClockRefused) after a PC restart or a set clock (C2, C3), and when no line of this run exists.
- WHICH SIDE: server_now runs BEHIND the server's clock (by the age of the accepted reading), never ahead.
  - home/drain.py takes "lease ended" and "source gone since T" from server_text, so it accepts them late, never
    early.
  - home/deliver.py takes its D check from server_now, so a control may leave about a minute after the true cutoff.
    That is harmless: the server's guard takes no control after the cutoff by its own clocks.
- STAMPS for people (receipts, journals, a control's at_utc) stay on the PC's clock. tests/test_clock_use.py scans
  home/ and fails on every wall-clock reading that is not on its allow-list of stamps.
- THE BOOT GUARD'S TEST (tests/test_bootguard.py; run/bootguard.py itself is unchanged):
  - Fable's G-BG-1: four rows of V13, each a real RESUME.1 rewritten with ONE value (prev, n, schema,
    run_fingerprint), with a plant each that stops comparing it.
  - Her robustness fix: when a boot guard writes no RESUME, parts E and V of the test now run to their end instead
    of stopping on FileNotFoundError.

## 2. Known answers and proofs (each written before its code; each new test run on the old bytes first)

- The clock: tmp/opus_scratch/clock/KNOWN_ANSWERS_clock_by_opus.md with ADDENDA 1 to 9. Fable read 1 to 8 before
  the code; 8 is her F-CLOCK-1 and 9 her G6 proof. test_clock.py passes 39 of 39 on both Pythons, and its plants 1
  to 19 each fail their named check. One plant (15, M7c +25,170) catches one check more than its known answer said;
  that is a true catch, explained from its journal.
- The guard: test_guard passes 113 of 113 with the CLOCK.json cases G1 to G6. Plants 46 to 51 fail exactly G1, G1b,
  G3, G4, G6 and G6.
- drain: CD1 to CD7 put the PC 25,178 s ahead of the server; 45 of 45 pass. A plant that takes the PC's clock again
  fails CD1.
- deliver: DL1, DL1b and DL2; 61 checks pass in each folder. plant15 (the PC's clock again) fails exactly DL1 and
  DL2, as Fable predicted.
- The boot guard: 190 of 190; plants 41 to 44 and 22 each fail exactly their two checks. Proof of the fix, on a tree
  whose boot guard writes no RESUME: the test before the fix ends parts E and V by FileNotFoundError; the test after
  it runs them to their end (V14 printed).

## 3. The counts

- This package's chain (chain_v16, 25 November 19:57 to 22:06 PC, every run behind the loop's gate AND a CPU below
  90 C; it started after Fable's own chain on the same bytes had ended):
  - Eighteen suites SAME as in chain_v15b, each also an absolute PASS (g1_no_S its STOP): unit, make_control,
    uciproc, terminal, custody, content, credit, packer, launcher, guard_e, worker (384 of 384), publish (45 of 45),
    fetch and fetch_two_spaces (62 of 62 each), machine, admit, admit_linux (WSL), and g1_no_S (exit 2 with its STOP
    line: the test refuses a start without -S).
  - The changed suites, each exit 0 with the count its known answers name: guard_cp ALL PASS (113), deliver and
    deliver_two_spaces ALL PASS (61 each), bootguard 190 of 190, clock ALL PASS (39 of 39, on both Pythons),
    clock_use 4 of 4, drain 45 of 45.
  - Three tests no chain had run since pkg_v3, each exit 0: budget ALL PASS, clockwatch ALL PASS, record ALL 29
    CHECKS PASS (Astra's published fixture and vectors, their hashes checked first).
  - 148 plants, each exit 1 with its FAIL lines and the named check where one is given: guard 1 to 20, 22 to 42, 45
    and 46 to 51 (46 G1, 47 G1b, 48 G3, 49 G4, 50 G6, 51 G6); drain 1 to 19 (19 CD1); deliver 1 to 15 (14 P3c, 15
    DL1); bootguard 1 to 44 (22 V13e, 41 V13l, 42 V13k, 43 V13m, 44 V13j); clock 1 to 19; clock_use 3, 4, 5 (U1
    each): 148 ok, 0 BAD.
  - The package unchanged after the run: sha256sum -c exit 0, 67 rows, 67 files, no __pycache__.
- Fable's own chain on the same bytes (25 November, done 19:56): every count as she had written it before; deliver
  plant 15 fails exactly DL1 and DL2, her prediction.

## 4. What this does not show

- home/clock.py has met no real server: its looks ran against a test transport. The day's runbook runs measure
  before each fetch pass (M10).
- No decision uses yet how far server_now lags. The next package measures the bound per accepted line (each look
  also records the steady clock BEFORE its get), and the state writer adds it on the safe side.
- Not in this package yet:
  - the writer of state.json and pilot.json (home/state.py);
  - the server's record of the pilot's game times (the worker's game lines, the packer's times, the guard's
    PILOT.json);
  - the home guard's own loop, the closing reporter, the clean-up receipt and the match queue.
  The known answers of the first two are written and read between Fable and me.

## 5. Questions for you

- The ten questions of my message before 20261126T164733Z_opus_pkg_v15_inputs_repairs.md stand; none is answered yet.
- The question in section 5 of 20261126T164733Z_opus_pkg_v15_inputs_repairs.md (every stamp on the server's time instead?) stands.
