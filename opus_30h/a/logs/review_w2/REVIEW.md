# Independent review - 30-h job, GPU window 2 code changes

Reviewer: an independent agent that did not write any of this code and had no part in the window-2 work.
Review started 2026-11-04 14:35:30 PC clock (`date`); REVIEW.md first written between the `date` outputs 14:52:41 and
14:55:13, last edited after the `date` output 14:57:59 (end time in the hand-back). Read-only on the branch;
the only writes are in this folder (REVIEW.md, nl_test.txt from one 1-second newline check).

## Scope

- Branch `opus-30h-20261103`, worktree `D:\o30\wt`, head `86da67bc`; range `a0a750c0..86da67bc`
  (`git -C D:/o30/wt diff --stat a0a750c0 HEAD -- opus_30h`, 121 files; code files only, logs read as evidence).
- Files reviewed (all under `D:\o30\wt\opus_30h\`): a/o30_gpu_guard.py, a/gpu_ckpt_watch.sh,
  a/forge_v2_bullet_o30/src/main.rs, a/o30_v2net.py, a/export_v2r.py, a/import_v2r.py, a/o30_fit.py, a/o30_soup.py,
  a/o30_expand_kb.py, a/soup_score.sh, a/soup_table.py, a/queue_runner.sh, a/queue_w2a.sh, a/queue_w2b.sh,
  a/queue_w2c.sh, a/gpu_run_o30c.bat, a/npt_busy.py, a/net_pack.sh, a/make_net_index.py, a/gpu_runs_table.py,
  tools/final_checks_o30.sh, a/o30_guard_dummy.py; context: STATUS.md "GPU window 2", a/forge_v2_bullet_o30/src/forge_r.rs
  (feature index), tools/idle.sh, tools/hash_sweep.py, a/o30_score.cpp (dump file mode), the commit messages of the range,
  a/logs/gpu/{cr9_guard_tests,cr12_watch_tests,cr10_refusal01,soup_selftest,expand_r7_to_kb32}.out,
  a/logs/gpu/soups_w2_table.md.

## Method

1. Read every diff hunk of the range for the files above and the full text of each new file.
2. Checked each claim of the commit messages / STATUS / test logs against the code and, where cheap and read-only,
   against the live artefacts: the guard logs on `C:\o30g\gpu` (r8, r10, r11), the queue logs, the TSV files, the
   CR 12 test artefacts under `D:\o30\tmp\cr12\root`, the control match log `D:\o30\control\lockkb4_v2p4`.
3. md5 of the committed guard and watcher compared with the md5 named in their test logs (both equal:
   `7899410083df7957516ae7b7ce9cbe11`, `ef8d3e07b574d6446b7935b403708e46`), so the tests ran on the committed code.
4. Line endings: `git ls-files --eol` = LF in index and worktree for every .sh/.py/.rs; only gpu_run_o30c.bat is CRLF
   (correct for cmd). `C:\o30g\gpu\plan.txt` is LF (cat -A).
5. Layout math of the soup / expand tools checked against export_v2r.py (counts, padding) and forge_r.rs:99
   (`bucket * 768 + (rel * 6 + typ) * 64 + sq`, bucket-major, so `l0w.reshape(kb, 768 * h)` is the per-bucket block).
6. Rust king maps rank4x4 / rank4x8 compared line by line with o30_v2net.king_map (same rank groups 0 / 1 / 2-3 / 4-7,
   file pair `f / 2` or file `f`, 16 / 32 buckets).
7. One computation only: a 1-second pinned (Idle, 0x38) interpreter run `print('x')` redirected to a file in this folder,
   to confirm the stdout newline translation behind W2-07. No engine, no GPU, no live script executed.

No live process, file or folder outside this one was modified. The running GPU run (r11_kb16long under the guard,
started 14:35:08), the watchers and the four sanity matches were not touched.

## Findings

Severity: BLOCKER = must be fixed before the result is used; SHOULD = fix before the next unattended use;
NIT = cosmetic or low-impact.

### W2-01  SHOULD  a/gpu_ckpt_watch.sh:26-49 (score_one) - the bounded retries cannot succeed after the first step that writes a file

What is wrong: every producer in `score_one` refuses an existing output: export_v2r.py -> o30_v2net.write_v2
(`a/o30_v2net.py:70-71 "refusing to overwrite"`), o30_score_v3.exe `--dump` (`a/o30_score.cpp:166 fopen(..., "wbx")`,
"cannot create (or exists)"). `score_one` never clears the partial outputs of a failed try, so try 2..WATCH_TRIES of any
failure *after* the export (scorer, paired, TSV step, a transient disk / memory error) always fails again at the export
step, and the checkpoint is given up after WATCH_TRIES tries without the failing step ever being re-run. The watcher is
still fail closed (no `.done`, `.gaveup` written, exit 5), but the retry logic of CR item 12 is dead for the realistic
failure modes, and the test log reads as if the TSV step had been retried.

Evidence (the author's own CR 12 test C, read-only):
```
$ cat /d/o30/tmp/cr12/root/fakeC_nets/forge_v2r_rank4_h256-1.export.txt
refusing to overwrite D:\o30\tmp\cr12\root\fakeC_nets\forge_v2r_rank4_h256-1.nnue2
$ cat /d/o30/tmp/cr12/root/fakeC_scores.tsv.errors
2026-11-04 13:43:07 score failed for .../fakeC/forge_v2r_rank4_h256-1 (try 1 of 2)
2026-11-04 13:43:13 score failed for .../fakeC/forge_v2r_rank4_h256-1 (try 2 of 2)
2026-11-04 13:43:13 GIVE UP on .../fakeC/forge_v2r_rank4_h256-1 after 2 failed tries (no .done written)
```
a/logs/gpu/cr12_watch_tests.out line 16 shows the injected TSV failure message exactly once for two tries: try 2 died
in the export step (6 s, the export refusal above), not in the TSV step. Nothing in production hit this yet
(no `*_scores.tsv.errors`, `*.fails` or `*.gaveup` under C:\o30g\gpu or D:\o30\gpu at 14:45).

Proposed minimal fix (move the leftovers of a failed try aside before the export; `mv`, no delete):
```diff
@@ score_one() {
   local ck="$1" name; name=$(basename "$ck")
   [ -f "$nets/$name.done" ] && return 0
   [ -f "$ck/quantised.bin" ] || return 1
   local N="$nets/$name.nnue2"; local NW; NW=$(cygpath -w "$N")
+  # a failed try leaves .nnue2 / .f64 / .json behind and every producer below refuses an existing output:
+  # park them, or every retry dies in the export step (CR item 12 retries were dead without this)
+  local old; for old in "$N" "$nets/$name.s16.f64" "$nets/$name.jobA.f64"; do
+    [ -e "$old" ] && mv -f "$old" "$old.failed.$(date +%s)"
+  done
   "$PY" -I -B "$A/export_v2r.py" ...
```
And re-run test C with WATCH_TRIES=2 so that the second try reaches the TSV step (two injected messages expected).

### W2-02  SHOULD  a/queue_runner.sh:29-35 - a run refused at start is marked done and the plan is burned through

What is wrong: the run name goes into `plan.done` (line 30) before anything starts and the exit code of
gpu_run_o30c.bat is only echoed (line 35). The guard refuses to start with exit 78 when an npt-like process runs, when
the sensor CSV is stale / unreadable, or when the mask cannot be set (a/o30_gpu_guard.py:161-171), and the bat aborts
with 2-4 on an existing run / log. Under any persistent condition (the sensor logger closed, an npt trainer up for an
hour) the loop takes the next plan line after 15 s, marks it, is refused again, ... - the whole plan is consumed in
~2 minutes with no run trained, unattended, and the cutoff logic never gets a chance. The header comment (line 9)
"no run starts while an npt-like process runs (the guard refuses too)" describes a check the runner does not have;
commit b8e73633 repeats the claim. The plan line is also not validated: `read -r name kb sb seed lr init` with a
5-field line gives an empty O30_INIT_DIR (a cold run with clip 7.99 / decay 0 if cmd drops the empty variable, or a
panic in load_from_checkpoint), a trailing comment lands in `init`, and a kb map that does not fit the init dir is
only caught (if at all) by the trainer. (The trainer itself is strict: `arg()` panics on a malformed number,
O30_CLIP / O30_DECAY are parsed with `expect` and range asserts - checked, no finding there.)

Evidence: a/queue_runner.sh lines 29-35 (quoted above); a/o30_gpu_guard.py:166-171
(`sys.exit(78)` before `Popen`); the live `C:\o30g\gpu\queue_runner.log` shows the happy path only
(r10 exit 0, r11 started 14:35:08).

Proposed minimal fix:
```diff
@@
-    read -r name kb sb seed lr init <<< "$line"
+    read -r name kb sb seed lr init extra <<< "$line"
+    case "$kb" in one|rank4|rank4x2|rank4x4|rank4x8) ;; *) echo "$(date '+%F %T') bad kb map in '$line': queue ends"; break ;; esac
+    if [ -n "${extra:-}" ] || [ -z "$init" ] || [ ! -d "$(cygpath -u "$init")" ]; then
+        echo "$(date '+%F %T') bad plan line '$line' (6 fields, init dir must exist): queue ends"; break
+    fi
+    if [ "$("$PY" -I -B "$A/npt_busy.py")" != "0" ]; then   # PY = the venv interpreter, as in the other queue scripts
+        echo "$(date '+%F %T') npt-like process present: $name waits 5 min"; sleep 300; continue
+    fi
     echo "$name" >> "$DONE"
     ...
