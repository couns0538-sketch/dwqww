# Forge6.4.12 TT synchronization experiment

Baseline6.4.11 `c5cbf97a7291a3bd960c71dcd77a29bf7c95ad8e`; gated candidate
`8865666cc0ab4961cd507bae40ff6ce44e9319df`. Default Shared library searches and
multiple workers retain striped synchronization. The UCI controller opts in
only when it owns one worker: request exclusive access, drain each existing
stripe, then hold one gate while owner-thread calls reuse that ownership.
Foreign entry access waits; lifecycle still requires every accessor joined.

The earlier all-held-stripes prototype `a5d2fcb5` passed Release9/9 and exact
search parity, but a default TSan smoke hit the runtime's64-held-lock limit at65.
Its source and evidence remain on the all-stripes branch. No sanitizer check
was disabled. The revised sequential drain holds at most two mutexes and its
default-TSan lock-pattern smoke passes; actual-engine TSan is still pending.

Gated Release9/9 and seven actual-API groups pass, including foreign
probe/store/hashfull, default/SMP behavior,1→4→1, externally stopped infinite
search, nested ownership restoration and both exception cleanup paths.
Six cold/warm searches match6.4.11 exactly; bench11 stays419798nodes.
An independently linked real-engine counter records706157baseline versus8204
gated successful mutex acquisitions. The predeclared100000-operation budget
fails on baseline and passes on candidate. This is an operation count, not a
measured speedup. TLS checks, flag loads and fixed drain cost may offset gains,
especially with multiple workers or very small searches.

Full ASan/UBSan, actual-engine TSan and Windows validation are underway.
No NPS or Elo gain is accepted, and the integration engine is unchanged.
The active649-versus651run39348571407 tests the previous NNUE hypothesis; it
does not validate652. A separate fresh651-versus652SPRT remains gated pending
correctness. Original647confirmation recovery is separately preserving the
existing artifact; no games are replayed or pooled.
