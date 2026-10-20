# Independent source and evidence audit

A second agent reviewed the source and then independently checked the saved
raw API outputs and frozen hashes without changing files, compiling, or
executing an engine.

No material implementation issue was found:

- Gain recurrence/backfold handles initial and recapture promotion material
  plus the next victim value correctly.
- Pin mask, LVA order, origin removal, ray updates, and terminal king-defense
  behavior match source16.
- The guard covers either side's later promoting recapture, removes consumed
  initial/EP origins, and preserves initial king/castle handling.
- Distinct consumed origins and the 64-entry bound prevent stack overrun.
- Target ghosts are suppressed. All helper calls use public getters inside the
  existing anonymous namespace; the Board class/header is unchanged.

The saved evidence reconciles:

- 326 rows: 324 legal and two initial-illegal controls.
- 314 non-guard rows are byte-identical, including both illegal controls.
- Twelve guard rows; exactly eight reference mismatch rows change and now
  match the independent oracle.
- All 324 legal scores, 6,480 fixed-threshold answers, and 30 adjacent answers
  pass.
- Source/helper/input/header frozen hashes match; removing helper and dispatch
  restores source16 exactly. Only Board.cpp.o differs between core members.

This is a bounded source/API result. LVA/lsb, optional stopping, and source16's
king-defense behavior remain. No speed, strength, full-suite, or integration
acceptance claim follows.
