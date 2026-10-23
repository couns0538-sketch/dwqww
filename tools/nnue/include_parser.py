"""Read Forge's existing int16 include format without executing C++ or Python."""
from __future__ import annotations

import hashlib
from pathlib import Path
import re

import numpy as np


def _array(text: str, name: str) -> np.ndarray:
    declarations = re.findall(
        rf"\bstatic\s+const\s+std::int16_t\s+{name}\s*\[\s*(\d+)\s*\]\s*=\s*\{{(.*?)\}}\s*;",
        text, re.DOTALL)
    if len(declarations) != 1:
        raise ValueError(f"Expected exactly one {name} array")
    count_text, body = declarations[0]
    tokens = [token.strip() for token in body.split(",")]
    if tokens and not tokens[-1]:
        tokens.pop()
    if not tokens or any(not re.fullmatch(r"[+-]?\d+", token) for token in tokens):
        raise ValueError(f"Invalid integer list for {name}")
    values = [int(token) for token in tokens]
    if len(values) != int(count_text):
        raise ValueError(f"Declared and actual lengths differ for {name}")
    if any(value < -32768 or value > 32767 for value in values):
        raise ValueError(f"Out-of-range int16 value in {name}")
    return np.asarray(values, dtype=np.int16)


def load_include(path, expected_hidden=None):
    """Return dequantized feature-major arrays and the declared evaluation mode.

    The no-flag legacy format is standalone, matching nnue.cpp. This function
    only reads the fixed Forge format; it never interprets arbitrary C++.
    """
    path = Path(path)
    original = path.read_bytes()
    text = original.decode("ascii")
    flags = re.findall(r"^\s*#\s*define\s+FORGE_NNUE_RESIDUAL\b([^\n]*)", text, re.MULTILINE)
    if len(flags) > 1:
        raise ValueError("Duplicate residual-mode definitions")
    if flags:
        flag = flags[0].split("//", 1)[0].strip()
        if flag not in ("0", "1"):
            raise ValueError("Residual mode must be 0 or 1")
        residual = flag == "1"
    else:
        residual = False
    arrays = {name: _array(text, name) for name in ("NnueW1", "NnueB1", "NnueW2")}
    hidden = len(arrays["NnueB1"])
    if hidden <= 0 or hidden % 16:
        raise ValueError("Hidden width must be a positive multiple of 16")
    if expected_hidden is not None and hidden != expected_hidden:
        raise ValueError("Include hidden width differs from the requested model")
    if len(arrays["NnueW1"]) != 768 * hidden or len(arrays["NnueW2"]) != 2 * hidden:
        raise ValueError("Include dimensions differ from the Forge architecture")
    biases = re.findall(r"\bstatic\s+const\s+std::int16_t\s+NnueB2\s*=\s*([+-]?\d+)\s*;", text)
    if len(biases) != 1 or not -32768 <= int(biases[0]) <= 32767:
        raise ValueError("Expected exactly one int16 NnueB2 scalar")
    scale = np.float32(4096.0)
    return {
        "hidden": hidden,
        "residual": residual,
        "w1": (arrays["NnueW1"].astype(np.float32) / scale).reshape(768, hidden),
        "b1": arrays["NnueB1"].astype(np.float32) / scale,
        "w2": arrays["NnueW2"].astype(np.float32) / scale,
        "b2": float(np.float32(int(biases[0])) / scale),
        "sha256": hashlib.sha256(original).hexdigest(),
        "quantization_scales": {"weight": 4096.0, "output": 4096.0},
    }
