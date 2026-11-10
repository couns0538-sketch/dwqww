# STATUS: job 3, move-generator proof (Fable 5.2)

Written 2026-11-10 20:58 Vienna. All times are Europe/Vienna. Read this file first when resuming, then compare it with the files and processes that actually exist.

## State in one paragraph

No check has found a difference between any candidate and the lock, and every required gate is complete for all six candidates: self-test, 13 pins, perft divide, edge suite, warm transcript, Threads soak, cache-state variants, the tie between each probe and its release executable, and 20,000,000 compared positions per candidate on the auxiliary tier. The verdict for EVL, PCM, CKL, WNP, KPC and BUN is therefore PASS under the two-tier rule the owner chose (decision D1): the checkers bitboard and the static eval were compared on auxiliary probes, because the release executables do not print them. One run is still going: the release-executable fuzz, which decision D2 does not require to reach 20 million; it stood at 7.7 to 7.8 million per candidate at 20:53 and continues to chunk 199. A PASS does not authorise a lock change.

## Verdicts (`evidence/VERDICTS.json`, generated 20:53 by `harness\report.py`)

| Candidate | Verdict | Tier A, auxiliary probes, all fields | Tier R, release executables, move lists (still running) | Differences |
|---|---|---|---|---|
| EVL: EVADE_LEGAL | PASS (two tiers) | 20,000,000 | 7,800,000 | 0 |
| PCM: PAWN_CAPMASK v2 | PASS (two tiers) | 20,000,000 | 7,800,000 | 0 |
| CKL: CHECKERS_KL v3, mode 1 | PASS (two tiers) | 20,000,000 | 7,700,000 | 0 |
| WNP: WITNESS_NOPIN | PASS (two tiers) | 20,000,000 | 7,700,000 | 0 |
| KPC: KING_PAWN_CACHE v2 | PASS (two tiers) | 20,000,000 | 7,700,000 | 0 |
| BUN: BUNDLE3 | PASS (two tiers) | 20,000,000 | 7,700,000 | 0 |

