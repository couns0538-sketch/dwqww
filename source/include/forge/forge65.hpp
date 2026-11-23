#pragma once

// forge6.5 play build (forge/r65/R65_NOTE.txt). Used only when the build sets -DFORGE65=1: the net lies inside the
// exe and the loop's settings are applied at the start, so a chess program has nothing to set. With the switch off
// (the default) nothing of this is compiled and the tree is forge/r15dsg.

#include <cstddef>
#include <cstdint>
#include <string>

namespace forge::forge65 {

// The NNUEArchFile value that names the net compiled into the exe.
inline constexpr const char* NetPath = "<forge65>";

[[nodiscard]] const std::uint8_t* net_data();
[[nodiscard]] std::size_t net_size();

// Hands out the start-up lines one by one (`index` counts up); false when none is left.
[[nodiscard]] bool startup_line(std::size_t& index, std::string& line);

}  // namespace forge::forge65
