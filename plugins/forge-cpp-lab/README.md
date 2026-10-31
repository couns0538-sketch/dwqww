# Forge C++ Lab

A skills-only plugin for C++ UCI chess-engine engineering: debug real defects, research useful ideas, implement isolated changes and distinguish correctness, speed and playing strength. The primary target is Forge; the guidance also applies to other C++ engines.

## What it adds

- A single **cpp-chess-engineering** skill, triggered by C++ engine development, bug investigation, NNUE/SIMD, SMP/TT, profiling and research requests.
- Focused references for C++ lifetime/undefined behavior, native sanitizer builds, chess state/search invariants, race-free TT access, NNUE bounds/parity, performance experiments and primary-source research.
- A Python **read-only evidence checker** that catches changed artifacts, malformed records and explicit bench-pin mismatches. It reports its limited scope and never claims Elo.

Existing resume, validator, research and evidence skills remain the owners of their workflows when installed. This plugin adds C++ depth without copying those packages. It can also operate with its bundled references when companion skills are unavailable. It discovers relevant connected tools at use time; no named connector is assumed installed.

No MCP service, external dependency, hook, automatic background job or credential is bundled. The helper needs Python 3.10+. Native build/debug tools remain the target environment's responsibility. A plugin cannot guarantee better code or a stronger engine; qualification is still required.

## Add it to Codex

This repository branch includes `.agents/plugins/marketplace.json` and `plugins/forge-cpp-lab/`. Keep that layout when using the downloadable bundle. With a compatible current Codex CLI:

```bash
codex plugin marketplace add /absolute/path/to/marketplace-root --json
codex plugin add forge-cpp-lab@forge-engine-tools --json
codex plugin list --available --json --marketplace forge-engine-tools
```

The first path is the checkout/extracted directory containing `.agents/` and `plugins/`, not the plugin folder itself. The command names were checked with Codex CLI 0.159.2. Run them only when you choose to install; creation and tests here do not modify your personal plugin installation. In Codex app, use the generated View link or plugin-management UI and start a new session after installation. Admin policy/client versions may limit custom plugins. This cloud workspace path is not automatically present on your local PC.

The root `plugin.json` uses the portable 1.0.0 schema. `.codex-plugin/plugin.json` provides the official Creator's Codex-compatible skill path and presentation metadata. Both identify version 1.0.0. Do not rename only one manifest or the plugin directory.

## Example requests

- “Use Forge C++ Lab to reproduce this SMP mate override and test the smallest repair.”
- “Research the highest-value improvement in this accepted revision; implement one bounded candidate.”
- “Audit this NNUE optimization for overflow, parity, races and exact OFF bench identity.”
- “Review these experiment records and tell me what is actually verified.”

Read [the skill](skills/cpp-chess-engineering/SKILL.md), [checker format](skills/cpp-chess-engineering/references/evidence-format.md), and [qualification rules](skills/cpp-chess-engineering/references/qualification.md). Pins and baselines are supplied per task, not frozen to an obsolete Forge version.

## Tests and scope

Run `python -W error::ResourceWarning -m unittest discover -s plugins/forge-cpp-lab/tests -v` from the marketplace root. Raw results and limited scenario review are in `validation/`. Manifest/schema validation is distinct from installation and actual client skill discovery; those states are recorded explicitly in the final validation report. No native Windows/engine/GPU qualification or Elo improvement is claimed by this package.

The new skill was compared on one scenario with a baseline reviewer. The baseline already found the principal issues; the guided test checks retrieval/application, not a measured improvement in model ability. Update this skill and its tests when recurring mistakes appear rather than creating overlapping copies.

License: MIT for this plugin's original files only. See [IDEA_SOURCE.md](IDEA_SOURCE.md) for source provenance and [LICENSE](LICENSE) for scope; the engine and external libraries retain their own licensing.
