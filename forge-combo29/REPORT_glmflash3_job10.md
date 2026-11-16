# glmflash3 job 10 report (2026-11-15/16)

## 1. First paragraph

**The eight-switch bundle at 80,000 nodes, pooled over Z1 and Z2: +13.9 Elo, 95 % pair interval
[+2.5, +25.4] (1400 games, 700 pairs) — above zero, next to the 20,000-node value +9.5
[−4.0, +23.1] (1,241 games, unconfirmed). The two seeds disagree badly — Z1 (seed 8201) +2.5
[−13.7, +18.7], Z2 (seed 8202) +25.4 [+9.2, +41.6], a 22.9-Elo gap between seed means — so the
pooled interval's lower bound rests on pooling away a between-seed spread the pair scores alone
do not model; read it as "the bundle is probably worth ~+10 to +14 per node at 80,000 nodes and
is not refuted", not as a firm +14. Nothing was cut: C, Z1 and Z2 all completed their prescribed
games (100/100, 700/700, 700/700); faults 0 everywhere.**

A step-0 discovery the job's known answer forced out: **the eighth switch, `MateAlphaGuard`, does
not exist in this tree's default build** — its option, its two search hooks and its setoption
handler are all behind `#if defined(FORGE_MATE_ALPHA_GUARD) && FORGE_MATE_ALPHA_GUARD`
(`src/search.cpp:110-111, 1870-1871, 1895-1896`, `src/uci.cpp:236-237, 450+`), and the CMakeLists
never defines it. The default build's all-eight bench gave **876772, not the expected 868694**;
rebuilding with `-DFORGE_MATE_ALPHA_GUARD=1` gave **exactly 868694** with all 83 options listed.
So the other helper's 20,000-node bundle was measured on a build with the define on, and every
match below runs that build (`build-mag`); the "eight switches" are eight only there. With the
switch off, that build still reproduces the three known numbers exactly (312866 / 862329 /
4865609 — `j10_magoff_*.out`), so the define changes nothing until the switch is set.

## 2. Step 0 (known numbers and the eight option lines)

Build (flags written once): the base 6b98f217 tree UNPATCHED, two builds —
`cmake -S orig -B build-orig -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++` (defaults: `-O3
-ffp-contract=off -fno-fast-math -march=x86-64-v4`, `FORGE_NNUE_HIDDEN=256`,
`FORGE_SEARCH_SPEED2=1`, `FORGE_EXPOSE_TUNABLES=1`) and the same plus
`-DCMAKE_CXX_FLAGS="-DFORGE_MATE_ALPHA_GUARD=1"` (`build-mag`, the one the matches use).
Fresh engine process per bench; Threads 1, Hash 16, OwnBook false in every input.

| build | config | command | expected | printed | match |
|---|---|---|---|---|---|
| build-orig | off | bench 11 | 312866 | 312866 | yes |
| build-orig | off | bench 13 | 862329 | 862329 | yes |
| build-orig | off | go perft 5 | 4865609 | 4865609 | yes |
| build-orig | all eight | bench 13 | 868694 | **876772** | **NO — MateAlphaGuard inert** |
| build-mag | off | bench 11 / 13 / perft 5 | 312866 / 862329 / 4865609 | same | yes |
| build-mag | all eight | bench 13 | 868694 | **868694** | **yes** |

The eight option lines as `build-mag`'s `uci` answer lists them (82 without the define, 83 with):
```
option name LmrDeeperShallower type check default false
option name ThreatHistory type check default false
option name NullThreatVerify type check default false
option name NullSeeVeto type check default false
option name ContHist4PlyRead type check default false
option name AspCappedReopen type check default false
option name NonPawnCorrection type check default false
option name MateAlphaGuard type check default false
```
(`j10_uci_list.out` — the build-orig list, 82 lines, lacks the last; the build-mag list has it.
The probe files show all eight setoption lines arriving on the candidate side.)

## 3. The matches

| match | nodes | cand | base | seed | games (complete pairs) | W-L-D | fastchess Elo ± | my Elo [95 % pair] | faults |
|---|---|---|---|---|---|---|---|---|---|
| C | 80000/40000 | none | none | 8200 | 100 / 100 (50) | 47-13-40 (fast) | +123.02 ± 45.83 | +123.0 [+78.8, +171.4] | 0 |
| Z1 | 80000 | all eight | none | 8201 | 700 / 700 (350) | 184-179-337 | +2.48 ± 16.14 | +2.5 [−13.7, +18.7] | 0 |
| Z2 | 80000 | all eight | none | 8202 | 700 / 700 (350) | 213-162-325 | +25.36 ± 16.19 | +25.4 [+9.2, +41.6] | 0 |

**Pooled Z1+Z2**: 1400 games, 700 complete pairs, W-L-D 397-341-662, score 0.5200 → **Elo +13.90,
95 % pair interval [+2.47, +25.37]** — entirely above zero, but see §1's seed-gap caveat (the
pair-score interval does not model the 22.9-Elo between-seed gap; a third seed would tell whether
Z2 was the outlier or Z1 was).

## 4. How the games ended (per match; `pgn_to_lines10.py` output, committed)

| match | total | White mates | Black mates | 3-fold | fifty-move | insufficient | stalemate | illegal/disconnect/time losses | faults |
|---|---|---|---|---|---|---|---|---|---|
| C | 100 | 33 | 27 | 29 | 3 | 7 | 1 | 0 | 0 |
| Z1 | 700 | 201 | 162 | 227 | 58 | 47 | 5 | 0 | 0 |
| Z2 | 700 | 205 | 170 | 230 | 47 | 45 | 3 | 0 | 0 |

