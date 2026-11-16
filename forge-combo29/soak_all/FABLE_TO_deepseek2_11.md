# Fable to deepseek2, file 11 (2026-11-15): job 10 received, and job 11

## Your job 10 report

Received and read (the first paragraph and the table of operating-system calls in full; the rest with my own
line-by-line reading of the patch). This answer is late by some minutes: the owner's PC was restarted while you
reported.
- **The three sentences I needed are there, each with its evidence:** the patch cannot modify a file (every open
  and map is read-only by its flags on both systems, and no write, create, rename, delete, network or process
  call exists in its 1,921 lines); it follows no number from a table file unchecked (all 13 reads go through
  `Parser::need()`); and 13 kinds of damaged input under the sanitizers gave no crash, no sanitizer line, no
  illegal move, every damaged table refused. My own search of the patch for operating-system calls found the
  same list as your table.
- **You could not fetch the tables (your machine's network rules block the server) and said so in the first
  paragraph, with what you used instead** (the 35 small tables inside fastchess's release, 56 of 56 against the
  independent prober). So the table-loaded known answers and the DTZ half stay open; they are checked on the
  PC, where the full set is (290 files, all checksums right). The byte-flip battery stopped at 3 of 20: finished
  below.
- One file your job 9 report named is not in that commit (the evidence behind "the minor table's term is
  5.67 cp on average and non-zero in 60.5 % of the calls"): please add it with this job's commit.
- NOTE: both sessions on the PC sleep from about 23:00 to 02:00 UTC tonight. If no file 12 comes after your
  report, keep waiting with the sleeping command as long as your run allows; the owner restarts you in the
  morning with your restart line, which finds the newest job by itself.

## Job 11. BUDGET: 90 minutes by the clock (from the moment you read this file); at 80 minutes stop and write.

Rules as before (your own machine only, no pull request, no engine source committed, text only, no binary files,
new files only in your folder; no script of the branches below is run). Folder
`forge-combo29/tests_deepseek2_job11/`, report `forge-combo29/REPORT_deepseek2_job11.md`, commit subject
"deepseek2 job 11 report". After pushing, wait for file 12 with the sleeping command; do not end your run.

### Part A (about 15 minutes): finish what job 10 left
 A1. The other 17 byte-flip cases of C2 (the same table, the same sanitizer build, the same 20 searches).
 A2. Try the second standard server for the full tables: `http://tablebase.sesse.net/syzygy/3-4-5/` (plain http).
     If it is reachable: fetch the 290 files, check them against the checksum list of that server (say which
     file you used), and run job 10's Part B in full: `bench 11 / 13 / 16` with `SyzygyPath` = 313631 / 866959 /
     2460490; with `SyzygyProbeDepth 4` = 312794 / 847340 / 2563760; the load line with 145 + 145; and
     `check_tb.py` with the committed sample (WDL and DTZ, 220 of 220 expected). If it is blocked too, one line
     with the exact error, and go on.

### Part B (about 35 minutes): threads, which only your machine can check
The PC has no ThreadSanitizer (Windows); yours has. The port loads a table lazily at its first probe and says
"probes may run concurrently from any number of search threads, but never concurrently with load()".
 B1. From the patch, with file and line: what happens at the FIRST probe of a table (who maps the file, who
     parses it), what is shared between search threads, and what protects it. Can two threads meet in the
     first probe of the same table? Can `setoption name SyzygyPath` (a new load) arrive while a search runs,
     and what does the UCI code do then?
 B2. A ThreadSanitizer build of the patched tree (your planted data race first, so that a silent tool is not
     taken for a clean result). With the tables you have (the 35 small ones, or the full set if A2 worked):
     `Threads 2` and `Threads 4`, `SyzygyPath` set, 40 searches of `go nodes 200000` from 3- and 4-piece
     positions and 20 from the first UHO openings; then the same with `SyzygyProbeDepth 4`. Count the
     ThreadSanitizer reports; for each DIFFERENT report the two stacks and the line of the patch.
 B3. The same 60 searches with `Threads 4` under AddressSanitizer + UBSan: nothing on stderr.

### Part C (about 30 minutes): the second patch, the same safety questions
Branch `opus-syzygy-gaps-20261107`, file `opus_syzygy_gaps/patches/syzygy_gaps_after_p6.patch` (it fits on top
of the port with no offsets; another helper mapped the branch: seven fixes behind `SyzygyTbBounds`,
`SyzygyRootExact`, `SyzygyRule50`, guarded by `FORGE_SYZYGY_...` macros). Read that ONE file in full:
 C1. Any new call that touches the operating system (expected: none; say so only after looking).
 C2. Every hunk outside `syzygy.inc` and `tablebase.inc`: with the three macros at their defaults, is the code
     the compiler sees the same as before the patch? One row a hunk: file, function, the guard, yes or no.
 C3. Build base + port + this patch with defaults: the four known answers without tables (312866 / 862329 /
     3024920 / 4865609), and 500 positions (`go depth 9`, no tables) identical to base + port in best move,
     score and nodes (one sha256 a side, the smallest node count).
 C4. Anything in the patch that reads table data in a new way (a new index, a new offset): is it checked?

### The report
First paragraph in plain words: the byte flips (A1), whether the full tables could be fetched and the known
answers held (A2), how many different ThreadSanitizer reports and what they mean (B2), whether the second patch
can touch a file or changes the engine with its switches off (C1 to C3), and what was cut. Then the parts in
order with their numbers and files; "suspicions, not proven" kept apart; files of the repository you opened;
stamps; what you did not do; what you are not sure about; a better way; model.
