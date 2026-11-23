# SETUP_PLAN.md: the plan for the server day

Editor: Fable. **Version 2**, written at 2026-11-23T20:05:51Z (Fable's clock). Sources: the three independent failure lists
(`FAILURES_fable.md` F1 to F40, `FAILURES_astra.md` rows A-1 to A-13 in its order, `FAILURES_neon.md` NF-01 to
NF-35) and the messages up to Astra `125634Z`. Changed against version 1 (2c45594): D3, D4, D5, D6, D8, D10,
D12, D13 after Astra's votes (`125559Z`); new D14, D15; section 4 filled with Astra's formulas (`125634Z`);
section 7 is now the merged failure table; section 5 has the PC's check of its budget tool.

**How this file changes.** Astra and Neon propose in messages; I write the text in; a part gets the mark
SETTLED only by ONE joint message of both that names the decision as it stands here, plus my check on the PC
where one exists. Marks: **SETTLED**, **PROPOSED** (written in, not yet settled), **OPEN**, **OWNER** (only the
owner can decide; collected in section 9), **NOT MEASURED**. Nothing in this file is a claim that code does
something today; the last column of section 7 and section 8 say what exists.

## 1. The frame (the owner's direction; binding, not voted)

- Goal: **2,000,000,000 kept positions** for training, made on one rented machine in one day, checked at home.
- 23 hours produce; the last hour only checks. What fits into the 23 hours is calculated from MEASURED rates.
- Everything is moved compressed; everything that arrives is compressed and transferred automatically.
- Scripts run all of it, also while no session of ours can work. As little as possible is lost when something
  breaks. Filtering and checking run from the beginning.
- Every script is read line by line by Astra, Neon and Fable; three YES for the exact bytes, or it does not run.
- The plan must hold for another machine too (section 4).
- Nothing is installed on the home PC. Nothing of ours reaches INTO the PC: the PC fetches. No secret of ours is
  ever on the server.

## 2. The path of the data and the five counts (PROPOSED; Astra A-8, NF-08, F9, F34)

```
server:  worker plays whole games -> packer seals a PIECE (packed rows + compressed game records + seal)
         -> the piece stays in the server's spool for the whole lease (nothing is deleted there)
home:    stage a1  fetch -> CUSTODY: size, sha256 and chain hold; a durable receipt is written        (C1)
         stage a2  CONTENT: every game replayed, all five fields and the opening binding hold        (C2)
         stage b   CORRECTED: the PC's own after-game rescoring (lone king, tablebase)                (C3)
                   KEPT: the PC's filter; a ROUND's kept rows packed again, durably, with their count (C4)
         round text exists only for one training window at a time
```

| Count | What it counts | What it is good for |
|---|---|---|
| C0 sealed | raw rows in sealed pieces on the server | the server's own rate; never credit |
| C1 custody | raw rows in pieces that are at home with a durable receipt | "the bytes are safe at home" |
| C2 content | raw rows of games that passed the replay at home | "the games are right" |
| C3 corrected | games rescored by the PC's after-game step, by reason | the label is the PC's label |
| C4 kept | rows in durable packed round output after the filter | **the only count that is credit toward 2 billion** |

Every progress line and every decision names which count it uses, and the lags C0-C1, C1-C2, C2-C4 are
reported apart.

## 3. Decisions

| # | Decision | Mark | From |
|---|---|---|---|
| D1 | **Compression uses only what Python brings on both sides** (no tool installed anywhere). The PC's packer as built uses `lzma` preset 6 for the game records and for the raw fallback, each with a read-back check; rows are packed in its own form. `zstd` is not assumed. `lzma` or `zlib` for which part is decided by ONE measurement of the real packer and the real reader on both platforms with their installed interpreter (M7). Every archive form ever written must have a reader in the package. Neon measured (`130210Z`): `lzma` preset 6 costs little processor on game records but about 90 MiB of memory for each compressor at work on a large chunk, so compression runs in the packer process only, never once a worker; M7 measures processor AND peak memory, and whether ONE packer keeps pace with the pieces the full width makes a second. | PROPOSED; Astra AGREE, Neon AGREE | NF-34, Neon `124630Z`, F3 |
| D2 | **The server keeps every sealed piece for the whole lease**, fetched or not, acknowledged or not. The spool is sized for what the machine CAN make until the cutoff at its measured rate with home offline, not for the target (at 40,000 rows a second the day is about 16 GB, not 9.7). A volume that cannot hold that plus staging plus reserve fails the first hour. If the estimate outgrows the room during the day, production pauses and the sealed pieces stay. No pruning rule exists. | **SETTLED** (joint record Astra `130332Z` with Neon `130210Z`; Neon withdrew pruning) | F14, A-6, NF-19, NF-26 |
| D3 | **The pilot counts only the games it started**, with run, round, slot and game identity kept across both ends of its window; carried-in work is counted apart; a repeated receipt adds zero. **C4 moves in whole rounds, so the pilot's verdict is NOT read from a C4 difference** (at a true 25,000 a second a 20-minute window shows one finished round = 12,715): it is computed from stage rates of the SAME cohort: completed games an hour at the full worker count x C2 rows a completed game x kept share. The kept share is measured by the real filter over the pilot's games as ONE declared pilot range and compared with whole rounds of the PC (round 142: 0.9532); the LOWER one is used, both are printed. Each home stage (a1, a2, b) must show its own rate inside the window; otherwise the window is extended inside the first hour or the forecast is UNQUALIFIED. Heat is judged by games completed a minute, not by C4. | first sentence **SETTLED** (joint record `130332Z`); the measuring rule PROPOSED: Neon (`130210Z`) wants C4 over K >= 1 whole pilot rounds by exact wall time to the K-th round's completion at home; my text uses stage rates; BOTH can be printed and the lower one decide: say which | Astra `124732Z`, `125559Z`; NF-08; F9 |
| D4 | **The pilot's decision table has no gap.** Before any row: target already reached -> no row needed; time used up with rows outstanding -> outcome SHORT with the exact deficit; not enough evidence (D3) -> UNQUALIFIED, nothing starts by script. Then, with r = forecast C4 rate and n = needed rate for the FULL target: r < floor: stop in the first hour so the machine can be given back; floor <= r < n: the owner's predeclared choice (a reduced target is its own outcome with its own n), no improvising, never a second rental or a charge by script; n <= r < 1.10 n: self-play only, the margin (r/n - 1) reported; r >= 1.10 n: self-play, and only the predeclared match queue may use the measured surplus, in complete pairs. The floor (proposed 0.50 n) and the 1.10 are policy for the owner, not measurements. | **SETTLED** as text (joint record `130332Z`; the three cases before the rows are from both votes); floor, 1.10 and the choice are OWNER; the PC's tool does not do this yet (section 5) | Astra `124728Z`, Neon Q2, F10 |
| D5 | **Time.** At the start the lease's real start and absolute end (UTC, as the provider shows them) and the host's boot identity are recorded. Durations inside one boot use a steady clock. The cutoff is D = min(start + 23 h, end - max(1 h, measured closing time)). **Dispatch of new games stops at D - g** (g = the longest game measured in the pilot plus a margin), so that games in flight end before D. **At D any search still running is ended, its game is thrown away whole and its identity reported as unfinished; after D no search runs**, only sealing of finished work, transfer and checks. After a restart of the host, production resumes only if the time left can be established from the recorded absolute end and a trustworthy clock; otherwise it stays paused and says so. A restart never buys a fresh 23 hours. | PROPOSED (changed to Astra's text of `125559Z`; Neon agrees with that change, `130210Z`): ready for your joint record | A-1, NF-03, NF-28, F21 |
| D6 | **Three YES.** A ledger line is `YES <sha256> <seat>`; three distinct seats (astra, neon, fable) for every file of the FROZEN package: scripts, helpers, config, net, book, fixtures. Files the day GENERATES (pieces, receipts, reports) are bound by their run identity, custody and verification rules instead: they cannot have a YES. The manifest's own hash is pinned OUTSIDE the package (on this branch and in the PC's ledger), and the verifier is started by a path that is itself pinned. The start, every stage, the restart path and the close path check it; a helper that the real entry point imports and the manifest does not list must fail the rehearsal. A file Fable wrote is also read by Opus on the PC. | PROPOSED; Astra AGREE with these clarifications | F1 to F4, A-3, NF-02, NF-35 |
| D7 | **The home side after a restart of the PC is NOT unattended today.** What exists: a guard program that keeps the home steps running and restarts them, started by a double click. After a reset or a restart by Windows somebody must double-click again; until then nothing is fetched. A start-at-logon entry would also leave a gap after a cold start with nobody logged in; either way the outage is MEASURED (M6) and written here. The server's full-day spool (D2) keeps the bytes while the lease lives; it cannot deliver after the lease has ended. Any change to Windows for this is the owner's alone (O3). The word "unattended" is used for the home side only with this sentence beside it. | PROPOSED; Astra AGREE, Neon AGREE | F25, NF-24, A-12 |
| D8 | **Home is three stages that progress independently**, each with its own durable queue on disk and a bound on its room: a1 fetch + custody (C1); a2 replay (C2); b rescoring + filter + packing of kept rows, one round at a time (C3, C4). A slow or frozen later stage never stops an earlier one. Data stays packed at home; round text exists for one training window at a time; before every write the free room of the PHYSICAL volume (two folder names on one volume are one budget) is compared with the owner's floor for it plus a margin, with everything that will lie there at the same time added up, and the durable replacement is written before the temporary data it replaces goes. Test: freeze a2 for ten minutes while a1 goes on. | PROPOSED (changed to Astra's text; Neon agrees, `130210Z`): ready for your joint record | NF-21, NF-25, A-2, A-9, F26, F29 |
| D9 | **A round is a predeclared range of game identities**, not a number of rows. Its kept output may vary. A deliberately shorter last range is named BEFORE that range is played; a range that is not sealed by the server and verified in full at home is never counted or rounded up; an earlier missing game is never relabelled as "the short last range", and a game that was never played is never a confirmed zero. | PROPOSED; Astra AGREE | A-11, NF-29, F35 |
| D10 | **Build.** Variants are built from the frozen source with the PC's real flags (the PC's build script is the reference, not the CMake file: the flags for the mate guard and for the king-bucket net are given explicitly). Each variant twice; reference numbers, perft counts, the fixed games against the PC's known answers; only instruction sets the processor has; each binary's rate measured with self-play at the full worker count, never with bench. **Profiled against plain, three outcomes declared beforehand (the first debate's N16): measurably slower = the profile is wrong: repair it or use the plain build; measurably faster = the profiled build; not decided = the rightly profiled build, the report says "gain not shown".** None of the three waives the pilot's rate. A missing or stale profile fails the build (compiler flags that make it an error); the profile run fails on ANY engine error line and without the net's start line. The log names the binary that is started, by sha256, and the worker's start-up check proves which evaluator answers. | PROPOSED (changed: version 1's "only if faster" contradicted N16; Astra's catch; Neon agrees): ready for your joint record | F6, NF-04, NF-05, A-4 |
| D11 | **Matches on the day:** none, unless D4's last row holds or 2 billion are already C4 at home. Until a match is authorized and its time measured, its share is zero. If matches run beside self-play the mixed rate is measured, switching and draining time counted; a falling rate takes the threads back at a pair boundary. | PROPOSED; Astra AGREE | Neon Q1, NF-10, NF-33, A-10 |
| D12 | **The end has four independent states**: every receipt reconciled; data still missing, with identities and bytes (exact bytes for a produced piece that the server's manifest names; "unknown" for an identity that was reserved and never finished); clean-up of the server verified; the provider's release confirmed. A missing receipt neither triggers a clean-up of the only copy nor renews a paid lease. Originals stay as long as the lease allows while any needed receipt is missing. Billing ends only by the owner's act. | **SETTLED** (joint record `130332Z`) | A-13, NF-30, F36, F37 |
| D13 | **When the machine may be given back.** Not on a row count alone. The server writes a TERMINAL INVENTORY at the end: every reservation by slot and epoch, every piece with its predecessor's fingerprint, every seal, and for every identity one of: produced (piece named), confirmed empty, unfinished at D, set aside. **CLEAN RELEASE** = that inventory is at home and reconciled: every produced piece has custody (C1) and passed content (C2) or is named as set aside; and everything the home stages b need without the server (frozen filter, tables, config) is at home, present and hashed; **and at least one complete round of THIS day has already gone through stage b to C4 with no failed tablebase probe** (Neon: otherwise a defect of rescoring or filter is found when the machine is gone). C3 and C4 may then finish at home after the lease. **DECLARED PARTIAL RELEASE or EXPIRY** = anything less, reported as such with the exact deficit. Forecast before the release: actual C4 + kept share x eligible C2 rows not yet filtered; the share as a lower bound from rounds filtered on THIS day (a historical mean is not a bound: at a share of 0.91 instead of 0.953 the same raw rows end 90 million short, Neon); earlier C4 counted once. | PROPOSED (rewritten after Astra's CHANGE and Neon's attack of `130210Z`; the twelve-reservation case of `125204Z` is its test) | F29, F36, NF-25, A-8, A-11 |
| D14 | **One writer a slot, and a chain.** A slot's spool is locked for the life of its worker; the guard starts a replacement only after the old process group is gone; every piece names the sha256 of the slot's piece before it and the worker's start count (epoch). A second writer or a lost piece then shows at home as a fork or a gap in the chain, whatever the file names say. | PROPOSED, new (today's code has the journal and the numbering, no lock, no chain) | A-5, F13, D13 |
| D15 | **A restart of the server is survived without anybody.** The guard is started by the system at boot from one unit file that is part of the package (three YES); it checks the package, then D5's rule for the time left, then resumes every slot from its journal. | PROPOSED, new | F15, F16, NF-15, A-1 |

## 4. Start minimums for ANY candidate machine (PROPOSED; Astra `125634Z`, my wording)

A machine is accepted in the first hour only if every row holds, with MEASURED inputs of that machine. A
missing measurement is an explicit UNQUALIFIED, never a guessed number and never an automatic rental. The raw
samples are kept with machine class, effective limits, workload manifest, worker count, time window.

| Resource | Test | A case that must fail |
|---|---|---|
| Processor | Recorded: affinity and cpuset, online threads, quota and period, instruction flags, throttle counters before and after. The minimum is the smallest TESTED worker count whose forecast C4 rate (D3) is at least n. A one-thread scaling estimate is a forecast, not a qualification. | 5 visible processors with a quota of 4; a narrow fast pilot standing in for the full width |
| Memory | Workers, packer and guard run together at the chosen width: measured peak of the whole GROUP (not a sum of per-process figures that count shared pages again), plus staging, plus compression bursts and several workers restarting at once, plus a reserve, against the memory really available on this boot under its limits. | enough host memory under a lower service limit |
| Server room | Per physical file system: free bytes >= the retained sealed bytes the machine can make until the cutoff with home offline + the largest unfinished pieces and temporary output + package, build and log growth + floor and reserve; every byte counted once. Measured as unique packed bytes an hour at full width. | a disk sized for the target only; an outage at a higher-than-needed rate |
| Home room | Per real volume: free now >= the worst growth still to come there at one time (packed arrivals, temporary text, set-aside pieces, the training window) + the owner's floor + margin; the durable replacement counted before the temporary data is released. | two folder names on one volume counted as two budgets; a rebuilt and a marked round text lying side by side (about 3.1 GB for one round on the PC; Astra's citation of the first debate's evidence, not recounted here) |
| Processes, open files, file entries | Measured peak in the scope that applies + room for retries, restarts and the close <= every soft and hard limit; per-process descriptor limits and the group's process limit apart; real mounts, writable folders, free file entries as well as bytes. | free bytes but no free file entries; a guard plus two replacement workers over a process limit that the clean pilot passed |
| Time and the home stages | Seconds of production left = D (D5) - now - what must still run exclusively. A budget exists only if that is positive and qualified. Rates of C1, C2, C3 and C4 are measured apart beside what the PC does that day; the day's credit cannot exceed the slowest necessary stage. | two hours gone leaves 21, not 22; the server makes 25,000 a second while home keeps 20,000: 23 hours credit at most 1.656 billion on the day, the rest is catch-up after the lease and is reported apart |

Also required: a compiler and library that reproduce the PC's fixed games node for node (D10); Python with
`lzma`, `zlib`, `hashlib`; a secure-shell server. The paid machine's own numbers (M4) cannot exist before it
does: before the rental the FORMULAS and the allowed outcomes are frozen; the pilot fills the row; the scripts
choose among those outcomes.

## 5. Rates and sizes (each with its source)

- Needed C4 rate n: 2,000,000,000 / (23 x 3600) = **24,155 a second** (rounded up) if all 23 hours produce.
  With the first two hours gone and one hour reserved: 2,000,000,000 / 75,600 = **26,456**. With 36,000,000
  pilot rows already credited: 1,964,000,000 / 75,600 = **25,979**. By hand (me), by Neon (`125330Z`), by Astra.
- **The PC's budget tool on these cases** (run by me on the PC; the tool is a draft from before this debate):
  it decides them rightly (26,455: not covered; 26,456: covered; 24,155 and 25,979: covered), but it prints the
  need rounded to one decimal (26455.0 for 26455.03, a figure at which it itself answers "not covered"); time
  used up with rows outstanding is answered as "bad input" like a broken file; it knows two outcomes where D4
  has four and the three cases before the rows; it lets matches in as soon as the target is covered. It takes a
  rate as given: the pilot's isolation (D3) is not in it. It is rewritten when D3, D4, D5 are settled, and
  comes to the three-YES read then.
- Round 142 on the PC: 15,258,168 kept of 16,007,134 raw rows (kept share 0.9532).
- **Packed size.** 1.99 (packed rows) + 2.64 (compressed game records) bytes per RAW row, on 30 games with 3,930
  rows: a small sample. About **9.7 GB** for 2 billion kept at round 142's kept share; about 16 GB if the
  machine makes 40,000 a second all day (D2 sizes for that). M5 replaces the sample.
- The PC's own self-play rate a worker (M1): measured by Opus this morning; my recount from his raw files is
  owed and comes as a message before a number of it is written here.
- NOT MEASURED: the server's rate and memory a worker (M4), the PC's stage rates a1, a2, b beside what else
  it does that day (M2, M3), the real packer's and reader's speed per codec (M7), recovery times at home (M6).

## 6. The day

### 6.1 The first hour (deadline: O2)
1. Machine check against section 4. Fail: stop, one line says which row.
2. Package unpacked; manifest and three-YES ledger checked against the pinned hash (D6). Fail: stop.
3. Builds (D10). Fail of every variant: stop.
4. Fixed games through the REAL path: worker -> packer -> fetch -> home stages, all five fields and the end
   lines equal to the PC's known answers; one fixed game's sha256 under the written byte rule equal on both
   sides. Fail: stop.
5. Pilot at the full worker count, judged by D3. Then D4.
6. The budget table is written from the pilot: which row of D4 holds, D and D - g (D5), what fits.

### 6.2 The 23 hours
- Server: the guard keeps workers, packer and spool alive (D14, D15); one stop rule; nothing is a child of a
  login.
- Home: stages a1, a2, b (D8). One progress line an hour, written at home also when the server is silent: C0
  to C4, the three lags with the oldest unacknowledged piece, the trailing hour's rate AND the cumulative rate,
  the needed rate, set-aside counts, failed tablebase probes, the share of equal games, free room above the
  floors on both machines.
- Any conflict of two complete records under one identity, any content failure, any failed tablebase probe:
  that piece or range is set aside whole, counted, never credited; production goes on.

### 6.3 The last hour
- From D - g no new game; at D no search (D5). The last pieces are sealed; each slot writes its final seal; the
  server writes the terminal inventory (D13).
- Home drains. A piece of a game finished before D that arrives late may still add credit in this hour: the
  report gives the count AT D and the count after the drain, with both times.
- The closing report has three classes: verified complete rounds; identities with zero rows; incomplete ranges
  with the exact missing identities (never credit). Then the four states of D12, and CLEAN or DECLARED PARTIAL
  by D13.

## 7. The merged failure table

One row a failure. "Lists" = where it stands in the three independent lists. "State" = what the PC's code does
TODAY: **built** (with the test that proves it), **partly**, **not built**. A row is done only when its planted
test fails without the guard, on the real script, in the rehearsal.

| # | What goes wrong | Lists | What notices it; what the script does | Planted test | State today |
|---|---|---|---|---|---|
| 1 | A file is not the approved bytes; an unlisted helper; changed line ends | F1, F3, A-3, NF-02, NF-35 | D6: ledger checked at start, every stage, restart, close; root pinned outside | one byte changed; an unlisted file imported by the entry point; an archive tampered consistently | not built (a ledger tool exists on the PC, unread; nothing calls it) |
| 2 | Package incomplete; wrong net; a folder given as the net | F2, NF-06, A-4 | manifest; the net's start line with its stored checksum; a queen-up probe far from zero; refusal before the first game | eleven changed inputs | built: worker start-up, test T6 |
| 3 | A number from memory instead of a measured file | F4, F40 | every input of the budget names its raw file; missing or stale: no start | a budget input without its file | not built |
| 4 | The machine is not as ordered; limits under the visible threads; data disk not mounted; open-file and process limits | F5, F8, A-2, NF-01, NF-27 | section 4 in the first hour | each failing case of section 4 | not built (a machine check exists, never run, written before section 4) |
| 5 | The build is not the PC's engine; wrong instruction variant; profile traps | F6, NF-04, NF-05, A-4 | D10 | a missing profile; a profile of another source; an engine error line in the profile run | not built (a build script exists, never run); M8 open on the PC's own profile driver |
| 6 | An option is refused and the engine plays on; the wrong evaluator answers | F7, NF-06, A-4 | the worker reads every answer; the start-up search must equal the known answer | Hash 32 on purpose; a misspelt option | built: T6, `known/startup_hash32.json` |
| 7 | The two machines hash different bytes | F33, NF-07 | one fixed game's sha256 as a known answer on both sides | a last line break more | partly: the six fixed games' digests are known answers; the byte rule is not written down |
| 8 | The pilot counts the wrong thing: server rows, carried-in rows, repeats, a window too short | F9, A-10, NF-08, NF-09 | D3 | Astra's case: 27,000,000 carried in + 3,000,000 own + 200 repeats must read 2,500 a second | not built |
| 9 | The first hour runs over | F10 | a written deadline; O2 decides which of two things happens | - | not built |
| 10 | Matches take threads the target needs | NF-10, A-10 | D4, D11 | a rate that falls under 1.10 n while a match runs | not built |
| 11 | A worker's engine dies or hangs; its error pipe fills; it fails again and again | F11, NF-11, A-5 | a time limit on every answer; both pipes read; the unfinished game thrown away whole; three failures in a row end the worker | a real kill in a run of 30 games; three failures | built in the worker: T5, T7, T11; the restart BY A GUARD is not built |
| 12 | The same game twice; colliding seeds; too many equal games | F12, NF-14, A-5, A-7 | identity from run, slot and counter, never the clock; credited once at home; the rolling share of equal games in the hourly line (about 1.9 % is healthy by Neon's count, alarm above 5 %) | the same pieces delivered twice; the same games under fresh identities | built: P3, P4; the rolling share is not built |
| 13 | No new-game command between two games | NF-12 | known answer for exactly that fault | the command left out before game 2 | built: T2, `known/n12_no_newgame.json` |
| 14 | Rows tied to the wrong opening | F22, NF-13 | A23: the binding digest over identity, sent line, rows, end line; the reader computes the opening itself | results, identities, sent lines exchanged; a consistent rewrite | built: T9, T10, P8, P9 |
| 15 | A piece is cut while it is written | F13, NF-17 | write, flush, checksum, rename; a journal; a restart finishes a closing or cuts the tail | five constructed states | built: T4; the flush of the DIRECTORY after a rename is open (read-me, point 5) |
| 16 | Two writers on one slot; an old worker wakes late | A-5 | D14 | a second worker started on a living slot; a piece with a wrong predecessor | not built |
| 17 | The server's disk fills; core dumps; logs | F14, NF-26, A-6 | D2: pause at a floor, never delete; no core files; bounded logs | a tiny floor | not built |
| 18 | The server restarts | F15, A-1 | D15, D5 | a restart five minutes before D | not built |
| 19 | The login that started it ends | F16, NF-15 | nothing is a child of a login | the starting shell killed | not built |
| 20 | Memory grows; the system kills for memory; too many open files | F17, NF-27 | the guard reads memory; a worker over its limit restarts at a game boundary; fewer workers while slot identities stay | a worker made to grow | not built |
| 21 | The rate falls; a process lives and nothing is verified | F18, NF-09, NF-32, A-12 | the hourly line at home with trailing and cumulative rate; a stage without progress is named | the server stopped mid-rehearsal: the line still comes and says so | not built |
| 22 | Two guards at once | F19, NF-16 | a lock that names a living process | a second start | not built |
| 23 | Somebody must stop it | F20 | one stop rule read by every loop and every wait | - | partly: worker and packer each read a stop file of their own |
| 24 | The clock is wrong, jumps, or resets with a restart | F21, NF-03, A-1 | D5 | the clock set forward; a restart | not built (today: the wall clock against a given end time) |
| 25 | The line is down; a connection hangs half open; a prompt waits for a person | F23, NF-18, NF-31 | fetch without any prompt, with time limits and growing waits, forever | the line cut for ten minutes before the last receipt | not built |
| 26 | A piece arrives damaged, half, or with right checksums and a wrong move | F24, NF-17, NF-20 | size and sha256; the piece built again at home must have the WORKER's sha256; the replay | one byte changed; one wrong final move with every checksum fitted | built: P6, P7, P8 |
| 27 | A piece is visible before it is closed; an acknowledgement is lost | A-6, NF-19 | the offer file is written last by a rename; D2: nothing is removed | a piece without its offer file | built: P1, P11; the packer's removal mode must come OUT (D2) |
| 28 | The PC is down, asleep, or another program holds a file at a rename | F25, NF-24, A-12 | D7; the home guard; a retried rename; the programs ask Windows not to sleep while they run | the home guard's process killed; a held file | partly: a home guard exists on the PC (unread); no retry; no sleep request |
| 29 | The PC's disk runs short; two paths on one volume | F26, NF-21, A-2 | D8 | two folders on one volume | not built |
| 30 | The server is not the server; a secret leaks | F27, F28, NF-31 | a pinned host key, never a "continue?"; nothing secret on the server, on this branch or in a chat | a changed host key | not built |
| 31 | Checking is slower than producing | F29, NF-25, A-9 | D8, D13, the three lags | replay frozen for ten minutes | not built; M2 and M3 not measured |
| 32 | A game fails its check in hour 9 | F30, NF-20 | the piece set aside whole with the reason, counted, asked for again; production goes on | P7's piece | partly: asked for again (P5 to P7); set-aside counts and the hourly line are not built |
| 33 | Arrival order decides; two complete records under one identity disagree | F31, NF-22, A-7 | A26 of the first debate: a fixed rule in the home program, tested with all orders | 120 orders of five pieces; +19 against +42 | not built (the receiver changes for it) |
| 34 | The PC's result corrections are skipped; a tablebase probe fails; no game is ever rescored | F32, NF-23 | the home step calls the loop's OWN function; it stops when the tables do not open; zero rescored in 10,000 games is an alarm (about 76 expected, Neon) | tables taken away | built: the round-text test, 10 checks; the alarm is not built |
| 35 | The totals do not add up; kinds of credit are mixed | F34, A-8 | section 2: five counts, reconciled in the last hour | - | not built (today's receiver knows "credited" only) |
| 36 | The day ends short; the last range | F35, A-11, NF-29 | D9 | a short declared range and an incomplete one side by side | not built |
| 37 | A search runs after the cutoff; the tail of a slot is not sealed | NF-28, A-11 | D5; each slot's final seal | a long game started just before D | partly: the worker seals its last, partly filled piece at a stop (T1); the cutoff rule is not built |
| 38 | Everything produced is acknowledged and a round is still short | Astra `125204Z` | D13: the terminal inventory | twelve reservations, eleven finished, seven pieces, one missing seal: 4 kept rows short of 9, zero pieces missing | not built |
| 39 | The machine is given back too early; billing goes on after the work has stopped | F36, NF-30, A-13 | D12, D13 | home offline at the release time | not built |
| 40 | Something of ours stays on a machine we no longer hold | F37 | clean-up only after reconciliation, and it says what it removed | - | not built |
| 41 | No session of ours can work | F38 | nothing waits for a session; alarms are files and one plain line | - | by design; to prove in the rehearsal |
| 42 | A session changes a running thing by hand | F39 | during the day a session only reads; a change is a new version with three YES at a piece boundary | - | rule |
| 43 | Match pairs are lost or counted twice across a restart | NF-33 | durable pair identities; only if matches run at all | a kill in the middle of a pair | not built |
| 44 | The codec is missing on one side | NF-34 | D1; a round trip at both starts | an unknown codec name in the manifest | partly: the packer reads back every part it writes; no check at the start |
| 45 | A substitute machine is booked, or a lease renewed, by a script | A-13 | never; only the owner | - | rule |

## 8. What exists on the PC today, and the scripts for the three YES

| Piece | State on the PC | On this branch for the read |
|---|---|---|
| player (worker, engine driver, record form) | written, tested (95 checks, 6 planted faults caught) | `debate/server_day/scripts/run/` |
| packer and seal | written, tested (with the receiver: 34 checks, 8 planted faults caught); its removal mode comes out (D2) | `scripts/run/packer.py` |
| home receiver; home step to round text | written, tested; NOT yet changed to A26, to the five counts and to three stages | `scripts/home/` (read now, will change) |
| budget tool; three-YES ledger tool; home guard | written and tested by Opus before this debate; the budget tool is rewritten after D3 to D5 settle (section 5) | after my read |
| Linux build script; machine check | written, NEVER RUN, older than D10 and section 4 | `scripts/linux/` |
| server guard with start at boot; lock and chain; hourly line; pause at a disk floor; fetch with pinned host key; terminal inventory; clean-up | NOT BUILT | - |
| full rehearsal at home (cable pulled, program killed, disk full, PC restarted) | NOT DONE | - |

Seven places where today's code differs from this plan are listed in `scripts/README.md`. The YES ledger of
this debate is `debate/server_day/APPROVALS.md` (it does not exist yet: no script is approved).

**What this means, said plainly:** of 45 rows, the guards inside ONE worker, the packer's proof and the home
content check are built and tested (rows 2, 6, 11 to 15, 26, 27, 34). Everything that makes the day run with
nobody there (rows 16 to 25, 28 to 31), the pilot and budget (8 to 10), the five counts and the end (33, 35 to
40) is not built. No machine is rented before those exist, have three YES, and have passed a full rehearsal.

## 9. For the owner (collected; I ask him once, before any rental) — OWNER

- O1. If the pilot's forecast is below what 2 billion need: take the lower total that fits, or stop and give
  the machine back, or something else he names. Also his: the floor under which the day is called off in the
  first hour (proposed: half the needed rate) and the surplus from which matches may run (proposed: 10 %).
- O2. The first hour's deadline: start with the last binary that passed, or call the day off.
- O3. The home PC after a restart: is a start-at-logon entry, made by himself, wanted, or does the double click
  stay (D7)? And: may the home programs ask Windows not to go to sleep while they run (a request a program makes
  for itself; no setting is changed)?
- O4. Does the PC's own loop pause its self-play on that day, so that the processor is free for the home stages
  (M2 and M3 decide whether this is needed)?
- O5. The provider's end of the lease and billing: what happens at the end by itself, and that giving the
  machine back is his act (D12). What he wants done if data is still missing at that moment.

## 10. Measurements owed (each gets its raw file and a line here)

- M1 the PC's self-play rates (Opus's files; my recount). M2 home stages a1 and a2: rows a second. M3 home
  stage b: rescoring and filter rows a second. (M2, M3, M5, M7, M6 are asked of Opus on the PC since 20:00Z.)
- M4 the server's rate, memory and longest game a worker (only on a machine of that kind: at the pilot).
- M5 bytes a row at scale and bytes really sent with retries. M6 recovery times at home (program killed; PC
  restarted). M7 the real packer and reader with `lzma` against `zlib` on both platforms.
- M8 the PC's own profile driver: does it end with an error on an engine error line (Neon's proof 3)?
