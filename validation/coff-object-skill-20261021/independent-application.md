# Independent actual-archive skill application

Raw identity fails for both archives and all seven object pairs. Six object pairs, including NNUE, satisfy **timestamp-qualified identity only**; the search object does not. No result establishes raw NNUE bit-exactness, full semantic equivalence, speed or Elo.

Both files decode as ordinary AR with two distinct, validated COFF linker-index metadata records, a COFF **NUL-terminated** long-name table (trailing LF padding), and seven uniquely named objects. Long-name references `/0` and `/17` resolve at bounded entry starts. The two `/` linker records are valid metadata, not duplicate object members. Both indexes agree with actual object offsets and symbols. No external source inventory or build provenance is authenticated.

| Object | Bytes 6421 / 6422 | Actual layout | Comparison | Exact raw differences |
|---|---:|---|---|---|
| bitboard.cpp.obj | 7950 / 7950 | ordinary AMD64 COFF | timestamp-qualified only | [4, 5] |
| board.cpp.obj | 81821 / 81821 | ordinary AMD64 COFF | timestamp-qualified only | [4, 5] |
| book.cpp.obj | 90053 / 90053 | ordinary AMD64 COFF | timestamp-qualified only | [4, 5] |
| eval.cpp.obj | 35087 / 35087 | ordinary AMD64 COFF | timestamp-qualified only | [4, 5] |
| eval_params.cpp.obj | 12995 / 12995 | ordinary AMD64 COFF | timestamp-qualified only | [4, 5] |
| nnue.cpp.obj | 214973 / 214973 | ordinary AMD64 COFF | timestamp-qualified only | [4, 5] |
| search.cpp.obj | 118693 / 118709 | ordinary AMD64 COFF | nonaccepted | 73858 differing bytes + 16-byte candidate tail |

For the six timestamp-qualified pairs, every byte outside object header offsets 4–7 is identical, including section headers, code, data, symbols and relocations. All seven pairs were checked for a 20-byte ordinary AMD64 COFF header (`0x8664`), bounded valid section tables, and bounded symbol/string/relocation references; PE, bigobj and unknown layouts receive no timestamp qualification. Search differs at offsets outside that field and has unequal lengths: it remains nonaccepted. No bytes were masked or rewritten.

The JSON retains whole-archive and every member's raw SHA-256, lengths, format observations and exact difference offsets. Large exact offset sets use a documented lossless compressed bitset plus the unmatched tail interval. Original archives and all raw member bytes remain unchanged at their original paths.

Applied skill SHA-256: `71aeb4c8b254bda1812cc9efcca831cebefe1667050764b61cbda504327da2ab`. This same skill path was read twice because its object-member wording was clarified during the task. Each actual archive was read three times for independent decoding, comparison and final structural verification. No other task-content files were read; no parent report, postmortem or answer key was consulted.

This is a local static/documentation application. No engines, builds, compilers, benchmarks, Git, network, source changes or global installation occurred. Static structure supplements independent arithmetic/search parity and runtime evidence; speed needs controlled timings and Elo needs a separately frozen audited equal-clock match. Those checks were not performed here.
