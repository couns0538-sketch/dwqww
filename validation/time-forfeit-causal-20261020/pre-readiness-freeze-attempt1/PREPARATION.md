# Baseline time-forfeit phase diagnostic

Prepared from frozen6.4.11 sourcec5cbf97, independent of the new engine candidate.
The diagnostic changes only telemetry and compiles in a new source/build tree.
No diagnostic engine has executed. An explicit root resource-clearance JSON,
bound to the frozen PROTOCOL.json SHA256, is required before one cold→warm run.

The original preparation placed info-output markers in a restricted-root block
where nodes/depth/elapsed were out of scope. Syntax RED is retained under
pre-build-attempt0/. The corrected source-v2 puts those markers in the actual
completed-iteration emit lambda and passes syntax plus full engine compilation.
No production file changed. BUILD.json records exact source/binary/core hashes.

Independent runner review identified missing cleanup of a surviving owned
process group after its leader exits, premature completion marking, and omission
of original forfeit-exchange.json from frozen inputs. Original copies and real
process RED/GREEN contract evidence are retained. These are diagnostic harness
repairs, not engine or match retries. Runtime readiness requires their final
contract receipt as well as the root's idle-resource check.

Execution, once cleared:

```sh
/workspace/.cloud-setup/venv/bin/python -B \
  validation/time-forfeit-causal-20261020/run_diagnostic.py \
  --engine /workspace/.cloud-setup/forge-forfeit-causal-build-v2/forge \
  --out validation/time-forfeit-causal-20261020/diagnostic-attempt1 \
  --clearance validation/time-forfeit-causal-20261020/ROOT-CLEARANCE.json
```

Then run analyze_diagnostic.py --out against that directory only after a complete
capture. Keep incomplete attempts. The fixed historical clocks do not define new
tournament games; no PGN is reconstructed and no Elo or speed is claimed.
