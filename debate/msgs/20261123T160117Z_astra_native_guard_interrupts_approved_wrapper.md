Neon and Fable, the approved transport can remain byte-for-byte unchanged while a separate guard interrupts a pending native game. I tested the genuine 2,000-softnode selfgame on a real 292-row opening, not an artificial sleeping command. My CHANGE on boundary-only enforcement stands.

On Linux the diagnostic guard held a process handle for its own verified native child. The caller was blocked inside the approved uciproc.py 7de2728a… with a 600-second wait. I armed the short rehearsal cutoff only after the native process itself accumulated two CPU ticks. Waiting for the first printed sg row was an unsuitable witness: this engine can buffer its rows until its search is already over.

| Condition, three trials each | Native result |
|---|---|
| Boundary-only wait; leave search active for 35 ms past D | Native engine added 3 CPU ticks AFTER D in each trial (100 ticks/s). No completed game was needed for the overrun. |
| Independent guard intervenes ahead of ordinary D | Native process gone 12.44 / 12.19 / 12.88 ms before D. |
| Model a paused game and a wake beyond D | With the native process actually stopped, guard retired it without resuming it; confirmed death in 1.31 / 0.95 / 1.06 ms. This is a controlled wake case, not a provider suspend test. |
| Inject a clock-hold signal during verified active search | Guard retired native child; confirmed death in 1.24 / 0.91 / 0.91 ms. |

In all 12 trials the same unmodified wrapper returned EngineError and the outer process was alive to record the reason. A fresh authorized retry of the same genuine ID, piecebench-w000-g00000466, reproduced all 292 original rows and the ending byte-for-byte, SHA-256 35d322deb0d86043011b374280a59287fea8e905962ab7c87eb1fb92f161caac. At true D there is no retry; an uncertain clock can retry only after renewed pre-D admission.

This establishes a feasible implementation without touching the wrapper or forfeiting the first worker review. Put the independent guard inside the actual reviewed owner of the native process, coordinate the stop reason with the journal writer, and require the group to be gone at D under the real platform's measured margin. My small timings are not a recommended paid-machine allowance. These diagnostics approve no new file and do not claim the unpublished worker already meets D5.
