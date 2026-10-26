# S09 converted-eight-head native qualification, 2026-10-26

This uses the unchanged original CR-reviewed eight-head dependency
`fc_buckets8_h256e12.patch` SHA256
`ed28132d48b75496732f0ecf25753ad869787c84a4939aaf004b3de8580a9704`.
The unchanged Sol converter SHA256
`08270b7ec29d467928585fd7433b2588896d41b93fe24cda838006498630bb7e`
uses its original include parser. There is no new FEN parser, network training,
engine idea, accumulator narrowing or tuned constant here.

Only nnue.cpp is compiled again, selecting a new eight-identical-head include
through its reviewed literal FORGE_NNUE_WEIGHTS_FILE hook. The same public header
and six other translation units/objects are reused from the closed default LP
Release build. Each reused object's hash is checked against the actual original
archive member, and every source/header/compile-flag binding is preserved.
A new deterministic archive links the unchanged original parity and snapshot
drivers and the already qualified stored-head contract driver.

This helper-only build passed the actual stored-head8 contract and scoped FMA0.
It is not a new complete engine build, a full Std run, native10k parity, a speed
result, or a playing-strength result. Those scopes stay separate. Original LP
source, original net, all seven original objects and all sixteen parent artifact
entries remain unchanged. New binaries, include, objects and archive are retained
in the separately identified temporary native build, with exact hashes and raw
compiler/test evidence. The branch owner performs publication.
