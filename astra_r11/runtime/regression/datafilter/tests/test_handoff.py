import json
import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

def test_payload_count_and_hash_fail_closed(tmp_path):
    from verify_handoff import verify_payload
    from filter_positions import sha256
    p=tmp_path/'sample.jsonl'; p.write_bytes(b'{}\n{}\n')
    item={'path':str(p),'sha256':sha256(p),'rows':2}
    assert verify_payload(item)==2
    with pytest.raises(ValueError,match='count'):
        verify_payload(dict(item,rows=3))
    p.write_bytes(b'{}\n')
    with pytest.raises(ValueError,match='hash'):
        verify_payload(item)
