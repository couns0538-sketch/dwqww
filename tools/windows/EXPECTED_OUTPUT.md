# Native Zen5 qualification

Run with PowerShell **7** on grok-pc. Pass the four immutable Windows executables in this exact order: OFF lock, stage1 AVX512, stage2 no-copy AVX512, stage3 AVX512+align64. Stage2 is a possible regression until its verdict is FASTER. Optional additional executables default to all experimental runtime options OFF. An explicit quantized research profile, described below, can enable int16 after its OFF identity gates.

```powershell
$b='C:\Users\Administrator\grok-pc\forge_push\bin'
.\zen5_qualify_sol.ps1 -Cpu 6 -Exes @("$b\forge_lock.exe","$b\forge_stage1.exe","$b\forge_stage2.exe","$b\forge_stage3.exe") -OracleExes @("$b\oracle_lock.exe","$b\oracle_stage3.exe") -Out 'D:\grok-pc-data\forge_push\speed_window\sol_20261024_run1'
```

`-Out` must be a new or empty directory. Earlier evidence is never overwritten. Every child uses ProcessStartInfo, redirected stdin/stdout/stderr, the selected CPU and Normal priority. The script sends engine commands or oracle `start` only after pinning. A timeout stops only its own child PID; no unrelated process is touched. Windows CPU indices 0..63 refer to the process's processor group; use this on the specified single-group Zen5 machine. Any affinity/priority failure stops the run.

The script prints hashes of all engine and oracle executables before the first engine command. For **each build**, its first engine test is bench11, all experimental runtime options OFF. Unknown optional `setoption` names are harmless in Forge; `UseNNUE` remains true. Identity checks do not publish the bench NPS. The exact expected lines include:

```text
MODE NATIVE_WINDOWS CPU=6 priority=Normal Threads=1 Hash=16 OwnBook=false depth=16
IDENTITY lock sha256=<64 hex> exe=<path>
IDENTITY stage1 sha256=<64 hex> exe=<path>
IDENTITY stage2 sha256=<64 hex> exe=<path>
IDENTITY stage3 sha256=<64 hex> exe=<path>
NODES PASS lock depth=11 nodes=308972 all_experimental_options=OFF
NODES PASS lock depth=13 nodes=745494 all_experimental_options=OFF
NODES PASS lock depth=16 nodes=2460422 all_experimental_options=OFF
NODES PASS lock depth=20 nodes=11901452 all_experimental_options=OFF
NODES PASS lock depth=22 nodes=31111774 all_experimental_options=OFF
```

The same five node lines must appear for every supplied executable. Actual Forge raw stdout uses `info string bench depth 11 nodes 308972 time <ms> nps <nps>`; the parser requires exactly one line at the requested depth. Any mismatch produces `STOP BADNODES`, STATUS `BADNODES`, exit1, and no later test of that build. Other failures also stop immediately and preserve raw text exchanges.

The identical oracle source is linked separately against the OFF lock and stage3 cores. Its CLI is `--positions 10000 --seed <1..100> --wait-start`; it waits for the exact stdin line `start`. Each producer executes 100 independent deterministic 10,000-position legal-walk corpora, totaling 1,000,000 records per producer. Seeds 1..100 define this corpus; it is **not** the earlier single-seed million-position corpus. Order alternates OFF/ON, ON/OFF per chunk, serially on the same CPU. Each H256 output is 42,160,320 bytes; matching SHA256, length and JSON coverage are required. At most two raw chunks (~84.4 MB) are retained while comparing. Passing raw binary chunks are deleted; hashes and coverage remain. A failing pair remains available.

Oracle stderr must contain one JSON line with `kind=nnue_million_oracle`, positions, records, seed, refresh, updates, parent_checks, inplace_checks, games, starts, moves, captures, en_passant, castles, quiet_promotions, capture_promotions, genuine_boards. Counts must agree with the requested seed/count; both producers' complete coverage JSON must agree. Legacy key=value stderr may precede it.

```text
ORACLE CHUNK PASS start=0 positions=10000 sha256=<hash> bytes=42160320
...100 chunks...
BIT_EXACT PASS positions=1000000 chunks=100 seeds=1..100 OFF_vs_AVX512_stage3 same_cpu=6 hashchain_sha256=<hash> (hashchain is not raw-concatenation SHA256)
AA PASS pairs=6 band_pct=<value> rule=max_absolute_of_all_six median_pct=<value>
SUMMARY stage3 sha256=<hash> nodes_ok=True median_pct=<value> mean_pct=<value> faster=<k>/14 slower=<k>/14 AA_band_pct=<value> verdict=<FASTER|NOISE|SLOWER> bit_exact=PASS_OFF_VS_STAGE3 oracle_gate=PASS EXPLICIT_AVX512_ON_VS_OFF
PHASE_SPLIT NOT_MEASURED optional -Profile native instrumented probes were not requested
SUMMARY END bit_exact=PASS phase_split=NOT_REQUESTED ... matches=0 Elo=UNPROVEN
```

