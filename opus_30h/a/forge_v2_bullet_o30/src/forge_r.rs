//! Opus 30-h job: residual Forge v2 nets (FORGENN2 feature set 0: piece-square inputs with king buckets + mirror,
//! 8 output buckets by piece count) trained from the self-play FPOS + FHCE shards with the lock net's residual target
//! (own code). Data = the o30_data.py output folder (D:\o30\data): shards with role "train" in AUDIT.json, skip lists
//! skip/<shard>.npy (int64 row indices) and jobA overrides override_npy/<shard>_index.npy (int64) + _score.npy (int16)
//! (o30_data_npy.py splits the .npz files, so this reader needs no zip code).
//! Target: b * sigmoid(score * K / 400) + (1 - b) * stm_result (the library's blend), prediction sigmoid(out + hce * K /
//! 400) through ValueTrainerBuilder::residual_base (patch of the private library copy, D:\o30\bullet). The saved net is
//! the output without the base: Forge adds its own hand-crafted evaluation (EvalFileV2 residual flag).
use std::{
    fs::File,
    io::{Read, Seek, SeekFrom},
    sync::Arc,
};

use bullet_lib::{
    game::{inputs::SparseInputType, outputs::OutputBuckets},
    value::loader::{DataReader, GameResult, LoadableDataType},
};

#[derive(Clone, Copy, Default, Debug)]
pub struct ForgeRow {
    /// FPOS board: two 4-bit piece codes per byte, squares a1..h8, P N B R Q K = 1-6, black = 7-12.
    pub board: [u8; 32],
    /// Side-to-move score in centipawns (jobA override applied).
    pub score: i16,
    /// Side-to-move hand-crafted evaluation (FHCE) in centipawns.
    pub hce: i16,
    /// 0 white, 1 black to move.
    pub stm: u8,
    /// Result for the side to move: 0 loss, 1 draw, 2 win.
    pub result: u8,
}

impl ForgeRow {
    pub fn code(&self, sq: usize) -> usize {
        let b = self.board[sq / 2];
        usize::from(if sq & 1 == 1 { b >> 4 } else { b & 15 })
    }
}

impl LoadableDataType for ForgeRow {
    fn score(&self) -> i16 {
        self.score
    }

    fn result(&self) -> GameResult {
        [GameResult::Loss, GameResult::Draw, GameResult::Win][usize::from(self.result.min(2))]
    }
}

/// Piece-square inputs with king buckets and optional mirroring, exactly as include/forge/nnue_v2.hpp:
/// kr = own king square in the perspective's frame, flip = 7 when mirrored and the king is on files e-h,
/// index = map[kr] * 768 + ((colour == p ? 0 : 1) * 6 + type) * 64 + ((p == white ? sq : sq ^ 56) ^ flip).
#[derive(Clone, Copy, Debug)]
pub struct ForgeV2R {
    pub kmap: [u8; 64],
    pub kb: usize,
    pub mirror: bool,
}

impl SparseInputType for ForgeV2R {
    type RequiredDataType = ForgeRow;

    fn num_inputs(&self) -> usize {
        self.kb * 768
    }

    fn max_active(&self) -> usize {
        32
    }

    fn map_features<F: FnMut(usize, usize)>(&self, pos: &ForgeRow, mut f: F) {
        let stm = usize::from(pos.stm);
        let mut ksq = [0usize; 2];
        for sq in 0..64 {
            match pos.code(sq) {
                6 => ksq[0] = sq,
                12 => ksq[1] = sq,
                _ => {}
            }
        }
        let key = |p: usize| {
            let kr = if p == 0 { ksq[0] } else { ksq[1] ^ 56 };
            let flip = if self.mirror && (kr & 7) >= 4 { 7 } else { 0 };
            (usize::from(self.kmap[kr]), flip)
        };
        let (bs, fs) = key(stm);
        let (bn, fnt) = key(1 - stm);
        for sq in 0..64 {
            let c = pos.code(sq);
            if c == 0 {
                continue;
            }
            let colour = (c - 1) / 6;
            let typ = (c - 1) % 6;
            let feat = |p: usize, bucket: usize, flip: usize| {
                let rel = usize::from(colour != p);
                let r = (if p == 0 { sq } else { sq ^ 56 }) ^ flip;
                bucket * 768 + (rel * 6 + typ) * 64 + r
            };
            f(feat(stm, bs, fs), feat(1 - stm, bn, fnt));
        }
    }

    fn shorthand(&self) -> String {
        format!("{}x768{}", self.kb, if self.mirror { "m" } else { "" })
    }

