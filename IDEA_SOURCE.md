# Idea sources

## H256 lock — f4911f2709bd5ae7e5fca7aea30aac5d87314a05

The user supplied the h256_e12 weight include (SHA256
74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b).
Only that include changed from the specified1ab base in the lock commit.
This is a supplied parameter artifact, not external engine implementation code.

## Opt-in AVX-512 kernels and exact-byte validation

Idea: process sixteen independent hidden lanes together while retaining every
per-lane subtraction, addition, clamp, product and ordered final reduction.
Source: the user's SOL_PROMPT_both_jobs.md acceptance contract and the public
[Intel Intrinsics Guide](https://www.intel.com/content/www/us/en/docs/intrinsics-guide/index.html)
for the AVX-512F intrinsic interface. Implementation original. No external engine
source, tables, comments or licence text were imported.

The original validation tools compare actual Board/NNUE API outputs, attribute
whole-executable FMA instructions by symbol, and retain bounded exact-byte
streams with independent hashes and verified lossless compression. These ideas
come from the same user acceptance contract and existing Forge validation APIs;
implementation original. The default-OFF production executable remains identical
to the lock. Million-position and timing completion are recorded separately;
an in-progress checkpoint is not a completed acceptance result.

## ABBA bench capture

Idea: alternate OFF/ON/ON/OFF fresh processes, retain complete paired original
transcripts, and report the median ratio of internal engine bench NPS separately
from process-wall time. Source: the user's JOB1 ABBA acceptance contract.
Implementation original; no external engine or benchmark-runner code imported.
The source and executable hashes, exact sequence and stopping rule are frozen
before launch. Failed or incomplete protocols have no ratio summary.

## Generic AVX-512 accumulator copy removal

Idea: load a parent vector once, apply the recorded dirty operations in order,
then store the child once; count zero remains an exact copy. Source: the user's
JOB1 no-copy contract and the existing Forge updater. Implementation original.
The AVX2/SSE/scalar fallback remains unchanged. Validation and timing outcomes
are recorded independently; fewer source-level memory passes alone are not a
measured NPS or playing-strength improvement.

## Exact canonical-compression retention reuse

Idea: execute both actual NNUE producers again, compare their fresh raw chunks,
then retain an existing immutable compressed representation only after full
canonical decompression compares byte-for-byte with each fresh raw output and
independent hashes/counts agree. Source: the user's million-position acceptance
contract and this project's retained deterministic oracle evidence.
Implementation original. This saves validation recompression, not inference or
engine computation. Canonical bytes and permissions remain unchanged, and
failure raws remain available. Role-specific compile-define metadata also keeps
the benchmark profile explicit about optional storage alignment.

## Optional private converted-weight alignment

Idea: guarantee 64-byte alignment for private converted float w1/b1/w2 storage,
removing observed cache-line crossings without changing the public accumulator
ABI or any arithmetic. Source: the actual original allocation probe and the
public C++ aligned allocation/deallocation rules,
https://eel.is/c++draft/new.delete.array . Implementation original.
`FORGE_NNUE_ALIGN64` defaults to0 and is effective only with `FORGE_AVX512=1`.
Matching aligned operator new[]/delete[] and RAII preserve allocation semantics;
value construction preserves positive-zero initialization without a net.

## Optional completed-iteration result coherence

Idea: when a root iteration is interrupted, retain the last completed
depth/score/PV/bestmove tuple instead of replacing its PV and bestmove with an
unfinished iteration while retaining the previous score. Source: the user's
JOB2 stop-mid-iteration audit checklist and the actual cold single-thread
`go nodes 600` Forge UCI reproducer. Implementation original; no external engine
source imported. `FORGE_COMPLETE_ITERATION_ONLY=1` enables this policy; undefined
or zero preserves the legacy partial-iteration policy and lock executable.
This establishes result coherence, not superior move choice or playing strength.

## Closed search-audit evidence and continuation records

Idea: retain exact original TT, terminal, lifecycle and failed-fixture captures
with source bindings, then keep current work separate from older integration
history. Source: the user's JOB2 checklist and evidence-preservation contract.
Implementation original. The single-CPU unsuppressed TSan audit is a finite
lifecycle check, not a proof of universal race freedom or SMP scaling. No new
production behavior, external engine code or match result is introduced here.

## Combined optional-flag qualification and final evidence audit

Idea: validate the newly available combination of independent inference and
interrupted-result flags, then verify the original experiment records against
their immutable source commits and public raw Git files. Source: the user's
acceptance and publication contracts. Implementation original. The combined
profile has native correctness/sanitizer checks, not a new million-position,
performance or Elo experiment. This checkpoint preserves completed evidence;
it adds no engine behavior or external implementation.

## Final bounded-mission report

Idea: report exact qualified source revisions, negative and inconclusive results,
flag defaults, platform limits and original-evidence locations together, with
immutable public readback of the delivery. Source: the user's final-report
contract. Implementation original. This documentation and receipt commit adds
no engine behavior, strength result or binary artifact.

## Verified report publication receipt

Idea: preserve the actual HTTP status and byte comparison for all119 changed
source/report/evidence files at immutable report commit e69a7c2. Source: the
user's successful-publication requirement. Implementation original. This receipt
is a publication proof, not a new engine test, implementation or strength claim.
