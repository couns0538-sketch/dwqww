// Trainer for Forge's NNUE evaluation.
//
// Architecture (per side-to-move perspective): 768 piece-square inputs ->
// Hidden accumulator, SCReLU activation, then a single output over both
// perspectives (2 * Hidden -> 1). Trained with Adam on the squared error
// between sigmoid(output) and a blend of game result and search score, using
// the same "<fen> <result> <score>" files that forge_texel consumes.
//
// Usage:
//   forge_nnue_train positions.txt [more.txt ...] [--epochs N] [--lr X]
//       [--lambda L] [--batch B] [--threads T] [--k K] [--out weights.inc]
//       [--load weights.bin] [--save weights.bin] [--seed S]
#include "forge/board.hpp"
#include "forge/nnue.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
#include <random>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

namespace {

constexpr int Inputs = forge::nnue::InputCount;
constexpr int Hidden = forge::nnue::HiddenSize;

struct Sample {
    std::array<std::uint8_t, 32> pieces{};   // piece codes 1..12
    std::array<std::uint8_t, 32> squares{};
    std::uint8_t count = 0;
    std::uint8_t side = 0;                   // side to move
    float target = 0.5F;
};

struct Network {
    std::vector<float> w1 = std::vector<float>(static_cast<std::size_t>(Inputs) * Hidden);
    std::vector<float> b1 = std::vector<float>(Hidden);
    std::vector<float> w2 = std::vector<float>(2 * Hidden);
    float b2 = 0.0F;

