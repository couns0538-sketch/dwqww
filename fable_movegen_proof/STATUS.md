# STATUS: job 3, move-generator proof (Fable 5.2)

Written 2026-11-10 20:36 Vienna. All times are Europe/Vienna. Read this file first when resuming, then compare it with the files and processes that actually exist.

## State in one paragraph

No check has found a difference between any candidate and the lock. All release-executable checks are complete for all six candidates (pins, perft divide, warm transcript, Threads soak, edge suite). A harness review at 19:41 led to harness version 2 (stricter probe, transcript identity, tie between probe and executable); its self-test passes 67 of 67. The counted fuzz runs were started again from chunk 0 with harness 2 at 19:58 and are running; nothing is a PASS until they reach 20,000,000 on the auxiliary tier. Results of harness 1 (13 million auxiliary and 1.3 million release-exe comparisons per candidate, all equal) are kept as an earlier run and are not added to the counts.

## Clock

| What | Value |
|---|---|
| Start of the 7-hour period (plan approved) | 2026-11-10 18:57:50 |
| Reporting must start by | 2026-11-11 01:12 |
| End of the period | 2026-11-11 01:57 |

## Paths and revisions

| What | Value |
|---|---|
| Repo | `D:\forge_jobs_20261109\fable2\repo` |
| Branch | `fable52-movegen-proof-20261110`, started from `08897a88e11c707c0ac4e39c19e44c06e1360bdd` (tip of job 2); pushed, tip of the last push `1fd97049` |
| Pack on the branch | `fable_movegen_proof\` |
| Output root | `D:\forge_jobs_20261109\fable2\out\job3` (`bin`, `src`, `aux` = harness-1 probes, `aux2` = harness-2 probes, `runs`, `runs\h1` = harness-1 results, `tmp`, `logs`, `fail`, `corpus`) |
| Plan | approved by Couns 2026-11-10 18:57; decisions D1 (two-tier PASS) and D2 (20 million on the auxiliary tier) answered 18:15 |
| git | promisor clone, sparse and non-cone; pattern `/fable_movegen_proof/` added locally; `GIT_NO_LAZY_FETCH=1` in every shell |

## Frozen inputs (`out\job3\runs\freeze\INPUTS.json`, written 19:00)

All six supplied MD5s matched. Every source tree matched its build's `SOURCE_INPUTS.sha256` file by file.

| Tag | Release exe MD5 | SHA256 | Source manifest sha256 | Meaning of ON |
|---|---|---|---|---|
| LOCK | `c0051c99695f48bf93272d96fe7548c3` | `e1284f7fc492c8fe1285797fdae8988cf2f2926b33fcfee7023d284d67d8802e` | `3389cfe3dc7bb3989cfebfbdc8ac13d3785b71f090257664d04a0d7c74137645` | reference |
| LOCKEQ | `c8084074dc8180f6e6b62e7013cf5b4b` | `74bb3cfa3121bc2e260406b24409fbb2c0eeb760fa3bc413d524bdcf04ab9f9b` | `d4ded828c5c7ded02759cab7e29dccced836add95f5c6b631792692c82a3c355` | BUNDLE3 tree, all switches 0 (control) |
| EVL | `35781e5cac204370584ff4cb1f5ee93e` | `b89df40fce1726e316e7fb8e3348866401bd86a406aa689e9967f4a487c30237` | `48dee946a6bc9f12506bfccc68b1f52b9c96604e205c0d776db823afb26b905a` | `src\board.cpp:721 #define FORGE_SPD_EVADE_LEGAL 1` |
| PCM | `2cd6d44845e343f8b206b60f876c2165` | `a60aa7cff6163b172dc4e0c88afffa41516c70b8722ce600817ff39c5feb482e` | `c579dc5a94bbbd200084a7a4863ff4903f12b525660d51c0d4d25716437025c4` | `src\board.cpp:441 #define FORGE_SPD_PAWN_CAPMASK 1` |
| CKL | `8a159aed19f0d1ff0a9ee468e279794f` | `c643808f19905387cc5b6328f2c464d63208579998777257b179762b33869dbd` | `fad9288b078986062d50795e5179e573aa16463b630ee1fea03421d441f08139` | `src\board.cpp:1009 #define FORGE_SPD_CHECKERS_KL 1` (mode 1) |
| WNP | `1bf0291be0b2936c394c9a908f7432fe` | `5c8f0ec88a73dc7c1049d47a7a69724f2079834a6c4cd47df61f8308287b478b` | `16fc5e4cc5277f34c123b1e5c2fcc363067f17528eeedf2896538ff9ccc61d39` | `src\board.cpp:703 #define FORGE_SPD_WITNESS_NOPIN 1` |
| KPC | `55e1fe1230b5d19bd5382636a86f9c90` | `67eea5dc9d0deb59c2248c6488ab70c6aa5e22a01d247d2497f2454a8083d4aa` | `01ecdea868e81ac734eaf61030fa4d1b262572f7253bd0e1554f057edad34fb6` | `include\forge\eval.hpp:17 #define FORGE_SPD_KING_PAWN_CACHE 1` |
| BUN (BUNDLE3) | `ec5dc9d16897fe00f9e788edd9707180` | `db12981c4c840be4e9a93f04e88f12b1d7e90beb11f73070d0df9c316cc17d3c` | `d4ded828c5c7ded02759cab7e29dccced836add95f5c6b631792692c82a3c355` | `-DFORGE_SPD_EVADE_LEGAL=1 -DFORGE_SPD_PAWN_CAPMASK=1 -DFORGE_SPD_CHECKERS_KL=1` on a tree whose defaults are 0; patch md5 `ba2fcf2e78a0e2c85964a1e6e258d150`; not rebuilt; pin-equivalent, not byte-identical |

