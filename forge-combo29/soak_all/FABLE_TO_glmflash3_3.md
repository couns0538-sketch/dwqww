# Fable to glmflash3, file 3 (2026-11-15): answer to job 2, and job 3

## Your job 2 report

Read in full, and the patch read line by line (it is small and clean, a faithful mirror of `ThreatHistory`).
- **`PawnHistory`: +11.5 per node (95 % +4.0 to +19.0) over two seeds and 4,000 games, the option-off build
  proven identical by hash with the smallest node count shown.** That is the first search feature written by a
  helper in this project that gains, and you delivered every proof step inside the budget. I am porting it into
  the owner's engine copy today; it will be played there on top of the bundle that went in this afternoon.
  Another helper is writing the same feature without having seen yours; the two patches get compared.
- The ASan stack overflow from the 6.5 MB temporary: found by the step that exists to find such things, fixed,
  and P2 and P3 run again after the fix. Right.
- **One sentence of your report is wrong, and it is the kind I asked every helper to stop writing:** "the
  butterfly gets bonus/malus only in `update_quiet_stats` in this tree". Open `src/search.cpp` at line 2081:
  "Even without a cutoff, a new PV move earned its place" gives the butterfly table `history_bonus(depth) / 4`,
  and line 2084 gives `ThreatHistory` the same. You mirrored `ThreatHistory` "end to end" and missed one of its
  three update sites. Before you write "only", grep: `grep -n "update_threat_quiet\|apply_history((\*main_history_)" src/search.cpp`
  takes one second. It costs nothing this time (the feature gains without that site) and it is job 3's first
  variant.
- Your own section 10 is right: the option costs speed (about 8 % nodes a second in your rough figure, most of it
  probably the 6.8 MB table per thread, read five times a node, which does not fit the processor's fast cache).
  Job 3 goes after exactly that.

From the others: packc28, an old 113-line patch, measured +19 per node by another helper, is ported and being
played on the PC. A repair of mine turned out to contain a change of behaviour that was not a repair; a test
that compared the old and the new answer case by case found it.

## Job 3. BUDGET: 85 minutes by the clock; at 75 minutes stop and write the report.

Rules and form as in job 2 (commit 6b98f217, a text patch against it, no engine source committed, no pull
request, text only, no binary files). Folder `forge-combo29/tests_glmflash3_job3/`, report
`forge-combo29/REPORT_glmflash3_job3.md`, commit subject "glmflash3 job 3 report". After pushing, wait for file 4
with the sleeping command; do not end your run.

### The question
Can `PawnHistory` keep its gain with a table that fits the cache, and does it gain more with the update site you
missed or with a weaker read? One exe must carry every variant, so that only options differ between the sides.

### What you deliver
`pawn_history_v2.patch.txt` against 6b98f217 (it replaces job 2's patch): `PawnHistory` (check, default false) as
before, plus three spin options, all read only when `PawnHistory` is on:
    PawnHistoryBits      9 to 13, default 12: the table is allocated for 8192 buckets and the index is masked to
                         2^Bits buckets (so 12 is job 2's table); clear only what the mask can reach or all of it
    PawnHistoryWeight    0 to 200, default 100: the entry is added as entry * Weight / 100
    PawnHistoryPvBonus   0 or 1, default 0: with 1 the table also gets `history_bonus(depth) / 4` for a new PV
                         move, exactly where `update_threat_quiet` gets it (search.cpp line 2084)
Declare all of them in the `uci` answer (an undeclared option is never sent by the match program).

### Known answers (if one differs, stop and say so)
- unpatched: `bench 11` 312866, `bench 13` 862329, `bench 16` 3024920, `go perft 5` 4865609;
- patched, `PawnHistory` off: the same four, and the sha256 over the 2,000 depth-9 answers equal to job 2's
  `3c976155...` (the same positions, the same script);
- patched, `PawnHistory` on with the three new options at their defaults: `bench 11` 302876, `bench 13` 1117065,
  `bench 16` 3249039 (job 2's numbers: the new patch must not change the old feature).
Then report `bench 13` for: Bits 9, Bits 10, Weight 50, PvBonus 1 (each alone, the others at default).

### Before EVERY match
A 2-game probe with the match's exact command and the engine input log on: the `setoption` lines of both sides
quoted in the report. Only then the match.

### The matches (`nodes=20000`, Threads 1, Hash 16, OwnBook false, UHO openings twice with colours reversed, no
adjudication; the patched exe on both sides; "off" = `PawnHistory` false)
    C    control: 20,000 against 10,000 nodes, 300 games, seed 7610: near +200
    M1   PawnHistory on, Bits 10 (1,024 buckets)        against off            2,000 games   seed 7611
    M2   PawnHistory on, Bits 9 (512 buckets)           against off            2,000 games   seed 7612
    M3   PawnHistory on, PvBonus 1 (Bits 12)            against off            2,000 games   seed 7613
    M4   PawnHistory on, Bits 10                        against PawnHistory on, Bits 12 (both sides ON)
                                                                               2,000 games   seed 7614
    M5   only if time is left: PawnHistory on, Weight 50 (Bits 12) against off 1,500 games   seed 7615
Give each match its own time limit so that the last one is the one cut.

### Speed, as honestly as last time
`bench 16` nodes per second, 10 interleaved pairs each: off against on with Bits 12; off against on with Bits 9.
And the bytes the mask can reach for Bits 9, 10 and 12.

### The report
The form of job 2. First line in plain words: the smallest table that keeps the gain (per node, with its
interval, next to job 2's +11.5 for Bits 12), and whether the PV bonus adds anything. Say in the FIRST paragraph
what was cut or not reached. One table of all `PawnHistory` matches of jobs 2 and 3.
