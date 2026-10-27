#!/usr/bin/env python3
"""Pure source/assembly-text observer controls; never compile or run an engine.

Synthetic snippets below test parser acceptance only. Original full/excerpt
fixtures are unchanged captured objdump text, not new native/parity evidence.
Set FORGE_S11_OBSERVER_TEST_TARGET to the pinned original observer for RED.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import sys
import unittest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
DEFAULT_TARGET = HERE / 'forge_sol_S11_scalar_parity_observer_v2_20261026.py'
TARGET = Path(os.environ.get('FORGE_S11_OBSERVER_TEST_TARGET', str(DEFAULT_TARGET)))
CONTROL = HERE / 'forge_sol_S11_scalar_observer_controls_20261026.json'
CONTROL_SHA = '12086e06d05954993b193f68af3b5d4d5112d4f6770ee4e37b8685bbb7a34ebc'
EVALUATE = 'forge::nnue::evaluate(forge::Board const&, forge::nnue::Accumulator const&)'
REFRESH = 'forge::nnue::refresh(forge::Board const&, forge::nnue::Accumulator&)'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if sha(CONTROL) != CONTROL_SHA:
    raise RuntimeError('frozen observer control binding changed')
CONTROL_DATA = json.loads(CONTROL.read_text())
if not TARGET.is_file():
    raise RuntimeError('observer target not ready; no default-target test run authorized')
spec = importlib.util.spec_from_file_location('forge_s11_observer_under_test', TARGET)
observer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(observer)


def assembly(*rows, symbol=EVALUATE):
    """Explicitly synthetic, single-function disassembly parser input."""
    return ('0000000000000980 <' + symbol + '>:\n'
            + ''.join(f' {0x980 + index * 4:x}:\t{op} {args}\n'
                      for index, (op, args) in enumerate(rows)))


SCALAR_MATH = (('vmulss', '%xmm1,%xmm0,%xmm0'),
               ('vaddss', '%xmm1,%xmm0,%xmm0'))
BLEND = ('vblendvps', '%xmm2,%xmm0,%xmm1,%xmm1')


class FixtureBindingTests(unittest.TestCase):
    def test_actual_full_and_excerpt_identity_and_original_nine(self):
        for name in ['full_fixture', 'excerpt_fixture']:
            row = CONTROL_DATA[name]
            path = HERE / row['name']
            self.assertEqual(sha(path), row['sha256'])
            self.assertEqual(path.stat().st_size, row['bytes'])
        self.assertEqual(len(CONTROL_DATA['original_nine_negatives']), 9)
        self.assertEqual(CONTROL_DATA['original_review']['sha256'],
                         '35ed06dec1a3b115d574abab252b5157ecfe9613e193dbb3f87ba17ddadb8809')
        self.assertEqual(CONTROL_DATA['original_observer']['sha256'],
                         '31f475c01580d376e3f5a28debe3f37651fff7c426ca1a12d20c77832b263ae5')
        self.assertEqual(CONTROL_DATA['excerpt_fixture']['instruction_rows'], 110)


class ScalarObserverTests(unittest.TestCase):
    def accepts(self, text, mode='scalar'):
        result = observer.verify_disassembly(text, mode)
        self.assertIs(result['ISA_proven'], True)
        self.assertEqual(result['mode'], mode)
        self.assertEqual(result['FMA_count'], 0)
        return result

    def rejects(self, text, mode='scalar'):
        with self.assertRaises(ValueError):
            observer.verify_disassembly(text, mode)

    def assert_actual_counts(self, result):
        for key, value in {'allowed_YMM_stack_store_count': 2,
                           'allowed_XMM_selection_count': 4,
                           'scalar_FP32_mul_count': 9,
                           'scalar_FP32_add_count': 20}.items():
            self.assertEqual(result[key], value, key)

    def test_actual_captured_full_disassembly_is_accepted(self):
        path = HERE / CONTROL_DATA['full_fixture']['name']
        self.assert_actual_counts(self.accepts(path.read_text()))

    def test_actual_captured_excerpt_with_actual_header_is_accepted(self):
        row = CONTROL_DATA['excerpt_fixture']
        # Only parser scope context is added. The original excerpt bytes are
        # separately pinned and remain unchanged; no native output is rebuilt.
        text = row['actual_header_context'] + '\n' + (HERE / row['name']).read_text()
        self.assert_actual_counts(self.accepts(text))

    def test_scalar_fp32_mul_and_add_still_demonstrated(self):
        self.accepts(assembly(*SCALAR_MATH))
        for rows in [(), SCALAR_MATH[:1], SCALAR_MATH[1:]]:
            with self.subTest(rows=rows):
                self.rejects(assembly(*rows))

    def test_only_reviewed_ymm_rsp_stores_are_accepted(self):
        for operands in ['%ymm0,(%rsp)', '%ymm0,0x20(%rsp)']:
            with self.subTest(operands=operands):
                self.accepts(assembly(('vpxor', '%xmm0,%xmm0,%xmm0'),
                                      ('vmovdqa', operands), *SCALAR_MATH))

    def test_only_four_xmm_register_selection_is_accepted(self):
        self.accepts(assembly(('vcmpnltss', '%xmm3,%xmm0,%xmm2'), BLEND,
                              ('vminss', '%xmm1,%xmm4,%xmm1'), *SCALAR_MATH))

    def test_original_nine_negative_controls_are_retained(self):
        for row in CONTROL_DATA['original_nine_negatives']:
            with self.subTest(original=row['review_description']):
                self.rejects(assembly(*SCALAR_MATH,
                                      (row['mnemonic'], row['operands'])))

    def test_packed_arithmetic_after_permitted_blend_still_rejected(self):
        for op, operands in [('mulps', '%xmm1,%xmm0'),
                             ('vaddps', '%xmm1,%xmm0,%xmm0'),
                             ('vmulps', '%ymm1,%ymm0,%ymm0'),
                             ('vdpps', '$255,%xmm1,%xmm0,%xmm0'),
                             ('vhaddps', '%xmm1,%xmm0,%xmm0')]:
            with self.subTest(op=op, operands=operands):
                self.rejects(assembly(BLEND, *SCALAR_MATH, (op, operands)))

    def test_ymm_zmm_memory_and_wrong_arity_blends_rejected(self):
        for operands in ['%ymm2,%ymm0,%ymm1,%ymm1',
                         '%zmm2,%zmm0,%zmm1,%zmm1',
                         '%xmm2,(%rax),%xmm1,%xmm1',
                         '%xmm2,%xmm0,%xmm1']:
            with self.subTest(operands=operands):
                self.rejects(assembly(*SCALAR_MATH, ('vblendvps', operands)))

    def test_unreviewed_ymm_transfers_and_stack_shapes_rejected(self):
        for op, operands in [('vmovdqa', '(%rsp),%ymm0'),
                             ('vmovdqa', '%ymm0,%ymm1'),
                             ('vmovdqa', '%ymm0,(%rax)'),
                             ('vmovdqa', '%ymm0,-0x20(%rsp)'),
                             ('vmovdqa', '%ymm0,32(%rsp)'),
                             ('vmovdqa', '%ymm0,0x20(%rsp,%rax,1)'),
                             ('vmovdqu', '%ymm0,(%rsp)'),
                             ('vmovaps', '%ymm0,(%rsp)'),
                             ('vmovdqa32', '%ymm0,(%rsp)')]:
            with self.subTest(op=op, operands=operands):
                self.rejects(assembly(*SCALAR_MATH, (op, operands)))

    def test_unknown_or_arithmetic_wide_opcodes_fail_closed(self):
        for op, operands in [('vunknown', '%ymm1,%ymm0'),
                             ('vpaddd', '%ymm1,%ymm0,%ymm0'),
                             ('vpshufb', '%ymm2,%ymm1,%ymm0'),
                             ('vpxor', '%ymm0,%ymm0,%ymm0'),
                             ('vaddps', '%ymm1,%ymm0,%ymm0')]:
            with self.subTest(op=op):
                self.rejects(assembly(*SCALAR_MATH, (op, operands)))

    def test_zmm_never_permitted_even_with_transfer_spelling(self):
        self.rejects(assembly(*SCALAR_MATH, ('vmovdqa', '%zmm0,(%rsp)')))

    def test_nnue_wide_fma_and_zmm_guards_not_bypassed(self):
        modes = [('scalar', assembly(*SCALAR_MATH)),
                 ('avx2', assembly(('vmulps', '%ymm1,%ymm0,%ymm0')))]
        for mode, good in modes:
            for row in [('vfmadd132ss', '%xmm1,%xmm2,%xmm0'),
                        ('vfnmadd231ss', '%xmm1,%xmm2,%xmm0'),
                        ('vfmsub132ps', '%ymm1,%ymm2,%ymm0'),
                        ('vmovdqa', '%zmm0,(%rsp)')]:
                with self.subTest(mode=mode, row=row):
                    self.rejects(good + assembly(row, symbol=REFRESH), mode)

    def test_fp64_x87_and_packed_sse_after_selection_rejected(self):
        for row in [('vaddsd', '%xmm1,%xmm0,%xmm0'),
                    ('mulsd', '%xmm1,%xmm0'),
                    ('addpd', '%xmm1,%xmm0'),
                    ('fadd', '%st(1),%st'),
                    ('flds', '(%rax)')]:
            with self.subTest(row=row):
                self.rejects(assembly(BLEND, *SCALAR_MATH, row))

    def test_normal_avx2_still_requires_actual_packed_inference(self):
        self.accepts(assembly(('vmulps', '%ymm1,%ymm0,%ymm0')), 'avx2')
        self.rejects(assembly(*SCALAR_MATH), 'avx2')
        self.rejects(assembly(('mulps', '%xmm1,%xmm0')), 'avx2')

    def test_unscoped_missing_evaluate_and_unknown_mode_rejected(self):
        self.rejects('unscoped assembly')
        self.rejects(assembly(*SCALAR_MATH, symbol=REFRESH))
        self.rejects(assembly(*SCALAR_MATH), 'unknown')


if __name__ == '__main__':
    print(json.dumps({'scope': 'PURE_ASSEMBLY_TEXT_TESTS_NOT_NATIVE',
                      'target': str(TARGET), 'target_sha256': sha(TARGET),
                      'control_sha256': sha(CONTROL)}), flush=True)
    unittest.main(verbosity=2)
