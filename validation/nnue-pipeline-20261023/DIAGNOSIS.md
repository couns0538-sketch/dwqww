# Initial diagnosis

The source attachment matches88 tracked files at1ab50b2d. The current engine uses a residual128 network. The supplied Python tools identify a standalone256 model and export `FORGE_NNUE_RESIDUAL0`; their loss does not include HCE. This is a demonstrated contract mismatch when those defaults are used for Forge6.4.24, not proof that the shipped network is useless.

The existing C++ residual trainer uses the correct HCE logit offset, but reads whitespace `FEN resultWhite scoreWhite`. The supplied data is `FEN | scoreSTM | resultWhite`. Direct ingestion fails; a delimiter-only conversion also flips Black scores incorrectly. Its arbitrary `--k` can additionally disagree with the runtime's fixed2.25 scaling, and first-epoch best selection does not establish an improvement over HCE.

The Python split hashes individual positions. It prevents exact-position overlap but allows fragments of a game on both sides. All13,500,000 supplied rows are well formed, but no game IDs, best moves, source-engine identity or provenance sidecars accompany them. Fresh provenance-tagged validation games and exact-position exclusion will be used; legacy rows remain training-only. Counter decreases are not authenticated game IDs.

The generator already filters checks, captures, promotions, mate/bounded labels and large scores. It discards the best move and game identity. The new data path must retain both, reject checking best moves too, and explicitly disable OwnBook. Missing best moves in old data require a conservative filter or actual rescoring.

The initial diagnosis preceded held-out measurements (now recorded below). Historical repository results used different objectives and contradict assuming that the shipped residual adds nothing. The new comparison will use one identical frozen held-out set and metric. No Elo conclusion is available.

See the engine/training audit reports and input-inspection receipts beside this file for exact source references and observed hashes.

## First measured baseline

On the frozen4149 positions from56 authentic fresh validation games, pure-teacher probability MSE is0.006660536215902123 for HCE and0.006082049055657535 for shipped HCE+NNUE (8.685% lower). The residual term alone is0.07561013420188484; it is a correction, not a complete evaluation. Thus the claim that this shipped net adds nothing is not supported on this set. The teacher is frozen Forge search, not an independent strength oracle. Baseline-only run and input-integrity verification completed with exit0. No Elo conclusion follows.

## Controlled small-data pilot diagnosis

Both20-epoch pilots overfit the same14895 clean training positions/4149 held-out positions. Constant pure-teacher train MSE for zero initialization falls0.0061279211→0.0024297396 while validation rises0.0066605362→0.0076272026. Warm initialization train MSE falls0.0055287028→0.0015423693 while validation rises0.0060820491→0.0072062214. These comparisons use the same pure-teacher metric at every epoch; they are not the online training objective whose result blend changes. The zero run selects epoch1; warm selects its unchanged initial shipped net. Neither pilot is a replacement. All42 checkpoints were evaluated on all14895 training rows, and all exports remain preserved.

The unchanged C++ loader API round-trips the Python residual float32 export byte-exactly and reproduces all98689 quantized parameters. Its CLI does not export for `--epochs0`; this existing limitation was preserved rather than modifying the old trainer. The original mock-UCI CLI integration also passes using its supplied test-only PID-namespace adapter. Actual256-game generation and native inference tests are separate production evidence.
