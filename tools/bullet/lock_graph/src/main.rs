// Original Forge AL1 graph using MIT Bullet compiler/trainer public APIs only.
// This creates an actual Bullet-initialized checkpoint, NOT a trained network.
// Deliberately avoids bullet_lib's unconditional GPL/AGPL format dependencies.
use std::{env, fs::OpenOptions, process};
use bullet_compiler::model::ModelBuilder;
use bullet_trainer::model::{ModelDefinition, ModelWeights};

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len()!=2 {
        eprintln!("usage: forge-lock-bullet-graph NEW_WEIGHTS_BIN");
        eprintln!("CPU graph/checkpoint initialization ONLY. No training occurs.");
        process::exit(2);
    }
    let builder=ModelBuilder::default();
    let stm=builder.new_sparse_input("stm",(768,1),32);
    let other=builder.new_sparse_input("other",(768,1),32);
    let hce_cp=builder.new_dense_input("hce_cp",(1,1));
    let score_cp=builder.new_dense_input("score_cp",(1,1));
    let transform=builder.new_affine("ft",768,256);
    let output=builder.new_affine("out",512,1);
    let own_hidden=transform.forward(stm).screlu();
    let other_hidden=transform.forward(other).screlu();
    let residual=output.forward(own_hidden.concat(other_hidden));
    // Same pure search-score residual objective as the offline CPU smoke:
    // sigmoid(HCE*K/400 + residual) against sigmoid(score*K/400).
    // HCE is an auxiliary training input, absent from the exported residual net.
    let prediction=(hce_cp*(2.25/400.0)+residual).sigmoid();
    let target=(score_cp*(2.25/400.0)).sigmoid();
    let loss=prediction.squared_error(target).reduce_sum_batch();
    let definition=ModelDefinition::new(builder.inner(),Some(loss.node()),[(residual.node(),"residual".to_owned())]);
    let weights=ModelWeights::new(&definition,20261030);
    let mut file=OpenOptions::new().write(true).create_new(true).open(&args[1])
        .expect("checkpoint must be a new writable file");
    weights.write_into(&mut file).expect("Bullet checkpoint serialization failed");
    println!("BULLET_INITIALIZED_NOT_TRAINED: four tensors,768->256 dual SCReLU->1 residual; seed20261030; HCE-conditioned score-only graph");
}
