# Sol report — 2026-10-24

Both bounded jobs are complete. All engine changes are isolated and optional; no integration branch was changed. This report records verified finite checks and remaining limits.

The three optional NNUE candidates preserve the tested accumulator bits, evaluations and deterministic search results. These cloud measurements establish no reliable quantified speed improvement or Elo gain. All optional inference flags remain off by default.

Branch: `forge/sol-nnue-speed-audit-20261024`. Engine implementation: `706da4421be204c201fa5615fee298ab44c9d09b`. Branch HEAD before this report: `97469f3326a7ba7fd074d53aa13c12c667b712df`. The delivery commit containing this report is printed after publication. Base: `1ab50b2dd64d9b2f752f7f1285f6968cad2fd792`; lock: `f4911f2709bd5ae7e5fca7aea30aac5d87314a05`. Network SHA256: `74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b`.

## Commits

- `f4911f2709bd5ae7e5fca7aea30aac5d87314a05` — H256 lock network; no experiment flag.
- `7e4c22a300dea7ae89313d4135184a4e6883029a` — AVX-512 kernels, `FORGE_AVX512=1`, default 0.
- `a57a84771495ee60e580fc67abb026ebac8f2eb8` — stage 1 exactness and ABBA evidence.
- `bf237d2cc0b59facf8fe420cbd8408b84913bd7a` — generic no-copy update under `FORGE_AVX512=1`.
- `b8ebc4ca030d3a534d2b28ca1d7267808c5c14c6` — exact oracle retention workflow and existing SIMD skill reference.
- `7716853d7a4bcf1422afaa5a7fe678cafbf69f9e` — private weight alignment, `FORGE_NNUE_ALIGN64=1`, default 0 and effective only with AVX-512 enabled.
- `76298789a5932f4933262ec75f3001cbc90ca5ec` — closed stage 2/3 and workflow evidence.
- `706da4421be204c201fa5615fee298ab44c9d09b` — interrupted-result guard and native regressions, `FORGE_COMPLETE_ITERATION_ONLY=1`, default 0.
- `a5670fab004ca694fbad34a702b759bcf084eeb5` — TT/lifecycle audit originals and continuation documents.
- `97469f3326a7ba7fd074d53aa13c12c667b712df` — combined-flag compatibility, independent evidence audit and publication receipts.
- This report and final delivery receipt are published next; the actual delivery SHA accompanies the printed report.

## JOB 1

Native Linux host: Intel Xeon Platinum 8573C cloud VM, AVX-512F available, four-CPU quota; timed searches pinned to CPU 4. Compiler: GCC 14.2.0, the available substitute for requested 15.2. Build flags: `-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -static -pthread -Iinclude`, with the stated experiment definitions. No Ryzen/Windows speed result is claimed.

Stage 1 adds refresh/update/evaluate AVX-512 kernels, retaining sixteen ordered output sums and pointer-selected output weights/bias. Stage 2 removes generic update copy/intermediate passes while preserving recorded dirty-operation order, count-zero copying and in-place semantics. Stage 3 aligns private converted weights to 64 bytes; public accumulator ABI remains alignment 32/size 2080. No quantized inference, FMA, net/trainer changes or crew implementation was imported.

Each OFF executable is byte-identical to the official lock, SHA256 `d90f5060880c799ef8cdfd41bbef3668610a08619c9edaa266452f1bc656c47f`. ON hashes:

- Stage 1: `220de80544d27e566013b682d00ab213c3b3416c36d833d71aea811bad78f6d6`.
- Stage 2: `f964adf97c596d0b6662c57c903d6e018f2ed28f8d128d0056cf01e36fc5b83c`.
- Stage 3: `d7c9b37e53b6100cc68ead3c0833100560dbfbea23f65d6d6932059ab1f3e0bd`.

All five deterministic benchmarks match:

| Depth | OFF | Stage 1 ON | Stage 2 ON | Stage 3 ON |
|---:|---:|---:|---:|---:|
| 11 | 308972 | 308972 | 308972 | 308972 |
| 13 | 745494 | 745494 | 745494 | 745494 |
| 16 | 2460422 | 2460422 | 2460422 | 2460422 |
| 20 | 11901452 | 11901452 | 11901452 | 11901452 |
| 22 | 31111774 | 31111774 | 31111774 | 31111774 |