-    echo "$(date '+%F %T') $name exit $?"
+    rc=$?; echo "$(date '+%F %T') $name exit $rc"
+    if [ "$rc" = 78 ]; then   # guard refused before the trainer started: keep the run open, wait, retry
+        sed -i "/^$name\$/d" "$DONE"; echo "$(date '+%F %T') guard refused $name (78): retry in 5 min"; sleep 300; continue
+    fi
```
(The runner is running now; the fix is for the next edit between runs, never in place.)

### W2-03  SHOULD  a/o30_gpu_guard.py:105-127 (--resume-pid) and 226-240 (poll) - an external resume is never noticed; the thermal guard is silently off for the rest of the episode

What is wrong: `--resume-pid` checks pid, create time and exe name, but not whether the guard that suspended the trainer
is still alive. Run against a trainer that the *live* guard holds suspended for heat (an operator reading the SUSPEND
line and the docstring's resume command too early), it resumes the trainer; the guard still has `st['suspended']=True`,
so on the next polls `want and not st['suspended']` is false, nothing re-suspends, and the log keeps saying
"still suspended" every 300 s while the trainer runs on a GPU above the HARD limit. The guard never re-reads the
child's real state. The docstring (lines 25-27) limits --resume-pid to the hard-kill case, but nothing enforces it.

Evidence: code lines 226-240 (the three branches all assume the guard's own state is the truth); resume_pid 105-127
has no parent check. The test log cr9 only exercises the intended case (guard gone).

Proposed minimal fix:
```diff
@@ def resume_pid(pid, create_time, expect_name):
     if name.lower() != expect_name.lower():
         print(f'refusing: pid {pid} is {name}, expected {expect_name}')
         return 2