    void randomize(std::uint64_t seed) {
        std::mt19937_64 rng(seed);
        std::normal_distribution<float> input_dist(0.0F, std::sqrt(1.0F / 32.0F));
        std::normal_distribution<float> output_dist(0.0F, std::sqrt(1.0F / static_cast<float>(2 * Hidden)));
        for (float& w : w1) w = input_dist(rng);
        for (float& w : w2) w = output_dist(rng);
        std::fill(b1.begin(), b1.end(), 0.0F);
        b2 = 0.0F;
    }
    bool load(const std::string& path) {
        std::ifstream in(path, std::ios::binary);
        if (!in) return false;
        in.read(reinterpret_cast<char*>(w1.data()), static_cast<std::streamsize>(w1.size() * sizeof(float)));
        in.read(reinterpret_cast<char*>(b1.data()), static_cast<std::streamsize>(b1.size() * sizeof(float)));
        in.read(reinterpret_cast<char*>(w2.data()), static_cast<std::streamsize>(w2.size() * sizeof(float)));
        in.read(reinterpret_cast<char*>(&b2), sizeof(float));
        return static_cast<bool>(in);
    }
    void save(const std::string& path) const {
        std::ofstream out(path, std::ios::binary);
        out.write(reinterpret_cast<const char*>(w1.data()), static_cast<std::streamsize>(w1.size() * sizeof(float)));
        out.write(reinterpret_cast<const char*>(b1.data()), static_cast<std::streamsize>(b1.size() * sizeof(float)));
        out.write(reinterpret_cast<const char*>(w2.data()), static_cast<std::streamsize>(w2.size() * sizeof(float)));
        out.write(reinterpret_cast<const char*>(&b2), sizeof(float));
    }
};

struct Gradients {
    std::vector<float> w1 = std::vector<float>(static_cast<std::size_t>(Inputs) * Hidden);
    std::vector<float> b1 = std::vector<float>(Hidden);
    std::vector<float> w2 = std::vector<float>(2 * Hidden);
    float b2 = 0.0F;
    double loss = 0.0;
    void clear() {
        std::fill(w1.begin(), w1.end(), 0.0F);
        std::fill(b1.begin(), b1.end(), 0.0F);
        std::fill(w2.begin(), w2.end(), 0.0F);
        b2 = 0.0F;
        loss = 0.0;
    }
};

inline float sigmoid(float x) { return 1.0F / (1.0F + std::exp(-x)); }

// Forward and backward pass for one sample; accumulates into g.
void train_sample(const Network& net, const Sample& s, Gradients& g) {
    alignas(32) float acc[2][Hidden];
    for (int p = 0; p < 2; ++p) std::memcpy(acc[p], net.b1.data(), sizeof(float) * Hidden);
    std::array<std::array<int, 32>, 2> features{};
    for (int i = 0; i < s.count; ++i) {
        const forge::Piece piece = static_cast<forge::Piece>(s.pieces[static_cast<std::size_t>(i)]);
        const int square = s.squares[static_cast<std::size_t>(i)];
        const forge::Color stm = static_cast<forge::Color>(s.side);
        features[0][static_cast<std::size_t>(i)] = forge::nnue::feature_index(stm, piece, square);
        features[1][static_cast<std::size_t>(i)] = forge::nnue::feature_index(forge::opposite(stm), piece, square);
        for (int p = 0; p < 2; ++p) {
            const float* column = net.w1.data() + static_cast<std::size_t>(features[static_cast<std::size_t>(p)][static_cast<std::size_t>(i)]) * Hidden;
            for (int h = 0; h < Hidden; ++h) acc[p][h] += column[h];
        }
    }
    alignas(32) float hidden[2][Hidden];
    float out = net.b2;
    for (int p = 0; p < 2; ++p) {
        for (int h = 0; h < Hidden; ++h) {
            const float clamped = std::clamp(acc[p][h], 0.0F, 1.0F);
            hidden[p][h] = clamped * clamped;
            out += hidden[p][h] * net.w2[static_cast<std::size_t>(p * Hidden + h)];
        }
    }
    const float prediction = sigmoid(out);
    const float diff = prediction - s.target;
    g.loss += static_cast<double>(diff) * diff;
    const float d_out = 2.0F * diff * prediction * (1.0F - prediction);
    g.b2 += d_out;
    for (int p = 0; p < 2; ++p) {
        alignas(32) float d_acc[Hidden];
        for (int h = 0; h < Hidden; ++h) {
            g.w2[static_cast<std::size_t>(p * Hidden + h)] += d_out * hidden[p][h];
            const float clamped = std::clamp(acc[p][h], 0.0F, 1.0F);
            const bool active = acc[p][h] > 0.0F && acc[p][h] < 1.0F;
            d_acc[h] = active ? d_out * net.w2[static_cast<std::size_t>(p * Hidden + h)] * 2.0F * clamped : 0.0F;
            g.b1[static_cast<std::size_t>(h)] += d_acc[h];
        }
        for (int i = 0; i < s.count; ++i) {
            float* column = g.w1.data() + static_cast<std::size_t>(features[static_cast<std::size_t>(p)][static_cast<std::size_t>(i)]) * Hidden;
            for (int h = 0; h < Hidden; ++h) column[h] += d_acc[h];
        }
    }
}

struct Adam {
    std::vector<float> m, v;
    explicit Adam(std::size_t n) : m(n, 0.0F), v(n, 0.0F) {}
    void step(float* params, const float* grads, std::size_t n, float lr, int t, float scale) {
        const float beta1 = 0.9F;
        const float beta2 = 0.999F;
        const float c1 = 1.0F - std::pow(beta1, static_cast<float>(t));
        const float c2 = 1.0F - std::pow(beta2, static_cast<float>(t));
        for (std::size_t i = 0; i < n; ++i) {
            const float g = grads[i] * scale;
            m[i] = beta1 * m[i] + (1.0F - beta1) * g;
            v[i] = beta2 * v[i] + (1.0F - beta2) * g * g;
            params[i] -= lr * (m[i] / c1) / (std::sqrt(v[i] / c2) + 1e-8F);
        }
    }
};

void write_include(const std::string& path, const Network& net) {
    std::ofstream out(path);
    out << "// Generated by forge_nnue_train. Quantised weights for forge::nnue.\n";
    out << "// Layout: w1[" << Inputs << " * " << Hidden << "], b1[" << Hidden << "], w2[" << 2 * Hidden << "], b2.\n";
    auto emit = [&](const char* name, const std::vector<float>& values, float scale) {
        out << "static const std::int16_t " << name << "[" << values.size() << "] = {";
        for (std::size_t i = 0; i < values.size(); ++i) {
            if (i % 24 == 0) out << "\n   ";
            const long rounded = std::lround(values[i] * scale);
            out << ' ' << std::clamp<long>(rounded, -32767, 32767) << ',';
        }
        out << "\n};\n";
    };
    emit("NnueW1", net.w1, forge::nnue::WeightScale);
    emit("NnueB1", net.b1, forge::nnue::WeightScale);
    emit("NnueW2", net.w2, forge::nnue::OutputScale);
    out << "static const std::int16_t NnueB2 = " << std::clamp<long>(std::lround(net.b2 * forge::nnue::OutputScale), -32767, 32767) << ";\n";
}

} // namespace

