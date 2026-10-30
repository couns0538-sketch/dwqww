// Original independent-loader qualification wrapper.
// IDEA_SOURCE: user full-FEN transport contract; official MIT bulletformat API.
use bulletformat::{ChessBoard, DataLoader};
use std::{env, fs::File, io::{BufRead, BufReader}};
fn main() {
    let a: Vec<String> = env::args().collect();
    assert_eq!(a.len(), 3, "usage: checker rows.bullet rows.txt");
    let bytes = std::fs::metadata(&a[1]).unwrap().len();
    assert_eq!(bytes % 32, 0, "truncated bullet record");
    let mut lines = BufReader::new(File::open(&a[2]).unwrap()).lines();
    let loader = DataLoader::<ChessBoard>::new(&a[1], 4).unwrap();
    let mut count = 0usize;
    loader.map_positions(|actual| {
        let line = lines.next().expect("short sidecar").unwrap();
        let f: Vec<_> = line.split('|').map(str::trim).collect();
        assert_eq!(f.len(), 3);
        let fen: Vec<_> = f[0].split_whitespace().collect();
        assert_eq!(fen.len(), 6);
        let stm_cp: i16 = f[1].parse().unwrap();
        let white_cp = if fen[1] == "b" { -stm_cp } else { stm_cp };
        let input = format!("{} | {} | {}", f[0], white_cp, f[2]);
        let expected: ChessBoard = input.parse().unwrap();
        assert_eq!(actual, &expected, "record {} differs", count);
        count += 1;
    });
    assert!(lines.next().is_none(), "extra sidecar rows");
    assert_eq!(count as u64, bytes / 32);
    println!("{{\"status\":\"PASS\",\"rows\":{},\"mismatches\":0}}", count);
}
