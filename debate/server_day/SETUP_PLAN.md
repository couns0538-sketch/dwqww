# SETUP_PLAN.md: the plan for the server day

Editor: Fable. Version 1, written at 2026-11-23T19:53:39Z (Fable's clock) from the three independent failure lists
(`FAILURES_fable.md` F1 to F40, `FAILURES_astra.md` rows A-1 to A-13 in its order, `FAILURES_neon.md` NF-01 to
NF-35) and the messages up to Astra `124850Z`.

**How this file changes.** Astra and Neon propose in messages; I write the text in; a part gets the mark
SETTLED only by ONE joint message of both plus my check on the PC. Marks: **SETTLED**, **PROPOSED** (written in,
not yet voted), **OPEN** (no text yet), **OWNER** (only the owner can decide; collected in section 9),
**NOT MEASURED** (a number that nobody has measured yet). Nothing in this file is a claim that code does
something today; section 8 says what exists.

## 1. The frame (the owner's direction; binding, not voted)

- Goal: **2,000,000,000 kept positions** for training, made on one rented machine in one day, checked at home.
- 23 hours produce; the last hour only checks. What fits into the 23 hours is calculated from MEASURED rates.
- Everything is moved compressed; everything that arrives is compressed and transferred automatically.
- Scripts run all of it, also while no session of ours can work. As little as possible is lost when something
  breaks. Filtering and checking run from the beginning.
- Every script is read line by line by Astra, Neon and Fable; three YES for the exact bytes, or it does not run.
- The plan must hold for another machine too (start minimums, section 4).
- Nothing is installed on the home PC. Nothing of ours reaches INTO the PC: the PC fetches. No secret of ours is
  ever on the server.

## 2. The path of the data and the five counts (PROPOSED; from Astra's row A-8, NF-08, F9, F34)

```
server:  worker plays whole games -> packer seals a PIECE (packed rows + compressed game records + seal)
         -> the piece stays in the server's spool for the whole lease (nothing is deleted there)
home:    fetch -> (1) CUSTODY: size, sha256 and chain of fingerprints hold; a durable receipt is written
         -> (2) CONTENT: every game replayed, all five fields and the opening binding hold
         -> (3) CORRECTED: the PC's own after-game rescoring (lone king, tablebase), with its reason kept
         -> (4) KEPT: the PC's filter; the kept rows of one ROUND packed again, durably, with their count
         -> round text exists only for one training window at a time
```

| Count | What it counts | What it is good for |
|---|---|---|
| C0 sealed | raw rows in sealed pieces on the server | the server's own rate; never credit |
| C1 custody | raw rows in pieces that are at home with a durable receipt | "the bytes are safe at home" |
| C2 content | raw rows of games that passed the replay at home | "the games are right"; the gate for giving the machine back |
| C3 corrected | games rescored by the PC's after-game step, by reason | the label is the PC's label |
| C4 kept | rows in durable packed round output after the filter | **the only count that is credit toward 2 billion** |

Every progress line and every decision names which count it uses. The pilot's rate is C4 of games the pilot
itself started, over the pilot's own wall time (section 5).

## 3. Decisions

| # | Decision | Mark | From |
|---|---|---|---|
| D1 | **Compression uses only what Python brings on both sides** (no tool installed anywhere). The PC's packer as built uses `lzma` preset 6 for the game records and for the raw fallback, each with a read-back check; rows are packed in its own form. `zstd` is not assumed (absent on a stock Ubuntu 24.04, Neon). Whether `lzma` or `zlib` is used for which part is decided by ONE measurement of the real packer at the full rate (M7). | PROPOSED | NF-34, Neon `124630Z` proofs 1 and 2, F3 |
| D2 | **The server keeps every sealed piece for the whole lease**, fetched or not, acknowledged or not. A server volume that cannot hold the measured full-day upper estimate plus staging plus reserve fails the first hour. If the estimate grows beyond the room during the day, production pauses and the sealed pieces stay. No pruning rule exists. | PROPOSED (Astra `124850Z` withdrew pruning; NF-19's "emergency pruning" is dropped unless Neon objects) | F14, A-6, NF-19, NF-26 |
| D3 | **The pilot counts only the games it started**, as C4 at home, with run, round, slot and game identity kept across both ends of its window; carried-in work is counted apart; a repeated receipt adds zero. | PROPOSED | Astra `124732Z`, NF-08, F9 |
| D4 | **The pilot's decision table has no gap** (r = measured C4 rate, n = needed rate): r >= 1.10 n: self-play, and matches from a predeclared queue may use the measured surplus; n <= r < 1.10 n: self-play only, the margin reported; floor <= r < n: the owner's predeclared alternative (section 9, O1), no improvising; r < floor: stop in the first hour so the machine can be given back. The numbers 1.10 and the floor (proposed 0.50 n) are policy, not measurements. | PROPOSED; the alternative and the floor are OWNER | Astra `124728Z`, Neon Q2, F10 |
| D5 | **Time.** The lease's real start and absolute end (UTC) as the provider shows them, plus the host's boot identity, are recorded at the start. Durations inside one boot use a steady clock. New games stop at the EARLIER of hour 23 and (lease end minus the measured closing reserve, at least one hour). A restart late in the lease gets only what is left; a clock jump buys nothing. | PROPOSED | A-1, NF-03, F21 |
| D6 | **Three YES.** A ledger line is `YES <sha256> <seat>`; three distinct seats (astra, neon, fable) for every file that runs or is read by something that runs (scripts, helpers, config, net, book, fixtures). The manifest's own hash is pinned OUTSIDE the package it describes (on this branch and in the PC's ledger). The start, every stage, the restart path and the close path check it. A file Fable wrote is also read by Opus on the PC. | PROPOSED | F1 to F4, A-3, NF-02, NF-35, Neon Q4 |
| D7 | **The home side after a restart of the PC is NOT unattended today.** What exists: a guard program that keeps the home steps running and restarts them, started by a double click. After a reset or a restart by Windows somebody must double-click again; until then nothing is fetched. The server's full-day spool (D2) keeps the bytes while the lease lives; it cannot deliver after the lease has ended. A start at logon would be a change to Windows and is the owner's alone (O3). The word "unattended" is used for the home side only with this sentence beside it. | PROPOSED (the fact is the PC's; the wording answers Astra `124850Z`) | F25, NF-24, A-12 |
| D8 | **Home is two independent queues**: (a) fetch + custody + content check, light and never waiting for (b); (b) rescoring + filter + packing of kept rows, one round at a time. Data stays packed at home; round text exists for one training window at a time; before every write the free room of the PHYSICAL volume is compared with the owner's floor for it plus a margin, with everything that will lie there at the same time added up. | PROPOSED | NF-21, NF-25, A-9, F26, F29 |
| D9 | **A round is a predeclared range of game identities**, not a number of rows. Its kept output may vary. The policy for a deliberately shorter last range is chosen at the pilot; a range that is not sealed by the server and verified in full at home is never counted or rounded up; an earlier missing game is never relabelled as "the short last range". | PROPOSED | A-11, NF-29, F35, Astra `124728Z` |
| D10 | **Build.** Variants are built from the frozen source with the PC's real flags (the PC's build script is the reference, not the CMake file: the flags for the mate guard and for the king-bucket net must be given explicitly). Each variant twice; reference numbers, perft counts, the fixed games against the PC's known answers; only instruction sets the processor has; each binary's rate measured with self-play at the full worker count, never with bench. A profiled binary is used only if it measured faster than the plain one; a missing or stale profile fails the build (compiler flags that make it an error); the profile run fails on ANY engine error line and without the net's start line. The log names the binary that is started, by sha256. | PROPOSED; the PC checks its own profile driver for the weakness Neon found (M8) | F6, NF-04, NF-05, A-4, Neon proof 3 |
| D11 | **Matches on the day:** none, unless the pilot shows surplus by D4 or 2 billion are already C4 at home. If matches run beside self-play, the mixed rate is measured, not assumed; a falling rate takes the threads back at a pair boundary. | PROPOSED | Neon Q1, NF-10, NF-33, A-10 |
| D12 | **The end has four independent states**: every receipt reconciled; data still missing, with identities and bytes; clean-up of the server verified; the provider's release confirmed. A missing receipt neither triggers a clean-up of the only copy nor renews a paid lease. Billing ends only by the owner's act; "processes stopped" is not "billing stopped". | PROPOSED | A-13, NF-30, F36, F37, Astra `124850Z` |
| D13 | **When the machine may be given back.** The gate is C2 for everything sealed (the games are at home and right). C3 and C4 need no server; if the home filter is slower than production (M3), C4 finishes at home after the lease and the report says so. The forecast "2 billion kept" before the release uses C2 times the measured kept share with its lower bound. | PROPOSED, new: please attack it | F29, NF-25, A-8 |

## 4. Start minimums (so that another machine can be used) — OPEN, numbers NOT MEASURED

A machine is accepted in the first hour only if every line holds. Each number is filled from a measurement
with its raw file before the rental; a blank number means "no rental yet".

| Minimum | Value | Source |
|---|---|---|
| usable threads (after affinity, quota, control groups) | NOT MEASURED | pilot rate needed / rate a thread |
| C4 rate of the 20-minute pilot | >= n of section 5 (table D4) | pilot |
| instruction sets | at least what one approved binary needs | D10 |
| free memory | workers x measured memory a worker + reserve | NOT MEASURED (M4) |
| free room on the data volume | full-day spool upper estimate + staging + reserve (D2) | NOT MEASURED (M5); about 9.7 GB packed payload by today's small sample |
| open files, processes | enough for the full worker count, shown by the pilot at full count | pilot |
| compiler and library | one that reproduces the PC's fixed games node for node | D10 |
| Python with `lzma`, `zlib`, `hashlib`; `ssh` server | present | machine check |
| time to the lease end | >= first hour + production + closing reserve | D5 |

## 5. Rates and sizes (each with its source)

- Needed C4 rate n: 2,000,000,000 / (23 x 3600) = **24,155 a second** (rounded up) if all 23 hours produce.
  With the first two hours gone and one hour reserved: 2,000,000,000 / (21 x 3600) = **26,456 a second**.
  With 36,000,000 pilot rows already credited: 1,964,000,000 / 75,600 = **25,979 a second**. Recomputed by me
  by hand; the PC's budget tool must print the same three and Astra's carry-in case (3,000,000 own rows in
  1,200 s = 2,500 a second, not 25,000) before it is used. PC check of the tool: owed (section 8).
- Round 142 on the PC: 15,258,168 kept of 16,007,134 raw rows (Astra's figures from the PC's table; kept share
  0.9532).
- **Packed size: answer to Astra `124732Z`.** The 1.99 (packed rows) + 2.64 (compressed game records) bytes are
  per RAW row: the packer packs every row the engine wrote; the filter runs at home. The sample is small (30
  games, 3,930 rows). So the first reading holds: about **9.7 GB** of useful payload for 2 billion kept at
  round 142's kept share. One rehearsal records raw rows, kept rows, packed row bytes, packed game-record bytes
  and bytes really sent with retries (M5); until then the figure carries the words "small sample".
- The PC's own self-play rate a worker, kept share and positions a game (M1): measured by Opus on the PC this
  morning; my recount from his raw files is owed and comes as a message before any number of it is written here.
- NOT MEASURED: the server's rate a thread (M4), the PC's content-check rate (M2), the PC's rescoring + filter
  rate beside what else the PC does that day (M3), codec speed of the real packer (M7), recovery times at home
  (M6).

## 6. The day

### 6.1 The first hour (deadline: section 9, O2)
1. Machine check against section 4. Fail: stop, one line says which minimum.
2. Package unpacked; manifest and three-YES ledger checked against the pinned hash (D6). Fail: stop.
3. Builds (D10). Fail of every variant: stop.
4. Fixed games through the REAL path: worker -> packer -> fetch -> home check, all five fields and the end
   lines equal to the PC's known answers; one fixed game's sha256 under the written byte rule equal on both
   sides. Fail: stop.
5. Pilot, 20 minutes at the full worker count, counted by D3; the per-minute rate must not fall by more than a
   written share between its first and last five minutes (heat, neighbours). Then table D4.
6. The budget table is written from the pilot (what fits, which row of D4 holds, when new games stop by D5).

### 6.2 The 23 hours
- Server: guard keeps workers, packer and spool alive (F11, F13 to F20, NF-11, NF-16, NF-26, NF-27, A-5, A-12);
  one stop file; nothing is a child of a login.
- Home: queue (a) fetches and checks; queue (b) rescoring, filter, packing (D8). One progress line an hour,
  written at home also when the server is silent, with C0 to C4, the trailing hour's rate AND the cumulative
  rate, the needed rate, backlog per stage with the oldest unacknowledged piece, quarantines, failed tablebase
  probes, free room above the floors on both machines (F18, NF-32, A-9).
- Any conflict of two complete records under one identity, any content failure, any failed tablebase probe:
  that piece or range is set aside whole, counted, never credited; production goes on (F12, F30, NF-20, NF-22,
  NF-23, A-7).

### 6.3 The last hour
- No new game. Each worker finishes its game, the last pieces are sealed, each slot writes its final seal.
- Home drains, then writes the closing report in three classes: verified complete rounds; games with zero
  rows; incomplete ranges with the exact missing identities (never credit) (A-11, NF-28, F34).
- The four states of D12, one after the other. The line "the machine can be given back" only by D13.

## 7. The merged failure table — OPEN (next version)

The three lists overlap in most rows. Version 2 of this file carries ONE table: each row with its identities in
the three lists, the script that owns it, the planted test that must fail without the safeguard, and its mark.
Rows that only one list has (so nobody loses them in the merge):
- only Astra: lease start and absolute expiry with boot identity (A-1); two paths on one physical volume (A-2);
  the manifest's root pinned outside the package (A-3); a slot's lease moved to another executor and the old
  one waking late (A-5); the pilot inflated by carried-in rows and 200 repeated receipts (A-10); no replay
  allowed in the checking hour, an old gap never called "the short last range" (A-11); a living process
  with no verified progress (A-12); never book a substitute machine by script (A-13).
- only Neon: control-group limits below the thread count, an unmounted data disk (NF-01); slow or missing
  instruction variants (NF-04); the profile traps and the missing profile tool (NF-05); a folder given as the
  net file (NF-06); the engine's error pipe filling and blocking (NF-11); the rolling share of equal games,
  alert above 5 % where about 1.9 % is healthy (NF-14); Windows sleep and a file held by the virus scanner at
  the moment of a rename (NF-24); core dumps and logs filling the disk (NF-26); the memory killer and stepping
  workers down while slot identities stay (NF-27); a prompt that hangs the fetch (NF-31); match pairs across
  a restart (NF-33); the package built from a changed source tree (NF-35).
- only Fable: a number taken from memory instead of a measured file (F4, F40); the first hour's deadline (F10);
  the guard started by the system at boot on the SERVER (F15); a session "helping" by hand during the day (F39);
  what stays on a machine we no longer hold (F37).

## 8. What exists on the PC today, and the scripts for the three YES

| Piece | State on the PC | On this branch for the read |
|---|---|---|
| player (worker, engine driver, record form) | written, tested (95 checks, planted faults) | next push |
| packer and seal | written, tested (with the receiver: 34 checks) | next push |
| home receiver; home step to round text (calls the loop's own after-game function) | written, tested; NOT yet changed to A26 | after the change |
| budget tool; three-YES ledger tool; home guard | written and tested by Opus; my read on the PC is under way | after my read |
| Linux build script; machine check | written, NEVER RUN | with the words "never run" |
| server guard with start at boot; hourly line; pause at a disk floor; fetch with pinned host key; clean-up | NOT BUILT | - |
| full rehearsal at home (cable pulled, program killed, disk full, PC restarted) | NOT DONE | - |

The YES ledger of this debate: `debate/server_day/APPROVALS.md` (does not exist yet; no script is approved).

## 9. For the owner (collected; I ask him once, before any rental) — OWNER

- O1. If the pilot's rate is below what 2 billion need (D4, third row): take the lower total that fits, or stop
  and give the machine back, or something else he names. Never a second rental by script.
- O2. The first hour's deadline: start with the last binary that passed, or call the day off.
- O3. The home PC after a restart: is a start-at-logon entry, made by himself, wanted, or does the double click
  stay (D7)?
- O4. Does the PC's own loop pause its self-play on that day, so that the PC's processor is free for checking
  and filtering (M2, M3 decide whether this is needed)?
- O5. The provider's expiry and billing: how the lease ends, and that giving it back is his act (D12).

## 10. Measurements owed (each gets its raw file and a line here)

- M1 the PC's rates (Opus's files; my recount). M2 home content-check rate. M3 home rescoring + filter rate.
- M4 the server's rate and memory a worker (only on a machine of that kind: at the pilot, or a short paid trial).
- M5 bytes a row at scale and bytes sent with retries. M6 recovery times at home (program killed; PC restarted).
- M7 the real packer's speed with `lzma` against `zlib` at the full rate. M8 the PC's own profile driver: does it
  end with an error on an engine error line (Neon proof 3)?
