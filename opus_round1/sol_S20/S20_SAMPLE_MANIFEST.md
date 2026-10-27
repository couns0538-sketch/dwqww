# S20 1M rescored sample — manifest (the sample is 63.5 MB, over the spec's 50 MB limit, so it is not committed)

| file (on the PC) | bytes | sha256 | content |
|---|---|---|---|
| `F:\opus_scratch\rescore_d8\full\rescored.txt` | 63,544,800 | `9b93882da92a0c39a13e3804bcbe83daa037b5d75edeec89536f300a0445563f` | 1,000,000 lines `FEN \| stm_cp \| white_result`, depth-8 lock re-search scores (STM cp; mates = ±3000, cp clipped to ±3000) |
| `F:\opus_scratch\rescore_d8\input\selfplay_1m.txt` | 63,544,649 | `fe1501377c3c72f7525023f5d79b0d8c2a1deb7c1988e44ce1ef403fc8e3c9aa` (md5 `650d401f…`) | the input: first 1,000,000 lines of an 11,700-game lock self-play run (5000 nodes/move labels) |
| `F:\opus_scratch\rescore_d8\full_loadcheck\data\s20_full_d8.pos` | 35,000,016 | `4e6ef58305372d2ed084d42a7941f7a7a203821dbf4b596c22f13346153fdde2` | FPOS v1 of the sample (fen2bin) |
| `F:\opus_scratch\rescore_d8\full_loadcheck\data\s20_full_d8.hce` | 2,000,016 | `11c7dd82c6297336107fa52179ae10a8e1ff2ec264993683538bd90f409c6c1b` | FHCE v1 of the sample (hce_dump) |
| `F:\opus_scratch\rescore_d8\bin\forge_al1_rescore.exe` | 3,828,330 | `04016f51626e187e7c311b8d5f2c718e88e3c11eb5d6ecd3cd075e8fa00b1b82` | the rescoring engine: box-recipe build of the AL1 lock sources (`uci_check --full` ALL OK, FMA 0) |

The 20 chunk files `full\chunk_000NN.txt` (50,000 lines each) and their sha256 are listed in
`results/full_summary.json` (`per_chunk`). The joined `rescored.txt` is their concatenation in order.

**Regenerate** (deterministic: `ucinewgame` before every position, Threads 1, Hash 16, depth 8; two runs of the
same input gave byte-identical output, `logs/step6_determinism.log`):
```
python -I -B opus_rescore.py --engine <forge_al1_rescore.exe> --in <selfplay_1m.txt> --out-dir <new dir> --depth 8
```
The output's sha256 must equal `9b93882d…` above.
