# IDEA_SOURCE - B1 bundle port (R13 P1 item 1)
Port: Opus R13, onto the lock tree d4f4312 (= src_al1s198_clean). All code is the crew's own code from this repo; no
code from other engines. What came from where (each verified by exact node counts, see README):
- HistRework (Astra A1, commit a8b63aae, opus-sol-A1): applied with `patch -p1 -F0` (written on the lock layout).
- CuckooRep board part (Opus C6, 2cb0babd): applied with `patch -p1 -F0`. Search part (147395c4 + 4d14f3cf, written on
  the O3 split layout): its wrappers copied unchanged (forge-bundle-int src/search/cuckoo.inc); R3's macro instances
  become one template parameter (search<true>/qsearch<true>); the call sites are the same 12 calls.
  Idea: upcoming-repetition detection with a cuckoo table, M. van Kervinck's public paper (see opus_round1/C6/IDEA_SOURCE.md).
- CorrHistPlus (Opus C2, e9307356, O3 layout): forge-bundle-int b7c17722 correction_plus.hpp + correction_plus.inc
  copied unchanged (incl. the R3 HistRework x CorrHistPlus combination); hooks re-placed in the lock's search.cpp.
  Idea: extra correction-history keys (continuation, minor-piece, non-pawn), public technique (Caissa / Stockfish ideas only).
- TtPruneV2 (Fable FB2-J3, 33e295b4): the forge-bundle-int b7c17722 version of its four rules, copied unchanged, with
  bundle-int's per-search snapshot (Worker::tt_prune_v2_). Ideas: public pruning ideas (BUNDLES.md IDEA_SOURCE).
- BundlePreset (forge-bundle-int b7c17722 uci.cpp/fb2.inc): OFF and B1 only (B2-B4 need CorrHistV2/LmrTableV2, not ported).
Status: UNPROVEN. No Elo or speed claim.
