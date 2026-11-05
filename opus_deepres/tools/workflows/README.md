# Workflow scripts of the deep-research job (one-line usage each)

- `deepres_tracks.js` - generic: `args = {root, python, tracks: [{key, title, minutes, verify_minutes, brief,
  extra_outputs?, reserved?, continue_note?, verify_skip?}]}`; one research worker per track, then one adversarial
  verifier per track (pipeline, no barrier). Run with the Workflow tool: `{scriptPath: <this file>, args: {...}}`.
  The briefs used on 2026-11-04 are in `tracks_core2.json` (T01, T02, T04, T05) and `tracks_extra.json`
  (T06, T07, T12).
- `deepres_extra.js` - the same shape, used for T06 / T07 / T12 (wf_dcef6221-e3c, launched 22:45).
- `deepres_two_chains_first_run.js` - the first run (wf_5cef37bf-0b9, launched 22:39): two chains of two tracks,
  2 agents at a time; stopped at 22:47 when the owner allowed up to 12 agents, replaced by `deepres_tracks.js`
  (wf_b823f43e-496, launched 22:48).
Every worker reads `../../WORKER_RULES.md` and `../../cards/TEMPLATE.md` first; workers write only their own
`cards/T<nn>/` and `notes/T<nn>/`; the coordinator commits.
