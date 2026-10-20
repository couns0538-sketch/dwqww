# Final NNUE strength audit: run 39348571407, attempt 1

**Valid completed run; inconclusive at the natural 1,024-pair cap. No strength gain accepted.** Forge 6.4.11 versus 6.4.9 finished 2,048 normal games: candidate **427 wins, 1,194 draws, 427 losses**. Pentanomial `[25, 190, 591, 196, 22]`; final native LLR **−0.76**, independently recomputed **−0.7565242360831034**. The frozen logistic SPRT tests H0=0 against H1=+5 Elo with alpha=beta=.05 and boundaries ±2.9444389791664403. Neither native acceptance message occurred; the final likelihood remains inside both boundaries. A cap result does not establish equivalence.

The immutable launch is `563bd406e9112b61f1f33f20f8ff8c07adb9b2a0`. Actual source commits are baseline `4edda780c68a742f20565d4e6a54a0c99a2c88a6` and candidate `c5cbf97a7291a3bd960c71dcd77a29bf7c95ad8e`. The original result tree is `eb1c1b7ff3b5769609cf3dd5290e29cde0912763`, retained at `origin/results/nnue-strength-39348571407-1`. Do not combine this result with the older 6.4.7 run or change the designated accepted development baseline on this evidence.

## Original archive and executable identity

The trusted `archive_results.py` from the immutable launch commit verified both physical parts, the combined ZIP, its internal/external manifests, and every payload SHA-256 and byte count. All **99 files / 1,143,208,752 uncompressed bytes** passed. Data-only extraction outside the checkout removed executable permissions and rejected unsafe/duplicate member paths and symlinks. No archived executable or downloaded helper was run.

- Complete ZIP: 130,709,760 bytes; SHA-256 `7ff0d14eb70b405b4ab3a9d4014e4fb6b9eae6636887262a7d1c6c0c676b0621`.
- Part 1: 67,108,864 bytes; `f3308fc5fd491554d1f9ccc19c1d6e7c5c2e207c6b4a283106c9abd155d86676`.
- Part 2: 63,600,896 bytes; `f523d42a88ff7e2287a72f065d435ed3eb1bc9fff00648e17b4eac70c503af0f`.
- Baseline engine: `82a385d5504733bf355dfad1ece2266c7889ef33229454e45c1f0cee4f0d2260`; core: `df734830ab22cbceeb902e27a53ebe30953eb061fec1b464bf0954dc55188ed9`.
- Candidate engine: `039a26d266bc33f26c5fcd23dcf7d140adbc5768ccf14e8403eb8204a8718dd7`; core: `9332a21a9d5ac7a974b9ba21bd85935153675bf9aba0439d166aaf964544f377`.
- Fastchess: `92253dbf94e8aafdbabcc1966273af4ae57ab07a48fa62e564d66f79811ef307`; frozen source `60d7a7a26c6b0582a15c112fb29a1829bef2adb3`.

Both original engine source TARs are byte-identical to fresh read-only `git archive` exports of their declared commits; all 67 baseline and 69 candidate exported source-file hashes match their original build records. The Fastchess source TAR is byte-identical to a Git export of its pinned source. Every archived package file, workflow, validator and protocol matches the immutable launch. The only engine/build-input changes are the two guarded NNUE update fusions and version labels; NNUE weights, fallback, search and clock logic are unchanged. The additional exported tool changes affect the update snapshot and benchmark helpers.

Original compiler metadata records GCC 14.2.0. Both sets of 13 compile commands preserve `-O3 -DNDEBUG -march=x86-64-v3 -mtune=generic -fno-fast-math -ffp-contract=off -fno-lto`; no fast-math or native-CPU substitution is present. Each original Release CTest log records **9/9 passed** and its hash matches build provenance. All **41** frozen inputs map to preserved payload bytes and agree with their expected and actual final rehash values. These are audits of the preserved original build chain; no rebuild or binary execution was performed during this audit.

## Independent operational, opening and game checks

The gross operational gate recomputes correctly from eight original fresh-process baseline bench records, including two excluded warmups: 419,798 nodes each, empty stderr, 3.325 seconds total subprocess wall time, and all original CPU/wall ratio gates passed. Baseline and candidate UCI records advertise `Ponder=false` and an empty default Book File. This gate supplies no NPS or small-speed-gain inference.

