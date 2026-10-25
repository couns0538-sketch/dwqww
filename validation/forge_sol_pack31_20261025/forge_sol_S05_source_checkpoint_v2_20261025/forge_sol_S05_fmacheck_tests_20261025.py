#!/usr/bin/env python3
"""Disassembly fixtures exercise the actual checker CLI without claiming machine code."""
import argparse,base64,hashlib,json,os
from pathlib import Path
import subprocess,sys,tempfile,unittest
ap=argparse.ArgumentParser();ap.add_argument('--checker',required=True);ap.add_argument('--old-checker');ap.add_argument('--out');ap.add_argument('--ctest-parent');ap.add_argument('--old-red-only',action='store_true');args,rest=ap.parse_known_args();sys.argv=[sys.argv[0]]+rest
if bool(args.out)==bool(args.ctest_parent):raise SystemExit('choose exactly one of --out or --ctest-parent')
CTEST_TEMP=tempfile.TemporaryDirectory(prefix='forge_sol_S05_ctest_20261025_',dir=args.ctest_parent) if args.ctest_parent else None
OUT=Path(CTEST_TEMP.name) if CTEST_TEMP else Path(args.out)
if args.out:OUT.mkdir(exist_ok=False)
PUBLIC='forge::nnue::evaluate(forge::Board const&, forge::nnue::Accumulator const&)'
HELPER='forge::nnue::(anonymous namespace)::evaluate_values(float const*, float const*)'
VECTORS=['vmaxps %ymm0,%ymm1,%ymm2','vminps %ymm0,%ymm1,%ymm2','vmulps %ymm0,%ymm1,%ymm2','vaddps %ymm0,%ymm1,%ymm2','ret']
def body(name,insns,start=4096):
 return f'{start:016x} <{name}>:\n'+''.join(f' {start+i*8:x}:\t00\t{ins}\n' for i,ins in enumerate(insns))