int main(int argc, char** argv) {
    std::vector<std::string> inputs;
    std::string output_path = "nnue_weights.inc";
    std::string load_path;
    std::string save_path = "nnue_weights.bin";
    int epochs = 20;
    float learning_rate = 0.001F;
    float lambda = 0.6F;
    std::size_t batch = 16384;
    int threads = static_cast<int>(std::max(1U, std::thread::hardware_concurrency()));
    float k = 2.25F;
    std::uint64_t seed = 20261012;
    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        auto next = [&]() -> std::string { return i + 1 < argc ? argv[++i] : ""; };
        if (arg == "--epochs") epochs = std::stoi(next());
        else if (arg == "--lr") learning_rate = std::stof(next());
        else if (arg == "--lambda") lambda = std::stof(next());
        else if (arg == "--batch") batch = static_cast<std::size_t>(std::stoul(next()));
        else if (arg == "--threads") threads = std::stoi(next());
        else if (arg == "--k") k = std::stof(next());
        else if (arg == "--out") output_path = next();
        else if (arg == "--load") load_path = next();
        else if (arg == "--save") save_path = next();
        else if (arg == "--seed") seed = std::stoull(next());
        else inputs.push_back(arg);
    }
    if (inputs.empty()) {
        std::cerr << "usage: forge_nnue_train positions.txt [options]\n";
        return 2;
    }

    std::vector<Sample> samples;
    {
        forge::Board board;
        std::string line;
        for (const std::string& path : inputs) {
            std::ifstream in(path);
            if (!in) {
                std::cerr << "cannot open " << path << '\n';
                return 1;
            }
            while (std::getline(in, line)) {
                std::istringstream fields(line);
                std::string placement, side, castling, ep, half, full, result_text, score_text;
                if (!(fields >> placement >> side >> castling >> ep >> half >> full >> result_text)) continue;
                fields >> score_text;
                if (!board.set_fen(placement + ' ' + side + ' ' + castling + ' ' + ep + ' ' + half + ' ' + full)) continue;
                Sample s;
                s.side = static_cast<std::uint8_t>(board.side_to_move());
                forge::Bitboard occupied = board.occupied();
                while (occupied != 0) {
                    const int square = forge::pop_lsb(occupied);
                    s.pieces[s.count] = static_cast<std::uint8_t>(board.piece_at(square));
                    s.squares[s.count] = static_cast<std::uint8_t>(square);
                    ++s.count;
                }
                // Targets are from the side to move's point of view.
                float result = std::stof(result_text);
                if (board.side_to_move() == forge::Black) result = 1.0F - result;
                float target = result;
                if (!score_text.empty() && score_text != "none") {
                    float score = std::stof(score_text);
                    if (board.side_to_move() == forge::Black) score = -score;
                    target = lambda * result + (1.0F - lambda) * sigmoid(k * score / 400.0F);
                }
                s.target = target;
                samples.push_back(s);
            }
        }
        std::cerr << "loaded " << samples.size() << " positions\n";
        if (samples.empty()) return 1;
    }

    Network net;
    if (!load_path.empty() && net.load(load_path)) std::cerr << "loaded weights from " << load_path << '\n';
    else net.randomize(seed);

    const std::size_t n1 = net.w1.size();
    Adam adam_w1(n1), adam_b1(net.b1.size()), adam_w2(net.w2.size()), adam_b2(1);
    std::vector<Gradients> thread_grads(static_cast<std::size_t>(threads));
    std::vector<std::uint32_t> order(samples.size());
    for (std::uint32_t i = 0; i < order.size(); ++i) order[i] = i;
    std::mt19937_64 rng(seed);
    int step = 0;
    const auto start = std::chrono::steady_clock::now();
    for (int epoch = 1; epoch <= epochs; ++epoch) {
        std::shuffle(order.begin(), order.end(), rng);
        double epoch_loss = 0.0;
        for (std::size_t begin = 0; begin < samples.size(); begin += batch) {
            const std::size_t end = std::min(samples.size(), begin + batch);
            std::vector<std::thread> workers;
            for (int t = 0; t < threads; ++t) {
                workers.emplace_back([&, t]() {
                    Gradients& g = thread_grads[static_cast<std::size_t>(t)];
                    g.clear();
                    const std::size_t lo = begin + (end - begin) * static_cast<std::size_t>(t) / static_cast<std::size_t>(threads);
                    const std::size_t hi = begin + (end - begin) * static_cast<std::size_t>(t + 1) / static_cast<std::size_t>(threads);
                    for (std::size_t i = lo; i < hi; ++i) train_sample(net, samples[order[i]], g);
                });
            }
            for (auto& worker : workers) worker.join();
            Gradients& total = thread_grads[0];
            for (int t = 1; t < threads; ++t) {
                const Gradients& g = thread_grads[static_cast<std::size_t>(t)];
                for (std::size_t i = 0; i < n1; ++i) total.w1[i] += g.w1[i];
                for (std::size_t i = 0; i < total.b1.size(); ++i) total.b1[i] += g.b1[i];
                for (std::size_t i = 0; i < total.w2.size(); ++i) total.w2[i] += g.w2[i];
                total.b2 += g.b2;
                total.loss += g.loss;
            }
            epoch_loss += total.loss;
            ++step;
            const float scale = 1.0F / static_cast<float>(end - begin);
            adam_w1.step(net.w1.data(), total.w1.data(), n1, learning_rate, step, scale);
            adam_b1.step(net.b1.data(), total.b1.data(), net.b1.size(), learning_rate, step, scale);
            adam_w2.step(net.w2.data(), total.w2.data(), net.w2.size(), learning_rate, step, scale);
            adam_b2.step(&net.b2, &total.b2, 1, learning_rate, step, scale);
        }
        const auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(std::chrono::steady_clock::now() - start).count();
        std::cerr << "epoch " << epoch << " loss " << epoch_loss / static_cast<double>(samples.size()) << " lr " << learning_rate
                  << " (" << elapsed << "s)\n";
        if (epoch % 8 == 0) learning_rate *= 0.5F;
        net.save(save_path);
        write_include(output_path, net);
    }
    std::cerr << "wrote " << output_path << " and " << save_path << '\n';
    return 0;
}
