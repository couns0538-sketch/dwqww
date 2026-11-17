# BASE.md — which tree these numbers came from, and how it was verified

Read this before quoting any number from this seat.

## Short version

| | |
| --- | --- |
| Audit base commit | **`6b98f2170a3210e71beed04bbd2553972c253ed7`** (`6b98f217`), "Checkpoint standalone NNUE v3 work and evidence" |
| Build | `cmake -DCMAKE_BUILD_TYPE=Release -DFORGE_MARCH=native -DCMAKE_CXX_COMPILER=/usr/bin/g++`, `LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13`, g++ 13.3.0 |
| **Pin** | `bench 11` → **312866** nodes. Verified before recording any result. |
| Also built | `6020972d3` (`integrate/combo29-all`), this seat's original base, for comparison only |

`/usr/bin/c++` is a broken clang on this host and cannot link `-lstdc++`; the
build must force `/usr/bin/g++` and point `LIBRARY_PATH` at
`/usr/lib/gcc/x86_64-linux-gnu/13`.

## What was wrong with the first pass, and what was not

The first revision of this audit measured on `6020972d3`
(`integrate/combo29-all`). That is **not** the audit base. The correction I was
given described the two as "completely disjoint, no common ancestor, base is a
root commit with 0 parents". Checked directly, that description is inaccurate on
both points:

```
$ git merge-base origin/integrate/combo29-all 6b98f217
e04556ddc3a430b2e751159b0d46111ef56c8b89        # a common ancestor exists

$ git rev-list --parents -n1 6b98f217 | awk '{print NF-1}'
1                                               # 6b98f217 has a parent

$ git rev-list --count origin/integrate/combo29-all..6b98f217
277                                             # target is 277 ahead

$ git rev-list --count 6b98f217..origin/integrate/combo29-all
1                                               # and the other is 1 ahead
```

So: **not disjoint, and not a root commit.** But the substance of the warning was
right and worth acting on — the trees differ materially where it counts:

```
 forge-combo29/src/search.cpp | 923 ++++++++++++++++++++++++++++++++++++++-----
 forge-combo29/src/uci.cpp    | 181 ++++++++-
```

`search.cpp` is where the drawn-root bail lives, and `uci.cpp` is where the book
gate lives. Both were re-measured rather than assumed.

## What was re-verified, and result

Everything below was run against a build of `6b98f217` with the pin confirmed.
Script: `scripts/reverify_6b98f217.sh`, evidence: `evidence/reverify-*.txt`.

| # | claim | result on `6b98f217` |
| --- | --- | --- |
| 1 | `go btime` with White to move does not reach the book | **reproduces** |
| 1b | same, plus: with no recognised clock for the mover the search is not time-limited | **reproduces** (new observation) |
| 2 | the book pre-empts the drawn-root answer, by book entry | **reproduces**, 2/2 with an entry, 0/4 without, 0/6 with book off |
| 3 | `Book Depth` reads the fullmove counter | **reproduces** (and is *correct* behaviour — see below) |
| 4 | default `Book Variety 30` is nondeterministic; 0 is not | **reproduces**, 2/10 distinct at 30, 1/10 at 0 |
| 5 | MultiPV is ignored on the book path | **reproduces**, 2 lines and no `multipv` token at MultiPV 1/2/3 |
| 6 | book reply is exactly two lines, no score | **reproduces** |
| 7 | one book emit site | **yes, now at `uci.cpp:539-540`** (was 385-386) |
| 8 | book data and legality | **identical**: 2616 entries, 2429 positions, 2520 moves, 0 illegal, 135 SEE flags |

Two things worth calling out:

* **The book walk is byte-identical across both bases.** `probe_book` built
  against each tree produces the same 2429 lines, and the soundness result is the
  same to the digit. That is expected — `book.cpp` and `book_data.inc` are
  unchanged between the trees — but it was checked rather than assumed.
* **`bench 11` is 312866 on both binaries.** The trees agree on search behaviour
  at the pinned bench despite the 277-commit gap, which is why none of the
  behavioural findings moved.

## The one thing that changed my conclusions

Not the base. Building candidate `game_ply` fixes did. The `Book Depth` finding
was reported as a defect in the first revision and **retracted** after a 14-case
matrix showed the lock is correct 14/14 and both proposed "fixes" are worse
(4/14 and 2/14 wrong). See `FINDINGS.md` §5.3. The behaviour reproduces on
`6b98f217`; the *diagnosis* was what was wrong.

## Reproduce the provenance check

```bash
cd <repo>
bash forge-combo29/swarm/65/scripts/reverify_6b98f217.sh
```

The script refuses to record anything unless `bench 11` prints 312866. It builds
in a detached worktree at the target commit, so the working tree is untouched.
