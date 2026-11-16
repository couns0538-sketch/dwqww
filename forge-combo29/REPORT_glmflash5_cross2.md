# REPORT glmflash5 — CROSS 2 — kimi5's job-9 slope ratios on the G position set, my build

Branch `cursor/glmflash5-work-cb5c`. Build B9 (job 20's: base 6b98f217 + kimi5's
NodeLiterals.patch.txt), sha256 f0daf1b6ec915311d998e1f0978befa77e3781bc54e0f91ee943668d0bcc1ead.
Positions: kimi5's `tests_kimi5_job9/set_G.epd` (353 game positions, fetched from its branch).
`go depth 12`, Threads 1, Hash 16, S14 on all three runs. times: see stamps.txt.

## 1. The cross-check, the answer, how sure

Asked (loop rule: a partner number remade on my build): kimi5's job-9 tree ratios on G —
slope 48 → 0.908 [0.867, 0.951]; slope 0 → 1.159 [1.099, 1.227].

Answer: **my ratios: slope 48 = 0.9083; slope 0 = 1.1585 — BOTH inside kimi5's intervals, to
three decimals of its central values. CONFIRMED.** Bonus confirmations that fell out: my G base
sum 18,466,239 equals deepseek5's job-30 G mode-0 sum EXACTLY (two builds, one number); and the
S14 first-3 rows on G carry kimi5's own shape.

How sure: deterministic searches, same positions, same settings — exact arithmetic on both
sides; the ratios agree to 3–4 decimals. As sure as a cross-check gets.

## 2. The rows (`job20g_rows.txt`, one row per search; driver committed)

| run | first-3 nodes | sum over 353 | ratio vs base | kimi5's |
|-----|---------------|--------------|---------------|---------|
| S14 (base) | 37203, 70845, 144383 | 18,466,239 | 1.0000 | (= deepseek5's G mode-0 ✓) |
| S14 + slope 48 | 30521, 41495, 73061 | 16,773,579 | 0.9083 | 0.908 [0.867, 0.951] ✓ |
| S14 + slope 0 | 43855, 59814, 79985 | 21,393,154 | 1.1585 | 1.159 [1.099, 1.227] ✓ |

Refusal lines: 0 in all three runs.

## 3. What this buys the session

- kimi5's "NullStaticSlope is the largest tree lever" claim now has two independent builds
  behind its two headline ratios.
- The book-vs-game disagreement I reported in job 20 (slope 48: book 1.012 vs game 0.908) is
  now measured on BOTH sets by ME — the disagreement is real and reproducible, not a build
  artifact.

## 4. What I did NOT do

- The intermediate slopes (36), the other seven literals of the patch, and any strength games —
  not asked by this cross-check.
- kimi5's intervals were not recomputed (bootstrap over positions is its method; my point
  ratios land inside them, which is the check).

## 5. What I am NOT sure about

- Nothing material: the sums are deterministic and the ratios match to the precision its
  intervals resolve. The only caveat: my depth-12 rows used Hash 16 and a fresh process per
  setting, as its job described; if its runs used a different hash size the agreement would be
  coincidental — its job text says Hash 16.

## 6. UTC stamps

times: see stamps.txt (cross 2 ran 15:2x–15:2xZ, after the file-21 wait expired at 15:21:01Z).

## 7. Model name

glmflash5 (GLM, flash tier), run A on `cursor/glmflash5-work-cb5c`.
