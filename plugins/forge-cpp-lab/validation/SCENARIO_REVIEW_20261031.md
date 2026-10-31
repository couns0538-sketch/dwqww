# Bounded skill application review

One baseline and one guided fresh-context subagent reviewed the same scenario before/after the skill existed. These are qualitative retrieval/application checks, not a statistical model benchmark. The baseline already detected the principal problems. **No causal skill efficacy or engine-strength gain is claimed.**

Scenario: a candidate changes same-depth nodes by 0.3%, reports 3% speed, Linux ASan/UBSan clean and standalone TT TSan clean but full-engine TSan unavailable; Windows Ryzen target; ordinary TT payload behind atomic sequence counter; qsearch early eval/TT return before legal-move fallback; int16 NNUE observed safe over 20k positions; 40-game W23/D10/L7 screen; accepted branch newer than report; preserve OFF identity and publish a candidate.

Baseline reviewer `/root/cpp_plugin_baseline` had no tool/skill access. It rejected acceptance, required recovery of the newer baseline, identified the ordinary-payload C++ data race, qsearch terminal risk and lack of NNUE bounds proof, rejected tiny-match Elo and cross-platform performance claims, and allowed explicitly experimental publication. This already meets the central correctness rubric. It did not establish any new experimental result.

Guided reviewer `/root/plugin_guided_review` read this skill and relevant references. It identified the same blockers, explicitly separated each platform/harness scope, preserved candidate OFF checks, required every-net/transient NNUE bounds, proposed primary-source verification and paired equal-time qualification, and kept full-engine TSan and Windows claims UNVERIFIED.

The guided reviewer additionally found three wording defects, now corrected:
1. Freeze each arm's own source revision; do not imply candidate and baseline source must be identical.
2. Bug fixes need a failing reproducer; optimization/research needs baseline measurements and falsifiable criteria, rather than an invented failing functional test.
3. A loose arithmetic bound exceeding int16 does not itself prove reachable overflow. Tighten the bound or use wider arithmetic before acceptance.

Independent reviewer `/root/plugin_package_review` read helper code/tests, manifests and technical references, ran 15 tests with ResourceWarning as error, and found no concrete blocker. It verified no engine execution/writes/network in the helper and limited MIT scope. Its initial review preceded README/evidence-format completion; a final targeted read follows separately.

Skill activation in the Codex app, native Windows behavior, long-term compliance and resulting engine gains remain UNVERIFIED. No installation was performed for these reviews.
