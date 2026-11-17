// Build the planted-wrong oracle used by selftest.py.
//
// The fault is chosen to be the one most dangerous to THIS audit, not a random
// bug: a "dist" that returns the engine's claimed N as soon as ANY mate exists,
// without proving the shorter distance impossible. That is exactly the shape of
// verifier that would report every label "exact" and make the whole measurement
// look clean. If the self-test cannot catch this, the clean run means nothing.
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <string>

// Reuse the real implementation, renaming main.
#define main real_oracle_main
#include "oracle.cpp"
#undef main

int main(int argc, char** argv) {
    // Forward perft so perft validation can also be run against this binary
    // (it must still pass -- the fault is confined to mate answers).
    if (argc >= 4 && std::string(argv[1]) == "perft") return real_oracle_main(argc, argv);

    std::string line;
    std::cout << "{\"banner\":\"matelabels-oracle-BROKEN\",\"version\":1}\n";
    while (std::getline(std::cin, line)) {
        if (line.empty() || line[0] == '#') continue;
        std::size_t p1 = line.find(' ');
        std::size_t p2 = line.find(' ', p1 + 1);
        std::size_t p3 = line.find(' ', p2 + 1);
        std::size_t p4 = line.find(' ', p3 + 1);
        if (p1 == std::string::npos || p4 == std::string::npos) continue;
        const std::string id = line.substr(0, p1);
        const std::string mode = line.substr(p1 + 1, p2 - p1 - 1);
        const int plies = std::stoi(line.substr(p2 + 1, p3 - p2 - 1));
        std::string rest = line.substr(p4 + 1);

        // Strip an optional leading move token for pinwin.
        std::string mv;
        if (mode == "pinwin") {
            const std::size_t sp = rest.find(' ');
            mv = rest.substr(0, sp);
            rest = rest.substr(sp + 1);
        }

        Board b;
        std::string err;
        if (!set_fen(b, rest, err)) {
            std::cout << "{\"id\":\"" << id << "\",\"error\":\"fen\"}\n" << std::flush;
            continue;
        }
        Search S;
        S.deadline = std::chrono::steady_clock::now() + std::chrono::seconds(600);

        if (mode == "dist") {
            // THE PLANTED FAULT: any mate anywhere in the budget is reported as
            // an exact mate at the requested depth. Never proves the shorter
            // distance impossible, so it can never report an over-statement.
            const bool any = win_within(S, b, plies);
            std::cout << "{\"id\":\"" << id << "\",\"mode\":\"dist\",\"exact_plies\":"
                      << (any ? plies : 0) << ",\"tested_up_to\":" << plies
                      << ",\"status\":\"ok\",\"nodes\":" << S.nodes << "}\n" << std::flush;
        } else if (mode == "win") {
            const bool v = win_within(S, b, plies);
            std::cout << "{\"id\":\"" << id << "\",\"mode\":\"win\",\"plies\":" << plies
                      << ",\"value\":" << (v ? "true" : "false") << ",\"status\":\"ok\""
                      << ",\"nodes\":" << S.nodes << "}\n" << std::flush;
        } else if (mode == "loss") {
            const bool v = loss_within(S, b, plies);
            std::cout << "{\"id\":\"" << id << "\",\"mode\":\"loss\",\"plies\":" << plies
                      << ",\"value\":" << (v ? "true" : "false") << ",\"status\":\"ok\""
                      << ",\"nodes\":" << S.nodes << "}\n" << std::flush;
        } else if (mode == "pinwin") {
            std::vector<Move> gen;
            legal_moves(b, gen);
            Move pin{-1, -1, 0, 0};
            bool found = false;
            for (const auto& g : gen) {
                char buf[8];
                std::snprintf(buf, sizeof buf, "%c%c%c%c",
                              'a' + (g.from & 7), '1' + (g.from >> 3),
                              'a' + (g.to & 7), '1' + (g.to >> 3));
                if (mv.substr(0, 4) == buf) { pin = g; found = true; break; }
            }
            const bool v = found && win_within_pinned(S, b, plies, pin);
            std::cout << "{\"id\":\"" << id << "\",\"mode\":\"pinwin\",\"value\":"
                      << (v ? "true" : "false") << ",\"status\":\"ok\",\"nodes\":" << S.nodes
                      << "}\n" << std::flush;
        } else {
            std::cout << "{\"id\":\"" << id << "\",\"error\":\"mode\"}\n" << std::flush;
        }
    }
    return 0;
}
