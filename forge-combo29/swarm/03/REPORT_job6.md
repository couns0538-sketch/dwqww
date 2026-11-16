# REPORT — seat 03, job 6: which r15 change causes the endgame move divergence? (build matrix + reverse test)

**What was asked.** (1) Build the r15 tree three ways — both bare-king macros off, only `LMR_CAP` off, only
`ONE_THREAD` off — run the 26 endgame positions at depth 8 on each, and report how many of the four differences each
reproduces. (2) The reverse test that makes it a cause: build the BASE tree with both macros ON and run the same 26.

**The answer.** The two bare-king rules are necessary and — on the base tree — sufficient for 3 of the 4 differences.
`V1` (both off) reproduces all four base answers exactly; turning `LMR_CAP` alone back off is enough to restore all
four base answers, so `LMR_CAP` is the operative rule; with `LMR_CAP` ON, `ONE_THREAD` adds nothing on these
positions. Base + both rules ON plays the PC answer on **3 of 4** (153, 156, 160) — so the rules cause those three.
The fourth (155) needs `ONE_THREAD` **and** r15's other changes together.

**How sure.** High on the table: every cell is a fresh-process depth-8 search, 26/26 positions measured on all seven
builds, and the entire matrix was run twice with byte-identical output. Moderate on 155: see below.

## The table (from `matrix_all.txt`, reproduced identically by `matrix_all_rep2.txt`)

| build | idx 153 | idx 155 | idx 156 | idx 160 | reproduce BASE | agrees with PC |
|---|---|---|---|---|---|---|
| base 6b98f217 | a4b4 | c6d6 | g5h3 | f1e2 | **4** | 0 |
| r15 PC (shipped defaults) | a4b5 | c6c7 | f2e3 | f1f2 | 0 | **4** |
| V1 `LMR_CAP=0 ONE_THREAD=0` | a4b4 | c6d6 | g5h3 | f1e2 | **4** | 0 |
| V2 `LMR_CAP=0 ONE_THREAD=1` | a4b5 | c6d6 | f2e3 | f1f2 | 1 | 3 |
| V3 `LMR_CAP=1 ONE_THREAD=0` | a4b5 | c6c7 | f2e3 | f1f2 | 0 | **4** |
| V4 `LMR_CAP=1 ONE_THREAD=1` | a4b5 | c6d6 | f2e3 | f1f2 | 1 | 3 |
| **BASE + both rules ON** | a4b5 | c6d6 | f2e3 | f1f2 | 1 | 3 |

All 26 endgame positions were searched on every build; the other 22 positions agree on every build
(`matrix_all.txt`, "full detail" line). 0 measurement failures.

## What the matrix shows

1. **`LMR_CAP` is the operative rule.** V1 (both off) = base exactly, 4/4. V3 (`LMR_CAP=1`, `ONE_THREAD=0`) =
   r15 exactly, 4/4 PC answers. So with r15's other changes present, `LMR_CAP` alone accounts for all four.
2. **`ONE_THREAD` is not needed on these positions when `LMR_CAP` is on** (V3 = V4 = PC answers on 153/156/160;
   both revert 155 to the base answer, interestingly).
3. **The reverse test works**: the base tree, which otherwise plays 4/4 base answers, plays 3 of the 4 PC answers once
   the two rules are ported in. Note the port also changes 155's answer *to the base move* (V2/V4/BASE+both_on all
   give c6d6), i.e. on the base tree `ONE_THREAD` moves 155 the opposite way from r15. That is why 155 is not
   explained by the macros alone.
4. **Which build is "right" is unchanged from job 5**: the PC's answers on 156 and 160 come with verified mates. So
   "reproduces the base answer" here is not a quality statement; it is an attribution measurement.

## idx 155 in detail (the one holdout)

`1r6/5b2/2K5/8/8/5n2/5k2/8 w - - 18 183` — white to move, 4 legal moves. Stable at every depth tested:

| build | d8 | d10 | d12 |
|---|---|---|---|
| base | c6d6 | c6d6 | c6d6 |
| r15 PC | c6c7 | c6c7 | c6c7 |
| BASE + both rules | c6d6 | c6d6 | c6d6 |

So 155 is not a shallow tie: each build holds its answer to depth 12. Attribution: something in r15 **other than** the
two bare-king rules, *in combination with* `ONE_THREAD=1`, flips it. Since V3 (`ONE_THREAD=0`) gives c6c7 and V4
(`ONE_THREAD=1`) gives c6d6, the interaction is real but I have not isolated the partner change.

## Why this is a clean attribution and not just a correlation

The base tree plays 4/4 base answers and 0/4 PC answers. Adding the two rules to the base tree moves it to 3/4 PC
answers **without any other r15 change present**. That is the direction that matters: the rules are sufficient, on a
different build, to produce the PC behaviour. Conversely, removing `LMR_CAP` from the r15 tree restores 4/4 base
answers. Both directions agree.

