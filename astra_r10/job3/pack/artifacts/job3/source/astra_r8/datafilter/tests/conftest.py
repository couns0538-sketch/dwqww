import json
import os
from pathlib import Path
import sys
import time
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

@pytest.fixture(scope='session',autouse=True)
def pin_cpu_runtime():
    import npt_adapter
    import train
    npt_adapter.torch.set_num_threads(1)
    before=npt_adapter.runtime_identity()
    yield
    after=npt_adapter.runtime_identity()
    assert all(after['files'].get(p)==digest for p,digest in before['files'].items()),'runtime changed during tests'
    output=Path('D:/grok-pc-data/dwqww/astra8_data')/f'cpu_runtime_{time.time_ns()}.json'
    with output.open('x',encoding='utf-8') as fh:
        json.dump({'before':before,'after':after},fh,indent=2)