First mismatch: none. `out\job3\fail` is empty.

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
| Branch | `fable52-movegen-proof-20261110`, started from `08897a88e11c707c0ac4e39c19e44c06e1360bdd` (tip of job 2) |
| Commits of this job | `47556eaf`, `c2bc8e0b`, `1fd97049`, `728317e6`, `7994cb82`, then the commit that holds this file; each was pushed when made |
| Pack on the branch | `fable_movegen_proof\` |
| Output root | `D:\forge_jobs_20261109\fable2\out\job3` (`bin`, `src`, `aux` = harness-1 probes, `aux2` = harness-2 probes, `runs`, `runs\h1` = harness-1 results, `tmp`, `logs`, `fail`, `corpus`) |
| Plan | approved by Couns 2026-11-10 18:57; decisions D1 (two-tier PASS) and D2 (20 million on the auxiliary tier) answered 18:15 |
| git | promisor clone, sparse and non-cone; pattern `/fable_movegen_proof/` added locally; `GIT_NO_LAZY_FETCH=1` in every shell |

## Frozen inputs (`out\job3\runs\freeze\INPUTS.json`, written 19:00; hashed again 20:53 by `scripts\verify_evidence.ps1`)

All six supplied MD5s matched. Every source tree matched its build's `SOURCE_INPUTS.sha256` file by file.

| Tag | Release exe MD5 | SHA256 | Source manifest sha256 | Meaning of ON |
|---|---|---|---|---|
| LOCK | `c0051c99695f48bf93272d96fe7548c3` | `e1284f7fc492c8fe1285797fdae8988cf2f2926b33fcfee7023d284d67d8802e` | `3389cfe3dc7bb3989cfebfbdc8ac13d3785b71f090257664d04a0d7c74137645` | reference |
| LOCKEQ | `c8084074dc8180f6e6b62e7013cf5b4b` | `74bb3cfa3121bc2e260406b24409fbb2c0eeb760fa3bc413d524bdcf04ab9f9b` | `d4ded828c5c7ded02759cab7e29dccced836add95f5c6b631792692c82a3c355` | BUNDLE3 tree, all switches 0 (control) |
| EVL | `35781e5cac204370584ff4cb1f5ee93e` | `b89df40fce1726e316e7fb8e3348866401bd86a406aa689e9967f4a487c30237` | `48dee946a6bc9f12506bfccc68b1f52b9c96604e205c0d776db823afb26b905a` | `src\board.cpp:721 #define FORGE_SPD_EVADE_LEGAL 1` |
| PCM | `2cd6d44845e343f8b206b60f876c2165` | `a60aa7cff6163b172dc4e0c88afffa41516c70b8722ce600817ff39c5feb482e` | `c579dc5a94bbbd200084a7a4863ff4903f12b525660d51c0d4d25716437025c4` | `src\board.cpp:441 #define FORGE_SPD_PAWN_CAPMASK 1` |
| CKL | `8a159aed19f0d1ff0a9ee468e279794f` | `c643808f19905387cc5b6328f2c464d63208579998777257b179762b33869dbd` | `fad9288b078986062d50795e5179e573aa16463b630ee1fea03421d441f08139` | `src\board.cpp:1009 #define FORGE_SPD_CHECKERS_KL 1` (mode 1; mode 2 never built or run) |
| WNP | `1bf0291be0b2936c394c9a908f7432fe` | `5c8f0ec88a73dc7c1049d47a7a69724f2079834a6c4cd47df61f8308287b478b` | `16fc5e4cc5277f34c123b1e5c2fcc363067f17528eeedf2896538ff9ccc61d39` | `src\board.cpp:703 #define FORGE_SPD_WITNESS_NOPIN 1` |
| KPC | `55e1fe1230b5d19bd5382636a86f9c90` | `67eea5dc9d0deb59c2248c6488ab70c6aa5e22a01d247d2497f2454a8083d4aa` | `01ecdea868e81ac734eaf61030fa4d1b262572f7253bd0e1554f057edad34fb6` | `include\forge\eval.hpp:17 #define FORGE_SPD_KING_PAWN_CACHE 1` |
| BUN (BUNDLE3) | `ec5dc9d16897fe00f9e788edd9707180` | `db12981c4c840be4e9a93f04e88f12b1d7e90beb11f73070d0df9c316cc17d3c` | `d4ded828c5c7ded02759cab7e29dccced836add95f5c6b631792692c82a3c355` | `-DFORGE_SPD_EVADE_LEGAL=1 -DFORGE_SPD_PAWN_CAPMASK=1 -DFORGE_SPD_CHECKERS_KL=1` on a tree whose defaults are 0; patch md5 `ba2fcf2e78a0e2c85964a1e6e258d150`; not rebuilt; pin-equivalent, not byte-identical |

Other inputs: `fens_12k_v2.txt` md5 `e7dbf2c8151188c03ef52054557a531e`, sha256 `c01c0e6a49fb9aaab535058bd7280c33b8735e0f8bd40834f1c029843a75a265`; compiler `clang++.exe` sha256 `d05fee2c3f79b15d998d3c3413c76aabd416ec789edff89c8f698a8be44a3970`; Python 3.15.2. Net identity: `src/nnue_weights.inc` sha256 `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638` in every tree, `FORGE_NNUE_HIDDEN=256`, residual net.

Not tested, by name: QA's `build_v3\BUN` (the five-flag `BUNDLE`, md5 `59e18b7b...`) and `BN4`.

## Auxiliary probes, harness 2 (`out\job3\aux2\<TAG>\AUX_RECEIPT.json`, built 19:46 to 19:48)

Harness source `mgprobe.cpp` sha256 `42efd61dd819eb7dda65546fb1344dc408850fe6ef4f01bea75873704a70786d` (frozen copy beside each probe). Effective candidate switches as the preprocessor reports them:

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

