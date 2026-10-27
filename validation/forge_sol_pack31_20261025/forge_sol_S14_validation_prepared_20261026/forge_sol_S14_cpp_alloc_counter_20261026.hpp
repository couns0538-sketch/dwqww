#pragma once
// Diagnostic-only replacements in ONE driver TU; never part of the engine.
// Counts C++ allocation entry calls on this thread, not direct C malloc family.
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <new>
#include <stdexcept>
#ifdef _WIN32
#include <malloc.h>
#endif

namespace forge_s14_alloc {
struct Stats { std::uint64_t calls = 0, bytes = 0; bool overflow = false; };
inline thread_local bool enabled = false;
inline thread_local bool disabled_control = false;
inline thread_local Stats current{};
inline thread_local std::uint64_t windows = 0;
inline void* volatile escaped_pointer = nullptr;

inline void observe(std::size_t size) noexcept {
    if (!enabled || disabled_control) return;
    if (current.calls == std::numeric_limits<std::uint64_t>::max() ||
        size > std::numeric_limits<std::uint64_t>::max() - current.bytes) {
        current.overflow = true;
        return;
    }
    ++current.calls;
    current.bytes += size;
}

struct Window {
    Stats& out;
    explicit Window(Stats& target) : out(target) {
        if (enabled) std::abort(); // Nested counters are a diagnostic error.
        current = {};
        ++windows;
        enabled = true;
    }
    ~Window() { out = current; enabled = false; }
    Window(const Window&) = delete;
    Window& operator=(const Window&) = delete;
};

inline void* allocate(std::size_t size) {
    observe(size);
    void* p = std::malloc(size == 0 ? 1 : size);
    if (p == nullptr) throw std::bad_alloc();
    return p;
}

inline void* allocate_aligned(std::size_t size, std::size_t alignment) {
    observe(size);
    if (alignment == 0 || (alignment & (alignment - 1)) != 0) throw std::bad_alloc();
    if (alignment < alignof(void*)) alignment = alignof(void*);
    void* p = nullptr;
#ifdef _WIN32
    p = _aligned_malloc(size == 0 ? 1 : size, alignment);
#else
    if (posix_memalign(&p, alignment, size == 0 ? 1 : size) != 0) p = nullptr;
#endif
    if (p == nullptr) throw std::bad_alloc();
    return p;
}

inline void free_aligned(void* p) noexcept {
#ifdef _WIN32
    _aligned_free(p);
#else
    std::free(p);
#endif
}

#if defined(__GNUC__) || defined(__clang__)
__attribute__((noinline))
#endif
inline void escape(void* p) noexcept {
    escaped_pointer = p;
#if defined(__GNUC__) || defined(__clang__)
    asm volatile("" : : "g"(p) : "memory");
#endif
    if (p != nullptr) static_cast<volatile unsigned char*>(p)[0] = 0x5a;
}
}

void* operator new(std::size_t n) { return forge_s14_alloc::allocate(n); }
void* operator new[](std::size_t n) { return forge_s14_alloc::allocate(n); }
void* operator new(std::size_t n, const std::nothrow_t&) noexcept {
    try { return forge_s14_alloc::allocate(n); } catch (...) { return nullptr; }
}
void* operator new[](std::size_t n, const std::nothrow_t&) noexcept {
    try { return forge_s14_alloc::allocate(n); } catch (...) { return nullptr; }
}
void* operator new(std::size_t n, std::align_val_t a) { return forge_s14_alloc::allocate_aligned(n, static_cast<std::size_t>(a)); }
void* operator new[](std::size_t n, std::align_val_t a) { return forge_s14_alloc::allocate_aligned(n, static_cast<std::size_t>(a)); }
void* operator new(std::size_t n, std::align_val_t a, const std::nothrow_t&) noexcept {
    try { return forge_s14_alloc::allocate_aligned(n, static_cast<std::size_t>(a)); } catch (...) { return nullptr; }
}
void* operator new[](std::size_t n, std::align_val_t a, const std::nothrow_t&) noexcept {
    try { return forge_s14_alloc::allocate_aligned(n, static_cast<std::size_t>(a)); } catch (...) { return nullptr; }
}
void operator delete(void* p) noexcept { std::free(p); }
void operator delete[](void* p) noexcept { std::free(p); }
void operator delete(void* p, std::size_t) noexcept { std::free(p); }
void operator delete[](void* p, std::size_t) noexcept { std::free(p); }
void operator delete(void* p, const std::nothrow_t&) noexcept { std::free(p); }
void operator delete[](void* p, const std::nothrow_t&) noexcept { std::free(p); }
void operator delete(void* p, std::align_val_t) noexcept { forge_s14_alloc::free_aligned(p); }
void operator delete[](void* p, std::align_val_t) noexcept { forge_s14_alloc::free_aligned(p); }
void operator delete(void* p, std::size_t, std::align_val_t) noexcept { forge_s14_alloc::free_aligned(p); }
void operator delete[](void* p, std::size_t, std::align_val_t) noexcept { forge_s14_alloc::free_aligned(p); }
void operator delete(void* p, std::align_val_t, const std::nothrow_t&) noexcept { forge_s14_alloc::free_aligned(p); }
void operator delete[](void* p, std::align_val_t, const std::nothrow_t&) noexcept { forge_s14_alloc::free_aligned(p); }

