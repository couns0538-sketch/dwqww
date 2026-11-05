# Independent read-only review of the Job A tools (speed job, branch opus-speed-20261105)

Reviewer: worker toolrev (fable), board slot S2. Started 10:14 PC clock, tools re-read at 11:43 (branch head dde4043b).
Versions reviewed (file times of 2026-11-05): abba.ps1 09:52, abba_queue.ps1 09:16, bitexact_check.ps1 10:42 (with
-ResumeFrom, -RefSrc, Get-MsvcAsanRefNodes, ref mutex), build_variants.ps1 09:57, speed_pack.ps1 10:43 (with
-ReuseBuildDirs, -PriorBitexact), uci_lib.ps1 09:37, tests 09:43 / 09:49, abba_table.py, pgn_positions.py,
ctrl_char_check.py, name_lint.py, ps_parse_check.ps1, make_stack.sh, commit_push.sh; QA kit build_ltopgo.ps1 v2.3
(read-only) for the command-line comparison. No engine was run, nothing was built; "cheap check" = reading the
job's own logs / CSVs / cache files under F:\ospd (lp_ppt_d20, q2 summaries, packs b1_tt_notls, pack_*.out,
bx_*.out, bv_*.out, F:\ospd\ref). No open question for the coordinator.

Bugs already fixed by the coordinator (pin DIFF fail-open, Build-One stream pollution, placement-only FENs, BEL
bytes, L3 reference race, workload file sharing, ordered-dictionary int index, -File lists, native stderr under
Stop) were re-read in the current code and are NOT re-reported; each fix looks right (see the "found fine" list).

## Summary

No BLOCKER found: I could not construct a path where a failure, missing data or an exception yields PASS,
BIT-EXACT, WIN or exit 0 in the current code. Every error path I traced ends in a non-zero exit (1 or 3) or a
FAIL line, and speed_pack stops on any rc != 0. The findings below are SHOULD items about provenance claims and
verdict wording that could let a *wrong description* of a right result through, plus LOW robustness items.

## Findings, ranked

### SHOULD 1 - speed_pack -ReuseBuildDirs: source equality is checked in one direction only (provenance)
- speed_pack.ps1:74-78. For every file under this pack's `include\` and `src\` the twin in the reused
  `src_copy` must exist and hash-match. Files that exist only in the reused `src_copy` (an extra `src\x.cpp` or a
  header) are never seen, yet the pack then says "sources byte-identical to this pack's" and names this pack's
  source as the origin of the exe. Status: suspected (by reading; the only reuse so far, locklock_v1b, reused a
  lock build for the lock source, where it cannot matter).
- Failure scenario: a worker re-runs a pack with `-ReuseBuildDirs` pointing at builds of a later revision of the
  same tree that added a translation unit; the proof (L1-L4, ABBA) is done on that exe and is valid for that exe,
  but the candidate .md records the wrong source / patch, and QA's pc1 = pc2 rebuild of the recorded source gives a
  different sha256.
- Fix: compare the relative file LISTS of `include\` and `src\` in both directions (or hash both trees with the
  same function Get-MsvcAsanRefNodes uses and require equal hashes), and record that tree hash in SUMMARY.md.

### SHOULD 2 - speed_pack records a patch md5 without verifying the source is lock + patch (provenance)
- speed_pack.ps1:135-137 cites `patches/<leaf of -SrcDir>.patch` and its md5 whenever such a file exists, by
  NAME only. Nothing checks that `-SrcDir` equals `F:\ospd\src\lock` + that patch (a worker may have edited the tree
  after writing the patch, or regenerated the patch after the pack). Status: suspected.
- Fix: in step (5) run `diff -ruN lock <SrcDir>` (relative, as make_stack.sh does) and require it to equal the patch
  byte for byte (or md5), else write "patch DOES NOT MATCH the built source" into the .md; additionally store the
  include\+src\ content hash of `$buildSrc` in signature.txt so exe <-> source stays checkable.

### SHOULD 3 - L4 ASan "N/A" and vacuous ASan coverage are reported as a full "L1-L4" proof
- bitexact_check.ps1:328-333 (port-copy anchor missing or MSVC compile failure -> `$script:AsanNa`, UBSan alone
  must pass) and :359-361 (verdict text "L1-L4 with L4 = UBSan only, ASan N/A", exit 0). speed_pack.ps1:119 maps
  exit 0 to `State: BIT-EXACT` with no qualifier; only the quoted verdict line carries it.
- Second gap: when a candidate's ON path is guarded by `defined(__GNUC__)` / GCC builtins and the lock text sits
  under `#else`, MSVC compiles the OFF path, so ASan tests the lock code, not the new code, and the verdict still
  reads "L1-L4" (nothing in the tool can tell the two cases apart). The candidates most likely to need ASan (new
  intrinsics, prefetch, pointer tricks) are exactly the ones most likely to hit either gap. Status: suspected (the
  b1_tt_notls san folder shows the MSVC ASan build and run do work on that source).