+    par = p.parent()   # the guard is the direct parent; alive = it suspended the trainer on purpose (heat / yield)
+    if par is not None and par.is_running() and 'o30_gpu_guard' in ' '.join(par.cmdline()):
+        print(f'refusing: the guard (pid {par.pid}) is still running; it suspended {pid} on purpose')
+        return 2
+    v = Feed(CSV).read()
+    if v is None or v[0] >= 76 or v[1] >= 86:
+        print(f'refusing: sensor feed stale or GPU hot ({v}); resume only below the HARD limits')
+        return 2
@@ main loop, after `hot, mj, pwm, util = v` handling:
+                if st['suspended'] and proc.is_running() and proc.status() != psutil.STATUS_STOPPED:
+                    st['suspended'] = False   # resumed from outside: fall through to the normal suspend decision
+                    say(f'WARNING {ident} was resumed externally; guarding it again')
```

### W2-04  SHOULD  a/o30_gpu_guard.py:179-190 and 260-262 - console path can claim "left running" for a frozen trainer

What is wrong: the console handler runs on a thread the console creates while the main loop may be inside, or just
past, `proc.suspend()` (line 228) with `st['suspended']` still False (set on line 229). The handler then does not
resume ("guard exits"), the main thread finishes the suspend, the interrupt lands, and the `finally` console branch
(lines 260-262) writes "trainer (...) left running to take the same event" and exits 130 without looking at the child.
The trainer is suspended, the log says it runs, nothing resumes it (the ABORT branch with the resume command is not
taken). The window is one poll iteration and only on a console event, but the branch asserts a state it has not
checked - the opposite of the fail-closed rule the rest of the file follows.

Evidence: lines 179-190 (handler acts on `st['suspended']` only), 226-231 (suspend then flag), 255-262 (console branch
has no `proc.status()` check and no resume).

Proposed minimal fix:
```diff
@@ finally:
         if code is None and st['ctrl'] is not None:
