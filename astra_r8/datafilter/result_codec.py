"""Versioned REC outcome bytes; scores retain their existing White POV. UNPROVEN."""
from numbers import Integral


def encode_result(has_result, result_stm):
    """Return bytes 29..31: mask, STM loss/draw/win=0/1/2, schema=1."""
    if not isinstance(has_result, Integral) or has_result not in (0, 1):
        raise ValueError('invalid result mask')
    if not has_result:
        if result_stm is not None:
            raise ValueError('unknown result must be null')
        return (0, 0, 1)
    if not isinstance(result_stm, Integral) or isinstance(result_stm, bool) or result_stm not in (-1, 0, 1):
        raise ValueError('invalid STM result')
    return (1, int(result_stm) + 1, 1)


def decode_result(reserved, stm):
    """Decode signed STM WDL; schema 0 is historical White POV, 1 is STM."""
    values = tuple(reserved)
    if len(values) != 3 or any(not isinstance(v, Integral) for v in (*values, stm)):
        raise ValueError('invalid result bytes')
    mask, code, version = values
    if stm not in (0, 1) or mask not in (0, 1) or code not in (0, 1, 2) or version not in (0, 1):
        raise ValueError('invalid result bytes or unsupported schema')
    if not mask:
        if code != 0:
            raise ValueError('unknown result has nonzero payload')
        return None
    result = int(code) - 1
    return -result if version == 0 and stm == 1 else result
