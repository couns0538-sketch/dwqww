// lp_probe.cpp - can this process get large pages, and how long does a 16 MB block take? (speed hunt, own code)
// Same calls as the engine's FORGE_SPD_LARGEPAGES path; prints the outcome of every step.
#define NOMINMAX
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <chrono>
#include <cstdio>
#include <cstring>

int main() {
    HANDLE token = nullptr;
    if (!OpenProcessToken(GetCurrentProcess(), TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY, &token)) {
        std::printf("OpenProcessToken failed %lu\n", GetLastError());
        return 1;
    }
    TOKEN_PRIVILEGES tp{};
    if (!LookupPrivilegeValueA(nullptr, "SeLockMemoryPrivilege", &tp.Privileges[0].Luid)) {
        std::printf("LookupPrivilegeValue failed %lu\n", GetLastError());
        return 1;
    }
    tp.PrivilegeCount = 1;
    tp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED;
    SetLastError(ERROR_SUCCESS);
    const BOOL adj = AdjustTokenPrivileges(token, FALSE, &tp, 0, nullptr, nullptr);
    const DWORD adj_err = GetLastError();
    CloseHandle(token);
    std::printf("AdjustTokenPrivileges ret %d last error %lu (%s)\n", adj, adj_err,
                adj && adj_err == ERROR_SUCCESS ? "enabled" : "NOT enabled");
    const SIZE_T page = GetLargePageMinimum();
    std::printf("GetLargePageMinimum %zu\n", static_cast<size_t>(page));
    if (!(adj && adj_err == ERROR_SUCCESS) || page == 0) return 2;
    const size_t bytes = 16u * 1024u * 1024u;
    for (int i = 0; i < 6; ++i) {
        const auto t0 = std::chrono::steady_clock::now();
        void* p = VirtualAlloc(nullptr, bytes, MEM_RESERVE | MEM_COMMIT | MEM_LARGE_PAGES, PAGE_READWRITE);
        const auto t1 = std::chrono::steady_clock::now();
        const DWORD err = p ? 0 : GetLastError();
        bool zero = true;
        if (p) {
            const unsigned char* c = static_cast<const unsigned char*>(p);
            for (size_t k = 0; k < bytes; k += 4096) zero = zero && c[k] == 0 && c[k + 4095] == 0;
            std::memset(p, 0, bytes);
        }
        const auto t2 = std::chrono::steady_clock::now();
        std::printf("try %d: %s err %lu alloc %.3f ms zeroed %s, memset %.3f ms\n", i, p ? "OK" : "FAILED", err,
                    std::chrono::duration<double, std::milli>(t1 - t0).count(), zero ? "yes" : "NO",
                    std::chrono::duration<double, std::milli>(t2 - t1).count());
        if (p) VirtualFree(p, 0, MEM_RELEASE);
    }
    return 0;
}