-            say(f'console event {st["ctrl"]}: guard exits; trainer ({ident}) left running to take the same event')
+            try:
+                if proc.is_running() and proc.status() == psutil.STATUS_STOPPED:
+                    proc.resume()
+                    say(f'console event {st["ctrl"]}: trainer ({ident}) was still suspended: resumed')
+                say(f'console event {st["ctrl"]}: guard exits; trainer ({ident}) left running to take the same event')
+            except psutil.Error as error:
+                say(f'console event {st["ctrl"]}: cannot check / resume the trainer ({ident}): {error}; '
+                    f'if frozen: --resume-pid {child.pid} --create-time {proc.create_time():.3f}')
             exit_code = EXIT_CONSOLE
```

### W2-05  SHOULD  a/net_pack.sh:16 (default O30_MASK 0x3 = CPUs 0-1) and a/gpu_ckpt_watch.sh:17 (default WATCH_MASK 0x4 = CPU 2) - defaults land on the CPUs of running sanity matches

What is wrong: in this window the 400-game 10+0.1 sanity matches run on CPUs 0, 1, 2 and 6 (STATUS: run 7 on CPU 0
from 13:57, soupC on CPU 1 from 14:12, run 5 on CPU 2 from 13:26). Both scripts still default to those CPUs when
the environment variable is unset: `o30_pin_self "${O30_MASK:-0x3}"` and `MASK="${WATCH_MASK:-0x4}"`. The queue runner
and soup_score.sh pass 0x38 explicitly, so the automated paths are fine; a manual `bash net_pack.sh ...` or
`bash gpu_ckpt_watch.sh r11_kb16long rank4x4` (the obvious thing to type to re-score a run) pins a scorer / pin_check
/ harness next to a timing-sensitive match on CPU 0-1 or 2. Commit 4b43ffa6 says net_pack "pins its own shell to
O30_MASK too" - true, but the default stayed on the match CPUs.

Evidence: the two lines quoted; tools/idle.sh:8 (`O30_MASK` overrides, otherwise the script's own default).

Proposed minimal fix (fail closed when the caller has not chosen a mask):
```diff
--- a/net_pack.sh
-. "$T/idle.sh"; o30_pin_self "${O30_MASK:-0x3}" || { ... }
+[ -n "${O30_MASK:-}" ] || { echo "net_pack: set O30_MASK (sanity matches run on CPUs 0-2, 6 in this window)" >&2; exit 78; }
+. "$T/idle.sh"; o30_pin_self "$O30_MASK" || { ... }
--- a/gpu_ckpt_watch.sh
-MASK="${WATCH_MASK:-0x4}"; ...
+[ -n "${WATCH_MASK:-}" ] || { echo "watch: set WATCH_MASK (the old default CPU 2 now hosts a sanity match)" >&2; exit 78; }
+MASK="$WATCH_MASK"; ...
```

### W2-06  SHOULD  a/gpu_ckpt_watch.sh:74 - the guard-exit pattern matches the old guard's text, not the new one

What is wrong: `grep -q -E 'ABORT|GUARD EXIT WHILE THE TRAINER RUNS'` - the second string is the pre-window guard's
line (`git show a0a750c0:opus_30h/a/o30_gpu_guard.py` line 179). The committed guard writes
`console event N: guard exits; trainer (...) left running ...` (a/o30_gpu_guard.py:261) and never the old text. After a
console-event exit of the guard (exit 130, no end line) the watcher does not exit 4 "at once" as the header (lines
8-10) and commit 16e84bc9 say; it polls until WATCH_MAX_MIN (720 min) and exits 3. Bounded, so no runaway, but the
documented behaviour and the test B of cr12 cover only the ABORT line.

Proposed minimal fix:
```diff
-  elif grep -q -E 'ABORT|GUARD EXIT WHILE THE TRAINER RUNS' "$glog" 2>/dev/null; then
+  elif grep -q -E 'ABORT|guard exits' "$glog" 2>/dev/null; then
```

### W2-07  NIT  a/gpu_ckpt_watch.sh:35-47 - TSV data rows end in CRLF, the header in LF

What is wrong: the TSV line is printed by an interpreter heredoc whose stdout translates `\n` to `\r\n` on this
platform; the header is written by `printf` (LF). Every `*_scores.tsv` on C: and D: is mixed. The two readers in the
branch cope (csv.DictReader and `read().splitlines()` use universal newlines), but the last column (sha256) carries a
trailing CR for any awk / cut / grep consumer, and `tail -1` in soup_score.sh prints a CR.

Evidence:
```
$ head -n 2 /c/o30g/gpu/r8_kb32short_scores.tsv | cat -A | tail -n 1 | tail -c 20
900b4bdb94583723^M$
$ head -n 1 /c/o30g/gpu/r8_kb32short_scores.tsv | cat -A | tail -c 12
bA^Isha256$
$ python -I -B -c "print('x')" > nl_test.txt; cat -A nl_test.txt      (pinned 0x38, this folder)
x^M$
```
Proposed minimal fix (first line of the heredoc program):
```diff
 import json, sys
