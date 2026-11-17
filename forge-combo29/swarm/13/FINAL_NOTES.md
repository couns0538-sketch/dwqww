# Notes to carry into the real FINAL block at 10:18:40Z

Things the coordinator explicitly asked to appear in the FINAL, plus my own reminders. Kept in a file so
they survive a context cut.

## Asked for by the coordinator
1. One-liner: **A settings list is not evidence of what was sent — only its length and MEMBERSHIP are.**
   (From the three times a hand-built "PC20" list omitted the 14 S14 settings; now structural in
   `lib/settings.py`, asserted at import.)

## Asked for later in the run
0. **Twice tonight my own "likely safe" guess was contradicted by a five-minute test** (job16's warm arm was
   cold because ucinewgame is a cold reset; job17/18/19 "likely safe because a systematic shift would cancel"
   was wrong — one cell moved depth 18 -> 24). That is the best argument for `lib/freshguard.py` replacing the
   guess: the guard is a runtime assertion, and it also fails when nothing was recorded so a harness cannot
   pass vacuously.
   Also carry: S-F24 withdrawn/corrected (1 of 16, +17 cp); S-F11 and S-F12 survive re-testing; S-F19/S-F21
   stand with a caveat on non-plateau cells; S-F22 CONFIRMED by exact reproduction under the strict discipline.

## My own reminders
2. Move generation is CLOSED — restate it (see `MOVE_GENERATION_CLOSED.md`), with its four limits.
3. Every finding must carry build + settings in the FINAL table (S-F1..S-F20, S-C1..S-C4).
4. S-F7 is CONFIRMED by seats 01 and 02 to the node — mark it so, not "open".
5. State which findings are still OPEN (unconfirmed by another seat with its own harness).
6. State the near-misses honestly: the two wrong-predicate/vacuous-test errors, the three settings-list
   errors, the stale-shard fabrication, and the select()-on-text-pipe bug. They are part of the record.
7. Keep "not a defect, no strength claim" as the framing on S-F10 / S-F19 / S-F21 — it is the part most
   likely to be over-read. FINDINGS.md now opens with a classification header that labels every entry as
   null result / property / not-a-defect / confirms-a-fix / my-tooling-fault, so a reader cannot mistake a
   property for an engine bug.
8. Name what I did NOT do: depth-5 divide, sanitizers (not my area), matches/strength, the owner's own
   match positions, and the full BARE_KING_LMR_CAP test.
