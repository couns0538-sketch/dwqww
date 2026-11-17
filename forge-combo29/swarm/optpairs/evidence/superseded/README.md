# Superseded evidence — do not quote

`pair1-report-3repeat-NAIVE-superseded.json` is the first run of the Hash x Threads
grid. It is kept only because `STATUS.md`'s "withdrawn" section cites it.

It used three repeats per cell, compared the same cell with itself, and reported
"12 of 12 positions differ" between Hash 16 and Hash 64 at Threads 4 — while its own
A/A control also differed 12 of 12. The number is an artefact of Threads noise, not
an effect of Hash.

The replacement is `../pair1-hash-threads.json` (6 repeats, A/A design),
`../pair1-analysis.json`, and `../pair1-pooled.json`.