Other inputs: `fens_12k_v2.txt` md5 `e7dbf2c8151188c03ef52054557a531e`, sha256 `c01c0e6a49fb9aaab535058bd7280c33b8735e0f8bd40834f1c029843a75a265`; compiler `clang++.exe` sha256 `d05fee2c3f79b15d998d3c3413c76aabd416ec789edff89c8f698a8be44a3970`; Python 3.15.2. Net identity: `src/nnue_weights.inc` sha256 `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638` in every tree, `FORGE_NNUE_HIDDEN=256`, residual net.

Not tested, by name: QA's `build_v3\BUN` (the five-flag `BUNDLE`, md5 `59e18b7b...`) and `BN4`.

## Auxiliary probes, harness 2 (`out\job3\aux2\<TAG>\AUX_RECEIPT.json`, built 19:46 to 19:48)

Harness source `mgprobe.cpp` sha256 begins `42efd61dd819eb7d` (frozen copy beside each probe). Effective candidate switches as the preprocessor reports them:

| Probe | sha256 (first 12) | Effective switches | Files differing from the lock tree |
|---|---|---|---|
| LOCK | `509e10996b47` | none | none |
| LOCKEQ | `c40583f2a612` | EVADE_LEGAL=0, PAWN_CAPMASK=0, CHECKERS_KL=0 | `src/board.cpp` |
| EVL | `565cfd95a47b` | EVADE_LEGAL=1 | `src/board.cpp` |
| PCM | `baacf0585769` | PAWN_CAPMASK=1 | `src/board.cpp` |
| CKL | `695e3ce13647` | CHECKERS_KL=1 | `src/board.cpp` |
| WNP | `e5d60da73cb6` | WITNESS_NOPIN=1 | `src/board.cpp` |
| KPC | `7f6c70a5519f` | KING_PAWN_CACHE=1 (pawn-cache entry 64 bytes, 40 elsewhere) | `include/forge/eval.hpp`, `src/eval.cpp` |
| BUN | `83e355912d6e` | EVADE_LEGAL=1, PAWN_CAPMASK=1, CHECKERS_KL=1 | `src/board.cpp` |

## What the release executables expose (`out\job3\runs\observe\out_LOCK.txt`)

`d`, `eval`, `checkers`, `moves`, `legalmoves` and `help` were sent to the lock exe: it printed nothing for them. `go perft 1` prints the legal moves in generation order. So legal moves and their order are observable on the release executables; the checkers bitboard and the static eval are not. Those two fields are compared on auxiliary probes (decision D1).

## Checks

