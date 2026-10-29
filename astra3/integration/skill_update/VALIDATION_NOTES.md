# Proposed update to validate-chess-engine — 2026-10-29

Status: **PROPOSED ONLY — NOT INSTALLED.** This updates the existing skill; it is not a new overlapping skill.
Existing package: `c6/6ad5f7d7bfb4819190376efc04503df1/validate-chess-engine`.
The original provider resource and SHA256 are recorded in `original_source.json`.

The 256-word addition covers five integration checks: named option construction, preset ownership, applicable
OFF/ON pins, UCI advertisement/setter/echo consistency, and coordination of qualification freezes. Existing
frontmatter, skill identity, reference links, and all previous guidance are unchanged. The existing match and
Stockfish rules remain intact. `SKILL.md` is a proposed replacement for the existing package's main file;
its relative reference files remain supplied by that existing package and are not duplicated here.

## Validation actually performed

- Read the existing validation skill and `superpowers:writing-skills` guidance. Reused the existing skill.
- One available-tool metadata scan found no callable skill-creator or cloud skill-edit/update tool. No install,
  update or publication to the skill provider was attempted or claimed.
- Independent control: four synthetic integration handoffs with the existing skill. The agent correctly found
  all four broad risks. It did not explicitly require named construction or exact ON bench pins. These are
  omissions relative to the requested addition, not evidence that the agent accepted unsafe engine code.
- Independent fresh-context proposal test: five synthetic handoffs; each response applied the expected checks,
  including rejection of candidate-generated ON references and accurate attribution after a runner edit.
- These were focused instruction scenarios, not native tests, training evaluations or Elo evidence. They were
  not a five-repetition-per-variant behavioral study. The control already handled the broad risks, so no
  measured behavioral improvement or deployment readiness is claimed. This is a reviewable reference update.
- Eight static checks PASS: original hash, identical frontmatter, exactly one new section, unchanged reference
  links, exact unified diff, forward patch dry-run, unchanged skill name, and all five required contract fields.
  Original raw dry-run output and machine-readable checks are retained.

## Applying it later

A user or an authorized provider editor must apply this to the **existing** skill package. First compare the
current provider SKILL.md against original SHA256
`2c818fa3da5a9000f97e88f6ff61571bf86e8e92edb381b3b6a4d6ecfe449527`.
If it changed, reconcile the small new section with the newer version; do not overwrite newer skill work.
Retain the existing package identity and its reference files. Confirm the provider's read-back content and
availability after applying. The files in this proposal folder alone do not make a skill installed or discoverable.

IDEA_SOURCE: recurring Forge option-integration and source-freeze mistakes observed in the authorized work,
plus the existing validate-chess-engine and writing-skills workflows. Original instruction text; no other-engine code.
