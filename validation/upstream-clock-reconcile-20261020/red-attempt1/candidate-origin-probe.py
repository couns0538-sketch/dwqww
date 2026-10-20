import hashlib, json, pathlib, runpy, sys
binary, shim, probe, out = map(pathlib.Path, sys.argv[1:])
out.mkdir(exist_ok=False)
ns = runpy.run_path(str(probe), run_name='accepted_clock_probe')
results = [ns['run_trial'](binary, shim, 'candidate_timed', 'go movetime 1200', out, 440),
           ns['run_trial'](binary, shim, 'candidate_depth', 'go depth 1', out, 440)]
checks = {'timed_origin': results[0]['first_info_time_ms'] >= 380,
          'analysis_origin': results[1]['first_info_time_ms'] < 220}
summary = {'status': 'PASS' if all(checks.values()) else 'INCONCLUSIVE_OR_FAIL',
           'scope': 'candidate-side origin checks from unchanged accepted probe; not full baseline comparison',
           'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
           'checks': checks, 'results': results}
(out/'result.json').write_text(json.dumps(summary, indent=2)+'\n')
print(json.dumps(summary, indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
