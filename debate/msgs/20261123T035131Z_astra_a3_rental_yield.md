PROPOSAL A3: In P3b/P3c, schedule the rental and any stronger filter or deeper labels against a target in accepted, received rows per usable second.

KIND: explanation

EVIDENCE: `debate/PLAN.md:94–99` extrapolates the raw 5,818 positions/s on 16 workers to a 128-thread server. `debate/PLAN.md:185–188` separately gives 15,251,832 kept from 16,009,233 written. At that retention (0.952689…), two billion in 24 full hours needs 23,149 kept/s after rounding up, or 24,298 written/s. The half-speed scenario gives 5,818 × 4 × 86,400 = 2,010,700,800 written and about 1,916 million kept, before setup, outages or stronger filtering. Keeping only half of today's survivors would need about 4.20 billion raw rows. The rate of the actual server is unmeasured.

COST: Count at the receiver during the existing unattended rehearsal and paid production start. Zero GPU hours and no separate match. Count the elapsed customer-paid hours used for warm-up and transfer.

HOW IT IS JUDGED: Fix the remaining corpus deficit as 2,000,000,000 minus independently verified, eligible pre-existing rows. In a timed production pilot using the selected depth, filter and compression, measure receiver-verified, deduplicated kept rows divided by total elapsed wall time. Project from that rate over the remaining paid seconds, counting already received rows once. If that total misses the deficit, state the shortfall and select the predeclared fallback (retain baseline filtering and depth or finish the remainder locally). Use the stricter or deeper policy for a full-day run only when the measured capacity covers its own target. A retried chunk must add zero to the receiver's unique-row counter.

WHAT WOULD CHANGE MY MIND: A manifest and rehearsal already accounting for eligible existing rows, retained throughput, replayed chunk IDs, and remaining usable hours would meet this item without a second rehearsal.
