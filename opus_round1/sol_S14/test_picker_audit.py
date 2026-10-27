#!/usr/bin/env python3
"""Unit tests for picker_audit.py (pure; synthetic disassembly and a synthetic PE image).
Run: python -I -B test_picker_audit.py.  PICKER_AUDIT_PATH=<file> tests another copy (planted-bug check)."""
import importlib.util
import os
import struct
import sys
import tempfile
import unittest
from pathlib import Path

_PATH = os.environ.get("PICKER_AUDIT_PATH", str(Path(__file__).with_name("picker_audit.py")))
_spec = importlib.util.spec_from_file_location("picker_audit", _PATH)
pa = importlib.util.module_from_spec(_spec)
sys.modules["picker_audit"] = pa
_spec.loader.exec_module(pa)

DIS = """\
0000000140001000 <forge::MovePicker::next(bool)>:
   140001000:\tcmp    $0x2,%eax
   140001003:\tja     140001020 <forge::MovePicker::next(bool)+0x20>
   140001005:\tlea    0x1ff4(%rip),%rcx        # 140003000 <.rdata>
   14000100c:\tmovslq (%rcx,%r8,4),%rdx
   140001010:\tadd    %rcx,%rdx
   140001013:\tjmp    *%rdx
   140001015:\tcall   140001100 <forge::Board::see_ge(forge::Move const&, int) const>
   14000101a:\tjmp    140001200 <helper()>
   140001020:\tret

0000000140001100 <forge::Board::see_ge(forge::Move const&, int) const>:
   140001100:\tcall   140001300 <operator new(unsigned long long)>
   140001105:\tret

0000000140001200 <helper()>:
   140001200:\tjmp    *0x10(%rip)        # 140004000 <__imp_memmove>

0000000140001300 <operator new(unsigned long long)>:
   140001300:\tret

0000000140001400 <forge::Worker::qsearch(forge::Board&, forge::SearchStack*, int, int)>:
   140001400:\tmov    $0x800,%r8d
   140001406:\txor    %edx,%edx
   140001408:\tcall   140001500 <memset>
   14000140d:\tcall   140001000 <forge::MovePicker::next(bool)>
   140001412:\tret

0000000140001500 <memset>:
   140001500:\tret

0000000140001600 <unreached()>:
   140001600:\tcall   140001300 <operator new(unsigned long long)>
"""


def tiny_pe(table_va_offset: int, entries):
    """PE32+ with one .rdata section at image_base + 0x3000 holding `entries` (int32) at the offset."""
    image_base = 0x140000000
    raw = bytearray(0x200)
    for j, e in enumerate(entries):
        struct.pack_into("<i", raw, table_va_offset + 4 * j, e)
    pe_off = 0x40
    opt_size = 240
    head = bytearray(0x400)
    head[0:2] = b"MZ"
    struct.pack_into("<I", head, 0x3C, pe_off)
    head[pe_off:pe_off + 4] = b"PE\0\0"
    struct.pack_into("<HH", head, pe_off + 4, 0x8664, 1)
    struct.pack_into("<H", head, pe_off + 20, opt_size)
    opt = pe_off + 24
    struct.pack_into("<H", head, opt, 0x20B)
    struct.pack_into("<Q", head, opt + 24, image_base)
    sec = opt + opt_size
    head[sec:sec + 8] = b".rdata\0\0"
    struct.pack_into("<IIII", head, sec + 8, 0x200, 0x3000, 0x200, 0x400)
    return bytes(head) + bytes(raw)


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.funcs, self.entry = pa.parse(DIS)

    def test_parse(self):
        self.assertIn("forge::MovePicker::next(bool)", self.funcs)
        self.assertEqual(len(self.funcs["forge::MovePicker::next(bool)"]), 9)
        self.assertEqual(self.entry[0x140001300], "operator new(unsigned long long)")

    def test_edges_skip_internal_jumps_and_keep_tail_calls(self):
        direct, indirect = pa.edges("forge::MovePicker::next(bool)", self.funcs["forge::MovePicker::next(bool)"], self.entry)
        callees = {c for _, _, c in direct}
        self.assertEqual(callees, {"forge::Board::see_ge(forge::Move const&, int) const", "helper()"})
        self.assertEqual([a for a, _ in indirect], [0x140001013])

    def test_closure_reaches_allocation_through_callee(self):
        reach = pa.closure(self.funcs, self.entry, ["forge::MovePicker::next(bool)"])
        self.assertIn("operator new(unsigned long long)", reach)
        self.assertNotIn("unreached()", reach)
        self.assertTrue(pa.ALLOC_RE.search("operator new(unsigned long long)"))
        self.assertTrue(pa.ALLOC_RE.search("malloc"))
        self.assertFalse(pa.ALLOC_RE.search("memset"))

    def test_memset_sites(self):
        sites = pa.memset_sites(self.funcs, self.entry)
        self.assertEqual([(s["addr"], s["size"]) for s in sites], [(0x140001408, 2048)])

    def test_jump_table_recognised(self):
        insns = self.funcs["forge::MovePicker::next(bool)"]
        self.assertEqual(pa.jump_table(insns, 5), (0x140003000, 3))

    def test_switch_table_inside_and_outside(self):
        name = "forge::MovePicker::next(bool)"
        bounds = {name: (0x140001000, 0x140001100)}
        insns = self.funcs[name]
        inside = pa.PEImage(tiny_pe(0, [0x140001015 - 0x140003000, 0x14000101a - 0x140003000, 0x140001020 - 0x140003000]))
        ok, note = pa.classify_indirect(name, insns, 5, insns[5][1], inside, bounds)
        self.assertTrue(ok, note)
        outside = pa.PEImage(tiny_pe(0, [0x140001015 - 0x140003000, 0x140001300 - 0x140003000, 0]))
        ok, note = pa.classify_indirect(name, insns, 5, insns[5][1], outside, bounds)
        self.assertFalse(ok, note)
        ok, _ = pa.classify_indirect(name, insns, 5, insns[5][1], None, bounds)
        self.assertFalse(ok)

    def test_import_thunks(self):
        ok, note = pa.classify_indirect("helper()", [], 0, "jmp    *0x10(%rip)        # 140004000 <__imp_memmove>", None, {})
        self.assertTrue(ok, note)
        ok, _ = pa.classify_indirect("helper()", [], 0, "call   *0x10(%rip)        # 140004000 <__imp_HeapAlloc>", None, {})
        self.assertFalse(ok)

    def test_main_flags_allocation(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.dis"
            p.write_text(DIS, encoding="utf-8")
            self.assertEqual(pa.main([str(p)]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