- Fix: (a) `$bxState = 'BIT-EXACT (ASan N/A: ...)'` in speed_pack when the verdict contains "ASan N/A", and put it
  into the candidate .md `State:` line; (b) consider a distinct exit code (e.g. 4) for "passed, ASan N/A" so a
  lock candidate needs an explicit `-AllowAsanNa`; (c) in L4 grep the MSVC port copy for each flipped switch name
  and report whether its ON block is inside a `__GNUC__`-only region ("ASan covered the ON path: yes / no / unknown").

### SHOULD 4 - abba.ps1 prints two verdicts of equal standing; the protocol WIN is the wall one
- abba.ps1:175-182 ("VERDICT wall X / cpu Y"); PLAN.md defines the WIN rule on the engine's own bench nps. The
  branch log already cites a "cpu WIN (narrow)" where wall is NO-WIN (commit 980067dc "prefetch-early cpu WIN").
  abba_queue results.tsv and abba_table.py sort by the cpu median. Status: confirmed by reading + the commit log.
- Fix: print one protocol verdict (`VERDICT WIN|NO-WIN` from the wall metric) and label the cpu metric
  "advisory"; sort abba_table.py by the wall median; never cite a cpu-only WIN as a protocol WIN in FINAL_REPORT.

### LOW 1 - Verdict-Line passes when both values are empty and the ref is not the lock
- bitexact_check.ps1:51-58: `"$RefVal" -eq "$CandVal"` is true for null = null; the pin check rescues the lock-ref
  case only. Needs a corrupt / incomplete `sig_*.json` in F:\ospd\ref (written without a mutex by Get-L1L2 :63-82,
  so two first-time checks of a NEW ref exe could collide). Fix: `$ok = $ok -and "$RefVal" -ne '' -and "$CandVal" -ne ''`.

### LOW 2 - shared reference uci log can abort a long reference computation
- bitexact_check.ps1:286 appends both engines' logs to `F:\ospd\ref\<sha8>\fens.uci.log.c0/.c1`; the mutex (:279)
  is per TSV leaf (n, depth), so a quick (n=2000) and a full (n=12000) reference computation may run at the same
  time and share these logs; File.AppendAllText opens with FileShare.Read, so the second writer throws "being used
  by another process" -> exit 1 after up to 37 min of work (fail-closed, data lost). Same for the ref `sig_*.uci.log`.
  Fix: name the logs after the TSV leaf + `$PID` (or write them into `$Out`).

### LOW 3 - Get-MsvcAsanRefNodes cache key ignores compiler and flag state
- bitexact_check.ps1:185-188: the cache `msvc_asan_b16_<h>.txt` is keyed by the ref source content only; cl.exe
  version, `/arch`, `/O2`, `-SanNdebug` (applied to BOTH builds via the script-level `$SanNdebug`, :175) and the
  port-copy edit are not part of the key. A later MSVC update or a `-SanNdebug` run compares a candidate against a
  stale reference count -> spurious FAIL (fail-closed), or an unnoticed difference if asserts ever have side
  effects. Fix: hash the cl version line + the `$clArgs` prefix + `$SanNdebug` together with the source list.