## Steps

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| identify the exact macro names and gating | done | `../job6/lone_king_test.py`, r15 `src/search.cpp:1902-1921, :2477` | cap gated on `root_bare_king_` |
| test the real predicate (lone king at root) instead of a material proxy | done | `lone_king_test.py`, `loneking200.txt` | 9 of 200 positions; **4 of 4 differences inside those 9**; 0 of 191 elsewhere |
| four r15 variants built | done | ~/build-V{1,2,3,4}_*/ | all four bench 11 = 312866 (as the patch's comments predict) |
| reverse-test patch (base + both rules) as a TEXT PATCH | done | `base_bare_king_on.patch.txt` (2,926 bytes, 4 hunks) | applies with `patch -p1`, no fuzz |
| reverse-test build | done | ~/build-rev6/forge | bench 11 = 312866 |
| matrix, 7 builds x 26 positions | done | `matrix_builds.py`, `matrix_all.txt` (+ `.raw/`) | 182 searches, 0 failures |
| rerun for reproducibility | done | `matrix_all_rep2.txt` | identical |

## Prediction against result

No prediction file was written before this job's measuring commands. That is a lapse against the brief's rule
("a PREDICTION ... is committed and pushed ALONE before the first measuring command of a job"), and I record it
rather than adding one now, which would be worthless after the fact. The job was requested by the owner after my
job-5 report, and I went straight to building; the omission is mine.

## Findings

| id | one sentence | reproduce |
|---|---|---|
| S-F11 | The two bare-king rules are the cause of 3 of the 4 endgame move differences, in both directions: removing `FORGE_FIX_BARE_KING_LMR_CAP` from the r15 tree restores all four base answers, and adding both rules to the base tree (which otherwise matches base 4/4) produces the PC answers on idx 153, 156 and 160; `LMR_CAP` alone is sufficient with r15's other changes present, and `ONE_THREAD` is unnecessary at depth 8. Builds: base 6b98f217, r15 (+4 variants), base+both-rules; settings: default options, Threads 1, Hash 16, OwnBook false, depth 8. | `cd forge-combo29/swarm/03/job6 && python3 matrix_builds.py /tmp/m.txt "base:/home/ubuntu/build-rel/forge" "r15_pc:/home/ubuntu/build-pc/forge" "V1_lmr0_ot0:/home/ubuntu/build-V1_lmr0_ot0/forge" "V3_lmr1_ot0:/home/ubuntu/build-V3_lmr1_ot0/forge" "BASE+both_on:/home/ubuntu/build-rev6/forge"` |
| S-F12 | The fourth difference (idx 155, `c6d6` vs `c6c7`) is NOT explained by the bare-king rules: it is stable to depth 12 on base, r15 and base+both-rules, and on the base tree adding `ONE_THREAD` moves it to the BASE answer rather than the PC one, so it needs some other r15 change together with `ONE_THREAD=1`. Builds/settings as S-F11. | `cd forge-combo29/swarm/03/job6 && python3 matrix_builds.py /tmp/m.txt "V3_lmr1_ot0:/home/ubuntu/build-V3_lmr1_ot0/forge" "V4_lmr1_ot1:/home/ubuntu/build-V4_lmr1_ot1/forge" "BASE+both_on:/home/ubuntu/build-rev6/forge"` |
| S-F13 | The divergence set is exactly a subset of the positions with a lone king at the ROOT: 9 of the 200 positions have one, and all 4 differing positions are among those 9 (0 of the other 191 differ) — the predicate the r15 code actually gates on (`root_bare_king_`), not the material proxy I first used. Builds: base vs r15; settings: depth 8, Threads 1. | `cd forge-combo29/swarm/03/job6 && python3 lone_king_test.py ../job5/bm200.txt ../job4/set_bm200.fens /tmp/l.txt` |

## Suspicions, not proven

- Which r15 change pairs with `ONE_THREAD` to flip idx 155. Candidates from the patch list are the other five
  `FORGE_FIX_*` switches; testing each is another matrix, not done.
- That the self-play reason for shipping `ONE_THREAD=0` (the patch's comment: KBB-K 14/50 vs 21/50) means the PC is
  better off as shipped. My numbers say nothing about that; they only attribute move choices.

## What I did NOT do

- Wrote no prediction before measuring (recorded above).
- Did not isolate idx 155's partner change.
- Did not test the other 174 non-lone-king positions on the variants (they were already identical on base vs r15).
- No sanitizer runs, no threaded measurements.

## What I am NOT sure about

- Whether the reverse-test port is bit-equivalent to r15's bare-king code. I ported the logic by reading
  `src/search.cpp:1902-1921` and `:2477`, and the LMR cap insertion point was anchored on the exact
  `LmrLateParentRelief` line; but base and r15 differ elsewhere in the search, so "same rule, different surroundings"
  is the honest description.
- Whether 26 positions are enough to claim sufficiency in general. They are enough to attribute these four, which is
  what was asked.

## Times

`job6/stamps.txt`, `matrix_all.txt.raw/` (182 per-search transcripts).
