# SETUP_PLAN.md: the plan for the server day

Editor: Fable. **Version 2.4**, written at 2026-11-23T22:23:59Z (Fable's clock). **2.4 changes no decision's text.** 2.3
(sha256 `cff7c298...`) has AGREE from Astra (`150955Z`) and from Neon (`151130Z`). 2.4 brings two older summary
lines into line with the agreed `FORMATS.md` (Astra `151735Z`: the C1 row of section 2, the last bullet of 6.2,
and row 32 of section 7 with it), enters one more point under D2 (the room of the close, Astra `151916Z`), and
brings section 8 up to the votes as they stand. Each is marked **[2.4]**.
Version 2.3 was written at 2026-11-23T22:07:30Z (Fable's clock). **2.3 changes no decision's text.** It
enters, below the decision table, what all three seats agreed after 2.2 (five entries marked **[2.3]**, each
with its messages), brings section 8 up to what exists in version 2, and adds one owed measurement (M2b).
Version 2.2 was written at 2026-11-23T20:34:07Z (Fable's clock). Sources: the three independent failure lists
(`FAILURES_fable.md` F1 to F40, `FAILURES_astra.md` rows A-1 to A-13 in its order, `FAILURES_neon.md` NF-01 to
NF-35) and the messages up to Astra `125634Z`. Changed against version 1 (2c45594): D3, D4, D5, D6, D8, D10,
D12, D13 after Astra's votes (`125559Z`); new D14, D15; section 4 filled with Astra's formulas (`125634Z`);
section 7 is now the merged failure table; section 5 has the PC's check of its budget tool. 2.1: D3's measuring
rule (Astra `130738Z`, Neon `130210Z`), D8's disk bound, D14's identity, `FORMATS.md`, `APPROVALS.md`. **2.2: sections 2 and 4 and
EVERY decision D1 to D15 are SETTLED** (your joint record on 2.1's text; D3 is 2.1's text unchanged). The
precisions you recorded with it are sentences in D2, D6, D13, D14, D15; M7's result, the opening mode and the
games without rows are entered below the table; section 7 has a planted test in every row; the PC's
measurements are at the end of section 10.

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

## 2. The path of the data and the five counts (**SETTLED**: joint record Neon `131930Z` with Astra `132125Z`; Astra A-8, NF-08, F9, F34)

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
| C1 custody | raw rows in pieces that are at home with a durable receipt **[2.4] and whose chain of seals connects to the slot's genesis** (`FORMATS.md` 2.1; Astra `151735Z`: a valid receipt that arrives out of order counts as RECEIVED at once and its rows enter C1 when its predecessors are there; waiting for a predecessor is normal, and the home bottleneck and the close are read from the right one of the two) | "the bytes are safe at home" |
| C2 content | raw rows of games that passed BOTH checks at home: (1) the packed form gives back the sealed plain bytes exactly and every record's binding holds (this is what proves a score: +19 for +42 changes the sealed bytes); (2) the home reader's own move rules replay the opening it computed for that id, every move, every row's position and ply, and the end. **No search is repeated for it**: an engine replay is run only on the fixed games of the first hour, to decide a conflict (A26) and on small spot samples (Astra `132008Z`, Neon `132330Z`) | "the bytes are the server's, and the games are legal games of this run" |
| C3 corrected | games rescored by the PC's after-game step, by reason | the label is the PC's label |
| C4 kept | rows in durable packed round output after the filter | **the only count that is credit toward 2 billion** |

Every progress line and every decision names which count it uses, and the lags C0-C1, C1-C2, C2-C4 are
reported apart.

## 3. Decisions

| # | Decision | Mark | From |
|---|---|---|---|
| D1 | **Compression uses only what Python brings on both sides** (no tool installed anywhere). The PC's packer as built uses `lzma` preset 6 for the game records and for the raw fallback, each with a read-back check; rows are packed in its own form. `zstd` is not assumed. `lzma` or `zlib` for which part is decided by ONE measurement of the real packer and the real reader on both platforms with their installed interpreter (M7). Every archive form ever written must have a reader in the package. Neon measured (`130210Z`): `lzma` preset 6 costs little processor on game records but about 90 MiB of memory for each compressor at work on a large chunk, so compression runs in the packer process only, never once a worker; M7 measures processor AND peak memory, and whether ONE packer keeps pace with the pieces the full width makes a second. | **SETTLED** (joint record Neon `131930Z` with Astra `132125Z`, on version 2.1's text; M7's result is entered below the table) | NF-34, Neon `124630Z`, F3 |
| D2 | **The server keeps every sealed piece for the whole lease**, fetched or not, acknowledged or not. The spool is sized for what the machine CAN make until the cutoff at its measured rate with home offline, not for the target (at 40,000 rows a second the day is about 16 GB, not 9.7). A volume that cannot hold that plus staging plus reserve fails the first hour. If the estimate outgrows the room during the day, production pauses and the sealed pieces stay. No pruning rule exists. **Both forms count for the room:** the plain records AND the packed offers lie on the server at once (Astra `131001Z`, from a six-game fixture: about 170 GB of plain records for 2 billion kept, against 9.7 GB packed); the pilot records the peak of both, and section 4's room is computed from both. | **SETTLED** (joint record Astra `130332Z` with Neon `130210Z`; Neon withdrew pruning) | F14, A-6, NF-19, NF-26 |
| D3 | **The pilot counts only the games it started**, with run, round, slot and game identity kept across both ends of its window; carried-in work is counted apart; a repeated receipt adds zero. **The measuring rule:** K >= 1 whole production-equivalent rounds, declared beforehand, are timed from the start of their first game to durable C4 of all K, with empty queues at the start and no carry-in: unique C4 / that whole time is the END-TO-END rate. Beside it the same cohort gives the STAGE capacities under the intended home load: completed games an hour, raw rows a game, the whole round's kept share, and the rates of C1, C2, C3, C4. Both are published in the same unit; **the LOWER decides** D4. A window that ends inside a round runs on to the round's end within the first hours' budget, or the forecast is UNQUALIFIED. A small range or a historical round never supplies the kept share (Astra's constructed round keeps 100 of 200 where such a rule predicts 190); only durable C4 is certain. Heat is judged by games completed a minute, never by C4, which moves in whole rounds. *Recorded with it:* one round timed cold reads about 9 % under the steady rate, four rounds 2.4 % (the last round's drain is counted once); taking the lower is the careful side, and K >= 2 narrows it. | **SETTLED** (joint record Neon `131930Z` with Astra `132125Z`, on version 2.1's text; my 2.2 draft with a drain term is withdrawn: you had settled the simpler rule) | Astra `124732Z`, `125559Z`, `130738Z`, `131633Z`; Neon `130210Z`, `131430Z`; NF-08; F9 |
| D4 | **The pilot's decision table has no gap.** Before any row: target already reached -> no row needed; time used up with rows outstanding -> outcome SHORT with the exact deficit; not enough evidence (D3) -> UNQUALIFIED, nothing starts by script. Then, with r = forecast C4 rate and n = needed rate for the FULL target: r < floor: stop in the first hour so the machine can be given back; floor <= r < n: the owner's predeclared choice (a reduced target is its own outcome with its own n), no improvising, never a second rental or a charge by script; n <= r < 1.10 n: self-play only, the margin (r/n - 1) reported; r >= 1.10 n: self-play, and only the predeclared match queue may use the measured surplus, in complete pairs. The floor (proposed 0.50 n) and the 1.10 are policy for the owner, not measurements. | **SETTLED** as text (joint record `130332Z`; the three cases before the rows are from both votes); floor, 1.10 and the choice are OWNER; the PC's tool does not do this yet (section 5) | Astra `124728Z`, Neon Q2, F10 |
| D5 | **Time.** At the start the lease's real start and absolute end (UTC, as the provider shows them) and the host's boot identity are recorded. Durations inside one boot use a steady clock. The cutoff is D = min(start + 23 h, end - max(1 h, measured closing time)). **Dispatch of new games stops at D - g** (g = the longest game measured in the pilot plus a margin), so that games in flight end before D. **At D any search still running is ended, its game is thrown away whole and its identity reported as unfinished; after D no search runs**, only sealing of finished work, transfer and checks. After a restart of the host, production resumes only if the time left can be established from the recorded absolute end and a trustworthy clock; otherwise it stays paused and says so. A restart never buys a fresh 23 hours. | **SETTLED** (joint record Neon `131930Z` with Astra `132125Z`, on version 2.1's text) | A-1, NF-03, NF-28, F21 |
| D6 | **Three YES.** A ledger line is `YES <sha256> <seat>`; three distinct seats (astra, neon, fable) for every file of the FROZEN package: scripts, helpers, config, net, book, fixtures. Files the day GENERATES (pieces, receipts, reports) are bound by their run identity, custody and verification rules instead: they cannot have a YES. The manifest's own hash is pinned OUTSIDE the package (on this branch and in the PC's ledger), and the verifier is started by a path that is itself pinned. The start, every stage, the restart path and the close path check it; a helper that the real entry point imports and the manifest does not list must fail the rehearsal. A file Fable wrote is also read by Opus on the PC. Every program of the package is started with `-I -B` (a cache file written into the package changes its hash list: Neon reproduced it, `131400Z`), and the unpacked package is made read-only after its check. The list tool refuses a link and anything that is not a plain file or a folder, and takes every path once. **In the ledger the LATEST line of a seat for a path and its bytes counts:** a later NOT YET ends an earlier YES (Astra `131652Z`). | **SETTLED** (joint record Neon `131930Z` with Astra `132125Z`, on version 2.1's text; with the two rules recorded there (the latest line of a seat counts; `-I -B` and a read-only package), which 2.2 has as sentences) | F1 to F4, A-3, NF-02, NF-35 |
| D7 | **The home side after a restart of the PC is NOT unattended today.** What exists: a guard program that keeps the home steps running and restarts them, started by a double click. After a reset or a restart by Windows somebody must double-click again; until then nothing is fetched. A start-at-logon entry would also leave a gap after a cold start with nobody logged in; either way the outage is MEASURED (M6) and written here. The server's full-day spool (D2) keeps the bytes while the lease lives; it cannot deliver after the lease has ended. Any change to Windows for this is the owner's alone (O3). The word "unattended" is used for the home side only with this sentence beside it. | **SETTLED** (joint record Neon `131930Z` with Astra `132125Z`, on version 2.1's text) | F25, NF-24, A-12 |
| D8 | **Home is three stages that progress independently**, each with its own durable queue on disk and a bound on its room: a1 fetch + custody (C1); a2 replay (C2); b rescoring + filter + packing of kept rows, one round at a time (C3, C4). A slow or frozen later stage never stops an earlier one until that earlier stage's OWN measured disk budget is full; then that stage pauses and says so. Data stays packed at home; round text exists for one training window at a time; before every write the free room of the PHYSICAL volume (two folder names on one volume are one budget) is compared with the owner's floor for it plus a margin, with everything that will lie there at the same time added up, and the durable replacement is written before the temporary data it replaces goes. Test: freeze a2 for ten minutes while a1 goes on. | **SETTLED** (joint record Neon `131930Z` with Astra `132125Z`, on version 2.1's text) | NF-21, NF-25, A-2, A-9, F26, F29 |
| D9 | **A round is a predeclared range of game identities**, not a number of rows. Its kept output may vary. A deliberately shorter last range is named BEFORE that range is played; a range that is not sealed by the server and verified in full at home is never counted or rounded up; an earlier missing game is never relabelled as "the short last range", and a game that was never played is never a confirmed zero. | **SETTLED** (joint record Neon `131930Z` with Astra `132125Z`, on version 2.1's text; the opening mode is entered below the table) | A-11, NF-29, F35 |
| D10 | **Build.** Variants are built from the frozen source with the PC's real flags (the PC's build script is the reference, not the CMake file: the flags for the mate guard and for the king-bucket net are given explicitly). Each variant twice; reference numbers, perft counts, the fixed games against the PC's known answers; only instruction sets the processor has; each binary's rate measured with self-play at the full worker count, never with bench. **Profiled against plain, three outcomes declared beforehand (the first debate's N16): measurably slower = the profile is wrong: repair it or use the plain build; measurably faster = the profiled build; not decided = the rightly profiled build, the report says "gain not shown".** None of the three waives the pilot's rate. A missing or stale profile fails the build (compiler flags that make it an error); the profile run fails on ANY engine error line and without the net's start line. The log names the binary that is started, by sha256, and the worker's start-up check proves which evaluator answers. | **SETTLED** (joint record Neon `131930Z` with Astra `132125Z`, on version 2.1's text) | F6, NF-04, NF-05, A-4 |
| D11 | **Matches on the day:** none, unless D4's last row holds or 2 billion are already C4 at home. Until a match is authorized and its time measured, its share is zero. If matches run beside self-play the mixed rate is measured, switching and draining time counted; a falling rate takes the threads back at a pair boundary. | **SETTLED** (joint record Neon `131930Z` with Astra `132125Z`, on version 2.1's text) | Neon Q1, NF-10, NF-33, A-10 |
| D12 | **The end has four independent states**: every receipt reconciled; data still missing, with identities and bytes (exact bytes for a produced piece that the server's manifest names; "unknown" for an identity that was reserved and never finished); clean-up of the server verified; the provider's release confirmed. A missing receipt neither triggers a clean-up of the only copy nor renews a paid lease. Originals stay as long as the lease allows while any needed receipt is missing. Billing ends only by the owner's act. | **SETTLED** (joint record `130332Z`) | A-13, NF-30, F36, F37 |
| D13 | **When the machine may be given back.** Not on a row count alone. The server writes a TERMINAL INVENTORY at the end: every reservation by slot and epoch, every piece with its predecessor's fingerprint, every seal, and for every identity one of: produced (piece named), confirmed empty, unfinished at D, set aside. **CLEAN RELEASE** = that inventory is at home and reconciled: every produced piece has custody (C1) and passed content (C2) or is named as set aside; and everything the home stages b need without the server (frozen filter, tables, config) is at home, present and hashed; **and at least one complete round of THIS day has already gone through stage b to C4 with no failed tablebase probe** (Neon: otherwise a defect of rescoring or filter is found when the machine is gone). C3 and C4 may then finish at home after the lease. **DECLARED PARTIAL RELEASE or EXPIRY** = anything less, reported as such with the exact deficit. Forecast before the release: actual C4 + kept share x eligible C2 rows not yet filtered; the share as a lower bound from rounds filtered on THIS day (a historical mean is not a bound: at a share of 0.91 instead of 0.953 the same raw rows end 90 million short, Neon); earlier C4 counted once. An extrapolated share is called an empirical lower scenario, never a bound: only C4 that is already durable counts as certain, and missing or set-aside work stays a deficit after a release (Astra `131547Z`). | **SETTLED** (joint record Neon `131930Z` with Astra `132125Z`, on version 2.1's text; with the precision recorded there: only durable C4 is certain, a forecast is a labelled scenario) | F29, F36, NF-25, A-8, A-11 |
| D14 | **One writer a slot, an identity, and a chain.** A slot's spool carries the run's identity, written once; a worker that finds another identity stops before it changes anything (the first read's finding 8). The spool is locked for the life of its worker; the guard starts a replacement only after the old process group is gone; every piece names the sha256 of the slot's piece before it and the worker's start count (epoch). A second writer or a lost piece then shows at home as a fork or a gap in the chain, whatever the file names say. The identity names run, slot, root seed, opening rule, manifest, net and engine (Neon `131430Z`). | **SETTLED** (joint record Neon `131930Z` with Astra `132125Z`, on version 2.1's text; the fields are in `FORMATS.md` 1.3 to 1.5) | A-5, F13, D13 |
| D15 | **A restart of the server is survived without anybody.** The guard is started by the system at boot from one unit file that is part of the package (three YES); it checks the package, then D5's rule for the time left, then resumes every slot from its journal. The machine check proves that the system's own service manager is process 1 and starts the unit after a restart; where it is not (many rented containers), the machine is UNQUALIFIED unless its provider's own restart hook is part of the checked package (Neon `131430Z`). | **SETTLED** (joint record Neon `131930Z` with Astra `132125Z`, on version 2.1's text; with the check recorded there that the service manager is process 1) | F15, F16, NF-15, A-1 |

**Entered under settled decisions (each is a measurement or a declaration the decision asks for, not a new rule):**

- **D1, M7's result.** Game records: `lzma` 6 (2.30 to 2.32 bytes a raw row; 424,000 rows a second on Neon's
  Linux host, 540,000 on the PC; under 10 % of one thread at 40,000 rows a second). **The plain-text fallback is
  NOT `lzma` 6:** it handles 37,000 rows a second on Linux and 43,000 on the PC, under what a full server can
  make. It is `zlib` 6 (431,000 rows a second, 18.4 bytes a raw row against 14.5; Neon `132330Z`). And the
  fallback's real cost is the WAIT before it: this morning's packer gives the converter 1,800 s for EVERY piece
  (Astra `132505Z`: 36 rows a second while that lasts). So: one bounded attempt a piece (a small multiple of the
  measured time of a piece), after three failures in a row a FALLBACK MODE that is written down and survives a
  restart, a probe of the converter now and then on a piece that is already offered, every sealed input kept,
  and a pause when the plain-text path cannot keep its own limits.
- **D9, the opening mode (W5 f of the first plan allows two).** The day uses the INDEPENDENT mode: every id's
  opening is drawn from (root seed, id) and computed again at home; there is no allocator and so none of its two
  crash cases. Equal games are counted (section 7 row 12), a game is never dropped for an equal position alone,
  and what the mode costs in doubled work is part of its own measured rate (Astra `132138Z`; Neon: 0 equal games
  in 495 on four workers).
- **Games without rows are about 1 % of all games** (Neon: 5 of 500; the PC: 16 of 2,000): completed games that
  end by a mate score straight after the opening. They are counted as completed games with zero rows, never
  refused (`FORMATS.md` 1.4 and 2.2).
- **[2.4] D2, the room of the close** (Astra `151916Z`, `152250Z`; Neon `152200Z`). The close needs room of its
  own, and it scales with what is SCHEDULED, not with what was played: with 16,384,000 scheduled ids unplayed at
  an early stop the per-id parts of the range seals and of the terminal inventory took 2,409,435,136 allocated
  bytes on her test volume, with one outstanding round of 128,000 ids 18,829,312. Three answers, all kept.
  (1) The admission test, agreed by both seats: before a schedule is published the guard sizes its possible
  close on each real volume from the ranges really outstanding (id lengths, codec, the open pieces' seals, the
  free file entries too) and HOLDS a schedule that would eat that reserve above the floor, before a game of it
  is dispatched. (2) A rolling horizon, agreed by both seats and legal under `FORMATS.md` 1.2: a schedule
  commits a bounded number of rounds ahead and the next one extends it, published durably before a slot needs
  the new range; the pilot's cohort stays fixed (D3); no started range and no stop time moves. My condition on
  it, as the editor: it makes PRODUCTION depend on the guard publishing in time, so the horizon is never under
  two rounds, and a late extension is a planted test (the slot waits, loses time and nothing else, and the
  hourly line names it). (3) `FORMATS.md` 2.4 writes the `never_dispatched` ids of a range as ONE interval
  (PROPOSED there, mine; its sizes are NOT MEASURED), which takes the scaling out of the files themselves. The
  rehearsal: the close near the floor with many scheduled ids and few games played; every range seal, the
  compressed inventory and the footer are written and verified, and the floor holds.
- **[2.3] D10, how the profiled and the plain build are timed** (Astra `144008Z`, `145040Z`; Neon `145000Z`,
  `145830Z`; Fable `215209Z`: agreed by all three). Two binaries with the same sha256 are never compared: the
  verdict is `identical_binary` and no effect is reported. Before the comparison ONE binary is timed against
  ITSELF, at the comparison's own length, width, opening blocks and day load: Astra gave the same binary under
  both labels eight times and the rule of that hour answered faster twice, slower twice, undecided four times
  (the same bytes read +7 % and -8 %, and five cohorts later -17 % and -10 %), so a short pair of repetitions
  is no yardstick. The number of repetitions and a paired uncertainty criterion are declared before the first
  timing; the rule is symmetric (slower is called by the same rule as faster, so that a truly worse profile
  still reaches "repair it or use the plain build"); the paired raw wall times are kept; when the time ends
  before the two separate, the qualified profile is used and the report says "gain not shown". The
  comparator's record of a game carries whether the opening loop COMPLETED, beside its move list; its two
  required cases: root seed `edge3146` (mate at ply 7: nothing is sent, `sent none`, `openingend plies 7 reason
  nomoves`) and `edge4013` (mate exactly at ply 8: the game command IS sent, zero rows).
- **[2.3] D3 and D4, the budget tool's boundaries** (Astra `140827Z`, `143323Z`; Neon `144130Z`). Every
  comparison is an exact inequality of integers, cross-multiplied BEFORE any rounding (rates in thousandths of
  a kept row a second). The order of the decision, each with its required case: (1) the target is already
  durable = target reached, no dispatch needed, whatever the rate (900 s left, 2 billion durable, rate 0);
  (2) no time left with rows outstanding = SHORT by the exact count (0 s, 1,999,999,999 durable: short by one
  row, never "invalid input"); both come before any rate is qualified; (3) the floor (with a floor of half the
  needed rate: 1,000 s, 25,000,001 rows to make, 12,500 rows a second is BELOW it, because 2 x 12,500,000 is
  less than 25,000,001); (4) the surplus for matches: self-play only while n <= r < 1.10 n, a queue of whole
  pairs becomes eligible from r >= 1.10 n (80,000 s, 2 billion: 26,000 a second is self-play only, 27,500 is
  eligible). The floor and the 10 % are the owner's values (O1). **Section 4's processor minimum is expressed
  against the target the owner AUTHORIZED**, and the tool gives two separate answers: are the resources and
  the evidence valid, and is the full target covered. Required case: 80,000 s, 20,000 a second at the largest
  safely tested width, a floor of 12,500: QUALIFIED evidence of a shortfall with a measured scenario of 1.6
  billion; with O1 "take the lower total" self-play runs under the declared lower target, with O1 "stop" it
  stops, without O1 dispatch is held; a rate guessed from one worker, or unknown disk headroom, stays
  UNQUALIFIED in all three. The capability probe before the rental and the paid first hour's pilot have
  separate states, so that a missing paid rate can never block the pilot itself.
- **[2.3] Section 4, what the machine check reads** (Neon `133500Z`; Astra `141912Z`, `143622Z`). Limits are
  read along the WHOLE chain of enclosing groups (at the root of a host without a namespace the files do not
  exist): processors = min(affinity, the smallest quota on the chain), memory = min(total, the smallest
  limit), processes = min(the user's limit, the smallest group limit, the kernel's thread limit); the throttle
  counters before and after the pilot. Instruction flags are the INTERSECTION over every processor of the
  affinity set. Per file system (folders grouped by device number, their budgets SUMMED): free bytes and free
  file entries, not read-only, not `noexec` where the engine lies. Core dumps off for the engine, enough open
  files, the boot id, the service manager as process 1 (D15). **A ceiling is not headroom** (Astra `143622Z`):
  for the launch the EXTRA peak is compared with (limit - current use) at EVERY enclosing level and with the
  host's available memory, the baseline subtracted once. Required fixture: leaf memory limit 4 GiB with 0 used
  and 1 of 512 processes; parent 8 GiB with 7 GiB used and 510 of 512 processes; host 32 GiB available; 2 GiB
  and four tasks asked = REFUSED (a check of ceilings alone says yes). **Room in two modes** (Astra `141912Z`):
  the disk probe reports the capacity for the normal form AND for a packer that stays in fallback (originals
  plus offers for the target: about 168 GB all normal, 175 GB with a quarter in fallback, 197 GB all fallback;
  263 and 310 GB at 40,000 raw rows a second for 23 hours; logical bytes of two samples, the real machine
  measures ALLOCATED bytes for both). A volume that covers only the normal mode is admitted with the fallback
  envelope reserved, or with the settled pause or the owner's lower total enacted BEFORE the floor is crossed,
  the open slots' last seals budgeted. A closed original is never discarded for room.
- **[2.3] D14 and D15, which machine goes on after a restart** (`FORMATS.md` 1.1 and 1.3; Neon `143000Z` 4;
  Astra `135328Z`, `141212Z`). The boot guard goes on by itself only on the SAME instance, proved by the machine
  id and at least one hardware value that is not a placeholder. A copy of the spool on a second machine, and a
  machine whose identity cannot be proved, hold for a person. A REPLACEMENT machine (the first is gone or not
  reachable) is a NEW run with its own header, machine check and first hour; nothing of the old spool is
  continued there, and what the old machine sealed counts only through its own chain and receipts.
- **[2.3] D8 and D13, a local outage at home is not a verdict on the games** (Astra `144620Z`; Neon `145000Z`;
  `FORMATS.md` 2.3): a table file or the staging volume that goes away during stage b leaves the round PENDING,
  the failed attempt recorded for good, and the round is made again as a whole once the identical inputs are
  back by their hashes. No missing prerequisite supports a clean release.

## 4. Start minimums for ANY candidate machine (**SETTLED**: joint record Neon `131930Z` with Astra `132125Z`, with the room counted as below; Astra `125634Z`, my wording)

A machine is accepted in the first hour only if every row holds, with MEASURED inputs of that machine. A
missing measurement is an explicit UNQUALIFIED, never a guessed number and never an automatic rental. The raw
samples are kept with machine class, effective limits, workload manifest, worker count, time window.

| Resource | Test | A case that must fail |
|---|---|---|
| Processor | Recorded: affinity and cpuset, online threads, quota and period, instruction flags, throttle counters before and after. The minimum is the smallest TESTED worker count whose forecast C4 rate (D3) is at least n. A one-thread scaling estimate is a forecast, not a qualification. | 5 visible processors with a quota of 4; a narrow fast pilot standing in for the full width |
| Memory | Workers, packer and guard run together at the chosen width: measured peak of the whole GROUP (not a sum of per-process figures that count shared pages again), plus staging, plus compression bursts and several workers restarting at once, plus a reserve, against the memory really available on this boot under its limits. | enough host memory under a lower service limit |
| Server room | Per physical file system: free bytes >= the retained sealed bytes the machine can make until the cutoff with home offline + the largest unfinished pieces and temporary output + package, build and log growth + floor and reserve; every byte counted once. Measured in ALLOCATED bytes of everything kept at once on that volume (sealed plain records, seals, packed offers, temporary files, logs, reserve) an hour at full width: about 75 bytes a raw row for the plain records alone, so about 160 to 180 GB for the target and 260 to 285 GB at 40,000 rows a second for 23 hours (Astra `131001Z`, Neon `131930Z`, the PC's 75.1). A 100 GB volume is refused in the first hour, not found full in the ninth. | a disk sized for the target only; an outage at a higher-than-needed rate |
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
- **[2.4]** (Astra `151735Z`: this bullet said "set aside whole" for every case; `FORMATS.md` 0.1, 2.2 and 2.3
  distinguish the cases, and they bind.) Bytes that cannot be rebuilt, a bad binding, or a seal that does not
  describe its piece refuse the WHOLE piece. A record that is sound in its bytes is judged by itself for C2: a
  game whose meaning fails is set aside and named, the other games of its piece count. A failed required LOCAL
  probe (a table file, the staging volume) leaves the round pending for a retry with the identical inputs. A
  conflict of two complete records under one identity stops both pieces' credit for that id (A26 decides). A
  game that stays defective is a named deficit of its round, and a partial round earns zero C4 even when some
  of its games passed C2. Production goes on in every one of these cases. Her fixture for the home reader:
  three genuine games, the middle one with a sent line one opening move short under a valid binding (piece
  sha256 `f9a36d17...`): the piece is read, that one game set aside, 198 of 345 rows pass the rules; the same
  fault under the old binding refuses the whole piece.

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
| 9 | The first hour runs over | F10 | a written deadline; O2 decides which of two things happens | a simulated clock crosses the first-hour deadline during the last build, once with a qualified complete fallback and once without: only the outcome the owner chose (O2) happens; a binary alone never passes the approved bytes, the start-up answers and the pilot minimum; without a qualified fallback zero games and the reason; the set-up time is counted once (Astra `130946Z`, Neon `131430Z`) | not built |
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
| 23 | Somebody must stop it | F20 | one stop rule read by every loop and every wait | STOP set while a worker is inside a game, the guard sleeps in a retry and the fetch is between two pieces; then the guard restarted with STOP still there: no new reservation anywhere, long waits wake within the stated bound, finished work is sealed and offered, a restart starts no search, no engine process is left; the emergency stop and the ordinary end are tested apart (Astra `130946Z`, Neon `131430Z`) | partly: worker and packer each read a stop file of their own |
| 24 | The clock is wrong, jumps, or resets with a restart | F21, NF-03, A-1 | D5 | the clock set forward; a restart | not built (today: the wall clock against a given end time) |
| 25 | The line is down; a connection hangs half open; a prompt waits for a person | F23, NF-18, NF-31 | fetch without any prompt, with time limits and growing waits, forever | the line cut for ten minutes before the last receipt | not built |
| 26 | A piece arrives damaged, half, or with right checksums and a wrong move | F24, NF-17, NF-20 | size and sha256; the piece built again at home must have the WORKER's sha256; the replay | one byte changed; one wrong final move with every checksum fitted | built: P6, P7, P8 |
| 27 | A piece is visible before it is closed; an acknowledgement is lost | A-6, NF-19 | the offer file is written last by a rename; D2: nothing is removed | a piece without its offer file | built: P1, P11; the packer's removal mode must come OUT (D2) |
| 28 | The PC is down, asleep, or another program holds a file at a rename | F25, NF-24, A-12 | D7; the home guard; a retried rename; the programs ask Windows not to sleep while they run | the home guard's process killed; a held file | partly: a home guard exists on the PC (unread); no retry; no sleep request |
| 29 | The PC's disk runs short; two paths on one volume | F26, NF-21, A-2 | D8 | two folders on one volume | not built |
| 30 | The server is not the server; a secret leaks | F27, F28, NF-31 | a pinned host key, never a "continue?"; nothing secret on the server, on this branch or in a chat | a changed host key | not built |
| 31 | Checking is slower than producing | F29, NF-25, A-9 | D8, D13, the three lags | replay frozen for ten minutes | not built; M2 and M3 not measured |
| 32 | A game fails its check in hour 9 | F30, NF-20 | **[2.4]** as 6.2 now says: the GAME set aside by itself and named when its record is sound and its meaning is not; the whole piece refused and asked for again when its bytes, a binding or its seal fail; counted; production goes on | P7's piece | partly: asked for again (P5 to P7); set-aside counts and the hourly line are not built |
| 33 | Arrival order decides; two complete records under one identity disagree | F31, NF-22, A-7 | A26 of the first debate: a fixed rule in the home program, tested with all orders | 120 orders of five pieces; +19 against +42 | not built (the receiver changes for it) |
| 34 | The PC's result corrections are skipped; a tablebase probe fails; no game is ever rescored | F32, NF-23 | the home step calls the loop's OWN function; it stops when the tables do not open; zero rescored in 10,000 games is an alarm (about 76 expected, Neon) | tables taken away | built: the round-text test, 10 checks; the alarm is not built |
| 35 | The totals do not add up; kinds of credit are mixed | F34, A-8 | section 2: five counts, reconciled in the last hour | C0 and C2 equal in rows while one empty reservation or one range seal is missing; one real after-game correction; one receipt delivered twice: the missing identity stays visible, C3 counts the correction with its reason, C4 only durable kept rows, the repeat adds zero, and completion FAILS although the row totals agree; one ledger total changed by 1 makes the reconciler end with an error (Astra `130946Z`, Neon `131430Z`) | not built (today's receiver knows "credited" only) |
| 36 | The day ends short; the last range | F35, A-11, NF-29 | D9 | a short declared range and an incomplete one side by side | not built |
| 37 | A search runs after the cutoff; the tail of a slot is not sealed | NF-28, A-11 | D5; each slot's final seal | a long game started just before D | partly: the worker seals its last, partly filled piece at a stop (T1); the cutoff rule is not built |
| 38 | Everything produced is acknowledged and a round is still short | Astra `125204Z` | D13: the terminal inventory | twelve reservations, eleven finished, seven pieces, one missing seal: 4 kept rows short of 9, zero pieces missing | not built |
| 39 | The machine is given back too early; billing goes on after the work has stopped | F36, NF-30, A-13 | D12, D13 | home offline at the release time | not built |
| 40 | Something of ours stays on a machine we no longer hold | F37 | clean-up only after reconciliation, and it says what it removed | a throwaway server root with one file of the run, one of a neighbouring run and one unrelated file; closing tried with a home receipt missing, then after a clean reconciliation; the clean-up run twice: the first try removes nothing; the clean one removes only the recorded run's files, keeps the other two and writes what it removed; an interrupted clean-up finishes on its second run (Astra `130946Z`, Neon `131430Z`) | not built |
| 41 | No session of ours can work | F38 | nothing waits for a session; alarms are files and one plain line | the small day started with no terminal, no input and no display, every launcher session closed; then one worker ended and home unreachable for ten minutes; nobody touches anything until the closing report: replacement, disk guards, catch-up, deadlines, the final ledger and the alarm file all happen (a cold restart of the PC is tested apart, under O3) (Astra `130946Z`, Neon `131430Z`) | by design; to prove in the rehearsal |
| 42 | A session changes a running thing by hand | F39 | during the day a session only reads; a change is a new version with three YES at a piece boundary | one checked helper changed between two stages in the rehearsal copy, the stage before it finished: the next stage refuses before any new work; what exists stays tied to the old version; going back to a valid list has a stated point to resume from (Astra `130946Z`, Neon `131430Z`) | rule |
| 43 | Match pairs are lost or counted twice across a restart | NF-33 | durable pair identities; only if matches run at all | a kill in the middle of a pair | not built |
| 44 | The codec is missing on one side | NF-34 | D1; a round trip at both starts | an unknown codec name in the manifest | partly: the packer reads back every part it writes; no check at the start |
| 45 | A substitute machine is booked, or a lease renewed, by a script | A-13 | never; only the owner | the substitute unreachable; the pilot under the floor; the lease ended with a receipt missing; each with a fake provider that records requests and with no provider login anywhere in the scripts' surroundings: zero create and zero renew requests, the program records the choice the owner made beforehand and the exact incomplete inventory (Astra `130946Z`, Neon `131430Z`) | rule |

## 8. What exists on the PC today, and the scripts for the three YES

**[2.3] Version 2, as it stands at the time in the head line** (`scripts_v2/` is the package to be; `ref/astra`
and `ref/neon` are independent Linux references and fixtures OUTSIDE the package; this morning's `scripts/` is
superseded and launches nothing):

| Piece of version 2 | State | Votes on the exact bytes |
|---|---|---|
| `run/engine_lines.py` (the table of every line the engine may write) | written, tested | three YES (`a82eb9c8...`) |
| `run/uciproc.py` (the engine process wrapper) | written; 61 checks, the version before fails 5 of them | three YES (`7de2728a...`) |
| `tests/test_uciproc.py` | 61 of 61 in 3 of 3 runs on the PC and in Astra's three native runs | **[2.4]** three YES (`690b3243...`; Neon `151130Z`: three native runs 61 of 61, the wrapper before it 56 of 61) |
| `run/record.py` (the record of 0.1, binding 2) and `tests/test_record.py` | written; 29 checks on Astra's 23 vectors; this morning's module fails all 24 module checks; Astra ran 288 native games through it | **[2.4]** three YES on each (`bc71fa89...`, `a8e16021...`; Neon `151130Z`: 29 of 29, and eight changes planted in the module all caught by the test) |
| `run/worker.py` and its test | written by Opus to `FORMATS.md` 2.2 and the 2.3 readings. **[2.4]** Fable read all 1,057 lines (bytes `bad2972b...`): NOT YET. `FORMATS.md` 2.4 changes what it must write (the sixth state, the `RESUME` rule at a second start, the interval), and the read found one fault (a date that does not exist is accepted as a time). No way was found for it to credit a game it should not. Its author changes it now; then Fable reads the changed parts and the test and runs the test | not published yet |
| `run/packer.py` and its test | **[2.4]** written by Opus (his count: one run, 68 of 68, on the voted record module and wrapper and the official converter; his full run both ways is owed); not yet read by Fable | not published yet |
| `tools/budget.py` | written by Opus; the four boundary cases above still to be run against it | not published yet |
| home reader (a1, a2 with the rules replay, b), home guard | NOT WRITTEN in version 2 | - |
| server guard with start at boot, boot guard, finalizer, launcher, fetch with a pinned host key, terminal inventory | NOT WRITTEN in version 2 | - |
| machine check and Linux build for the package | NOT WRITTEN for the package; `ref/neon` holds an independent reference of both (Astra ran its tests natively), not yet read line by line on the PC | - |
| full rehearsal at home (cable pulled, program killed, disk full, PC restarted) | NOT DONE | - |

**What this means, said plainly:** **[2.4]** five files of the package have three YES on their exact bytes (the
table of engine lines, the engine wrapper and its test, the record module and its test). The worker and the packer exist on the PC and are not through their reads. The home side, the guards and
the launcher of version 2 are not written. No machine is rented before all of them exist, have three YES, and
have passed a full rehearsal. The table below is this morning's state (version 1), kept for the record.

| Piece | State on the PC | On this branch for the read |
|---|---|---|
| player (worker, engine driver, record form) | written, tested (95 checks, 6 planted faults caught) | `debate/server_day/scripts/run/` |
| packer and seal | written, tested (with the receiver: 34 checks, 8 planted faults caught); its removal mode comes out (D2) | `scripts/run/packer.py` |
| home receiver; home step to round text | written, tested; NOT yet changed to A26, to the five counts and to three stages | `scripts/home/` (read now, will change) |
| budget tool; three-YES ledger tool; home guard | written and tested by Opus before this debate; the budget tool is rewritten after D3 to D5 settle (section 5) | after my read |
| Linux build script; machine check | the build script RAN ONCE, on Astra's Linux host (one compiler, one variant): it reproduces the PC's profile run and start-up search to the node (`130703Z`); it has no plain comparator build yet (D10). The machine check reads the first processor's flags only: to rewrite for section 4 | `scripts/linux/` |
| server guard with start at boot; lock and chain; hourly line; pause at a disk floor; fetch with pinned host key; terminal inventory; clean-up | NOT BUILT | - |
| full rehearsal at home (cable pulled, program killed, disk full, PC restarted) | NOT DONE | - |

Sixteen places where today's code differs from this plan or fails a case are listed in `scripts/README.md`
(seven found by me, nine by Astra's read; four more on the tools in `APPROVALS.md`). The YES ledger is
`debate/server_day/APPROVALS.md` (one YES so far; no file has three). Every file the day WRITES is specified in
`debate/server_day/FORMATS.md`, for your vote before the PC builds its writers and readers.

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
- **[2.3] M2b** stage a2 as `FORMATS.md` 2.3 defines it (decode, the seal's fields recomputed, the record parse
  with binding 2, the rules replay), rows a second on the PC with the version 2 reader: NOT MEASURED (that
  reader is not written; M2 below is this morning's reader).

### Measured on the PC, 12:10 to 12:17 PC clock (M2, M3, M5, M6, M7)

Opus's rehearsal: one worker, 2,000 games, the frozen manifest, this morning's scripts, one thread a step. The PC
was full meanwhile (the loop's training, its early self-play, the tune's matches; 88 to 89 C). Recounted by Fable
from his raw files: every number below holds. They describe the PC and this morning's code, not the server.

- **M2:** reading and replay 116,703 raw rows a CPU second. 1,984 games credited, 16 without rows, 0 refused.
- **M3:** rescoring with the tables 122,881 raw rows a CPU second; the loop's own filter on rounds 141 to 144:
  166,000 to 170,000 records a second. The three home steps in a row: 42,332 raw rows a CPU second on ONE
  thread, so the needed 26,456 kept rows a second (27,913 raw at this run's kept share) take 0.66 of one thread.
- **A blocker found by it (Opus, measured):** this morning's home programs load the whole identity ledger at
  every pass: 1,018 bytes of memory a credited game, 15.5 GiB and 55 s a pass at the day's 16.4 million games.
  Version 2 has no such ledger (`FORMATS.md` section 2).
- **M5:** kept 94.78 % of raw (round 142: 95.32 %). Packed positions 2.012 + game records 2.318 = 4.330 bytes a
  raw row = 4.568 a KEPT row: **9.14 GB for 2 billion kept** (the 30-game sample said 9.7). All 4 pieces
  travelled packed; none fell back to plain text (which would be 14.53 bytes a raw row, 3.4 times as much). The
  plain records on the server: 75.1 bytes a raw row, about 158 GB for 2 billion kept (D2: both forms count).
  Bytes really sent with retries: not measurable on the PC.
- **M6:** a home program killed hard is back in 0.137 s (median of 5) WHEN something starts it. Nothing does
  today, and nothing of ours starts after a restart of the PC (question O3).
- **M7 (Windows; the Linux half is running):** on the game records `lzma` 6 gives 2.318 bytes a raw row, `zlib` 6
  gives 2.825 (1.22 times as much); `lzma` takes 3.8 times as long and still handles 540,000 raw rows a second
  on one thread: about 5 % of ONE server thread at the needed rate. D1's choice costs nothing that matters when
  it runs in the packer process only.
- One worker on one loaded PC thread: 707 raw rows a second (it says nothing about the server: M4).
