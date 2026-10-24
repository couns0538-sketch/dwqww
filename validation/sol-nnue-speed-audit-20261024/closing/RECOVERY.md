# H256 mission continuation checkpoint

All engine work and native QA are closed. No engine/match/benchmark job is active.
Do not resume an old live-status paragraph or rebuild a frozen compressed tree.

- Repository: /workspace/dwqww; only branch forge/sol-nnue-speed-audit-20261024
  may be pushed. Root owns Git/index/refs. Other branches and preexisting untracked
  files remain outside this mission. No merge or force push.
- Exact lock f4911f2709bd5ae7e5fca7aea30aac5d87314a05 = specified 1ab base + H256
  net SHA256 74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b.
- Latest engine implementation 706da4421be204c201fa5615fee298ab44c9d09b. All new
  flags default OFF: FORGE_AVX512, FORGE_NNUE_ALIGN64 (effective only with AVX512=1),
  FORGE_COMPLETE_ITERATION_ONLY. No training/net/format/publicABI change.
- Default engine remains byte-identical to lock d90f5060880c799ef8cdfd41bbef3668610a08619c9edaa266452f1bc656c47f.
- All three NNUE stages passed actual fresh OFF/ON million positions. Each 4,216,000,320B
  stream SHA256 e2ccf250bfbf1cc688bba9cbe20a7abffe09ffce8fe9681ea4459ba85341ad6f.
  Lossless immutable gzip originals remain in oracle-avx512-1, oracle-nocopy-2,
  oracle-align64-3. Later runs reused canonical representation only after fresh
  actual producer execution and full decoded/raw identity checks. Never replay.
- Each stage has five bench signatures: 308972/745494/2460422/11901452/31111774 and
  startpos perft5 = 4865609. Release 13/14 with exactly four user-whitelisted lines; tests unchanged.
  Forge FMA count 0; 46 libc hits attributed. Stage1 OFF/ON and stage2 ON full ASan CTest: 13/14, known four lines only;
  stage3 ASan: six short searches only. Each profile: six T1/T2 depth10 searches clean, leaks enabled.
- Actual eight-pair ABBA medians .9562505598/.9154113959/1.2488884484 versusOFF;
  huge variation, no reliable quantifiedspeed gain. Original timings preserved.
- Completeiterationguard: lock RED, then ON 19 UCI and 19 public API checks pass; root fresh
  Release 19 and ASan 19 pass. Six additional ASan searches pass. OFF five bench signatures/perft and
  byteidentity pass. ON five bench signatures/perft/Release known four lines pass. Coherenceonly, notElo.
- All-three-flag combined profile also passes five bench signatures/perft/Release known four lines, 19 UCI in
  Release and ASan, six ASan searches, Forge FMA count 0. No new million-position oracle or NPS run for combined.
- Frozen lock: 14 targeted TT checks; TSan 15 phases/68 assertions/23 legal replies pass;
  single CPU, finite coverage, no universal race-freedom/scaling proof. Bounds review
  no additional confirmed defect. Capture buffer suspicion unconfirmed; native
  checker blocked by automated safety filter and not retried. No fix/reproducer claimed.
- Independent evidence audit of 706 verified 900 embedded originals and 79 artifact references,
  all 60 NPS rows/24 pairs and six producer receipts. Public a5670fab004ca694fbad34a702b759bcf084eeb5
  readback: 106 files, all HTTP200/byte-equal. Newer closing/report publication must
  receive its own immutable readback; do not assume this old receipt covers it.
- No matches/SPRT/Elo claims, no binaries/ZIP/build-directory commits, no crew imports.
  Reference PC binaries unavailable; physical Ryzen/Windows not tested. GCC 14.2,
  Intel Xeon 8573C, AVX512F, four-CPU quota. Optional CodeRabbit CLI/skill-creator unavailable;
  existing repository SIMD skill improved/tested, no duplicate/global installation claim.
- Old ASan objects/test binaries/disassembly/snapshots have verified lossless restore maps
  in avx512-agent/{closed-evidence-restore-map,asan-build-restore-map}.json and
  avx512-agent/nocopy-qa/asan-restore-map.json. Main ASan engine binaries remain raw.
  NEVER rebuild a frozen compressed build directory in place. Fresh directories only.
- Job1 stop 13:03:47UTC, engine code stop 14:18:47, hard final 14:33:47UTC,2026-10-24.
  Next action: finish the report delivery commit, push, verify its immutable public
  files, and print the report and actual delivery SHA. After delivery, the next
  engineering gate is the owner's separate PC QA, with every optional flag off
  until separately adopted. No active model restart or chat-report scheduler exists.