### LOW 4 - -ResumeFrom does not check FEN file / depth of the reused L3 line
- bitexact_check.ps1:240-253: cand and ref sha256 are checked, n is parsed; the FEN file md5 and `go depth` in the
  reused L3 line are not compared with the current `-Fens` / `-FenDepth`. speed_pack never passes those, so
  theoretical today. Fix: parse `(md5 xxxxxxxx` and `go depth N` from the line and require equality.

### LOW 5 - abba.ps1 validates -AaCsv only after all rounds
- abba.ps1:164-174: a wrong `-AaCsv` path throws in `Import-Csv` after the 6-minute run; runs.csv is complete but no
  summary is written (queue marks ERROR). Fix: `Test-Path -LiteralPath $AaCsv` at :99.

### LOW 6 - cpu metric: tick quantisation and SMT sibling
- abba.ps1:144-150: TotalProcessorTime has 15.625 ms resolution (cpu_ms in runs.csv are multiples of 15.625; about
  0.1-0.3 % per run at d20) and does not remove SMT-sibling contention: load.txt of lp_ppt_d20 shows cpu3 at 87 %
  during the run (the Idle trainer's mask 0xF covers CPU 3). Both arms suffer alike, so this is noise, not bias; the
  comment at :142-143 reads as if the cpu metric were load-free. Fix: say "preemption only" in the comment / summary.

### LOW 7 - abba_queue leaves the queue process on CPU 2 BelowNormal between runs
- abba.ps1:107 pins the CALLING process (same process under `&`); abba_queue.ps1 never restores 0x3 / Idle
  (speed_pack does, :89/:109/:129). Only sha256 / file writes run there; no timing effect. Fix: Set-OspdPlacement
  0x3 Idle after :38.

### LOW 8 - L3 counts a forced-move position as a DIFF even when ref = cand
- bitexact_check.ps1:304: the row must match "`t\d+`t"; a position where the engine prints `bestmove` with no
  `info depth` line gives empty depth/score/nodes and fails the regex -> false FAIL (fail-closed). None in the 12k
  set (12000 / 12000 identical was observed), so no effect now; worth a comment or an explicit "empty row" rule.

### LOW 9 - make_stack.sh switch count regex and unchecked diff
- make_stack.sh:31: `\r` is not an escape in GNU ERE (`0\r?$` = "0 optionally followed by r"), so a CRLF source
  would count 0 default lines and abort (lock sources are LF, no effect now); :35 ignores diff's exit code 2 and
  silently overwrites an existing `<name>.patch`. Fix: `grep -P` or strip CR first; `|| [ $? -eq 1 ]`; refuse an
  existing patch file.

### LOW 10 - commit_push.sh lints only worktree-modified / untracked code files
- commit_push.sh:15: `git ls-files -mo` misses a code file already staged by hand (or left staged by a failed push
  after `git add -A` at :24) and unchanged since; `git add -A` then commits it unlinted. Fix: lint the union with
  `git diff --cached --name-only`.

### LOW 11 - small provenance / robustness nits
- speed_pack.ps1:98-101: the pack exe's sha256 is printed next to the REPRO sha but never asserted equal.
- speed_pack.ps1:55-57: ReadAllText / WriteAllText(UTF8 no BOM) would drop a BOM from a flipped header (lock files
  are ASCII; no effect; the kit builds src_kit as written anyway).
- build_variants.ps1:158: variant `o3` adds `-Wl,--no-insert-timestamp` that the kit's plain line lacks, so an o3
  exe is not byte-comparable with QA's plain exe (documented in the header; fine for screening).
- build_variants.ps1 / speed_pack.ps1:96: the EXE line is split on spaces, so a `-Work` or `-Tag` with a space
  breaks the path (fail-closed: Copy-Item throws).
- Mutexes use the `Local\` namespace: serialisation holds only inside one logon session (true for everything that
  runs from the coordinator's session today).

## Looked at and found fine (confirmed by reading; evidence named where a log was used)

- Fail-closed paths: build_variants pin table empty -> throw (:206); pin DIFF -> RESULT FAIL + FAILED + exit 1, no
  EXE line (:209-213), pc2 skipped after a failed pc1 (:241); speed_pack requires rc 0 AND an `EXE *_pc1` line AND a
  `REPRO` line AND ` pins OK ` on every EXE line (:90-96), maps bitexact rc 3 -> NOT BIT-EXACT / other rc -> CHECK
  ERROR, never runs ABBA unless rc 0 (:119-125), abba rc != 0 -> throw -> exit 1 (:131). Evidence: pack_b2_nnue_zmm.out
  and pack_locklock_v1.out (rc 1 "Cannot create a file..." -> "no ABBA", exit 1), bv_mut / bx_mutant_histmax.out
  (10 L1 FAIL lines, exit 3), test_moveorder_run1.out (3/3), test_cr_637b 13/13.
- bitexact L1: cand = ref AND = lock pins (net on + off) when ref is the lock; L2 perft always against pins; L3
  compares depth, score, nodes, bestmove per FEN with `ucinewgame` + OwnBook=false, identical 2-way chunking for
  ref and cand (so any state that survives ucinewgame is equal on both sides), rejects any `info string ... invalid`
  line, degenerate-reference guard (< n/10 distinct), a short ref file or an unfilled cand row compares unequal,
  Stop-IfFailed after every level, exit 3 with -NoStop when any line failed. The ref TSV race fix (:283-296) is
  correct: mutex per leaf, `.part<PID>` then Move-Item, byte comparison if an older process wrote it meanwhile.
- L4: UBSan = the lock's g++ with `-fsanitize=undefined -fsanitize-trap=all -fno-sanitize-recover=all` at -O1 on the
  unchanged source, nodes must equal the candidate's own g++ d16; a trap or an ASan report gives a non-zero exit and
  /or a report line, both fail the line; a missing ASan runtime DLL fails the process start (non-zero exit). The MSVC
  port copy edits exactly one anchor (present once in the lock, search.hpp:179-180, LF file) and the MSVC-vs-MSVC
  node comparison is the right fix for the libstdc++ / MSVC std::sort difference.
- -ResumeFrom: ref + cand sha256 must appear in the prior log, exactly 10 L1 + 2 L2 + 1 L3 PASS lines and no L1-L3
  FAIL line, the prior sig_*.json must carry the cand sha256; the quick-subset wording is preserved.
- build_variants vs the kit (build_ltopgo.ps1 :82-146): `$F`, LTO tokens, gen / gen link / use / use link lines,
  `-fprofile-update=single`, `-fprofile-correction -Wmissing-profile`, `-static`, `-Wl,--no-insert-timestamp` on the use
  link only, object order (`Get-ChildItem obj_ltopgo\*.o`), unit order (`Sort-Object Name`), training as raw stdin
  bytes of the sha256-checked frozen workload, 3 bench lines, gcda = units, rebuilt-after-training check, 0
  missing-profile warnings, LTO IR per object, vfmadd = 0: token for token equal for lp_v1; only the exe / instr file
  names and the work path differ, and they do not reach the bytes - evidence: lp_v1 of the lock source = FD3A5190
  (bv_stack3off.out, pack_locklock_v1.out, bv_scr.out lp_noplt / lp_nosi / lp_pvw512 also = FD3A5190). Extra flags are
  appended at the end of `$F`; the `-Define` route is correctly NOT used by speed_pack (flip in source, :46-60, exactly
  one `^#define NAME 0$` across *.hpp/*.cpp/*.inc, `(?m)` + `(\r?)` keeps CRLF, anchored so FORGE_SPD_TT does not hit
  FORGE_SPD_TT_NOTLS).