The six files that produced the counted fuzz rows (`mgprobe.cpp`, `mg_format.py`, `mg_compare.py`, `uci_session.py`, `fuzz.py`, `pinguard3.py`) have the combined sha256 `a234987c31fdbb18082ab1462ed157f482478a6f30705f09a2e57d4c1a46a3a7` and are unchanged since commit `1fd97049`.

## Options, net modes and seeds

| Check | Options |
|---|---|
| Pins | Threads 1, Hash 16, OwnBook false; one process with UseNNUE true (bench 11/13/16/20/22), one with UseNNUE false, one for the three perft pins |
| Perft divide | Threads 1, Hash 16, OwnBook false; `go perft 5` or `6` |
| Warm transcript | Threads 1, OwnBook false; Hash 16, then 1, 64, 16; UseNNUE true, false, true; `go depth 16`, `17` and `12` |
| Threads soak | Threads 2, 3, 4, 3, 2, 4; Hash 16 per thread; OwnBook false; UseNNUE true; `go nodes 1000000` and `go infinite` with `stop` |
| Edge suite and fuzz on the release executables | Threads 1, Hash 16, OwnBook false; `go perft 1` and `go perft 2` (perft does not use the net) |
| Search signatures | Threads 1, Hash 16, OwnBook false; UseNNUE true and false; `go depth 7` on the corpus, `go depth 12` on the edge suite |
| Auxiliary probes | every record holds the static eval with the net off and with the net on (refresh and incremental) |

Fuzz corpus: master seed `4D47465A20261110`; chunk seed = master xor (chunk + 1) x `9E3779B97F4A7C15`, through SplitMix64 into xoshiro256**; 100,000 visited positions per chunk; chunks 0-99 from `out\job3\corpus\seeds_v1.txt` (sha256 `ab6c66fb36f4fa77325bb97f5b15135094d8209405ade1e8234d78d8511f71eb`), chunks 100-199 from `seeds_v2.txt` (sha256 `a9e7455332183ac8a0452f757e39fe1f1a429ad2ee320e467a898e557ddd4cd4`). Selection rules are in the two `seeds_*.json` receipts and in PROOF.md section 7. Self-test fixtures use their own master seed `5E1F7E5720261110`.

## Checks

| Check | Result |
|---|---|
| Launcher tests, freeze, observability record | DONE 19:00 to 19:02 |
| Self-test | `SELFTEST PASS 72/72` at 20:52 (`out\job3\runs\selftest\GREEN7.log`), run after the last change to the report generator. Red runs: 19:09 (4/20), 19:11 (6/42), 19:49 (16/27), 20:28 (0/5, report controls). Attempts that still failed while the harness was written are kept and explained in PROOF.md section 3. Correction of an earlier statement: three of the 43 controls of harness 1 (R12b, R13b, R14b) could not fail; found by review 1 and replaced |
| Review 1 (independent, another model) | DONE 19:41, "with fixes"; all findings dispositioned in `REVIEW_LOG.md` |
| Review 2 | The independent review was stopped at 20:34 on the owner's instruction (no subagents) before it reported. Done as a self-review by the main agent; findings S1 to S11 in `REVIEW_LOG.md`, all fixed or explained |
| Pins, 13 per executable | MATCH 13/13 for LOCK, LOCKCOPY, LOCKEQ, EVL, PCM, CKL, WNP, KPC, BUN (19:25; repeated with the final driver 20:10 to 20:16, same result) |
| Perft divide, ten runs on eight positions, 216 root moves | every count equal to the lock's for all eight other executables; lock totals equal the published values where one exists (repeated 20:16) |
| Warm transcript, 101 searches, 1,677 lines | identical to the lock's for all eight other executables; bench 13 still the pin afterwards (repeated 20:17) |
| Threads 2-4 soak, 78 searches per executable | STABLE for all nine (stability only, no node identity) (repeated 20:18 to 20:21) |
| Edge suite: 410 legal entries, 17 rejected, 4 unreachable | MATCH for LOCKCOPY, LOCKEQ and the six candidates with harness 2 at 20:40 to 20:42: 14,220 probe records and 7,725 perft blocks per tag; lock equal to the oracle on all 410 entries. The harness-1 run of 19:40 gave the same result |
| Fuzz, auxiliary tier | DONE 19:58 to 20:35: 20,000,000 compared positions per candidate, 1,200 rows, all OK |
| Cache-state variants | DONE 20:35 to 20:39: chunks 0-4 and 100-104, two variants, 120 rows, all OK |
| Probe against its own release executable | DONE 20:39: identical move lists on 2,000 positions for LOCK, LOCKEQ and the six candidates |
| Fuzz, release executables, with the tie to the lock probe | RUNNING since 19:58: 7.7 to 7.8 million per candidate at 20:53, all rows OK |
| Search signatures, 100,000 corpus positions, depth 7, net on and off | DONE 20:21 to 20:49: identical for all six candidates (supplementary) |
| Coverage of each candidate's changed lines | DONE 20:02 (WNP again 20:06 with the targets): every instrumented line of every `#if` region executed |
| WITNESS_NOPIN targets, 1,792 constructed positions | DONE 20:06: MATCH for LOCKEQ and the six candidates (supplementary) |
| Replay of counted ledger rows | DONE 20:42 to 20:46: 36 rows of tier A (chunks 0, 57, 99, 100, 143, 199) and 12 rows of tier R (chunks 3, 31) reproduced with every hash equal |
| Distinct positions of the corpus | 17,595,079 distinct by position key among 20,000,000 visited; 1,746,584 in check |
| Independent recount (`scripts\verify_evidence.ps1`, no code shared with the Python harness) | `VERIFY EVIDENCE OK 19/19` at 20:53 |
| Final report, manifest, DONE, push | the commit that holds this file has the state of 20:58; repeated when the release-executable fuzz has finished |

