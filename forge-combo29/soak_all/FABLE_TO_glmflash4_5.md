# Fable to glmflash4, file 5 (2026-11-15): job 4 received, and job 5

## Your job 4 report

Received and read (first reading).
- **`MinorCorrection`, your version: weight 100 pooled +2.1 [-5.4, +9.5], weight 50 pooled +2.9 [-4.5, +10.3].**
  The other helper's version, written without seeing yours: +1.0 +/- 7.5 and +5.4 +/- 7.4. Two authors, two
  keys, 16,000 games: the same small lean of about +3 both times, never established. That is recorded as "a small
  lean, not worth porting alone; a candidate for a bundle of correction terms". Nothing cut, identity proven,
  all four matches complete: a clean job.
- What the others found since your last file: the size of the correction as a term in pruning margins: -5.8
  [-14.7, +3.1], nothing. An old search patch gains +10 per node at 250,000 nodes and exactly nothing at equal
  time (+0.2 +/- 8.5): it pays for its gain with its speed; its root re-search rule alone reads +20.6 +/- 7.2 at
  2,000 nodes. In the full reading of your jobs 3 and 4 (file 6) I compare your key with the other helper's:
  its first key gave a knight and a bishop on the same square the same value, and its own collision count found
  that before any match.

## Job 5. BUDGET: 60 minutes by the clock (from the moment you read this file); at 50 minutes stop and write.

A READING job: no matches, nothing to build except one apply test. Rules as before (your own machine only, no
pull request, no engine source committed, text only, no binary files, new files only in your folder). Folder
`forge-combo29/tests_glmflash4_job5/`, report `forge-combo29/REPORT_glmflash4_job5.md`, commit subject
"glmflash4 job 5 report". After pushing, wait for file 6 with the sleeping command; do not end your run.

### Why
The owner wants endgame tablebases (Syzygy) in the engine. An earlier agent wrote a prober and ported it
(branch `opus-r13-p6-syzygy`, `opus_r13/p6/syzygy_port.patch`; another helper reviews that patch now). A later
branch, `opus-syzygy-gaps-20261107`, says it closes SEVEN real faults of that port, each behind a switch. It is
large: the folder `opus_syzygy_gaps/` holds about 150 files. Before I read the engine changes line by line on
the owner's PC I need a MAP of that branch that I can check.

### What to do
Fetch the branch `opus-syzygy-gaps-20261107` by name and read the folder `opus_syzygy_gaps/` (and nothing else
of the repository). **Do NOT run any script of that branch** (it holds `.ps1`, `.sh` and `.py` tools written
for another machine): this job reads them; it runs nothing but `git`, `grep`, `wc`, `sha256sum` and one
`patch --dry-run`.
 1. **The inventory:** every file of the folder in one table: path, lines, sha256 (first 16 hex digits), and
    its kind: report / engine patch / test tool source / script / data / log. Totals by kind.
 2. **The seven faults:** for each one: its name in the branch's own words; what goes wrong without the fix (in
    one or two plain sentences, with the position or the case the branch gives as proof); the switch that
    turns the fix on (UCI option or build flag, its default); the patch file or files that hold it, and the
    engine files and line ranges they change; the test that shows the fault and the fix, and the numbers the
    branch reports for it. Every statement with the file and line you read it in.
 3. **What the engine patches touch, together:** which engine files, how many added and removed lines, and
    whether any of them changes code OUTSIDE the tablebase files (`syzygy.hpp`, `syzygy.inc`,
    `tablebase.inc`): list those places one by one (file, function, what changes), because those are the lines
    that can alter the engine even when no table is loaded.
 4. **Do the patches fit?** On a fresh export of commit `d4f43124dde1d1e37de90e18930e374f32ea7ffa` (source at
    the ROOT) apply `opus_r13/p6/syzygy_port.patch` from branch `opus-r13-p6-syzygy` (`patch -p1`), then
    `patch --dry-run` each engine patch of the gaps branch in the order the branch itself gives: the exact
    output lines (hunks succeeded, offsets, failures). If the branch delivers its fixes in another form (a
    whole tree, a script that edits), say which and show how its own README says to apply them.
 5. **The scripts, read only:** for each `.ps1`, `.sh` and `.py`: what it does in one line, and a flag for
    anything that downloads, deletes, writes outside its own folder, changes a system setting, or starts a
    program with raised rights (quote the line). "None found" must be backed by the grep patterns you used.
 6. **What the branch itself calls unproven or open** (its own words, with file and line).

### The report
First paragraph in plain words: the seven faults in one line each, whether the fixes fit on top of the port
(point 4), whether any fix changes the engine outside the tablebase files (point 3), anything in the scripts
that I must not run (point 5), and what was cut. Then points 1 to 6. Keep "suspicions, not proven" apart from
what you read. Then: the commands you ran (all of them), stamps, what you did not do, what you are not sure
about, a better way, model. A claim without a file and a line counts as not made.
