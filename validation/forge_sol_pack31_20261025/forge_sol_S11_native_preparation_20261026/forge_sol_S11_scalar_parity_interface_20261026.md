# S11 scalar parity source preparation, 2026-10-26

No C++ compiler, engine, oracle or performance run was launched. All native
checks below remain UNVERIFIED. Existing S11 source/patch/oracle files are unchanged.

Import `forge_sol_S11_scalar_parity_20261026.py`; import has no subprocess effects.
The builder can use `verify_link_map(text, absolute_core_path, scalar_object=None)`
for the normal material oracle. Scalar callers pass the explicit scalar object;
the actual observed link argv is separately checked with
`verify_oracle_link_argv(argv, core, scalar)`.

`scalar_compile_argv(normal_nnue_compile_argv, new_scalar_object)` returns a new
command without modifying the input. `macro_probe_argv(that_command)` removes
only compile/output selectors and adds `-dM -E` so all actual NNUE source macros
are captured. `verify_macros(text, 'scalar'|'avx2')` and
`verify_disassembly(demangled_no_raw_instruction_bytes, 'scalar'|'avx2')` fail
closed if the requested path/width/arithmetic is not proven. Packed SSE fallback
is rejected. The driver itself is always normally compiled, including its FP
control header; `verify_oracle_compilation(receipt, 'baseline'|'candidate')`
checks the unchanged source hash and candidate-only actual-table marker.

After all source/build/artifact/link/ISA receipts are verified and a root grant
exists, `capture_arm(executable, sealed_corpus_fd, input_bytes=..., input_sha256=...,
positions=1000000, child_limit=4096, table_checks=0|650, out=existing_new_directory,
label='safe_label', seconds=finite_1_to_1800, stop=optional_callback)` runs one
arm. It reuses the frozen owned-subprocess/subreaper cleanup, records original
stderr and deterministic lossless gzip stdout, checks exact header/count/EOF,
source-pinned summary fields, normal rc0 and an empty owned process group. The
caller owns affinity, RSS/resource policy, full source/artifact freezes and the
finite total experiment deadline. Output captures must have new names.

Run arms sequentially: the same sealed input FD is rewound for each arm.
`compare_gzip(left, right, 1000000, 4096)` compares every decompressed byte;
require both baseline/candidate and candidate-AVX2/candidate-scalar equality.
Expected full size is 2,068,000,036 bytes per arm. All twelve actual summary
fields and make/unmake/null coverage must pass. These are correctness results,
not NPS or playing-strength evidence. Reuse the existing S09 sealed corpus helper;
no extra corpus or FEN parser is introduced here.

Nine source-only Python test methods passed. Synthetic fixtures cover link
selection, scalar macros, SSE/AVX512/FMA rejection, format and FP header, actual
summary semantics, exact-byte comparison/EOF and Linux memfd sealing. The first
run exposed omitted Python fcntl constant names; the old source and failing log
are preserved. The corrected fallback uses the same Linux UAPI values as the
existing S09 sealer. These fixtures never count as native engine positions.
