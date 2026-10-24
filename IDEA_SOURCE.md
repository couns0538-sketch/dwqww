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
