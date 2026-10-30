# Forge native binpack adapter, 2026-10-30

Original wrapper code. IDEA_SOURCE: Forge full-FEN transport requirement and the external GPL-3.0 binpack API/format in official-stockfish/nnue-pytorch commit ec2ead9feeb5677b828536fc53000d1379a1d207. No engine search/evaluation code is modified or imported.

**QA licence correction:** this is **GPL-3.0 external tooling**, not MIT-only.
`nodchip.h:46-47` explicitly contains modified nodchip/Stockfish GPLv3 code;
`binpack.h` includes it and `chess.h` cites Cfish. Leading MIT permission notices
do not override embedded third-party provenance. Preserve all notices. The
manifest pins five dependency files, but does not certify a MIT-only closure.

Default conversion uses bulletformat plus its sidecar and needs none of this
tooling. Binpack is optional/OFF until `--binpack-tool` and `--accept-gpl3` are explicitly provided.
Conversion and verification check the executable path before invoking it.
Only the original wrapper/tests stay here; fetch headers and build the executable
**outside every repository**. The fetcher requires `--accept-gpl3` and rejects
Git directories. Historical raw logs are retained and their MIT-only descriptions
are superseded by this correction, not silently edited.

```bash
python3 tools/data2/fetch_binpack_dependency.py --accept-gpl3 --out /tmp/forge-binpack-gpl3-20261030
c++ -std=c++20 -O2 -Wall -Wextra -I/tmp/forge-binpack-gpl3-20261030 tools/data2/forge_binpack_adapter.cpp -o /tmp/forge-binpack-adapter-20261030
FORGE_BINPACK_ADAPTER=/tmp/forge-binpack-adapter-20261030 python3 tests/data2/test_binpack_adapter.py -v
/tmp/forge-binpack-adapter-20261030 encode input_with_move.txt new_output.binpack
/tmp/forge-binpack-adapter-20261030 decode new_output.binpack > new_roundtrip.txt
```

Encoding input is `FEN | STM score_cp | White result | legal UCI move`. The fourth field can be omitted ONLY with `--allow-transport-move`; that explicit mode chooses a deterministic legal transport move, reports the fallback count, and **does not assert a searched best move, quiet root, or training readiness**. It is appropriate to the 1M format-only test. For searched filtering, pass the actual native probe's legal best move.

Score remains STM-relative; White W/D/L is converted to signed STM result for binpack and inverted on decode. Every record is packed/unpacked before write, and its full canonical six-field FEN, score, result and move must match. Inert EP targets are restored after the upstream parser's EP normalization so castling and the original EP target survive. Clocks must be representable: halfmove0..255 and packed ply1..16383 (fullmove up to8192, final bound depends on STM). Larger values reject cleanly; none are clamped. Original source lines use canonical FEN and result spellings; decoder emits White result as0.0/0.5/1.0.

Output uses standard `BINP` chunks of independent32-byte packed entries plus zero16-bit continuation count. This costs34bytes/row plus8bytes/chunk. The external GPL-3.0 reader reads each record; the adapter decoder intentionally refuses continuation-compressed chunks from unrelated producers. It preflights chunk lengths, counts and structural piece constraints before invoking that reader. It is a narrowly scoped decoder for its own immutable, hash-verified output, **not a general fuzz-hardened arbitrary-binpack reader**. Empty output is supported. Encoding reserves a NEW output exclusively; on error an unsealed partial is preserved, never overwritten/deleted.

## Recorded verification

`evidence/tests.stderr`:13/13unit tests PASS. `refetch.stdout`: exact five-file dependency re-fetch PASS. `build3.stderr`: no compiler warnings.

`evidence/roundtrip_1m.json`: first1,000,000 real shard003 rows encoded and decoded through the external GPL-3.0 native binpack loader; exact input/output text bytes matched;0mismatches;216,652rows retained castling rights and35,547retained EP targets. All1M used explicitly labelled transport-move fallback, with no filter or training claim. The1M binpack is34,000,264bytes, SHA256 db200a129194456ffbdc101e2154a5d5fd920c175fea12b69e878c38a28c9396. Original/decoded1M text SHA256 f8fb8e78cfc643bbc3a79f0384aafc848bb679e01a9e5b71ca97fd91966766be. Wall8.263088s, childrenCPU8.160987s; format verification only, not a performance claim. This native reader proof does not establish a GPU trainer run or a whole training epoch.
