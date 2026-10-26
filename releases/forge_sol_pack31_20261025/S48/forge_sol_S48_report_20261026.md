# Forge S48 development report — 2026-10-26

Implemented the comparability guard and conditional simulation diagnostics.
The accepted engine is unchanged. No actual match or Elo-gain claim.

|Check|Verdict|Evidence|
|---|---|---|
|Unit/API tests|PASS|16 tests; actual small synthetic simulation path included|
|Independent final guard review|PASS|15 non-MC tests plus three old/new regression probes|
|G120conc7 vs G104conc5 guard|PASS|Concurrency mismatch and missing provenance block comparison|
|H1-stopped upward-bias demonstration|PASS|True+10 model:4,247 H1 trials average+18.167438|
|Seed/layout reproducibility|PASS|Frozen S33 protocols and original samples; no selection reroll|
|Original sample reconciliation|PASS|All1,890 H1/H0/cap sets independently recounted|
|Actual G104/G120 corrected Elo|UNVERIFIED|No actual paired profiles; no substitution|
|Actual conc8 correction|UNVERIFIED|No actual conc8 observations supplied|
|Coverage-corrected observational CI|UNVERIFIED|MC precision is not gate/selection uncertainty|

Under the G119-shape true+10 model, H1-stopped estimates average+18.167438:
bias+8.167438, Monte-Carlo95% interval[8.059960,8.274917]. This is a model
selection effect, not a measured engine gain or an estimate of G104's true Elo.

|Gate|Observed source Elo|Condition|Assumed true Elo|Model-adjusted sensitivity|MC-only95% interval|
|---|---:|---|---:|---:|---|
|G100r,conc5|+10.89|cap|+10|+12.648465|[12.597286,12.699644]|
|G119,conc5|+9.50|cap|+10|+11.119115|[11.064946,11.173284]|
|G104,conc5|+29.44|H1|unknown|UNVERIFIED|Actual profile missing|
|G120,conc7|+23.62|H1|unknown|UNVERIFIED|Actual profile missing|

These are explicitly assumption-dependent sensitivity points. The original
reported G100r/G119 errors ±8.38/±8.84 are preserved in the JSON; they are not
replaced by the much narrower Monte-Carlo intervals. No corrected observational
confidence interval is established. Capped observations are conditioned on cap,
not on H1. The five-bin profiles are separate; no seeds or concurrency are pooled.

The comparison guard refuses to rank gates with different concurrency, TC,
book, opponent hash or core mask. Missing current PC metadata remains unknown,
even if equally absent. Actual G104/G120 raw evidence must be supplied to run
their correction; no hypothetical pair counts are used as real profiles.

All code, tests, failures and original modeled samples are retained with exact
source and dependency hashes. S48 source is
21713b327007b0cda450200e172f6affb27cd65ac10e26ed8680d9447669d855.
The shared original sample archive is published with S33; its independent audit
reconciles every terminal record. Local skill maintenance is documented in S33;
no duplicate/new/global skill was installed. Continue S07 and the remaining
finite job queue; this add-on does not complete the whole pack.
