#pragma once

// Runtime search options set over UCI (src/uci.cpp). Every option defaults to
// OFF; with all options OFF the search is the AL1 s198 search. Options are
// written only while no search runs (the UCI loop stops the search first).
namespace forge::options {

// UCI MaterialKeyTable (check, default false), job S11 (node-exact speed).
// The material-correction key (src/search.cpp material_key) is computed from
// the contribution table of forge/material_key_table.hpp (ten table loads and
// additions) instead of the ten dependent Horner multiplications. Both give the
// same 64-bit key for every board, so the search (nodes, scores, moves) is
// unchanged; only the speed can differ.
extern bool material_key_table;

} // namespace forge::options
