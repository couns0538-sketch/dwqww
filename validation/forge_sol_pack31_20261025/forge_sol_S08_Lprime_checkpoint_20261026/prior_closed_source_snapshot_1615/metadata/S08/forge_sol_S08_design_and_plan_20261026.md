# S08 profiling implementation plan

**Goal:** measure real search events without changing search decisions, and retain
an OFF build whose instrumentation is removed by preprocessing.

**Architecture:** root approved one per-Searcher bank of relaxed atomic uint64
counters, one immutable per-search enable snapshot, and a nested RAII worker TLS
scope. `FORGE_PROF` defaults OFF. `Profile` is one OFF-default UCI check option in
instrumented builds. `bench_prof N` is an explicit profiling command using the
same eight fixed-depth bench positions and TT-clearing sequence as `bench N`.

**Spec:** full handoff S8 lines385–389; root's S08 task and design approval.
Private source only: `S08/Lprime`; original file01c lockderived source read-only.
No compiler, native engine, timing or Git mutation until root authorizes it.

## Counter definitions and scope

The measurement window is Worker::search entry through its return, after board
FEN loading/copying. Setup is excluded and reported as such. Missing or zero
NNUE refreshes do not prove unused code. Every worker uses the same Searcher
bank, but independent Searchers never share banks; nested scopes restore TLS.
Counter reset happens before worker launch; snapshots are taken after all
helpers join, under the same quiescent controller contract as TT clear/resize.

Nodes attach to the two actual local_nodes increments. Static-eval requests
attach to Worker::static_evaluate; HCE computations, NNUE forward passes and
NNUE refreshes attach to their actual function bodies. TT hit/miss attaches to
the probe's snapshot return. Picker counters count each executed stage case.
Razor, ProbCut, SE, IIR, LMP, quiet/capture futility, history and qs-SEE counters
record real checks and the actual search/reduction/pruning branches. Separate
checks/fires prevent a low firing percentage from hiding low opportunity count.

Each counter uses uint64 modulo arithmetic. A sticky overflow flag marks any
individual fetch_add or snapshot aggregation that wraps; wrapped output must
not be used as an accurate frequency. This is not an arbitrary infinite-run
bound. The depth/node-limited planned corpora are finite and must report their
actual maximum counters and overflow=false.

All profile lines precede the unchanged final bench summary or bestmove line.
No profile code, includes, fields, symbols or control branches survive compile
OFF. A source-level OFF projection checks unchanged noninstrumentation tokens;
it does not replace root's required executable byte-identity checks.

## Interfaces/files

- `include/forge/profile.hpp`, `src/profile.cpp`: Counter, Bank, Snapshot,
  Scope, count(), merge(), write_snapshot(). No hot-path allocation.
- `search.hpp/search.cpp`: bank/requested atomic/active snapshot, profiling
  API, worker scope, real node/TT/picker/pruning hooks.
- `nnue.cpp`, `eval.cpp`: actual refresh/forward/HCE computation hooks.
- `uci.cpp`: Profile option, explicit bench_prof, quiescent capture/output.
- `CMakeLists.txt`: OFF-default option; compile definition and new source/test
  target exist only when ON. No ISA/NNUE/arithmetic feature changes.
- `tests/prof_tests.cpp`: executable API/nested/TLS/reset/wrap/concurrency tests
  for root's later authorized compile/run.
- `test_forge_sol_S08_source_contract_20261026.py`: bounded source contracts,
  including OFF-token projection and real branch placement. No native claims.

## Tasks and validation

- [ ] Preserve original source hashes and create a <=4.1MB private Lprime copy.
- [ ] Write failing source/API contracts and C++ behavioral fixtures first;
  run source checks RED (compiler tests explicitly NOT RUN).
- [ ] Implement bank/TLS/controller lifecycle; instrument actual branches.
- [ ] Run source checks GREEN; preserve every RED/failure/source version.
- [ ] Append README/IDEA_SOURCE and produce a source-grounded counter map.
- [ ] Hand root the patch/source/tests for independent review and authorized
  native OFF whole-exe identity, five ON node references, full required tests,
  sanitizer/concurrency checks and S25 output-order regression.

## Input coverage and evidence limits

Only WAC.001–300 are available: 300 distinct legal EPD boards, canonical file
`/workspace/forge-sol-next-20261024/int16-review/wac300.epd`, SHA256
`9bfb7b42cf5bbc7f3d60ff767ca3be460e0ae4d9110ef9a71ddf0bd7071d4d46`.
Three identical copies add no coverage. A workspace/archive inventory found no
genuine STS corpus. The requested 2,000-position experiment is short by 1,700
distinct genuine WAC/STS positions; opening books/training boards are excluded.
The feature and runner must report that limit rather than padding the corpus.

Profiling uses fixed depth/node limits, fresh hash/history state per position,
and advisory event frequencies. Instrumentation overhead invalidates any
wall-time strength/speed inference; no such gain is claimed.
