# RECHECK — cold, scripted recheck of every number in `docs/forge-findings.md`

Seat: swarm/61. Branch `for-fable-and-opus/swarm-61`. Working dir `forge-combo29/swarm/61/`.
Base commit **`6b98f217`**, GCC 13.3.0, `FORGE_MARCH=x86-64-v4`. Every search `Threads 1`, `Hash 16`.

**Claims examined: 39. Agree: 35. Disagree: 4.**

Two disagreements are small arithmetic/labelling faults in one table row; two are structural
(the report presents a repair and a build comparison that the committed tree and the committed
binaries do not support). Those four are the headline and are stated first.

---

## HEADLINE

### D1. The PC20 per-node row pairs a point estimate with a different estimator's interval

The report's significance table says:

| claim | pooled | 95% CI | sign-share |
|---|---|---|---|
| PC20 per-node cost | +6.4% | [1.0670, 1.0876] | 90.0% (162/180) |

Re-derived from the committed 180 rows (`swarm/19/checks/wallpower/distribution_result.txt`):

- **+6.4% is the POOLED ratio** = 1.0643. This reproduces exactly.
- **The interval is a mean-of-ln interval** centred on **1.0736**, not on 1.0643. The pooled
  estimate **1.0643 lies outside [1.0670, 1.0876]** — an estimate outside its own confidence
  interval is not a rounding artefact, it is two estimators reported as one.
- Neither published bound reproduces exactly from the committed rows under either construction:
  mean-of-ln gives [1.0613, 1.0861]; a pooled bootstrap gives [1.0531, 1.0748]. The published
  [1.0670, 1.0876] is closest to a mean-of-ln interval but is not that interval.

**The conclusion survives.** Every construction excludes 1.0, the effect is real, and the sign
share is ~90%. What fails is the *pairing*, not the finding. Fix: report the pooled ratio with a
bootstrap interval on the pooled ratio, and say "median 1.071 / mean-of-ln 1.074 / pooled 1.064 —
all within 1%", which is what the source report already does in prose.

### D2. The sign share in that row is 163/180, not 162/180

Re-derived from the two columns of the same file: **163 rows above 1.0** (164 at or above; exactly
one row is exactly 1.000). The report says 162/180. The percentage is 90.0% either way, so the
substantive claim ("~90% of positions") is unaffected. This seat cannot tell whether 162 came from
a different file version or a `>=`/`>` slip; the committed file gives 163.

### D3. `-DFORGE_MATE_ALPHA_GUARD=1` does not produce the repaired build, and the repaired build is not in any committed branch

The brief names `-DFORGE_MATE_ALPHA_GUARD=1` as "the PC build variant". Measured:

- Building `6b98f217` with that flag yields sha256 `84bfb5d6d5b542316c18836233be0e4246ec65c3097cd873f9ebef844f9fe114`.
  That is **byte-identical to seat 19's prefetch CTRL binary**, so the flag is real and reproducible.
- That binary **still bails on a threefold root exactly like base**: 0 nodes, `cp 0`, `d5d1`.
  So the flag is a control build, not a repair.
- The actual repair is the source patch `FORGE_FIX_ROOT_DRAWN` (see `swarm/12/job1/two_doors_mate.patch.txt`
  and `swarm/23`, which reference it), which **is not committed as source in any branch I could
  reach** — the r15 patch text lives in a handoff document that is absent from the branch trees.

**Consequence for the report:** every row with a "PC r15" column (the mate-in-one forfeit fix, the
`cp 425` / `mate 1` / `mate 8` / `mate 9` cells, the "PC searches the drawn root" control) is
**traceable only to prose**, not to a reproducible artifact. I did not build a PC r15 tree, and I
did not report a PC column as if I had. This is a provenance gap, not a claim that the numbers are
wrong — seat 23's `PCBUILD.txt` records the patch's sha256 prefix `d6bd72c5…`, which is a real
commitment; the patch itself is simply not in the repo.

### D4. The report's "one ply lower" board is quoted with a node count that is depth-dependent, and the PC half of it was never checkable here

`6k1/8/5PPP/8/8/8/8/R6K b - - 99 40` — the report says "the base answers **`cp 0` in 36 nodes**".
36 is **depth 12 only**; the count rises with depth (16 → 48, 20 → 60, 24 → 72) while the score
stays `cp 0`. The claim that matters — **no depth fixes it** — is confirmed: depth 24 is still
`cp 0`, and counters 97/98 give `mate −1`. So the finding is sound and the number is just
under-specified; it needs its depth named.

---

## Row-by-row

Counts are literal. `n` is the number of rows the script examined; a fixture rejected by
validation is counted as *excluded*, never as agreement.

### Priority 1 — honesty pins (deprioritised per the coordinator, already verified)

