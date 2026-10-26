# S48 comparability and conditional bias — 2026-10-26

The guard is standard-library only. The simulation helper reuses the exact S33
planner and S06 dependency; keep the supplied dated modules together. NumPy and
SciPy are required only when simulating.

```sh
python3 -B -m unittest -v test_forge_sol_S48_gate_guard_20261026
```

`comparability(left,right)` requires concurrency (integer1..8), exact TC, full
book/opponent SHA256 and an explicit logical-CPU list. Missing values on both
sides are unknown, not equality. Differing or one-sided Threads/Hash/options
metadata also block. Hash spelling and CPU ordering are safely normalized;
no path, mask syntax, binary identity or absent settings are inferred. This is
a bounded metadata guard, not authentication of a run or permission to rank.

`selection_bias(samples,true_elo,outcome='H1',observed_elo=None)` estimates
conditional stopped-Elo bias under an assumed true logistic Elo. It keeps H1,
H0 and cap samples separate. Non-finite selected estimates block the mean;
none are silently discarded. MC standard error/95% bounds quantify simulation
error only. `corrected_observation_ci95` remains null: the helper does not claim
a coverage-corrected gate confidence interval or an unbiased strength estimate.

`simulate_gate_bias(gate,profile=...,true_elo=...,runs=20000,seed=...)` simulates
one declared gate. A profile supplies actual five-bin counts and source
concurrency; borrowing another concurrency is rejected. Missing G104/G120
profiles return UNVERIFIED. Five bins cannot be reconstructed uniquely from
W/D/L, Elo or error bars. Default observed-point plug-in and explicit true-Elo
assumptions are separately labelled sensitivity calculations.

The published sensitivity rows reuse the original full-grid20k samples at
assumed true+10, with **cap conditioning** for capped G100r/G119. They do not
apply an H1 winner correction to a capped gate. The H1 selection demonstration
uses the separately labelled G119-shape true+10 model. No observations are pooled.

G120 conc7 versus G104 conc5 is blocked by the guard. Missing book/opponent/core
metadata also remains unknown. Actual conc8 results and actual G104/G120
corrections remain UNVERIFIED. Same fixed seed/input/layout gives deterministic
modeled output. No gate, lock, engine, PC rule or trainer is modified.

Idea sources: user S48/S33 spec, supplied unpooled profiles and classical
conditional Monte-Carlo/selection-bias mathematics; original implementation.
