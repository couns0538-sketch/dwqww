# STATUS — build provenance audit

**State: COMPLETE.** No finding re-measured (not the assignment). Every claim below is
backed by a script in `scripts/` and a transcript in `evidence/`.

Audit base `6b98f2170a3210e71beed04bbd2553972c253ed7` · census **8,899 commits / 617 refs**
(612 `origin/*`, 3 tags, 2 heads — the audit branch is itself a ref) · `evidence/refs_census.txt`.

## The brief's premise, checked

> "build PC r15 `068f0927` … `git rev-list --all` contains no object starting with `068f`,
> so the row cannot be re-derived by anyone."

- `git rev-list --all | grep -c '^068f'` = **0**. **True, and it is the wrong test.**
- `068f0927…` is the **sha256 of a binary**, not a commit id. No commit should start with it.
- The build **is** re-derivable: committed patch text (`FABLE_TO_swarm_5.md`) whose sha256
  verifies as `d6bd72c5…`, applied to `6b98f217`, built with the documented flag, gives
  binary sha256 `068f0927…` **byte-exact**, `id name` = `Chess Engine Forge 6.4.24 candidate`,
  and `bench 11/13/16` = `312866 / 862329 / 3024920` — the exact pins the handoff records.
- Base binary `e06310ec…` reproduces byte-exact from the same commit.
- Net file: 6,309,096 bytes, sha256 `1db8525e…`, FNV-1a64 `fdff70de72e4ca82`, byte-exact.

Transcripts: `evidence/reproduce_builds.txt`, `evidence/reproduce_net.txt`,
`evidence/verify_claims.txt`.

**Verdict on the row the brief named: it is sound.** The defect is in the *writing* — a
file hash and a commit id appear in the same tables with nothing distinguishing them, and
that is what made a correct grep look like a fatal provenance hole.

## Counts

| | |
|---|---|
| build identifiers found | **14** (+ PC20, which is a settings block, not a build) |
| **resolved** | **9** |
| **unresolved** | **5** |
| findings naming some build | **874** across 20 seats |
| findings on a **resolved** build | **829** — re-derivable today |
| findings on an **unresolved** build | **45** — must be re-measured or re-labelled |
| worst offender | **"TSan build", 27 findings / 8 seats** — no flags recorded, and its load-bearing row (`24-F3`) is a 1000× **wall-clock** outlier measured inside TSan |

Resolved: `6b98f217` (base commit), PC r15 (label), `068f0927` (r15 binary), `e06310ec`
(base binary), `d6bd72c5` (patch), `1db8525e`/`fdff70de` (net), `handoff/fable-opus…`,
`integrate/combo29-all`, `e6beb5f9` (result digest).
Unresolved: TSan descriptor, ASan+UBSan descriptor, `owner's PC` (unshared net),
`-D_GLIBCXX_DEBUG` descriptor, `698d2d9b` (r15 TSan binary).

Also unresolved but carried **only in evidence files, never in a finding row** — so no
finding rides on them: `b109a0a5`, `7c4e1aee`, `6e0e9522`, `81c52608`, `1a9460d6`,
`0dceb07e`, `571e7c83`, `ae1a49b6`. All eight: hash recorded, **no rebuild recipe**.

## Corrections made to my own method, in order (each changed the answer)

1. **Token-level counting conflated `PC20` with `PC r20`** — a settings block was being
   reported as a build with 2,236 file mentions. Split, and `PC20` excluded from the build
   count.
2. **A loose substring match in canonicalisation silently dropped every short binary
   hash**, so the table simply did not list them. Replaced with prefix matching.
3. **The row mapper searched a hardcoded hash list**, missing five binary sha256s the
   census had found. Made data-driven from `evidence/identifiers.json`.
4. **The transitive-dependency pass first matched on shared parent directory** and
   produced 6 false positives (seat 30's rows cite `read_board.sh`, whose *siblings* carry
   the hash). Now requires the hash inside the file the row actually names → **0**.
5. **The net FNV check hashed the whole file.** The generator appends its own digest as an
   8-byte trailer, so the reported FNV is over `data[:-8]`. The artefact was fine; the
   check was wrong — the exact wrong-span trap the corpus documents.
6. **"the owner's PC" matched 31 findings on a bare mention.** Only net-dependent rows
   count → **3**.
7. **The hash→path map was produced by an unrecorded shell one-liner**, and it
   undercounted: it enumerated blobs but reported the *first* path per blob, so a hash
   appearing in 30 files was reported as 22. A provenance audit must not depend on an
   unrecorded command, so it is now `scripts/find_unresolved_paths.py` and the counts are
   per path (`b109a0a5` 22 → **30**). No finding count changed — that map only feeds the
   transitive-dependency pass.
8. **I rewrote a regex to silence a lint warning, and it changed the audit's answer.**
   The super-linear-backtracking warning was legitimate, so I replaced
   `owner'?s?[^.\n]{0,30}\bnet\b` with a hand-rolled "linear" predicate and checked
   equivalence. They disagreed, and the disagreement was real: the regex consumes
   through the first "net" after an "owner", so a second "net" in one phrase is not a
   separate match. The rewrite reported **874 -> 871 findings and 45 -> 42 unresolved**.
   **A linter warning is not worth changing the product for**, so the regex is back and
   CI's warning-level annotation is accepted. This is the sharpest instance in the run of
   a check whose fix is not evidence for its replacement: the counts are the deliverable,
   and the tidy version was quietly a different audit.
9. **Two static-analysis rules were genuinely worth fixing**, not just satisfying:
   `open()`/`makedirs()` were called on raw CLI arguments (a path-traversal shape) and
   scratch dirs defaulted to a hardcoded `/tmp` path. Both are now routed through
   `scripts/pathsafe.py`, which resolves the target and refuses anything outside the
   audit directory — verified by passing `--out /etc/evil.json` and `--out
   ../../../evil.json`, both of which now raise instead of writing. The one exception is
   the corpus cache, which the program creates itself with `mkdtemp` (owner-only,
   unpredictable name) and passes `allow_outside`; output paths never can.

## Limits, stated

- **46 findings are attributed by descriptor, not by name.** "ASan+UBSan build" in prose
  may name a build that *is* reproducible elsewhere in the same report; this audit counts
  what the row says, not what the seat meant. The count is an upper bound on the gap.
- **`map_finding_rows.py` only reads rows that name a build.** A finding that never names
  one is not in the 874 and not counted as a gap — it is a different defect (no provenance
  at all) that this audit was not scoped to size.
- **The rebuilds pin one toolchain.** All five reproductions used g++ 13.3.0 with
  `LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13`. A different g++ may give different
  bytes for the same source — that would be a finding about reproducibility, not about
  these hashes, and it was not tested.
- **`integrate/combo29-all`** is 277 commits **behind** the base's line (merge-base
  `e04556ddc`); rows measured there are statements about an older engine. The findings
  document already records one such retraction; this audit found no second *unretracted*
  instance in a finding row.
