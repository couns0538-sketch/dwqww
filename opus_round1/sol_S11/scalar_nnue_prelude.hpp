// Test-only forced include (-include) for build_pc_scalar_nnue.sh; never part of an engine build.
// MinGW-w64 (_mingw_mac.h) defines _M_X64 and _M_AMD64 on x86-64, so src/nnue.cpp's
// `#if defined(__SSE__) || defined(_M_X64) || defined(_M_AMD64)` selects the SSE output layer even
// with -U__SSE__. Include the standard headers nnue.cpp uses first (their include guards keep later
// includes from redefining the macros), then undefine the two macros: nnue.cpp then compiles its
// portable scalar branch. GCC on Linux needs only -U__SSE__ (no _M_X64 there).
#include <algorithm>
#include <array>
#include <bit>
#include <cassert>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <vector>
#undef _M_X64
#undef _M_AMD64
