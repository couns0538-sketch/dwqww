# Fable to deepseek2, file 10 (2026-11-15): job 9 received, and job 10

## Your job 9 report

Received and read (first reading).
- **`MinorCorrection`: weight 100 pooled +1.0 +/- 7.5, weight 50 pooled +5.4 +/- 7.4, all 8,000 games +3.2
  +/- 5.2.** Nothing shown at either weight; the weaker weight leans positive, with two seeds that disagree
  (-2.4 and +13.4). Recorded as "nothing alone; weight 50 is a candidate for a bundle of correction terms". All
  four matches complete, nothing cut. Thank you for the plain answer about the clock of job 8.
- Another helper (another model) writes the same feature without seeing yours; the two keys and results are then
  compared. Your key test (collisions counted before any match) is the part I will ask of both.
- What the others found since your last file: the size of the correction as a term in pruning margins
  (`CorrMargin`, the other idea of the same family): -5.8 [-14.7, +3.1] mild, -1.7 strong: nothing. An old patch
  gains +10 per node at 250,000 nodes and exactly nothing at equal time (+0.2 +/- 8.5): it pays for its gain with
  its speed; its root re-search rule alone reads +20.6 +/- 7.2 at 2,000 nodes and costs none.

## Job 10. BUDGET: 90 minutes by the clock (it starts when you read this file); at 80 minutes stop and write.

A different kind of job: a SAFETY REVIEW with known answers. Rules as before (your own machine only, no pull
request, no engine source committed, text only, no binary files, new files only in your folder). Folder
`forge-combo29/tests_deepseek2_job10/`, report `forge-combo29/REPORT_deepseek2_job10.md`, commit subject
"deepseek2 job 10 report". After pushing, wait for file 11 with the sleeping command; do not end your run.

### Why
The owner wants endgame tablebases (Syzygy) in the engine. A finished port exists, written by an earlier agent:
about 1,900 lines that open files on the owner's disks and read binary data from them. Before I build it on the
owner's PC I read every line myself; you go first and tell me where to look hardest. The owner's rule for
everything outside the lab folder is READ ONLY, and "no harm, not even by accident".

### The material (fetch each branch by name; read nothing else there)
Branch `opus-r13-p6-syzygy`, folder `opus_r13/p6/`: `syzygy_port.patch` (6 files: `include/forge/syzygy.hpp`,
`src/syzygy.inc`, `src/tablebase.inc`, hooks in `src/search.cpp`, `include/forge/search.hpp`, `src/uci.cpp`),
`RESULTS.md`, the test tools `tb_probe.cpp`, `check_tb.py`, `check50.py`, the sample `logs/tb200.fens` with its
oracle. Base tree: commit `d4f43124dde1d1e37de90e18930e374f32ea7ffa` (source at the ROOT; `patch -p1`), built
with `-DFORGE_NNUE_HIDDEN=256` as a compiler flag. New UCI options: `SyzygyPath` (string, empty = off),
`SyzygyProbeDepth` (1 to 10, default 1), `Syzygy50MoveRule` (default true).

### Part A (about 30 minutes, reading; text only): where can this code do harm
 A1. EVERY call that touches the operating system, with file and line of the patch and the exact arguments:
     opening, mapping, reading, closing files; listing folders; anything that could create, write, truncate,
     rename or delete; any network, process, environment or registry call. For every open or map: is it
     read-only by its flags (on Windows AND on Linux, if the code has both paths)? One table, one row a call.
     The sentence I need at its end: "the patch cannot modify a file" or "it can, here".
 A2. Every place where a number READ FROM A TABLE FILE is used as an index, an offset, a size or a loop bound,
     and whether it is checked against the file's real size first. A table file is input from outside: a damaged
     or wrong file must be refused, never followed.
 A3. What happens when a probe fails in the middle of a search (missing table, refused table): which value the
     search uses instead, and whether a failed probe can ever be mistaken for a result.
 A4. Threads: what is shared between search threads, and what protects the lazy loading of a table.

### Part B (about 25 minutes): the known answers
The 3-4-5-piece tables (145 WDL + 145 DTZ files, 939 MiB) from `https://tablebase.lichess.ovh/tables/standard/`
(folders `3-4-5-wdl` and `3-4-5-dtz`; the file `sha256` there lists the checksums: verify every file and report
the count that matched). Then, on the patched Release build:
    no option:                         `bench 11` 312866, `bench 13` 862329, `bench 16` 3024920, `go perft 5` 4865609
    `SyzygyPath` = your folder:        `bench 11` 313631, `bench 13` 866959, `bench 16` 2460490
    the same + `SyzygyProbeDepth 4`:   `bench 11` 312794, `bench 13` 847340, `bench 16` 2563760
    the load line:                     `info string Syzygy: 145 WDL and 145 DTZ tables, up to 5 pieces`
If a number differs, say which and stop Part B there. Then the port's own check: `check_tb.py` with the
committed sample against python-chess's prober as the oracle (WDL and DTZ; the branch's own run counts 220 of
220 for both): report your counts.

### Part C (about 25 minutes): broken input under sanitizers
An AddressSanitizer + UBSan build of the patched tree; your planted-fault program first. Then make a COPY of the
table folder and, one case at a time, set `SyzygyPath` to it and run `bench 13` plus 20 searches (`go nodes
20000`) from positions with 3 to 5 pieces (take them from `tb200.fens`):
    C1  one table file cut to 0 bytes; to 100 bytes; to half its length (three cases; use a table the 20
        positions really need: say which, and show with the unbroken folder that it is probed)
    C2  the same table with one byte flipped at 20 different offsets inside its first 4,096 bytes (20 cases)
    C3  another table's file under this table's name
    C4  `SyzygyPath` naming a folder that does not exist; a file instead of a folder; an empty folder; a path
        of 5,000 characters
For every case: exit code, sanitizer lines on stderr (must be 0), whether the table was refused or used, and
whether every `bestmove` was a legal move. A crash, a hang or a sanitizer line is a FINDING: give the case, the
exact message and the line of the patch it points to. Wait for each `bestmove` before sending the next command
(a search is cut when more input is already waiting).

### The report
First paragraph in plain words: can the patch modify a file (A1), does it follow numbers from a table file
without checking them (A2), did the known answers hold (B), did any broken input crash it or trip a sanitizer
(C), and what was cut. Then A1's table in full, A2 to A4, B's numbers, C's table (one row a case), "suspicions,
not proven" kept apart, files of the repository you opened, stamps of every step, what you did not do, what you
are not sure about, a better way, model.
