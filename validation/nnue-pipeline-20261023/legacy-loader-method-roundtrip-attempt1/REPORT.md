# Legacy C++ loader API round-trip

PASS: the actual unchanged trainer source was included in an external C++20 wrapper. Its existing Network::load, Network::save and write_include methods were called directly; the original CLI main and all optimizer/training code were not invoked.

Float binary: 394756 bytes, byte exact=True. Quantized parameters: 98689 total; exact arrays=True. Hidden width: 128; residual flags: True/True.

Compiler/run commands, original stdout/stderr/exit codes, source/core/input identities and output hashes are retained here. The immutable core was linked without rebuilding it; all retained inputs were rehashed after execution. This verifies API format interoperability, not CLI zero-epoch export support, native evaluation parity, heldout loss or Elo. The separate legacy-loader-zero-epoch-inspection checkpoint remains valid.
