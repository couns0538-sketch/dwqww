"""Write a NEW handoff manifest whose runtime pin matches the current adapter and npt install.
Payload, source, holdout and clearance pins are copied unchanged and re-verified. Never trains. UNPROVEN."""
import argparse
import json
import os
from pathlib import Path
import sys
if __name__ == '__main__' and '--npt-root' in sys.argv[:-1]:
    os.environ['ASTRA_NPT_ROOT'] = sys.argv[sys.argv.index('--npt-root') + 1]
    os.environ['NNUE_DATA_LOADER_LIB'] = os.path.join(os.environ['ASTRA_NPT_ROOT'], 'build', 'libtraining_data_loader.dll')
from filter_positions import sha256, low_priority
from npt_adapter import runtime_identity, NPT
import train  # same trainer modules as train_adapter imports, so the identity matches at run time
from verify_handoff import verify

def rebind(old, new):
    old, new = Path(old), Path(new)
    if new.exists():
        raise FileExistsError(new)
    m = json.loads(old.read_text(encoding='utf-8'))
    m['runtime'] = runtime_identity()
    m['npt_root'] = str(NPT)
    m['derived_from'] = dict(path=str(old.resolve()), sha256=sha256(old), change='runtime re-pin after QA datafilter fixes')
    hp = dict(m.get('hyperparameters', {}))
    for key in ('seed', 'epoch_size', 'epochs'):
        hp[key] = 'per-run CLI (QA fix 2)'
    m['hyperparameters'] = hp
    with open(new, 'x', encoding='utf-8') as fh:
        json.dump(m, fh, indent=2)
    return verify(new)

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('old'); p.add_argument('new'); p.add_argument('--npt-root')
    a = p.parse_args(); low_priority()
    print(json.dumps(rebind(a.old, a.new), indent=2))
