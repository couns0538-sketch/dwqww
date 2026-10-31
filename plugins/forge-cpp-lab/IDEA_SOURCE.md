# Idea sources and scope

Original plugin instructions and Python helper, written for the user's Forge development workflow. Ideas: existing `chess-engine-tool-router`, `validate-chess-engine`, `native-experiment-integrity`, `preserve-chess-evidence`; recurrent Forge QA failures involving TT ownership, NNUE width, Windows file/launch semantics, stale baselines, misleading bench and Elo conclusions, retained evidence and storage budgets.

Plugin layout/scaffolding: official OpenAI Plugin Creator at `openai/plugins` commit `0722921d5542fc593105c27bd52630babd8b8c2a`, https://github.com/openai/plugins/tree/0722921d5542fc593105c27bd52630babd8b8c2a/.agents/skills/plugin-creator ; current portable format https://developers.openai.com/plugins/build/plugins and https://agent-plugins.org/schemas/1.0.0/plugin.schema.json . The scaffold tool was executed externally, not bundled.

Skill-writing/testing methods: available `superpowers:writing-skills`, `superpowers:test-driven-development`, and `superpowers:brainstorming`. Existing authorization for autonomous skill creation took precedence over additional design confirmation. The bounded baseline reviewer already detected the important bugs; no causal behavioral improvement is claimed.

C++/tool research entry points are in `references/research.md`. They are leads for future version-specific verification, not a claim of supporting an unperformed experiment. No other engine implementation or tuned constants are copied. No optional external source library, MCP server, hook or connector is bundled.

The MIT license applies only to this plugin subtree's original files. It does not license the parent Forge engine, user data, third-party tools or externally retrieved documents. Schema/source hashes and URLs are recorded as provenance only.
