# S33 model and API — ADVICE

This tool models future hypothetical tests. It changes no gate, lock, promotion
rule, or acceptance threshold. It cannot establish a strength gain.

`true_elo` means **logistic Elo**, with mean score
`mu = 1 / (1 + 10 ** (-true_elo / 400))`. Hypothesis bounds default to **nElo**.
For paired scores `X = [0, .25, .5, .75, 1]`, the S06 convention uses
`C = 800 / ln(10)` and `nElo = C * (mean - .5) / sqrt(2 * variance)`.
Variance is the population variance of pair scores; completed pairs, rather
than individual games, supply the sample size.

The online simulation checks the S06 Gaussian LLR after every completed pair:

`N * (s1 - s0) * (2 * mean - s0 - s1) / (2 * variance)`.

For nElo hypotheses, `si = .5 + (ei / C) * sqrt(2 * variance)`, recomputed from
each path prefix. A zero-variance prefix has no available LLR and cannot cross.
The final pair at the cap is checked before an uncrossed path becomes `cap`.
Wald bounds are `log(beta/(1-alpha))` and `log((1-beta)/alpha)`.

This LLR is an **approximation**, not native fastchess's exact arbitrary-profile
GSPRT. The original S06 module is an explicit dependency at
`../S06/forge_sol_S06_statistics_20261026.py`, and is used directly for QA
fixture checks. A standalone packet selects an adjacent copy of that frozen
file first, then falls back to `../S06`; both locations require the original
SHA256 `4598c5839519af2ed4680b074669d097b9616dfe7c03c1afb7622b276efecb8a`.
Its frozen hash and original release hash match in the protocol manifest.
Supplied Gaussian LLR fixtures reproduce G95 -0.56, G100r 2.22 and
G119 1.72 within 0.02. Native G104 counts are absent: illustrative synthetic
counts `[0, 44, 219, 75, 11]` sum to 349 pairs/698 games and produce Gaussian
LLR 2.948544; they are **UNVERIFIED**, are not recovered observations, and do
not establish which counts produced G104's native LLR.

The three empirical pair profiles remain separate. The supplied 13:35 CSV
identifies G95, G100r and G119 as concurrency 5. No measured concurrency 7/8
profile is available here; independent draw models are hypothetical and have
no measured concurrency. No observations, gates, or concurrency regimes are
pooled.

Exponential tilting sets `p_i(theta) proportional to p_i * exp(theta * X_i)`
to reach the true logistic score. Absent bins remain absent and multiplicative
pentanomial shape ratios remain constant. Individual-game W/D/L and Pearson
correlation cannot be identified from the five bins; preservation of those
quantities is not claimed. Draw-ratio inputs use an independent two-game
model with fixed per-game draws `D`, wins `mu-D/2` and losses `1-mu-D/2`.
Unreachable target scores and infeasible hypothesis scores fail closed.

The analytic OC/ASN calculation uses Brownian absorption with drift and
diffusion derived by the delta method for the *online empirical-variance*
statistic, including variance-estimation fluctuations. Image-series
first-passage CDFs give finite-horizon H1/H0 probabilities and remaining cap
mass. Integrating survival gives mean games; its 0.5 crossing gives median
games, retaining the atom at the cap. Continuous monitoring omits discrete-pair
overshoot and early-sample effects. The source records the formulas; all are
original mathematical implementations, with no copied engine code.

Six cells were declared before inspecting MC. Each used 20,000 runs and fixed
seed `202610263300 + cell_index`. All three absolute outcome differences must
be at most 0.03 for every cell. All six passed; the largest observed difference
was 0.0078305063. Full summaries, integer outcome counts, terminal samples,
seeds, sampling layouts, source hash, commands and return code are retained.
For G119 true +9.5 under [0,10] nElo/1500 games, MC cap probability was 0.8177
(16,354/20,000), versus analytic 0.812163. These are model outputs.

Public entry points:

- `tilted_profile(weights, true_elo)` and `draw_profile(draw_ratio, true_elo)`
  return five NumPy probabilities.
- `named_profile(name, true_elo)` selects one of the six separate profiles.
- `simulate_cell(profile, true_elo, e0=0, e1=10, cap_games=1500, *, runs=20000,
  seed=..., units='nelo', return_samples=False)` returns outcome probabilities,
  Wilson intervals, mean/median games, mean-game standard error and full
  reproduction metadata.
- `simulate_protocols(profile, true_elo, protocols, ...)` shares modeled paths
  across protocol alternatives. Exact replay requires the recorded protocol
  set, block size, maximum pair horizon, seed, NumPy version and input vector.
  Sharing random paths is a variance-reduction device, not gate pooling.
- `return_samples=True` adds NumPy arrays `outcome` (`H1`, `H0`, `cap`), `games`
  and `terminal_elo` (logistic). Boundary scores have infinite raw Elo and must
  be reported separately. Summaries remain finite JSON.
- `analytic_cell(...)` returns the finite-cap Brownian approximation;
  `brownian_finite_cap(...)` exposes its deterministic mathematical kernel.

For stopping-bias analysis, condition on the requested terminal set. In
particular, H1 stopping bias uses only `samples['outcome'] == 'H1'`. Including
all capped paths estimates a different quantity and is not an H1 bias estimate.

Bounded checks run with `python -B -m unittest discover -s tests -v` (23 tests).
CLI actions require `--output-dir` naming a new directory; existing output
paths and symlink ancestors are refused, and result files use exclusive create.
The original six-cell execution is preserved in
`forge_sol_S33_run_frozen_validation_20261026.py` with its original b04 source
binding and a byte-exact source snapshot. It is historical execution evidence.
The final source changes only the CLI and S06 dependency lookup/hash metadata.
`forge_sol_S33_numerical_ast_equivalence_20261026.json` proves exact equality
of every remaining AST node, including all 24 non-CLI functions, constants and
RNG code. The six receipts therefore apply to the unchanged numerical model;
no Monte-Carlo run was repeated for those packaging corrections.
`--full-grid` is an explicit 630-cell action and requires at least 20,000 runs
per cell. Its table is an advisory planning dataset, not a gate decision.
