#pragma once

#include <mutex>

namespace forge {

inline std::mutex& uci_output_mutex() {
    static std::mutex mutex;
    return mutex;
}

} // namespace forge
