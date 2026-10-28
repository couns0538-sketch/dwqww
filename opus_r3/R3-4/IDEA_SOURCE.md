# R3-4 idea sources

- **Spec:** the user's R3 pack, job R3-4 (verbatim in the agent brief): an offline SPSA tuner (Python,
  fastchess-compatible, `opus_spsa*.py`), the 20 most important search constants (LMR, null move, RFP, futility,
  SEE margins, aspiration) as UCI options with identical defaults, a dry-run self-test at a very short time
  control with at most 2 threads, no real tuning session.
- **SPSA:** J. C. Spall's simultaneous perturbation stochastic approximation: gains a_k = a/(A+k+1)^alpha,
  c_k = c/(k+1)^gamma with the practical alpha = 0.602, gamma = 0.101 and A about 10% of the iterations.
- **Chess-engine practice (concepts only, no code copied):** fishtest's SPSA form, a per-parameter c_end and
  r_end with c = c_end·N^gamma, a_end = r_end·c_end², a = a_end·(A+N)^alpha, the update R·c·(W-L)·flip with
  R = a_k/c_k², game pairs with reversed colours, randomized rounding of integer parameters; r_end = 0.002 as the
  usual end learning rate.
- **Forge inputs:**
  - `opus-sol-SA6` (S-A6 plan): parameter groups, c_end heuristics (5-10% of the default), the 8+0.08 time
    control, the 29 s per game per slot throughput of the PC gates and the game-time model, the validation path
    (STC gate, LTC confirm), the harness needs (Spall schedule with A, per-parameter c_end, resumable state).
  - `opus-sol-S15` (harness v2): fastchess refuses or drops options an engine does not advertise (probe C), the
    exposed build re-advertises the current value (application proof), `-maxmoves` makes adjudicated draws,
    Idle priority for side runs, fastchess 1.8.2 at `C:/Users/Administrator/grok-pc/tools/fastchess/`.
  - `src/search/tune.inc` / `forge/search_tune.hpp` (the ~55 tunables, unlisted unless FORGE_EXPOSE_TUNABLES),
    `src/uci.cpp` (setoption of tunables), `src/search/alphabeta.inc` (the null-move literal), O3's note that
    globals defined before the AL1 block keep the AL1 addresses, S29's `codegen_compare.sh` and `nps_ab.py`.
- **New here:** the bench-node sensitivity scan as a liveness check of each candidate, the finding that
  `QsSeeMargin` is constant over 0-99 (SEE balances are multiples of 100), the fastchess `-strict` finding (one
  time forfeit stops the run), the set-and-reread preflight instead of `-strict`, the job-object kill of the whole
  fastchess tree on timeout.
