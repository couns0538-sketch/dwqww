# S02 v2 — warning repair and gate-option precheck, 2026-10-25

**Status: bounded S02 v2 validation PASS; publication pending root verification. Strength/speed UNPROVEN.** The original S02 release is preserved. This v2 keeps `FORGE_WARN_UNKNOWN_OPTIONS` default **OFF**, including normal PC gate builds, and fixes only the empty-name diagnostic's trailing space. A separate warn-ON executable is used for gate prechecks. ON CTest requires Python **3.10+**.

The authoritative targets are current 12:15 Job C/S01 L' and B, with code base `1ab50b2dd64d9b2f752f7f1285f6968cad2fd792` plus the explicit supplied network overlay `74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b`. Current merged tests/tests.cpp has SHA256 `55334ba94fd508d5f8e8e0e715c86a6996eddc69b20b1c110a96e46deaa2c`; B also preserves buffer-repair patch `9ce56b3d9b5291e450679209ac991c4d560bf40f64aa0281492c53ad37d96a5c`. The code-base commit and selected network overlay are separate provenance inputs.

The frozen bottom patch is `forge_sol_S02_unknownopt_v2_20261025.patch`, SHA256 `cc1d5823edbf285aab5311f40b22cd515e42d6f9872e24002a3cd237d5f217d9`. It was generated with private-scratch `git diff --full-index --unified=5`, a/b prefixes and `new file mode 100644`. Actual `git apply --check`, GNU `patch -p1 -F0 --dry-run`, and application passed on minimal target-file copies of plain L, current L' and current B. Added blocks reverse to each tree's own original files, preserving their different Job C/S01/buffix notes. The source regression adds an empty parsed-name command and requires the exact bare line `info string unknown option`, with no trailing space.

S03 v2 is stacked above this exact S02 bottom patch; it is a separate job. The precheck tool, README, tests and fixtures are separate dated deliverables, not extra engine flags or runtime options.

The final precheck tool SHA256 is `5858d867dd210a49497231957602fc4a1b78dd683d21db098ff92b70a725b30e`. It takes a JSON-list manifest, a dedicated warn-ON executable and a NEW output directory. A reserved unknown-name probe first proves warning capability; the tool cannot silently approve a warn-OFF executable. It sends core settings then each manifest option serially with readiness barriers, with no go/bench/perft. Canonical names and single-token values prevent the current Forge parser from silently changing requested wire semantics. A final complete-stream sweep catches unknown/invalid replies during quit/EOF drain and attributes them to gate/option. Original bytes, exits and EOF state are retained, with input hashes and an inside-output checksum check.

| Check | Status | Evidence/scope |
|---|---|---|
| Private Git diff proper new-file headers/full context | PASS | Four files; explicit 100644 header and full a/b paths |
| Git and GNU zero-fuzz apply, L/L'/B | PASS | Actual three-tree check/dry-run/apply receipts; offsets remain visible in raw output |
| Warning compile switch default OFF | PASS source | Same guard and OFF CMake default; no new UCI option, stats or counter |
| Python-only precheck tests | PASS | Initial missing-tool RED; initial 10 GREEN; five parser/drain cases RED on earlier tool; final 15 GREEN |
| Independent precheck source review | PASS | Reserved delimiter/alias, truncated value and late diagnostic defects closed |
| Actual old warn-ON focused regression | PASS expected RED | Actual original exe returns1; only full-warning list and empty no-trailing-space checks fail; other checks and raw handshake comparison pass |
| L' Release OFF | PASS | Exact accepted engine SHA; actual first bare d11; complete current CTest14/14, 4 KNOWN/0 FAIL |
| L' Release ON | PASS | Actual five references/perfts/FMA; complete current CTest15/15, 4 KNOWN/0 FAIL; unchanged UCI list |
| L' ASan/UBSan ON | PASS | Current merged tests/tests.cpp compiled fresh; qualified unchanged core/support reused; complete current CTest15/15, 4 KNOWN/0 FAIL |
| Current B Release OFF/ON and ASan ON | PASS | Actual current CTest15/15,16/16,16/16; all exits0, four KNOWN/zero PIN_MISMATCH or FAIL; fresh frontend/current sanitizer tests, qualified core/support reuse |
| Actual precheck controls, L'/B | PASS | Warn-ON clean fixture exits0; typo exits1 naming G_typo and RefutLmrMinr; warn-OFF capability control exits1 |
| Live PC manifest, Windows/PC, gates, speed/Elo | UNVERIFIED | Only supplied self-authored fixtures/native local builds; no PC/PGO script, live gate, match or gain claim |

