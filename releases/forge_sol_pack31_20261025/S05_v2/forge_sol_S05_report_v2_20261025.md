# S05 v2 — copied-zero FMA qualification and fixture cleanup, 20261025

The repaired checker passes static disassembly of the supplied Windows PC lock and Linux lock, rejects the retained real helper-FMA mutant, and cleans temporary CTest fixture directories on both successful and failing test exits. All six current L-prime/B profiles pass 107/107 CTest with exactly four known outcomes and no PIN_MISMATCH/FAIL in each merged CPP suite. `FORGE_BUILD_NNUE_VALIDATION` remains OFF by default. Speed and Elo are UNPROVEN; accepted h256_e12 is unchanged. Publication remains UNVERIFIED until root's actual immutable readbacks.

Baseline code `1ab50b2dd64d9b2f752f7f1285f6968cad2fd792` plus the supplied h256_e12 net overlay SHA256 `74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b`; the commit's original net differs. B retains the supplied buffer repair. Current merged `tests/tests.cpp` SHA256 `55334ba94fd508d5f8e8e0e715c86a6996eddc69b20b1c110110a96e46deaa2c` is calculated from the actual file. No engine, NNUE arithmetic, network, search, TT, move ordering, UCI tool or CMake behavior changed from S05 v1. The two Python file updates and IDEA placement are the bounded v2 changes.

Patch `forge_sol_S05_ctestwire_v2_20261025.patch` SHA256 `b5f38950761743c8a53943bfc02942edc449a471cbda20b9c91438801b566090` is a full-index Git-U5 diff: 7 files, +579/-0, five proper new-file mode100644 headers. Actual old S05 Git checks PASS all three bases; no fabricated old Git RED is claimed. Actual v2 Git-check and GNU-F0 dry/apply PASS L/L-prime/B. CMake, both float C++ helpers and UCI tool are byte-identical to the old applied patch on each base. The same IDEA entry is relocated after a shared safe title, preserving every old note. The original publication remains untouched.

## Checker and cleanup evidence

The old checker fails two of the 27 copied-zero fixtures. Final checker SHA256 `e7ba90e5c2bdb43c490d9c992a684f7f0d311d83c7639ad852f77a4dd079d07f` and final runner SHA256 `152f0d77b61d69bd28d93a24b43a936b7b7bf49f1fea1998a0946d48df70e287` pass all27. Zero provenance now propagates only across an unmasked same-width YMM register `vmovaps`/`vmovups` copy from an already proven-zero source. Existing register/alias clobber invalidation and call/jump barriers remain. Memory, unknown, narrow and masked-copy sources are rejected by fixtures. This is a bounded 256-bit recognized-lowering checker requiring demangled NNUE symbols, not proof of arbitrary binary data flow or semantic equivalence. Unsupported or stripped lowerings remain unsupported.

Supplied PC PE SHA256 `456743d9c065d2dec2d9a52ef23992f36908efc1243b6916edab9a8ab3c7fdfa` passes the copied-zero mask-clamp path, NNUE-scoped FMA0 and a separately retained whole-executable FMA count0. Linux canonical ELF also passes both counts0. Full original whole-disassembly gzip streams, original checker commands/stdout/stderr and scopes are preserved. The Windows executable was statically disassembled on Linux; Windows runtime execution is UNVERIFIED. The new checker also rejects the exact retained native helper-FMA mutant with exit1. That is a fresh static qualification of a source/binary-bound old mutant; no new mutant engine runtime or compilation is claimed.

Default fixture execution uses a temporary-directory lifetime that is closed through success and unittest SystemExit1. The actual old cleanup RED retains its leaked directory; new success and deliberate fixture-failure cases both leave an empty parent. Explicit `--out` remains persistent for review evidence. Full27 final-runner execution and selected lifetime controls are distinct recorded runs.

|Check|Status|Evidence scope|
|---|---|---|
|Old copied-zero fixtures / final27|RED2 / PASS27|Actual original commands and streams|
|Default success/failure cleanup|PASS|Both parent listings empty; explicit output persists|
|Actual PC PE / Linux scoped and whole FMA|PASS static|All counts0; both original full disassembly gzip streams|
|Actual helper-FMA mutant|PASS expected rejection|Retained exact native executable; new checker exits1|
|Git and GNU-F0 all three bases|PASS|22 original commands /44 streams; unchanged C++/CMake/UCI bytes|
|Six current merged native suites|PASS|107/107 actual CTest; KNOWN4 /PIN0 /FAIL0|
|First bare d11|PASS fresh invocation|308972 before other runtime checks in each profile|
|Five Release refs and perft5 totals|PASS inherited|Exact canonical production engine/source binding and original current-handoff VERIFY streams|
|Float parity/thread/UCI replay|PASS current CTest|Only registered ON-suite invocations; no extra old-corpus replay|
|Windows runtime, speed, Elo|UNVERIFIED / UNPROVEN|No native PC execution or strength measurement|

