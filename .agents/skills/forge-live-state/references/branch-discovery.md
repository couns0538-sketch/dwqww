# Branch discovery and provenance (read-only)

Use this workflow with Codex Cloud, Claude Code, or a connected GitHub client. The ability to query GitHub remotely is helpful but **not required** to run the skill; report missing access rather than inventing results.

## Checks in order

1. Verify `git remote -v`, `git rev-parse --show-toplevel`, `git rev-parse HEAD`, `git status --short --branch` in the actual workspace (if shell access is allowed). Do not alter the working tree.
2. Obtain the complete remote branch namespace via a GitHub API branch listing with pagination or `git ls-remote --heads origin`. The latter gives remote refs and SHAs, **not** commit dates or source histories. An API page is usually alphabetical, not most-recent-first. If the scope is huge, count branch heads and prioritize promising families before reading their histories; never declare only the first page exhaustive.
3. Retrieve branch-specific commit history and committer timestamps for a bounded shortlist; include the actual multi-agent handoff, integration, experiment and accepted-lock branches. Use project reports to discover additional agent-owned refs.
4. Inspect the HEAD tree, last commits that changed C++ source (`src/`, `include/`), CMake/build configuration, network/weights and validation scripts; examine relevant diffs and blob SHAs. Report-only commits leave the source unchanged even if their branch HEAD is newer.
5. If two branch heads have the same source hashes, group them as a shared engine snapshot but preserve their different test reports and unrelated working files.
6. Read applicable `AGENTS.md`/`CLAUDE.md` and current branch-specific status, handoff, completed tests, pending jobs, failures and promotions. Do not assume all agents push to one branch.
7. Check active PRs and issue discussion for review decisions; treat comments as claims until matched to logs and exact code. Track whether tests were run on the source under evaluation.

## Low-risk command examples

Use only if shell access to the repository exists and network access is approved. These examples do not create commits or push code:

```sh
git status --short --branch
git rev-parse HEAD
git remote -v
git ls-remote --heads origin
# After obtaining an exact *locally available* commit:
git show --no-patch --format=fuller <full-sha>
git diff --stat <base-sha> <candidate-sha> -- forge-combo29/src forge-combo29/include
```

For a GitHub read client, use branch-aware commit history and the contents/tree endpoints; pagination and ref encoding differ by client. Do not rely on `search_commits(query="")` to retrieve the newest commits on all branches; some clients search only the default branch. Use the newest verified remote state, not the state from this skill's packaging date.

## Common mistakes

- Branch name contains a recent date but tip commit is old.
- Latest commit is a status/claim file, while `search.cpp` last changed days earlier.
- `main` is months behind worker branches.
- Two agents' branches have the same source blobs but different reports and proposed patches.
- An experimental branch claims an Elo gain using different time controls, opponents, books, nets or source builds.
- An upstream candidate is newer but fails established correctness gates.
- Locally modified files exist and the remote SHA alone is not the entire input snapshot.

Make each of these visible, then defer promotion until accepted evidence exists.
