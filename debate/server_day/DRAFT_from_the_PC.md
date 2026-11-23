# THE SERVER DAY: THE FIRST DRAFT FROM THE PC, for Astra, Neon and Fable to take apart

What this file is: the first draft of the plan for the server day, written on the PC by its second session (Opus)
on the owner's order of 23 November; read by Fable before it came here (sha256 of the lab's file begins
`08250dbb7e34c87a`). NOTHING IN IT IS DECIDED. It is the starting text for the session the owner will start: the
three of us debate it until no mistake is left, the agreed plan becomes `debate/server_day/SETUP_PLAN.md`, and
after that every script of the day is checked by each of us and needs the yes of each. Where this draft and W5 of
`debate/FINAL_PLAN.md` differ, W5 with its addendum holds.

FABLE'S NOTES, read them before the draft (each is a correction or a point that the draft leaves open):
- F-1. THE SIZE. The draft says 2.01 bytes a row and about 4 GB for the day. Measured on the PC with the package's
  own packer: 1.99 bytes a row for the packed rows PLUS 2.64 for the compressed game records (opening, position
  line as sent, end line, binding), together about 4.6 bytes a row: 2 billion rows are about 9.2 GB. The plan's
  "about 4 GB" counted the rows alone.
- F-2. WHEN A ROUND CLOSES (the draft's Q3). Not by a row count. A26 and its safeguards (Astra `112803Z` to
  `114050Z`, Fable `183232Z`, `183951Z`): a round is a fixed range of game numbers of every logical slot, written
  down before play; its text is in the order (slot, game number, row); a range is released only on the source's
  own seal with every predecessor piece verified at home.
- F-3. THE FALLBACK in section 2 says "the games cut at 1000 plies". W5 (h) means something else: games ENDED at a
  SCORE of 1000 instead of 2000, and only if W10's net passed its bar. Not a ply count.
- F-4. WHO APPROVES (section 4). The draft says that whoever writes a file does not approve it. The owner's
  condition is the yes of Astra, Neon AND Fable for every script. For a file Fable wrote, the PC's second session
  reads it line by line as well; the three yes stay required. The debate settles the exact rule; the ledger that
  the start scripts enforce (a changed file loses its approvals) is the part to keep.
- F-5. THE WAY HOME. The PC cannot be reached from outside and nothing may be installed on it: the PC fetches
  (Fable `183849Z`, point 5), with the programs it already has.
- F-6. THE RATES quoted from the PC's loop are a forecast only. W5 (a): a timing from one machine is never quoted
  for another. The pilot on the rented machine decides, and the day's numbers are the ones of 23 hours of
  production: 24,155 verified kept rows a second, 26,456 with two hours of set-up inside the 23.
- F-7. ANOTHER MACHINE. The machine named may not be free on the day; then the owner takes another one or the day
  waits. Every line of the draft that leans on 64 cores or 2.3 GHz needs its general form.

------------------------------------------------------------------------------------------------------------------

# The server day: FIRST DRAFT for the debate (Opus, 23 November 2026, 10:40 PC clock)

The owner's order of 23 November: the PC's second session writes the first draft of the server-day plan; then
Fable, Astra and Neon debate it until no mistake is left, and every script is checked by each of the three and
needs the yes of each. This is that start. NOTHING HERE IS DECIDED. The frame is W5 of
`FINAL_PLAN_2311.md`, and Fable's working plan is `teamwork/W5_PLAN_by_fable.md` (package `serverday/`). Where this
draft and W5 differ, W5 holds until the debate changes it. No provider name and no price stand here: the file may go
onto a public branch as it is.

## 1. The owner's six requirements, and where each is met

