# T12-02-nps-protocol: nps protocol that resolves 1 % at 2-5 % A/A noise
Status: COMPLETE

## Source
https://llvm.org/docs/Benchmarking.html (SMT pair off, boost/frequency scaling off, ASLR off, reserved cores, repeat
runs; "low noise is required, but not sufficient. It does not exclude measurement bias", pointing to Mytkowicz et al.,
ASPLOS 2009). https://learn.microsoft.com/windows-hardware/customize/power-settings/options-for-perf-state-engine-perfboostmode
(PERFBOOSTMODE index 0 = Disabled). Fishtest wiki Creating-my-first-test (speed-ups: several bench runs, mean + sd,
target ~0.5 %; "1 % speedups pass with an 85 % chance"). Own: forge-ltopgo-pgo / forge-opus-tools / forge-engine-verify.

## Licence
LLVM docs (llvm-project f7d11195ab, Apache-2.0 WITH LLVM-exception), Microsoft docs and fishtest wiki: ideas only, no
code involved. Protocol and numbers below are own.

## Mechanism
Two error kinds. (1) Random run-to-run noise (load, boost, temperature): falls as 1/sqrt(pairs); palindromic ABBA
cancels linear drift. (2) A fixed per-file bias: one exe vs its own byte copy read -3.0 % at d16 (R12). It does not
shrink with more pairs of the same two files. Probable cause (UNPROVEN): each file keeps its cached physical pages
and its per-boot ASLR image base, so cache and branch-predictor aliasing is fixed per file. Fix: a fresh byte copy per
run, so the bias becomes random noise that the pairs average out, plus an A/A arm (copy vs copy) as the control.

## Forge fit
Tools exist: abba.py (ABBA slots, --identity, Student-t CI on log ratios), r12_speed.py (palindromic blocks, A/A
copies, bootstrap lower bound), nps_opts_ab.py (bench-window CPU time). Missing: copy-per-run, a power-based run count,
boost/temperature logging per run. Measured noise: A/A -0.02 % [-2.24, +2.25] on the loaded PC (forge-engine-verify).
The 9850X3D has one CCD: logical CPUs 2k and 2k+1 share a core (CPUs 2-3 = one core, forge-opus-tools).

## Expected gain
Source: LLVM expects "variations of less than 0.1%" with all its controls (Linux); fishtest: "about 0.25 % speedup at
STC ... for a 50 % passing chance", "1 % speedups pass with an 85 % chance" (STC/LTC SPRT, bounds not stated there).
No Elo claim. Required ABBA pairs for a 1 % effect (one-sided 95 %, power 90 %): n = 8.6 x s^2, s = per-pair sd of
the log ratio in %: s 2 % -> 35 pairs, 3 % -> 78, 5 % -> 215; bench 16 is ~2-3 s per run, so 215 pairs ~25 min.
Forge estimate: with copy-per-run the 1 % call is decidable in < 30 min of one core - **UNPROVEN** (s not yet measured
under copy-per-run).

## Effort
Crew ~2 h: add --fresh-copy-per-run and --power-n to abba.py (or r12_speed.py), log PERFBOOSTMODE, clock and
temperature per run (HWiNFO log). CPU: one physical core for 10-30 min per comparison. Disk: copies kept (no deletes),
~2 MB each, ~1 GB per 400-run study on F:.

## Test plan
Protocol (PROTOCOLS.md section 5): identity first (T12-03), then a pilot of 20 pairs to measure s, then n pairs by
the formula; arms A, B and A' (fresh copies of A) in palindromic order; pin to ONE logical CPU of a core whose SMT
sibling is idle; Idle/BelowNormal; no gate on that core; boost state fixed and recorded. Accept "B faster" only if
the A/A CI contains 0 and the B/A one-sided 95 % lower bound is > 0; keep it only if the point estimate is >= 1 %
(to also prove ">= 0.5 %" needs 4x the pairs). Route:
node-identical speed changes = nps ABBA only; everything else = UHO SPRT at STC (T12-01).

## OFF-by-default design
Measurement tooling only; no engine change. New tool flags default off, so old runs reproduce; lock pins
312866/862329/3024920/12389307/34048354 untouched.
