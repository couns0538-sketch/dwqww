# Resume ledger - bitexact_check.ps1 -ResumeFrom (runner audit, 2026-11-06)

The run was on 2026-11-06 from 16:40:49 to 16:42:26 PC clock. Owner brief job 1: deploy the CR-approved runner fix to
all four tips, then prove that resume cannot lie.

## Shipped runner (all four tips, tools-only commits)

| branch | start tip | swap commit | runner before | runner after |
|---|---|---|---|---|
| opus-speed-20261105 | 277a8f90 | deefef64 | 5038452d (an older runner without -FenOptions) | 4d1c8d52 |
| opus-cut-nott-lmr-20261105 | 1c9fe4a4 | 0e796eb2 | f382cdc2 (blob aa87b6f0) | 4d1c8d52 |
| opus-tt-cut-node-20261105 | 87efb548 | 8b7b728e | f382cdc2 (blob aa87b6f0) | 4d1c8d52 |
| opus-nmp-tt-capture-20261105 | add89e04 | a8f00c42 | f382cdc2 (blob aa87b6f0) | 4d1c8d52 |

- The md5 values are content md5 of `opus_speed/tools/bitexact_check.ps1`. After the push, all four values were re-read
  with `git show <branch>:...`, and all four remote tips were checked with `git ls-remote`.
- The source copy was `D:\oleft2\tools_qa\bitexact_check_fixed_APPROVED_4d1c8d52.ps1`. The two other PC copies named in
  the brief also hash 4d1c8d52.
- Approved patch md5: e8744d8f. CR recheck md5: 8b4ea175.
- No guard was added, because every required case below was rejected. So the shipped md5 is still **4d1c8d52** on every
  tip, with no change against the approved file.
- `uci_lib.ps1` was not touched. QA's copy in `D:\oleft2\tools_qa\` allows mask 0xFFFF; the tips keep 0xF.

## Inputs
- Real priors (only read): `D:\oleft2\cnl\fens12k_on` and `D:\oleft2\cnl\fens12k_off`.
  - Both are full 12k runs: 12000 FENs, depth 13, `fens_12k_v2.txt` md5 e7dbf2c8.
  - Both were written by the old f382cdc2 runner, whose L3 line reads `depth 13:12000` with no space.
  - Ref: the lock trial_w6 4181a589. Cand: the cnl gate dcdec9a7.
  - The off prior ran with `-FenOptions UseNNUE=false`.
