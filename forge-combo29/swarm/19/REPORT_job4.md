# REPORT job 4 — the TT probe miss path: the change I predicted is ALREADY IN THE CODE

seat 19 · area 9 · branch `for-fable-and-opus/swarm-19`

## 1. The three lines

**What was asked.** My own job 4 prediction: the TT probe is the second-largest PC-relevant symbol
(`probe_body<false>` 5.77 % self). I proposed that on a probe miss, remembering the first empty slot during
the first loop would make the second (replacement) loop unnecessary, since an empty slot is always the
correct victim.

**The answer.** **That change is already in the code.** `src/search.cpp:424` reads
`if (!entry.occupied()) return snapshot(entry, false);` — the replacement loop returns at the first
unoccupied entry exactly as I proposed. There is nothing to implement, and therefore no patch: the honest
result is that my hypothesis was not a hypothesis, it was a description of the existing code.

**How sure.** Certain. It is one `grep` on the source, and the same short-circuit also exists in the second
copy of the logic at `src/search.cpp:522`. My prediction R4 ("at least 20 % of probes that miss find an
unoccupied slot within the first loop") is therefore not just unmeasured — it is **irrelevant**, because the
saving it described is already taken.

## 2. Why the prediction was wrong, and what that says about my process

I predicted a change without first reading whether the code already did it. The prediction was committed
alone and cannot be edited, which is working as intended: it is now on record that I proposed an
already-present optimisation. The lesson is the one the brief states directly — "Before you write 'X is in
file Y', open file Y and look." I wrote a prediction about file `src/search.cpp` without opening the
relevant lines.

Nothing was measured, so nothing can be claimed about speed. This job cost one `grep` and produced no
artefact beyond this note, which is the correct cost for a hypothesis that dies on inspection.

## 3. What the probe's cost actually consists of (what I can say from the profile)

Since the obvious redundancy is absent, the 5.77 % is real work:

- the cluster address computation (`cluster_for`: a 128-bit multiply on this target),
- one 64-byte load of the cluster and a four-way `key32`/`occupied()` scan on the hit path,
- the generation update on a hit (`found->gen_bound = ...`),
- the age/depth replacement scan on any full miss,
- and the `TTProbeSnapshot` copy itself.

I did **not** measure the split among those, so I am not proposing a next step on the strength of a guess
twice in one job.

### Suspicions, not proven

- That `cluster_for`'s 128-bit multiply is a meaningful share, given it is on the hottest path of every
  probe. Unmeasured.
- That the generation-refresh write on hits (`found->gen_bound = ...`) dirties a cache line on every hit,
  which on a shared table could be expensive. Unmeasured, and plausible enough that it should be measured
  before being optimised.

## 4. What I did NOT do

- No patch. There is nothing to patch.
- No instrumented split of the probe's internal cost. I considered it and decided one wrong prediction per
  job is enough; the next probe job should start with counters, not a proposal.
- R1/R2/R3 were never tested, because R4 killed the job before any measurement.

## 5. Files

`job4/prediction.txt` (committed alone, unedited), this report.
