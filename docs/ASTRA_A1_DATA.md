# Astra A1: Forge training-data tools

Status: WIP. Checkpoint UTC 2026-10-30T01:55:00.175833+00:00. Branch astra-a1-data, based on e0d76ce8a6450573b503852aeca12b929bf4a17a. Engine source is unchanged from926c55f33227bc4a030d7ce5b1140528aeba75af; pinned OFF nodes312866/862329/3024920/12389307/34048354. No search change, live trainer, main or Opus branch modification. No Elo claim.

## Scope and implementation contract

1. Stream validated FPOS/FHCE files; use a matched full-FEN sidecar for faithful search. Incoming user release data-sample-10m-20261030 contains the authoritative10M pair; download/verification pending. Prior verified003–010 text heads provide12M real rows for smoke/prefix crosschecks;013 is held out. Original305M corpus/014/game IDs are not available here.
2. Offline filter: report ordered, non-overlapping removal counts and denominators for invalid/holdout/in-check/result disagreement/exact or near duplicate/teacher capture-or-promotion. Fixed-node teacher budget and all thresholds will be declared before the10M run. Near-duplicate definition will be explicit, not a claim of semantic equivalence.
3. Relabel a bounded slice with cold-state, single-thread Forge searches at configurable fixed nodes. Preserve original boards/results and generate matching current HCE values, full FEN sidecar and provenance. Reconstructed fallback must be explicit and excluded from exact-label counts.
4. Use original Python orchestration plus a standalone C++ helper linked to unchanged Forge core. No copied other-engine code. Stream with bounded memory; create only new output folders/files and preserve failures/partial outputs.
5. Deterministic standard openings export as plain UCI move sequences for exact R8source5dd3a57d6f286f09b8881671ba8a368f6d34f717. R8 cannot consume arbitraryFEN/Chess960 starts; optional no-castling960-style FENs will be clearly separate and not advertised as R8-compatible.
6. Trainer experiment plan uses actual v3b flags and teacher-fraction blend semantics; no training or data installation into the live system. Windows commands use Idle priority and explicit spare-core affinity for owned tools.

## Current verification

Read-only repository and network checks complete. GitHub connector/managed-environment status MCP are not exposed in this session; Git CLI through the configured proxy works outside tracing. Runtime cloud skill, existing coordinator/validation/engine-development skills are being reused. No provider skill editor or skill-creator has been found; skill changes will be marked proposed unless installation is actually possible.

Source recon independently verified13.5M original text rows/hashes, with12M outside013. Existing local data32 fixture is SYNTHETIC and will not be used for real removal-rate claims. FPOS stores board/STM/score/result but no castling/EP/clocks; user confirmed the new .txt preserves full FEN and matches .pos exactly. Native helper, shared format module and generator are being implemented independently; tests and all measurements are still pending.

## Next action

Fetch and verify the release assets; complete sharedI/O/native helper; run cheap correctness and a throughput pilot; then freeze the10M filter protocol and execute it. Push all code and original results about every10minutes, including unfinished work.

## Release and implementation checkpoint — 2026-10-30T02:04:56.554501+00:00

Release data-sample-10m-20261030 fetched read-only. ArchiveSHA2561d6160dd859740fe617c8dc6c6e6ad8fbcdd0ba40b59ee9cee84342f9202cca5 matches GitHubassetdigest and releasebody. Safe extraction retained originalarchive and produced FPOS1 count10000000,350000016bytes; full-FENtext645348352bytes. Row-by-row alignment and label provenance checks are pending. No measured removal fractions yet.

Added logged/bounded native-probe Python IPC and first offline filter implementation; sharedbinaryI/O, nativehelper and openinggenerator are inprogress. C++/Python correctness and real-data throughput remain unverified at this checkpoint. Dataset/binaries are outsideGit; source, exactreceipts and future raw compact evidence are committed. Initial checkpoint required gitadd--sparse due excludedvalidationpath; this is now handled explicitly.

## Implementation checkpoint — 2026-10-30T02:18:49.779886+00:00

Native helper compiled warning-free and passed 8 regression tests; source/core unchanged. Fixed helper SHA256 ad2fa25e384d71fc30bf5c22108da0336675d93a21fd9b11604964acb771c498. Shared-format tests 15/15 and filter tests 9/9 pass. First malformed error-response compile/test attempt retained, repaired before data use. Full 10M sidecar audit is running; no full-data removal or throughput results yet. Relabel/generator implementation and independent review are WIP. Blend plan is written and 7 actual trainer CLI configurations were statically checked; no training performed. Next: native pilot, freeze filter protocol, complete full10M run.

## Native data checkpoint — 2026-10-30T02:26:26.270564+00:00

Full sidecar verification PASS: all10,000,000 rows match board/STM/score/White-result and total count, input hashes unchanged. Pilot10k kept9274 (capture455,promotion2,near268,disagreement1). Full attempt1 aborted unsealed at row27772 because a1024-node search completed no iteration; original evidence retained. Added an explicit teacher_incomplete exclusion for legitimate insufficient-budget results; all other errors still abort. New helperSHA256 ddf8713016863512ffd6227c5b3f623d53a87e9964f0bbb8c94c146525d58ff3,9native tests pass. Full10M v2 running,3workers,T1/Hash1,1024nodes,known013head holdout included; output not yet accepted.

A256-position deterministic strided real slice was relabeled at65536nodes:256exact-full-FEN rows,21.189165 total pipeline CPU seconds,43493.93 positions/core-hour (Linux pilot only). Full-FEN lacks prior repetition history; exact denotes preserved current state, not game history. Original teacher budget is unknown; no label-quality or Elo claim. Results/hashes/original responses preserved. Relabel integrity10tests and IPC8tests pass after fixing reconstruction provenance and native result validation.

## Qualification checkpoint — 2026-10-30T02:37:07.289663+00:00

Fresh unchanged engine OFF pins PASS:312866/862329/3024920/12389307/34048354; startposperft5=4865609,kiwipeteperft4=4085603; fullhelper executableFMA=0. ASan/UBSan/leak checks PASS (9native tests and256real FEN comparisons); initial ptrace/sandbox failure retained and successfully rerun untraced. Newstandalonebuild reproduces the qualified helper byte-for-byte.

Openinggeneration PASS: two64-position standardbooks byte-identical;16no-castling960-styleFENs separately generated. Native replay707legalplies/787score-depth-nodechecks,0mismatches,maximumabs148cp. WindowsR8execution remainsUNVERIFIED. CPU-only unchangedtrainer smoke passed four optimizerupdates with512realtrain/512heldoutrows,trainMSE0.004578 andteacherholdoutMSE0.005856420306372456; plumbingtest only. Initialwrapper run-dir errorretained.

Full10Mv2 currently RUNNING, processed635392,kept584780; no finalfractionclaimuntilsealed. Finalreport/Windowscommands and final-manifest failurehardening inprogress.