Startpos perft5 is 4865609 for OFF and every ON candidate. Kiwipete perft5 is 193690690 for stage 1 OFF/ON; this was not repeated for later stages.

Release CTest is 13/14, with only `forge_tests` failing and precisely these unchanged lines:

```text
FAIL: WAC 001 expected g3g6 got f6h5
FAIL: WAC 001 score 661 below 31997
FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion
FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion
```

Full ASan/UBSan CTest ran for stage 1 OFF/ON and stage 2 ON: 13/14 with those same four lines and no sanitizer finding. Short Threads 1/2 depth-10 searches also passed. **Stage 3 ran six ASan/UBSan smoke searches with leak detection; its full fourteen-test sanitizer suite was not run.**

All disassembled Release variants have zero FMA instructions in `forge::` functions; all 46 static-libc hits are attributed, 23 each to `__ieee754_log_fma` and `__ieee754_log_fma4`. ON NNUE refresh/update/evaluate contain ZMM instructions. Original snapshot and update-snapshot streams compare equal.

Each stage additionally completed **1,000,000 positions per OFF/ON producer**, including legal walks, incremental special moves and API invariants. Each original stream is 4,216,000,320 bytes; all six have SHA256 `e2ccf250bfbf1cc688bba9cbe20a7abffe09ffce8fe9681ea4459ba85341ad6f`. Original byte comparisons, independent hashes/counts and producer exits passed. Reused compression still executes both producers and compares each fresh raw chunk against fully decoded canonical bytes before linking immutable archives.

Each timing screen used two fresh-process warmups per engine and four OFF/ON/ON/OFF blocks: eight ON/OFF pairs, Threads 1, Hash 16, OwnBook false, `bench 20`. The metric is engine-reported internal NPS, validated against nodes/time; process wall time is diagnostic. Rows below are pairs 1–8. Each candidate is compared with the OFF lock, so stage 3 is not an isolated alignment-versus-stage-2 comparison.

| AVX-512 | + Generic no-copy | + Private alignment |
|---:|---:|---:|
| 0.76786071 | 0.83654654 | 1.12728636 |
| 0.77322435 | 1.03821084 | 2.30392215 |
| 0.98551005 | 1.08273273 | 1.29745410 |
| 1.10986756 | 0.90911461 | 0.90962206 |
| 1.43488783 | 0.80601246 | 1.20032280 |
| 1.01718838 | 0.79867629 | 1.36179911 |
| 0.89289450 | 0.92170819 | 1.35169504 |
| 0.92699107 | 1.18236415 | 0.83619566 |
| **Median 0.95625056** | **0.91541140** | **1.24888845** |
| Range 0.76786071–1.43488783 | 0.79867629–1.18236415 | 0.83619566–2.30392215 |

The wide ranges prevent a reliable quantified speed conclusion. No matches or SPRT ran. The existing nearest-valid walkback was retained; exact refresh caching lacked a useful proven opportunity. Activation/dot fusion already existed; optional final-update/evaluate fusion was deferred.

## JOB 2

`FORGE_COMPLETE_ITERATION_ONLY=1` is an off-by-default coherence guard. Legacy abort handling can replace best/PV/ponder from an unfinished iteration while retaining the previous score/depth, then emit the newer attempted depth with that old score. Selecting a partial move is an intentional policy; this finding does not prove that move inferior.

Minimal fresh-process reproduction, waiting for protocol responses and for bestmove before quit:

```text
uci
setoption name Threads value 1
setoption name Hash value 16
setoption name OwnBook value false
ucinewgame
isready
position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
go nodes 600
quit
```

The complete depth-3 line is cp26, `e2e4 h7h6 d2d4`, at 206 nodes. Legacy output then advertises depth4/cp26 with `h2h3 g8f6 d2d4 d7d5` and returns `h2h3`; a full depth-4 control needs 772 nodes. Enabled guard retains the completed tuple and returns `e2e4`. Cumulative internal nodes/seldepth still include unfinished work. Initial native GREEN passes the five completed-tuple/fallback/depth4/depth10 controls.

