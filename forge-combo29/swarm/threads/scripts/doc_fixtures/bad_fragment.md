# t

**`Threads x MultiPV > 1` silently runs single-threaded.** Confirmed from behaviour,
not just from the source line: `single_threaded = ...` and `all` is cut to
`workers_.front()` when `multipv > 1` (`src/search.cpp:2700`). A "Threads 4 at
MultiPV 3" measurement is a Threads 1 measurement wearing a threaded label.
not just from the source line. A "Threads 4 at MultiPV 3" measurement is a Threads 1
measurement wearing a threaded label. Anyone with a MultiPV corpus should assume their
Threads setting did nothing, and this trailing clause is long enough to be compared.