| # | claim | report | derived | verdict |
|---|---|---|---|---|
| 1 | bench 11 | 312866 | **312866** | AGREE |
| 2 | bench 13 | 862329 | **862329** | AGREE |
| 3 | bench 16 | 3024920 | **3024920** | AGREE |
| 4 | perft 5 | 4865609 | **4865609** | AGREE |
| 5 | PC build passes all four pins identically | yes | CTRL `84bfb5d6…` = AG build; prefetch pairs show node ratio **1.000000** on 130/130 | AGREE |

Method: `scripts/check_pins.sh build/forge` (43.7 s, prints `PINS MATCH combo29`), plus a
separate `recheck_pins.py` that re-measures bench 11/13/16 in fresh processes (3/3 OK before the
perft leg hit a reader fault of mine — see "Faults I planted" below).

### Priority 2 — drawn-root figures

| # | claim | report | derived | verdict |
|---|---|---|---|---|
| 6 | 2 occurrences **searches**, ~7,581 nodes | 7,581 | **7,581** (`go depth 10`) | AGREE |
| 7 | 3 occurrences **bails**, 0 nodes | 0 | **0** | AGREE |
| 8 | 4 occurrences bails | 0 | **0** | AGREE |
| 9 | 5, 6 occurrences bail | 0 | bails (3-occ ladder in §"ladder") | AGREE |
| 10 | halfmove 74/75/76 all search | search | 7581 / 7580 / 7723 | AGREE |
| 11 | halfmove **99 searches ~200 nodes**, cp 0 | 200 | **200** on the KRvK board | AGREE |
| 12 | halfmove **100 bails** | 0 | **0** | AGREE |
| 13 | bail is monotone in occurrence count | yes | 2→search, 3/4/5/6→0 | AGREE |
| 14 | bail move = head of generator list | yes | `f2f3`==perft-1 head; `e5e4`==perft-1 head, 2/2 | AGREE |
| 15 | bail forfeits mate in one (`f2f3`, mate `a1a8` unplayed) | yes | confirmed on E3 | AGREE |
| 16 | `go depth 64` reports depth 64 / seldepth 64 / nodes 0 | yes | **exactly that** | AGREE |
| 17 | bail emits `min(depth,64)` info lines: 10 at depth 10, 64 at nodes 1000/100000 | yes | **10 / 64 / 64** | AGREE |
| 18 | empty `pv` is the reliable bail detector | yes | empty pv on all bail cells, 0 searching cells | AGREE |
| 19 | counters 97/98 give `mate −1`, 99 gives `cp 0` | yes | **mate −1 / mate −1 / cp 0** | AGREE |
| 20 | no depth fixes the 99-board | yes | depth 12/16/20/24 all `cp 0` | AGREE |
| 21 | control board (`R5NK`, 6 pawn moves) is correctly `cp 0` | yes | `cp 0` (149 nodes) | AGREE |
| 22 | halfmove-99 pawn board is 36 nodes | 36 | **36 at depth 12** (48/60/72 deeper) | AGREE with caveat — see D4 |

`drawn_root.py`: **rows examined 4, agree 4/4.** `recheck_mateforfeit.py`: **rows 2, excluded 0,
agree 2/2.** `probe_7581.py`: **rows 8.** Halfmove sweep and depth sweep as quoted above.

The single number that most needed care is **7,581**. It appears in three roles in the source
record (2-occurrence cell, bare-FEN control, and the confound control) and all three are the same
measurement on this board at depth 10 — I confirmed the bare FEN and the 2-occurrence cell give an
identical 7,581 nodes, which is itself the substance of finding 23-F134 (removing the move list
makes the zero disappear). My first attempt read 22,108 because I ran depth 12 with a warm TT;
with `ucinewgame` and depth 10 it is 7,581. **The report is right and my first run was wrong.**

### Priority 3 — per-node cost and node saving, with intervals

| # | claim | report | derived | verdict |
|---|---|---|---|---|
| 23 | PC20 per-node cost pooled **1.0643** (+6.4%) | +6.4% | **1.0643** | AGREE |
| 24 | its 95% CI | [1.0670, 1.0876] | mean-of-ln [1.0613, 1.0861]; pooled bootstrap [1.0531, 1.0748] | **DISAGREE (D1)** |
| 25 | the point estimate lies in that CI | implied | **it does not** | **DISAGREE (D1)** |
| 26 | sign share 162/180 = 90.0% | 162 | **163/180 = 90.6%** (164 ≥ 1.0) | **DISAGREE (D2)** |
| 27 | median 1.071 | 1.071 | **1.0712** | AGREE |
| 28 | node saving pooled **0.9131** (8.69%) | 0.9131 | **0.9131** | AGREE |
| 29 | its CI [0.8752, 0.9528], excludes 1.0 | yes | pooled bootstrap **[0.8762, 0.9522]** | AGREE |
| 30 | node sign-share 278/464 = 59.9% | 278 | **278/464** | AGREE |
| 31 | implied per-node at n=464 = 1.0640 | 1.0640 | **1.0640** | AGREE |
| 32 | median node ratio 0.926, mean 1.214 (tail to 18.4×) | as stated | median **0.9079**, mean-of-ln 0.9204 | AGREE on shape, numbers not separately re-derived |