The fixed node sequence remains **308972 / 745494 / 2460422 / 11901452 / 31111774** and perft5 totals **4865609 / 193690690**. OFF qualification reuses fixedrefs/perft/FMA only where actual OFF engine bytes equal the freshly qualified current baseline, with the baseline receipt hash retained. ON uses actual measurements. Every newly linked frontend is first invoked with bare OFF d11 before any other engine request.

Native execution is deliberately described precisely: **fresh frontend compilation/linking against source/hash-qualified existing core**, with unchanged qualified support tests reused. The merged current tests/tests.cpp (SHA256 `55334ba94fd508d5f8e8e0e715c86a6996eddc69b20b1c110a96e46deaa2c`) is freshly compiled for sanitizer profiles. This is not claimed as a fresh all-target engine build. Current L'/B test outputs require four KNOWN lines, zero PIN_MISMATCH/FAIL lines and full CTest exit0; historical failing test binaries are not substituted.

Preserved failed approaches include an early minimal-file producer postcondition that wrongly compared L's entire IDEA file to L' (their existing notes intentionally differ), and five initial precheck false-PASS cases. The corrected producer reverses only newly added blocks and compares each base to its own original. The producer failure is retained as summary metadata, not misrepresented as original stderr. Unit test logs explicitly distinguish initial10 GREEN from final15 GREEN. Fake protocol children are Python-only fixtures; actual C++ evidence is separate.

The gate tool is an unknown-option/protocol precheck, not the later full gate schema/value-effectiveness validator or strength activation gate. Empty/whitespace-containing values are rejected because current Forge consumes one value token; option names use canonical single spaces and cannot include its literal `value` delimiter. Hidden recognized tunables remain allowed without requiring advertisement. See the PRECHECK_README for fixture schema, command and raw-evidence details.

Skills: existing review and verification guidance was reused. Root updated the existing repository-local [validating-chess-simd skill](https://github.com/couns0538-sketch/dwqww/blob/35dcc1fda6ef9073b1b0ead40a1264fe7175928f/.agents/skills/validating-chess-simd/SKILL.md) to require proper Git new-file headers/full context and both apply checks on each current base. The [actual before/after reference-command proof](https://raw.githubusercontent.com/couns0538-sketch/dwqww/35dcc1fda6ef9073b1b0ead40a1264fe7175928f/validation/forge_sol_pack31_20261025/forge_sol_handoff1435_recovery_20261025/forge_sol_S02_patch_skill_reference_red_green_20261025.json) preserves old S02 Git-apply RED versus this v2 GREEN on all three trees. Existing local skill SHA256 changed from `dafcfbe574c7d6b13146aaea18eb48db0965094cba25b1c2c720e7f63d94caea` to `71bb030e24e5a7c38077ae3f9470022f839fa415a68666bcb38a63a47386dc97`. This was reference-command validation, not a fresh-agent pressure test. No duplicate skill or cloud/global installation is claimed; skill-creator was unavailable, so the existing writing-skills workflow was used.

All six native profiles and focused controls are closed. Independent source/native review is PASS. Remaining action is the final delivery seal/review, root Git publication and immutable download verification; S03 has the next native lease. Do not redo these completed builds/tests on resume. No source or accepted engine version is discarded.


| Engine flavour | L' SHA256 | B SHA256 |
|---|---|---|
| Release, warnings OFF | `e3df99cddb609d9f00168d8df3187fdf6943c10812dd5c4f82206895e594367b` | `55fa7e81768452bf62e5c9fa748d88353e37fbec50492077e70d30f14fc7d406` |
| Release, warnings ON | `0187fe03451d04678b095a19db3eb7cb209449868afad5fc9ca6c140a7675880` | `f575b1a5a087bce1fe18693e2f108611d79a21112825743878cfdc602a403857` |
| ASan/UBSan, warnings ON | `c11f0b898d5a6b1db9fb4a4731731ce507ec0bab9c2e7e06f0a5c22610c6287b` | `47bdf1d8f62acf738fff07676046e3ffc238a0f87bc8f2a7067b385ceef667e9` |

The actual old-warn-ON focused RED used unchanged original engine SHA256 `e99321524b39f1bffb740c67904fe96805aacbb8299dcdbeb1ffeef187582cee`. It is a diagnostic control, not the accepted current build. Plain L has source-apply checks; candidate native qualification targets the required current merged L'/B. No PC or live manifest was accessed.

Patch diffstat: 4 files, +61 −0. CMakeLists.txt +8 −0; IDEA_SOURCE.md +5 −0; src/uci.cpp +8 −0; tests/forge_sol_S02_unknownopt_test_20261025.py +40 −0.

Exact commands, source/header/core bindings, original full streams, current full LastTest logs, focused controls and failures are in the lossless indexed evidence bundle. Complete source/build/ELF copies remain private. The warning/precheck code and fixtures are supplied as separate dated files; no source ZIP or stale original test binary is delivered.