+sys.stdout.reconfigure(newline='\n')   # no \r\n translation: the header is LF
```

### W2-08  NIT  a/soup_table.py:11-19 and 29-30 - member labels lose the checkpoint, failed soups vanish

What is wrong: `members()` reduces each input path to the run folder name, so checkpoints of one run collapse:
a/logs/gpu/soups_w2_table.md shows `r7_kb16short + r7_kb16short` (175 + 200) and
`r3_kb8warm + r3_kb8warm + r3_kb8warm + r3_kb8warm` (four unknown checkpoints). A soup whose scoring was given up
(header-only TSV) is skipped silently (`continue`), so the table cannot show that a soup exists without a score.

Proposed minimal fix:
```diff
-            run = next((p for p in parts if re.match(r'r\d+_', p)), None)
-            out.append(run or os.path.splitext(parts[-1])[0])
+            run = next((p for p in parts if re.match(r'r\d+_', p)), None)
+            ck = next((p.rsplit('-', 1)[1] for p in parts if re.match(r'forge_v2r_.*-\d+$', p)), None)
+            out.append((run or os.path.splitext(parts[-1])[0]) + (f'@{ck}' if ck else ''))
@@
         if not rows:
-            continue
+            print(f'| {name} | {" + ".join(members(os.path.join(root, name + ".soup.txt")))} | not scored | not scored | - |'); continue
```

### W2-09  NIT  a/o30_soup.py:40-43 - shape is checked by byte size only; the king map and mirror flag are trusted

What is wrong: a raw quantised.bin carries no layout. `--kb-map` only fixes the expected size, so two checkpoints of
different maps with the same bucket count (or a mirrored and an unmirrored run) would be averaged without a word. In
this window every run is an unmirrored rank4* map and the checkpoint folders carry the map
(`forge_v2r_<map>_h<H>-<n>`), so no soup in soups_w2_table.md is affected; the expanded copies (`r3_k16.bin`) are
named by hand. The printed "max |difference|" is the only tell.

Proposed minimal fix (refuse a path that names another map, keep an override):
```diff
     for path in a.inputs:
