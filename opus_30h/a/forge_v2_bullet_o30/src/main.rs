//! R13 P4: Forge v2 (FORGENN2) net trainer for the bullet trainer library da426a49 (own code). Opus 30-h job: `r` mode
//! (residual nets from the FPOS + FHCE shards, king buckets + mirror; forge_r.rs) on a private library copy with residual_base.
//!
//! Stages (Engine Strategist M4, staged order):
//!   a = 768 piece-square inputs + 8 output buckets by material count
//!   b = a + O6 threat inputs (12 x 12 x 64 = 9216, count-valued: one column per attacker/victim pair)
//!   c = b + O7 pawn-pair inputs (4 x 7 x 64 = 1792)
//! Architecture = forge/nnue_v2.hpp: (inputs -> H) per perspective, SCReLU (clamp to [0, 1], square), side to move
//! first, one linear output per bucket; Forge reports cp = out * 400 / 2.25, so eval_scale here is 400 / 2.25.
//! Feature indices mirror nnue_v2.hpp exactly (king buckets 1, no mirroring):
//!   piece-square  ((colour == p ? 0 : 1) * 6 + type) * 64 + relative square          (= bullet Chess768)
//!   threat        768 + (rel(A) * 12 + rel(V)) * 64 + relative victim square, rel = (colour == p ? 0 : 6) + type;
//!                 skipped: a king attacking a king, and any piece attacking its own side's king
//!   pawn pair     768 [+ 9216] + ((colour(anchor) * 2 + colour(other)) * 7 + o) * 64 + relative anchor square
//! bulletformat keeps boards in the side-to-move frame (black to move: ranks flipped, colours swapped), so the
//! side-to-move features use the stored squares and the other perspective uses square ^ 56 with colours swapped.
//! Output: raw f32 tensors l0w [input][H], l0b [H], l1w transposed [bucket][2H], l1b [bucket] -> export_v2.py.
//!
//! usage: forge-v2-bullet <a|b|c> <binpack> <out_dir> [hidden=256] [superbatches=4] [batches_per_sb=1024] [threads=2] [seed]
//!        forge-v2-bullet features <a|b|c> <fen>      (prints the active feature pairs, for the parity tests)
use bullet_lib::{
    game::{inputs::SparseInputType, outputs::MaterialCount},
    nn::optimiser::AdamW,
    trainer::{
        save::SavedFormat,
        schedule::{TrainingSchedule, TrainingSteps, lr, wdl},
        settings::LocalSettings,
    },
    value::{ValueTrainerBuilder, loader},
};
use bulletformat::ChessBoard;

const PSQ: usize = 768;
const THREATS: usize = 12 * 12 * 64;
const PAIRS: usize = 4 * 7 * 64;
const MAX_THREATS: usize = 512;
const MAX_PAIRS: usize = 16 * 7;
const OUTPUT_BUCKETS: usize = 8;
const SIGMOID_K: f32 = 2.25;

#[derive(Clone, Copy, Debug)]
pub struct ForgeV2 {
    threats: bool,
    pawn_pairs: bool,
}

impl ForgeV2 {
    fn stage(s: &str) -> Self {
        match s {
            "a" => Self { threats: false, pawn_pairs: false },
            "b" => Self { threats: true, pawn_pairs: false },
            "c" => Self { threats: true, pawn_pairs: true },
            _ => panic!("stage must be a, b or c"),
        }
    }
    fn pair_base(&self) -> usize {
        PSQ + if self.threats { THREATS } else { 0 }
    }
}

const FILE_A: u64 = 0x0101_0101_0101_0101;
const FILE_H: u64 = FILE_A << 7;

fn ray(s: usize, occ: u64, dirs: &[(i32, i32)]) -> u64 {
    let (r0, f0) = ((s / 8) as i32, (s % 8) as i32);
    let mut out = 0u64;
    for &(dr, df) in dirs {
        let (mut r, mut f) = (r0 + dr, f0 + df);
        while (0..8).contains(&r) && (0..8).contains(&f) {
            let b = 1u64 << (r * 8 + f);
            out |= b;
            if occ & b != 0 {
                break; // up to and including the first piece
            }
            r += dr;
            f += df;
        }
    }
    out
}

