# STATUS: job 3, move-generator proof (Fable 5.2)

Written 2026-11-10 19:16 Vienna. All times are Europe/Vienna. Read this file first when resuming, then compare it with the files and processes that actually exist.

## State in one paragraph

Inputs are frozen and hash-checked, the auxiliary probe for the lock is built, and the harness self-test passes 43 of 43 controls. No candidate has been judged yet. The six candidate probes are building. Next come the harness review, pins and perft divide, the edge suite, warm and Threads checks, then the fuzz.

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
| Pack on the branch | `fable_movegen_proof\` |
| Output root | `D:\forge_jobs_20261109\fable2\out\job3` (`bin`, `src`, `aux`, `runs`, `tmp`, `logs`, `fail`, `corpus`) |
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

## What the release executables expose (`out\job3\runs\observe\out_LOCK.txt`)

`d`, `eval`, `checkers`, `moves`, `legalmoves` and `help` were sent to the lock exe: it printed nothing for them. `go perft 1` prints the legal moves in generation order. So legal moves and their order are observable on the release executables; the checkers bitboard and the static eval are not. Those two fields are compared on auxiliary probes (decision D1).

## Checks

| Check | State |
|---|---|
| Launcher: child inherits mask 0x78 and Idle; subset 0x08; disk-guard refusal (exit 95); mask outside the lane refused (exit 94) | DONE 19:00, all as required |
| Freeze and hash check | DONE 19:00 |
| Observability record | DONE 19:02 |
| LOCK probe built | DONE 19:06, sha256 `b111ea4f3637adf46bd2d1d10a236ce27ec1c3b0fba256b66a0399bad837f50b`, harness `mgprobe.cpp` sha256 `79324eabf56d94df37d10ce5465b79117c8a948726642c9782a955bf4e2f4cc0` |
| Self-test, red runs | DONE 19:09 and 19:11: against stub comparators 4/20 and 6/42 (every negative control failed, as it must) |
| Self-test, green | DONE 19:14: `SELFTEST PASS 43/43` (`out\job3\runs\selftest\GREEN2.log`) |
| Candidate probes (EVL, PCM, CKL, WNP, KPC, BUN) | RUNNING since 19:14 (one background shell, sequential) |
| Review 1 of the harness | PENDING |
| Pins, perft divide | PENDING |
| Edge suite | PENDING |
| Warm states, Threads soak | PENDING |
| Fuzz, auxiliary tier (target 20,000,000 per candidate) | PENDING, 0 done |
| Fuzz, release executables | PENDING, 0 done |

## Verdicts so far

None. No candidate has been compared yet.

## Rulings made while executing

1. **Ledger.** The executing-plans skill wants its own helper scripts and a ledger under `.superpowers\`. I follow its method (inline, test-first, rulings recorded, fresh review) but keep the record in this file and did not run the scripts: they are unread code that would call git outside the `GIT_NO_LAZY_FETCH` and pinning rules. Cost if wrong: another executor resumes from this file instead of the skill's ledger.
2. **Launcher before its test.** `pin_run.ps1` and `job3_env.ps1` were ported from job 2's launcher before their tests were written; the four launcher tests were then run and read. Cost if wrong: none found; the tests pass.
3. **Dump in Python.** The plan listed a `dump` subcommand of the probe. It is `mg_format.py TRANSCRIPT` instead, decoding the `run` transcript, so the fields have one code path. Cost if wrong: none; same data.
4. **Fixture correction.** Two self-test fixtures (one move line removed, one count changed) left the block's `nodes` total inconsistent, which no engine prints; the comparator rightly called them malformed. The fixtures now keep the block consistent and are caught as mismatches; the inconsistent block stays as its own control (R4b).
5. **Missing last record is MALFORMED.** A transcript whose trailer announces more records than are present is classed as missing output, not as a candidate difference.

## Disk and processes

D: 31.97 GiB free at 19:00 (floor 30.3). Transcripts are compared in memory; `out\job3` holds about 60 MiB. Live processes of this job: the probe build shell (started 19:14). Machine: cores 4-6 at 97-100 % from the live gate (read 18:07), so the work effectively runs on core 3.

## Skills, servers, tools

Used: superpowers brainstorming, writing-plans, executing-plans, test-driven-development; forge-uci `pc_status` (read-only). Not used: forge-uci `bench`, `perft`, `pin_check` (they run on cores 0-1, outside this lane). Suggestion, not installed: a chess rules library under a permissive licence would spare the hand-written oracle.

## Next action

Wait for the candidate probe builds, check that the seven probe hashes are pairwise different, then run pins and perft divide (`harness\checks_release.py`, being written).

## Resume commands

```powershell
. D:\forge_jobs_20261109\fable2\repo\fable_movegen_proof\scripts\job3_env.ps1
# self-test (about one minute)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $J3_PACK\scripts\pin_run.ps1 -Exe $J3_PY -ArgLine "-I -B $J3_PACK\harness\selftest.py"
# rebuild one probe (refuses to overwrite: move the old folder under out\job3\aux first)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $J3_PACK\scripts\build_aux.ps1 -Tag EVL
```