| Check | State |
|---|---|
| Launcher tests, freeze, observability record | DONE 19:00 to 19:02 |
| Self-test, harness 1 | DONE: red 19:09 (4/20) and 19:11 (6/42), green 19:14 (43/43). Correction: three of those 43 lines (R12b, R13b, R14b) could not fail, and they also "passed" in the red runs; found by review 1, replaced in harness 2 |
| Self-test, harness 2 | DONE: red 19:49 (16/27 against the old Python code), green 19:55 `SELFTEST PASS 67/67` (`out\job3\runs\selftest\GREEN5.log`) |
| Review 1 of the harness | DONE 19:41, "with fixes"; all findings dispositioned in `REVIEW_LOG.md` |
| Pins, 13 per executable | DONE 19:25: MATCH 13/13 for LOCK, LOCKCOPY, LOCKEQ, EVL, PCM, CKL, WNP, KPC, BUN |
| Perft divide, ten runs on eight positions, every root move | DONE 19:25: all nine tags equal to the lock; lock totals equal the published values where one exists |
| Warm transcript (101 searches, 1,677 lines, depth 16 and 12) | DONE 19:24: identical for all tags; bench 13 still the pin afterwards |
| Threads 2-4 soak (78 searches of 1,000,000 nodes per executable) | DONE 19:24: STABLE for all tags (stability only, no node identity) |
| Edge suite built: 410 legal entries, 17 rejected, 4 unreachable | DONE 19:35; oracle validated on published perft counts and on wrong labels |
| Edge suite run, harness 1 (search depth 12) | DONE 19:40: all tags MATCH. Being rerun with harness 2 at the end of chain A |
| Search signatures on 20,000 corpus positions, depth 7, net on and off (release exes) | DONE 19:50: identical for all six candidates |
| Coverage of each candidate's changed lines | DONE 20:02: every instrumented line in every candidate's `#if` region executed (EVL 16/16, PCM 1/1, CKL 8/8, WNP 3/3, KPC 28/28, BUN 25/25) |
| Fuzz, auxiliary tier, harness 2, chunks 0-199 (target 20,000,000 per candidate) | RUNNING since 19:58 (chain A); chunks 0-99 done 20:16 with every row OK, chunks 100-199 running, about 11 s per chunk |
| Cache-state variants, cross-tier check, edge suite, harness 2 | QUEUED behind the auxiliary fuzz in chain A |
| Fuzz, release executables, harness 2 with tie, chunks 0-199 | RUNNING since 19:58 (chain R); chunk 24 at 20:15 with every row OK, about 43 s per chunk |
| WITNESS_NOPIN targets (1,792 constructed stalemates with a pinned pawn push) | DONE 20:06: all tags MATCH 1,792 of 1,792; included in the coverage inputs |
| Pins, divide, warm, soak repeated with the final driver (chain C) | DONE 20:21: pins MATCH 13/13, divide MATCH 10/10, warm MATCH (101 searches, 1,677 lines), soak STABLE, for all nine tags (`out\job3\logs\h2_release_summary.log`) |
| Search signatures on 100,000 corpus positions, depth 7, both nets (chain C) | RUNNING since 20:21; EVL and PCM net on identical so far |
| Report controls L1 to L5 (counting, binding to the frozen binaries, verdict rule, self-test line, replay) | Red run 20:28 `RED4.log` FAIL 0/5 against a counter and a verdict that cannot refuse; 5/5 against the real code; the full self-test (`GREEN6.log`) is run when an engine slot is free |
| Replay of counted ledger rows (`harness\replay.py`) | PENDING: after chain A, a sample of rows of both tiers |
| Review 2a (runners and report generator, read-only reviewer on another model) | STOPPED 20:34 on the owner's instruction "no subagents allowed" (they cost tokens); it had returned no finding. No subagent is started any more. |
| Review 2 as a self-review by the main agent (runners, report generator, PROOF.md against the evidence) | RUNNING; findings so far are fixed in `report.py`, `proof_template.md`, `README.md` (commit `728317e6` and later) |
| Final reports, manifest, DONE | PENDING |

## Verdicts so far

None. Zero differences so far in every check. No candidate is PASS before its auxiliary count reaches 20,000,000 with harness 2.

## Rulings made while executing

