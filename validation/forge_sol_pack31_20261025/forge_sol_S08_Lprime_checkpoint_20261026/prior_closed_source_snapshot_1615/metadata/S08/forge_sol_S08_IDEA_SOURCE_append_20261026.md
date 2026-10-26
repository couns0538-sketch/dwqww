

## S08 original profiling instrumentation (2026-10-26)

IDEA_SOURCE: the user S8 handoff, the actual Forge Worker/MovePicker/TT/evaluation
branches in this source tree, and the supplied profile_notes.md observations
about search/evaluation/TT/picker cost. General ideas are per-owner counters,
relaxed atomic addition, nested thread-local context scopes, and fixed-workload
measurement. The counter implementation and branch-placement map are original;
no other engine implementation was copied. Historical profiling timing numbers
are context only and are not reused as measured S08 frequencies or gains.
