# FAILURES_fable.md: what can go wrong on the server day, how it is noticed, what the script does

Fable's own list, written before reading Astra's and Neon's. Each line is a REQUIREMENT that a script of the
day is read against; it is not a claim that the code does it today. The state of the PC's code is at the end.
Words: "server" = the rented machine; "home" = the PC; "piece" = one sealed, packed file of whole games;
"guard" = the plain program on each side that keeps the work running with nobody there.

## A. Before the day: the package and the three YES

1. **A file on the server is not the file that got three YES** (edited after the vote, an older copy, line ends
   changed on the way). NOTICED: the approvals tool hashes every file of the package at the start and again
   before every stage and compares with the ledger. SCRIPT: refuses to start, names the file. Nothing runs
   "just this once".
2. **The package is incomplete or the net file is another one.** NOTICED: manifest with size and sha256 of every
   file; the engine's own start line must show the net's stored checksum (N17), and one position a queen up must
   be far from zero. SCRIPT: stop before the first game.
3. **Line ends or permissions change in the transfer.** NOTICED: by 1. SCRIPT: the package is ONE compressed
   archive, unpacked by one command; no checkout, no editor on the server.
4. **A script takes a path, a count or a rate from memory instead of from the measured file.** NOTICED: the
   budget table names the raw file of every number. SCRIPT: a missing or stale input file stops the start.

## B. The first hour on the machine

5. **The machine is not what was ordered** (fewer threads, less memory, a slower or throttled processor, no
   fast vector instructions, a small or slow disk). NOTICED: the machine check prints threads, memory, disk
   room, instruction sets, and the trial's measured rate; each is compared with a written minimum. SCRIPT:
   below a minimum it stops and prints the budget table's fallback row, or "do not start: call the owner".
6. **The build is not the PC's engine** (another compiler or library version: equal moves are ordered by the
   C++ library, so node counts can differ; a profile step that makes it SLOWER; a miscompile). NOTICED: the
   reference numbers with the built-in net, the fixed test games move for move and node for node against the
   PC's known answers, two builds of each variant, each binary's speed measured. SCRIPT: only a binary that
   passed all of it is started, the log names which one; no profiled binary is taken unmeasured.
7. **An option is refused and the engine plays on with its default** (one info line). NOTICED: the player reads
   every answer line up to `readyok` and looks every option up in the exe's own list. SCRIPT: stops the worker
   before its first game.
8. **Limits of the system are too low for 128 workers** (open files, processes, shared memory). NOTICED:
   the machine check reads them; the trial runs the FULL worker count. SCRIPT: stop in the first hour, not at
   hour 3.
9. **The trial counts the wrong thing.** A rate of "positions written on the server" says nothing about what
   arrives and passes at home. NOTICED and SCRIPT: the 20-minute trial is counted as positions ARRIVED at home
   and CHECKED there, and the budget is computed from that number.
10. **The first hour runs over.** SCRIPT: a written deadline. At that minute production starts with the last
    binary that passed, or the day is called off; which of the two is decided before the day, by the owner.

## C. The 23 hours on the server

11. **A worker's engine dies or hangs.** NOTICED: a time limit on every engine answer; a heartbeat per worker
    (games finished, last time). SCRIPT: the guard ends that worker, throws its unfinished game away WHOLE,
    starts the worker again on the same slot. A half game is never written.
12. **The same game twice** (a restart replays a slot; two executors finish one slot; two workers draw the same
    numbers). NOTICED: game identity comes from (range, slot, counter), never from the clock; home refuses a
    second complete record under one identity unless it is byte-equal, and reports a conflicting one (A26); the
    share of games with an equal move list is measured in the trial and every hour. SCRIPT: byte-equal repeat
    is dropped and counted; a conflict stops that range and raises the alarm.
13. **A piece is cut while it is written** (kill, power, full disk). NOTICED: a piece exists only after write,
    flush to disk, checksum and an atomic rename; each piece carries the fingerprint of the one before it.
    SCRIPT: on a restart the unsealed tail is thrown away and its games are played again.
14. **The server's disk fills** (the line is down for hours and nothing is fetched). NOTICED: free room read by
    the guard. SCRIPT: production PAUSES at a written floor and resumes by itself; **no sealed piece is ever
    deleted on the server during the day**, fetched or not.
