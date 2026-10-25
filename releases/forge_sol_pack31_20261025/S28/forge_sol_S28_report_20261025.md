# S28 development report — 2026-10-25

**Qualification complete; adoption/strength UNPROVEN.** Accepted source remains code-base `1ab50b2dd64d9b2f752f7f1285f6968cad2fd792` plus the supplied h256_e12 network overlay `74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b` (MD5 `6d22f612c855e17c62d396d32da99ea4`); accepted buffix base is preserved separately. The supplied L/B manifests and 151-file audit bind the actual inputs; the code-base commit and selected network are recorded separately. Candidate e48f006 is not adopted. S03 was published before this work at `a57839e55d3c2d2cc7578369c9e09cc7be21b62c`.

The portable kit copies full build inputs into a NEW output, swaps only its copied net, performs fresh full Release builds, gates every new engine first at OFF d11, observes pins, regenerates exact allowlists/checksums and appends metadata preserving old bytes. It defaults to dry-run. Three existing queue patches were qualified independently; only the demonstrated B/timepack4 CMake conflict received a necessary context repair.

| Check | Status | Actual evidence |
|---|---|---|
| Native full Release matrix | PASS | 10 fresh engines, four controller cases; GCC 14.2, C++20, CMake 3.31.6; strict float H256 x86-64-v3/znver5 recipe in guide and original argv/flags |
| First invocation d11 gate | PASS | Every new engine first invoked OFF; fixed oracle, not self-derived |
| Current-net OFF five references | PASS | L/B: 308972 / 745494 / 2460422 / 11901452 / 31111774 |
| Candidate-net OFF five references | PASS | All eight f006 engines: 328459 / 945640 / 3024381 / 9162399 / 20421972 |
| ON five-depth observations | PASS | Six independent queue runs; exact table in rebase report |
| perft5 / kiwipete5 | PASS | 4865609 / 193690690 on all ten engines |
| FMA | PASS | 0 whole-executable + 0 NNUE-object on all ten; supplied NNUE-body checker also passed |
| Original forge_tests / full CTest | PASS known-failure policy | Only forge_tests fails; each actual run retains exactly four original FAIL lines, not silently relabeled |
| Final strict OFF/base pin postcheck | PASS | All ten stage signatures; original four checksum manifests verified first |
| Input / source / net / executable identity | PASS | 151 original files unchanged; all ten actual net and retained source/binary hashes verified |
| Final tool tests | PASS | 27/27, including relocated five-file kit layout |
| Final shell dry-run filesystem trace | PASS | Four successful mutating file syscalls, all inside NEW output; inside-output checksum check PASS |
| New ASan/UBSan matrix | UNVERIFIED | No new sanitizer matrix in S28; Release results are not a sanitizer claim |
| Full native filesystem syscall trace | UNVERIFIED | Trace proof is final shell dry-run only; native input immutability/source audits are separate |
| Windows / PC / speed / equal-time Elo / G104c confirmation | UNVERIFIED | No PC run, speed percentage, match, Elo claim, or lock switch |

Native execution used the actual frozen v2 tool SHA256 `7530b90a4e5dcb2cfdd49f4fc186cabd78b193a8523700dc50637038c7543c7d`. The exact original source bytes are preserved, not reconstructed. Final v3 SHA256 `421b156ea48dfbaa5ff0e6b219baa6b4e3e3102b705d0c181144413e8cd39db3` adds strict queued-OFF/base pin equality and printed summaries. Its pure guard was applied read-only to closed native evidence; it is not described as a repeated final-v3 native matrix. Final v3 shell dry-run was executed and traced. Postchecker SHA256 `a091b30611829ddb8319b5d47e6bb2dea7cdb1b1e3042db6df2d7ac6aee15f08` verifies the original captured manifest SHA, actual inside-output sha256sum -c, complete planned stage IDs and all three zero-exit/EOF captures before comparing exact signatures.

## Native engine identities