    fn description(&self) -> String {
        "Forge v2 piece-square inputs with king buckets (include/forge/nnue_v2.hpp)".to_string()
    }
}

/// 8 output buckets by the number of pieces (kings included): min(7, (pieces - 2) * 8 / 32) = Forge's default map.
#[derive(Clone, Copy, Default)]
pub struct PieceCount8;

impl OutputBuckets<ForgeRow> for PieceCount8 {
    const BUCKETS: usize = 8;

    fn bucket(&self, pos: &ForgeRow) -> u8 {
        let n = (0..64).filter(|&sq| pos.code(sq) != 0).count();
        (n.saturating_sub(2) * 8 / 32).min(7) as u8
    }
}

#[derive(Clone)]
struct Shard {
    pos: String,
    hce: String,
    rows: usize,
    skip: Arc<Vec<i64>>,
    ovr_index: Arc<Vec<i64>>,
    ovr_score: Arc<Vec<i16>>,
}

/// Streaming reader over the FPOS / FHCE shards: chunk c = `mix` blocks of block / mix rows from shards drawn (with
/// replacement, weighted by rows) by a generator seeded with (seed, c), overrides applied, skipped rows dropped, the
/// chunk shuffled. Deterministic in (seed, c), so a resumed run (skip_count) sees the same stream.
#[derive(Clone)]
pub struct FposReader {
    shards: Vec<Shard>,
    block: usize,
    mix: usize,
    seed: u64,
}

fn npy<T: Copy + Default>(path: &str, width: usize, decode: fn(&[u8]) -> T) -> Vec<T> {
    let mut raw = Vec::new();
    File::open(path).unwrap_or_else(|e| panic!("cannot open {path}: {e}")).read_to_end(&mut raw).unwrap();
    assert!(raw.len() >= 10 && &raw[..6] == b"\x93NUMPY", "{path}: not a .npy file");
    let (hlen, start) = if raw[6] == 1 {
        (usize::from(u16::from_le_bytes([raw[8], raw[9]])), 10)
    } else {
        (u32::from_le_bytes([raw[8], raw[9], raw[10], raw[11]]) as usize, 12)
    };
    let data = &raw[start + hlen..];
    assert!(data.len() % width == 0, "{path}: data size");
    data.chunks_exact(width).map(decode).collect()
}

