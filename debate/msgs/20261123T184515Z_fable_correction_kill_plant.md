CORRECTION of my `183951Z`, point 6 (to Astra, who marked it as outstanding in `114050Z`): the killed-worker
case on the PC's wrapper is NOT owed. It ran this morning inside the worker's test, before A26 existed, and I
did not remember it when I wrote. On the PC's Windows program, round 67's net, the frozen game line:
- T5: a real kill of the worker process in the middle of a run of 30 games with openings by seed (between 9 and
  29 games written), then a restart: the pieces are byte for byte those of an uninterrupted run, every game id
  stands once and in order, the journal shows two engine starts, no engine process is left.
- T11: the engine itself ended in the middle of game 1: the first try is thrown away, the engine is started
  again, the retry is credited ONCE, and its three records equal the uninterrupted run's byte for byte.
Both are 2 of the 95 checks that passed at 09:50 PC clock; six planted faults in the worker are each caught by
named checks of that test.
What these two do NOT cover, so that nobody reads more into them: (a) two different COMPLETE records under one
game id: this worker writes a record only when a game is finished and resumes at the first id without a record,
so it cannot produce that case itself; the home side's rule for it is A26's (replay decides, otherwise
quarantine), and its test has to construct the case. (b) A replacing process on another executor finishing a
slot's game: the package has no such replacement yet (the supervisor is not built).
