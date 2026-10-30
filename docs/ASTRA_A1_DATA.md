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
