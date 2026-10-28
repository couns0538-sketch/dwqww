"""Compare the Fable re-run of S19 step 3 (result.json) with the numbers in Opus's REPORT.md / step3 log."""
import json, sys
r = json.load(open('F:/opus_scratch/fable_review/s19/result.json', encoding='utf-8'))
# Opus, opus-sol-S19 REPORT.md section 3 (fit 003+007, holdout 013+014, stride 5, bootstrap 50)
opus = {
    'phases': [  # label, fit rows, holdout rows, fitted k, ci lo, ci hi, table k, ll ref, ll table
        ('0-3', 652152, 510818, 2.2396, 2.2312, 2.2455, 2.2396, 0.377257, 0.377312),
        ('4-7', 1107257, 894624, 2.7602, 2.7537, 2.7690, 2.7602, 0.350309, 0.345992),
        ('8-11', 467405, 388563, 3.3302, 3.3157, 3.3431, 3.3302, 0.386625, 0.372731),
        ('12-15', 326865, 273235, 3.4559, 3.4329, 3.4782, 3.4559, 0.426298, 0.411517),
        ('16-19', 317824, 266822, 3.3261, 3.3082, 3.3437, 3.3261, 0.420836, 0.407850),
        ('20-24', 1128497, 943653, 3.3615, 3.3524, 3.3707, 3.3615, 0.571497, 0.562828),
    ],
    'global_k': 2.9255, 'global_ci': (2.9223, 2.9292),
    'holdout_rows': 3277715, 'll_ref': 0.434570, 'll_global': 0.428393, 'll_table': 0.426968, 'delta': -0.007602,
}
worst = 0.0
rows_ok = True
pt = r['phase_table']
assert len(pt) == 6, len(pt)
for e, o in zip(pt, opus['phases']):
    keys = [k for k in e if 'rows' in k]
    fit_rows = e.get('fit_rows', e.get('rows'))
    hold_rows = e.get('holdout_rows')
    d = [abs(e['fitted_k'] - o[3]), abs(e['fitted_k_ci95'][0] - o[4]) if 'fitted_k_ci95' in e else 0.0,
         abs(e['fitted_k_ci95'][1] - o[5]) if 'fitted_k_ci95' in e else 0.0, abs(e['k'] - o[6]),
         abs(e['holdout_logloss_reference'] - o[7]), abs(e['holdout_logloss_table'] - o[8])]
    worst = max(worst, max(d))
    same_rows = (fit_rows == o[1]) and (hold_rows in (o[2], None))
    rows_ok &= same_rows
    print(f"phase {o[0]:>5}: fit_rows {fit_rows} (opus {o[1]}) holdout_rows {hold_rows} (opus {o[2]}) "
          f"k {e['fitted_k']:.4f} (opus {o[3]}) ll_ref {e['holdout_logloss_reference']:.6f} ll_table {e['holdout_logloss_table']:.6f} max|diff| {max(d):.2e}")
h = r['holdout']
dg = [abs(r['global_k'] - opus['global_k']), abs(r['global_k_ci95'][0] - opus['global_ci'][0]), abs(r['global_k_ci95'][1] - opus['global_ci'][1]),
      abs(h['logloss_reference_k2.25'] - opus['ll_ref']), abs(h['logloss_global_k'] - opus['ll_global']),
      abs(h['logloss_per_phase_table'] - opus['ll_table']), abs(h['table_minus_reference'] - opus['delta'])]
worst = max(worst, max(dg))
print(f"global k {r['global_k']:.4f} CI [{r['global_k_ci95'][0]:.4f}, {r['global_k_ci95'][1]:.4f}] (opus 2.9255 [2.9223, 2.9292])")
print(f"holdout rows {h['rows']} (opus 3277715); ll k=2.25 {h['logloss_reference_k2.25']:.6f} global {h['logloss_global_k']:.6f} "
      f"table {h['logloss_per_phase_table']:.6f} delta {h['table_minus_reference']:+.6f}")
print(f"bootstrap: {r['bootstrap_unit']} x {r['bootstrap_samples']}; label {r.get('label')!r}")
print(f"rows identical: {rows_ok and h['rows'] == opus['holdout_rows']}; max |printed - rerun| over all numbers: {worst:.2e} "
      f"({'within print rounding (<=5e-5 / 5e-7)' if worst <= 5e-5 else 'DIFFERS'})")
