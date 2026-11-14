#include "forge/search.hpp"
#include <iostream>
namespace forge { int uci_loop(std::istream&); }
// Uses the reviewed branch's existing per-case testing API; no engine edit.
int main() {
    forge::tune::SoundArmPv = forge::tune::SoundPruneArm::ForceOff;
    forge::tune::SoundArmInCheck = forge::tune::SoundPruneArm::ForceOff;
    forge::tune::SoundArmMateAlpha = forge::tune::SoundPruneArm::FollowOption;
    forge::tune::SoundPruneTrace = false;
    return forge::uci_loop(std::cin);
}
