# Item B draft - the tuned exe (tag tuned184) from the SPSA session stc8_main at 184 pairs

Written 2026-11-04 from 13:48 PC clock (= Vienna), last edit 13:52:10; every other time below is a log stamp (build
log, kit outs, checks_itemB). No Elo claim and no convergence claim: the crew gates (UHO [0,5] SPRT, then the
8moves_v3 confirm).

## 1. Deliverable
| item | value |
|---|---|
| exe pc1 (the gate exe) | `D:\o30\w\tuned184_pc1\src_copy\forge_ltopgo_tuned184_pc1.exe` |
| exe pc2 (the clean rebuild) | `D:\o30\w\tuned184_pc2\src_copy\forge_ltopgo_tuned184_pc2.exe` |
| sha256 pc1 = pc2 (binding) | 3b35f5cfa662f4f09916fa9c4b40f6bfc6a6d0d4ce7fa1f1b8f6970daadb66d1 |
| patch | `D:\o30\wt\opus_30h\b\o30tuned_tuned184.patch` (branch path `opus_30h/b/o30tuned_tuned184.patch`), md5 eaa42c9fb3806a884c46a6f635548b93 |
| scratch repo | `D:\o30\repos\tuned184` = clone of `D:\o30\repos\spsa` (expose22, head deabbd2) + 1 commit 574b018 ("O30Tuned: one switch for the tuned set") |
| what the switch does | UCI `option name O30Tuned type check default false`; `true` = the 8 tuned values of TUNED_OPTIONS.txt, `false` = the lock values (the start column of the run's params.csv), each clamped to its option range, then tune::refresh(); untouched = the expose22 exe = the lock pins |
| inputs | `D:\o30\spsa\report_184pairs\TUNED_OPTIONS.txt` md5 5b1097b872cefcb1700ec2984f24e09a; `D:\o30\spsa\stc8_main\params.csv` md5 b837b7754254c8a6954bd4f6d84726c8; `D:\o30\spsa\report_184pairs\REPORT.md` md5 5db42aaec5704137b5fade83e3fae21c |
| kit | QA's LTO+PGO kit v2.3 -Expose, CPUs 0-1 (`tools/kit_build_o30.sh`), OFF pins + perft pins per side, node identity plain = ltopgo |

## 2. Every check (result, log path)
| check | result | log |
|---|---|---|
| preparation (read-only, 12:3x): spsa repo head deabbd2, 0 changed files; TUNED_OPTIONS.txt = REPORT.md "end (int)" = gate_options.txt for all 8 (round-to-nearest of the end thetas), every value inside its CSV range, the CSV start = the REPORT start; games = 2 x pairs, W+L+D = games; beyond-2-sigma file = the table's | PASS (TUNED_VS_REPORT PASS) | `D:\o30\checks_itemB\prep.log`, `D:\o30\checks_itemB\prep_tuned_vs_report.txt` |
| start gate: no forge-v2-bullet / fastchess / forge_ltopgo* with CPU 0 or 1 in its affinity mask (polled every 60 s, nothing touched; the 14:10 clock condition was dropped by the coordinator at 13:27 - the first waiter with that condition, `wait_cpu01.log`, was left to expire; at 13:27:45 the only blocker was forge_ltopgo_v2p4_pc1 pid 1920 on mask 0x1, the play-check probe) | CLEAR at 13:40:05 (polls 13:28:05 - 13:39:05 each saw one blocker: a forge_ltopgo_v2p4_pc1 probe on mask 0x1 with a new pid every minute; nothing touched) | `D:\o30\checks_itemB\wait_cpu01_v2.log` (superseded: `wait_cpu01.log`) |
| build_o30tuned.sh tuned184: clone, o30_tuned_patch.py, commit, cleanroom_lint, kit pc1 + pc2, test_o30tuned.sh | exit 0, 13:40:43 - 13:44:34 (the script pinned itself to Idle / mask 0x3; clone deabbd2 -> commit 574b018; "O30Tuned added ... (8 values, CRLF)"; lint CLEAN; kit pc1 13:40:48 - 13:42:15, pc2 13:42:20 - 13:43:51; PC1 = PC2: PASS; O30TUNED PASS) | `D:\o30\logs\build_o30tuned_tuned184.out` |
| kit pc1: OFF pins d11-d22 + perft, node identity plain = ltopgo, warnings | RESULT PASS 13:42:15: bench d11-d22 and both perfts = the lock pins, node identity plain = ltopgo ALL OK (8 FENs), compiler warning lines plain 0 / ltopgo 1 with real missing-profile / coverage warnings 0 (the same line as the sp1 build), vfmadd 0, -flto on the link line | `D:\o30\w\tuned184_pc1.out` |
| kit pc2: the same on a second clean export | RESULT PASS 13:43:51: the same on the second clean export; exe sha256 identical | `D:\o30\w\tuned184_pc2.out` |
| pc1 = pc2 exe sha256 (binding) | PASS: both 3b35f5cfa662f4f09916fa9c4b40f6bfc6a6d0d4ce7fa1f1b8f6970daadb66d1 (md5 b5339b8538337fbc3e8db7b1146ab3ea) | build log |
| cleanroom_lint on the patch | CLEAN (patches 1): 60 diff lines, one file src/uci.cpp, three hunks (the table in the anonymous namespace, the option line, the setoption handler), no `id` line touched, 0 CR bytes | build log |
| test_o30tuned.sh 1: OFF pins -Full (d11-d22, perft) | PASS | build log |
| test_o30tuned.sh 2: O30Tuned=true bench == explicit option list bench, differs from the lock | PASS: O30Tuned=true d11 330152 / d13 745986 / d16 2436337 = the explicit list's bench; lock 312866 / 862329 / 3024920 | build log |
| test_o30tuned.sh 3: true then false = the lock pins | PASS | build log |
| test_o30tuned.sh 4: advertised by `uci`, invalid value rejected | PASS (`option name O30Tuned type check default false` advertised; value `maybe` -> `info string invalid value for option O30Tuned`) | build log |
| `uci` option list (sorted) vs the SPSA exe sp1 7bf5dab3 | PASS: 83 -> 84 options, the only difference is the added `option name O30Tuned type check default false` (the lock's 61 + the 22 expose22 options unchanged) | `D:\o30\checks_itemB\uci_options_diff.txt` |
| UCI conformance, switch untouched (CPU 1, mask 0x2, Idle) | CONFORMANCE PASS 18 / 18 (13:45:04 - 13:45:07) | `D:\o30\checks_itemB\conformance_off.txt` / `.json` |
| UCI conformance, O30Tuned=true (incl. setoption during go infinite) | CONFORMANCE PASS 21 / 21 (13:45:27 - 13:45:31): option advertised, setoption O30Tuned during go infinite -> readyok 0.02 s, go depth 8 after it legal, every bestmove legal and inside its limit, quit exit 0, stderr empty | `D:\o30\checks_itemB\conformance_on.txt` / `.json` |
| smoke2m 120 s, O30Tuned=true, Threads 2, Hash 16, tc 2000+20, engine-side legality (CPU 1, Idle) | SMOKE2M PASS (13:45:31 - 13:47:31): 21 games (20 finished), 2450 plies, illegal 0, crashes 0, hangs 0, time losses 0, overruns 0, option errors 0, restarts 0, stderr empty, 12 mates / stalemates | `D:\o30\checks_itemB\smoke_on.txt` / `smoke_on.json` / `smoke_on.stderr.txt` |

## 3. SPSA facts (quoted from D:\o30\spsa\report_184pairs\REPORT.md, written by b/spsa_report.py at 10:49)
- "Config: o30 stc8: 8 search constants from the lock values, STC 8+0.08, Threads 1, Hash 16, UHO book; tc 8+0.08,
  book UHO_Lichess_4852_v1.epd, engine `D:\o30\w\sp1_pc1\src_copy\forge_ltopgo_sp1_pc1.exe`."
- "Batches 92, pairs 184 (planned 1800), games 368: +88 -77 =203 (draw rate 55.2%); first batch 2026-11-04 00:05:41,
  last 2026-11-04 02:57:56; terminations {'normal': 368}." "Per-game result variance v = 0.4475."
- Sessions (tuner.log): session 1 on CPUs 0-1 (threads <= 2) 00:05 - 02:49, 182 pairs; session 2 resumed on CPU 1
  (threads <= 1) 02:56 - 02:57:56, 2 pairs, ended by the stop event ("stop: stop requested"). 184 of 1800 planned
  pairs = 10.2 % of the planned schedule.
- Per parameter (start -> end, end rounded = the tuned value; z = move / null-gradient sigma, R9 method):

| parameter | start | end | end (int) | move | move / c_end | null sigma | z | halves same way |
|---|---|---|---|---|---|---|---|---|
| LmrQuietBase | 85 | 80.47 | 80 | -4.53 | -0.25 | 6.67 | -0.68 | yes |
| LmrQuietDivisor | 220 | 215.14 | 215 | -4.86 | -0.20 | 8.90 | -0.55 | yes |
| LmrCutNode | 2048 | 2037.98 | 2038 | -10.02 | -0.03 | 142.35 | -0.07 | no |
| HistoryMalusPercent | 100 | 99.39 | 99 | -0.61 | -0.04 | 5.56 | -0.11 | no |
| NmpEvalBase | 180 | 173.71 | 174 | -6.29 | -0.14 | 16.68 | -0.38 | yes |
| RfpMargin | 72 | 64.97 | 65 | -7.03 | -0.64 | 4.08 | -1.72 | no |
| SeeQuietMultiplier | 24 | 27.91 | 28 | +3.91 | +0.78 | 1.85 | +2.11 | yes |
| SingularDoubleMargin | 24 | 25.14 | 25 | +1.14 | +0.14 | 2.97 | +0.39 | no |

- "Beyond 2 sigma: SeeQuietMultiplier (with 8 parameters about 0.4 pass by chance)." That is the null-noise
  statement: one of eight parameters beyond 2 sigma is what pure noise produces about 0.4 times per 8-parameter run,
  so no convergence claim is possible from 184 pairs; the honest expectation for the set is ~0 Elo until a gate says
  otherwise.
- Convergence table (theta after the batch at that share of the run):

| parameter | 10 % (20 pairs) | 25 % (46 pairs) | 50 % (92 pairs) | 75 % (138 pairs) | 100 % (184 pairs) |
|---|---|---|---|---|---|
| LmrQuietBase | 83.44 | 85.09 | 84.57 | 82.98 | 80.47 |
| LmrQuietDivisor | 217.80 | 215.59 | 217.82 | 217.05 | 215.14 |
| LmrCutNode | 2014.72 | 2049.98 | 2084.19 | 2006.47 | 2037.98 |
| HistoryMalusPercent | 99.58 | 100.05 | 95.13 | 97.29 | 99.39 |
| NmpEvalBase | 178.82 | 174.67 | 178.66 | 179.89 | 173.71 |
| RfpMargin | 70.99 | 69.31 | 64.32 | 65.25 | 64.97 |
| SeeQuietMultiplier | 24.14 | 24.90 | 26.54 | 26.41 | 27.91 |
| SingularDoubleMargin | 23.78 | 24.02 | 23.79 | 24.95 | 25.14 |

- TUNED_OPTIONS.txt (the set the switch holds): LmrQuietBase=80 LmrQuietDivisor=215 LmrCutNode=2038
  HistoryMalusPercent=99 NmpEvalBase=174 RfpMargin=65 SeeQuietMultiplier=28 SingularDoubleMargin=25.
  TUNED_OPTIONS_beyond2sigma.txt: SeeQuietMultiplier=28.

## 4. Gate line for the crew (the tuned set vs the lock)
Engine A: `D:\o30\w\tuned184_pc1\src_copy\forge_ltopgo_tuned184_pc1.exe` (sha256 3b35f5cfa662f4f09916fa9c4b40f6bfc6a6d0d4ce7fa1f1b8f6970daadb66d1, pc1 = pc2) with
`option.O30Tuned=true`; engine B: the lock FD3A5190 (the crew's `forge_push\bin\forge_ltopgo_x_al1s198_v23.exe`,
sha256 fd3a51903e73dc1fa20263f1dcc7a4eec506592e9f25e50b8f8739ca36873072, re-hashed 12:35) with no options. UHO [0,5]
SPRT, then the
8moves_v3 confirm. The exe with the switch untouched = the lock pins (check 1), so A with `O30Tuned=false` or no option
would be a lock-vs-lock gate.
- Same set, no new exe: the SPSA exe `D:\o30\w\sp1_pc1\src_copy\forge_ltopgo_sp1_pc1.exe` (7bf5dab3) with
  `option.LmrQuietBase=80 option.LmrQuietDivisor=215 option.LmrCutNode=2038 option.HistoryMalusPercent=99
  option.NmpEvalBase=174 option.RfpMargin=65 option.SeeQuietMultiplier=28 option.SingularDoubleMargin=25`
  (gate_options.txt); check 2 proves bench(switch) == bench(this list).
- The policy line (skill forge-o30-spsa, FINAL_REPORT section 4 item 2: gate only parameters beyond 2 sigma): the lock
  exe itself with `option.SeeQuietMultiplier=28` vs the lock with no options (SeeQuietMultiplier is one of the 41
  constants the lock exe already advertises under -Expose). One line, not a recommendation: the crew chooses.

## 5. Ready to paste into opus_30h/b/RESULTS.md
```
## Tuned exe for the stc8_main session at 184 pairs (tag tuned184; built 2026-11-04 13:40:43 - 13:44:34, checks to 13:47:31)
No Elo claim, no convergence claim: 184 of 1800 planned pairs (92 batches, 368 games, +88 -77 =203, draw rate 55.2 %),
only SeeQuietMultiplier beyond 2 sigma of the null-gradient noise (24 -> 28, z +2.11; with 8 parameters about 0.4 pass
by chance); report `D:\o30\spsa\report_184pairs\REPORT.md`. The crew gates.
- `build_o30tuned.sh D:\o30\spsa\report_184pairs\TUNED_OPTIONS.txt D:\o30\spsa\stc8_main tuned184` (log
  `D:\o30\logs\build_o30tuned_tuned184.out`): clone of the expose22 repo (deabbd2) -> `D:\o30\repos\tuned184`
  (574b018), patch `b/o30tuned_tuned184.patch` md5 eaa42c9fb3806a884c46a6f635548b93 (cleanroom_lint CLEAN), kit v2.3 -Expose on
  CPUs 0-1 at Idle, pc1 + pc2.
- Exe `D:\o30\w\tuned184_pc1\src_copy\forge_ltopgo_tuned184_pc1.exe` sha256 3b35f5cfa662f4f09916fa9c4b40f6bfc6a6d0d4ce7fa1f1b8f6970daadb66d1 = pc2 (binding);
  kit pc1 / pc2 RESULT PASS (OFF pins d11-d22 + perft, node identity plain = ltopgo ALL OK, real missing-profile / coverage warnings 0, vfmadd 0); `uci` = the SPSA exe 7bf5dab3's option list + O30Tuned.
- The set (O30Tuned=true): LmrQuietBase 85 -> 80, LmrQuietDivisor 220 -> 215, LmrCutNode 2048 -> 2038,
  HistoryMalusPercent 100 -> 99, NmpEvalBase 180 -> 174, RfpMargin 72 -> 65, SeeQuietMultiplier 24 -> 28,
  SingularDoubleMargin 24 -> 25 (false = the lock values; untouched = the expose22 exe).
| check | result |
|---|---|
| kit pc1 / pc2: OFF pins d11-d22 + perft, node identity plain = ltopgo | RESULT PASS / RESULT PASS (sha256 identical) |
| test_o30tuned.sh 1 OFF pins -Full | PASS |
| 2 O30Tuned=true == explicit list, differs from the lock | PASS (d11 330152 / d13 745986 / d16 2436337 both ways; lock 312866 / 862329 / 3024920) |
| 3 true then false = the lock pins | PASS |
| 4 advertised + invalid value rejected | PASS |
| UCI conformance (tools/uci_conformance_o30.py, CPU 1): switch untouched / O30Tuned=true | PASS 18 / 18 / PASS 21 / 21 |
| smoke2m 120 s, O30Tuned=true, Threads 2, Hash 16, tc 2000+20, engine-side legality (CPU 1) | SMOKE2M PASS: 21 games (20 finished), 2450 plies, 0 illegal / crashes / hangs / time losses / overruns / option errors, stderr empty |
Evidence: `D:\o30\checks_itemB\` (prep, waiter, option-list diff, conformance, smoke). Gate line: engine A = the exe
above with `option.O30Tuned=true`; engine B = the lock FD3A5190 (no options); UHO [0,5] SPRT, then the 8moves_v3
confirm. The same set without a new exe: the SPSA exe 7bf5dab3 with the explicit list in
`D:\o30\spsa\report_184pairs\gate_options.txt` (check 2: bench(switch) == bench(list)).
```

## 6. Ready to paste into FINAL_REPORT.md (Item B paragraph, section 0 / section 1)
```
- **Item B (SPSA): a tuned set exists as one switch, but 184 pairs support no convergence claim.** The session
  stc8_main (8 search constants from the lock values, 8+0.08, UHO, Threads 1, Hash 16, Idle on CPUs 0-1) played
  92 batches = 184 pairs = 368 games (+88 -77 =203, draw rate 55.2 %) of the 1,800 planned, 00:05 - 02:58 on
  2026-11-04, then stopped (stop event). Of the 8 parameters only SeeQuietMultiplier moved beyond 2 sigma of the
  null-gradient noise (24 -> 28, z +2.11); with 8 parameters about 0.4 pass by chance, so no convergence claim, and
  the honest expectation for the set is ~0 until a gate says otherwise. Packaged as ONE switch on the expose22 exe:
  `D:\o30\w\tuned184_pc1\src_copy\forge_ltopgo_tuned184_pc1.exe` (sha256 3b35f5cfa662f4f09916fa9c4b40f6bfc6a6d0d4ce7fa1f1b8f6970daadb66d1, pc1 = pc2, kit v2.3 -Expose;
  patch `opus_30h/b/o30tuned_tuned184.patch` md5 eaa42c9fb3806a884c46a6f635548b93): `O30Tuned` default false = the lock pins (d11-d22,
  perft), `true` = the 8 tuned values (bench equal to the explicit option list, differs from the lock), `true` then
  `false` = the lock pins again, an invalid value is rejected (test_o30tuned.sh: O30TUNED PASS 4 / 4; O30Tuned=true bench d11 330152 / d13 745986 / d16 2436337); UCI conformance
  PASS 18 / 18 with the switch untouched and 21 / 21 with O30Tuned=true; 120-s smoke with the switch on PASS: 21 games, 2450 plies, 0 illegal / crashes / hangs / time losses, stderr empty (`D:\o30\checks_itemB\`). Gate line: that exe
  with `option.O30Tuned=true` vs the lock FD3A5190, UHO [0,5] SPRT, then the 8moves_v3 confirm - the crew gates; no
  Elo claim.
```

## 7. Notes for the main session
- `tools/final_checks_o30.sh` check 15 sweeps exes matching `/d/o30/w/*o30tuned*_pc1/src_copy/*.exe`; the tag
  `tuned184` does not match that glob, so the new exe's sha256 is only swept if its path is added there (check 10 does
  pick up `b/o30tuned_*.patch`). Observation only - tracked files are the main session's.
- `build_o30tuned.sh` refuses an existing `D:\o30\repos\<tag>` or `b/o30tuned_<tag>.patch`: a rebuild needs a new tag
  (no deletes).
- LmrCutNode 2038 differs from the lock's 2048 by 10/1024 ply (the smallest move of the run, z -0.07); the LMR sum is
  truncated to whole plies, so this term alone changes the tree only where the sum crosses a multiple of 1024. Its
  liveness on its own was not tested here; the set as a whole changes the bench (check 2).
- Process hygiene: the build script pinned itself to Idle / mask 0x3 (pids 1540 and 7752), the option-list diff ran
  under idle.sh on mask 0x2 (pid 11868), the conformance and smoke drivers pinned themselves to Idle / mask 0x2; no
  process was touched; nothing of mine runs on CPUs 0-1 since 13:47:31 (the first waiter, an unpinned sleeping
  PowerShell loop, exits by itself at 14:10 or earlier).
- D: free fell from 55 GB (12:35) to 52.7 GB (13:42) through other work; the kit's gate needs >= 51 GB and the script
  stops below 50 GB - a later rebuild may need space first.
- The patch tool reported the tree's uci.cpp as CRLF (it keeps a file's line ends); the patch itself comes from the
  committed blobs (0 CR bytes, cleanroom_lint CLEAN); the kit built from the same kind of working tree as sp1 did.
- Not done and not in the brief: a plain (non-kit) build of the patched tree; a per-parameter liveness test of the 8
  tuned values (the set as a whole is live: check 2; the 22 expose22 options were proven live one by one on
  2026-11-03); any game vs the lock (sanity matches are not part of the deliverable; the crew gates). Nothing from the
  brief is missing.

## Note on the branch copy (main session)
The four conformance_{off,on}.{txt,json} copies here have the value of the engine's own `id author` line replaced by
"[value redacted in this branch copy]" (this branch carries no such names); originals with their exact bytes in D:\o30\checks_itemB\.
