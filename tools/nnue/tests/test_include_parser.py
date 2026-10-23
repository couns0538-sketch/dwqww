"""Format guards for the legacy-compatible read-only Forge include reader."""
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from include_parser import load_include


def include_text(hidden=16):
    w1 = [0] * (768 * hidden)
    w1[hidden + 2] = 4096
    w1[-1] = -32768
    b1, w2 = [0] * hidden, [0] * (2 * hidden)
    b1[0], w2[0], w2[hidden] = 4096, 8192, -4096
    lines = ["#define FORGE_NNUE_RESIDUAL 1"]
    for name, values in [("NnueW1", w1), ("NnueB1", b1), ("NnueW2", w2)]:
        lines.append(f"static const std::int16_t {name}[{len(values)}] = {{" + ",".join(map(str, values)) + ",};")
    lines.append("static const std::int16_t NnueB2 = -2048;")
    return "\n".join(lines)


class IncludeParserTests(unittest.TestCase):
    def read(self, text, **kwargs):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "weights.inc"
            path.write_text(text, encoding="ascii")
            return load_include(path, **kwargs)

    def test_feature_major_shape_and_exact_dequantization(self):
        data = self.read(include_text(), expected_hidden=16)
        self.assertEqual(data["w1"].shape, (768, 16))
        self.assertEqual(data["w1"].dtype, np.float32)
        self.assertEqual(data["w1"][1, 2], 1.0)
        self.assertEqual(data["w1"][-1, -1], -8.0)
        self.assertEqual(data["b1"][0], 1.0)
        self.assertEqual(data["w2"][[0, 16]].tolist(), [2.0, -1.0])
        self.assertEqual(data["b2"], -0.5)
        self.assertIs(data["residual"], True)

    def test_legacy_include_without_flag_is_standalone(self):
        data = self.read(include_text().replace("#define FORGE_NNUE_RESIDUAL 1\n", ""))
        self.assertIs(data["residual"], False)

    def test_mode_must_be_unique_boolean(self):
        for text in [include_text().replace("RESIDUAL 1", "RESIDUAL 2"),
                     include_text() + "\n#define FORGE_NNUE_RESIDUAL 1"]:
            with self.subTest(text=text[-50:]), self.assertRaises(ValueError):
                self.read(text)

    def test_requested_and_lane_widths_must_match(self):
        with self.assertRaises(ValueError):
            self.read(include_text(), expected_hidden=32)
        with self.assertRaises(ValueError):
            self.read(include_text(15))

    def test_array_length_is_not_silently_padded(self):
        with self.assertRaises(ValueError):
            self.read(include_text().replace("NnueB1[16]", "NnueB1[17]"))

    def test_noninteger_and_overflow_are_rejected(self):
        for text in [include_text().replace("4096,", "nan,", 1),
                     include_text().replace("-32768,", "32768,", 1)]:
            with self.subTest(text=text[:80]), self.assertRaises(ValueError):
                self.read(text)

    def test_scalar_and_array_declarations_must_be_unique(self):
        for suffix in ["\nstatic const std::int16_t NnueB2 = 0;",
                       "\nstatic const std::int16_t NnueB1[16] = {" + "0," * 16 + "};"]:
            with self.subTest(suffix=suffix[:40]), self.assertRaises(ValueError):
                self.read(include_text() + suffix)


if __name__ == "__main__":
    unittest.main(verbosity=2)
