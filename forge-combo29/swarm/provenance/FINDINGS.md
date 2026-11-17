# Build provenance audit — every build identifier in the seat reports

Audit base: `6b98f2170a3210e71beed04bbd2553972c253ed7`, folder `forge-combo29/`.
Measured against: **8,898 commits reachable from 615 refs** (611 `refs/remotes/origin/*`,
3 `refs/tags/*`, 2 `refs/heads/*`; this audit's own branch is excluded and named in
`scripts/verify_claims.sh`, so the figure does not drift with its own pushes). Command that enumerates them, and the full census:
`evidence/refs_census.txt`.

> **The negative claim in the brief had to name its command, and so does this one.**
> "No object starts with `068f`" is a claim about a list. The list is every ref in the
> repository except this audit's own branch — 615 refs, including all 611
> `refs/remotes/origin/*` remote branches and all 3 tags — enumerated by name in
> `scripts/verify_claims.sh`. Run it and `grep -c '^068f'` returns **0**. That is the
> whole evidence, and it is reproduced in `evidence/refs_census.txt`.
>
> The audit's own branch is excluded **by name, not silently**, because including it
> makes the published figure grow with every push — and it is the branch under audit, so
> counting it would be the census counting itself. (`rev-list --all --exclude=<ref>` was
> tried first and left the count unchanged; the explicit ref list is what works.)

---

## 1. Headline: the premise does not survive contact with the record

The brief says build **PC r15 `068f0927`** cannot be re-derived by anyone because no
commit in the repository starts with `068f`. **The observation is correct and the
conclusion is wrong**, because `068f0927` was never a commit.

`068f0927…` is the **sha256 of a compiled binary**, `068f0927768d30be60e8cce6c9f29620dec330565397357dccc9e0fe361e32f4`.
A grep over commits is guaranteed to return zero for a file hash. What matters is whether
the *build* is reachable from committed text, and it is:

| step | artefact | check | result |
|---|---|---|---|
| 1 | r15 source, as text | `forge-combo29/soak_all/FABLE_TO_swarm_5.md`, blob `12772bb7` | committed |
| 2 | patch integrity | sha256 of the fenced block, first `diff` line to last line | `d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a` — **matches the recorded prefix `d6bd72c531f785f4`** |
| 3 | applies to base | `patch -p1` inside an archive of `6b98f217` | exit **0**, 11 files, no fuzz |
| 4 | binary | `cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1` | sha256 `068f0927…` — **byte-exact** |
| 5 | identity | `id name` | `Chess Engine Forge 6.4.24 candidate` — the string the report quotes |
| 6 | pins | `bench 11/13/16` sent on **stdin** | `312866 / 862329 / 3024920` — **all three match** the handoff table |

The base build reproduces the same way: `6b98f217` + g++ 13.3.0 Release →
`e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`, byte-exact.

**So the row the brief calls load-bearing is re-derivable end to end, by a third party,
from committed text alone.** Both binaries, the patch and the net file were rebuilt in
this audit; the transcript is `evidence/reproduce_builds.txt` and the scripts are
`scripts/reproduce_builds.sh` and `scripts/reproduce_net.sh`.

Two things the brief's framing got exactly right, and they are the reason this audit was
worth running:

- **A figure whose provenance is a build nobody can check is the right thing to be
  suspicious of**, and the `068f` grep was the right first move. It found a real
  weakness in *how the reports cite builds*, just not the weakness it predicted — see §4.
- **Trap 2f is real in this corpus**, and there are 45 findings sitting on builds that
  genuinely cannot be re-derived. They are just not the ones anyone was looking at.

---

## 2. The table — every build identifier, sorted by findings riding on an unresolved build

"Findings" = distinct `(seat, finding-id)` pairs whose row names that build. One finding
can name two builds (the usual shape is "PC r15 under PC20 VS base under S14") and is
counted against each. **874 findings across 20 seats name some build.** 45 of them name a
build that cannot be re-derived.