fn split_mix(mut x: u64) -> u64 {
    x = x.wrapping_add(0x9E37_79B9_7F4A_7C15);
    x = (x ^ (x >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
    x = (x ^ (x >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
    x ^ (x >> 31)
}

struct Rng(u64);

impl Rng {
    fn next(&mut self) -> u64 {
        self.0 = split_mix(self.0);
        self.0
    }

    fn below(&mut self, n: u64) -> u64 {
        self.next() % n.max(1)
    }
}

fn read_at(f: &mut File, offset: u64, len: usize) -> Vec<u8> {
    let mut buf = vec![0u8; len];
    f.seek(SeekFrom::Start(offset)).unwrap();
    f.read_exact(&mut buf).unwrap();
    buf
}

impl FposReader {
    pub fn new(data_dir: &str, pos_dir: &str, hce_dir: &str, block: usize, mix: usize, seed: u64) -> Self {
        let audit = std::fs::read_to_string(format!("{data_dir}/AUDIT.json")).expect("AUDIT.json");
        // minimal parse: every `"forge_selfplay_NNN": {"rows": R, ... "role": "train"` entry
        let mut shards = Vec::new();
        for part in audit.split("\"forge_selfplay_").skip(1) {
            // only the keys of the "shards" object (`"forge_selfplay_NNN": {`), not the names in "holdout_shards"
            if part.len() < 7 || !part[3..].starts_with("\": {") {
                continue;
            }
            let name = format!("forge_selfplay_{}", &part[..3]);
            let rows: usize = part.split("\"rows\": ").nth(1).and_then(|s| s.split(|c: char| !c.is_ascii_digit()).next())
                .and_then(|s| s.parse().ok()).expect("rows");
            let role_train = part.split("\"role\": \"").nth(1).is_some_and(|s| s.starts_with("train"));
            if !role_train {
                continue;
            }
            let ovr = format!("{data_dir}/override_npy/{name}_index.npy");
            let (oi, os) = if std::path::Path::new(&ovr).exists() {
                (npy(&ovr, 8, |b| i64::from_le_bytes(b.try_into().unwrap())),
                 npy(&format!("{data_dir}/override_npy/{name}_score.npy"), 2, |b| i16::from_le_bytes(b.try_into().unwrap())))
            } else {
                (Vec::new(), Vec::new())
            };
            assert_eq!(oi.len(), os.len(), "{name}: override sizes");
            shards.push(Shard {
                pos: format!("{pos_dir}/{name}.pos"),
                hce: format!("{hce_dir}/{name}.hce"),
                rows,
                skip: Arc::new(npy(&format!("{data_dir}/skip/{name}.npy"), 8, |b| i64::from_le_bytes(b.try_into().unwrap()))),
                ovr_index: Arc::new(oi),
                ovr_score: Arc::new(os),
            });
        }
        assert!(!shards.is_empty(), "no training shards in {data_dir}/AUDIT.json");
        Self { shards, block, mix: mix.max(1), seed }
    }

    pub fn total_rows(&self) -> usize {
        self.shards.iter().map(|s| s.rows).sum()
    }

    fn piece(&self, s: &Shard, start: usize, m: usize, out: &mut Vec<ForgeRow>) {
        let n = s.rows as u64;
        let mut fp = File::open(&s.pos).unwrap_or_else(|e| panic!("{}: {e}", s.pos));
        let mut fh = File::open(&s.hce).unwrap_or_else(|e| panic!("{}: {e}", s.hce));
        let boards = read_at(&mut fp, 16 + 32 * start as u64, 32 * m);
        let scores = read_at(&mut fp, 16 + 32 * n + 2 * start as u64, 2 * m);
        let metas = read_at(&mut fp, 16 + 34 * n + start as u64, m);
        let hces = read_at(&mut fh, 16 + 2 * start as u64, 2 * m);
        let lo = s.skip.partition_point(|&x| x < start as i64);
        let hi = s.skip.partition_point(|&x| x < (start + m) as i64);
        let skipped: std::collections::HashSet<i64> = s.skip[lo..hi].iter().copied().collect();
        let olo = s.ovr_index.partition_point(|&x| x < start as i64);
        let ohi = s.ovr_index.partition_point(|&x| x < (start + m) as i64);
        let mut k = olo;
        for i in 0..m {
            let row = (start + i) as i64;
            let mut score = i16::from_le_bytes([scores[2 * i], scores[2 * i + 1]]);
            while k < ohi && s.ovr_index[k] < row {
                k += 1;
            }
            if k < ohi && s.ovr_index[k] == row {
                score = s.ovr_score[k];
            }
            if skipped.contains(&row) {
                continue;
            }
            let meta = metas[i];
            let stm = meta & 1;
            let white = meta >> 1; // 0 loss, 1 draw, 2 win for white
            let result = if stm == 0 { white } else { 2 - white.min(2) };
            let mut board = [0u8; 32];
            board.copy_from_slice(&boards[32 * i..32 * i + 32]);
            out.push(ForgeRow { board, score, hce: i16::from_le_bytes([hces[2 * i], hces[2 * i + 1]]), stm, result });
        }
    }

    pub fn chunk(&self, c: u64) -> Vec<ForgeRow> {
        let mut rng = Rng(split_mix(self.seed ^ split_mix(c.wrapping_add(1))));
        let total = self.total_rows() as u64;
        let mut out = Vec::with_capacity(self.block);
        for _ in 0..self.mix {
            let mut pick = rng.below(total);
            let mut idx = 0;
            while pick >= self.shards[idx].rows as u64 {
                pick -= self.shards[idx].rows as u64;
                idx += 1;
            }
            let s = &self.shards[idx];
            let m = (self.block / self.mix).min(s.rows);
            let start = rng.below((s.rows - m + 1) as u64) as usize;
            self.piece(s, start, m, &mut out);
        }
        for i in (1..out.len()).rev() {
            let j = rng.below(i as u64 + 1) as usize;
            out.swap(i, j);
        }
        out
    }
}

impl DataReader<ForgeRow> for FposReader {
    fn read_chunks<F: FnMut(&[ForgeRow]) -> bool>(&self, skip_count: usize, mut f: F) {
        let mut skipped = 0usize;
        let mut c = 0u64;
        loop {
            let rows = self.chunk(c);
            c += 1;
            let mut slice = &rows[..];
            if skipped < skip_count {
                let k = (skip_count - skipped).min(slice.len());
                skipped += k;
                slice = &slice[k..];
                if slice.is_empty() {
                    continue;
                }
            }
            // bullet's contract (trainer/src/reader.rs, every library reader): the callback returns true to STOP.
            // The first GPU smoke (2026-11-04 10:13) stopped after one chunk with the inverted test.
            if f(slice) {
                return;
            }
        }
    }
}
