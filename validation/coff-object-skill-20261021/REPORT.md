# Repo-local SIMD skill: archive and COFF comparison guidance

Extended the existing `.agents/skills/validating-chess-simd/SKILL.md`; no duplicate skill or global/cloud installation was created. Its original SIMD arithmetic, disassembly, parity, runtime and strength requirements remain a verbatim prefix. The writing-skills workflow used the two retained real auxiliary failures as baseline evidence; this is not a controlled causal test of skill effectiveness.

The new section requires original hashes and byte preservation, observed GNU/COFF long-name decoding, known ordinary AMD64 COFF layout, and raw identity reported separately. Timestamp-qualified identity is allowed only when lengths match and every byte outside the standard header timestamp offsets4..7 is identical. It does not permit ignoring sections, relocations, code/data, masking other fields, or rebuilding to obtain preferred hashes. Original failed parsers/assertions and unknown exit facts stay preserved.

The retained-data/static validator passed **27 checks**. All seven actual object pairs have different raw hashes. Six nonsearch pairs, including NNUE, differ only at timestamp offsets4 and5; the real search object differs in length by16 and in other bytes, so the timestamp-only rule rejects it. GNU long-name and malformed-offset controls, PE/bigobj layout controls, and an in-memory extra-byte mutation confirm the bounded distinction. Derived controls are data tests, not new engine results.

Frontmatter and the existing relative link validate. All11 consumed old proof/core files and74 frozen Windows22 source files retain their hashes. A fresh independent application is saved separately in this namespace. No engine, compiler, benchmark, network, Git operation or frozen experiment artifact was modified or executed. Repo-local availability means the existing skill file is present and readable; no global registration is claimed.

This limited object-structure evidence does not establish full semantic equivalence, arithmetic/search parity, speed or Elo. Those existing skill requirements remain necessary.
