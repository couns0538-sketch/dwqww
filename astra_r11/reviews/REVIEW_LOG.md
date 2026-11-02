# R11 review ledger — static qualification only

## Prerequisite
Independent audit_crfix verified22 copy receipts / 21 unique staged targets, available manifests, missing-manifest disclosure and preserved sealed-pack paths. Commit 30c1993856ea41135ed4b0f7f8acf72e950a7739; exact hashes are in evidence/CRFIX_APPLIED.json.

## Historical recovery
Independent audit_crfix checked RECOVERY.md/json and INPUT_PREFLIGHT.json claims against the recorded evidence. No overstated full scan or globally exhaustive absence claim; inherited counts and unknown game counts correctly distinguished. No authentic mapping found. Broader PC/GitHub receipts extend the search per user instruction; inspected ID lists are heuristics or different populations. Missing original maps remain a hard evidence blocker.

## Provenance toolkit
Independent trace_design first review: FIX before execution. Root accepted 4 findings: P1 origin digest did not authenticate row-binding choices; P1 incomplete storage reservations/live checks; P1 trailing-dot/space Windows aliases and leaf-first reparse checks; P2 nested checksum-name coverage gap. Author fixed all and wrote controls. Initial review overlapped final author edits; corrected candidate was explicitly frozen for re-review. A stale missing-verifier-bundling finding was withdrawn after inspection of the current code.

Same reviewer rechecked frozen corrections and closed all 4 findings by STATIC inspection. No new concrete defect found in changed areas. SHA256:
- build_game_provenance.py: 90eee5f294be01602356016853c8be8cd679b2f6a3de0d47152e846be943fe98
- pack_io.py: 6dc0b4f89b702331f75e41f834724e3697fd7b2b1d5d90e712abb021e79b7818
- verify_game_provenance.py: 91693542f76effe7ea1a259c80dead06081ed15c43040a4aeac124d2dc47b9ae
- test_gameprov.py: 84ce19a3bff1751e30374cd6ffb54c472ed14a7145c7b54c3dbca15bf94c8902
- README.md: 7625e471354a64f5f813ee3fc706582aca9527b88228767c6a8cc08f9a89f7ae

26 test methods authored, ZERO executed. No production adapters/registry entries authenticated. Output-shard resume remains INCOMPLETE; only input-copy-boundary resume exists. No production acceptance or zero-overlap PASS is granted.

## Runtime
Root review confirmed 3 important defects: prepared binding omitted imported helpers/manifests; inherited Python startup environment could inject code; path aliases and leaf-first traversal weakened guards. Author added complete candidate capture/prepost checks, clean/restored environment and lexical/root-first policy, with17 executed PowerShell policy checks plus hash-drift refusal. Original 14 test modules plus conftest remain byte-identical to checked-in R10 suite. Python assembly/fixtures/child startup/original 73 UNRUN. Independent corrected-candidate review pending at time of this entry.

Independent trace_design then found two additional P1 issues: wrapper preparation/admission output paths lacked pre-access validation, and the first Python launch did not yet bind extracted DLL/stdlib files to official archives. Root accepted both, plus the stale a10 launcher-contract instructions and exact fixture-count improvement. Author corrections require a focused static recheck before Prepare/Run. See RUNTIME_REVIEW.md.

Final focused recheck closed all accepted findings with frozen identities matching; see RUNTIME_RECHECK.md. Root read the corrections and prepared fixtures01: 61 source/input files and 1,791 official archive-bound bootstrap files. Exact command inspection matched one worker, CPU3, D-only output and 256MiB reservation. Actual Run refused at CPU admission before native launch. Ten conflicts and CPU2 load100% are in the original receipt. This is a verified refusal, not a fixture PASS. All Python checks remain UNRUN. Next action: preserve the prepared command for safe admission; no bypass.

## Small blocked-evidence sealer
Independent pack_tool inspected the exact sealer and found two narrow defects: copies could overwrite newly appeared destinations, and the reservation omitted generated metadata. Root accepted and fixed them with exclusive CreateNew streams, a fresh root, exact final census, metadata headroom and final size/floor checks. PowerShell parsed. Reviewer rechecked corrected SHA256 `2e90aa14e738ca30244eb09f0bea58f695a0ce1c036a63c30f7cece2f795a228` and closed both by static inspection. This permits the small evidence-only operation; root must independently reread both manifests and census before reporting sealed bytes. See SEALER_REVIEW.md. It grants no data qualification.
