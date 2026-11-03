# Independent native qualification

`qualify.py` uses only the independent runtime, the external chess package, and
the frozen native executable. It does not read source datasets or training code.
The source, candidate and generated receipts have explicit identities. No large
run is authorized merely by installing or reviewing this harness.

Defaults: deterministic seed 140020261103; 1,000,000 randomized one-ply pairs;
10,000 independent complete legal-successor comparisons; 256 constructed positive
pairs at every depth 2 through 8; 256 bounded exhaustive two-ply negatives; and
separate special-move/clock/transposition fixtures. Positive paths are generated
using legal oracle moves; all native positive witnesses are independently replayed.
Negative one-ply endpoints include changed clocks, relocated pieces with valid
state, and changed results. Their oracle verdicts are independently checked.

Complete legal move sets and every successor's six-field FEN are compared before
pair qualification. Special cases cover both colors, castling followed by later
moves, en passant, promotion and captures, nonzero starting clocks with and
without resets, and equivalent endpoints from different move orders. This is
sampled behavior qualification, not proof of authentic game identity.

## Invocation

Use the owned runtime to run this script with a fresh `--out` below D:/a14.
The default candidate is `D:/a14/tools/r14_native/build/chain_native_r03.exe`,
pinned to SHA256
`f1827f44d1e10ab503aed1ac9d1fb4bacc23d8a2cc1199d78ac0aea36a6c446a`.

`--deadline-seconds` defaults to 5400; the deadline is checked between requests
and while waiting for native replies. `--cpu` defaults to 3; two 250ms samples
must average at most 70% utilization before the process pins itself to that CPU.
The allowed spare pool is CPU0 through CPU3; admission never overrides a busy CPU.
It runs Idle and creates only one native child at a time, also Idle, with GPU
devices hidden. The child inherits the single-CPU affinity. No reader thread is
created. Only owned children can be terminated after a deadline or bounded close.

The harness enforces D: >=50 GiB, C: >=30 GiB, available RAM >=8 GiB, and combined
parent/owned-child RSS <=2 GiB and shared D:/a14 storage below 5 GB at admission
and progress checks, and once per
second during a long native request. It cannot independently establish live
training/gate throughput; the supervising task must admit the run using its
fresh health evidence and stop/throttle owned work if that evidence changes.

`Native.query_many(lines)` supports one to eight requests with unique nonempty
IDs and at most 2048 total encoded bytes, including newlines. It writes only this
bounded batch before reading exactly that many replies; unexpected IDs, extra
output, truncation and deadlines fail closed. `query(line)` uses the same path.
Callers must split larger batches before calling; invalid bounds send no bytes.

Native request batches are at most 2048 bytes, responses at most one MiB, and an
individual request has a 30-second wall limit. Response IDs/counts, extra output,
child exit codes, witness validity and node bounds are checked. Any incomplete
transport or resource/deadline interruption produces UNVERIFIED, never PASS.

For a small check explicitly use `--fixture`, for example `--pairs 2000
--move-positions 100 --deep-pairs-per-depth 3 --exhaustive-negatives 4`.
These runs have `scope: qualification_smoke`, `status: UNVERIFIED`, and an
independent `smoke_status: PASS` only after all small checks complete. Their exit
code may be zero, but they cannot qualify a production scanner.

## Report contract

The final `REPORT.json` includes schema=1; status PASS, FAIL or UNVERIFIED;
`native_exe`, `native_md5`, `native_sha256`; `requested_pairs`, `resolved_pairs`,
`disagreements`, `unknown_pairs`, `per_depth`; and `complete`.

Production-helper PASS requires scope `production_helper_qualification`, at
least one million requested/resolved one-ply foundation comparisons (extra
strata cannot compensate for unresolved foundation pairs), completion of all extra
strata and required special features, zero pair and legal-set disagreements,
clean transport/exit, and the unchanged pinned executable. Native node-limit
UNKNOWNs are counted separately and never count as resolved successes. Detailed
depth/stratum counts and `deep_coverage_status` expose unresolved deep searches
even when the million resolved-comparison requirement has passed.

Non-finite deadlines are refused. A child-close failure clears completion and
smoke success as well as production success. Final publication repeats resource
admission with space reserved for the report; a hard resource stop produces a
stdout-only UNVERIFIED summary and does not allocate a report file.

Only aggregate reports, progress every 30 seconds, the first failing generated
case, and at most 100 generated unknown examples are retained. Random pairs and
hash sets are not written to disk. Original failed/small-run directories remain.
