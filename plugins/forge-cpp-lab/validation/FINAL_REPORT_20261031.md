# Forge C++ Lab v1.0.0 validation and continuation

Created on `astra-cpp-chess-plugin-20261031`, based on preserved converter checkpoint `ae223de098c166bc639f484c501cef4336d8e247`. Plugin Creator tools were absent from the callable catalog; the pinned official OpenAI Creator skill and scaffold were retrieved and used instead. Its provenance is recorded in `plugin_creator_source.json`.

Implemented: portable + Codex compatibility manifests; an AVAILABLE repo marketplace entry; one distinct C++ chess-engine skill with debugging, TT/SMP, NNUE/performance, research and qualification references; read-only evidence checker; complete usage/install documentation; plugin-scoped MIT license and IDEA_SOURCE. Existing engine skills are reused by name, not duplicated. No engine source or accepted branch changed.

| Check | Result |
|---|---|
| Helper unit/CLI regressions | PASS, 15 tests; original failing-before logs retained |
| Optimized Python (-O) regressions | PASS, 15 tests |
| Official portable JSON schema | PASS; schema hash/provenance recorded |
| Compatibility/catalog/path/frontmatter checks | PASS; package-validation.log |
| Independent source/package review | No concrete blocker found |
| Bounded guided skill application | Essential checks retrieved; three wording defects corrected |
| Demonstrated improvement over baseline reviewer | UNVERIFIED; baseline already found key defects |
| Codex client installation/activation | UNVERIFIED; not installed |
| Native Windows/Forge/GPU/Elo | Not performed or claimed for a plugin-only task |

Run tests from the marketplace root with `python -W error::ResourceWarning -m unittest discover -s plugins/forge-cpp-lab/tests -v`. Schema validation requires jsonschema only for development; the installed helper has no third-party dependencies. No service or automatically executed hook is included.

To resume: read README and current source; preserve this branch. Installation is a separate client action through Codex plugin management. The local CLI command names were checked; no personal configuration was changed. After installation start a fresh session, verify skill discovery and exercise a real bounded engine task before making any long-term efficacy claim. Extend the existing plugin when a reproducible gap appears.

IDEA_SOURCE: user request, official Plugin Creator and existing Forge skills/QA history. No copied engine code or tuned constants.
