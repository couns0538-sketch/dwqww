#!/usr/bin/env python3
"""Fixture tests for forge_sol_S05_fmacheck_v4.py: synthetic disassembly listings (not machine code), fed with
--disassembly so the tests run on Windows and Linux. Sol's 27 v3 fixtures (forge_sol_S05_fmacheck_tests_20261025.py)
are kept with their expectations, except the one that S05-1 deliberately reverses: an FMA in a function outside
forge::nnue:: now FAILS the whole-.text scan. New tests cover the computed counts and the whole-binary count.
Optional: FORGE_S05_CHECKER=<path> runs the same tests against another checker file (used by the planted-bug run).
usage: python -B test_forge_sol_S05_fmacheck_v4.py [-v]"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
CHECKER = Path(os.environ.get('FORGE_S05_CHECKER', HERE / 'forge_sol_S05_fmacheck_v4.py'))
PUBLIC = 'forge::nnue::evaluate(forge::Board const&, forge::nnue::Accumulator const&)'
HELPER = 'forge::nnue::(anonymous namespace)::evaluate_values(float const*, float const*)'
VECTORS = ['vmaxps %ymm0,%ymm1,%ymm2', 'vminps %ymm0,%ymm1,%ymm2', 'vmulps %ymm0,%ymm1,%ymm2',
           'vaddps %ymm0,%ymm1,%ymm2', 'ret']


def body(name, insns, start=4096):
    return f'{start:016x} <{name}>:\n' + ''.join(f' {start + i * 8:x}:\t00\t{ins}\n' for i, ins in enumerate(insns))


def section(name):
    return f'\nDisassembly of section {name}:\n\n'


class Checker(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='forge_s05_v4_')

    def tearDown(self):
        self.tmp.cleanup()

    def run_checker(self, assembly, *extra):
        path = Path(self.tmp.name) / 'listing.txt'
        path.write_text(assembly, encoding='utf-8')
        run = subprocess.run([sys.executable, '-B', str(CHECKER), '--disassembly', str(path), *extra],
                             capture_output=True, text=True, timeout=60)
        lines = run.stdout.strip().splitlines()
        data = json.loads(lines[-1]) if lines and lines[-1].startswith('{') else None
        return run, data

    def ok(self, assembly):
        run, _ = self.run_checker(assembly)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def bad(self, assembly):
        run, _ = self.run_checker(assembly)
        self.assertNotEqual(run.returncode, 0, run.stdout + run.stderr)

    # ---- Sol's v3 fixtures (expectations unchanged) ----
    def test_pc_copied_zero_clamp_passes(self):
        self.ok(body(PUBLIC, ['vxorps %xmm5,%xmm5,%xmm5', 'vmovaps %ymm5,%ymm16', 'vmovaps %ymm5,%ymm2',
                              'vcmpgtps %ymm2,%ymm0,%k1', 'vmovaps %ymm0,%ymm1{%k1}{z}'] + VECTORS[1:]))

    def test_unaligned_copied_zero_clamp_passes(self):
        self.ok(body(PUBLIC, ['vxorps %xmm5,%xmm5,%xmm5', 'vmovups %ymm5,%ymm2', 'vcmpgtps %ymm2,%ymm0,%k1',
                              'vmovaps %ymm0,%ymm1{%k1}{z}'] + VECTORS[1:]))

    def test_unknown_copy_source_rejected(self):
        self.bad(body(PUBLIC, ['vxorps %xmm5,%xmm5,%xmm5', 'vmovaps %ymm7,%ymm2', 'vcmpgtps %ymm2,%ymm0,%k1',
                               'vmovaps %ymm0,%ymm1{%k1}{z}'] + VECTORS[1:]))

    def test_masked_zero_copy_rejected(self):
        self.bad(body(PUBLIC, ['vxorps %xmm5,%xmm5,%xmm5', 'vmovaps %ymm5,%ymm2{%k2}', 'vcmpgtps %ymm2,%ymm0,%k1',
                               'vmovaps %ymm0,%ymm1{%k1}{z}'] + VECTORS[1:]))

    def test_memory_zero_copy_rejected(self):
        self.bad(body(PUBLIC, ['vxorps %xmm5,%xmm5,%xmm5', 'vmovaps (%rax),%ymm2', 'vcmpgtps %ymm2,%ymm0,%k1',
                               'vmovaps %ymm0,%ymm1{%k1}{z}'] + VECTORS[1:]))

    def test_xmm_copy_does_not_prove_full_ymm_rejected(self):
        self.bad(body(PUBLIC, ['vxorps %xmm5,%xmm5,%xmm5', 'vmovaps %xmm5,%xmm2', 'vcmpgtps %ymm2,%ymm0,%k1',
                               'vmovaps %ymm0,%ymm1{%k1}{z}'] + VECTORS[1:]))

    def test_clobbered_copy_source_rejected(self):
        self.bad(body(PUBLIC, ['vxorps %xmm5,%xmm5,%xmm5', 'vmovaps %ymm7,%ymm5', 'vmovaps %ymm5,%ymm2',
                               'vcmpgtps %ymm2,%ymm0,%k1', 'vmovaps %ymm0,%ymm1{%k1}{z}'] + VECTORS[1:]))

    def test_clobbered_copy_destination_rejected(self):
        self.bad(body(PUBLIC, ['vxorps %xmm5,%xmm5,%xmm5', 'vmovaps %ymm5,%ymm2', 'vmovaps %ymm7,%ymm2',
                               'vcmpgtps %ymm2,%ymm0,%k1', 'vmovaps %ymm0,%ymm1{%k1}{z}'] + VECTORS[1:]))

    def test_copy_before_call_rejected(self):
        self.bad(body(PUBLIC, ['vxorps %xmm5,%xmm5,%xmm5', 'vmovaps %ymm5,%ymm2', 'call 3000 <helper()>',
                               'vcmpgtps %ymm2,%ymm0,%k1', 'vmovaps %ymm0,%ymm1{%k1}{z}'] + VECTORS[1:]))

    def test_copy_before_branch_rejected(self):
        self.bad(body(PUBLIC, ['vxorps %xmm5,%xmm5,%xmm5', 'vmovaps %ymm5,%ymm2', 'jne 3000 <other()>',
                               'vcmpgtps %ymm2,%ymm0,%k1', 'vmovaps %ymm0,%ymm1{%k1}{z}'] + VECTORS[1:]))

    def test_public_float_output_passes(self):
        self.ok(body(PUBLIC, VECTORS))

    def test_outlined_float_output_passes(self):
        self.ok(body(PUBLIC, ['call 2000 <' + HELPER + '>', 'ret']) + body(HELPER, VECTORS, 8192))

    def test_outlined_fma_rejected(self):
        self.bad(body(PUBLIC, VECTORS) + body(HELPER, ['vfmadd213ps %ymm0,%ymm1,%ymm2', 'ret'], 8192))

    def test_public_fma_rejected(self):
        self.bad(body(PUBLIC, VECTORS + ['vfnmsub132ss %xmm0,%xmm1,%xmm2']))

    def test_other_nnue_fma_rejected(self):
        self.bad(body(PUBLIC, VECTORS) + body('forge::nnue::refresh(forge::Board const&, forge::nnue::Accumulator&)',
                                              ['vfmsub231pd %ymm0,%ymm1,%ymm2'], 8192))

    def test_symbol_name_is_not_instruction(self):
        self.ok(body(PUBLIC, VECTORS) + body('forge::nnue::vfmadd_name_only()', ['ret'], 8192))

    def test_missing_output_contract_rejected(self):
        self.bad(body(PUBLIC, ['ret']))

    def test_masked_clamp_passes(self):
        self.ok(body(PUBLIC, ['vxorps %ymm0,%ymm0,%ymm0', 'vcmpgtps %ymm0,%ymm1,%k1',
                              'vmovaps %ymm1,%ymm2{%k1}{z}'] + VECTORS[1:]))

    def test_wrong_mask_polarity_rejected(self):
        self.bad(body(PUBLIC, ['vxorps %ymm0,%ymm0,%ymm0', 'vcmpltps %ymm0,%ymm1,%k1',
                               'vmovaps %ymm1,%ymm2{%k1}{z}'] + VECTORS[1:]))

    def test_blend_nonzero_false_lanes_rejected(self):
        self.bad(body(PUBLIC, ['vxorps %ymm0,%ymm0,%ymm0', 'vcmpgtps %ymm0,%ymm1,%k1',
                               'vblendmps %ymm1,%ymm7,%ymm2{%k1}'] + VECTORS[1:]))

    def test_stale_compared_value_rejected(self):
        self.bad(body(PUBLIC, ['vxorps %ymm0,%ymm0,%ymm0', 'vcmpgtps %ymm0,%ymm1,%k1', 'vmovaps %ymm7,%ymm1',
                               'vmovaps %ymm1,%ymm2{%k1}{z}'] + VECTORS[1:]))

    def test_clobbered_zero_blend_rejected(self):
        self.bad(body(PUBLIC, ['vxorps %ymm0,%ymm0,%ymm0', 'vcmpgtps %ymm0,%ymm1,%k1',
                               'vmovaps %ymm7,%ymm0 # overwritten', 'vblendmps %ymm1,%ymm0,%ymm2{%k1}'] + VECTORS[1:]))

    def test_blend_proven_zero_false_lanes_passes(self):
        self.ok(body(PUBLIC, ['vxorps %ymm0,%ymm0,%ymm0', 'vcmpgtps %ymm0,%ymm1,%k1',
                              'vblendmps %ymm1,%ymm0,%ymm2{%k1}'] + VECTORS[1:]))

    def test_caller_clobbered_zero_before_compare_rejected(self):
        self.bad(body(PUBLIC, ['vxorps %ymm0,%ymm0,%ymm0', 'call 3000 <helper()>', 'vcmpgtps %ymm0,%ymm1,%k1',
                               'vmovaps %ymm1,%ymm2{%k1}{z}'] + VECTORS[1:]))

    def test_zmm_alias_zero_clobber_rejected(self):
        self.bad(body(PUBLIC, ['vxorps %ymm0,%ymm0,%ymm0', 'vmovaps %zmm7,%zmm0', 'vcmpgtps %ymm0,%ymm1,%k1',
                               'vmovaps %ymm1,%ymm2{%k1}{z}'] + VECTORS[1:]))

    def test_zero_reestablished_after_call_passes(self):
        self.ok(body(PUBLIC, ['call 3000 <helper()>', 'vxorps %ymm0,%ymm0,%ymm0', 'vcmpgtps %ymm0,%ymm1,%k1',
                              'vmovaps %ymm1,%ymm2{%k1}{z}'] + VECTORS[1:]))

    # ---- S05-1: reversed v3 expectation ----
    def test_unrelated_fma_is_now_counted_and_fails(self):
        # v3 (test_unrelated_fma_not_misclassified) PASSED this listing: it only scanned forge::nnue::.
        run, data = self.run_checker(body(PUBLIC, VECTORS) + body('unrelated_function()',
                                                                   ['vfmadd213ps %ymm0,%ymm1,%ymm2'], 8192))
        self.assertEqual(run.returncode, 1)
        self.assertEqual((data['fma_count'], data['fma_count_whole_binary'], data['fma_count_nnue_scoped']), (1, 1, 0))
        self.assertEqual(data['fused_listed'][0]['symbol'], 'unrelated_function()')
        self.assertIn('FMA_COUNT whole_text=1 whole_binary=1 nnue_scoped=0', run.stdout)

    # ---- S05-1: computed counts, whole-binary count ----
    def test_fma_count_is_computed_not_literal(self):
        listing = (section('.text') + body(PUBLIC, VECTORS) +
                   body('search_helper()', ['vfmadd231sd %xmm1,%xmm2,%xmm0', 'vfmsubadd132ps %ymm0,%ymm1,%ymm2',
                                            'vfnmadd213ss %xmm0,%xmm1,%xmm2'], 8192) +
                   body('forge::nnue::refresh(forge::Board const&)', ['vfmaddps %xmm0,%xmm1,%xmm2,%xmm3'], 12288))
        run, data = self.run_checker(listing)
        self.assertEqual(run.returncode, 1)
        self.assertEqual(data['fma_count'], 4)
        self.assertEqual(data['fma_count_nnue_scoped'], 1)
        self.assertEqual(data['status'], 'FAIL')
        self.assertEqual(len(data['fused_listed']), 4)

    def test_clean_listing_reports_computed_zero(self):
        listing = (section('.text') + body(PUBLIC, VECTORS) +
                   body('main', ['vmulsd %xmm1,%xmm2,%xmm0', 'vaddsd %xmm0,%xmm3,%xmm0', 'ret'], 8192))
        run, data = self.run_checker(listing)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual((data['fma_count'], data['fma_count_whole_binary']), (0, 0))
        self.assertEqual(data['instructions_scanned'], 8)
        self.assertEqual(data['instructions_by_section'], {'.text': 8})
        self.assertIn('FMA_COUNT whole_text=0 whole_binary=0 nnue_scoped=0 instructions=8', run.stdout)

    def test_whole_binary_counts_every_executable_section(self):
        listing = (section('.init') + body('_init', ['vfmadd132ps %ymm0,%ymm1,%ymm2', 'ret'], 256) +
                   section('.text') + body(PUBLIC, VECTORS) + section('.fini') + body('_fini', ['ret'], 65536))
        run, data = self.run_checker(listing)
        self.assertEqual(run.returncode, 1)
        self.assertEqual((data['fma_count_whole_text'], data['fma_count_whole_binary']), (0, 1))
        self.assertEqual(data['fma_by_section'], {'.fini': 0, '.init': 1, '.text': 0})

    def test_fma_only_counts_a_stripped_binary(self):
        listing = section('.text') + ''.join(f' {4096 + i * 4:x}:\t00\t{ins}\n' for i, ins in
                                             enumerate(['push %rbp', 'vmulps %ymm0,%ymm1,%ymm2', 'ret']))
        run, data = self.run_checker(listing)
        self.assertEqual(run.returncode, 1)  # the NNUE contract cannot be checked without symbols
        self.assertIn('public NNUE evaluate symbol not found', run.stderr)
        run, data = self.run_checker(listing, '--fma-only')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual((data['fma_count'], data['instructions_scanned'], data['nnue_contract']),
                         (0, 3, 'skipped (--fma-only)'))

    def test_complex_and_4fma_mnemonics_are_counted(self):
        listing = section('.text') + body('f()', ['vfcmaddcph %zmm0,%zmm1,%zmm2', 'v4fmaddps (%rax),%zmm4,%zmm0',
                                                  'vfmaddcsh %xmm0,%xmm1,%xmm2', 'vfmulcph %zmm0,%zmm1,%zmm2'])
        run, data = self.run_checker(listing, '--fma-only')
        self.assertEqual(data['fma_count'], 3)  # the complex multiply vfmulcph is not a fused add

    def test_nothing_disassembled_fails(self):
        run, data = self.run_checker('\nDisassembly of section .text:\n\n', '--fma-only')
        self.assertEqual(run.returncode, 1)
        self.assertIn('no instructions disassembled', run.stderr)


if __name__ == '__main__':
    unittest.main()