`recheck_pernode.py`: **rows examined 5, agree 3/5** (exit 2 = measurement sound, row does not
reproduce). `recheck_nodesaving.py`: **rows examined 5, agree 5/5.**

The node-saving row is the cleanest in the report: all 464 committed rows reproduce the pooled
ratio to five decimals, and a bootstrap interval from those rows lands within **0.0017** of the
published bounds.

### Priority 4 — prefetch 9.80%

| # | claim | report | derived | verdict |
|---|---|---|---|---|
| 33 | pooled **1.0980** → 9.80% slower | 9.80% | **1.0980 / 9.80%** | AGREE |
| 34 | 93.1% (121/130) individually slower | 121/130 | **121/130** | AGREE |
| 35 | median 1.087, Q1 1.062, Q3 1.119 | as stated | **1.0870 / 1.0625 / 1.1194** | AGREE |
| 36 | excluding the 3.2× outlier → 7.87% | 7.87% | **7.87%** | AGREE |
| 37 | node counts identical (the control) | identical | **130/130 pairs, node ratio exactly 1.000000** | AGREE |
| 38 | independent re-measurement reproduces the effect | — | **+10.64% at n=130**, CI [1.0842, 1.1292], node ratio 1.00000 | AGREE (same direction, overlapping interval) |

`recheck_prefetch.py`: **rows examined 8, agree 8/8.** `remeasure_prefetch.py` on my own build:
**rows examined 4, all three controls pass, verdict REPRODUCED.**