| Case / stage | Executable SHA256 | CTest passed / total |
|---|---|---|
| L_lock / base | `e3df99cddb609d9f00168d8df3187fdf6943c10812dd5c4f82206895e594367b` | 13/14; original known-four forge_tests failure |
| B_lock / base | `55fa7e81768452bf62e5c9fa748d88353e37fbec50492077e70d30f14fc7d406` | 14/15; original known-four forge_tests failure |
| L_f006 / base | `668b8483e349d8c11a36bf0ad95cebdcd657aa24cac5739b09981e50f93066f4` | 13/14; original known-four forge_tests failure |
| L_f006 / P23b | `8bc18596c1f2f52029c035d2c0c0554e9aba0e4cdb72b31fc4c2d36447c64d99` | 13/14; original known-four forge_tests failure |
| L_f006 / P27R | `c060437d2a2670fb962e15ced94ed0c172cd9df13d1176467d57994d19828408` | 14/15; original known-four forge_tests failure |
| L_f006 / timepack4 | `b81e3b37a583b404695701f92dc73d63ffc06d89985bf96de2de64d22cf5ab9a` | 14/15; original known-four forge_tests failure |
| B_f006 / base | `e8682b8407e1a76d4b927d63273103ec27635148d6f0b1c460b65ef97a2ddd83` | 14/15; original known-four forge_tests failure |
| B_f006 / P23b | `72047800ab781703d9cf2b7b9b87d7354414195465381140a5f856553cb3471c` | 14/15; original known-four forge_tests failure |
| B_f006 / P27R | `b7e3fa79bd53d065a5ce3a16b9c9fade73a48fab9dbf09e8beebd9e480049314` | 15/16; original known-four forge_tests failure |
| B_f006 / timepack4 | `18a53264874875412e02134c698a46a716613472617b9803a221f5c253fb4738` | 15/16; original known-four forge_tests failure |

## Net-specific observations

| Case | Current h256_e12 | Candidate e48f006 |
|---|---|---|
| WAC001, d12 | f6h5, cp661 | f6h5, cp629 |
| White promotion, d1 | c6d7, cp642 | c6d7, cp686 |
| Mirror promotion, d1 | c3d2, cp642 | c3d2, cp686 |

Only one literal FAIL line changes: `FAIL: WAC 001 score 661 below 31997` becomes `FAIL: WAC 001 score 629 below 31997`. The WAC move line and the two identical promotion FAIL lines stay unchanged. Promotion score pins nevertheless change and are recorded explicitly. No expected test source value was edited.

## Preserved evidence and limitations

There are **209 actual Runner command receipts / 627 stdin+stdout+stderr streams**, plus independent pin captures, full test logs, original manifests, actual patch failure/repair receipts, generated compile flags and hashes. The compressed JSONL evidence bundle has 383 original-file records. Every record was decoded and its original byte count/SHA verified after compression; its index maps each original private path. This gzip file is a lossless raw-evidence container, not a source archive. Complete source/build/binary products remain retained in their original private output directories and were checked by the original manifests.

Independent closed review verified all 3048 files listed by the four native manifests, all 209 commands/627 streams, ten source/net/executable identities and unchanged original inputs. Source review found and closed the OFF-pin allowance gap. TDD RED/GREEN receipts and the trace-observer false-positive attempt are retained. The first failed observer did not retain its stdout/stderr before assertion: those bytes are marked UNAVAILABLE and were not reconstructed; its original trace is retained. A fresh observer retained raw evidence before checking and passed.

The current-net baseline executable hashes reproduce the accepted native binaries exactly. Candidate compatibility is not candidate strength acceptance. No NPS percentage or Elo is inferred from changed ON node counts.

Next action after verified publication: proceed to S04, preserve h256_e12 references globally, and use these f006-specific OFF/ON pins only if a future authorized lock transition is confirmed. No existing queued engine patch is accepted by this tooling task.

For original-file verification, read each gzip JSONL line, base64-decode `data`, and require its length/SHA256 to equal `bytes`/`sha256`; the published index lists the same records. Never extract over an existing directory. The five-file kit and full dated instructions are in `forge_sol_S28_lock_transition_kit_20261025/`; the S01 pin helper remains a SHA-pinned existing dependency rather than a duplicate.

The retained `forge_sol_S28_baseline_git_audit_20261025.json` independently binds 21 CMake/src/include files to the full code-base commit. Every checked code file matches exactly; the explicit supplied network overlay is recorded with both commit-network and selected-network hashes. This is provenance evidence, not a source-version substitution.

The first flat publication producer is retained privately as a packaging attempt. The canonical publication preserves the required named kit directory, one copy of every callable and evidence payload, a checked inner kit manifest, and a checked outer manifest. No native result or payload byte changed during this layout correction.