15. **The machine restarts** (a fault, the provider's maintenance). NOTICED: nothing notices by itself. SCRIPT:
    the guard is started by the system at boot (one unit, in the package, three YES) and resumes from the last
    sealed piece. A production that needs a logged-in person to start it again loses the night.
16. **The login that started the work ends, and the work ends with it.** SCRIPT: nothing of the day is a child
    of a login session.
17. **Memory grows over 23 hours** or the system kills a process for memory. NOTICED: the guard reads memory
    per worker and in all; the trial is long enough to show a slope. SCRIPT: a worker over its limit is
    restarted at a game boundary; a killed one is handled as in 11.
18. **The rate falls during the day** (heat, a neighbour on the same host, a runaway process). NOTICED: one
    progress line an hour with games, positions sealed, positions arrived, positions checked, and the rate
    against the trial's. SCRIPT: recomputes "what fits in the hours left" and writes which fallback row holds;
    it never shortens a check to catch up.
19. **Two guards run at once** (started twice by hand or by a restart). NOTICED: a lock that names a living
    process. SCRIPT: the second one ends at once and says why.
20. **Somebody must stop it.** SCRIPT: ONE stop file ends production at game boundaries and seals what is
    complete; the same file is read by every loop and every wait.
21. **The clock of the server is wrong or jumps.** SCRIPT: no decision of the day depends on the wall clock
    except the final deadline; durations use a steady clock.
22. **Opening lines repeat or run out.** NOTICED: the opening of a game follows from its identity; every
    position is tied to the opening that was really sent (A23). SCRIPT: a game whose first positions do not
    replay from its opening fails the home check.

## D. The way home (the PC fetches; the server can reach nothing at home)

23. **The line is down for minutes or hours.** SCRIPT: the fetch tries again with growing waits and no limit of
    tries; the server keeps everything (14); nothing is lost, only late.
24. **A piece arrives damaged or half.** NOTICED: size and sha256 after the download, and the chain of
    fingerprints. SCRIPT: a download goes to a part file, is checked, and only then gets its name; a bad one is
    fetched again; a piece that is bad on the server too is reported with its range and that range is replayed.
25. **The PC is down** (a reset, a restart by Windows, the home guard killed). NOTICED on the server: nothing has
    to be noticed, because the server needs no answer from home. SCRIPT: after the PC is back the home guard is
    started (by the owner's double-click file; nothing is installed into Windows for it) and fetches from the
    last piece it verified. The room on the server must hold the WHOLE day packed, so the longest outage of the
    PC costs nothing but time.
26. **The PC's disk runs short.** NOTICED: free room against the owner's floors before every fetch. SCRIPT:
    data stays packed at home; round text is written for one training window at a time; below a floor the
    fetch waits and the alarm line says so.
27. **The server is not the server** (a changed host key, a wrong address). NOTICED: the host key is pinned at
    the first connect against what the provider shows. SCRIPT: a changed key stops the fetch; it never asks
    "continue?" and never answers yes.
28. **A secret leaks.** SCRIPT: the secret half of the key never leaves the PC; no key, token or password of
    ours is ever put on the server, on this branch or into a chat.

## E. Checking at home

29. **Checking is slower than producing**, and the last hour is too short for what is left. NOTICED: the trial
    measures the PC's checking rate beside what the PC does that day; the hourly line shows arrived minus
    checked. SCRIPT: the budget table has the checking rate as an input; if the backlog cannot be cleared in
    the last hour the table says so in the FIRST hour, and the day's size is cut then, not at the end.
30. **A game fails its check in hour 9.** SCRIPT: its piece is set aside whole with the reason, the count goes
    into the hourly line, the range is asked from the server again; production goes on. Nothing unchecked ever
    becomes round text.
31. **The same position arrives twice with two scores.** SCRIPT: the order of arrival never decides (A26): the
    rule is fixed in the text of the home program and tested with a constructed case.
32. **The PC's own result corrections are skipped** (a drawn game that ends with a lone king against mating
    material, or as a tablebase win, is rescored by the loop after every game). SCRIPT: the home step that
    writes round text calls the loop's own function for it; a test compares with the loop's output on the same
    games.
33. **Home and server disagree about bytes** (what exactly is hashed: which records, which separator, a last
    line break). NOTICED: one fixed game's sha256 is a known answer checked in the first hour on both sides.
34. **The totals do not add up.** NOTICED: three numbers kept apart all day: positions sealed on the server,
    positions arrived and verified at home, positions kept by the filter. SCRIPT: the last hour's check is
    exactly the comparison of these three with the ledger of pieces; any gap is a named range.

## F. The last hour and the end

35. **The day ends short of 2 billion.** SCRIPT: the policy for a shorter last range is chosen at the trial;
    an unverified range is never rounded up or counted.
36. **The machine is given back too early.** SCRIPT: the line "you can give the server back" is written only
    after 34 holds at home for every range; until then the server deletes nothing.
37. **Something of ours stays on a machine we no longer hold.** SCRIPT: the last step removes the package, the
    net and the data from the server and says so; no secret was ever there (28).

## G. Us

38. **No session of ours can work for hours** (a usage limit, a closed window). SCRIPT: nothing of the day waits
    for a session. Alarms are files and one plain line the owner can read by a double click.
39. **A session "helps" by hand in the middle of the day** and changes a running thing. RULE: during the day a
    session only reads. A change is a new version with three YES, started at a piece boundary.
40. **A number in the plan is from memory.** RULE: every rate, size and minimum in `SETUP_PLAN.md` names its raw
    file or carries the words NOT MEASURED.

## State of the PC's code today (so nobody takes a requirement for a fact)

- Written and tested on the PC, not yet read by a second seat: the player and its record and packing code, the
  home receiver, the home step that makes round text (it calls the loop's own correction function), tools for a
  budget table, for the three-YES ledger and a guard for the home side.
- Written, never run: the Linux build script and the machine check.
- NOT built: a guard for the SERVER side with start at boot (15, 16, 19), the hourly progress line (18), the
  pause at a disk floor on the server (14), the fetch with pinned host key (27), the home programs' change to
  A26 (12, 31), the full rehearsal at home, the clean-up at the end (37).
- NOT measured: the PC's checking rate beside its other work (29), the server's rate, the room the day needs
  on the server.