- abba.ps1 statistics: per-round ratio (B1+B2)/(A1+A2); median; t-interval of the mean log ratio with the correct
  two-sided 97.5 % quantiles (df 9 -> 2.262) and Cornish-Fisher beyond df 30; seeded bootstrap of the median with
  percentile indices 249 / 9749 of 10,000; WIN = low end > 1.000 AND median >= 1.010 exactly as PLAN.md; A/A band
  parsed only from complete rounds (2 A + 2 B) and flagged when it excludes 1; nodes constant per exe and equal A = B
  unless -AllowNodeDiff (speed_pack never passes it); exit 2 on node mismatch / missing `UseNNUE default true`; fresh
  byte copies per round with an untimed warm-up; ABBA / BAAB alternation with the copy order alternating too, so
  every slot and copy position is balanced over each pair of rounds. Evidence: lp_ppt_d20/runs.csv (orders 1:A 2:B
  3:B 4:A then 1:B 2:A 3:A 4:B, nodes 12389307 on every row, cpu_ms within 0.5 % of ms, md5 of A = lock, of B = the
  lp_ppt exe of bv_scr.out). Degenerate inputs (no cpu rounds) give NO-WIN, not WIN. Cheap check 11:55: an own
  Python recomputation from lp_ppt_d20/runs.csv (F:\ospd\toolrev\recompute.py: per-round sums, median, log-mean
  t-interval with t = 2.262, sample sd) reproduces the summary digit for digit - wall 0.9973 [0.9846, 1.0111] sd
  1.86 %, cpu 0.9959 [0.9844, 1.0114] sd 1.89 %.