- Other exes used: the old lock v23 fd3a5190 (as the other ref) and the tcn gate 8151e220 (as the other cand).
- Command: `bash opus_speed/tools/resume_cases.sh`.
  - Output goes to `D:\opus_5h\runner_audit\`: `priors\<case>\` holds the edited copies, `runs\<case>\` the runner's
    output.
  - Every run uses `-ResumeFrom <prior> -SkipSan`, so no engine search and no sanitizer build take place.
  - A REJECT counts only when the run exits non-zero and prints the expected guard text.
- Evidence: `opus_speed/logs/resume_audit/` holds results.tsv (md5 44a1b004) and the console output of each case.

## Cases (runner = shipped 4d1c8d52, tree deefef64)

| case | input | expected | result | exit | runner text |
|---|---|---|---|---|---|
| K1 control | on prior, same exes, default options | ACCEPT | ACCEPT | 0 | VERDICT BIT-EXACT (L1-L3; L3 on 12000 FENs) |
| K2 control | off prior + `-FenOptions UseNNUE=false` | ACCEPT | ACCEPT | 0 | VERDICT BIT-EXACT (L1-L3; L3 on 12000 FENs) |
| K3 control | on prior cut right after the L3 PASS line (as if L4 crashed; this is what resume is for) | ACCEPT | ACCEPT | 0 | VERDICT BIT-EXACT (L1-L3; L3 on 12000 FENs) |
| a1 options | off prior, run without FenOptions | REJECT | REJECT | 1 | resume: prior L3 used FenOptions but this run has none |
| a2 options | on prior, run with UseNNUE=false | REJECT | REJECT | 1 | resume: FenOptions mismatch (this run: UseNNUE=false; prior: (none)) |
| a3 options | off prior, run with Hash=64 | REJECT | REJECT | 1 | resume: FenOptions mismatch |
| b1 binary | other cand exe (8151e220) | REJECT | REJECT | 1 | is not for this ref + cand (sha256 mismatch) |
| b2 binary | other ref exe (fd3a5190) | REJECT | REJECT | 1 | is not for this ref + cand (sha256 mismatch) |
| b3 binary | sig json sha256 edited to another exe | REJECT | REJECT | 1 | signature file ... belongs to another exe |
| c1 FEN set | `-Fens` = first 2000 lines of the 12k file (another md5) | REJECT | REJECT | 1 | the reused L3 line is for another FEN file or depth |
| c2 FEN set | `-FenDepth 11` | REJECT | REJECT | 1 | the reused L3 line is for another FEN file or depth |
| c3 FEN set | L3 md5 field edited to 00000000 | REJECT | REJECT | 1 | the reused L3 line is for another FEN file or depth |
| d1 truncated | log cut after 5 of the 10 L1 lines | REJECT | REJECT | 1 | lacks a complete L1-L3 PASS set |
| d2 truncated | log cut before L3 (L1 + L2 complete) | REJECT | REJECT | 1 | lacks a complete L1-L3 PASS set |
| d3 truncated | L3 `0 / 12000 identical ... PASS` | REJECT | REJECT | 1 | cannot parse L3 identical counts |
| d4 truncated | L3 count unreadable (`twelve-k / 12000`) | REJECT | REJECT | 1 | cannot parse L3 identical counts |
| d5 truncated | L3 total zero (`12000 / 0`) | REJECT | REJECT | 1 | cannot parse L3 identical counts |
| d6 truncated | one extra L1 FAIL line next to the complete PASS set | REJECT | REJECT | 1 | lacks a complete L1-L3 PASS set |
| d7 truncated | no bitexact.log in the prior folder | REJECT | REJECT | 1 | resume: no ...\bitexact.log |
| d8 truncated | no cand\sig_*.json | REJECT | REJECT (ungraceful) | 1 | Cannot bind argument to parameter 'Path' because it is null. |
| X1 extra probe | L3 `11999 / 12000 identical ... PASS` | REJECT | **ACCEPT** | 0 | VERDICT BIT-EXACT (L1-L3; L3 on 12000 FENs) |
| X2 extra probe | chained resume (the prior is K1's own resumed log) | REJECT | REJECT | 1 | lacks a complete L1-L3 PASS set (rejected by the format, not by a guard) |

**Counts:**
- Required cases: 17 / 17 REJECT, each with the expected text (a 3, b 3, c 3, d 8).
- Controls: 3 / 3 ACCEPT.
- Extra probes: X1 ACCEPT, X2 REJECT.
- Ledger total: 18 REJECT, 4 ACCEPT.

## For Code Review (deploy of 4d1c8d52 to the four tips; nothing queued)
1. Deploy: four tools-only commits (table above). The resume behaviour is proven by the table. No engine file or exe was
   changed.
2. **X1 is a finding.** No guard was added, because X1 is not a required case.
   - Resume checks that both L3 counts are above 0, but it does not check identical == total.
   - So a hand-edited log with `11999 / 12000 ... PASS` resumes as BIT-EXACT.
   - The runner itself never writes PASS for k < n (`bitexact_check.ps1` line 345: `if ($same -ne $n) FAIL`). Truncation
     cannot produce such a line either. Only an edited or forged log can.
   - Suggested one-line guard (CR to decide): `if ($nm.Groups[1].Value -ne $nm.Groups[2].Value) { throw ... }`.
3. d8 fails closed (exit 1), but only through a null-path exception. An explicit "resume: no signature json" throw would
   make the reason readable.
4. X2: a resumed log cannot be resumed again. Its lines end with `(resumed from ...)`, so the `PASS$` patterns find
   nothing. This fails closed, but by format, not by design.
5. Not tested, observation only: PowerShell's `-ne` is case-insensitive. So an option line spelled `UseNNUE=FALSE` would
   compare equal to `UseNNUE=false`.

## Reproduce
```
cd /f/ospd/wt && git checkout opus-speed-20261105
bash opus_speed/tools/resume_cases.sh D:/opus_5h/runner_audit_rerun   # new folder; never overwrites
cut -f1-5 /d/opus_5h/runner_audit_rerun/results.tsv
```
