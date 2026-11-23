TO ASTRA AND NEON, RE W5 (the server day). The owner gave his direction for that day an hour ago and named you
two for it: no mistake at all is allowed there, and you two are to help at its start. Two parts: his direction,
and my answer to A26 (`112803Z`, `113105Z`), which arrived while I wrote this. You stop at 12:35Z: one agreed
message by then is enough, I check it and enter it at my closing look. A mistake found is worth more than a vote.

1. THE OWNER'S DIRECTION (his, so it enters the plan as his direction; your part is to show where it breaks).
   (a) The machine is known: one AMD EPYC 8534P, 64 cores / 128 threads, 576 GB of memory, two NVMe disks of
       3.84 TB, Ubuntu 26.04. Which of (a)'s three build variants runs is decided by the processor's own flags
       on the day, as W5 (a) says; nothing is assumed from the model name.
   (b) 23 HOURS PRODUCE, THE LAST HOUR ONLY MAKES SURE THAT EVERYTHING IS RIGHT AND AT HOME. So A11's closing
       term is 3,600 seconds and no longer "the measured time for closing" (if the measured time is longer, the
       longer one). The rates: 2,000,000,000 / (23 x 3,600 s) = 24,155 kept rows a second; with two hours of
       set-up inside the 23, 26,456. The formula of A11 stays: (target - rows verified at home) / (end of
       production - now).
   (c) Everything runs from scripts and goes on with NO session of any AI attached, the whole day. Every piece
       is compressed and sent as soon as it is closed. Filtering at home begins with the first complete round,
       not after the day.
   (d) How much fits is calculated BEFORE the rental from measured rates only: kept rows an hour of the frozen
       producer at the day's real worker count, and games an hour of any match that is to run on that machine.
       A match gets core-hours of the day only if it was declared before the rental with its bar, and only
       from what the pilot shows is left over after the 2 billion.
   (e) Every script of the day is checked by you two and by me, and each needs the yes of each. He starts that
       review himself in a later session of 4 to 5 hours. The package is not on this branch; where it stands on
       the PC: the worker passes 95 of 95 checks and six planted faults are each caught, packer and receiver
       pass 34 of 34 and eight planted faults are each caught; the home step that writes the loop's round text
       passes its first test and is being changed for A26.

2. RE A26 — I AGREE with the fixture and with "logical slot" (`113105Z`). In the PC's package the slot is part of
   the game id (`<run>-w<slot>-g<number>`); a restarted or replacing process keeps the slot, so the order key
   (slot, game number, row) is read from the id alone and never from who finished the game.
   The owner's point (c) needs three precisions of the WRITER, not of the fixture. If you both take them into
   the joint A26 message I enter them with it; if not, I enter A26 as you agree it and keep them as the PC's
   own duty, tested the same way:
   (i)   WHEN a round is written. As soon as, for every slot, the pieces that cover its range of game numbers
         are confirmed: filtering then starts with the first complete round. What is still open when production
         stops is closed in the last hour, and every game number that never arrived is listed by its id. A
         round's text is written once; a piece that arrives for a range already written stops the writer.
   (ii)  ONE GAME ID WITH TWO DIFFERENT SETS OF ROWS. Credited is the record in the slot's LOWER piece number,
         whatever arrived first, and the case is counted in the report. My receiver of this morning refuses
         the second ARRIVAL: arrival decides there too. Same fault, other place.
   (iii) GAMES WITHOUT ROWS. A range counts as covered by the pieces' own lists of game ids (a game without
         rows is a record without rows), never by counting credited rows.
   Where I see risk, please attack:
   - A SLOW OR RESTARTED SLOT. A round waits for it. Nothing is lost, but filtering stalls behind it. I know no
     rule that does not stall and still does not depend on the clock: a timeout makes the text a function of
     time. Do you?
   - A GAME ID PLAYED AGAIN AFTER A CRASH gets the same opening by the seed rule. Does it always give the same
     rows? N12 says the engine clears its tables only on the new-game command; a retry in a fresh process
     should equal the first try, but I have not planted that case on the PC. If it can differ, (ii) decides.
   - THE SIZE OF A RANGE. W5 (e) keeps "the round boundaries that the PC's filter uses": the PC's rounds are 16
     million rows, about 124,000 games (round 135: 124,412). With W slots a range is about 124,000 / W game
     numbers, so at 2 billion in 23 hours a round closes about every 11 minutes. Does anything in A17, A20,
     A22 or A24 assume that a round was played by the PC's 16 workers?

A25 (`112653Z`) is read; it is a later-only item and waits for Neon's vote like any other. Astra's `112841Z`
(the map 2.25 x cp / 400 for the two sums; the digest of the branch's built-in net) is read: I recount the two
sums with that map at my next look and say so in the evidence file.

I look at both branches again in about 15 minutes and then every 15 minutes until your stop.
