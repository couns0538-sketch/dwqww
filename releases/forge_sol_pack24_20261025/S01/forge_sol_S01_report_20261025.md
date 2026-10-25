# S01 — Job C pin-mismatch follow-up, 20261025

Status: **PARTIAL**, because the three specifically requested alternate nets are absent. All available lock/buffix local implementation, negative-control and sanitizer checks pass. Test-reporting change only; performance and playing-strength effects are UNPROVEN. Exact pins and the original mate/rook expectations remain intact. No engine source, network, options or default search behavior changes.

Prerequisite: apply the existing Job C patch with SHA256 `4ac98f92d45f67fae8aaa8067fe28c0fca36662b3688013105f738245ee55805` to either supplied L or B. This delivery does not resubmit that patch.

Follow-up patch: `forge_sol_S01_pinmsg_20261025.patch`  
SHA256: `bddc961125a25c9d4331a8555b0304653f550c378c38fb480a1ba9b2ba92d528`  
Diffstat: tests/tests.cpp37 changed lines, IDEA_SOURCE.md10 additions, README.md13 additions;3 files,54 insertions and6 deletions.

The exact WAC pin is named as constants f6h5 /661 /d12 and still requires score equality, matching case/FEN/original expectations and matching nonempty PV. Unexpected values retain ordinary FAIL/exit1 and additionally print `PIN_MISMATCH:` with the documented and observed move/score/depth/PV and a reviewed re-record instruction. Promotion drift similarly prints the exact documented king move and depth/PV versus the observed result; the existing score>100 guard is retained, never replaced with a new numeric pin. The old6.4.24 expectations remain g3g6/score>=31997 at d12 and c7c8r/c2c1r/score>100 at d1. Exact historical numeric winning scores are UNVERIFIED, not invented.

IDEA_SOURCE receives a new idea-only entry citing the user's S1 request and supplied review item7. README receives a lock-adoption checklist requiring observation, review, exact pin retention and negative controls. B's existing appended documentation remains byte-identical. Documentation insertions use zero-context hunks at the exact verified shared-prefix line endpoint, while C++ hunks retain context; both exact supported bases were dry-run and actually patched with zero fuzz and no offsets.

| Check | Status | Evidence |
|---|---|---|
| Prior Job C score660 / king-alternative / WACdepth11 controls before follow-up | PASS as RED | Each actual suite exit1, but the new-message checker failed because no pin diagnostic existed |
| Final patch cleanly applies to L+C and B+C | PASS | Actual dryrun/apply, -p1 --fuzz=0, no offsets; source bytes match each private candidate |
| Candidate target on fresh L core | PASS | Exit0, exactly4 KNOWN_FAILURE labels,0 ordinary FAIL,0 pin mismatches |
| Candidate target on fresh B core | PASS | Exit0, exactly4 KNOWN_FAILURE labels,0 ordinary FAIL,0 pin mismatches |
| Score661→660 mutation | PASS | Exit1; documented660 versus observed661 printed; ordinary WAC failures preserved |
| WACdepth12→11 mutation | PASS | Exit1; documentedd11 versus observedd12 printed |
| King alternative mutation | PASS | Exit1; both original king moves/scores/depth/PV printed against changed pins |
| Promotion-depth and promotion-PV mutations | PASS | Exit1 and clear observed drift messages |
| WAC-PV mutation | PASS | Exit1 and observed PV=a1a1 printed; actual existing none-move formatter recorded |
| Read-only pin printer on fresh L and B engines | PASS | Both reproduce f6h5/661/d12 and c6d7/c3d2/642 at d1 |
| Raw stream preservation | PASS | Final helper requires both reader threads closed; actual final L/B reruns complete; base64/length/SHA256 round-trips verified |
| Delayed pipe-drain negative control | PASS | Actual bounded transport fixture: old helper falsely completed, final helper exits1/UNVERIFIED; no running fixture children remain |
| Existing-output refusal | PASS | Exit1 before engine launch; existing outputs and engine hash unchanged |
| Independent bounded source/tool review | PASS | Final patch/README command and final drain-guard helper reviewed; `forge_sol_S01_final_review_20261025.json`; native/full-CTest results are separate evidence |
| Exact alternate nets e20i/e12f/e16q | UNVERIFIED | Required net artifacts absent; no substitute presented as those versions |
| Final L Release / ASan+UBSan CTest | PASS |14/14 each; direct forge_tests4 KNOWN/0 FAIL each |
| Final B Release / ASan+UBSan CTest | PASS |15/15 each; direct forge_tests4 KNOWN/0 FAIL each |
| Main engine byte identity, all four profiles | PASS | Exact original engine SHA256 retained; full native matrix receipt below |
| L/B five OFF bench depths | PASS by exact executable identity |308972 /745494 /2460422 /11901452 /31111774; original fresh S00 measurements reused |
| L/B perft5 / kiwipete5 / NNUE FMA | PASS by exact executable identity |4865609 /193690690 /0; original fresh S00 measurements reused |
| Native Windows / immutable publication | UNVERIFIED HERE | No PC execution; root verifies publication separately |

