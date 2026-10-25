# S03 fixed-reference regression suite, 20261025

Status: DONE for the two local Linux Release bases. This is optional test infrastructure; engine behavior, performance and playing-strength effects are UNPROVEN. No engine source, evaluation, network, TT, move ordering or expected test value is changed.

Patch: `forge_sol_S03_fixedrefs_20261025.patch`  
SHA256: `96a2b1bb4bd7bf4bb9ed15e35d024e79f99349feca5b7b6abd6f1c8f73dc1ca7`  
Diffstat: five files,300 insertions: CMakeLists.txt13; IDEA_SOURCE.md10; shell5; Python97; fixed-oracle JSON175. The sole option, `FORGE_FIXED_REFERENCES`, defaults OFF. With OFF no new target or runtime code is registered. With ON CTest registers `forge_fixed_references`, serially, using Python3.10+ and fresh unique output subdirectories. No engine executable needs a new source or link input.

The standalone shell/Python/oracle files are also supplied separately. The fixed values come from the user's published lock numbers, canonical benchmark data at https://www.chessprogramming.org/Perft_Results and original Forge tactical expectations. They are never inferred from a lock binary's output. Only benchmark data/ideas are used; no external engine implementation or tuned constants are imported. IDEA_SOURCE receives a new entry without replacing earlier content. Its common-prefix insertion preserves B's appended notes.

| Check | Result | Actual scope |
|---|---|---|
| Patch dry-run and apply to pristine L and B | PASS | GNU patch -p1 --fuzz=0, no fuzz/offsets; all src/include bytes unchanged |
| Implicit CMake default and explicit OFF | PASS | OFF by default; no fixed-reference CTest registered |
| CMake ON registration | PASS | Both bases list forge_fixed_references |
| Standalone fixed suite on L | PASS |65 comparisons plus5 validated PV records,70 result rows |
| Standalone fixed suite on B | PASS |65 comparisons plus5 validated PV records,70 result rows |
| Actual private Board::perft mutation | PASS as RED | Leaf count1→2; first d11 still308972; startpos perft1 becomes40 versus fixed20; checker exits1 |
| Full registered Release CTest on L | PASS known-failure policy | New target passes;14/15 targets pass; only original forge_tests fails with exactly four known lines; actual CTest exit8 |
| Full registered Release CTest on B | PASS known-failure policy | New target passes;15/16 targets pass; only original forge_tests fails with exactly four known lines; actual CTest exit8 |
| Independent source/oracle/raw-evidence review | PASS | No material issues; `forge_sol_S03_review_20261025.json`;36 complete native raw records independently verified |
| Original engine/source identity | PASS | Common completed Release ELFs reused byte-for-byte; original four-FAIL test ELFs restored only in private S03 test directories |
| Original ASan+UBSan engine/suite qualification | PASS inherited scope | Unchanged common engine/core sources and earlier original sanitizer receipts retained separately |
| New fixed-reference target under ASan+UBSan | UNVERIFIED | Not rerun; do not infer a new full sanitizer run from the Release target results |
| Windows / PC / gates | UNVERIFIED | No PC work, match or performance measurement performed |

Both Release engines retain their original SHA256:

- L: `e3df99cddb609d9f00168d8df3187fdf6943c10812dd5c4f82206895e594367b`
- B: `55fa7e81768452bf62e5c9fa748d88353e37fbec50492077e70d30f14fc7d406`

The completed original-source engines/core/support tests are reused by exact hash to avoid rebuilding unchanged C++ code. CMake is actually configured OFF and ON on private fresh source copies, actual CTest registration is checked, and all registered Release commands are run. The original forge_tests ELF is used rather than the later JobC relabelled executable. Main-engine copies, original support binaries, source identity and commands are recorded. Parent/original builds and evidence are not overwritten.

## Fixed references observed on both bases

