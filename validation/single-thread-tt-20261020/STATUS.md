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
default-TSan lock-pattern smoke passes; actual-engine TSan subsequently passed all nine CTests and seven API groups.

Gated Release9/9 and seven actual-API groups pass, including foreign
probe/store/hashfull, default/SMP behavior,1→4→1, externally stopped infinite
search, nested ownership restoration and both exception cleanup paths.
Six cold/warm searches match6.4.11 exactly; bench11 stays419798nodes.
An independently linked real-engine counter records706157baseline versus8204
gated successful mutex acquisitions. The predeclared100000-operation budget
fails on baseline and passes on candidate. This is an operation count, not a
measured speedup. TLS checks, flag loads and fixed drain cost may offset gains,
especially with multiple workers or very small searches.

Full Release, ASan/UBSan and TSan each passed all nine CTests. Seven actual public-API groups passed in each profile. Eight positive-node active UCI transitions passed under TSan, with legal bestmoves, complete capture and joined shutdown. The default deadlock detector stayed enabled. Eight Windows/Wine checks plus an independent artifact audit passed. No native Ryzen performance is established.
No NPS or Elo gain is accepted, and the integration engine is unchanged.
The completed649-versus651run39348571407 reached its natural1024-pair cap: W427/D1194/L427, no boundary; inconclusive. It does not validate652. A separate fresh651-versus652SPRT is prepared. Original647-versus644confirmation recovery and independent2794-check audit passed:320games, capped inconclusive; no games are pooled.

Newer accepted integration356e863dbd86d2ce24b8ee9486d7406f1d525480 adds timed-only admission accounting and evidence. Preserve it. Frozen886 already includes timed admission accounting but differs on untimed/ponder reporting. A follow-up candidate must reconcile this contract without mutating886 or discarding accepted work.

The original mixed-header diagnostic API helper was never executed; preserve it only as unused provenance. Final v3 and frozen886 drivers are authoritative. The immutable Windows package records sanitizers as pending at its earlier packaging time; completed cross-profile results here supersede that historical status.
