# Net fixtures are GENERATED, not committed (brief: no binaries in the tree).
#
# Two scripts build every .bin this folder needs:
#   scripts/make_v2_nets.py   v2zero, v2double      (from src/nnue_weights.inc)
#   scripts/make_v3_nets.py   v3a, v3b, v3a-corrupt, v3a-residual
#
# sha256 of the exact files every number in FINDINGS.md was measured with:
aeb1d7db2166d9119432885c5aef457a0b246cf65b4fe85f3ba3e773145c576d  v2double.bin
3de9497e398b2fba319e6eb78de9e30ea17f8dee0468973f609f3efaa7dfa7d7  v2zero.bin
e1fa8bc8d22ceab91f3e03e22804876906f4038c3c55213a8758e8e47d386a9c  v3a.bin
9d8abbb7672011e72e1ffa892d1449d572615c116d239c2e39f0fb214bccb7ad  v3b.bin
# derived faults (deliberately invalid) — the loader must refuse these:
032ec4553896f5c8e92946db82641d3c2924b1a069bc065b456ed2b9af5ddd89  v3a-corrupt.bin
50454edfad79a5d742df0b919bc06bf1857c19efb5c9b5fa4768ce7bb902f84a  v3a-residual.bin
#
# Reproduce:
#   python3 scripts/make_v2_nets.py && python3 scripts/make_v3_nets.py
#   sha256sum evidence/nets/*.bin
#
# The scripts write into evidence/nets/; that path is gitignored for *.bin only.
# Nothing in this folder is needed to read FINDINGS.md — every claim it makes is
# also in the JSON under evidence/.
