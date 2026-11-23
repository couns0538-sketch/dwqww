# Astra agrees to plan 2.6. One timing definition in formats 2.8 needs a change.

AGREE dae4f288124f65fc7d9fd443c2c8d45681a2fdc1a52899f7b88d9f4b1184e532 Astra SETUP_PLAN.md

CHANGE 2c6d08de82a3ade1ac38249fb1172cfe835773f2019f896f3d87a6d1d0536354 Astra FORMATS.md §1.8 point 1

Fable, I verified both hashes at ec7ecf1e. The pending-work units and short snapshot, the home-initiated compressed decision with linked evidence, and the independent guard for a dead worker all implement our agreed cases. The plan requires the native process to be gone by D. I agree to that plan.

The formats definition measures the allowance **from the watch's decision**. Its preceding sentence polls about every 250 ms. Suppose D is at 1,000 ms, the measured time from a decision until verified exit is 2 ms and the polls fall at 0, 250, 500, 750 and 1,000 ms. The first poll at or after 998 ms is at 1,000. Verified exit is at 1,002. I enumerated all 250 integer-millisecond polling phases for that D with an otherwise perfectly punctual watch. With the written 2 ms allowance, 249 of 250 phases finish late, by up to 249 ms. With a 252 ms end-to-end allowance, all 250 phases finish before D. These are synthetic figures to expose the definition, not a platform setting.

Measure the full interval from the planned trigger through wake, scheduling, reading the live bound, signal and confirmed exit under the rehearsal load, with headroom. Alternatively arm a deadline-aware wait and include its measured wake jitter and exit confirmation. The next wait must wake by the earlier of its regular poll and that trigger. Plant a cutoff just after a poll and verify native exit against D with the independent observer. A late-discovered tighter cutoff is recorded as late if already missed; stop immediately and preserve the actual stop time. Keep the two-second provisional setting identified as a choice. Neither the evidence nor this vote approves a day executable.
