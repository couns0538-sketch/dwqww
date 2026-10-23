"""Eight-output selection, export and whole-game training guards."""
import importlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

import numpy as np
import torch

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
try:
    training = importlib.import_module('train_bucketed_nnue')
except ModuleNotFoundError:
    training = None
from include_parser import load_include

def features(counts):
    x = torch.zeros((len(counts), 2, 768), dtype=torch.float32)
    for row, count in enumerate(counts): x[row, :, :count] = 1.0
    return x

class BucketedTrainingTests(unittest.TestCase):
    def model(self, qat=False):
        self.assertIsNotNone(training, 'Eight-output trainer must be available')
        return training.BucketedNNUE(qat=qat)

    def test_piece_count_boundary_mapping_and_both_perspectives(self):
        self.model()
        counts = list(range(2, 33))
        self.assertEqual(training.bucket_indices(features(counts)).tolist(), [(n-1)//4 for n in counts])
        x = features([4]); x[0, 1, 4] = 1
        with self.assertRaises(ValueError): training.bucket_indices(x)

    def test_invalid_features_cannot_silently_choose_a_head(self):
        self.model()
        for x in [features([0]), features([33]), torch.zeros(1, 2, 767), features([4])+0.5]:
            with self.subTest(shape=x.shape), self.assertRaises(ValueError): training.bucket_indices(x)

    def test_forward_selects_nonidentical_head_for_every_bucket(self):
        model = self.model()
        with torch.no_grad():
            model.ft.weight.zero_(); model.ft.bias.zero_(); model.output.weight.zero_()
            model.output.bias.copy_(torch.arange(8, dtype=torch.float32)/8)
        torch.testing.assert_close(model(features([2,5,9,13,17,21,25,29])).flatten(), torch.arange(8)/8)

    def test_only_selected_output_heads_receive_gradients(self):
        model = self.model()
        with torch.no_grad(): model.ft.bias.fill_(0.5)
        model(features([5, 29])).sum().backward()
        changed = (model.output.bias.grad != 0).nonzero().flatten().tolist()
        self.assertEqual(changed, [1, 7])
        self.assertTrue(torch.all(model.output.weight.grad[[0,2,3,4,5,6]] == 0))

    def test_small_synthetic_optimizer_step_is_finite(self):
        model = self.model(qat=True); model.train()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        x=features([2,5,9,13,17,21,25,29]); y=torch.tensor([0.,.5,1.,0.,.5,1.,0.,.5])
        loss=training.train_batch(model, optimizer, x, torch.zeros(8), torch.zeros(8), y, result_weight=0.4)
        self.assertTrue(np.isfinite(loss)); self.assertTrue(all(torch.isfinite(p).all() for p in model.parameters()))

    def test_legacy_initialization_duplicates_all_eight_heads(self):
        model=self.model(); old=load_include(TOOLS.parents[1]/'src/nnue_weights.inc',expected_hidden=128)
        self.assertEqual(old['output_buckets'],8)
        with tempfile.TemporaryDirectory() as temp:
            # Make a real legacy export from the unmodified legacy exporter.
            from train_nnue import NNUE, export_forge
            legacy=NNUE([128]); stem=Path(temp)/'legacy'; export_forge(legacy,stem,2.25,residual=True)
            training.load_initial(model,stem.with_suffix('.inc'))
            for i in range(1,8):
                torch.testing.assert_close(model.output.weight[i],model.output.weight[0],rtol=0,atol=0)
                self.assertEqual(model.output.bias[i].item(),model.output.bias[0].item())

    def test_eight_head_export_round_trip_and_no_overwrite(self):
        model=self.model()
        with torch.no_grad(): model.output.bias.copy_(torch.arange(8)/16)
        with tempfile.TemporaryDirectory() as temp:
            stem=Path(temp)/'export'; metadata=training.export_bucketed(model,stem)
            parsed=load_include(stem.with_suffix('.inc'),expected_hidden=128)
            self.assertEqual(parsed['output_buckets'],8); self.assertEqual(parsed['bucket_w2'].shape,(8,256))
            np.testing.assert_array_equal(parsed['bucket_b2'], np.arange(8)/16)
            loaded=self.model(); training.load_initial(loaded,stem.with_suffix('.inc'))
            torch.testing.assert_close(loaded.output.bias,model.output.bias,rtol=0,atol=0)
            self.assertTrue(metadata['residual']); self.assertEqual(metadata['output_buckets'],8)
            with self.assertRaises(FileExistsError): training.export_bucketed(model,stem)

    def test_export_rejects_nonfinite_and_saturation(self):
        model=self.model()
        with tempfile.TemporaryDirectory() as temp:
            for value in [float('nan'),float('inf'),10.0]:
                with torch.no_grad(): model.output.bias[0]=value
                with self.subTest(value=value), self.assertRaises((ValueError,RuntimeError)):
                    training.export_bucketed(model,Path(temp)/'bad')

    def test_prepared_guard_rejects_audit_role_and_game_overlap(self):
        self.model()
        base={'schema_version':1,'hidden_size':128,'score_pov':'side_to_move','result_pov':'side_to_move',
              'dataset_role':'training_and_selection','training_permitted':True,'status':'QUALIFIED_FROZEN',
              'minimum_positions':5000000,'retained_total_positions':5000000,
              'split':{'train_game_ids':['a'],'validation_game_ids':['b'],'legacy_training_game_ids_unknown':False}}
        training.validate_training_manifest(base)
        for changed in [dict(base,dataset_role='final_audit_only'),dict(base,training_permitted=False),
                        dict(base,split={**base['split'],'validation_game_ids':['a']})]:
            with self.assertRaises(ValueError): training.validate_training_manifest(changed)

    def test_sparse_features_reject_duplicates_and_preserve_counts(self):
        self.model()
        indices=np.full((1,2,32),-1,dtype=np.int16);indices[:,:,:2]=[0,64]
        dense=training.dense_features(indices)
        self.assertEqual(training.bucket_indices(dense).tolist(),[0])
        indices[:,:,1]=0
        with self.assertRaises(ValueError): training.dense_features(indices)

    def test_validation_uses_engine_integer_cp_and_restores_mode(self):
        model=self.model();model.train()
        with torch.no_grad():
            model.ft.weight.zero_();model.ft.bias.zero_();model.output.weight.zero_();model.output.bias.fill_(.009)
        indices=np.full((2,2,32),-1,dtype=np.int16);indices[:,:,:2]=[0,64]
        arrays={'features':indices,'hce':np.zeros(2,np.int32),'score':np.ones(2,np.int32),'result_stm':np.zeros(2,np.float32)}
        self.assertEqual(training.evaluate(model,arrays,2,0.),0.)
        self.assertTrue(model.training)

    def test_bucket_parser_rejects_duplicate_or_unsupported_bucket_flags(self):
        model=self.model()
        with tempfile.TemporaryDirectory() as temp:
            stem=Path(temp)/'base';training.export_bucketed(model,stem);text=stem.with_suffix('.inc').read_text()
            for i,changed in enumerate([text+'\n#define FORGE_NNUE_OUTPUT_BUCKETS 8\n',
                    text.replace('FORGE_NNUE_OUTPUT_BUCKETS 8','FORGE_NNUE_OUTPUT_BUCKETS 4'),
                    text.replace('NnueB2[8]','NnueB2[7]')]):
                p=Path(temp)/f'bad{i}.inc';p.write_text(changed)
                with self.assertRaises(ValueError):load_include(p)

    def test_cli_rejects_old_single_head_protocol_before_reading_data(self):
        self.model()
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);protocol=root/'protocol.json';out=root/'run'
            protocol.write_text(json.dumps({'schema_version':1,'target':{'kind':'teacher_probability_game_result_blend',
                'result_weight':.4,'sigmoid_k':2.25,'cp_scale':400.},'dataset_manifest_sha256':'a'*64,
                'training':{'epochs':8,'output_buckets':1,'selection_metric':'target_mse_combined','include_initial':False}}))
            with self.assertRaises(ValueError):training.main(['--data-dir',str(root/'missing-data'),
                '--manifest-sha256','a'*64,'--initial-net',str(root/'missing.inc'),'--protocol',str(protocol),'--out',str(out)])
            self.assertFalse(out.exists())

    def test_protocol_binds_all_training_parameters_and_initial_net(self):
        self.model()
        initial=TOOLS.parents[1]/'src/nnue_weights.inc'
        args=SimpleNamespace(result_weight=.4,manifest_sha256='a'*64,epochs=8,seed=20261023,
            batch_size=1024,threads=4,lr=.0003,min_lr=.000003,initial_net=str(initial))
        policy={'epochs':8,'output_buckets':8,'selection_metric':'target_mse_combined','include_initial':False,
            'seed':args.seed,'batch_size':1024,'threads':4,'lr':args.lr,'min_lr':args.min_lr,
            'schedule':'cosine','initial_net_sha256':training.sha256(initial)}
        protocol={'schema_version':1,'target':{'kind':'teacher_probability_game_result_blend','result_weight':.4,
            'sigmoid_k':2.25,'cp_scale':400.},'dataset_manifest_sha256':'a'*64,'training':policy}
        self.assertTrue(hasattr(training,'validate_training_protocol'),'Protocol must bind every effective setting')
        training.validate_training_protocol(protocol,args)
        for name,bad in [('seed',0),('lr',.01),('min_lr',.00002),('batch_size',32),('threads',1),
                         ('schedule','constant'),('initial_net_sha256','0'*64)]:
            with self.subTest(parameter=name), self.assertRaises(ValueError):
                training.validate_training_protocol({**protocol,'training':{**policy,name:bad}},args)

    def test_legacy_parser_rejects_scalar_plus_array_duplicate_bias(self):
        self.model()
        from train_nnue import NNUE,export_forge
        with tempfile.TemporaryDirectory() as temp:
            stem=Path(temp)/'legacy';export_forge(NNUE([128]),stem,2.25,residual=True)
            p=stem.with_suffix('.inc');p.write_text(p.read_text()+'\nstatic const std::int16_t NnueB2[1] = {0};\n')
            with self.assertRaises(ValueError):load_include(p)

if __name__ == '__main__': unittest.main()
