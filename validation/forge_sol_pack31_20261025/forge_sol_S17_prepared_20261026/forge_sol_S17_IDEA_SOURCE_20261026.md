# S17 idea sources — 2026-10-26

Idea sources only: the user-supplied S17 specification and `06_jobD/holdout/build_forge_holdout_gamesplit_reference.py` in the 14:35 handoff. The reference was read for the goal and assumptions, not executed or copied. The new SHA256 group ranking, configuration, SQLite selection, text export and shard manifest are independently written here; no other engine code, tables or tuned values are used.

Existing implementation reused as an explicit dependency: S16 filter v2 SHA256 `5dd0c009566bc5a8c8e06300a8541c5d130d458ca75266a432d1477d1d156332`, which imports the original Job D reader/writer SHA256 `6ccf78c864c44155cea22044fe05d0584bec5241acdc5ebb2b71e23886007ab3`. Their original filenames and bytes are retained. S16's provenance checks and chronology across source boundaries are reused, rather than copying the old reference's per-file group reset or guessing authentic IDs.