| Bench depth | Fixed nodes | L | B |
|---|---:|---|---|
|11|308972|PASS|PASS|
|13|745494|PASS|PASS|
|16|2460422|PASS|PASS|
|20|11901452|PASS|PASS|
|22|31111774|PASS|PASS|

Every standalone or registered suite begins with a fresh-process OFF d11 precondition before any perft or mate search. Later depths each use fresh processes with Threads1, Hash16 and OwnBook=false.

| Perft position | d1 | d2 | d3 | d4 | d5 | L/B |
|---|---:|---:|---:|---:|---:|---|
|start|20|400|8902|197281|4865609|PASS|
|kiwipete|48|2039|97862|4085603|193690690|PASS|
|P3|14|191|2812|43238|674624|PASS|
|P4|6|264|9467|422333|15833292|PASS|
|P5|44|1486|62379|2103487|89941194|PASS|
|P6|46|2079|89890|3894594|164075551|PASS|
|P3 colour/rank mirror|14|191|2812|43238|674624|PASS|
|P4 colour/rank mirror|6|264|9467|422333|15833292|PASS|

The JSON contains all eight exact FENs. The two additional cases reverse ranks and swap piece colours, side-to-move and castling colours. This invertible transformation maps every legal move/promotion/castling sequence bijectively; these fixtures have no en-passant target. Their expected arrays are the same published canonical arrays, not measured counts adopted as truth.

| Mate fixture | Search depth | Expected mate | Best move / observed PV on L and B |
|---|---:|---:|---|
|white back rank|3|1|e1e8|
|smothered knight|3|1|h6f7|
|promotion mate|3|1|c7c8q|
|black back rank|3|1|e8e1|
|WAC001|16|2|g3g6 c6e5 g6h7|

Each mate case checks the UCI mate distance, expected best move, PV length2N−1, and PV first move. It replays the whole PV through the engine's legal position parser, checks zero legal terminal moves, and checks terminal score mate0/bestmove0000, distinguishing mate from stalemate. This is a real-engine regression check, not an independent chess implementation. The original WAC mate-in-two truth is tested at depth16 to clear the documented shallow horizon; its original depth12 test and known failure remain untouched.

## Commands and preservation

Standalone, with all three tool files together:

```sh
bash /path/to/forge_sol_S03_fixedrefs_20261025.sh /path/to/forge --out NEW_FOLDER
```

After applying the patch to a private L or B copy:

```sh
cmake -S PRIVATE_SOURCE -B PRIVATE_BUILD -DCMAKE_BUILD_TYPE=Release -DFORGE_FIXED_REFERENCES=ON \
  -DCMAKE_CXX_FLAGS="-march=x86-64-v3 -mtune=znver5 -ffp-contract=off -fno-fast-math -DFORGE_NNUE_HIDDEN=256"
cmake --build PRIVATE_BUILD -j2
ctest --test-dir PRIVATE_BUILD -R '^forge_fixed_references$' --output-on-failure
```

Actual local commands and hashes are retained by `forge_sol_S03_cmake_validation_20261025.py`, `forge_sol_S03_perft_mutation_20261025.py` and the native result records. The runtime checker uses only Python standard-library modules, changes no host limits/affinity/priority, and invokes no process-termination API. It awaits bestmove after searches and complete stdout/stderr closure before sealing original streams. Timeouts/unclean closure are failures with retained evidence; no process is killed. Existing explicit output folders are refused; CTest uses new unique subdirectories.

`forge_sol_S03_raw_evidence_20261025.json` preserves original commands, raw output, configuration, mutation evidence and failed tooling attempts with exact byte lengths/SHA256 and base64 payloads. Decode only for inspection; existing engine banner text is retained without adding it as new delivery text. Two generation-only conditional-spacing syntax errors failed before execution and are recorded; the corrected controllers run successfully. Fixed oracle values and successful native checker code were not changed to obtain a pass. No experimental perft source/binary is shipped as a production change.

Next job is S28 HIGH after this S03 delivery is published and download-verified. S04 is not next. No other implementation is included here.