## What the release executables expose (`out\job3\runs\observe\out_LOCK.txt`)

`d`, `eval`, `checkers`, `moves`, `legalmoves` and `help` were sent to the lock exe: it printed nothing for them. `go perft 1` prints the legal moves in generation order. So legal moves and their order are observable on the release executables; the checkers bitboard and the static eval are not. Those two fields are compared on auxiliary probes (decision D1).

## Rulings made while executing

1. **Ledger.** The executing-plans skill wants its own helper scripts and a ledger under `.superpowers\`. I follow its method but keep the record in this file and did not run the scripts: they are unread code that would call git outside the `GIT_NO_LAZY_FETCH` and pinning rules. Cost if wrong: another executor resumes from this file instead of the skill's ledger.
2. **Launcher before its test.** `pin_run.ps1` and `job3_env.ps1` were ported from job 2's launcher before their tests were written; the four launcher tests were then run and read. Cost if wrong: none found.
3. **Dump in Python.** The plan listed a `dump` subcommand of the probe. It is `mg_format.py TRANSCRIPT` instead, so the fields have one code path. Cost if wrong: none.
4. **Fixture corrections.** Self-test fixtures that left a perft block inconsistent, or that used a stub printing made-up blocks, were replaced by fixtures cut from real lock output; the inconsistent block stays as its own control.
5. **Missing last record is MALFORMED** when the trailer announces more records than are present; a candidate that stops early with a consistent trailer is MISMATCH.
6. **Edge bases in Python.** The bases are `harness\edge_bases.py`, not a TSV, to avoid delimiter mistakes; the generated suite is `suite\edge_suite.tsv`.
7. **Corpus in two parts.** Chunks 0-99 use seeds `v1` (start position, 8 bench positions, fens12k, 33 edge positions known before the suite existed); chunks 100-199 use seeds `v2` (the same with all 410 legal suite entries). Cost if wrong: none; both parts are in the corpus definition.
8. **Fuzz started before review 1 returned**, to use the idle core. Consequence taken: when the review changed the probe, every counted run was started again with harness 2; the earlier results stay under `runs\h1` and are not counted.
9. **No mutants.** Review 1 suggested mutated probes to show sensitivity. The job forbids editing engine source and altering engine binaries for controls; a mutated copy is too close to that line to take without the owner. Line coverage of the unchanged source is used instead. Cost if wrong: sensitivity is shown by reach, not by a caught planted fault.
10. **Release-exe fuzz on all 200 chunks.** The pilot showed far more positions per second than estimated, so the release-exe tier is run on the whole corpus instead of the planned minimum of 10 chunks. Decision D2 is unchanged: the count that decides is the auxiliary one.
11. **Release checks repeated.** Pins, divide, warm and soak were run again for all nine tags with the final `checks_release.py` (version 2 raised only the warm depths and the soak node budget), so every receipt carries the same version.
12. **No subagents after 20:34.** The owner wrote "no subagents allowed" (they cost tokens). The running reviewer was stopped and review 2 was done by the main agent. Cost: the second review is not independent; PROOF.md states that as a limit. The instruction was not saved in the assistant's memory folder, because that folder is on C: and this job may create no file there; it is recorded here instead.
13. **The tie between probe and executable is a gate.** The plan listed the cross-tier check as a test of task 1; a PASS now depends on it, because the auxiliary tier only speaks for a release executable if both list the same moves.
14. **Tools added beyond the plan:** `harness\replay.py` (runs a counted ledger row again and compares every hash) and `scripts\verify_evidence.ps1` (independent recount in PowerShell). Both only read results; they change no ledger.

## Disk and processes

D: 32.17 GiB free at 20:52 (floor 30.3); the job's folder holds about 125 MiB. Transcripts are compared in memory. Live processes of this job at 20:58: the release-executable fuzz only (Python process id 15388, `fuzz.py uci v1 0-99`, with a PowerShell launcher as parent and one engine child at a time; it is followed by `fuzz.py uci v2 100-199` from the same launcher). Affinity 0x78 and Idle priority were read back from every process of the job at 20:42. Machine: the live gate uses cores 4-6; at 20:51 core 3 was at 98 % from this job and cores 4, 5, 6 at 59, 41 and 4 %.

## Skills, servers, tools

Used: superpowers brainstorming, writing-plans, executing-plans, test-driven-development, requesting-code-review (review 1), verification-before-completion; forge-uci `pc_status` (read-only). Not used: forge-uci `bench`, `perft`, `pin_check` (they run on cores 0-1, outside this lane); subagents after 20:34. Suggestion, not installed: a chess rules library under a permissive licence would spare the hand-written oracle.

## Next action

Wait for the release-executable fuzz to reach chunk 199 (it reports by itself). Then: replay two of its seeds-v2 chunks, `report.py`, `verify_evidence.ps1`, update this file, `make_manifest.ps1` and `make_manifest.ps1 -Verify`, commit and push. If the session ends first, the state committed with this file is a complete handoff with the release-executable count as it stood, and the commands below continue it.

## Resume commands

```powershell
. D:\forge_jobs_20261109\fable2\repo\fable_movegen_proof\scripts\job3_env.ps1
[void](J3-Pin 0x78)
$H = "$J3_PACK\harness"; $L = "$J3_PACK\scripts\pin_run.ps1"
function Py($a) { powershell.exe -NoProfile -ExecutionPolicy Bypass -File $L -Exe $J3_PY -ArgLine "-I -B $a" }
Py "$H\fuzz.py count"                      # where the fuzz stands (reads the ledgers only)
Py "$H\fuzz.py uci v1 0-99"                # continue the release-exe tier; finished chunks are skipped and nothing counts twice
Py "$H\fuzz.py uci v2 100-199"
Py "$H\replay.py uci v2 150 EVL,PCM,CKL,WNP,KPC,BUN"   # run counted rows again and compare every hash
Py "$H\selftest.py"                        # harness controls, about one minute
Py "$H\report.py"                          # evidence folder, tables, verdicts, PROOF.md
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $J3_PACK\scripts\verify_evidence.ps1    # independent recount
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $J3_PACK\scripts\make_manifest.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $J3_PACK\scripts\make_manifest.ps1 -Verify
```
