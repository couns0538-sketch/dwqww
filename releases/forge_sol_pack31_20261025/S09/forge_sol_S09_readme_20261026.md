# Forge S09 review packet — 2026-10-26

Start with forge_sol_S09_job_report_20261026.md. The preSAN checkpoint is preserved
history. Source/native validation passes; this packet does not adopt a net or
claim speed, Windows qualification or Elo.

New patches: native_delta (contract/tools only), trainer, documentation_addendum.
fc_buckets8_h256e12.patch is the ORIGINAL supplied dependency, unchanged SHA256
ed28132d48b75496732f0ecf25753ad869787c84a4939aaf004b3de8580a9704.
The native preparer selects its exact reviewed core/header/test/helper payloads,
integrates original CMake declarations with unique anchors, omits its converted-
net asset, then applies the new delta. Do not treat the original complete patch
as literally applied to all differently labelled baseline trees.

Standalone source/export checks (Python3+NumPy, no Torch/GPU/engine):

    python -B forge_sol_S09_portable_tests_20261026.py

This ran15 unchanged assertions with original-workspace reads blocked, using the
local pinned original trainer dependency. The historical source_before JSON is
provenance; the portable runner deliberately binds the equivalent local bytes.
The two generic helper names make_heads_inc.py and qa_adam_dml.py are unchanged,
hash-pinned supplied dependencies required by the original imports.

Create a NEW eight-head include (source is never modified):

    python -B forge_sol_S09_buckets_20261026.py replicate INPUT.inc NEW_OUTPUT.inc
    python -B forge_sol_S09_buckets_20261026.py check NEW_OUTPUT.inc

New trainer CLI `--buckets 1` (default) or `--buckets 8`; f006 recipe defaults are documented with
observed/inherited settings separated. DirectML/GPU runtime remains unverified.
Training and net adoption require the owner's separate CR/crew process.

Evidence contains original logs, full CTest/JUnit/recipe/source and binary hashes,
raw CP gzip streams and primary lossless FEN/floatword data. Full ASAN disassembly
uses lossless gzip transport with raw hashes and independent decoder proof.
No compiled engine binary (.exe/ELF), ZIP, LICENSE, AGENTS or .agents file is in this packet.
Native cloud controllers/source checkpoints retain historical absolute paths;
the standalone converter and portable source/export test above are relocatable.