- Mutex handling: AbandonedMutexException treated as acquired (correct), release in `finally`, `exit` inside try
  runs the finally (PS flow control, not caught by `catch`).
- PowerShell 5.1: every script path ends in an explicit `exit`, so `$LASTEXITCODE` after `& script.ps1` is fresh; an
  exception that escapes a child script (e.g. parameter binding) propagates into the parent's `try` -> ERROR, exit 1;
  `-File` list parameters are split on commas in every tool; `Say` in build_variants writes to Console.Out so the
  Build-One return value stays one object (REPRO seen in pack_r14_speed2.out); functions defined inside a child
  script do not leak into the caller (three different `Say`s coexist); `$script:` variables of the dot-sourced lib
  resolve in each script's own scope; InvariantCulture set for `-f` formatting (the `{0:N0}` seconds print a thousands
  comma, cosmetic); hashtable pins with string keys replace the `[ordered]` int-index bug; `Get-ChildItem -Recurse
  -Include` works with -Recurse; `break` inside `catch` leaves the sides loop as intended; `exit` inside a function
  (Stop-IfFailed) ends the script, as intended.
- uci_lib: placement checked after setting (affinity + class) and allowed masks limited to CPUs 0-3; disk gates;
  Write-OspdLf refuses overwrites (T4a); ConvertTo-OspdFen appends defaults only for trailing fields and throws on
  < 1 / > 6 fields or != 8 ranks; Invoke-OspdSearch throws on `info string ... invalid`; Read-OspdLine has a hard
  timeout and reuses the pending task; Stop-OspdEngine never kills.
- abba_queue: entries done by summary / IDENTICAL / ERROR markers, identical-to-lock exe recorded as ratio 1 (can never
  be a WIN); any abba rc != 0 -> ERROR.txt and an ERROR row (evidence: results_q2.tsv rows o3 / lto after the BEL bug).
- abba_table.py, pgn_positions.py (two `#` header lines with source md5, refuses overwrite, six-field FENs, seeded
  choice), ctrl_char_check.py, name_lint.py, ps_parse_check.ps1: read, nothing wrong found; T6 verifies the TSV md5.
- Tests: test_cr_637b counts the status field only (fixed counter); test_moveorder_mutant checks both the pipeline
  (exit 3, no abba dir, no candidate file) and the proof (exit 3, NOT BIT-EXACT).

## NOT REVIEWED
- pack_table.py (added after my brief), novendor_filter.py, board.py, the jobc tools and skills, candidates/*.md,
  FINAL_REPORT.md, the data file bodies beyond their heads, the `-ResumeFrom` / `-PriorBitexact` / `-ReuseBuildDirs`
  paths at run time (read only; no run exists besides locklock_v1b), the MSVC ASan build at run time (no builds allowed
  for this review), QA's lp_check.py.
