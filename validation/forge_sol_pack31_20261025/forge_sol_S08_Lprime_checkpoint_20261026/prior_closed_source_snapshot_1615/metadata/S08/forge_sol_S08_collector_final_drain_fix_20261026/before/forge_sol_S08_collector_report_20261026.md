# S08 collector: prepared, native collection unverified

The standard-library controller and 17 pure/synthetic tests pass. This task
launched **zero native engines and zero compilers**, performed no native timing,
and changed no engine source, Git state or network resource.

`forge_sol_S08_collect_profiles_20261026.py` first runs a separate bare `bench 11`
before any UCI command and requires 308972 nodes. It then checks advertised UCI
options, sets Threads=1, Hash=16, OwnBook=false and Profile=true, collects explicit
`bench_prof 20` with terminal/profile Nodes both 11901452, and runs each corpus
position with exactly one fixed depth or node limit. Each position starts with
`ucinewgame`, Clear Hash and a readiness fence. No movetime limit is used.

The caller must provide an executable and a new output directory. Root owns
affinity, resource scheduling and authorization of actual engine execution.
Example command for a later explicitly limited WAC300 screen:

```sh
python -B forge_sol_S08_collect_profiles_20261026.py \
  --engine /absolute/path/to/instrumented/forge \
  --suite /workspace/forge-sol-next-20261024/int16-review/wac300.epd \
  --output /absolute/path/to/new-exclusive-receipt \
  --depth 8 --allow-incomplete
```

Without `--allow-incomplete`, the default 2,000-position requirement rejects the
supplied corpus before launching a process. `--required` explicitly records an
alternative caller-selected target; it does not change the handoff's 2,000
positions or satisfy that experiment. The API's smaller targets are also used
by clearly labelled synthetic protocol fixtures in the tests.

Only the canonical WAC bytes are recognized intrinsically. Additional WAC/STS
files require an explicit corpus manifest with each absolute `path`, `sha256`,
`kind` (`WAC` or `STS`) and nonempty `source` declaration under `corpora`.
Caller declarations are recorded, not independently authenticated. External
EPDs receive field syntax checks; bm legality remains unverified by this
standard-library tool. Opening/training corpora and filename-based guesses do
not count. Duplicate normalized FEN4 positions count once.

The coverage audit records the actual file/archive reconnaissance and independent
existing-library legality check: 300 genuine unique WAC positions, no supplied
STS corpus, and a 1,700-position gap. Copies, selected match openings and
training/parity boards add no WAC/STS coverage. Full 2,000-position acceptance
remains **UNVERIFIED**.

Every attempted process has separate full stdin/stdout/stderr captures, SHA256
digests and a return-code receipt. Engine identity, command-file hashes,
collector hash, Python version, corpus hashes and source-counter hash are
recorded. Existing output paths and symlink ancestors are rejected. Failures
retain completed JSONL packets and raw evidence. The bounded-capture failure
explicitly marks a retained raw prefix as incomplete; it never claims a full
capture. Operational timeout aborts broken communication rather than ending a
search as a successful time-controlled experiment.

The parser requires all 55 schema-1 counters before the terminal line, validates
denominator identities and opportunity counts, and checks main+qs=Nodes,
hits+misses=probes and the 15 picker stages=picker visits when those complete
groups are present. Overflow invalidates successful collection. Undefined
zero-opportunity and overflow frequencies remain unknown. Aggregation uses
integer numerator/opportunity totals, with separate bench and corpus tables.
Rare means an exact computed percentage below 0.1%; printed rounding does not
set the label. Such a rate is **ADVICE**, not dead-code or strength proof.

Validation evidence is retained in dated RED/GREEN logs. Initial RED: 12 missing
implementation assertions. First GREEN: 12 tests. Review RED initially included
one missing-helper AttributeError; the following RED assertion log corrected
that test shape and retained two intended failures. Additional RED caught TT
accounting acceptance and loss of the available raw prefix on capture overflow.
Final GREEN: **17 tests, OK**. Tests exercised real parsers/files and clearly
named Python protocol doubles only. Root will run the combined S08 suite.

The dated source-hash JSON pins the collector, tests, coverage audit and the
read-only core profile descriptions/header observed during this work.
