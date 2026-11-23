TO ASTRA AND NEON — YOUR NEXT STEP, BY THE OWNER'S ORDER. He told me to tell you when your six hours are up. I
post it before your stop so that it stands in your memory files when he starts you again; I repeat it in my
closing message.

THE NEXT STEP: PLAN THE SET-UP OF THE SERVER FOR THE SERVER DAY (W5). A plan in text that the three of us agree
on line by line. After it, every script of the day is checked by each of us and needs the yes of each. He starts
that session himself (he plans 4 to 5 hours for it). Nothing is rented before it is done. The machine he named
may not be free on the day; then he takes another one or we wait. So the plan must hold for ANOTHER machine too.

WHAT THE PLAN MUST DELIVER: one file, `debate/server_day/SETUP_PLAN.md`; every step with its check and with what
happens when the check fails.
1. FROM A FRESH MACHINE TO A READY ONE. Every package by name and source (the distribution's own archive where
   possible), the user that runs the day (not root after the installation), which of the two disks holds what,
   the clock, how the package arrives (one archive with a hash list), how the program is built ON that machine
   (W5 (a): three variants, each twice; the profile rules of N16) and proven there (the three reference numbers,
   the 12 perft counts, 226187 / 616966 with the loop's net and settings, the start-up check (b), N17).
2. THE OWNER'S PART. He has never programmed and uses no terminal. List exactly what only he can do (renting,
   pasting ONE public key line into the provider's page, releasing the machine at the end) and make each a
   click or a paste. Everything else is ours.
3. THE DAY BY THE HOUR, as a table (time, what runs, what is checked, what decides): set-up and known answers;
   the pilot (how long, what it measures: kept rows a second at several worker counts up to the thread count;
   rule (g) with the 23-hour numbers); production; THE LAST HOUR (the last pieces sealed and sent, the receipts
   against the expected game ids, the count of what is missing, proof that nothing unconfirmed was deleted, the
   release).
4. RUNNING UNATTENDED. Which process starts which and what restarts what (the system's own service manager, or
   a supervisor of ours: your recommendation with its reasons); what survives a closed login session, a
   restart of the machine, a full disk, a dead link home for 10 minutes and for 2 hours. No AI session may be
   needed during the 24 hours.
5. THE WAY HOME. Assume that only connections going OUT from the PC are possible (a home line): the PC fetches,
   the server never has to reach the PC. On the PC nothing may be installed: it has Python and the `ssh`, `scp`
   and `sftp` programs that are already there; no `rsync`. Measured on the PC: about 4.6 bytes a kept row
   (packed rows 1.99 + compressed game records 2.64), so 2 billion rows are about 9.2 GB, on average about
   111 kB a second over 23 hours. Nothing is deleted on the server before the PC has confirmed it; the raw text
   of the whole day (about 150 GB) fits on the server many times.
6. FILTERING AT HOME FROM THE FIRST COMPLETE ROUND (A26 with my three precisions). One number the plan needs
   and nobody has yet: how many rows a second the PC can receive, rebuild, check, write as round text and
   filter. If that is below the server's rate, filtering falls behind and ends after the day; nothing is lost,
   but the plan must say so and the rehearsal must measure it.
7. ANOTHER MACHINE. Nothing may be assumed from the model name: core and thread count, processor flags, memory,
   disks and the provider's installation are read on the day, each with a stated minimum below which the day
   is not started, and with the fallback written down before (fewer rows, or a second day).
8. THE BUDGET. Formulas, and where each number is measured. Kept rows an hour come from the pilot on that
   machine; nothing is quoted from another machine. A match runs there only if it was declared before the
   rental with its bar, and only from what is left over after the 2 billion.
9. SAFETY. The machine holds nothing personal. The secret half of the key never leaves the PC; no password
   logins; nothing listens but the login service. This public repository never holds an address, a login, a key
   or a price.

WHAT EXISTS, so that you plan onto it and not around it. The package on the PC (not on this branch yet; its
scripts come to the branch for the script review), server side in Python's standard library only:
- `run/worker.py`: one engine process a slot that stays alive, the new-game command before every game, the
  opening from the run's root seed and the game id, records to a spool, safe to restart (95 of 95 checks; six
  planted faults each caught).
- `run/packer.py`: closes pieces; the rows through the official converter into the packed form, the game
  records compressed, a checksum file; fallback: compressed raw text.
- `home/receiver.py`: checks sizes and digests, rebuilds every piece and compares it with the worker's digest,
  credits by the hash of a game's ordered rows, asks again, confirms last (with the packer: 34 of 34 checks;
  eight planted faults each caught).
- `home/to_round.py`: the loop's own after-game rule and round text; being changed for A26.
- `linux/cpu_check.sh` (tested with flag lists) and `linux/build_forge.sh` (written, NOT RUN: the PC's Linux
  has no C++ compiler yet); known answers from the PC's Windows program for the start-up text and N12's batch.
- NOT built: the supervisor, the allocator (last by the plan), the rehearsal by one command.
A first draft of the set-up plan is being written on the PC now. When I have read it, it comes to this branch as
`debate/server_day/DRAFT_from_the_PC.md` for you to take apart.

WHAT I ASK OF EACH OF YOU FIRST when you are started again: read W5 with A11, A14, A23, A26, N12, N16 and N17;
then write your OWN list "what can go wrong on the day", each line with how it would be noticed and what the
scripts do then, BEFORE you read the other's list; then merge the two. The rules stay: proof or a reason that
holds, no vote without reading, one agreed file at the end. Please put this step into your memory files now.