| # | The owner (10:28) | Already in W5 | What this draft adds |
|---|---|---|---|
| R1 | "every file needs to be compressed so the transfer is fast" | (d) the packed record, measured 2.01 bytes a row: the whole day is about 4 GB; (e) closed, checksummed pieces | the OUTBOUND package too: one archive (source, net, book, scripts, known answers) with a sha256 list, checked on arrival before anything runs |
| R2 | scripts run everything automatically and go on when our usage runs out | (c) one start command, restarts, a full disk, a stalled worker, a stop at the set time | the HOME side is autonomous as well: the receiver runs as a detached process under a watchdog (like the loop's), with double-click start and stop files for the owner; it never lives inside a Claude session |
| R3 | the budget calculated exactly from MEASURED self-play and SPRT games an hour, for 23 hours | (g) the pilot rule, 23,149 kept rows a second for 2 billion in 24 hours; (c) the rate recomputed from the time really left | section 2: both rates measured in a pilot hour on the rented machine; one script turns them into the day's schedule; the forecast before the day comes from the PC's rates |
| R4 | the last hour for making sure everything is right | A11: the end of the lease, sealing, receipts, the missing count, the provider's release shown | hour 24 is reserved: no new game starts after 23:00 of the lease |
| R5 | filtered from the beginning, automatically | (e) the PC checks and filters at home; the filter only marks | the receiver runs the loop's OWN filter on each complete round of credited rows as it arrives, so the data is ready to train when the day ends |
| R6 | zero mistakes: every script is checked by Astra, Neon and Fable, and each must agree | the debate; tests with plants in every piece | section 4: an approval ledger that the start scripts enforce |

## 2. The budget (R3)

- **What is measured where.**
  - M1, on the PC before the day: kept rows a second for each self-play worker, at 2,000 soft nodes, with the
    frozen program, net and options. Also games an hour for one match slot at the node counts a match on the day
    would use. Purpose: the forecast, and a sanity check of the pilot.
  - M2, on the server in the pilot, right after the set-up checks: 20 minutes of self-play at full width, counted as
    VERIFIED KEPT rows at home (W5 g), plus a 200-game match at the day's settings.
- **The schedule script** (`budget.py`, to be written with hand-worked known answers):
  - rows a second still needed = (target - rows verified at home) / (end of production - now) (W5 c);
  - match games that fit = games an hour from M2 x hours given to matches.
  - It prints the schedule before production starts and again every hour, and it starts the declared fallback when
    the need exceeds the rate.
- **The forecast.** Rough: the loop's log prints cumulative rates, not clean ones. M1 replaces it.
  - The PC's loop: about 5,400 to 5,900 positions a second on 16 threads (17 and 23 November). Round 142 kept
    95.3 % (15,258,168 of 16,007,134) in 124,927 games, so about 128 records a game. That makes about 320 to 350
    kept rows a second per PC thread.
  - 2 billion kept rows in 23 hours of production need 24,155 a second, which is 189 per thread on 128 threads. So
    the rented machine must reach at least about 0.56 of the PC's per-thread rate (0.54 to 0.59 across the range
    above).
  - The machine is 64 cores at 2.3 GHz base. A server core is slower than a desktop core, so this is NOT safe on
    paper. M2 decides, and the fallback must be written before the day: a lower target, a second day, or the
    games cut at 1000 plies if W10 passed.
- **Matches.** On the PC a 400-game chunk at 250,000 nodes, 8 at once, took 12.2 to 20.8 minutes (TD twin chunks
  c05 and c06, 23 November): 1,150 to 1,970 games an hour, or 145 to 245 games an hour for each game in play. With
  about 120 games at once and the same per-thread ratio (0.5 to 0.8), a 2,000-game match at 250,000 nodes would
  take about 5 to 15 minutes. M2 measures it.

## 3. The day, hour by hour (a 24-hour lease)

| Lease time | What runs | Ends when |
|---|---|---|
| 0:00 to about 0:45 | arrival check: package hashes, the approval ledger (section 4), W5 (a) the build of three variants with the processor check, (b) the start-up search, (i) the N12 games equal to the PC's | every check passes; otherwise STOP and report (nothing paid for is wasted on a wrong program) |
| about 0:45 to 1:15 | the pilot M2 | the schedule is printed and logged |
| 1:15 to 23:00 | production under the supervisor: self-play, and any declared match share (section 5, Q1); pieces sent as they close; at home, credit, the filter round by round, and the hourly schedule | 23:00, or the target is reached |
| 23:00 to 24:00 | closing (A11): seal, last transfer, receipts against expected game ids, the missing count, the release shown | the release is shown |

The sessions only watch. Everything above runs from the two start commands (server and home).

## 4. Zero mistakes: the approval ledger (R6)

- `serverday/MANIFEST.sha256` lists every file that runs on the day, on the server and at home.
- `serverday/APPROVALS.txt` has one line per review: `<sha256> <path> <reviewer> <date> YES|NO <one-line note>`. The
  reviewers are fable, astra and neon; whoever writes a file does not approve it.
- `start.sh` (server) and the receiver (home) REFUSE to start when any listed file's current sha256 lacks three YES
  lines. A test plants one edited file that still carries its old approvals: it must be refused. A second plant is a
  file that is missing from the manifest.
- In the debate each file is read line by line. Where possible each reviewer runs its test on their own machine:
  Astra and Neon on Linux, Fable in the PC's Linux subsystem.

## 5. Open questions for the debate

- **Q1, matches on the day.** The owner asked for the SPRT rate too. Proposal: self-play first ("FIRST 2 billion
  positions", the owner's order of 23 November). Matches run only in time the pilot shows to be spare, from a queue
  and order declared before the day (for example W1's five matches, then the bundles of the plan's SPRT [0, 5]
  rule). Which matches, and at what share?
- **Q2, the fallback** if M2 gives less than 0.56 of the PC's per-thread rate.
- **Q3, the filter at home** as rows arrive (R5): is a round of 16 million kept rows the unit, as in the loop?
- **Q4, the installation** if the provider does not install Ubuntu: Fable writes the owner's guide later (his order).
- **Q5, both start commands survive** the end of every session (R2). The home side is tested with the session
  closed on purpose, as W5 (c) already does for the server.

## 6. What I (Opus) offer to build, if Fable (owner of W5) agrees

- M1: the PC's clean rates, in a loop pause or a quiet window, declared before it runs.
- `budget.py` and its test (hand-worked cases: the target met, the target missed, the fallback started).
- The approval-ledger check and its two plants (section 4).
- The home watchdog for the receiver, with the owner's double-click files.

Everything else is W5 as Fable is building it.
