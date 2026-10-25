S03 v2 fixed-reference repair and delivery, 2026-10-25

Status: DONE for the requested v2 repairs and Release validation. No engine algorithm or evaluation changes. Existing S03 v1 remains preserved.

The engine code base is commit 1ab50b2dd64d9b2f752f7f1285f6968cad2fd792 with the separate h256_e12 net overlay src/nnue_weights.inc SHA256 74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b. L-prime and B are the exact supplied current Job C/S01-merged source trees; B also preserves its buffer repair. This job retains that network and those existing changes.

Apply the replacement S03 v2 patch above the S02 v2 bottom patch, rather than above S03 v1. S02 v2 was published at commit 9999b5a20bda52eded802dc56f49e90a2b4fe019.

- S02 prerequisite SHA256: `cc1d5823edbf285aab5311f40b22cd515e42d6f9872e24002a3cd237d5f217d9`
- S03 v2 patch SHA256: `0265586224f041140e25e7fe1a46233e0c18f155324f60d83808a8ad30ae5791`
- Native receipt SHA256: `f78a4c2c5f223d42c0df28d5a87d16df53606a08aa15a2c485cfb2be9dd9e054`
- Updated runner SHA256: `321780dedced0daf267a885ac8281d01a0a5e6f3c1813a6779f88941cb038847`

The only runner behavior change converts an existing explicit --out directory, file or dangling symlink from a traceback to exactly one error line and exit 1. The three real CLI collision controls fail on the published runner and pass on the repair; no engine is invoked in those controls and existing entries remain intact. Perft, bench, mate/PV, oracle, command handling and stream capture remain unchanged.

The patch is generated with full-index five-line-context Git diff, a/ and b/ paths and three new-file-mode 100644 headers. Ordered S02 then S03 passes actual git apply --check and GNU patch -p1 -F0 dry-run/apply on all L, L-prime and B context probes; actual complete L-prime and B build trees were patched independently. Existing notes and source inputs are preserved. No C++ files, existing test expectations, UCI options, net, search or move ordering are changed by S03. FORGE_FIXED_REFERENCES remains a validation-only default-OFF CMake option.

Diffstat:

```text
CMakeLists.txt                            |   13 ++
 IDEA_SOURCE.md                            |    9 +
 tests/forge_sol_S03_fixedrefs_20261025.py |  100 +++++++++++++++++
 tests/forge_sol_S03_fixedrefs_20261025.sh |    5 +
 tests/forge_sol_S03_oracle_20261025.json  |  175 +++++++++++++++++++++++++++++
 5 files changed, 302 insertions(+)
```

Actual qualification:

| Check | Result | Evidence and scope |
| --- | --- | --- |
| New runner CLI collision regression | PASS | Original RED 3/3, repaired GREEN 3/3; directory/file/dangling-link retained |
| Ordered patches on L/L-prime/B | PASS | Git check and GNU zero-fuzz dry/apply, proper file modes |
| Four fresh Release configurations | PASS | L-prime/B, fixed references OFF/ON; core/main/forge_tests freshly compiled |
| First engine use per fresh binary | PASS | Bare bench11 = 308972 before UCI/CTest |
| Fresh main and forge_tests identities | PASS | OFF/ON match the separately qualified current baseline bytes |
| Direct current forge_tests | PASS | All four profiles exit 0, exactly four KNOWN_FAILURE, zero FAIL/PIN_MISMATCH |
| CTest registration | PASS | OFF L-prime14/B15; ON L-prime15/B16; no OFF target leak |
| Actual full CTest ON | PASS | L-prime15/15 and B16/16, exit0, four KNOWN_FAILURE only |
| Actual fixed-reference ON suite | PASS | 70 rows per base; complete actual child closure and original streams |
| Five bench references | PASS | Fresh ON checks: d11/13/16/20/22 = 308972/745494/2460422/11901452/31111774 |
| Perft references | PASS | Fresh ON: 40 depth-count cases including startpos5=4865609 and kiwipete5=193690690 |
| Mate and full terminal PV references | PASS | Fresh ON: five fixed tactics, expected mate distances, PV first move/length, terminal zero legal moves and mate score |
| NNUE and whole-executable FMA count | PASS, inherited by exact ELF identity | Canonical current baseline count0; no fresh disassembly command claimed |
| OFF deep benches/perfts and full suite | PASS by exact source/ELF inheritance | Fresh OFF first11/direct tests/listing; other OFF full checks not rerun here |
| Leaf-count mutation | PASS, expected RED | Actual engine first bare11=308972; runner exits1 at start_d1 expected20/observed40 |
| Skipped-en-passant mutation | PASS, expected RED | Actual engine first bare11=308972; runner exits1 at start_d5 expected4865609/observed4865351 |
| New optional fixed suite under ASan | UNVERIFIED | Not freshly executed under ASan in this job |
| Current production/tests sanitizer qualification | Inherited, separate scope | Unchanged C++ and tests are source-qualified to the published S02 native ASan results; this is not a new optional-suite sanitizer run |
| Original input source identities | PASS | All baseline source hashes rechecked before and after |
| Windows, PC gates, PGO, playing strength | UNVERIFIED | Not executed; no speed or Elo claim |