`oracle_hashchain.txt` is UTF8 without BOM. It contains one LF-terminated line per chunk: `zero_based_chunk,seed,count,raw_chunk_sha256,bytes`. Its SHA256 authenticates this ordered hash manifest; it is not a SHA256 of concatenated raw oracle bytes. Arithmetic oracle PASS in this run applies only to OFF and stage3. Stage1/stage2/additional summary rows say `NOT_CHECKED_THIS_RUN`, while their mandatory prerequisite oracle gate says PASS.

Six A/A pairs each execute four fresh lock processes in palindrome order A A A A. The A/A band is the **maximum absolute gain across all six**; no outliers are discarded. Then each listed executable, including the lock control, gets 14 actual ABBA pairs against the first lock executable. Each pair is four fresh processes A B B A, two engine-reported NPS values averaged per side, gain=100*(mean(B)/mean(A)-1). All timed runs must retain the exact depth-specific lock nodes. FASTER requires at least 12 positive pairs and median gain strictly greater than the stated A/A band. Otherwise SLOWER requires at least 12 negative pairs; all remaining cases are NOISE. The band is descriptive calibration for this session, not a statistical confidence interval. No speed verdict establishes Elo.

Files: `frozen_protocol.json` and its printed SHA256, `zen5_qualify_sol.STATUS`, complete text log, bounded raw stdin/stdout/stderr per run, `oracle_chunks.csv`, `oracle_hashchain.txt`, paired CSV and summary CSV. The frozen protocol includes executable hashes, options and any supplied research expected-node map before the first engine test. Engine/oracle hashes are checked again before paired timing. Final STATUS is DONE only after every requested phase passes. Failed runs retain partial evidence and a failure STATUS; do not interpret their partial rows as completed qualification.

Pair CSV header:

```csv
kind,candidate,exe_sha256,pair,A1_nps,B1_nps,B2_nps,A2_nps,nodes_ok,A_nodes,B_nodes,gain_pct,depth,cpu,threads,hash_mib,ownbook,oracle_gate,option_profile,dry_run
```

Summary CSV header:

```csv
candidate,exe_sha256,nodes_ok,expected_nodes_at_depth,option_profile,per_pair_pct,median_pct,mean_pct,faster,slower,pairs,aa_band_pct,verdict,bit_exact,oracle_gate,profile,phase_split,interpretation,dry_run
```

PowerShell Export-Csv quotes header/value cells. Decimal strings use invariant culture. `per_pair_pct` contains all 14 gains separated by semicolons.

## Optional API profiling and limits

Add `-Profile -ProfileExes @('<OFF native probe>','<stage3 native probe>') -ProfileIterations 10000`. Each probe receives `--iterations N --wait-start`, waits for stdin `start`, and returns one stdout JSON record: `kind=nnue_phase_benchmark`, iterations, hidden_size=256, refresh_ns_per_call, update_ns_per_call, evaluate_ns_per_call, checksum, api_phase_only=true. Values must be finite and nonnegative. This gives API kernel ns/call only. It does not provide the fraction of whole search time. Internal whole-engine timing instrumentation is not delivered; the phase split remains NOT_MEASURED. Profiles run after NPS; their results do not influence speed verdicts.

Linux is allowed only with `-DryRun` and synthetic fixtures; the final STATUS is DRY_RUN_DONE_NO_SPEED_CLAIM, every verdict is DRY_RUN_ONLY, and every CSV row is marked dry_run=True. A syntax parse and failure-gate fixture run are software checks, not Zen5 speed evidence. No native Windows run has been performed by the script author.

## Windows g++15.2 build lines

Use frozen source directories corresponding to the stated commits; compiling all four against the latest source does **not** reconstruct stages1/2. Copy the identical supplied oracle/probe source into each relevant frozen export before building. The root handoff supplies those files and source/network hashes. No network changes or fast-math. Execute each one-line command from its named source directory; `bin` must exist. All commands use the exact requested Zen5 H256 flags. The patches against f4911f2 and the buffer repair are delivered separately by the root owner.