## Current native scope

|Base|Profile|Option|CTest|Added S05 targets|Main ELF SHA256|
|---|---|---|---|---|---|
|B|asan|ON|20/20|5|`1564bd068a03c0293983b666a8fdfb2d56e8d2c2406485e36114bf0af7a9a8e6`|
|B|release|OFF|15/15|0|`55fa7e81768452bf62e5c9fa748d88353e37fbec50492077e70d30f14fc7d406`|
|B|release|ON|20/20|5|`55fa7e81768452bf62e5c9fa748d88353e37fbec50492077e70d30f14fc7d406`|
|Lp|asan|ON|19/19|5|`61da67f15ebce9edb186d5cf76dac7096a486584d2382e54e7c6eabadcd4e23e`|
|Lp|release|OFF|14/14|0|`e3df99cddb609d9f00168d8df3187fdf6943c10812dd5c4f82206895e594367b`|
|Lp|release|ON|19/19|5|`e3df99cddb609d9f00168d8df3187fdf6943c10812dd5c4f82206895e594367b`|

Current merged CPP tests are freshly compiled and the actual current CMake full suites exercise the frozen Python files. Qualified existing production main/core/native helper bytes are reused with exact source, flags, archive/member and fixture identities. No fresh full-engine all-target build is claimed. OFF adds no validation targets; ON adds the same five float/API/UCI/checker targets. H256 stays float with C++20, `-ffp-contract=off -fno-fast-math`; exact Release O3 and ASan/UBSan O1/g1 per-target flags are retained. Each registered ON parity invocation reports21306 comparisons/20194 transitions with zero lane/score/state mismatches; the warm four-worker test reports8000 transitions with zero errors. It serially bootstraps immutable data before its worker gate and does not replace S04's separate cold-first-Board test. Actual depth4 UCI searches reset via ucinewgame before each replay; NNUE c2c4/cp25 repeats around the completed HCE d2d4/cp13 search, without a universal warm/cold equality claim.

The fixed reference oracle remains d11/13/16/20/22 =308972/745494/2460422/11901452/31111774, perft5 start4865609 and kiwipete193690690. Deep refs/perfts are inherited through exact same production bytes and original provided-handoff full-VERIFY evidence. No extra old whole corpus, deep benchmark sweep or new speed measurement is claimed. Kiwipete: `r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1`.

Existing repository-local SIMD-validation guidance was extended for copied-register zero proofs and temporary-directory lifetime checks. The separate S05 before/after reference proof, original static/fixture/cleanup command captures and final local guide SHA256 `a1da44076c52410b87033d41fcbb7eab478b7752b12aacc54bcb0516ed70470c` are included; the frozen S04 guide2b8 identity is separate. The updated skill is `.agents/skills/validating-chess-simd/SKILL.md`; see `forge_sol_S05_skill_proof_v2_20261025.json`. This is reference-command validation and existing-skill maintenance, not a fresh-agent pressure test or cloud/global installation. The immutable v1 checker pointer remains until root qualifies and publishes its successor.

## Recoverable checkpoint

The flat delivery provides the patch, five exact helper sources, source/static/native reviews and 217 original-byte evidence records. The index records every path, size and SHA256. Prior current-handoff baseline logs and the actual helper-FMA result/identity are the only inherited corpus; the entire old S05 corpus is not resubmitted. All new fixture history, cleanup RED/GREEN, native full streams/LastTest logs, controllers, incomplete observer approaches and skill proof are retained. No ZIP, source-tree, engine ELF/PE, net, object or cache-payload export is included. Any cache payload paths remain local-only dependencies for rebuilding reused products.

```sh
sha256sum -c forge_sol_S05_SHA256SUMS_v2_20261025.txt
python3 -B forge_sol_S05_raw_restore_v2_20261025.py --archive forge_sol_S05_raw_evidence_v2_20261025.jsonl.gz --index forge_sol_S05_evidence_index_v2_20261025.json --out NEW_OUTPUT_FOLDER
```

The reused portable decoder actually restored and byte-compared every record; an existing output directory was rejected. All S05 native jobs and leases are closed. Next: independent final document/package binding and root immutable publication verification, then the saved S25 requalification/S27 order. No engine acceptance or speed/Elo claim follows.