Fresh byte identities (SHA256):

| Base | Fixed references | Main | forge_tests |
| --- | --- | --- | --- |
| Lp | OFF | e3df99cddb609d9f00168d8df3187fdf6943c10812dd5c4f82206895e594367b | 70a5eeadd320e6e8380e93e1ab0ed46bc4ad8fc8e2144f5f11027f00900861b3 |
| Lp | ON | e3df99cddb609d9f00168d8df3187fdf6943c10812dd5c4f82206895e594367b | 70a5eeadd320e6e8380e93e1ab0ed46bc4ad8fc8e2144f5f11027f00900861b3 |
| B | OFF | 55fa7e81768452bf62e5c9fa748d88353e37fbec50492077e70d30f14fc7d406 | 0be00f18f6867b6d23da68669fab15202e1038350fcfcb62d671e936897c9f9d |
| B | ON | 55fa7e81768452bf62e5c9fa748d88353e37fbec50492077e70d30f14fc7d406 | 0be00f18f6867b6d23da68669fab15202e1038350fcfcb62d671e936897c9f9d |

The ON full suites reuse eight L-prime and nine B support executables from the fresh canonical baseline after source and executable hash checks; these unchanged helpers were not recompiled. Main, core and forge_tests were freshly built in all four profiles. The current test source SHA256 is 55334ba94fd508d5f8e8e0e715c86a6996eddc69b20b1c110110a96e46deaa2c.

Historical script recovery:

- forge_sol_S03_cmake_validation_20261025.py, SHA256 `07dff850b53cbf42ec675447ac38f6d97abd67c36de9156b5537fed58f386e35`: recovered byte-identical original v1 producer. HISTORICAL ONLY: hardcoded old paths and four-FAIL assumptions, including restoration of the old test source. Do not run it as a validator for the current merged KNOWN_FAILURE trees.
- forge_sol_S03_perft_mutation_20261025.py, SHA256 `dbd5485bcf34f0acd74cc348635403150e78d344d6ed91f75602003727df68db`: recovered byte-identical original v1 producer. HISTORICAL ONLY: uses old local objects; it is not the current mutation producer.
- forge_sol_S03_v2_native_validation_20261025.py is the separately delivered current explicit-input producer used for the four fresh builds, current KNOWN_FAILURE checks and both new actual mutation controls. Its source and all44 native command records are retained. The private faulty engine sources and binaries remain isolated locally; no mutant engine patch is delivered or adopted.

Reproduction from a clean L-prime or B tree (Python >=3.10, CMake, GCC, Bash, GNU patch and Git available):

```bash
git apply --check /path/forge_sol_S02_unknownopt_v2_20261025.patch
patch -p1 -F0 < /path/forge_sol_S02_unknownopt_v2_20261025.patch
git apply --check /path/forge_sol_S03_fixedrefs_v2_20261025.patch
patch -p1 -F0 < /path/forge_sol_S03_fixedrefs_v2_20261025.patch
cmake -S . -B /path/NEW_BUILD -DCMAKE_BUILD_TYPE=Release -DFORGE_FIXED_REFERENCES=ON -DCMAKE_CXX_FLAGS='-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256'
cmake --build /path/NEW_BUILD -j2
printf 'bench 11\nquit\n' | /path/NEW_BUILD/forge
ctest --test-dir /path/NEW_BUILD --output-on-failure
bash tests/forge_sol_S03_fixedrefs_20261025.sh /path/NEW_BUILD/forge --out /path/NEW_RESULTS
python3 -B /path/forge_sol_S03_cli_regression_20261025.py --tool tests/forge_sol_S03_fixedrefs_20261025.py --out /path/NEW_CLI_RESULTS
```

FORGE_WARN_UNKNOWN_OPTIONS is deliberately omitted from the configure command, leaving the S02 compile option at its default OFF. Run the shell wrapper with bash because the patch records mode100644. Every output path above must be new. The separate current native producer accepts --baseline-receipt, --s02-patch, --s03-patch, --out, --cmake and --ctest; exact executed command lines and strict flags are in the native command records. No process is killed, no parent affinity/limits are changed, and no timing comparison was run.

Evidence and continuation: the flat raw-evidence JSON preserves original bytes using base64, original paths, byte counts and full SHA256, including original failed approaches. The final checkpoint identifies all current source/tool/result hashes, parent prerequisite and next action. SHA256SUMS is checked from inside the delivery folder. Native work finished 2026-10-25T15:11:38.665782+00:00; no owned native jobs remain. Publication and immutable download verification are performed by the coordinating parent after this delivery.

Skills reused: chess-engine validation, native evidence preservation, test-driven development and verification-before-completion. No duplicate or global skill was created or claimed installed. The existing validation guide's shared S02 patch-application improvement has actual old RED/new all-three-base GREEN proof; it is a prerequisite maintenance change, not an additional S03 engine patch. The CLI collision lesson and its actual RED/GREEN proof are available for the same existing guide.

Next: publish and download-verify this sealed S03 v2 delivery, retain original v1, then continue S28 v2 in the specified order. Optional fixed-reference ASan execution remains a distinct unverified follow-up.
