#include "forge/eval_params.hpp"

#include <string>

namespace forge::params {
namespace {

// The flat parameter table lives in a generated include so the Texel tuner
// (tools/tune) can rewrite it wholesale.
constexpr Table Defaults{{
#include "eval_params_table.inc"
}};

} // namespace

Table defaults() { return Defaults; }

Table table = defaults();

const char* name(int index) {
    static thread_local std::string buffer;
    auto indexed = [&](const char* base, int start) {
        buffer = std::string(base) + "[" + std::to_string(index - start) + "]";
        return buffer.c_str();
    };
    if (index < KnightMobility) {
        constexpr std::array<const char*, 6> pieces{"PawnPsqt", "KnightPsqt", "BishopPsqt", "RookPsqt", "QueenPsqt", "KingPsqt"};
        buffer = std::string(pieces[static_cast<std::size_t>(index / 64)]) + "[" + std::to_string(index % 64) + "]";
        return buffer.c_str();
    }
    if (index < BishopMobility) return indexed("KnightMobility", KnightMobility);
    if (index < RookMobility) return indexed("BishopMobility", BishopMobility);
    if (index < QueenMobility) return indexed("RookMobility", RookMobility);
    if (index < BishopPair) return indexed("QueenMobility", QueenMobility);
    switch (index) {
    case BishopPair: return "BishopPair";
    case RookOpenFile: return "RookOpenFile";
    case RookSemiOpenFile: return "RookSemiOpenFile";
    case RookOnSeventh: return "RookOnSeventh";
    case KnightOutpost: return "KnightOutpost";
    case BishopOutpost: return "BishopOutpost";
    case MinorBehindPawn: return "MinorBehindPawn";
    case BishopPawnsSameColor: return "BishopPawnsSameColor";
    case QueenEarlyDevelopment: return "QueenEarlyDevelopment";
    case Tempo: return "Tempo";
    case PawnIsolated: return "PawnIsolated";
    case PawnDoubled: return "PawnDoubled";
    case PawnBackward: return "PawnBackward";
    case PawnPhalanx: return "PawnPhalanx";
    case PawnDoubleSupport: return "PawnDoubleSupport";
    case PassedBlocked: return "PassedBlocked";
    case PassedUnstoppablePath: return "PassedUnstoppablePath";
    case PassedSafePush: return "PassedSafePush";
    case PassedEnemyKingDistance: return "PassedEnemyKingDistance";
    case PassedOwnKingDistance: return "PassedOwnKingDistance";
    case ThreatByKing: return "ThreatByKing";
    case ThreatByPawn: return "ThreatByPawn";
    case ThreatByPawnPush: return "ThreatByPawnPush";
    case HangingPiece: return "HangingPiece";
    case RestrictedPiece: return "RestrictedPiece";
    case KingFileOpen: return "KingFileOpen";
    default: break;
    }
    if (index >= PawnConnected && index < PawnConnected + 8) return indexed("PawnConnected", PawnConnected);
    if (index >= PassedRank && index < PassedRank + 8) return indexed("PassedRank", PassedRank);
    if (index >= ThreatByMinor && index < ThreatByMinor + 7) return indexed("ThreatByMinor", ThreatByMinor);
    if (index >= ThreatByRook && index < ThreatByRook + 7) return indexed("ThreatByRook", ThreatByRook);
    if (index >= ShelterDistance && index < ShelterDistance + 4) return indexed("ShelterDistance", ShelterDistance);
    if (index >= StormDistance && index < StormDistance + 4) return indexed("StormDistance", StormDistance);
    if (index >= KingDanger && index < KingDanger + 100) return indexed("KingDanger", KingDanger);
    return "Unknown";
}

} // namespace forge::params