def record(b):return {'encoding':'base64','data':base64.b64encode(b).decode(),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def invoke(checker,assembly,label):
 with tempfile.TemporaryDirectory(prefix='forge_sol_S05_fixture_20261025_',dir=OUT) as d:
  p=Path(d);fixture=p/'forge_sol_S05_assembly_20261025.txt';fixture.write_text(assembly)
  shim=p/'objdump';shim.write_text('#!/usr/bin/env python3\nimport os,sys\nsys.stdout.buffer.write(open(os.environ["S05_ASSEMBLY_FIXTURE"],"rb").read())\n');shim.chmod(0o700)
  env=dict(os.environ,PATH=str(p)+os.pathsep+os.environ['PATH'],S05_ASSEMBLY_FIXTURE=str(fixture),PYTHONDONTWRITEBYTECODE='1')
  argv=[sys.executable,'-B',checker,str(fixture)];run=subprocess.run(argv,env=env,capture_output=True)
  receipt={'argv':argv,'exit':run.returncode,'fixture':record(assembly.encode()),'stdout':record(run.stdout),'stderr':record(run.stderr),'scope':'Synthetic disassembly fixture; not an actual executable','child_waited':True,'stream_capture_complete':True}
  (OUT/f'forge_sol_S05_{label}_20261025.json').write_text(json.dumps(receipt,indent=2)+'\n')
  return run
class CheckTests(unittest.TestCase):
 def test_pc_copied_zero_clamp_passes(self):
  ins=['vxorps %xmm5,%xmm5,%xmm5','vmovaps %ymm5,%ymm16','vmovaps %ymm5,%ymm2','vcmpgtps %ymm2,%ymm0,%k1','vmovaps %ymm0,%ymm1{%k1}{z}']+VECTORS[1:]
  self.assertEqual(invoke(args.checker,body(PUBLIC,ins),'fixture_pc_copied_zero').returncode,0)
 def test_unaligned_copied_zero_clamp_passes(self):
  ins=['vxorps %xmm5,%xmm5,%xmm5','vmovups %ymm5,%ymm2','vcmpgtps %ymm2,%ymm0,%k1','vmovaps %ymm0,%ymm1{%k1}{z}']+VECTORS[1:]
  self.assertEqual(invoke(args.checker,body(PUBLIC,ins),'fixture_unaligned_copied_zero').returncode,0)
 def test_unknown_copy_source_rejected(self):
  ins=['vxorps %xmm5,%xmm5,%xmm5','vmovaps %ymm7,%ymm2','vcmpgtps %ymm2,%ymm0,%k1','vmovaps %ymm0,%ymm1{%k1}{z}']+VECTORS[1:]
  self.assertNotEqual(invoke(args.checker,body(PUBLIC,ins),'fixture_unknown_copy_source').returncode,0)
 def test_masked_zero_copy_rejected(self):
  ins=['vxorps %xmm5,%xmm5,%xmm5','vmovaps %ymm5,%ymm2{%k2}','vcmpgtps %ymm2,%ymm0,%k1','vmovaps %ymm0,%ymm1{%k1}{z}']+VECTORS[1:]
  self.assertNotEqual(invoke(args.checker,body(PUBLIC,ins),'fixture_masked_zero_copy').returncode,0)
 def test_memory_zero_copy_rejected(self):
  ins=['vxorps %xmm5,%xmm5,%xmm5','vmovaps (%rax),%ymm2','vcmpgtps %ymm2,%ymm0,%k1','vmovaps %ymm0,%ymm1{%k1}{z}']+VECTORS[1:]
  self.assertNotEqual(invoke(args.checker,body(PUBLIC,ins),'fixture_memory_zero_copy').returncode,0)
 def test_xmm_copy_does_not_prove_full_ymm_rejected(self):
  ins=['vxorps %xmm5,%xmm5,%xmm5','vmovaps %xmm5,%xmm2','vcmpgtps %ymm2,%ymm0,%k1','vmovaps %ymm0,%ymm1{%k1}{z}']+VECTORS[1:]
  self.assertNotEqual(invoke(args.checker,body(PUBLIC,ins),'fixture_xmm_copy').returncode,0)
 def test_clobbered_copy_source_rejected(self):
  ins=['vxorps %xmm5,%xmm5,%xmm5','vmovaps %ymm7,%ymm5','vmovaps %ymm5,%ymm2','vcmpgtps %ymm2,%ymm0,%k1','vmovaps %ymm0,%ymm1{%k1}{z}']+VECTORS[1:]
  self.assertNotEqual(invoke(args.checker,body(PUBLIC,ins),'fixture_clobbered_copy_source').returncode,0)
 def test_clobbered_copy_destination_rejected(self):
  ins=['vxorps %xmm5,%xmm5,%xmm5','vmovaps %ymm5,%ymm2','vmovaps %ymm7,%ymm2','vcmpgtps %ymm2,%ymm0,%k1','vmovaps %ymm0,%ymm1{%k1}{z}']+VECTORS[1:]
  self.assertNotEqual(invoke(args.checker,body(PUBLIC,ins),'fixture_clobbered_copy_destination').returncode,0)
 def test_copy_before_call_rejected(self):
  ins=['vxorps %xmm5,%xmm5,%xmm5','vmovaps %ymm5,%ymm2','call 3000 <helper()>','vcmpgtps %ymm2,%ymm0,%k1','vmovaps %ymm0,%ymm1{%k1}{z}']+VECTORS[1:]
  self.assertNotEqual(invoke(args.checker,body(PUBLIC,ins),'fixture_copy_before_call').returncode,0)
 def test_copy_before_branch_rejected(self):
  ins=['vxorps %xmm5,%xmm5,%xmm5','vmovaps %ymm5,%ymm2','jne 3000 <other()>','vcmpgtps %ymm2,%ymm0,%k1','vmovaps %ymm0,%ymm1{%k1}{z}']+VECTORS[1:]
  self.assertNotEqual(invoke(args.checker,body(PUBLIC,ins),'fixture_copy_before_branch').returncode,0)
 def test_public_float_output_passes(self):self.assertEqual(invoke(args.checker,body(PUBLIC,VECTORS),'fixture_public').returncode,0)
 def test_outlined_float_output_passes(self):self.assertEqual(invoke(args.checker,body(PUBLIC,['call 2000 <'+HELPER+'>','ret'])+body(HELPER,VECTORS,8192),'fixture_outlined').returncode,0)
 def test_outlined_fma_rejected(self):self.assertNotEqual(invoke(args.checker,body(PUBLIC,VECTORS)+body(HELPER,['vfmadd213ps %ymm0,%ymm1,%ymm2','ret'],8192),'fixture_helper_fma').returncode,0)
 def test_public_fma_rejected(self):self.assertNotEqual(invoke(args.checker,body(PUBLIC,VECTORS+['vfnmsub132ss %xmm0,%xmm1,%xmm2']),'fixture_public_fma').returncode,0)
 def test_other_nnue_fma_rejected(self):self.assertNotEqual(invoke(args.checker,body(PUBLIC,VECTORS)+body('forge::nnue::refresh(forge::Board const&, forge::nnue::Accumulator&)', ['vfmsub231pd %ymm0,%ymm1,%ymm2'],8192),'fixture_refresh_fma').returncode,0)
 def test_unrelated_fma_not_misclassified(self):self.assertEqual(invoke(args.checker,body(PUBLIC,VECTORS)+body('unrelated_function()', ['vfmadd213ps %ymm0,%ymm1,%ymm2'],8192),'fixture_unrelated_fma').returncode,0)
 def test_symbol_name_is_not_instruction(self):self.assertEqual(invoke(args.checker,body(PUBLIC,VECTORS)+body('forge::nnue::vfmadd_name_only()', ['ret'],8192),'fixture_name_only').returncode,0)
 def test_missing_output_contract_rejected(self):self.assertNotEqual(invoke(args.checker,body(PUBLIC,['ret']),'fixture_missing').returncode,0)
 def test_masked_clamp_passes(self):
  ins=['vxorps %ymm0,%ymm0,%ymm0','vcmpgtps %ymm0,%ymm1,%k1','vmovaps %ymm1,%ymm2{%k1}{z}']+VECTORS[1:]
  self.assertEqual(invoke(args.checker,body(PUBLIC,ins),'fixture_masked').returncode,0)
 def test_wrong_mask_polarity_rejected(self):
  ins=['vxorps %ymm0,%ymm0,%ymm0','vcmpltps %ymm0,%ymm1,%k1','vmovaps %ymm1,%ymm2{%k1}{z}']+VECTORS[1:]
  self.assertNotEqual(invoke(args.checker,body(PUBLIC,ins),'fixture_bad_mask').returncode,0)
 def test_blend_nonzero_false_lanes_rejected(self):
  ins=['vxorps %ymm0,%ymm0,%ymm0','vcmpgtps %ymm0,%ymm1,%k1','vblendmps %ymm1,%ymm7,%ymm2{%k1}']+VECTORS[1:]
  self.assertNotEqual(invoke(args.checker,body(PUBLIC,ins),'fixture_bad_blend').returncode,0)
 def test_stale_compared_value_rejected(self):
  ins=['vxorps %ymm0,%ymm0,%ymm0','vcmpgtps %ymm0,%ymm1,%k1','vmovaps %ymm7,%ymm1','vmovaps %ymm1,%ymm2{%k1}{z}']+VECTORS[1:]
  self.assertNotEqual(invoke(args.checker,body(PUBLIC,ins),'fixture_stale_value').returncode,0)
 def test_clobbered_zero_blend_rejected(self):
  ins=['vxorps %ymm0,%ymm0,%ymm0','vcmpgtps %ymm0,%ymm1,%k1','vmovaps %ymm7,%ymm0 # overwritten','vblendmps %ymm1,%ymm0,%ymm2{%k1}']+VECTORS[1:]
  self.assertNotEqual(invoke(args.checker,body(PUBLIC,ins),'fixture_stale_zero').returncode,0)
 def test_blend_proven_zero_false_lanes_passes(self):
  ins=['vxorps %ymm0,%ymm0,%ymm0','vcmpgtps %ymm0,%ymm1,%k1','vblendmps %ymm1,%ymm0,%ymm2{%k1}']+VECTORS[1:]
  self.assertEqual(invoke(args.checker,body(PUBLIC,ins),'fixture_good_blend').returncode,0)
 def test_caller_clobbered_zero_before_compare_rejected(self):
  ins=['vxorps %ymm0,%ymm0,%ymm0','call 3000 <helper()>','vcmpgtps %ymm0,%ymm1,%k1','vmovaps %ymm1,%ymm2{%k1}{z}']+VECTORS[1:]
  self.assertNotEqual(invoke(args.checker,body(PUBLIC,ins),'fixture_call_clobber').returncode,0)
 def test_zmm_alias_zero_clobber_rejected(self):
  ins=['vxorps %ymm0,%ymm0,%ymm0','vmovaps %zmm7,%zmm0','vcmpgtps %ymm0,%ymm1,%k1','vmovaps %ymm1,%ymm2{%k1}{z}']+VECTORS[1:]
  self.assertNotEqual(invoke(args.checker,body(PUBLIC,ins),'fixture_zmm_alias').returncode,0)
 def test_zero_reestablished_after_call_passes(self):
  ins=['call 3000 <helper()>','vxorps %ymm0,%ymm0,%ymm0','vcmpgtps %ymm0,%ymm1,%k1','vmovaps %ymm1,%ymm2{%k1}{z}']+VECTORS[1:]
  self.assertEqual(invoke(args.checker,body(PUBLIC,ins),'fixture_call_rezero').returncode,0)
if __name__=='__main__':
 try:
  if args.old_red_only:
   if not args.old_checker:raise SystemExit('--old-checker required')
   r=invoke(args.old_checker,body(PUBLIC,VECTORS)+body(HELPER,['vfmadd213ps %ymm0,%ymm1,%ymm2','ret'],8192),'old_false_pass')
   print('old checker helper-FMA rejection expected; actual exit',r.returncode)
   raise SystemExit(1 if r.returncode==0 else 2)
  unittest.main()
 finally:
  if CTEST_TEMP:CTEST_TEMP.cleanup()
