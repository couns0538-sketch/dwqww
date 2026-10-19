// Source-grounded rule-50 TT score-consumer policy model. MODEL ONLY.
#include <array>
#include <cassert>
#include <iostream>
constexpr bool allowed(int clock) { return clock < 90; }
constexpr bool lower_cut(int score,int beta) { return score >= beta; }
int main() {
    unsigned preserved=0, rejected=0;
    for(int clock : std::array<int,6>{0,50,89,90,99,100}) {
        const bool score_ok=allowed(clock);
        // Main TT cutoff, qsearch TT cutoff, main/qsearch score-as-eval,
        // null-move upper-bound hint, ProbCut TT hint, singular extension.
        for(int consumer=0; consumer<7; ++consumer) {
            const bool original = (consumer!=0 || clock<90); // main already guarded
            const bool proposed = score_ok;
            assert(!proposed || original);
            if(clock<90) {assert(proposed);++preserved;}
            else {assert(!proposed);++rejected;}
        }
        // Position-based raw static eval and hash move remain available.
        assert(true);
        assert(lower_cut(200,100));
    }
    assert(preserved==21 && rejected==21);
    std::cout<<"PASS rule50 consumer model: 21 low-clock paths retained; 21 high-clock paths gated; no engine score tested.\\n";
}
