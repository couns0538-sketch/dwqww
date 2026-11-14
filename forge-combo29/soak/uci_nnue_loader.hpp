#pragma once
// Link the unchanged src/uci.cpp with -Dmain=forge_soak_uci_entry.
// Its real NnueFile command handler changes the same linked NNUE state
// that the position checker evaluates after the UCI loop returns.
#include <iostream>
#include <sstream>
#include <string>

int forge_soak_uci_entry();

static bool soak_load_net(const std::string& path, std::string& error) {
    const std::string value=path.empty()?"<empty>":path;
    const std::string commands="setoption name Threads value 1\nsetoption name Hash value 16\n"
        "setoption name OwnBook value false\nsetoption name NnueFile value "+value+"\nisready\nquit\n";
    std::istringstream input(commands);
    std::ostringstream output;
    const auto old_state=std::cin.rdstate();
    auto* old_input=std::cin.rdbuf(input.rdbuf());
    auto* old_output=std::cout.rdbuf(output.rdbuf());
    std::cin.clear();
    int status=0;
    try { status=forge_soak_uci_entry(); }
    catch(...) {
        std::cin.rdbuf(old_input);std::cin.clear(old_state);std::cout.rdbuf(old_output);throw;
    }
    std::cin.rdbuf(old_input);std::cin.clear(old_state);std::cout.rdbuf(old_output);
    const auto transcript=output.str();
    std::cout<<"UCI_INPUT\n"<<commands<<"UCI_OUTPUT\n"<<transcript<<"UCI_EXIT "<<status<<std::endl;
    const auto failure=transcript.find("info string nnue:");
    if(status!=0||failure!=std::string::npos) {
        error=failure==std::string::npos?"UCI entry returned nonzero":transcript.substr(failure);
        return false;
    }
    if(transcript.find("readyok")==std::string::npos ||
       (!path.empty()&&transcript.find("info string loaded nnue "+path)==std::string::npos)) {
        error="UCI load acknowledgement missing";return false;
    }
    error.clear();return true;
}