fn steps(s: usize, deltas: &[(i32, i32)]) -> u64 {
    let (r0, f0) = ((s / 8) as i32, (s % 8) as i32);
    let mut out = 0u64;
    for &(dr, df) in deltas {
        let (r, f) = (r0 + dr, f0 + df);
        if (0..8).contains(&r) && (0..8).contains(&f) {
            out |= 1u64 << (r * 8 + f);
        }
    }
    out
}

const DIAG: [(i32, i32); 4] = [(1, 1), (1, -1), (-1, 1), (-1, -1)];
const ORTH: [(i32, i32); 4] = [(1, 0), (-1, 0), (0, 1), (0, -1)];
const KNIGHT: [(i32, i32); 8] = [(1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)];
const KING: [(i32, i32); 8] = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)];

/// Attack set of a piece of colour c (0 = side to move, moving up the board in this frame) and type t on s.
fn attacks(c: usize, t: usize, s: usize, occ: u64) -> u64 {
    match t {
        0 => steps(s, if c == 0 { &[(1, -1), (1, 1)] } else { &[(-1, -1), (-1, 1)] }),
        1 => steps(s, &KNIGHT),
        2 => ray(s, occ, &DIAG),
        3 => ray(s, occ, &ORTH),
        4 => ray(s, occ, &DIAG) | ray(s, occ, &ORTH),
        _ => steps(s, &KING),
    }
}

/// Pawn-pair features of one perspective; side[0] = its own pawns, side[1] = the other side's, in its own frame.
fn pawn_pairs(side: [u64; 2], base: usize, out: &mut [usize; MAX_PAIRS]) -> usize {
    const OFFSETS: [(u32, u64); 7] =
        [(1, !FILE_H), (7, !FILE_A), (8, !0), (9, !FILE_H), (15, !FILE_A), (16, !0), (17, !FILE_H)];
    let mut n = 0;
    for (o, &(shift, mask)) in OFFSETS.iter().enumerate() {
        for c1 in 0..2 {
            for c2 in 0..2 {
                let mut anchors = side[c1] & mask & (side[c2] >> shift);
                while anchors != 0 {
                    let a = anchors.trailing_zeros() as usize;
                    anchors &= anchors - 1;
                    out[n] = base + ((c1 * 2 + c2) * 7 + o) * 64 + a;
                    n += 1;
                }
            }
        }
    }
    n
}

impl SparseInputType for ForgeV2 {
    type RequiredDataType = ChessBoard;

    fn num_inputs(&self) -> usize {
        self.pair_base() + if self.pawn_pairs { PAIRS } else { 0 }
    }

    fn max_active(&self) -> usize {
        32 + if self.threats { MAX_THREATS } else { 0 } + if self.pawn_pairs { MAX_PAIRS } else { 0 }
    }