1. **Ledger.** The executing-plans skill wants its own helper scripts and a ledger under `.superpowers\`. I follow its method but keep the record in this file and did not run the scripts: they are unread code that would call git outside the `GIT_NO_LAZY_FETCH` and pinning rules. Cost if wrong: another executor resumes from this file instead of the skill's ledger.
2. **Launcher before its test.** `pin_run.ps1` and `job3_env.ps1` were ported from job 2's launcher before their tests were written; the four launcher tests were then run and read. Cost if wrong: none found.
3. **Dump in Python.** The plan listed a `dump` subcommand of the probe. It is `mg_format.py TRANSCRIPT` instead, so the fields have one code path. Cost if wrong: none.
4. **Fixture corrections.** Self-test fixtures that left a perft block inconsistent, or that used a stub printing made-up blocks, were replaced by fixtures cut from real lock output; the inconsistent block stays as its own control.
5. **Missing last record is MALFORMED** when the trailer announces more records than are present; a candidate that stops early with a consistent trailer is MISMATCH.
6. **Edge bases in Python.** The bases are `harness\edge_bases.py`, not a TSV, to avoid delimiter mistakes; the generated suite is `suite\edge_suite.tsv`.
7. **Corpus in two parts.** Chunks 0-99 use seeds `v1` (start position, 8 bench positions, fens12k, 33 edge positions known before the suite existed); chunks 100-199 use seeds `v2` (the same with all 410 legal suite entries). Both seed files are identified by sha256 in every ledger row. Cost if wrong: none; both parts are in the corpus definition.
8. **Fuzz started before review 1 returned**, to use the idle core. Consequence taken: when the review changed the probe, every counted run was started again with harness 2; the earlier results stay under `runs\h1` and are not counted.
9. **No mutants.** Review 1 suggested mutated probes to show sensitivity. The job forbids editing engine source and altering engine binaries for controls; a mutated copy is too close to that line to take without the owner. Line coverage of the unchanged source is used instead. Cost if wrong: sensitivity is shown by reach, not by a caught planted fault.
10. **Release-exe fuzz may reach 20 million too.** The pilot showed about 10,000 to 20,000 positions per second per executable, far above my estimate, so the release-exe tier is run on all 200 chunks instead of the planned minimum of 10. Decision D2 is unchanged: the count that decides is the auxiliary one.
11. **Receipts of harness version 1 and 2 of `checks_release.py`.** Version 2 only raised the warm depths and the soak node budget; the pins and divide code is the same. LOCK's pins and divide receipts carry version 1, the others version 2 for divide.

## Disk and processes

D: 31.84 GiB free at 20:16 (floor 30.3). Transcripts are compared in memory. Live processes of this job at 20:30, Python process ids: 15388 (fuzz.py uci v1 0-99); 392 (fuzz.py aux v2 100-199); 14700 (fuzz.py search v1 0 100000 7); each has a PowerShell launcher as parent and one probe or engine child at a time. Affinity 0x78 and Idle priority were read back from every one of them at 20:17. Machine: cores 4-6 at 97-100 % from the live gate (read 18:07), so the work effectively runs on core 3.

## Skills, servers, tools

Used: superpowers brainstorming, writing-plans, executing-plans, test-driven-development, requesting-code-review; forge-uci `pc_status` (read-only). Not used: forge-uci `bench`, `perft`, `pin_check` (they run on cores 0-1, outside this lane). Suggestion, not installed: a chess rules library under a permissive licence would spare the hand-written oracle.

## Next action

Wait for chain A (auxiliary fuzz to chunk 199, cache-state variants, cross-tier, edge suite), chain R and chain C; finish the self-review; then `selftest.py` (log `runs\selftest\GREEN6.log`), `replay.py` on a sample of rows, `fuzz.py keys v1:0-99 v2:100-199`, `fuzz.py count`, `coverage.py`, `report.py`, manifest, commit and push. No subagents (owner's instruction of 20:34).

## Resume commands

```powershell
. D:\forge_jobs_20261109\fable2\repo\fable_movegen_proof\scripts\job3_env.ps1
$H = "$J3_PACK\harness"; $L = "$J3_PACK\scripts\pin_run.ps1"
# where the fuzz stands (reads the ledgers only)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $L -Exe $J3_PY -ArgLine "-I -B $H\fuzz.py count"
# continue the auxiliary tier (finished chunks are skipped: one row per candidate and chunk counts once)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $L -Exe $J3_PY -ArgLine "-I -B $H\fuzz.py aux v1 0-99"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $L -Exe $J3_PY -ArgLine "-I -B $H\fuzz.py aux v2 100-199"
# continue the release-exe tier
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $L -Exe $J3_PY -ArgLine "-I -B $H\fuzz.py uci v1 0-99"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $L -Exe $J3_PY -ArgLine "-I -B $H\fuzz.py uci v2 100-199"
# self-test (about one minute)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $L -Exe $J3_PY -ArgLine "-I -B $H\selftest.py"
```
