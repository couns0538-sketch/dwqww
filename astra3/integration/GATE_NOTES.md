# A1 integration gate handoff — 2026-10-29

Status: WIP. No gate is run and no queued gate, lock, or live executable is changed.

The accepted integration input is b7c177222038e9332965a95ec53ea3b94e90dbc9. The isolated astra3-integration branch uses real no-ff merges in the supplied order. See REPORT.md for each tested source and its binary SHA256.

A candidate for replacing the executable of a queued R5A single must reproduce that gate's full five-depth ON vector from `opus_r5/r5a/gate_specs.json`, plus the fixed OFF vector312866/862329/3024920/12389307/34048354, startpos4865609, kiwipete193690690, and whole-executable FMA0. Qualification results are pending for the final head; until they pass, no executable migration is recommended. Windows qualification remains separate.

CorrMargins1/Scale100 uses343365/858019/2522546/12894582/22287047, as confirmed by the user. CorrMargins0/Scale100 keeps OFF pins. No threshold or queued ON meaning is changed.

Even after native identity passes, these identities are not Elo or speed evidence. QA/CR own adoption, Windows checks, installation and fresh gate seeds. Existing gates must not be rewritten in flight. No strength result transfers automatically to a combined bundle: CorrMargins and TtPruneV2 affect shared margins; CorrHistPlus and CorrHistV2 are exclusive; CorrExt and SingularV2 are exclusive. N1 is CorrHistPlus4 plus SingularV2 only; independent SmpV2 and TmSoftHardClamp survive preset changes and are not implied by N1.

For any later authorized strength gate proposal: one explicit option set, normalized SPRT[0,10], cap_games3000 as an integer, and empty srand/openings_start for QA assignment. Node-identical speed switches instead require NPS evidence and a[-10,0] non-regression proposal. No result is claimed here.

IDEA_SOURCE: Engine QA round-three contract, same-repository R5A gate specifications, and the user's CorrMargins clarification.