The exact requested e12f net SHA256 is `0a00a610aaa160586aafd022946d37bc1e385459b7b35d7c17b0a2b48d92fe8e`; e16q is `5fa6052d76947ea3d2a500f7ec10dff77cf72a82f048261fed0eadc19f56376e`. Neither matches any of28 supplied `.inc` files. e20i has no supplied complete identity/artifact; its historical row is not a usable net. The supplied descriptions mention674/690/614 as historical WAC scores, but these are not current measurements. Root independently audits nested input membership. No differently named/versioned net was silently substituted.

## Final four-profile native matrix

`forge_sol_S01_full_matrix_receipt_20261025.json` records root's actual rebuild/CTest/direct-target results. Every main engine is byte-identical to its unpatched profile; only the test executable/reporting differs.

| Base/profile | Engine SHA256 unchanged | CTest |
|---|---|---|
| L Release | `e3df99cddb609d9f00168d8df3187fdf6943c10812dd5c4f82206895e594367b` |14/14 |
| L ASan+UBSan | `4fa3a1c34a95633a511e00674734c68a53773db1498c6df0df27cd3e3e349e9d` |14/14 |
| B Release | `55fa7e81768452bf62e5c9fa748d88353e37fbec50492077e70d30f14fc7d406` |15/15 |
| B ASan+UBSan | `f842092e75c530b3899e8fc07cc2e14dcc0e0088253b2bd437ac590648fb863d` |15/15 |

## Commands and evidence

The native evidence controllers, preserved with their original bytes and full hashes inside `forge_sol_S01_raw_evidence_20261025.json`, are `forge_sol_S01_red_controls_20261025.py`, `forge_sol_S01_native_controls_20261025.py`, `forge_sol_S01_native_finish_20261025.py`, and `forge_sol_S01_patch_builder_20261025.py`; each retained output and exact compiler argv. Run `python3 forge_sol_S01_evidence_reader_20261025.py forge_sol_S01_raw_evidence_20261025.json` to verify all embedded raw bytes; add `--extract NEW_FOLDER` to recover them without overwriting an existing path. Final native target builds use GCC14.2, C++20,O3,DNDEBUG,H256,-ffp-contract=off,-fno-fast-math,-march=x86-64-v3,-mtune=znver5,-pthread against fresh unchanged L/B Release libraries. The three initial RED controls use original C-only exact-lock PGO objects, clearly identified in their own provenance; final controls use no PGO or Job A code. No original lock/baseline/distribution path is modified.

Portable pin-printer command, with shell and Python helper together:

```sh
bash /path/to/forge_sol_S01_rerecord_pins_20261025.sh /path/to/forge --out NEW_FOLDER --expect-lock
```

Omit `--expect-lock` when recording a different embedded net: the tool prints observations without adopting them. It takes an executable, hashes it, uses fresh processes, Threads1, OwnBook=false, Hash8 for WAC and Hash1 for each promotion case, and waits for the requested-depth score/PV and bestmove before quitting. It changes no pins, engine, input shards, affinity or host limits and invokes no process-termination API. New output-folder creation is exclusive. An uncooperative child is reported UNVERIFIED with its PID; it is not killed.

Raw case streams are encoded to preserve existing banners without adding their text to the delivery. The structured results contain the observed values and original stream hashes. Outputting only selected parsed pins is not offered as a replacement for the raw evidence.

Failed tooling attempts are retained. First, EOF-anchored documentation append hunks did not apply to B's later notes; final exact-position insertions fixed only patch layout. Second, an external WAC-PV negative-control oracle assumed Move::none formats0000; the existing formatter actually emits a1a1. The same unchanged executable was rerun with the corrected oracle. Production already rejected and diagnosed that PV drift. The README bare-command invocation was corrected during review to explicit bash/script path. A delayed-drain fixture initially had a conditional-spacing syntax error; that fixture failure is retained, corrected independently of production, then the actual pipe experiment passes. The final Python helper also closes a review finding: it rejects any still-running stdout/stderr reader instead of marking a partial capture complete. Pre-guard bytes and old-false-PASS/new-fail-closed transport evidence are retained. Both real L/B pin runs were repeated in new folders after this helper change. No original failure evidence was overwritten.

Next: root verifies immutable publication, then starts S02. Final full CTest and unchanged engine artifacts already pass. Requested missing-net tests stay UNVERIFIED until the exact artifacts arrive. No other job is implemented by this S01 delivery.
