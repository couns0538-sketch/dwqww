# Existing strength skill: bounded provenance application

Date: 2026-10-20. Reused the existing repository-local [validating-chess-strength skill](../../.agents/skills/validating-chess-strength/SKILL.md) and [scenarios](../../.agents/skills/validating-chess-strength/scenarios.md), including their source/build evidence, final-rehash, artifact-mode and deadline additions. Read the [phase2 closure](../hosted-correction-history-strength-20261020/PHASE2-CLOSURE.md). No duplicate skill was created.

This is a documentation application and metadata/link inspection. No engines, tests, compiler, Git commands or network commands ran. Only `application.md` and `application.json` were written; existing evidence files were preserved.

## Exact input identities

| Input | SHA-256 |
|---|---|
| `SKILL.md` | `a9a5ec3216206db28891a84e1e679e90f59c1303c0971f7fad99f9e4e38f9de8` |
| `scenarios.md` | `55e5565b59690a8d72faf0fc807f788bb21f117485f83f85721d07e12ae1ac21` |
| `PHASE2-CLOSURE.md` | `8c320f11775ecd172361cdd75f82df0e7be198b151c40d31e483623935d1f1b3` |

All three input hashes were rechecked before writing. The frontmatter name is `validating-chess-strength`, matching its directory. Its nonempty description states when to use the skill: “Use when evaluating chess-engine Elo or Stockfish claims, planning Fastchess paired matches or SPRT, encountering timeouts or incomplete pairs, or comparing fixed-node search quality with equal-clock strength.” Both metadata checks pass.

All five relative Markdown links in the three read documents exist. The closure has no relative Markdown links. Link existence does not validate target contents or operational readiness.

| Source | Original relative target | Resolved repository path | Result |
|---|---|---|---|
| `.agents/skills/validating-chess-strength/SKILL.md` | `../../../validation/clock-safety-9850x3d/run-quality-sprt.py` | `validation/clock-safety-9850x3d/run-quality-sprt.py` | exists |
| `.agents/skills/validating-chess-strength/SKILL.md` | `scenarios.md` | `.agents/skills/validating-chess-strength/scenarios.md` | exists |
| `.agents/skills/validating-chess-strength/scenarios.md` | `../../../validation/chess-bench-parser-repair-20261020/REPORT.md` | `validation/chess-bench-parser-repair-20261020/REPORT.md` | exists |
| `.agents/skills/validating-chess-strength/scenarios.md` | `../../../validation/hosted-correction-history-strength-20261020/PHASE2-CLOSURE.md` | `validation/hosted-correction-history-strength-20261020/PHASE2-CLOSURE.md` | exists |
| `.agents/skills/validating-chess-strength/scenarios.md` | `../../../validation/hosted-correction-history-strength-20261020/independent-review/FINAL-ENABLED-REVIEW.md` | `validation/hosted-correction-history-strength-20261020/independent-review/FINAL-ENABLED-REVIEW.md` | exists |

## Required applications

### Case 1: BLOCK

Declared source SHA and executable hash; required source archive, core, compiler and CTest records missing.

Readiness and acceptance; reject the source-to-binary authentication claim. A declaration and executable hash do not authenticate the build relationship. Mandatory evidence cannot be replaced by optional globs or byte-equivalence assertions.

Specific next action:

- Preserve the incomplete evidence and classify absent original records as missing; do not invent original statuses.
- Before readiness, supply the actual frozen Git source archive identity and complete source inventory; original compiler/configuration/flags/cache/compile commands; executable and core hashes matching actual runtime paths; original stage commands, streams and statuses; exact named baseline9/candidate10 CTest passes; Fastchess provenance; and completed outer-collector observations.
- Include every consumed proof and build-evidence file in frozen_inputs and the final rehash. If the original build cannot be authenticated, produce a distinct properly frozen build with its genuine records.

No future pass was observed.

### Case 2: REJECT

A correctness proof initially matches its pinned hash, then is modified or deleted before the final decision.

Final acceptance of the affected attempt. An initial match is insufficient. Deletion or mutation of a consumed proof fails the final freeze and invalidates acceptance even if other checks passed.

Specific next action:

- Retain initial verification plus the final missing/mismatched observation, attempted run records and all failure facts.
- Do not restore a file or recompute a hash merely to rescue the affected attempt. Investigate, bind legitimate proof hashes and all consumed evidence, and preregister a distinct future freeze with before-readiness checks and a final rehash.

No future pass was observed.

### Case 3: BLOCK

Historical local build47 has 72 byte/mode-identical inputs to frozen b590, while the protocol requires an actual b590 host build.

Actual b590 hosted build qualification; reject relabeling build47 as b590. Byte/mode equivalence supports only the stated historical equivalence. It does not turn a genuine build47 validation into the separately required b590 host build.

Retain historical47 under its genuine revision and original validation scope. The 72-file equivalence is reported in the supplied closure; it was not independently reaudited in this bounded application.

Specific next action:

- Keep the historical47 evidence and equivalence record without changing source labels.
- Build the actual frozen b590 revision on the intended host, preserve its source/build/collector evidence, and obtain the exact nine required named baseline CTest passes before claiming that gate passed.

No future pass was observed.

### Case 4: BLOCK

Collector copying drops the engine execute permission, and its internal deadline equals the outer step timeout.

Readiness launch and evidence-safe collector completion. A nonexecutable native artifact must be rejected before a probe. Equal inner and outer bounds leave no reserved cleanup/finalization interval; timeout can lose process and partial-evidence facts.

Specific next action:

- Preserve the failed copy/mode and any actual original process observations; do not reinterpret a later passing check as the original result.
- Make artifact copying preserve executable modes, then require executable access on every runtime artifact before readiness. Mode preservation can be checked with inert artifacts; no engine need be launched for that check.
- Freeze an internal work deadline below the outer step bound with bounded cleanup and evidence-finalization headroom; the supplied closure uses 450 seconds inside a 480-second build step, reserving 30 seconds.
- Retain pre-verdict and post-cleanup observations, cleanup actions/errors and final status/group state separately. Headroom cannot guarantee survival after infrastructure loss.

No future pass was observed.

## Evidence and claim boundaries

Missing original exit/group observations remain **unknown**. An offline parser replay that assumes exit zero does not reconstruct the original process status, clear its failed attempt or establish readiness.

The closure records a prepared, blocked phase2 package with unbound proof hashes and pending review/authorization gates. Its reported historical test passes and 72-file equivalence were read as historical evidence; none was independently rerun or reaudited here. This task did not inspect current protocol/workflow state or establish a later enabled state. A real future pass requires the actual frozen artifacts, recorded process outcomes, exact named tests and all final acceptance gates.

**No causal baseline comparison was performed. No skill-caused improvement was demonstrated. No Elo gain is claimed.** This application establishes no new strength, speed, NPS or clock-reliability result.

The supplied catalog has no available skill-creator capability; none was used or claimed. This reuses a project-local skill and makes no global installation claim.
