# Initial diagnosis

The source attachment matches88 tracked files at1ab50b2d. The current engine uses a residual128 network. The supplied Python tools identify a standalone256 model and export `FORGE_NNUE_RESIDUAL0`; their loss does not include HCE. This is a demonstrated contract mismatch when those defaults are used for Forge6.4.24, not proof that the shipped network is useless.

The existing C++ residual trainer uses the correct HCE logit offset, but reads whitespace `FEN resultWhite scoreWhite`. The supplied data is `FEN | scoreSTM | resultWhite`. Direct ingestion fails; a delimiter-only conversion also flips Black scores incorrectly. Its arbitrary `--k` can additionally disagree with the runtime's fixed2.25 scaling, and first-epoch best selection does not establish an improvement over HCE.

The Python split hashes individual positions. It prevents exact-position overlap but allows fragments of a game on both sides. All13,500,000 supplied rows are well formed, but no game IDs, best moves, source-engine identity or provenance sidecars accompany them. Fresh provenance-tagged validation games and exact-position exclusion will be used; legacy rows remain training-only. Counter decreases are not authenticated game IDs.

The generator already filters checks, captures, promotions, mate/bounded labels and large scores. It discards the best move and game identity. The new data path must retain both, reject checking best moves too, and explicitly disable OwnBook. Missing best moves in old data require a conservative filter or actual rescoring.

The initial diagnosis preceded held-out measurements (now recorded below). Historical repository results used different objectives and contradict assuming that the shipped residual adds nothing. The new comparison will use one identical frozen held-out set and metric. No Elo conclusion is available.

See the engine/training audit reports and input-inspection receipts beside this file for exact source references and observed hashes.

## First measured baseline

On the frozen4149 positions from56 authentic fresh validation games, pure-teacher probability MSE is0.006660536215902123 for HCE and0.006082049055657535 for shipped HCE+NNUE (8.685% lower). The residual term alone is0.07561013420188484; it is a correction, not a complete evaluation. Thus the claim that this shipped net adds nothing is not supported on this set. The teacher is frozen Forge search, not an independent strength oracle. Baseline-only run and input-integrity verification completed with exit0. No Elo conclusion follows.