+        m = re.search(r'forge_v2r_(\w+?)_h(\d+)-\d+', path.replace('\\', '/'))
+        if m and (m.group(1), int(m.group(2))) != (a.kb_map, h) and not a.force:
+            raise SystemExit(f'{path}: folder says map {m.group(1)} H {m.group(2)}, not {a.kb_map} H {h} (--force to override)')
```

### W2-10  NIT  a/make_net_index.py:18-40 - "latest" summary is the first folder found; a running match is not marked

What is wrong: `sanity_from_log` returns at the first of `('sanity', 'sanity2')` that has a sanity.log, so when both
exist the older folder wins although the docstring says "Latest". The last `Games:` / `Elo:` lines of a match still in
progress are shown like a finished one (only "planned N games" lets a reader notice). Commit 192fe062 cites
"test_make_index.py PASS", but a/test_make_index.py (33 lines) renders three fake net folders that have no sanity
folder, so sanity_from_log only takes its `return '-'` exit there; the parsing path (Games / Elo lines, RUN_INFO) is
not exercised by that test. Header numbers checked: the v2p4 control "47.0 % = -20.9 +/- 18.5" equals
`D:\o30\control\lockkb4_v2p4\lockkb4_v2p4.log` (Elo: -20.87 +/- 18.51; Points 188.0 (47.00 %)).

Proposed minimal fix:
```diff
-    for sub in ('sanity', 'sanity2'):
+    subs = [s for s in ('sanity', 'sanity2') if os.path.isfile(os.path.join(d, s, 'sanity.log'))]
+    for sub in sorted(subs, key=lambda s: os.path.getmtime(os.path.join(d, s, 'sanity.log')), reverse=True):
@@
-            out += f"; exe {info['candidate']['sha256'][:8]}; planned {info.get('games', '?')} games ({sub})"
+            planned = info.get('games')
+            played = int(games.split(',')[0].split(':')[1]) if ':' in games else None
+            out += f"; exe {info['candidate']['sha256'][:8]}; planned {planned or '?'} games ({sub})"
+            if planned and played is not None and played < int(planned):
+                out += ' RUNNING'
```

### W2-11  NIT  a/gpu_run_o30c.bat:7 and a/o30_guard_dummy.py:1 - stale names in messages

`gpu_run_o30c.bat` prints `usage: gpu_run_o30.bat ...`; the dummy's docstring calls the file `dummy_busy.py` (the
test copy's name). Cosmetic; fix the two strings.

### W2-12  NIT  tools/final_checks_o30.sh:78 - the hash sweep walks the whole run tree on C:

`/c/o30g/gpu` is passed to hash_sweep.py, which hashes every file under a directory (tools/hash_sweep.py:55-58):
593 files / 2.6 GB at 14:45 and growing with every 600-superbatch run (checkpoints, per-row .f64 dumps). Only the
nets, guard logs and soups carry hashes that a document cites. Fine as a one-off at the end of the job, but it reads
gigabytes from the drive the live run writes to; narrow it to `/c/o30g/gpu/*_nets /c/o30g/gpu/soups /c/o30g/gpu/*.log`
or run it after the window.

## Checked, no finding

- checked: a/forge_v2_bullet_o30/src/main.rs - rank4x4 / rank4x8 maps equal o30_v2net.king_map (rank groups, file pair
  `f / 2`, file `f`; 16 / 32 buckets); the CR 10 early refusal runs before any GPU or file work and exits 2 with the
  message (a/logs/gpu/cr10_refusal01.out: three cases, no out dir), the in-block assert repeats it; O30_CLIP / O30_DECAY
  are parsed with `expect` and range asserts, `arg()` panics on a malformed number - no silent defaults.
- checked: a/o30_v2net.py, a/export_v2r.py, a/import_v2r.py, a/o30_fit.py - choices lists carry the two new maps in every
  parser (from-lock, info, random, train, selfcheck, export, import).
- checked: a/o30_expand_kb.py - layout = export_v2r.py (counts, `need`, padding `b'bullet' * 11`), l0w is bucket-major
  (forge_r.rs:99), l0b / l1w / l1b copied unchanged, fine->coarse map derived from the maps and verified square by
  square, finer->coarser refused ("spans"), exactness shown in a/logs/gpu/expand_r7_to_kb32.out (identical S31 / jobA
  numbers for run 7 as KB16 and as KB32).
- checked: a/o30_soup.py - size and padding rule = export; float64 accumulation; non-finite refused; existing output
  refused twice (`exists` + `'xb'`); self-soup byte-identical (a/logs/gpu/soup_selftest.out). See W2-09 for the trust
  in the map name.
- checked: a/soup_score.sh - refuses an existing name; the synthetic guard log's " end: " line matches the watcher's
  grep; `touch -d '-1 minute'` satisfies the 20-s age rule; exit = watcher's exit (5 on a given-up soup, header-only
  TSV, no false PASS).
- checked: a/queue_w2a.sh, a/queue_w2b.sh, a/queue_w2c.sh - runs 7 and 8 gated on `COMPARE: byte-identical -> PASS` of
  the lr-0 warm proofs; npt check before each proof; refuse existing outputs / logs; paths LF; the logs they produced
  (warmproof02-04, C:\o30g\gpu\queue_w2c.log) match the scripts.
- checked: a/gpu_run_o30c.bat - `diff` with gpu_run_o30.bat: only the C:\o30g\gpu paths and the comment differ; CRLF
  in the index (correct for cmd); existing run / log / guard log abort before anything starts. W2-11 is the usage text.
- checked: a/npt_busy.py - imports npt_like only (no side effects); its own command line carries none of the marks.
- checked: a/gpu_runs_table.py - C: fallback only when the D: file is absent; both absent -> FileNotFoundError (no
  silent empty table).
- checked: a/o30_gpu_guard.py beyond W2-03 / W2-04 - fail-closed start (mask read back, feed fresh, no npt-like
  process, all before Popen), ERROR_CAP ABORT path leaves the trainer suspended with the resume command and exit 79,
  no end line; `--resume-pid` checks pid + create time (+-0.01 s vs 3 decimals logged) + exe name; the tests in
  a/logs/gpu/cr9_guard_tests.out ran on the committed md5 and show the ABORT and resume paths on a direct child; the
  live r8 and r10 guard logs have the start line with pid + create time and `end: trainer exit 0 ... poll errors 0`
  (STATUS claim holds).
- checked: a/net_pack.sh - PCMASK is passed to pin_check.ps1 on both calls, so "every step, pin_check included"
  holds once O30_MASK is set (W2-05 is about the default).
- checked: a/logs/gpu/soups_w2_table.md vs commits 85d58c72 / 81c1f692 - soupC -2.253e-4 (z -50.2) / -1.343e-4
  (z -2.70) and soupE16 -2.087e-4 / -1.304e-4 (z -2.54) as claimed.
- checked: line endings and quoting of every reviewed .sh / .py (LF; cygpath for every path handed to a native tool;
  no backslash path inside an inline interpreter command).

## Also read: code in the range outside the focus list

- checked: a/logs/checks_gpu/scripts/depth_probe_ab.py (182 lines, the record copy of the net-vs-control depth / nps
  probe) - an engine given options must print the `--expect-load` line and no ERROR line or the probe exits 3 before
  any figure is produced (fail closed); rounds alternate A-B / B-A on one CPU at Idle; JSON written with `'x'`
  (no overwrite). Note only: its default `--mask 0x1` is CPU 0, a sanity-match CPU in this window (same class as
  W2-05; the checks of 13:05-13:39 ran before those matches started).
- checked: b/o30tuned_tuned184.patch (src/uci.cpp only) - `O30Tuned` check option, default false; true writes the
  8 tuned values, false writes the lock values, both clamped to the option range, then `tune::refresh()`; an invalid
  value is answered with an info string and changes nothing. Consistent with the commit cf354f86 claims (default =
  lock pins, true-then-false = lock pins, invalid value rejected); the exe itself was not run here.
- checked: b/logs/itemB/wait_cpu01.ps1, wait_cpu01_v2.ps1 - read-only pollers of the affinity masks of
  forge-v2-bullet / fastchess / forge_ltopgo* processes; never touch a process; exit 1 at their cutoff.

## Not verified (out of the review's reach or budget)

- The bullet library's `load_from_checkpoint` behaviour on a weights.bin of the wrong bucket count (the W2-02
  kb-vs-init mismatch case) - library source not in the branch.
- Whether cmd.exe keeps or drops an empty `O30_INIT_DIR=` from the environment block (W2-02: cold run vs panic) -
  not executed, both outcomes are bad.
- The Rust-vs-Python feature equality on 3,000 rows (a/logs/gpu/kb16_check_rfeatures.out) was taken from the log,
  not re-run (would need the trainer exe).
- The soup / expand tools were not re-executed on real checkpoints (reads of 10-25 MB files next to the live run);
  the author's logs were checked for consistency instead.