```powershell
# lock=f4911f2 (h256_e12)
g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_AVX512=0 -DFORGE_NNUE_ALIGN64=0 -ffp-contract=off -fno-fast-math -march=znver5 -static -pthread -Iinclude src/bitboard.cpp src/board.cpp src/book.cpp src/eval.cpp src/eval_params.cpp src/nnue.cpp src/search.cpp src/uci.cpp -o bin/forge_lock.exe
# stage1=7e4c22a (AVX512)
g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_AVX512=1 -DFORGE_NNUE_ALIGN64=0 -ffp-contract=off -fno-fast-math -march=znver5 -static -pthread -Iinclude src/bitboard.cpp src/board.cpp src/book.cpp src/eval.cpp src/eval_params.cpp src/nnue.cpp src/search.cpp src/uci.cpp -o bin/forge_stage1.exe
# stage2=bf237d2 (AVX512+no-copy)
g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_AVX512=1 -DFORGE_NNUE_ALIGN64=0 -ffp-contract=off -fno-fast-math -march=znver5 -static -pthread -Iinclude src/bitboard.cpp src/board.cpp src/book.cpp src/eval.cpp src/eval_params.cpp src/nnue.cpp src/search.cpp src/uci.cpp -o bin/forge_stage2.exe
# stage3=7716853 (AVX512+no-copy+align64; later buffer-only repair may be included if identified in root manifest)
g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_AVX512=1 -DFORGE_NNUE_ALIGN64=1 -ffp-contract=off -fno-fast-math -march=znver5 -static -pthread -Iinclude src/bitboard.cpp src/board.cpp src/book.cpp src/eval.cpp src/eval_params.cpp src/nnue.cpp src/search.cpp src/uci.cpp -o bin/forge_stage3.exe
# oracle OFF: lock source + identical supplied tools/nnue_million_oracle.cpp
g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_AVX512=0 -DFORGE_NNUE_ALIGN64=0 -ffp-contract=off -fno-fast-math -march=znver5 -static -pthread -Iinclude src/bitboard.cpp src/board.cpp src/book.cpp src/eval.cpp src/eval_params.cpp src/nnue.cpp src/search.cpp tools/nnue_million_oracle.cpp -o bin/oracle_lock.exe
# oracle ON: stage3 source + identical supplied tools/nnue_million_oracle.cpp
g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_AVX512=1 -DFORGE_NNUE_ALIGN64=1 -ffp-contract=off -fno-fast-math -march=znver5 -static -pthread -Iinclude src/bitboard.cpp src/board.cpp src/book.cpp src/eval.cpp src/eval_params.cpp src/nnue.cpp src/search.cpp tools/nnue_million_oracle.cpp -o bin/oracle_stage3.exe
# optional phase probe OFF: lock source + supplied tools/nnue_phase_benchmark.cpp
g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_AVX512=0 -DFORGE_NNUE_ALIGN64=0 -ffp-contract=off -fno-fast-math -march=znver5 -static -pthread -Iinclude src/bitboard.cpp src/board.cpp src/book.cpp src/eval.cpp src/eval_params.cpp src/nnue.cpp src/search.cpp tools/nnue_phase_benchmark.cpp -o bin/profile_lock.exe
# optional phase probe ON: stage3 source + identical supplied tools/nnue_phase_benchmark.cpp
g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_AVX512=1 -DFORGE_NNUE_ALIGN64=1 -ffp-contract=off -fno-fast-math -march=znver5 -static -pthread -Iinclude src/bitboard.cpp src/board.cpp src/book.cpp src/eval.cpp src/eval_params.cpp src/nnue.cpp src/search.cpp tools/nnue_phase_benchmark.cpp -o bin/profile_stage3.exe
```

Optional int16-ON testing needs a supplied, frozen expected-node map. Append its executable and label `int16`; pass `-Labels @('lock','stage1','stage2','stage3','int16') -OptionProfiles @{int16=@{Options=@{NnueInt16=$true};ExpectedNodes=@{13=<actual frozen ON nodes>;16=<actual frozen ON nodes>}}}`. Replace placeholders with independently obtained actual counts before running; this is intentionally not a runnable example. Depth 13, 16 and the selected timing Depth require positive declared counts. The int16 executable first passes all five lock depths with NnueInt16=false. It then verifies the declared ON d13/d16 counts before any oracle/timing phase; every later int16 ABBA run checks the same frozen ON count. Every ON run must advertise `option name NnueInt16 type check default false`, then acknowledge `info string NnueInt16 active`. Missing activation or `info string NnueInt16 unavailable; using float` stops BACKEND_INACTIVE; matching node counts alone cannot prove activation. Lock A remains OFF. Pair rows include separate A/B node counts, summary rows state the option profile and expected count, and arithmetic status is `NOT_APPLICABLE_QUANTIZED_RESEARCH`. A changed count stops BADNODES. This is an explicit quantized research speed screen, not float parity or playing-strength acceptance. No int16-ON map or result is supplied by the script author.

Fixture checks: `python3 tests/test_failure_gates.py --pwsh /absolute/path/to/pwsh`. They parse PowerShell, check the 12/14 and median-band verdict boundaries, then run synthetic bad-d11, bad-d13, nonzero-exit, truncated-oracle, unsupported-int16-option and inactive-int16-backend cases. They verify immediate stopping, raw evidence and absence of paired NPS before oracle PASS. They never run an actual engine or interpret synthetic NPS as a speed result. The checks passed under privately extracted Linux PowerShell 7.5.2; native Windows remains unrun.
