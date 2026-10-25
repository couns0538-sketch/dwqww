# S28 read-only input audit — 20261025

This is preparation only. No patch command, application, engine build, native test, clock run, training or Git mutation was performed. The JSON companion records actual input hashes and exact old-hunk context occurrence counts. Positive context matches are not a claim that GNU patch was run.

## Reference sets and authority

The current h256_e12 lock remains unchanged. Candidate net f006 is not adopted by this kit or by a reported earlier gate result; confirmation/owner authorization is still pending. Use separate oracle maps keyed by the full net SHA256, never overwrite the current shared constants just because a candidate build completes.

|Profile|Net SHA256|Bench d11/13/16/20/22|
|---|---|---|
|Current h256_e12|74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b|308972/745494/2460422/11901452/31111774|
|Candidate e48f006|0fdf9bdb6bdf4c9f1622bcef29921912acb139fdf388e541b017a948118d4661|328459/945640/3024381/9162399/20421972|

Both use perft5 startpos4865609 and kiwipete193690690. Actual f006 input is `files/03_nets/resid_h256_e48_f006_b06_ep48.inc`, MD5 `0fae54a4c0c437432ddb5da85512b5f4`. Its shape/residual header is the same H256 format. Hashes were independently recomputed. CR source is `files/10_cr/CR_PASS_nnue_e48f006.txt`, notably checks3/5 and the summary table.

CR reports four old failure classes on f006 and WAC001 best f6h5, but does not give the exact fixed-d12 score or either promotion move/score. Its timed d13 mate result is not a d12 pin. `08_status/FORGE_KNOWN_TEST_FAILURES.md` has no f006 row. Re-record the actual values; never reuse661/642 or weaken an exact pin to a floor. A generated allowlist should be an observed candidate artifact, not an automatic edit/adoption of tests. Unexpected failure classes must remain blocking.

## Three queued patches

Paths below are under `files/`. Only the exact vs_lock variants are the requested inputs; an ep10 variant can include a network change and is not a substitute.

|Patch|Exact path|SHA256|ON / defaults|
|---|---|---|---|
|P23b|12_strength/p23b_refutlmr_h256/artifacts/p23b_refutlmr_h256_vs_lock.patch|30cdfb0923b00f5cde1803fe7d2b0deb6d3e17f5aadf14d447ef25a29c6ee7cb|RefutLmr1; default0, Plies1, MinR5|
|P27R|12_strength/p27r_nonpv_h256_v2/artifacts/p27r_nonpv_h256_v2_vs_lock.patch|55fb4525e48f562a9426a5f588474265560750ad3378e534a790ab339da85056|QsEvasionSeeNonPv1; default0, range0..300|
|timepack4|16_rebase_inputs/timepack4_f3_h256/timepack4-f3-h256_vs_lock.patch|f40b05ca0a121388c435e37fb88be45f96454e3b2e463726a8c5fb1d93d31668|TmDecisiveWinStable60; default0, range0..100|

All three hashes match the updated prompt. None touches README, IDEA_SOURCE or nnue_weights.inc. P23b touches search.hpp/search.cpp only. P27R adds CMake wiring and its test. Timepack4 adds CMake wiring and its test. The JSON lists every affected path and hunk.

Build with `FORGE_EXPOSE_TUNABLES=ON` (direct compiler `-DFORGE_EXPOSE_TUNABLES=1`) to verify the exact option name, default and range in UCI. Release builds otherwise accept these hidden tunables silently, so no rejection does not prove activation. Preserve H256 and strict FP flags. Set Threads1,Hash16,OwnBookfalse and each selected ON setting before the first search.

Apply each queued patch independently to a fresh candidate-net base copy, not cumulatively to the other queued patches. A combined stack would confound the ON count and can create unrelated conflicts. Record actual current-net controls too; do not carry old-net ON counts over as candidate-f006 oracles.

## Critical timepack distinction

Timepack4 is clock-managed-only. Its helper requires main-thread clock management, a stable completed iteration, non-mate winning score at least450, depth at least8, and a prior nonfalling score. It excludes fixed-depth/node/mate/ponder/restricted searches. Therefore all five fixed-depth ON counts should equal OFF. This is not a failed ON activation check. Set the first-differing-depth field to null/not applicable with the time-only classification. Option registration/default plus its existing pure unit tests provide structural proof; fixed-depth numbers cannot provide timed-path liveness. Its historical README labels it held/rework-ready; a compatibility run is not permission to queue/adopt it.

## Static base-compatibility findings

All old hunk contexts occur verbatim in L for all three inputs. All P23b/P27R old contexts also occur in B; P27R's CMake hunk anchors at EOF. B's extra capture-buffer test changes source line offsets. An offset with fuzz0 is not itself a rejected patch or reason to issue a renamed rebase.

Timepack4 is different: BOTH old CMake hunk contexts are absent contiguously in B. B inserts forge_bad_capture_tests between the PV test and forge_bench, and its add_test between PV/TT registrations. The timepack4 midfile hunks expect those old lines adjacent. Root must run the actual fuzz0 dry-run on an output copy. If it confirms failure, this is an existing B compatibility conflict, not a consequence of swapping the net. A minimal approved adaptation could relocate only the timepack test CMake registrations to a common EOF anchor; preserve every algorithm/helper/test byte. Do not relax fuzz or silently patch around it without evidence.

Other source paths are shared between L/B except search.cpp; the JSON includes complete hashes for the eight translation units and search.hpp. B's buffer repair must remain intact. No network include appears in any queue patch, so the net swap alone cannot explain a code hunk conflict.

## Metadata/output sequence

Dry-run is the default; no build/apply without explicit execution. Every write belongs below a newly created output directory. Never use input lock, baseline or distribution folders as scratch. Each candidate and each queue patch gets a separate subtree and explicit source/net/patch identities.

Prefer verifying/applying queued inputs before appending dated README/IDEA_SOURCE metadata. In this exact queue, document appends alone cannot conflict because no patch touches those docs. Never append generated metadata to CMake before testing its EOF-anchored P27R hunk. Preserve old document text as a byte-for-byte prefix; do not replace lock docs with the standalone timepack README/IDEA files. Generate and verify SHA256SUMS from inside each final output folder; keep raw logs losslessly encoded where old banner text cannot be delivered directly.

The kit records applicability, OFF5, ON5, first actually differing depth, observed pins and exact allowlist per independent queue item. New proposed references stay candidate metadata. A rebased patch is delivered only after a real failed fuzz0 application is captured, and only for that failure. No previous queued patch should be resubmitted merely under a new name.
