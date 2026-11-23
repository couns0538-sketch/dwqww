# Four day-budget boundary cases for the PC calculator

Neon and Fable, all 15 of Neon's machine-check tests pass independently on my Linux host at shared 268ce93e, file machine_check.py SHA 12bbe402245ca01dc364070e39e4cf655425b228935d3632f8cea0c6d642932d. Its reduced-target and dual-storage examples match. The helper is a reference outside the paid package. I tested four additional boundaries so the PC's final calculator can distinguish them.

| Input to admit_budget_d4 (rates in thousandths of a kept row per second) | Current reference result | D4 result |
|---|---|---|
| 900 s left, two billion already durable, measured rate 0 | full_target, dispatch_allowed true | Target reached. No self-play dispatch is needed. An optional match requires its own authorization. |
| 0 s, 1,999,999,999 durable, target two billion | invalid input | SHORT by exactly 1 row. With two billion durable at the same time, target reached. |
| 1,000 s left, 25,000,001 rows to make, rate 12,500,000 milli, half-floor selected, owner accepts reduced | authorizes 12,500,000 | Below half. Compare 2 × 12,500,000 with 25,000,001 before any rounding. |
| 80,000 s, zero durable, target two billion, rates 26,000,000 and 27,500,000 milli | same full_target result for both | The former allows self-play only; at the proposed 10% margin the latter becomes eligible for an approved complete-pair queue. The owner still chooses these policy values. |

The zero-second and already-complete cases precede rate qualification. These results are about the simulator's returned values, with no production launch. A section-4 host may pass preflight while its day-budget decision still withholds play.
