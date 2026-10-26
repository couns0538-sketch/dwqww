"""Pure orchestration bindings; native scalar compiler/oracles never launched."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest import mock

HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('run_test',HERE/'forge_sol_S11_scalar_parity_run_20261026.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class RunTests(unittest.TestCase):
    def test_codec_rewrap_requires_explicit_flag_and_exact_original_raw(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'rewrapped.json';d={'count':1000000,'unique_position_fields':1000000,'gzip_size':9000000,'gzip_sha256':'1'*64,'raw_size':52261200,'raw_sha256':'0d6594d3fb7dba38064eddc2a0f673d23c6551c052186cc5989047b86e762eb6','gzip':'/tmp/rewrapped_same_raw_fixture.gz'};p.write_text(json.dumps(d));sealer=mock.Mock();sealer.sealed_memfd_from_gzip.return_value=18
            with mock.patch.object(m,'load',return_value=sealer),mock.patch.object(m.proof,'sha',return_value='e43b6ec82a611e9fd03a1b44b70487189b7df1ed32cfe5734de9e139b055d7bb'):
                with self.assertRaises(ValueError):m.bind_corpus(p)
                result,fd=m.bind_corpus(p,allow_rewrapped=True);self.assertEqual(fd,18);self.assertEqual(result['recovery_classification'],'EXPLICIT_REWRAP_SAME_ORIGINAL_RAW')
                self.assertEqual(sealer.sealed_memfd_from_gzip.call_args.kwargs['compressed_sha256'],'1'*64)
                d['raw_sha256']='0'*64;p.write_text(json.dumps(d))
                with self.assertRaises(ValueError):m.bind_corpus(p,allow_rewrapped=True)

    def test_initial_build_first_and_artifact_identity_cannot_be_replaced(self):
        arm={'source':Path('/tmp/source'),'build':Path('/tmp/build'),'build_receipt_path':'/tmp/build.json','FIRST_receipt_path':'/tmp/first.json','build_receipt_sha256':'a'*64,'FIRST_receipt_sha256':'b'*64,'data':{'base':'Lprime','role':'candidate','profile':'Release','source_before':{'src/search.cpp':'source'},'target_artifacts':{'core_archive':{'path':'/tmp/build/core.a','sha256':'c'*64}},'material_oracle_compilation':{'map_sha256':'d'*64}},'link_map_audit':{'archive_nnue_pulled':True}}
        frozen=m.binding_identity(arm);m.require_arm_identity(frozen,arm)
        for change in ('build','FIRST','artifact','source','map'):
            changed=copy.deepcopy(arm)
            if change=='build':changed['build_receipt_sha256']='0'*64
            elif change=='FIRST':changed['FIRST_receipt_sha256']='0'*64
            elif change=='artifact':changed['data']['target_artifacts']['core_archive']['sha256']='0'*64
            elif change=='source':changed['source']=Path('/tmp/other_source')
            else:changed['data']['material_oracle_compilation']['map_sha256']='0'*64
            with self.subTest(change=change),self.assertRaisesRegex(ValueError,'initial'):m.require_arm_identity(frozen,changed)

    def test_scalar_driver_stays_normal_and_explicit_object_precedes_core(self):
        source=Path('/tmp/unit_src');build=Path('/tmp/unit_build');core=build/'libforge_core.a';scalar=Path('/tmp/unit_scalar.o')
        argv=m.builder.oracle_command(m.builder.release,source,build,'candidate')
        output=Path('/tmp/new_oracle');mp=Path('/tmp/new.map');new=m.scalar_link_argv(argv,core,scalar,output,mp)
        self.assertEqual(new[new.index('-o')+1],str(output));self.assertLess(new.index(str(scalar)),new.index(str(core)));self.assertIn('-DS11_REQUIRE_TABLE=1',new);self.assertFalse(any(x in m.proof.SCALAR_FLAGS for x in new))
        self.assertEqual(len([x for x in new if x.startswith('-Wl,-Map,')]),1)
        for bad in (argv+['-Wl,-Map,/tmp/extra'],argv+[str(core)],argv+['-U__SSE__']):
            with self.assertRaises(ValueError):m.scalar_link_argv(bad,core,scalar,output,mp)

    def test_actual_oracle_command_role_source_map_and_closed_index_bound(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);source=p/'src';source.mkdir();build=p/'build';build.mkdir();(build/'forge').write_text('unit, never executed');core=build/'libforge_core.a';core.write_text('unit archive')
            argv=m.builder.oracle_command(m.builder.release,source,build,'candidate');mp=build/'forge_sol_S11_materialkey_oracle.map';mp.write_text(str(core)+'(board.cpp.o)\n'+str(core)+'(nnue.cpp.o)\nLOAD '+str(core)+'\n')
            oracle={'source':str(m.builder.ORACLE),'sha256':m.proof.ORACLE_SHA,'argv':argv,'command_index':0,'map_path':str(mp),'map_sha256':m.proof.sha(mp)}
            data={'profile':'Release','role':'candidate','S10_published_commit':'a'*40,'compiler_sha256':m.owned.CXX_SHA,'source_inventory_sha256':m.builder.INVENTORY_SHA,'patch_sha256':m.builder.PATCH_SHA,'material_oracle_compilation':oracle,'commands':[{'argv':list(argv)}]}
            br=p/'build.json';br.write_text('{}');first=p/'first.json';first.write_text('{}')
            with mock.patch.object(m.qual,'verify_build',side_effect=lambda path:(data,source,build)),mock.patch.object(m.builder,'verify_dependencies'),mock.patch.object(m.qual,'verify_first'),mock.patch.object(m.qual.previous,'verify_first_files'):
                m.bind_arm(br,first,'candidate','a'*40)
                for kind in ('wrong-role','wrong-publish','bool-index','wrong-command','wrong-map','wrong-source','extra-include'):
                    old=copy.deepcopy(data)
                    if kind=='wrong-role':data['role']='baseline'
                    elif kind=='wrong-publish':data['S10_published_commit']='b'*40
                    elif kind=='bool-index':data['material_oracle_compilation']['command_index']=True
                    elif kind=='wrong-command':data['commands'][0]['argv']=['different compiler']
                    elif kind=='wrong-map':data['material_oracle_compilation']['map_sha256']='0'*64
                    elif kind=='wrong-source':data['material_oracle_compilation']['sha256']='0'*64
                    else:
                        data['material_oracle_compilation']['argv']=argv+['-I/tmp/other_source'];data['commands'][0]['argv']=list(data['material_oracle_compilation']['argv'])
                    with self.subTest(kind=kind),self.assertRaises(ValueError):m.bind_arm(br,first,'candidate','a'*40)
                    data.clear();data.update(old)

    def test_scalar_artifact_binding_cannot_silently_turn_back_into_normal_oracle(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);d={}
            for key in ('object','driver','map'):
                q=p/key;q.write_text('qualified scalar fixture '+key);d[key]=str(q);d[key+'_sha256']=m.proof.sha(q)
            m.verify_scalar_artifacts(d)
            for key in ('object','driver','map'):
                q=Path(d[key]);before=q.read_text();q.write_text('changed')
                with self.subTest(key=key),self.assertRaises(ValueError):m.verify_scalar_artifacts(d)
                q.write_text(before)

    def test_normal_nnue_recipe_binds_actual_source_and_only_one_tu(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);source=p/'source';build=p/'build';build.mkdir();argv=[str(m.owned.CXX),'-std=c++20','-O3','-DNDEBUG',*m.owned.FLAGS.split(),'-c',str(source/'src/nnue.cpp'),'-o','nnue.o'];row={'file':str(source/'src/nnue.cpp'),'arguments':argv}
            cp=build/'compile_commands.json';cp.write_text(json.dumps([row]));self.assertEqual(m.normal_nnue_command(source,build),argv)
            cp.write_text(json.dumps([row,row]))
            with self.assertRaises(ValueError):m.normal_nnue_command(source,build)
            row['arguments']=argv+['-U__SSE__'];cp.write_text(json.dumps([row]))
            with self.assertRaises(ValueError):m.normal_nnue_command(source,build)

    def test_reuses_exact_existing_corpus_and_original_sealer(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'manifest.json';d={'count':1000000,'unique_position_fields':1000000,'gzip_size':8950562,'gzip_sha256':'e06bf2de476f1819ab098b854d718ff1b528c49c60ee9edbfd82206b99798a42','raw_size':52261200,'raw_sha256':'0d6594d3fb7dba38064eddc2a0f673d23c6551c052186cc5989047b86e762eb6','gzip':'/tmp/unit_not_read.gz'};p.write_text(json.dumps(d));sealer=mock.Mock();sealer.sealed_memfd_from_gzip.return_value=17
            with mock.patch.object(m,'load',return_value=sealer),mock.patch.object(m.proof,'sha',return_value='e43b6ec82a611e9fd03a1b44b70487189b7df1ed32cfe5734de9e139b055d7bb'):
                self.assertEqual(m.bind_corpus(p)[1],17)
                self.assertEqual(sealer.sealed_memfd_from_gzip.call_args.kwargs['raw_sha256'],d['raw_sha256'])
                d['count']=999999;p.write_text(json.dumps(d))
                with self.assertRaises(ValueError):m.bind_corpus(p)

if __name__=='__main__':unittest.main(verbosity=2)
