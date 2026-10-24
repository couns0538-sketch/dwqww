# Portable NNUE qualification helpers

The current-source incremental patch is `oracle_windows.patch`. The required
`-p1` patch against f4911f2 is `oracle_helpers_vs_f491.patch`: both helper files
are additions because f4911f2 has no `tools/nnue_million_oracle.cpp`.
No engine source, network, trainer, match runner or search behavior is changed.

## Oracle contract

`nnue_million_oracle.exe --positions 10000 --seed 1 --wait-start`

Options may appear in any order. Positions default to 1,000,000 and stay bounded
to [1024, 4294967295]. Seed is a strict unsigned decimal UInt64, defaulting to the
original 0x243f6a8885a308d3. Duplicate options, unknown options, signed values and
overflow fail before binary output. `--wait-start` consumes one stdin line;
`start` plus LF or CRLF succeeds, another line or EOF fails before output.
Network initialization and board generation begin only after this gate. The
Windows producer retains `_setmode(_fileno(stdout), _O_BINARY)`.

The old binary format is preserved: 64-byte NMO1 header, N records of 4216 bytes
for H256, 256-byte NMOT trailer: exact stream length `4216*N + 320`. The header
stores the selected seed. With no seed argument the binary stream is unchanged.
There is no offset, skip or prior-walk rescan. Native qualification uses seeds
1 through 100, independently generating 10,000 records per seed on each producer:
1,000,000 real board records per producer. Every chunk repeats full special-move
fixtures and records actual API accumulator/evaluation output.

The original key=value stderr summary is preserved, followed by exactly one JSON
coverage line. Keys: `kind=nnue_million_oracle`, `positions`, `records`, `seed`,
`refresh`, `updates`, `parent_checks`, `inplace_checks`, `games`, `starts`,
`moves[2]`, `captures[2]`, `en_passant[2]`, `castles[2][2]`,
`quiet_promotions[2][4]`, `capture_promotions[2][4]`, `genuine_boards=true`.
All count fields are JSON numbers. Sides are white then black. Castle columns
are king then queen; promotion columns are knight, bishop, rook, queen.

A successful chunk must satisfy records=positions=refresh,
updates+starts=records, parent_checks=inplace_checks=updates, games=starts,
and every special-move counter positive. Compare all JSON fields between OFF
and ON, require zero process exit, compare exact bytes and SHA256, and require
all 100 chunks before declaring the million-record check complete.

## Phase probe

`nnue_phase_benchmark.exe --iterations 200000 --wait-start`

The same start gate precedes preparation and timing. Iterations is a strict
unsigned decimal in [1, 4294967295], default 200000. One JSON line reports
`kind=nnue_phase_benchmark`, `iterations`, `hidden_size`,
`refresh_ns_per_call`, `update_ns_per_call`, `evaluate_ns_per_call`,
`refresh_elapsed_ns`, `update_elapsed_ns`, `evaluate_elapsed_ns`, `checksum`,
`api_phase_only=true`. The deterministic 64-board corpus and warmup happen
outside timed loops. Timings are direct calls to the engine's public API.
These costs do not measure the fraction of search time spent in each phase;
whole-engine phase split remains NOT_MEASURED. No local timing supports a speed
or playing-strength claim.

## Evidence and build binding

Linux old/new producers link the same original H256 lock core at
`/workspace/forge-sol-nnue-speed-audit-20261024/build-lock/libforge_core.a`.
Before helper tests, its corresponding official engine passed d11=308972 at
2026-10-24 14:47:04 UTC; see `../lock-d11-precondition/RESULT.json`.
`verify_oracle.py` checks 1024-position old/new default identity, explicit default
seed, seeds 0/1/2/UInt64-max, body diversity, boundary parsing, start-gate blocking,
CRLF, rejected EOF/wrong commands and JSON/API/special-move invariants.
`linux-interface-result.json` records the bounded test result and stream hashes.
It is not the native one-million-position OFF/ON qualification.

Windows helpers compile against `windows-source`, whose exact bytes are listed
in `windows-source-sha256.json`. Before their first runtime test, the matching
Windows engine must pass d11=308972 with all switches OFF. Windows build success
or PE inspection does not substitute for that precondition or native execution.

## Idea source

Original local support code based on Forge's existing actual-API oracle and
public `nnue::refresh`, `nnue::update`, `nnue::evaluate` interfaces. Seeded chunks
and the stdin gate implement the supplied SOL_PROMPT_next native qualification
protocol. No external engine code, constants, tables or network changes used.
