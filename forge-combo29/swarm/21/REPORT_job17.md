# REPORT job17 — the PC build (r15) built and its three honesty rows checked

**What was asked.** TEXT 2: fetch `handoff/fable-opus-combo29-all-20261114`, read
`FABLE_TO_swarm_5.md`, build the source of the engine the owner's PC really plays in a SEPARATE
copy with `-DFORGE_MATE_ALPHA_GUARD=1`, and check the known bench numbers.

**The answer.** Built and **all three rows match exactly.**

| settings | bench 11 | bench 13 | bench 16 | go perft 5 | expected (file 5) |
|---|---|---|---|---|---|
| none (no setoption at all) | **312866** | **862329** | **3024920** | **4865609** | 312866 / 862329 / 3024920 / 4865609 |
| S14 | **242796** | **656517** | 2155620 | 4865609 | 242796 / 656517 / – / – |
| PC20 | **278024** | **587276** | 2343893 | 4865609 | 278024 / 587276 / – / – |

No `unknown option`, `invalid value` or `ERROR` line in any row, so every option was accepted
by the exe. Threads 1 and Hash 16 throughout (the swarm rule on Threads).

**How sure.** High. The patch's sha256 matches the stated prefix `d6bd72c531f785f4` exactly
(`d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a`), it applies with
`patch -p1` to a clean copy of 6b98f217 changing exactly the 11 stated files with no fuzz, and
the build is clean. The three rows are the pasted output of a committed script.

## Provenance of every step

| step | result | evidence |
|---|---|---|
| patch extracted from the file-5 fence | 2,319 lines, 11 `diff -ruN` headers | `/tmp/pc_r15.patch` |
| sha256 of the patch | `d6bd72c5…09c1a1a` — matches the stated prefix | `sha256sum` |
| `patch -p1 --dry-run` on a clean 6b98f217 copy | RC 0, 11 files, no fuzz | `job17/` output |
| apply | clean | `/tmp/pcwork/forge-combo29` (outside the repo) |
| build | clean, `-DFORGE_MATE_ALPHA_GUARD=1`, Release, g++ 13.3.0 | `~/b/pc` |
| three rows | all match | `job17/out/pins_*.txt`, `pins_summary.json` |

## What file 4 changed about my earlier practice

File 4 (read this session) says the four pins are DEFAULT-option numbers and the known node
sums are S14 numbers, and that a harness using one regime for both sees a false mismatch. My
earlier honesty checks were default-option runs (no setoption except Hash/Threads in the
20,000-FEN runner), which is the correct regime for the pins — so my pins stand. My job-level
reports did not compare against the O-depth-12/G-depth-12 sums, so no false mismatch was ever
reported by me.

## Swarm rule on Threads, applied from now on

- Every harness of mine runs Threads 1: `job6/safe_engine.py` defaults to `threads=1` and only
  `job13/churn_tsan.py` ever sends another value, because that job is specifically a threading
  test and it reports **no scores at all** (it counts TSan reports, crashes and illegal moves).
- So no recorded score of mine is provisional for threading reasons. Recorded in every finding
  line from here on: build + settings + Threads 1.

## What I did NOT do

- Did not build the PC tree under ASan+UBSan yet (next: the area-1 re-runs need it, and a
  sanitizer build of the PC source is the right way to catch anything the patch introduced).
- Did not run the O/G depth-12/14 sums on the PC build; file 4 says they are S14 numbers and my
  area does not need them, but they are a useful whole-build check I may add later.
- Did not commit the patch or any binary: the patch stays in `/tmp`, the build in `~/b/pc`.

## What I am NOT sure about

- Whether the PC's own trained net would change any of my area-1 results. File 5 says the PC
  plays with its own net and I keep the built-in evaluation, so evaluation-dependent results
  stay questions for the PC — my area (FEN parsing, protocol) is not evaluation-dependent, so
  this is a small caveat for me and a large one for area 5/6.

## Times

see `job17/stamps.txt`.
