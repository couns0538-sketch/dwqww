"""Synthetic provenance controls; no reconstructed gate matches."""
import copy
import unittest
import forge_sol_S48_gate_guard_20261026 as s48
from forge_sol_S48_gate_guard_20261026 import comparability

def synthetic_gate(gate='SYNTHETIC'):
    return {'gate':gate,'concurrency':5,'tc':'10+0.1','book_sha256':'a'*64,
            'opponent_exe_sha256':'b'*64,'core_mask':[4,5,6,7,8]}

class Comparability(unittest.TestCase):
    def test_equal_fully_pinned_required_fields(self):
        r=comparability(synthetic_gate('A'),synthetic_gate('B'))
        self.assertTrue(r['can_compare'])
        self.assertTrue(r['advice_only'])
        self.assertFalse(r['acceptance_authorized'])
    def test_G120_conc7_G104_conc5_blocked_even_same_other_fields(self):
        a=synthetic_gate('G120');a['concurrency']=7
        r=comparability(a,synthetic_gate('G104'))
        self.assertFalse(r['can_compare'])
        self.assertIn('concurrency',[x['field'] for x in r['mismatches']])
    def test_each_required_difference_blocks(self):
        for field,value in [('concurrency',8),('tc','5+0.05'),('book_sha256','c'*64),
                            ('opponent_exe_sha256','d'*64),('core_mask',[9,10,11,12,13])]:
            with self.subTest(field=field):
                b=synthetic_gate('B');b[field]=value
                r=comparability(synthetic_gate('A'),b)
                self.assertFalse(r['can_compare'])
                self.assertIn(field,[x['field'] for x in r['mismatches']])
    def test_missing_both_is_unknown_not_equality(self):
        a=synthetic_gate();del a['book_sha256']
        r=comparability(a,copy.deepcopy(a))
        self.assertFalse(r['can_compare'])
        self.assertEqual(sum(x['field']=='book_sha256' for x in r['unknown']),2)
    def test_invalid_provenance_rejected(self):
        for field,value in [('concurrency',True),('concurrency',0),('concurrency',9),('concurrency','5'),
                            ('book_sha256','short'),('opponent_exe_sha256','g'*64),
                            ('core_mask',[]),('core_mask',[1,1]),('core_mask',[-1,2]),
                            ('core_mask',[True,2]),('core_mask','4-8'),('tc','')]:
            with self.subTest(field=field,value=value):
                b=synthetic_gate();b[field]=value
                r=comparability(synthetic_gate(),b)
                self.assertFalse(r['can_compare'])
                self.assertIn(field,[x['field'] for x in r['unknown']])
    def test_only_equivalent_hash_spelling_and_core_order_normalized(self):
        b=synthetic_gate();b['book_sha256']='A'*64;b['core_mask']=list(reversed(b['core_mask']))
        self.assertTrue(comparability(synthetic_gate(),b)['can_compare'])
    def test_optional_settings_mismatch_or_one_missing_blocks(self):
        for field,a_value,b_value in [('threads',1,2),('hash_mb',16,32),
                                     ('engine_options',{'OwnBook':False},{'OwnBook':True}),
                                     ('engine_options',{'Flag':True},{'Flag':1})]:
            with self.subTest(field=field):
                a=synthetic_gate();b=synthetic_gate();a[field]=a_value;b[field]=b_value
                self.assertFalse(comparability(a,b)['can_compare'])
                del b[field]
                self.assertFalse(comparability(a,b)['can_compare'])
    def test_no_silent_mutation(self):
        a=synthetic_gate('A');b=synthetic_gate('B');before=copy.deepcopy([a,b])
        comparability(a,b)
        self.assertEqual([a,b],before)

class SelectionBias(unittest.TestCase):
    def test_conditional_bias_does_not_pool_h0_and_cap(self):
        f=getattr(s48,'selection_bias',None)
        self.assertTrue(callable(f),'selection-bias implementation missing')
        r=f({'outcome':['H1','H1','H1','H0','cap'],'terminal_elo':[10,20,30,-900,999]},10,observed_elo=40)
        self.assertEqual(r['selected_replicates'],3)
        self.assertAlmostEqual(r['conditional_mean_elo'],20)
        self.assertAlmostEqual(r['bias_estimate'],10)
        self.assertAlmostEqual(r['bias_mc_standard_error'],(100/3)**.5)
        self.assertAlmostEqual(r['adjusted_elo_assuming_model'],30)
        self.assertIsNone(r['corrected_observation_ci95'])
        self.assertFalse(r['acceptance_authorized'])
    def test_infinite_selected_estimates_cannot_be_discarded(self):
        f=getattr(s48,'selection_bias',None);self.assertTrue(callable(f))
        r=f({'outcome':['H1','H1'],'terminal_elo':[10,float('inf')]},10,observed_elo=20)
        self.assertEqual(r['status'],'UNVERIFIED_NONFINITE_SELECTED_ESTIMATES')
        self.assertIsNone(r['bias_estimate'])
        self.assertEqual(r['nonfinite_selected'],1)
    def test_empty_selection_unknown_not_zero_bias(self):
        f=getattr(s48,'selection_bias',None);self.assertTrue(callable(f))
        r=f({'outcome':['cap'],'terminal_elo':[10]},10)
        self.assertIsNone(r['bias_estimate'])
        self.assertEqual(r['selected_replicates'],0)
    def test_invalid_samples_rejected(self):
        f=getattr(s48,'selection_bias',None);self.assertTrue(callable(f))
        for samples in ({'outcome':['H1'],'terminal_elo':[]},
                        {'outcome':['unknown'],'terminal_elo':[1]}):
            with self.subTest(samples=samples),self.assertRaises(ValueError):f(samples,10)
    def test_g104_missing_profile_cannot_invent_corrected_elo(self):
        f=getattr(s48,'simulate_gate_bias',None);self.assertTrue(callable(f))
        r=f({'gate':'G104','concurrency':5,'observed_elo':29.44,'selection':'H1'},profile=None)
        self.assertEqual(r['status'],'UNVERIFIED_MISSING_PAIRED_PROFILE')
        self.assertIsNone(r['adjusted_elo_assuming_model'])
    def test_profile_from_other_concurrency_cannot_be_borrowed(self):
        f=getattr(s48,'simulate_gate_bias',None);self.assertTrue(callable(f))
        with self.assertRaises(ValueError):
            f({'gate':'G120','concurrency':7,'observed_elo':23.62,'selection':'H1'},profile={'counts':[1,2,3,4,5],'concurrency':5})
    def test_boolean_profile_concurrency_is_not_integer_one(self):
        f=getattr(s48,'simulate_gate_bias',None);self.assertTrue(callable(f))
        with self.assertRaises(ValueError):
            f({'gate':'SYNTHETIC','concurrency':1,'observed_elo':10,'selection':'H1'},profile={'counts':[1,2,3,4,5],'concurrency':True},runs=4)
    def test_real_simulation_api_smoke_is_only_synthetic(self):
        f=getattr(s48,'simulate_gate_bias',None);self.assertTrue(callable(f))
        r=f({'gate':'SYNTHETIC_API','concurrency':5,'observed_elo':10,'selection':'cap','cap_games':20},
            profile={'counts':[1,2,3,4,5],'concurrency':5,'provenance':'SYNTHETIC'},runs=4,seed=48)
        self.assertEqual(r['simulation']['runs'],4)
        self.assertEqual(r['selection'],'cap')
        self.assertEqual(r['concurrency'],5)
        self.assertFalse(r['acceptance_authorized'])

if __name__=='__main__':unittest.main()
