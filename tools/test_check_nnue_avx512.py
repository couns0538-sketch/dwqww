#!/usr/bin/env python3
"""Parser fixtures for complete, exact-symbol FMA attribution."""
import unittest
import check_nnue_avx512 as audit

FIXTURE = '''sample: file format elf64-x86-64

Disassembly of section .text:

0000000000401000 <__ieee754_log_fma>:
  401000: c4 e2 f1 a9 c2        vfmadd213sd %xmm2,%xmm1,%xmm0
  401005: e8 06 00 00 00        call 401010 <forge::nnue::evaluate()>
0000000000401010 <forge::nnue::evaluate()>:
  401010: c4 e2 75 9c c2        vfnmadd132ps %ymm2,%ymm1,%ymm0
0000000000401020 <notforge::nnue::evaluate()>:
  401020: c4 e2 75 9a c2        vfmsub132ps %ymm2,%ymm1,%ymm0 # forge::text_in_comment()
0000000000401030 <std::less<forge::Type>::operator()(int) const>:
  401030: c4 e2 75 9e c2        vfnmsub132ps %ymm2,%ymm1,%ymm0
0000000000401040 <forge::nnue::refresh(forge::Board const&, forge::nnue::Accumulator&)>:
  401040: 62 f1 7c 48 58 c1     vaddps %zmm1,%zmm0,%zmm0
  401046: 00 00 00
'''

class AttributionFixtures(unittest.TestCase):
    def test_every_fused_family_is_attributed_to_real_raw_header(self):
        result = audit.scan_disassembly(FIXTURE.splitlines())
        self.assertEqual([hit['symbol'] for hit in result['fma_hits']], [
            '__ieee754_log_fma', 'forge::nnue::evaluate()',
            'notforge::nnue::evaluate()',
            'std::less<forge::Type>::operator()(int) const'])
        self.assertEqual(len(result['fma_hits']), 4)
        self.assertFalse(result['unattributed_fma'])

    def test_negative_forge_fma_is_rejected_despite_preceding_library_symbol(self):
        result = audit.scan_disassembly(FIXTURE.splitlines())
        self.assertEqual([hit['symbol'] for hit in result['forge_fma']],
                         ['forge::nnue::evaluate()'])
        self.assertEqual(len(result['nonforge_fma']), 3)

    def test_namespace_substring_and_operand_comment_do_not_change_owner(self):
        self.assertFalse(audit.is_forge_symbol('notforge::nnue::evaluate()'))
        self.assertFalse(audit.is_forge_symbol('std::less<forge::Type>::operator()(int) const'))
        self.assertTrue(audit.is_forge_symbol('forge::nnue::evaluate() [clone .cold]'))
        self.assertTrue(audit.is_forge_symbol('non-virtual thunk to forge::Worker::run()'))

    def test_zmm_witness_uses_instruction_operands_in_actual_symbol(self):
        result = audit.scan_disassembly(FIXTURE.splitlines())
        refresh = next(s for s in result['symbols'] if s['name'].startswith('forge::nnue::refresh('))
        evaluate = next(s for s in result['symbols'] if s['name'] == 'forge::nnue::evaluate()')
        self.assertEqual(refresh['zmm_instructions'], 1)
        self.assertEqual(evaluate['zmm_instructions'], 0)

    def test_unattributed_fma_is_a_failure_not_silently_ignored(self):
        result = audit.scan_disassembly(['  401000: c4 e2 f1 a9 c2 vfmadd213sd %xmm2,%xmm1,%xmm0'])
        self.assertEqual(len(result['unattributed_fma']), 1)

if __name__ == '__main__':
    unittest.main()
