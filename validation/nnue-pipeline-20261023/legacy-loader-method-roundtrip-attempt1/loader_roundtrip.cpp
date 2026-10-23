// API-only verification wrapper. The actual trainer source is included unchanged.
#define main legacy_trainer_main
#include "/workspace/dwqww/tools/tune/nnue_train.cpp"
#undef main

int main(int argc, char** argv) {
    static_assert(Hidden == 128);
    static_assert(Inputs == 768);
    if (argc != 4) return 2;
    Network net;
    if (!net.load(argv[1])) {
        std::cerr << "original Network::load rejected input\n";
        return 3;
    }
    net.save(argv[2]);
    write_include(argv[3], net, true);
    std::cout << "original loader/save/export methods completed; inputs=" << Inputs
              << " hidden=" << Hidden << " residual=1\n";
    return 0;
}
