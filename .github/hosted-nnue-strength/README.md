# Bounded hosted Linux NNUE strength test

Status: **PREREGISTERED_REVIEWED_READY_FOR_SINGLE_PUSH**. Frozen candidate6.4.11 source is`c5cbf97a7291a3bd960c71dcd77a29bf7c95ad8e`.
The final source correctness gates and independent review are recorded in
protocol, with exact proof-file hashes. Preparation and
mocked safety checks provide no playing-strength or host-readiness evidence.

This prospective comparison is Forge6.4.11 against6.4.9
`4edda780c68a742f20565d4e6a54a0c99a2c88a6`: the combined two-change and three-change
NNUE update fusion, with original float operations, weights, fallback, search,
evaluation and time constants preserved. The actual source commit is frozen in protocol/workflow. Release9/9 and both
actual-core differential gold streams, ASan9/9+instrumentedstream, Windows8Winechecks
and independentartifactaudit pass. No Elo gain is accepted yet.

Both sources build serially with GCC14, genericx86-64-v3, identical strict flags,
`-ffp-contract=off`, no fast-math or LTO, and full CTest. Source exports,
compile commands/cache, full test logs, actual engine/core and pinned
Fastchess`60d7a7a26c6b0582a15c112fb29a1829bef2adb3` bytes are retained before timing.
Matches execute the archived binaries. Source exports and build provenance are
frozen and rehashed alongside every package/runtime input.

The original gross operational A/A gate uses2excluded fresh-process bench11
warmups then3baseline/baseline pairs,419798nodes each,30seconds total, CPU and
external-wall median ratios0.95..1.05 and all ratios0.85..1.15. Failure stops
before games; there is no retry. Then4normal identical deterministic
color-swapped baseline A/A pairs use10000nodes/move withtc=inf. Neither gate
measures a3%speed difference or provides Elo evidence. The separate strict3%
hosted performance experiment failed its A/A gate, ran no A/B, remains failed
and retained, and receives no retry or widened threshold. This new protocol
answers the separately preregistered equal-clock strength question on a fresh
host with the existing gross operational gate.

One uninterrupted serial native logistic SPRT tests H0=0/H1=+5Elo,
alpha=beta=.05, equal2+0.02, Threads1, Hash32, MoveOverhead10, OwnBookfalse,
restarton. Ponderfalse and empty Book File defaults are verified by runtime
handshakes; no Book File option is sent. There is no adjudication or maxmoves,
even in A/A. Natural stopping is a native boundary or1024complete
pairs/2048games. A300minute emergency deadline invalidates acceptance and
preserves failures. There is no48-pair screen, reset, resume, retry, pooling,
trimming or outcome filter. A cap without boundary is inconclusive. H1 provides
conditional evidence against H0, not proof of a minimum+5Elo gain.

The unchanged4A/A and1024SPRT opening pools come from the original
[official-stockfish/books](https://github.com/official-stockfish/books)
`8moves_v3.pgn.zip`, commit`a804a97e709f40aa75a00f9d19e84915b7a3a45c`, archive
SHA256`7e1e9dd118b4bb97d8a8b5b8a790c86e21f8509d59a27d2883767d94477be02e`.
Original archive, upstream CC0 license/README/metadata, legal replay script,
full research report and historical registry hashes are in`provenance/`.
All34700games were legally replayed16plies;31603unique final positions already
have strictEP='-'. Actual final EP positions are excluded without normalization.
Zero overlap was found across42prior registries, unused frozen tails and the
explicit new164confirmation cohort. The selector string seed is
`20261019-official-stockfish-8moves-v3-long-strength-v1`; first4A/A and next1024
SPRT rows are reserved together. Runtime CLI seed20261021 reranks only each
unchanged reserved pool. The exact runtime order is separately frozen in
`provenance/runtime-order.json` and matching runtimeEPDs. A/A never overlaps
SPRT. This source is Stockfish2013self-play, with no balanced or representative
human-opening-distribution claim. No old147/current647-versus644 games are reused.

Engine communication logging uses pinned Fastchesslevel=warn engine=true for
both sides, retaining its equal logging I/O overhead as part of these conditions.
The live scanner reads appended bytes and incomplete-line tails. Any warning,
error, non-normal game, crash, timeout, illegal move, orphan pair/owned process,
changed input or observed output deletion/replacement/truncation forbids
acceptance. The independent audit requires normal unique paired games, exact
opening prefix/full selection, native pentanomial agreement, exactly one native
acceptance for a decision and a finite final LLR matching an independent0/+5
likelihood. Final input rehash runs in`finally`, including fault/signal/deadline.
Only owned process groups are stopped; every raw byte is retained.

GitHububuntu24.04 job/build/match limits are330/6/310minutes. The workflow fires
only on push to`forge/hosted-nnue-strength-20261019-*`, attempt1, with no schedule,
dispatch or retry. This is one automated bounded strength test that may continue
independently of chat; it does not promise24hours of continuous agent work or a
6hour chat scheduler. Native hosted Linux evidence does not establish Windows,
Ryzen or Stockfish superiority. Platform hard loss can prevent cleanup.

Raw results always upload as an artifact. Every original source/binary/PGN/log
is also ZIP-archived outside the input tree with per-file SHA256 and sizes.
Any ZIP above64MiB becomes fixed64MiBbyteparts plus whole-archive/part SHA
manifest, so a raw engine log aboveGit100MiB remains fully preserved. The
archiver verifies streamed part reassembly and every ZIP payload before success.
The new`results/nnue-strength-RUNID-ATTEMPT` branch contains these archives and
manifests and cannot retrigger the launch workflow. Raw PGNs are never rebuilt.
Reassemble split archives in manifest order, verify whole SHA256, then extract;
`archive_results.py` exposes`verify_archive(manifest_path)` for full verification.

Preparation checks run without engines:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B validation/nnue-strength-20261019/test_hosted_nnue_strength.py
PYTHONDONTWRITEBYTECODE=1 python3 -B validation/nnue-strength-20261019/test_archive_results.py -v
```