    fn map_features<F: FnMut(usize, usize)>(&self, pos: &ChessBoard, mut f: F) {
        let mut bb = [[0u64; 6]; 2];
        let mut mailbox = [255u8; 64];
        let mut occ = 0u64;
        for (piece, square) in pos.into_iter() {
            let c = usize::from(piece & 8 > 0);
            let t = usize::from(piece & 7);
            let sq = usize::from(square);
            bb[c][t] |= 1u64 << sq;
            occ |= 1u64 << sq;
            mailbox[sq] = (c * 6 + t) as u8;
            f([0, 384][c] + 64 * t + sq, [384, 0][c] + 64 * t + (sq ^ 56));
        }
        if self.threats {
            for c in 0..2 {
                for t in 0..6 {
                    let mut attackers = bb[c][t];
                    while attackers != 0 {
                        let s = attackers.trailing_zeros() as usize;
                        attackers &= attackers - 1;
                        let mut targets = attacks(c, t, s, occ) & occ;
                        while targets != 0 {
                            let v = targets.trailing_zeros() as usize;
                            targets &= targets - 1;
                            let code = mailbox[v] as usize;
                            let (cv, tv) = (code / 6, code % 6);
                            if tv == 5 && (t == 5 || cv == c) {
                                continue; // redundant pairs (nnue_v2.hpp threat_keys)
                            }
                            let stm = PSQ + ((c * 6 + t) * 12 + cv * 6 + tv) * 64 + v;
                            let ntm = PSQ + (((1 - c) * 6 + t) * 12 + (1 - cv) * 6 + tv) * 64 + (v ^ 56);
                            f(stm, ntm);
                        }
                    }
                }
            }
        }
        if self.pawn_pairs {
            let base = self.pair_base();
            let (own, their) = (bb[0][0], bb[1][0]);
            let mut stm_list = [0usize; MAX_PAIRS];
            let mut ntm_list = [0usize; MAX_PAIRS];
            let ns = pawn_pairs([own, their], base, &mut stm_list);
            let nn = pawn_pairs([their.swap_bytes(), own.swap_bytes()], base, &mut ntm_list);
            assert_eq!(ns, nn, "pawn pairs differ between perspectives");
            for i in 0..ns {
                f(stm_list[i], ntm_list[i]);
            }
        }
    }

    fn shorthand(&self) -> String {
        format!("768{}{}", if self.threats { "+T9216" } else { "" }, if self.pawn_pairs { "+P1792" } else { "" })
    }

    fn description(&self) -> String {
        "Forge v2 inputs: piece-square, optional O6 threats and O7 pawn pairs (forge/nnue_v2.hpp)".to_string()
    }
}

fn arg<T: std::str::FromStr>(a: &[String], i: usize, d: T) -> T {
    // a missing argument takes the default; a present but unparsable one is an error (never a silent default)
    match a.get(i) {
        None => d,
        Some(s) => s.parse().unwrap_or_else(|_| panic!("argument {i} ({s:?}) is not a valid number")),
    }
}

mod forge_r;

/// Opus 30-h job: `r` mode - residual nets from the FPOS + FHCE shards (see forge_r.rs).
/// usage: forge-v2-bullet r <data dir> <out dir> <kb map one|rank4|rank4x2|rank4x4|rank4x8> <mirror 0|1> [hidden=256] [superbatches=40]
///        [batches_per_sb=1024] [threads=2] [seed] [lr=0.001] [wdl=0.4] [mix=8]
///        forge-v2-bullet rfeatures <data dir> <kb map> <mirror 0|1> <chunk> <count>   (features of the first rows of
///        a chunk: "S <stm indices>", "N <ntm indices>", "B <output bucket> H <hce> T <score> R <result>", for checks)
fn kmap_of(name: &str) -> ([u8; 64], usize) {
    let mut m = [0u8; 64];
    match name {
        "one" => (m, 1),
        "rank4" => {
            for (sq, v) in m.iter_mut().enumerate() {
                let r = sq / 8;
                *v = if r == 0 { 0 } else if r == 1 { 1 } else if r <= 3 { 2 } else { 3 };
            }
            (m, 4)
        }
        "rank4x2" => {
            // rank4 x board half (files a-d -> even bucket, e-h -> odd): 8 buckets, as o30_v2net.king_map
            for (sq, v) in m.iter_mut().enumerate() {
                let r = sq / 8;
                let g: u8 = if r == 0 { 0 } else if r == 1 { 1 } else if r <= 3 { 2 } else { 3 };
                *v = g * 2 + u8::from(sq % 8 >= 4);
            }
            (m, 8)
        }
        "rank4x4" | "rank4x8" => {
            // rank4 x file pair (a-b, c-d, e-f, g-h): 16 buckets / rank4 x file: 32 buckets, as o30_v2net.king_map
            let per: u8 = if name == "rank4x4" { 4 } else { 8 };
            for (sq, v) in m.iter_mut().enumerate() {
                let r = sq / 8;
                let g: u8 = if r == 0 { 0 } else if r == 1 { 1 } else if r <= 3 { 2 } else { 3 };
                let f = (sq % 8) as u8;
                *v = g * per + if per == 4 { f / 2 } else { f };
            }
            (m, usize::from(per) * 4)
        }
        _ => panic!("king map must be one, rank4, rank4x2, rank4x4 or rank4x8"),
    }
}

