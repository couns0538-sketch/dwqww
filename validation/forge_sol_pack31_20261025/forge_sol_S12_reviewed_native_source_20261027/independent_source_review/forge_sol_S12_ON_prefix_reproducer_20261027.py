"""Intentional pure RED: synthetic stdout only, never native bench evidence."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
sys.path.insert(0,"/tmp/forge_sol_S12_native_prep_20261027")
import forge_sol_S12_feature_qualify_20261027 as feature
p=Path(__file__).with_name("forge_sol_S12_synthetic_ON_bench_fixture_20261027.txt")
text=p.read_text();lines=text.splitlines()
diagnostics=feature.diagnostics(lines,1,8)
result=feature.binding.qual.q.s25.inspect_bench(text.encode(),b"",0,11,308972)
print(json.dumps({"scope":"SYNTHETIC_PURE_OBSERVER_REPRODUCER_NOT_NATIVE","feature_source":feature.__file__,"feature_sha256":hashlib.sha256(Path(feature.__file__).read_bytes()).hexdigest(),"fixture_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"expected_diagnostics_pass":diagnostics,"strict_normal_bench_parser_result":result}),flush=True)
assert result["status"]=="PASS","Current ON qualifier falsely rejects its required active+stats prefix"