| # | identifier(s) in the reports | findings | seats | resolved? | why / what it actually is |
|---|---|---|---|---|---|
| 1 | "**TSan** build" (prose descriptor, flags never recorded) | **27** | 8 | **UNRESOLVED** | No flag set, no compiler line, no hash. One row does hash it (`698d2d9b`, itself unresolved). TSan builds are the most flag-sensitive in the set. **Worst offender** — see §3. |
| 2 | "**ASan+UBSan** build" (prose descriptor) | **12** | 7 | **UNRESOLVED** | The one ASan build that got a hash is `b109a0a5`; it is *also* unresolved (my ASan rebuild gave `ba18e7a7`). Behaviour survives; bytes do not. |
| 3 | "**the owner's PC**" (its trained net, explicitly not shared) | **3** | 2 | **UNRESOLVED by design** | The handoff states the PC plays with its own net and cloud seats keep the built-in evaluation. Rows whose value depends on that net are unreproducible off that machine, and saying so is honest rather than a gap. |
| 4 | `-D_GLIBCXX_DEBUG` build (descriptor) | 2 | 1 | **UNRESOLVED** | My `-D_GLIBCXX_DEBUG` base build gave `715b7c90` against a reported `581159a4`, so ≥1 other flag differs and the record does not say which. |
| 5 | `698d2d9b` (PC r15 TSan binary) | 1 | 1 | **UNRESOLVED** | Hash recorded, no recipe. |
| 6 | **"PC r15"** (the label) | **393** | 19 | **RESOLVED** | Label → `6b98f217` + `FABLE_TO_swarm_5` patch → binary `068f0927`. All three links verified in §1. **The 393 findings that name it are re-derivable.** |
| 7 | **`6b98f217`** / "the base" | 378 | 20 | **RESOLVED** | `git cat-file -t` = commit; contains `forge-combo29/`; **is** the audit base. Reachable from refs (80 remote branches contain it). |
| 8 | `d6bd72c5…` (r15 patch text) | 15 | 12 | **RESOLVED** | sha256 of the committed fenced block. Verified byte-exact in §1 step 2. |
| 9 | `e06310ec…` (base binary) | 14 | 7 | **RESOLVED** | Rebuilt from `6b98f217`, byte-exact; pins match. |
| 10 | `068f0927…` (PC r15 binary) | 13 | 8 | **RESOLVED** | Rebuilt, byte-exact. **This is the identifier the brief flagged.** |
| 11 | `1db8525e…` / FNV `fdff70de72e4ca82` (v3 test **net**, not a binary) | 7 | 3 | **RESOLVED** | Running the committed `make_v3_testnet.py` gives 6,309,096 bytes, sha256 `1db8525e…`, FNV-1a64 `fdff70de72e4ca82` — all three figures reproduce. (**Check the span**: the generator hashes the payload and appends the digest as an 8-byte trailer, so the file's own FNV is over `data[:-8]`. Hashing the whole file "differs" and that is a fault in the *check* — the same wrong-span trap the corpus warns about. Caught and fixed during this audit; `scripts/reproduce_net.sh` now checks both the payload and the trailer.) |
| 12 | `handoff/fable-opus-combo29-all` | 6 | 6 | **RESOLVED** | Branch exists; an older tree, not the base. Correct as a statement, ineligible as evidence about the base. |
| 13 | `e6beb5f9…` / `2337b0d1…` (digests of result tables, not builds) | 2 | 1 | **RESOLVED** | Checksums *of results*. They pin a table's integrity, not a build — see the caveat in §4. |
| 14 | `integrate/combo29-all` | 1 | 1 | **RESOLVED** | Exists at `6020972d3`; 277 commits **behind** the base's line (merge-base `e04556ddc`). Older tree. |
| — | **PC20** (S14 + 6 options) | 484 | 20 | *n/a — not a build* | A settings block, listed so nobody counts it as a build. It resolves trivially: it is a list of `setoption` commands. |

**Count: 14 real build identifiers — 9 resolved, 5 unresolved.** (Plus PC20, which is a
settings block and not a build at all.) Every hex prefix in the table, resolved against
the object database with the enumerating command: `evidence/refs_census.txt`.

Binary hashes that appear **only inside evidence files and never in a finding row**
(so no finding rides on them, but they are in the record): `7c4e1aee`, `6e0e9522`,
`81c52608`, `1a9460d6`, `0dceb07e`, `571e7c83`, `ae1a49b6`. All seven have a recorded
hash and **no recorded rebuild recipe**. `1a9460d6`/`0dceb07e` are seat 28's deliberately
*planted* controls; a control that misbehaves is still a valid control, so their
conclusions stand even though the bytes cannot be re-derived.

---

## 3. The worst offender

**"TSan build", 27 findings across 8 seats — and its most load-bearing row is a timing
measurement.** Seat 24's `24-F3` reports a ~**1000× warm-state search-time outlier**
(348,278 ms at Threads 2, 376,680 ms at Threads 4) for one position, against 0.8–2.0 s in
fresh processes. That is:

- measured on a build whose flags are **never recorded** (so nobody can hold the same
  instrument), and
- a **wall-clock** statistic from inside a ThreadSanitizer process, which is the least
  representative timing environment available.

The claim ("this position is a warm-state outlier") may well be true — 24-F3 is reported
as reproduced three times, and a fresh-process control is given. But **the magnitude
cannot be attributed to the engine** from this record: a 1000× factor quoted from a TSan
build is a property of "the engine under TSan at whatever flags were used", and the flags
are missing. A reader cannot separate the defect from the instrumentation.

This is the honest ranking: not the most findings (seat 01/27's PC r15 rows are far more
numerous at 393), but the most findings whose **magnitude** dies with an unrecoverable
build. The 393 PC r15 rows are re-derivable; these 27 are not.

---

## 4. What must be re-measured, if I were the owner

The deliverable is the list and the reason — **I did not re-measure any of these.**

**Must be re-measured on a build that exists (blocking):**

1. **Every wall-clock / timing row measured under TSan** — starting with `24-F3`
   (348 s / 376 s outlier), `24-F9`, and seat 04's TSan rows `04-C4`, `04-F22`, `04-F24`,
   `04-F25`, `04-F26`, `04-F4`. *Reason:* a timing number is a property of the
   instrumented process; with the flag set unrecorded the number has no referent. Re-run
   on the reproducible Release binary (`068f0927` / `e06310ec`), Threads 1, and quote
   that.
2. **Any finding whose headline number appears ONLY against an ASan/TSan descriptor**
   — `07-C38` (which rests on all three descriptors at once, see below), `10-F4`,
   `15-F2`, `21-C6`, `21-F10`. *Reason:* same as above where the number is a time or a
   rate; sanitizer *findings* (a crash, a leak, a data race, an out-of-bounds) are safe
   to keep, because those are behaviour the source can be re-instrumented for.
3. **The three rows that depend on the owner's unshared net** — `01-23-F200`, `29-F20`,
   `29-N11`. *Reason:* not a defect in the record; the net is not shared on purpose.
   Either mark them "owner-machine only" permanently, or re-run with the built-in
   evaluation and say so.

**Should be re-checked, not necessarily re-measured (cheap, and one is a real trap):**

4. **`07-C38` names TSan, ASan+UBSan *and* `-D_GLIBCXX_DEBUG` in one row.** It is the
   single row in the corpus that rests on all three unresolvable descriptors. Whatever
   its conclusion, its support is the least checkable in the set.
5. **Rows citing `integrate/combo29-all` or `handoff/fable-opus-…`** as though they were
   the base. Both are real branches — but the base is **277 commits ahead** of their
   merge-base, so a number taken there measures a different engine. The findings document
   already records one such retraction (the FEN field-count row); this audit found no
   second *unretracted* instance in a finding row, which is a genuine negative worth
   stating.
6. **Anything quoting a binary hash as if it identified a source revision.** Nine seats
   write `068f0927` and `6b98f217` in the same table without distinguishing a *file* hash
   from a *commit*. Nobody is wrong, but a reader can reasonably try `git show 068f0927`
   and conclude the work is unfounded — which is exactly what happened in this brief.
   Fix the writing, not the measurement.

**No action needed:** all 393 PC r15 rows, all 378 base rows, the 15 patch rows, the 7
net rows, and the 13 `068f0927` rows. They are re-derivable today; this audit re-derived
their build from scratch to prove it.

---

## 5. Two things this audit found that were not asked for

- **The 068f confusion is itself a defect in the reports' writing, and it is
  contagious.** The brief's negative claim and the finding it was aimed at are both
  *correct in their measurement* and wrong in their *joining*: a binary hash was read as
  a commit id. That is the joining-phrase family from `forge-findings.md` §6 — every
  individual statement true, the arrangement implying something false. `STATUS.md`
  records it as the one structural recommendation.
- **A result-table digest (`e6beb5f9`) is not a build reference, and two rows treat it as
  if it were.** A checksum over `(fen|nodes|score|best)` rows proves the table was not
  edited; it says nothing about which engine produced it. Two different builds can each
  be internally consistent. Those rows still name their build elsewhere, so nothing is
  broken — but the digest should not be read as provenance.

## 6. Reproducing this audit

```
python3 scripts/enumerate_builds.py     # census + role classification -> evidence/identifiers.json
python3 scripts/map_finding_rows.py     # finding row -> build refs     -> evidence/finding_rows.json
python3 scripts/build_table.py          # canonical identities + ranks  -> evidence/build_table.json
python3 scripts/find_unresolved_paths.py  # hash -> swarm paths  -> evidence/unresolved_hash_paths.json
python3 scripts/transitive_deps.py        # findings whose evidence files carry a dead hash
sh      scripts/reproduce_builds.sh       # rebuilds BOTH binaries; verifies patch + pins
sh      scripts/reproduce_net.sh          # rebuilds the v3 net; verifies all three hashes
```

Every script is mechanical and re-runnable; none reads the worktree, so a stale checkout
cannot change the answer. `scripts/verify_claims.sh` re-runs the negative claims and the
`git rev-list --all` census that every "does not exist" in this document depends on.
