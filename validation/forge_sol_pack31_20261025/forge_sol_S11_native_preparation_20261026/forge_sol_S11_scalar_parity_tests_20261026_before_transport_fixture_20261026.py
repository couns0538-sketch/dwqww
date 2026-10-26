"""Synthetic source-only controls; these are not native engine results."""
import copy
import fcntl
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest import mock

HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('scalar',HERE/'forge_sol_S11_scalar_parity_20261026.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
CORE=Path('/tmp/unit/libforge_core.a');SCALAR=Path('/tmp/unit/nnue_scalar.o')

def normal_map():return str(CORE)+'(board.cpp.o)\n'+str(CORE)+'(nnue.cpp.o)\nLOAD '+str(CORE)+'\n'
def scalar_map():return str(CORE)+'(board.cpp.o)\nLOAD '+str(SCALAR)+'\nLOAD '+str(CORE)+'\n'
def assembly(op,args):return '0000000000000000 <forge::nnue::evaluate(forge::Board const&, forge::nnue::Accumulator const&)>:\n  0: '+op+' '+args+'\n'
def macros(mode):
    base='#define FORGE_NNUE_HIDDEN 256\n#define FORGE_HAS_NNUE 1\n#define FORGE_NNUE_SSE '+('0' if mode=='scalar' else '1')+'\n'
    return base+('' if mode=='scalar' else '#define __AVX2__ 1\n#define __SSE__ 1\n')
def stream(n=2,child=1):return m.HEADER.pack(0x4b313146,1,256,2068,n,child,0x1f80)+bytes(n*2068)
def summary(n=2,table=650):return {'positions':n,'record_bytes':2068,'header_bytes':36,'actual_table_basis_checks':table,'legal_children':20,'nulls':1,'captures':2,'promotions':0,'castles':0,'en_passant':0,'material_key_mismatches':0,'state_mismatches':0}

class ScalarParityTests(unittest.TestCase):
    def test_link_map_proves_normal_and_explicit_selection(self):
        self.assertTrue(m.verify_link_map(normal_map(),CORE)['archive_nnue_pulled'])
        self.assertFalse(m.verify_link_map(scalar_map(),CORE,SCALAR)['archive_nnue_pulled'])
        for text,explicit in [(normal_map()+str(CORE)+'(search.cpp.o)\n',None),(scalar_map()+str(CORE)+'(nnue.cpp.o)\n',SCALAR),(scalar_map().replace('LOAD '+str(SCALAR),'LOAD /tmp/other.o'),SCALAR),(normal_map().replace('LOAD '+str(CORE),''),None),(normal_map()+'LOAD '+str(CORE)+'\n',None),(normal_map()+'LOAD /tmp/foreign/libforge_core.a\n',None),(scalar_map(),None),('LOAD '+str(CORE)+'\n',None)]:
            with self.subTest(text=text),self.assertRaises(ValueError):m.verify_link_map(text,CORE,explicit)

    def test_scalar_command_modifies_only_test_object_and_probe(self):
        argv=['c++','-O3','-std=c++20','-c','/tmp/nnue.cpp','-o','/tmp/old.o']
        changed=m.scalar_compile_argv(argv,SCALAR)
        self.assertEqual(changed[changed.index('-o')+1],str(SCALAR));self.assertEqual(tuple(changed[-4:]),m.SCALAR_FLAGS)
        self.assertEqual(argv[-1],'/tmp/old.o')
        probe=m.macro_probe_argv(changed);self.assertNotIn('-o',probe);self.assertNotIn('-c',probe);self.assertEqual(probe[-2:],['-dM','-E'])
        with self.assertRaises(ValueError):m.scalar_compile_argv(changed,SCALAR)

    def test_normally_compiled_driver_and_link_order(self):
        argv=['c++','driver.cpp',str(SCALAR),str(CORE),'-o','oracle']
        m.verify_oracle_link_argv(argv,CORE,SCALAR)
        for bad in [argv+['-U__SSE__'],['c++',str(CORE),str(SCALAR)],argv+['-Wl,--whole-archive'],argv+['-Wl,--allow-multiple-definition']]:
            with self.assertRaises(ValueError):m.verify_oracle_link_argv(bad,CORE,SCALAR)
        r={'source':'driver.cpp','sha256':m.ORACLE_SHA,'argv':['c++','-DS11_REQUIRE_TABLE=1','driver.cpp']}
        self.assertEqual(m.verify_oracle_compilation(r,'candidate')['expected_table_basis_checks'],650)
        for bad in [dict(r,sha256='0'*64),dict(r,argv=['c++','driver.cpp']),dict(r,argv=r['argv']+['-U__AVX2__'])]:
            with self.assertRaises(ValueError):m.verify_oracle_compilation(bad,'candidate')
        r['argv']=['c++','driver.cpp'];self.assertEqual(m.verify_oracle_compilation(r,'baseline')['expected_table_basis_checks'],0)

    def test_actual_macro_selection_catches_sse_fallback(self):
        m.verify_macros(macros('scalar'),'scalar');m.verify_macros(macros('avx2'),'avx2')
        for bad in [macros('scalar')+'#define __SSE__ 1\n',macros('scalar')+'#define __AVX2__ 1\n',macros('scalar').replace('FORGE_NNUE_SSE 0','FORGE_NNUE_SSE 1'),macros('scalar')+'#define __FAST_MATH__ 1\n',macros('scalar').replace('HIDDEN 256','HIDDEN 128')]:
            with self.assertRaises(ValueError):m.verify_macros(bad,'scalar')

    def test_disassembly_rejects_fma_packed_sse_and_unsupported_width(self):
        good=assembly('vmulss','%xmm1,%xmm0,%xmm0')+assembly('vaddss','%xmm1,%xmm0,%xmm0')
        m.verify_disassembly(good,'scalar');m.verify_disassembly(assembly('vmulps','%ymm1,%ymm0,%ymm0'),'avx2')
        for extra in [assembly('mulps','%xmm1,%xmm0'),assembly('vaddps','%xmm1,%xmm0,%xmm0'),assembly('vmulss','%ymm1,%ymm0,%ymm0'),assembly('vmovaps','%zmm1,%zmm0'),assembly('vfmadd132ss','%xmm1,%xmm2,%xmm0'),assembly('mulsd','%xmm1,%xmm0'),assembly('flds','(%rax)')]:
            with self.subTest(extra=extra),self.assertRaises(ValueError):m.verify_disassembly(good+extra,'scalar')
        with self.assertRaises(ValueError):m.verify_disassembly(assembly('mulps','%xmm1,%xmm0'),'avx2')
        with self.assertRaises(ValueError):m.verify_disassembly('unscoped assembly','scalar')

    def test_full_header_format_and_normally_compiled_fp_control(self):
        m.parse_header(stream()[:36],2,1)
        vals=list(m.HEADER.unpack(stream()[:36]))
        for index,value in [(0,0),(1,2),(2,128),(3,2064),(4,1),(5,0),(6,0xffffffff),(6,1)]:
            changed=list(vals);changed[index]=value
            with self.assertRaises(ValueError):m.parse_header(m.HEADER.pack(*changed),2,1)
        with self.assertRaises(ValueError):m.parse_header(stream()[:35],2,1)

    def test_summary_actual_table_and_restoration_coverage(self):
        m.parse_summary(json.dumps(summary()).encode(),2,1,650)
        for k,v in [('positions',1),('actual_table_basis_checks',0),('material_key_mismatches',1),('state_mismatches',1),('nulls',2),('captures',21),('legal_children',0),('positions',True)]:
            d=summary();d[k]=v
            with self.subTest(field=k),self.assertRaises(ValueError):m.parse_summary(json.dumps(d).encode(),2,1,650)
        with self.assertRaises(ValueError):m.parse_summary(b'oracle FAIL\n',2,1,650)

    def test_exact_every_byte_comparison_and_eof_not_just_hash(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);a=p/'a.gz';b=p/'b.gz';a.write_bytes(gzip.compress(stream(),mtime=0));b.write_bytes(gzip.compress(stream(),mtime=0))
            self.assertEqual(m.compare_gzip(a,b,2,1)['bytes_compared'],4172)
            for raw in [stream()[:-1],stream()+b'x',stream()[:100]+b'\1'+stream()[101:],stream(n=1,child=1)]:
                b.write_bytes(gzip.compress(raw,mtime=0))
                with mock.patch.object(m,'sha',return_value='same-hash'),self.assertRaises(ValueError):m.compare_gzip(a,b,2,1)
            b.write_bytes(gzip.compress(stream()[:-1],mtime=0));a.write_bytes(b.read_bytes())
            with self.assertRaises(ValueError):m.compare_gzip(a,b,2,1)

    def test_sealed_input_bound_to_original_manifest_bytes(self):
        fd=os.memfd_create('unit_S11_corpus',os.MFD_ALLOW_SEALING)
        try:
            raw=b'unit fixture only, not chess evidence\n';os.write(fd,raw);digest=hashlib.sha256(raw).hexdigest()
            with self.assertRaises(ValueError):m.verify_sealed_input(fd,len(raw),digest)
            fcntl.fcntl(fd,getattr(fcntl,'F_ADD_SEALS',1033),0x000f)
            m.verify_sealed_input(fd,len(raw),digest)
            with self.assertRaises(ValueError):m.verify_sealed_input(fd,len(raw),'0'*64)
            with self.assertRaises(ValueError):m.verify_sealed_input(fd,len(raw)+1,digest)
        finally:os.close(fd)

if __name__=='__main__':unittest.main(verbosity=2)
