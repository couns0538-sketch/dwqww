"""Independent literal expectations for versioned result bytes. UNPROVEN."""
import pytest
from result_codec import encode_result, decode_result


@pytest.mark.parametrize('turn,white,stm,code', [
    (0,-1,-1,0),(0,0,0,1),(0,1,1,2),
    (1,-1,1,2),(1,0,0,1),(1,1,-1,0),
    (0,None,None,0),(1,None,None,0),
])
def test_stm_and_legacy_oracle(turn,white,stm,code):
    mask = int(white is not None)
    assert encode_result(mask,stm) == (mask,code,1)
    assert decode_result((mask,code,1),turn) == stm
    old = (mask,0 if white is None else white+1,0)
    assert decode_result(old,turn) == stm
    # Color-swapped board and outcome preserve the STM result.
    assert decode_result((mask,code,1),1-turn) == stm


@pytest.mark.parametrize('reserved,turn', [
    ((1,2,2),0),((2,1,1),0),((1,3,1),0),((0,1,1),0),
    ((0,2,0),1),((1,0,1),2),((1,0),0),
])
def test_invalid_record_result_rejected(reserved,turn):
    with pytest.raises(ValueError): decode_result(reserved,turn)


@pytest.mark.parametrize('mask,value', [(0,0),(1,None),(1,2),(2,0),(1,0.5)])
def test_invalid_semantic_result_rejected(mask,value):
    with pytest.raises(ValueError): encode_result(mask,value)