fn main_r(a: &[String]) {
    use bullet_lib::value::loader::DataReader;
    use forge_r::{FposReader, ForgeRow, ForgeV2R, PieceCount8};
    const POS: &str = "D:/grok-pc-data/forge_push/nnue_data/pos";
    const HCE: &str = "D:/grok-pc-data/forge_push/nnue_data/hce";
    if a[1] == "rfeatures" {
        assert!(a.len() == 7, "usage: forge-v2-bullet rfeatures <data dir> <kb map> <mirror 0|1> <chunk> <count>");
        let (kmap, kb) = kmap_of(&a[3]);
        let inputs = ForgeV2R { kmap, kb, mirror: a[4] == "1" };
        let reader = FposReader::new(&a[2], POS, HCE, 1_000_000, 8, 1);
        let rows = reader.chunk(arg(a, 5, 0u64));
        for r in rows.iter().take(arg(a, 6, 10usize)) {
            let (mut s, mut n) = (Vec::new(), Vec::new());
            inputs.map_features(r, |x, y| {
                s.push(x.to_string());
                n.push(y.to_string());
            });
            use bullet_lib::game::outputs::OutputBuckets;
            let hex: String = r.board.iter().map(|b| format!("{b:02x}")).collect();
            println!("P {hex}\nS {}\nN {}\nB {} H {} T {} R {} M {}", s.join(" "), n.join(" "), PieceCount8.bucket(r), r.hce,
                     r.score, r.result, r.stm);
        }
        let _ = reader.read_chunks(0, |c| { println!("first chunk rows {}", c.len()); true });   // true = stop
        return;
    }
    assert!((6..=14).contains(&a.len()), "usage: forge-v2-bullet r <data dir> <out dir> <kb map> <mirror 0|1> [hidden] [sb] [bpsb] [threads] [seed] [lr] [wdl] [mix]");
    let (kmap, kb) = kmap_of(&a[4]);
    let mirror = a[5] == "1";
    let hidden: usize = arg(a, 6, 256);
    let sbs: usize = arg(a, 7, 40);
    let bpsb: usize = arg(a, 8, 1024);
    let threads: usize = arg(a, 9, 2);
    let seed: u64 = arg(a, 10, 30_001);
    let lr0: f32 = arg(a, 11, 0.001);
    let wdl: f32 = arg(a, 12, 0.4);
    let mix: usize = arg(a, 13, 8);
    // CR item 10: refuse a warm start without explicit O30_CLIP and O30_DECAY before anything touches the GPU
    if std::env::var("O30_INIT_DIR").is_ok() && (std::env::var("O30_CLIP").is_err() || std::env::var("O30_DECAY").is_err()) {
        eprintln!("refusing: O30_INIT_DIR (warm start) needs O30_CLIP and O30_DECAY set explicitly; the defaults (clip +-1.98, \
                   decay 0.01) would clip / shrink the loaded net");
        std::process::exit(2);
    }
    let inputs = ForgeV2R { kmap, kb, mirror };
    let n_in = inputs.num_inputs();
    println!("forge_v2_bullet r: kb {kb} ({}) mirror {mirror} hidden {hidden} superbatches {sbs} x {bpsb} seed {seed} lr {lr0} wdl {wdl} mix {mix}", a[4]);
    let mut trainer = ValueTrainerBuilder::default()
        .dual_perspective()
        .seed(seed)
        .optimiser(AdamW)
        .inputs(inputs)
        .output_buckets(PieceCount8)
        .save_format(&[
            SavedFormat::id("l0w"),
            SavedFormat::id("l0b"),
            SavedFormat::id("l1w").transpose(),
            SavedFormat::id("l1b"),
        ])
        .loss_fn(|output, target| output.sigmoid().squared_error(target))
        // residual: prediction = sigmoid(out + hce * K / 400); the saved net is `out` (Forge adds its own HCE)
        .residual_base(|r: &ForgeRow| f32::from(r.hce) * (SIGMOID_K / 400.0))
        .build(|builder, stm_inputs, ntm_inputs, output_buckets| {
            let l0 = builder.new_affine("l0", n_in, hidden);
            let l1 = builder.new_affine("l1", 2 * hidden, OUTPUT_BUCKETS);
            let stm_hidden = l0.forward(stm_inputs).screlu();
            let ntm_hidden = l0.forward(ntm_inputs).screlu();
            l1.forward(stm_hidden.concat(ntm_hidden)).select(output_buckets)
        });
    // Warm start (GPU window 2026-11-04): O30_CLIP widens AdamW's weight clip (default +-1.98; a warm start from the
    // lock net needs about +-3.5, and +-7.99 still fits int16 at scale 4096); O30_INIT_DIR loads <dir>/optimiser_state
    // (weights.bin + zero momentum / velocity written by import_v2r.py) before the first superbatch. Unset = as before.
    // O30_DECAY: AdamW's decoupled weight decay (default 0.01); 0 = plain Adam like the CPU fine-tunes (a warm start
    // from a converged net would otherwise shrink by about 7 % over ~700k steps at lr 1e-5).
    if std::env::var("O30_CLIP").is_ok() || std::env::var("O30_DECAY").is_ok() {
        let clip: f32 = std::env::var("O30_CLIP").map(|s| s.parse().expect("O30_CLIP must be a number")).unwrap_or(1.98);
        let decay: f32 = std::env::var("O30_DECAY").map(|s| s.parse().expect("O30_DECAY must be a number")).unwrap_or(0.01);
        assert!(clip > 0.0 && clip < 8.0, "O30_CLIP must be in (0, 8)");
        assert!((0.0..=0.1).contains(&decay), "O30_DECAY must be in [0, 0.1]");
        use bullet_lib::nn::optimiser::AdamWParams;
        trainer.optimiser.set_params(AdamWParams { decay, beta1: 0.9, beta2: 0.999, min_weight: -clip, max_weight: clip });
        println!("AdamW weight clip +-{clip} decay {decay}");
    }
    if let Ok(dir) = std::env::var("O30_INIT_DIR") {
        // review G-001 / CR item 10: the defaults (+-1.98 clip, 0.01 decay) would clip / shrink a loaded net
        assert!(std::env::var("O30_CLIP").is_ok() && std::env::var("O30_DECAY").is_ok(),
                "O30_INIT_DIR needs O30_CLIP (>= the max |weight| import_v2r.py printed) and O30_DECAY set explicitly");
        println!("warm start from {dir}/optimiser_state");
        trainer.load_from_checkpoint(&dir);
    }
    let schedule = TrainingSchedule {
        net_id: format!("forge_v2r_{}_h{hidden}", a[4]),
        eval_scale: 400.0 / SIGMOID_K,
        steps: TrainingSteps { batch_size: 16_384, batches_per_superbatch: bpsb, start_superbatch: 1, end_superbatch: sbs },
        wdl_scheduler: wdl::ConstantWDL { value: wdl },
        lr_scheduler: lr::CosineDecayLR { initial_lr: lr0, final_lr: lr0 / 100.0, final_superbatch: sbs },
        save_rate: (sbs / 8).max(1),
    };
    let settings = LocalSettings { threads, test_set: None, output_directory: &a[3], batch_queue_size: 32 };
    let reader = FposReader::new(&a[2], POS, HCE, 1_000_000, mix, seed);
    println!("training rows (shards with role train): {}", reader.total_rows());
    trainer.run(&schedule, &settings, &reader);
}