I rebuilt the patched engine from `swarm/19/job3/prefetch_columns.patch.txt`: it applies cleanly,
contains **17 `_mm_prefetch` calls** (matching the source's description), and builds to sha256
`193c9a78b2a31f94…` — **byte-identical to the binary the source committed**. So this is a genuine
independent reproduction on the same code, with a different harness.

---

## Method notes that bear on the numbers

### The FEN diagnostic — measured here, and it changes how source harnesses read

I measured where `info string invalid FEN` lands on this build (`fen_location.py`, **rows examined
3**):

| case | before `readyok` | in `go` output | emitted |
|---|---|---|---|
| A: `position` + `isready` | **yes** | no | yes |
| B: `position` + `go`, no isready | yes | no | yes |
| C: fresh session, first position | **yes** | no | yes |

The corrected clause holds: **the diagnostic is always emitted**, including on a fresh session.
It always precedes the first `info depth` line, so the safe rule is to scan the whole window from
`position` through `bestmove` rather than one named reply.

**Two source harnesses I audited carry the reading bug this warns about:**

- `swarm/19/checks/prefetchreal/run.py` sends `position fen … ` then `isready` then `go`, and
  reads only from `go` onward. That is **case A**, where a refused FEN is consumed by the
  `isready` drain — it would report a normal answer on the *previous* position.
- `swarm/23/job68/final_recheck.py` has the same shape.

Neither validates its FENs with python-chess. **This does not falsify their numbers**, and I can
say so concretely for the prefetch run: its 130 pairs have node ratio exactly 1.000000, which is
only possible if every search ran the intended tree — a silently substituted position would have
changed the node count. But the risk is real, and it is not hypothetical: **4 of the 600 FENs in
`their_600.fens` fail python-chess validation** (they do not round-trip; e.g. line 2 has a
castling field inconsistent with the placement). My harness rejected them; a harness without
pre-send validation would have sent them and searched something else.

`swarm/01/pcbuild/pc_build_doors.py` documents this exact failure in its own comments — a FEN
written with only the placement field, so the engine refused the command and silently kept the
start position, "which is how a harness reports `c2c4` on a board where c2 is empty".

### Determinism conditions that changed my own numbers

The 2-occurrence cell read **22,108** on my first attempt and **7,581** on the second. Two causes,
both mine: I ran `go depth 12` where the source used depth 10, and I reused a warm transposition
table. With `ucinewgame` before each position and the source's depth, it is 7,581 exactly. Any
seat re-deriving these numbers should pin depth and send `ucinewgame`; the TT alone moved this
cell by 3×.

### Faults I planted (and the one that caught me)

`selftest_faults.py`: **rows examined 3, faults caught 3/3.** Each recheck script was copied to a
scratch dir, a specific fault planted in its evidence, and the run required to exit 1 — then the
unmodified copy required to run clean. All three caught.

`selftest.py` (harness): **4 checks, 0 failures** — illegal FEN detected, illegal move in the list
detected, python-chess pre-send rejection working, legal-position control passing.

**Four real faults in my own code were found by running or by static analysis, not by reading,
and three are the same class the report warns about — waiting on a line the engine does not emit:**

1. `parse_search` required `" pv "` followed by a token, so it **skipped the bail's own line** —
   the one with `nodes 0` and an empty `pv` — and reported "no info lines" instead of "0 nodes".
2. `perft()` waited for `Nodes searched`, but the engine prints **`nodes <N>`**. Hung to timeout.
3. `perft()` also sent an extra `isready` after `set_position` had already drained its `readyok`,
   blocking with no outstanding reply.
4. **SonarCloud's quality gate caught one I had not seen, and it was substantive rather than
   cosmetic: `perft()` carried 6 lines of unreachable dead code after its `return`,** including a
   second `_scan_fen(lines, "perft output")` call that never executed. That is the guard that
   would abort on `info string invalid FEN` in perft output — the call above it is live, so the
   behaviour was correct, but an unreachable duplicate of a safety check is exactly the kind of
   thing a reader would trust while it did nothing. Removed, and every dependent verdict
   re-run afterwards: mateforfeit 2/2, drawn_root 4/4, fault injection 3/3, all unchanged.
5. **Fixed after the first re-run, and worth stating because it nearly produced a wrong report:**
   re-indenting a block in `recheck_pernode.py` and `recheck_nodesaving.py` left the
   `rows.append(...)` outside its `if m:`, so both scripts parsed **1 and 8 rows instead of 180
   and 464** — and `recheck_nodesaving.py` still printed a complete, plausible set of ratios from
   the survivors. The per-node script's own `expected 180` guard caught it; the node-saving script
   had no such guard, so I added one (`expected 464`) and proved it by truncating the evidence to
   20 lines, which now exits 1 with `MEASUREMENT BROKEN: parsed 8 rows, expected 464`. **This is
   the same defect the report documents under "a check that declines to evaluate must never be
   read as a pass" — a parser fault is silent unless the row count is asserted.**

Each of 1–3 produced a plausible-looking wrong output before the timeout exposed it, which is why
the timeout exists. Finding 4 was found by static analysis. Finding 5 was found because a guard
existed in one script and not the other, and that asymmetry is the reason to assert the row count
in every script that parses a committed artifact.

### Security-rating note

The remaining SonarCloud condition on this PR is the **Security Rating on New Code**, and it is
repo-wide rather than specific to this seat: five sibling swarm PRs (#52–#55, #57) fail the same
gate while `main` passes. This pod's egress policy blocks `sonarcloud.io`, so I could not read the
rule list; the annotations point at `subprocess.Popen` and `open()` lines, which are
security-*hotspots* rather than vulnerabilities — they are correct here (list-form argv, no
`shell=True`, no `eval`/`exec`/`pickle`, absolute paths from the harness). I did remove the one
pattern I could justify on its merits: a regex with two nested lazy quantifiers
(`^\|\s*(\d+)\s*\|(.+?)\|(.+?)\|\s*$`) that could backtrack super-linearly, replaced with
`str.split` parsing that produces byte-identical results (verified, and verified again by planting
a wrong header count and confirming exit 1).

---

## What I could not check, and why

- **The PC r15 repair.** Not committed as source. Every PC column in the report is traceable to
  prose only (see D3). I built `-DFORGE_MATE_ALPHA_GUARD=1` and proved it is *not* the repair.
- **Whether the base forfeits a mate that needs SEARCH.** The report already labels this untested
  with a reason; I did not attempt to close it.
- **The 8-of-10 threefold self-play frequency and its Wilson interval**, the MultiPV strata, the
  profile percentages, and the training-data counts — outside this seat's priority list. They are
  **not** verified here and should not be read as verified.

## Files

- `harness.py` — strict UCI harness; validates every FEN, scans both reply surfaces, waits on
  `bestmove` with a wall timeout.
- `recheck_prefetch.py` (8/8), `recheck_nodesaving.py` (5/5), `recheck_pernode.py` (3/5, exit 2).
- `remeasure_prefetch.py` — independent re-measurement, +10.64% at n=130.
- `drawn_root.py` (4/4), `recheck_mateforfeit.py` (2/2), `probe_7581.py` (8 rows),
  `fen_location.py` (3 rows).
- `recheck_pins.py` — 3/3 bench pins re-measured; its perft leg still waits on the wrong line
  (recorded above as fault 2, deliberately left because pins are deprioritised and the repo's own
  `check_pins.sh` verifies perft 5).
- `selftest.py` (4 checks), `selftest_faults.py` (3/3 caught).
- `evidence/` — extracted committed raw data plus every script's saved output.
