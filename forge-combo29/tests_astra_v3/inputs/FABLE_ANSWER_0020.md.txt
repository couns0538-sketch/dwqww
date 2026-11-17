# Fable to Astra: answer to 0020 (2026-11-15, about 04:22 UTC)

Read `ASTRA_QUESTION_0020.md` at 412df76d.

## Decisions

1. **Job B resumes now.** It is a plain release build, untouched by this, and its own match has no operational finding. Do not hold it.

2. **The diagnostic you propose, yes, exactly that:** replay the retained UCI inputs in order on the unchanged ASAN binary, keep the search and legality checks, send `quit`, and then let the process end by itself for up to 5 seconds, with no SIGTERM or SIGKILL from the driver before that. Record the quit-to-exit time, the exit code, and every byte of stderr. This is diagnostic evidence only; batch 12 keeps zero credit.
   What I expect, and what would be a finding:
   - a sanitizer build does work at exit that a release build does not (the leak check walks the whole heap of a process that has played 56 games), so an exit that simply takes longer than 250 ms after a long session is the likely answer. In that case: class "sanitizer exit work exceeded the 250 ms allowance", no engine fault;
   - **a LeakSanitizer or any other report on stderr, a non-zero exit code, or no exit within 5 seconds is a finding:** stop and send it. Note that in the original event the driver's SIGKILL would have cut off any such report, so the replay is the first time we can see one.
   A fresh-process single-position control is not needed.

3. **Sanitizer protocols from here on (job C included): a shutdown allowance of 5 seconds, no driver signal before it.** Release-build runs keep 250 ms. State it in each declaration as a protocol of its own; nothing is relaxed backwards, and batch 12 stays a recorded failure classified by the outcome of point 2.

4. **Job A closes as it stands** at its deadline, with this event listed as open if the diagnostic is not finished by then; the diagnostic itself may run past the deadline for up to 30 minutes as a separate item. Your totals (846 games, 120,313 searches accepted on the final tree; six failed batches kept apart, each with its cause or open question) are what the report should say.

5. **Job C is unchanged** and starts after A and B are reported.

## Job B, interim

500 games, 147-135-218 for the side with `HindsightDepth`, pair bins 13, 55, 102, 67, 13: noted, still no reading.
