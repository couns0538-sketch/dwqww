# REPORT glmflash5 — JOB 4 — STOPPED AT STEP 0: the bundle-8 number is a finding

Branch `cursor/glmflash5-work-cb5c`, build of commit 6b98f2170a3210e71beed04bbd2553972c253ed7 as
in jobs 1–3. times: see stamps.txt (and its honesty note: this agent stamped too late — the job's
steps ran back to back and only their boundaries are stamped).

## 1. What was asked, the answer, how sure

Asked: step 0 = `bench 13` with the eight standing-job switches on (expected 868694), then the
FIRST real-clock look at TmNodeShare (new openings, probe, one match cut at minute 45).

Answer: **step 0 gave 876772, NOT 868694 — a finding, and the job is stopped at step 0 as the
job text instructs. The cause is diagnosed to file-and-line and the expected number is
REPRODUCED exactly on the corrected build: 868694.** M2 was not played; no openings file was
built (nothing to attach it to until Fable rules on the build question).

How sure: sure of the diagnosis (below has the exact command, the engine's own "unknown option"
line, the source lines, and the exact reproduction). What needs Fable's ruling: which build the
session standardizes on for matches (default vs guard-enabled), because standing jobs S2 and S4
both need MateAlphaGuard.

## 2. The finding, with its full chain (all raw files in tests_glmflash5_job4/)

1. **Default build** (the one of jobs 1–3; plain `cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++`):
   bench 13 with all eight `setoption ... value true` lines → **876772**, and the FIRST line of
   the engine's own output is `info string unknown option MateAlphaGuard`
   (`step0_bundle8_b13.txt`). Only 7 switches were on; the eighth was silently refused.
2. **Why**: the option exists in the source but is compile-time gated —
   - `src/uci.cpp:236-239`: the option is ADVERTISED only `#if defined(FORGE_MATE_ALPHA_GUARD) && FORGE_MATE_ALPHA_GUARD`;
   - `src/uci.cpp:450-460`: the setoption HANDLER sits behind the same `#if` — without the
     define, `setoption name MateAlphaGuard` prints "unknown option" and nothing changes;
   - `src/search.cpp:111`: `bool MateAlphaGuard = false;` — default off.
   - The repo's own logs agree on how the owner's PC builds it:
     `tests_astra_mateguard/logs/guard-enabled-configure.metadata.txt:19`:
     `"-DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1"`.
   - CMakeLists exposes NO cmake option for it; it goes through CMAKE_CXX_FLAGS.
3. **Reproduction**: rebuilt with `-DCMAKE_CXX_FLAGS="-DFORGE_MATE_ALPHA_GUARD=1"` (same
   everything else), same eight setoption lines → bench 13 = **868694**, deepseek3's number
   EXACTLY (`step0_bundle8_guard_b13.txt`); the option is now in the `uci` list (count 1).
4. **Base behaviour unchanged by the flag**: the guard build with NO options gives bench 13 =
   **862329** — the session's base number (`step0_guardbuild_base_b13.txt`). With MateAlphaGuard
   off, the guard build searches like the default build (at least in this bench position); the
   flag only exposes the option. So my jobs 1–3 results are not invalidated by this — but that
   inference is from bench positions only, not from games; games are Fable's to weigh.

Also step 0 as the job asked: `bench 11` with **TmNodeShare=true** = **312866** — UNCHANGED from
the base number (`liveness_TNS_b11.txt`). Expected per kimi5's model: the switch acts only in
clock play (search.cpp:2577-2590 replaces the effort rule; it is read inside the time-management
path, which a fixed-depth bench never enters) — so "no change in bench" is the model's
prediction, and the observation matches it. TmNodeShare liveness therefore remains UNPROVEN by
bench and must come from the probe + match, which are not played yet.

## 3. What this blocks (for Fable to rule on)

- **S2 standing job**: its own gate says do NOT play it if bench-13-with-all-eight differs from
  868694. On my default build it differs BECAUSE the eighth option cannot exist there. If the
  session standard becomes the guard-enabled build, S2 becomes playable again (its gate number
  reproduces).
- **S4 standing job**: uses MateAlphaGuard=true on one side — impossible on the default build
  (silent refusal → the "both sides get the pair" design would silently compare wrong things;
  the probe would catch it, but there is nothing to probe).
- My jobs 1–3 and deepseek5's runs are untouched by the flag question (no MateAlphaGuard
  anywhere in them).

## 4. Losses on time by side, and where the switched side spent its time

Not applicable — no match was played. (Job 2's standing answer on this machine: 0 losses on
time in 986 clocked games; job 3 added 833 more, still 0.)

## 5. From my partners

- deepseek5 (NOTES after its job 3): movetime reserve = `Move Overhead` exactly; 0 of 3,600
  direct searches and 0 of 996 fast-clock games overstepped; "no wtime safety patch is needed on
  this build". Nothing of mine changes because of it; my tc=2+0.02 sits far inside its proven
  safety region (its 0.1+0.001 games had no loss on time).
- kimi5 (NOTES): its model says both time switches act only in clock play (search.cpp:2395-2399,
  2586-2590) and that TmNodeShare REPLACES the effort rule (forced to 1) rather than adding to
  it — this is the prediction my unrun M2 would check, and the bench-11-invariance I report above
  agrees with the model's claim about where the switch lives.
- Cross-check: the only number of mine another colleague has already covered is the base bench
  (deepseek5 + me: identical). Nothing else was comparable this job (no partner number for the
  bundle-8 bench was published besides deepseek3's 868694, which I reproduce).

## 6. What I did NOT do

- No `openings_job4.epd` (the job's step 1 sits behind the step-0 gate in the job's own order;
  building it while stopping would waste nothing, but committing a file whose match may be
  re-ruled seemed wrong — say if you want it built anyway next job).
- No probe, no M2 match, no per-move-time buckets (nothing to measure).
- No rebuild was committed as a patch (rules: engine changes are committed as text patches, and
  this is not an engine change — it is a build-flag discovery; the CMake invocation is recorded
  in the report text and stamps).

## 7. What I am NOT sure about

- Whether "with the flag off the two builds are identical in GAMES" — my evidence is one bench
  position; the r4 acceptance criterion in the repo's own logs demanded byte-for-byte equality
  with the switch off, and the owner's PC presumably enforces it, but I did not test equality
  myself.
- Whether deepseek3's 868694 build had OTHER flags beside FORGE_MATE_ALPHA_GUARD that could also
  matter to node counts; my guard build reproduces 868694 with the flag ALONE, which is strong
  but not proof that it is the whole story for every option combination.
- The exact `date -u` boundary between my step-0 sub-steps (stamps.txt records the gap honestly).

## 8. A better way

- CMake should own this flag: `option(FORGE_MATE_ALPHA_GUARD ...)` with a default, so a build
  never silently lacks an option that job files name. One-line change in CMakeLists.txt (kimi5's
  territory; I write this as a suggestion, not a patch).
- Every job whose step 0 names an option should FIRST grep the `uci` list for all its names —
  one command, and the "unknown option" fault (which here wasted nothing only because the
  mismatch was visible in node counts) becomes impossible. I will do this before every match
  from now on.

## 9. UTC stamps

times: see stamps.txt in this folder (includes its own honesty note about the stamping gap).

## 10. Model name

glmflash5 (GLM, flash tier) — cloud agent apprentice to Fable, paired with deepseek5 and kimi5.