Full source-book replay passed **34,700 legal 16-ply games**, 34,700 unique positions, and 31,603 eligible strict-EP-none positions. The original official-stockfish/books ZIP and PGN hashes match the frozen provenance. All 42 historical registry hashes match, there is zero historical overlap, and the explicit 164-position confirmation cohort is excluded. The exact frozen seeded 4 A/A + 1,024 SPRT selection and separate runtime order match. Current inputs used by the repository's full opening checker are byte-identical to all 22 archived launch-package files.

A/A passed all **8 games / 4 complete color-swapped pairs / 1,076 legal plies**, with identical moves and results within every pair. Pentanomial `[0,0,4,0,0]`; it remains operational calibration only.

The SPRT used serial concurrency 1, Threads 1, equal Hash 32 MiB, Move Overhead 10 ms, OwnBook false and restart on, with native 2+0.02 clocks and no node cap, adjudication, maxmoves, resume or recovery. State, command, engine manifest, PGN headers and raw protocol agree. CPU affinity was `[0]` on an AMD EPYC 7763 hosted Linux VM. Original elapsed SPRT time **13,252.394559799 seconds** is below the invalidating 18,000-second emergency guard; the native console ends with `Finished match` after game 2,048.

Independent python-chess replay passed **284,195 legal SPRT plies**. Every recorded result is supported by its final board: 854 checkmates, 855 threefold repetitions, 125 fifty-move draws, 208 insufficient-material draws and 6 stalemates. All 1,024 pairs use unique frozen openings in exact prospective order, with swapped colors and no orphan, duplicate or interrupted pair. The original PGN, statistics, native state and all **512** native interim WDL/pentanomial reports agree. Recomputing likelihoods with a separate constrained multinomial MLE reproduces all printed reports within the frozen 0.005000001 tolerance (maximum 0.004994908772949669); every reported checkpoint lies inside the boundaries. A separate check of all 1,024 complete-pair prefixes also stays inside: minimum LLR −1.123414858552544 and maximum +0.45459095504015995. Native final state splits the middle bin as 187 win/loss pairs plus 404 double draws.

The complete **1,100,982,495-byte / 6,778,519-line** SPRT protocol log contains no warnings, errors or fatal messages. It contains 2,048 normal exit-status-zero records for each engine, 4,096 UCI handshakes and each required option setting, and 284,195 matching `go`/`bestmove` exchanges, exactly equal to the replayed plies. The complete A/A protocol log also passed. Preserved summary and final rehash show successful natural completion without an error or emergency signal; the launch wrapper also checks for surviving owned descendants before accepting successful runner exit.

## Reproduction and retained audit records

The original giant logs and binaries remain in the preserved split archive; they are not copied into plain Git files. Extraction is `/workspace/.cloud-setup/nnue-strength-final-audit-39348571407/verified/files`.

```sh
PYTHONDONTWRITEBYTECODE=1 /workspace/.cloud-setup/venv/bin/python \
  validation/nnue-strength-20261019/final-audit/audit_final.py \
  --output validation/nnue-strength-20261019/final-audit/independent-results.json
PYTHONDONTWRITEBYTECODE=1 /workspace/.cloud-setup/venv/bin/python \
  validation/nnue-strength-20261019/check_frozen_openings.py \
  --out validation/nnue-strength-20261019/final-audit/openings-independent.json
```

The first consolidated audit attempt stopped on an audit-harness PGN-format assumption: pinned Fastchess serializes untimed A/A `TimeControl` as `-`, as verified in its source. That original failed audit JSON and stderr are retained. A subsequent lifecycle diagnostic corrected the expected process count to exactly two starts per game; the pinned runner does not perform an extra engine start outside the games. These were audit-harness corrections; no original result byte changed, no engine ran, and no game was retried or removed.

Permitted interpretation: this prospective equal-clock hosted Linux comparison completed validly and did not cross either SPRT boundary. **No NNUE strength improvement is established.** No old-run pooling, NPS, native Windows/Ryzen or full-strength Stockfish claim follows.
