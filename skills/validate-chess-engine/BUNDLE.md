# Proposed update to validate-chess-engine

Status: **PROPOSED; NOT INSTALLED** (2026-10-30). This is a repository copy for
review and later application to the existing skill, retaining its name. It is
not a second installed skill. The provider is read-only in this environment.

Source: `skill://user/6ad5f7d7bfb4819190376efc04503df1/validate-chess-engine/`.
`SKILL.md`, `references/correctness.md`, `references/matches.md` and
`references/result-record.md` were read from the provider. The correctness and
matches references retain their source text. The update adds training-data
discovery and the consolidated `references/training-data.md` guidance from
[`ASTRA_A1_SKILL_ADDENDUM.md`](../../docs/ASTRA_A1_SKILL_ADDENDUM.md).

The provider's referenced `scripts/check_match_counts.mjs` failed retrieval,
including a retry, and no local copy was found. It is **not included** or
reimplemented. The two relevant passages now explain that limitation and scope
the command to an existing installation which contains the script. Do not
replace an installed skill tree wholesale with this proposal: apply the changed
Markdown files while retaining any existing script. This bundle has no callable
script and no package dependencies.

The bounded baseline/with-guidance review is recorded in
[`review-scenarios.md`](review-scenarios.md). It checks retrieval on one technical
scenario; it does not establish general agent compliance, Windows execution,
complete private-holdout clearance or training strength. No provider change,
installation, engine run, training run or cleanup was performed for this bundle.