Repair source is commit `706da442…d09b`. The portable UCI suite gives lock RED exit 1 (8/19 pass, 11 expected coherence failures), candidate GREEN 19/19 exit 0. The independent direct public `SearchInfo` checker gives lock 15/19, candidate 19/19. Root independently reran 19/19 for Release and ASan/UBSan. Cases cover Ponder, restricted `searchmoves`, an actual nonempty partial first-iteration PV, legal fallback and complete depth4/10 tuple/node parity.

Both official OFF/ON builds preserve all five benchmark node counts and startpos perft5. OFF is byte-identical to the qualified lock; ON SHA256 is `208e82c556d940c5cf519d330867f8fdfd0da4912e50134054b6417b5508d9de`. ON Release CTest is 13/14 with exactly the same four known lines. Six additional T1/T2 depth10 ASan/UBSan searches pass with leak detection.

The all-three-flags-enabled combined profile also passes all five node signatures, perft5, Release 13/14 with only those four lines, 19 UCI assertions under Release and ASan/UBSan, six sanitizer searches and Forge FMA0. Its Release binary SHA256 is `45f5a84856a27f62008105444bb362f09582c0232f572a5e6d53239fddcedcec`. This is additional integration qualification, not another million-position or performance experiment. The policy remains default OFF; coherence validation does not establish an Elo benefit.

Bounded TT/mate/rule50 controls found no additional confirmed defect. Native lock lifecycle TSan recorded exit 0, 15 active phases, 68 passing assertions, 23 legal replies and no diagnostics. It exercised T1/T2 stop/isready, ponderhit, active ucinewgame, Hash/Threads/UseNNUE changes and active quit. Both workers were pinned to one CPU; this is finite lifecycle coverage, not a scaling test or universal race-freedom proof. The excluded crew root-draw and stale-SMP-counter fixes were not duplicated. Sparse-ending null-pruning remains an unconfirmed lead, not a demonstrated bug or submitted fix.

The 64-entry bad-capture buffer is another unconfirmed capacity lead: no accepted reproducer or native failure was established. An automated safety filter blocked the native checker; it was not retried, and only static review was completed. No patch is proposed for that suspicion.

## Evidence, tools and next action

[Source and evidence branch](https://github.com/couns0538-sketch/dwqww/tree/forge/sol-nnue-speed-audit-20261024); [experiment records](validation/sol-nnue-speed-audit-20261024/). Records cover stage1/2/3, workflow, job2-complete-iteration, job2-audits, combined-profile and closing. Original logs, failed fixture designs, commands and hashes are preserved as exact UTF-8 bytes in reversible JSON bundles. Large original streams are retained losslessly locally; executables, binary objects, ZIPs and build directories were not committed.

The independent audit of commit 706 verified 85 committed validation files, 900 embedded records, 79 artifact references, all 60 original NPS process rows/24 pairs and 300 oracle chunk receipts/six closed producers. A separate public readback verified all 115 changed files at 97469f3: HTTP200 and byte-equal to immutable local Git blobs. This receipt covers that pre-report checkpoint; the final report delivery receives a separate public readback.

Relevant available skills were reused. The existing repository SIMD validation skill was improved and validated without creating a duplicate. Skill-creator and CodeRabbit CLI were unavailable; no global installation is claimed. Git/public raw access worked; optional GitHub API access was unavailable and was not retried.

Windows/Ryzen qualification, Elo, exhaustive correctness and stage3 full sanitizer CTest remain unverified. The requested reference PC/box binaries were unavailable and were not run. Activation/dot fusion already existed; no useful bit-exact refresh-cache variant was established.

Next: the owner’s separate PC QA should compare the exact lock and individually selected optional flags under controlled timing. Evaluate completed-iteration policy independently. No matches were run for this delivery. Keep every flag OFF until separately adopted; no integration merge or positive Elo result is claimed.
