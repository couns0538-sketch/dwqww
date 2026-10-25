# User clarification: authoritative AUTOLOCK checklist and CAP-LATE — 2026-10-25

The text below is the user's supplied clarification. Abbreviated hash references are prefixes, not measured full hashes. This supersedes the earlier derived S47 checklist. The currently verified input archive is the 14:35 snapshot; the cited 16:15 prompt and exact referenced file must be checked separately rather than assumed present.

## Verbatim clarification

CAP-LATE rule: it's already in his bundle. The rule text is in files/10_cr/CR_autopromote_RHQ1.md (the CAP-LATE Z and Z-1/Z-2 parts). The 16:15 prompt also has it in two places: the "CAP-LATE vote Z 8/8" line near the top, and S46 fixture (v).   R first-AUTOLOCK checklist (11 points), copied word for word from files/10_cr/CR_autopromote_RHQ1.md, lines 124–146. It's S47's spec.
What CR must check when the first real AUTOLOCK_<n> appears:
1. The live autopromote.ps1 sha256 on the PC is F41CF92F… (or a CR-reviewed successor), and NO_AUTOPROMOTE was absent at the time.
2. The winner's confirm and parent are not VOID: there is no VOID.txt, and RESULT.md has no **VOID**. The ENGINE_OPTIONS_CHECK.txt final line is a PASS. (HIGH-1)
3. The race decision in README/LOCK.json race:
  - If G104c is H1, the winner must be gate104_e48f006, and G120 must be listed as PARKED-E32 (RH-Q1) with a REWORK_LIST entry and no *_rebase_vs_AL* gate for G120.
  - If G104c is H0 or capped, the winner is G120, and G104 is in REWORK_LIST with no re-gate.
  - If the cap expired, the winner is G120, G104 has a gate104_e48f006_rebase_vs_AL1 with a fresh srand and ag_rebase_exempt24, and the crew is alerted (INFO).
4. The AUTOLOCK dir is new (locks\AUTOLOCK_<n>_<tag>) with no orphan lower-n dir.
  - The exe sha256 equals the RUN_INFO candidate sha of both the parent and the confirm.
  - LOCK.json parent.tag=h256_e12, and kind is net only if the Tree-Diff log line shows exactly src\nnue_weights.inc.
  - The net md5 is in nnue_weights.inc.md5. For e48f006 it must be 0FAE54A4C0C437432DDB5DA85512B5F4, with pins/PINS.md listing 3AECB403… and 5A4ED675… as "attached", not applied.
5. The new lock's checks:
  - PERFT.txt: perft5 4865609, kiwipete5 193690690, FMA 0.
  - BENCH_REF.txt: two identical runs, equal to the gate's prebench.cand_off.
  - The nps ratio only warns.
6. h256_e12 is unchanged: e3df99cd exe and sources hashes are unchanged (attributes only, read-only). The pointer backup CURRENT_LOCK.json.bak_pre_<ltag>_* exists, and AUTOLOCK_STEPS.log has CREATE then POINTER lines with matching hashes.
7. State is consistent: st.promotes[-1].tag equals the pointer tag, seen.<gate> is PROMOTED, and datagen.pending is set. Also, the promoted chain is NOT in COMBINE_LIST (that would point to MED-4).
8. Rebuilt net gates: each has a manifest notes "REBUILT on …" line with a fresh srand, the base_override of the new lock, and ag_prev stored. Search/option gates are labelled "vs h256_e12". No started gate was edited (compare against the manifest backup forge_gates.json.bak_rebuild_<n>_*).
9. No chain with a double H1 shows INELIGIBLE in autopromote_state.json seen because of "no FORGE_RESULTS.csv row" or "RUN_INFO.json missing" (HIGH-2). If one does, clear it by hand with a crew-visible note.
10. The datagen switch happened only at a file boundary, the nps ratio was within 10 %, and NNUE training (trainer) was untouched.
11. CR then writes autonomy\CR_PASS_AUTOLOCK_<n>.txt, or a FAIL with reasons. There can be at most 2 chained AUTO-LOCKs without one.
Later additions:
- autopromote_state.json inflight must be null after the promote, and ALERTS.md must have no inflight_* lines.
- On a cap promote of e32: check that the queued gate104_e48f006_rebase_vs_AL1 has ag_rebase_exempt24=True, a fresh srand and conc 5, and is HELD until G104c is H1 (once Z-2 is in). Its later promote must log kind=net against AUTOLOCK_1 (Z-1).
- Any RH-Q1 FALLBACK promote of e32 needs a crew-visible note. "Note: the live autopromote.ps1 is now 896663B0 (Zfix VOID-HOLD), which replaced F41CF92F. Code Review checked and passed it, so it counts as the CR-reviewed successor in point 1."