fn main() {
    let a: Vec<String> = std::env::args().collect();
    if matches!(a.get(1).map(String::as_str), Some("r") | Some("rfeatures")) {
        main_r(&a);
        return;
    }
    if a.get(1).map(String::as_str) == Some("features") {
        assert!(a.len() == 4, "usage: forge-v2-bullet features <a|b|c> <fens.txt>");
        // forge-v2-bullet features <a|b|c> <fens.txt>: per FEN two lines, "S <stm indices>" and "N <ntm indices>",
        // plus "W" or "B" (side to move) first, for the parity reference (eval_ref.py)
        let inputs = ForgeV2::stage(&a[2]);
        let text = std::fs::read_to_string(&a[3]).expect("cannot read the FEN file");
        for fen in text.lines().map(str::trim).filter(|l| !l.is_empty()) {
            let board: ChessBoard = format!("{fen} | 0 | 0.5").parse().expect("bad FEN");
            let (mut s, mut n) = (Vec::new(), Vec::new());
            inputs.map_features(&board, |x, y| {
                s.push(x.to_string());
                n.push(y.to_string());
            });
            let stm = if fen.split_whitespace().nth(1) == Some("b") { "B" } else { "W" };
            println!("{stm}\nS {}\nN {}", s.join(" "), n.join(" "));
        }
        return;
    }
    assert!((4..=9).contains(&a.len()), "usage: forge-v2-bullet <a|b|c> <binpack> <out_dir> [hidden] [superbatches] [batches_per_sb] [threads] [seed]");
    let inputs = ForgeV2::stage(&a[1]);
    let data = a[2].clone();
    let out = a[3].clone();
    let hidden: usize = arg(&a, 4, 256);
    let sbs: usize = arg(&a, 5, 4);
    let bpsb: usize = arg(&a, 6, 1024);
    let threads: usize = arg(&a, 7, 2);
    let seed: u64 = arg(&a, 8, 13_401);
    println!("forge_v2_bullet stage {} hidden {hidden} superbatches {sbs} x {bpsb} seed {seed}", a[1]);
    let n_in = inputs.num_inputs();

    let mut trainer = ValueTrainerBuilder::default()
        .dual_perspective()
        .seed(seed)
        .optimiser(AdamW)
        .inputs(inputs)
        .output_buckets(MaterialCount::<OUTPUT_BUCKETS>)
        .save_format(&[
            SavedFormat::id("l0w"),
            SavedFormat::id("l0b"),
            SavedFormat::id("l1w").transpose(),
            SavedFormat::id("l1b"),
        ])
        .loss_fn(|output, target| output.sigmoid().squared_error(target))
        .build(|builder, stm_inputs, ntm_inputs, output_buckets| {
            let l0 = builder.new_affine("l0", n_in, hidden);
            let l1 = builder.new_affine("l1", 2 * hidden, OUTPUT_BUCKETS);
            let stm_hidden = l0.forward(stm_inputs).screlu();
            let ntm_hidden = l0.forward(ntm_inputs).screlu();
            l1.forward(stm_hidden.concat(ntm_hidden)).select(output_buckets)
        });

    let schedule = TrainingSchedule {
        net_id: format!("forge_v2_{}_h{hidden}", a[1]),
        eval_scale: 400.0 / SIGMOID_K,
        steps: TrainingSteps { batch_size: 16_384, batches_per_superbatch: bpsb, start_superbatch: 1, end_superbatch: sbs },
        wdl_scheduler: wdl::ConstantWDL { value: 0.4 },
        lr_scheduler: lr::CosineDecayLR { initial_lr: 0.001, final_lr: 0.0001, final_superbatch: sbs },
        save_rate: sbs,
    };
    let settings = LocalSettings { threads, test_set: None, output_directory: &out, batch_queue_size: 32 };

    use loader::sfbinpack::{MoveType, PieceType, SfBinpackLoader, TrainingDataEntry};
    fn filter(e: &TrainingDataEntry) -> bool {
        !e.pos.is_checked(e.pos.side_to_move())
            && e.score.unsigned_abs() <= 10000
            && e.mv.mtype() == MoveType::Normal
            && (e.mv.to().index() >= 64 || e.pos.piece_at(e.mv.to()).piece_type() == PieceType::None)
    }
    let data_loader = SfBinpackLoader::new(&data, 512, threads, filter);
    trainer.run(&schedule, &settings, &data_loader);
}