Every game ended by mate or a draw rule; no illegal moves, no disconnects, no time losses, faults
0 — the harness is clean at 80,000 nodes.

## 5. The probes (before every match; `probe_z1.txt`, `probe_z2.txt`; C's in `probe_c10.txt`)

Each candidate side received, in order, in both games: `Threads 1`, `Hash 16`, `OwnBook false`,
then `LmrDeeperShallower true`, `ThreatHistory true`, `NullThreatVerify true`, `NullSeeVeto true`,
`ContHist4PlyRead true`, `AspCappedReopen true`, `NonPawnCorrection true`, `MateAlphaGuard true`
(all eight, seen arriving); the base side the three base options only.

## 6. Files of the repository I opened

- `src/uci.cpp` — the eight option declarations in the `uci` answer (and the `MateAlphaGuard`
  guard around its declaration at 236-237, the reason it went missing).
- `src/search.cpp` — `MateAlphaGuard`'s definition (110-111) and its two hook sites (1870-1871,
  1895-1896); the `FORGE_MATE_ALPHA_GUARD` gate in the CMakeLists (absent — checked by grep).
No engine source modified; no patch this job (NO new code, as instructed).

## 7. Stamps of every step

All UTC from `/tmp/g3job2/stamps.txt` (job 10 lines appended; committed copy). Job start (reading
file 10) ~00:49:15; budget end (60 min) 01:49:15; the 50-min stop-and-write mark 01:39:15.

| step | start | end | note |
|---|---|---|---|
| MateAlphaGuard gating discovered (grep) | 00:49:15 | 00:49:20 | before any bench (grep; no stamp — bounded by the first file mtime) |
| step-0 battery on build-orig (off + all-eight + uci list) | 00:49:20 | 00:49:23 | file mtimes of saved10/j10_off_*, j10_eight_bench13.out, j10_uci_list.out; all-eight = 876772 ≠ 868694 |
| build-mag + all-eight re-test | 00:49:25 | 00:49:33 | file mtime of j10_eight_mag_bench13.out; all-eight = 868694 ✓ |
| build-mag off-state checks | 00:49:34 | 00:49:39 | file mtimes of j10_magoff_*.out; 312866 / 862329 / 4865609 ✓ |
| chain launch | 00:49:45 | — | |
| control C (80k vs 40k) | 00:49:45 | 00:51:28 | 100/100; elapsed 103 s → rate_C80 = 0.971/s → rate_Z_est = 0.728/s |
| Z1 | 00:51:33 | 01:07:59 | full-size mode (LEFT ≥ 2×need); deadline 1051 s; completed 700/700 in 986 s |
| Z2 | 01:08:04 | 01:24:24 | deadline 1051 s; completed 700/700 in 980 s |
| pooled + report + commit + push | 01:25 | ~01:36 | before the stop mark |

## 8. What I did not do

- No third seed (the seed gap is the open question and one more 700-game match would have
  narrowed it; the budget went to the two prescribed seeds).
- No per-switch breakdown at depth (the bundle is measured whole, as the job ordered; which of
  the eight carries the 80,000-node gain is unknown — at 20,000 nodes the same question was open).
- No measurement of the switches' SPEED at depth (the PC's per-switch speed costs are known
  there; here I only know the node counts: all-eight bench 13 = 868694 vs off 862329 — the
  bundle searches ~0.7 % more nodes at the same depth).

## 9. What I am not sure about

- The 22.9-Elo seed gap is far larger than anything jobs 1-9 showed between seeds of one config
  (job 2's two seeds: 13.4/9.6; job 7's: 8.3/10.4). Either Z2 drew a lucky book sequence, or the
  bundle's effect is genuinely seed-dependent (eight switches interacting differently along
  different opening lines). The pooled +13.9 hides this; I flag it as the result's main weakness.
- The MateAlphaGuard reconstruction: I inferred "the other helper's build had the define" from
  the bench-number match (868694). I did not ASK the helper or Fable; if their build differed in
  some OTHER way that coincidentally produces 868694, my build-mag matches the number but maybe
  not their binary. The off-number agreement + the exact 868694 make the define the simplest
  explanation.
- The pooled interval assumes pair scores are iid across the two seeds; the visible seed gap says
  they are not fully pooled-compatible. A conservative reading treats the true 95 % interval as
  wider than [+2.5, +25.4] — roughly the union of the two seeds' intervals.

## 10. A better way

1. **A bundle's bench number is a build fingerprint — use it.** The 868694-vs-876772 mismatch
   found a silent build difference (an #if'd switch) in one bench run, before any match was
   spent. Rule for every bundle job: run the all-switch bench FIRST and treat a mismatch against
   the reference number as a build difference to explain before playing. It cost 15 seconds here
   and would have cost 1,400 games of ambiguity if it had been caught only in the matches.
2. **The seed-gap warning belongs IN the pooled line whenever it exceeds the pooled half-width**:
   a mechanical check (|seed1 Elo − seed2 Elo| vs the pooled interval width) would have made
   "pooled +13.9 [+2.5, +25.4], but the seeds are 22.9 apart — treat the lower bound as soft"
   the FIRST sentence instead of a §9 paragraph. The reader should never assemble the caveat
   themselves.

## 11. Model

GLM 5.3 Flash (glm-5.3-flash).

Thank you for ten jobs. glmflash3 signing off — the run ends here as instructed.
