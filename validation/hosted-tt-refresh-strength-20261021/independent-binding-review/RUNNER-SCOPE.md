# Proposed runner scope — static review

**CLEAR for source-only preparation; not READY or launch authorization.** No blocker found in this bounded runner/lifecycle scope. Reviewed 2026-10-21T02:44:43.005084+00:00.

The actual proposed runner differs from current canonical bytes in exactly one assignment and its adjacent comment: `CANDIDATE_BENCHMARK_NODES = None` becomes `292545`. Normalizing that AST constant produces the identical complete AST; the saved unified diff also matches the actual two files. All functions, including launch guards, process stop/cleanup, fault handling, and the independent outer affinity-restoration finally, remain unchanged. The other five execution Python files match the proposed code map byte for byte.

| Bound input | SHA-256 |
| --- | --- |
| Current disabled runner | `6da0a0d76f21c90b46fd320b81ac66f4a6cf7dd5e9f731a57e34c6ff65b2c105` |
| Proposed runner | `1a31e24185d228a67b497334e608376f13abd7f3e53e0fbe253c362efe477095` |
| Preparation checkpoint | `e6b190952a39f48a14d5f1713bf48b1f513110a9383446e374bae472f326c568` |
| 34-entry support seal | `abffd72ba568161b72f391eca9bf8d04baba9dbe005defe5349389be094359ae` |
| Current disabled workflow | `512fdf53e6649832290ee717563563995a2ea1674d0fa5367170addc679c231f` |
| Current package inventory | `54cb3685cea94e4e98daa70fa6b0f444b4dd4005194f9c3728a1c9627bf3ee0f` |

All 34 sealed preparation files authenticate. The current protocol is still unbound DRAFT, the workflow remains `on: []` with job condition `false`, and the exact package inventory currently verifies. The inventory excludes its own file and includes the workflow; its verification precedes affinity changes and child launches. A future scalar/metadata transition must recompute that inventory.

The binding builder excludes package files, its future final-output folder and final enabled-review records from the proof set to avoid hash cycles. Genuine root preparation/one-attempt records and the aggregate capture review are separately consumed; pending examples and an in-memory positive protocol fixture are not authority. The existing blocked attempt honestly records its then-missing three records; 2 remain absent at this review's read. The parent owns detailed native/schema/proof collection and conditional authorization review. Proposed READY metadata and a future enabled workflow require a separate closed final review before the sole root trigger.

No binder, proposal, helper, packet import, engine, build, test, Git or network operation ran in this review. Only standard-library reads, hashes, AST/diff comparisons and this new report write occurred. The saved 25 source-only controls were not rerun and are not a hosted result. No speed or Elo inference is made.