namespace forge_s14_alloc {
inline constexpr std::array<const char*, 8> ControlNames{
    "new", "new_array", "new_aligned", "new_array_aligned", "new_nothrow",
    "new_array_nothrow", "new_aligned_nothrow", "new_array_aligned_nothrow"};

inline void* control_allocate(unsigned kind) {
    // Ordinary function calls through volatile pointers, NOT elidable new expressions.
    using Fn = void* (*)(std::size_t);
    using AF = void* (*)(std::size_t, std::align_val_t);
    using NF = void* (*)(std::size_t, const std::nothrow_t&) noexcept;
    using ANF = void* (*)(std::size_t, std::align_val_t, const std::nothrow_t&) noexcept;
    switch (kind) {
    case 0: { Fn volatile fn = static_cast<Fn>(&::operator new); return fn(32); }
    case 1: { Fn volatile fn = static_cast<Fn>(&::operator new[]); return fn(32); }
    case 2: { AF volatile fn = static_cast<AF>(&::operator new); return fn(32, std::align_val_t{64}); }
    case 3: { AF volatile fn = static_cast<AF>(&::operator new[]); return fn(32, std::align_val_t{64}); }
    case 4: { NF volatile fn = static_cast<NF>(&::operator new); return fn(32, std::nothrow); }
    case 5: { NF volatile fn = static_cast<NF>(&::operator new[]); return fn(32, std::nothrow); }
    case 6: { ANF volatile fn = static_cast<ANF>(&::operator new); return fn(32, std::align_val_t{64}, std::nothrow); }
    case 7: { ANF volatile fn = static_cast<ANF>(&::operator new[]); return fn(32, std::align_val_t{64}, std::nothrow); }
    default: std::abort();
    }
}

inline void control_free(void* p, unsigned kind) noexcept {
    if (kind == 2 || kind == 3 || kind == 6 || kind == 7) free_aligned(p);
    else std::free(p);
    escaped_pointer = nullptr;
}

inline void positive_controls() {
    for (unsigned kind = 0; kind < ControlNames.size(); ++kind) {
        Stats stats;
        void* p = nullptr;
        {
            Window window(stats);
            p = control_allocate(kind);
            escape(p);
        }
        const bool okay = p != nullptr && !stats.overflow && stats.calls == 1 && stats.bytes == 32;
        const bool aligned = !(kind == 2 || kind == 3 || kind == 6 || kind == 7) ||
            (reinterpret_cast<std::uintptr_t>(p) & 63U) == 0;
        control_free(p, kind);
        std::cout << "CONTROL\t" << ControlNames[kind] << '\t' << stats.calls << '\t'
                  << stats.bytes << '\t' << (okay && aligned ? 1 : 0) << '\n';
        if (!okay || !aligned) throw std::runtime_error("allocation positive control failed");
    }
    windows = 0; // Workload windows exclude controls and all setup activity.
}
}
