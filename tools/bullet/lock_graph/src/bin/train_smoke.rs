// Original bounded Forge GPU smoke driver using only MIT Bullet core APIs.
use std::{env, fs, io::{Read, Write}, path::Path, process, sync::Arc};
use bullet_trainer::{
    model::{ModelDefinition, ModelInputs, ModelInputsMapper, ModelWeights},
    optimiser::adam::{AdamW, AdamWParams},
    reader::{DataReader, ReadMapLoader},
    run::{DefaultDevice, TrainingSchedule, TrainingSteps, train, measure_max_cpu_throughput},
};

#[derive(Clone)]
struct Row { stm: [i32;32], other: [i32;32], hce: f32, score: f32 }
#[derive(Clone)]
struct Slice(Arc<Vec<Row>>);
impl DataReader<Row> for Slice {
    fn read_chunks<F: FnMut(&[Row])->bool>(&self, skip: usize, mut f: F) {
        if skip < self.0.len() { f(&self.0[skip..]); }
    }
}
fn load(path: &str)->Result<Vec<Row>,String> {
    let file=fs::File::open(path).map_err(|e|e.to_string())?;
    let size=file.metadata().map_err(|e|e.to_string())?.len();
    if !(12..=12+65536*136).contains(&size) {return Err("input outside bounded format size".into());}
    let mut bytes=Vec::new();file.take(size+1).read_to_end(&mut bytes).map_err(|e|e.to_string())?;
    if bytes.len() as u64 != size || &bytes[..4]!=b"FBS1" {return Err("invalid/changed input header".into());}
    let count=u64::from_le_bytes(bytes[4..12].try_into().unwrap()) as usize;
    if count==0 || count>65536 || bytes.len()!=12+136*count {return Err("input count/size mismatch".into());}
    let mut result=Vec::with_capacity(count);
    for data in bytes[12..].chunks_exact(136) {
        let mut row=Row{stm:[-1;32],other:[-1;32],hce:0.,score:0.};
        for (n, features) in [&mut row.stm,&mut row.other].into_iter().enumerate() {
            let mut padding=false;let mut seen=[false;768];let mut active=0;
            for j in 0..32 {
                let v=i16::from_le_bytes(data[64*n+2*j..64*n+2*j+2].try_into().unwrap()) as i32;
                if v == -1 {padding=true;} else {
                    if padding || !(0..768).contains(&v) || seen[v as usize] {return Err("invalid sparse feature sequence".into());}
                    seen[v as usize]=true;active+=1;
                }
                features[j]=v;
            }
            if active<2 {return Err("fewer than two active features".into());}
        }
        row.hce=f32::from_le_bytes(data[128..132].try_into().unwrap());
        row.score=f32::from_le_bytes(data[132..136].try_into().unwrap());
        if !row.hce.is_finite() || !row.score.is_finite() || row.hce.abs()>32767. || row.score.abs()>32767. {
            return Err("nonfinite/out-of-range score or HCE".into());
        }
        result.push(row);
    }
    Ok(result)
}
fn graph()->ModelDefinition {
    let b=bullet_compiler::model::ModelBuilder::default();
    let stm=b.new_sparse_input("stm",(768,1),32);
    let other=b.new_sparse_input("other",(768,1),32);
    let hce=b.new_dense_input("hce_cp",(1,1));
    let score=b.new_dense_input("score_cp",(1,1));
    let ft=b.new_affine("ft",768,256);let out=b.new_affine("out",512,1);
    let residual=out.forward(ft.forward(stm).screlu().concat(ft.forward(other).screlu()));
    let predicted=(hce*(2.25/400.)+residual).sigmoid();
    let target=(score*(2.25/400.)).sigmoid();
    let loss=predicted.squared_error(target).reduce_sum_batch();
    ModelDefinition::new(b.inner(),Some(loss.node()),[(residual.node(),"residual".to_owned())])
}
fn run()->Result<(),String> {
    let args:Vec<String>=env::args().collect();
    let check_input=args.len()==5 && args[4]=="--check-input";
    if args.len()!=4 && !check_input {return Err("usage: train_smoke INPUT.fbs NEW_OUTPUT_DIR BATCH_SIZE [--check-input]".into());}
    let rows=load(&args[1])?;
    let batch:usize=args[3].parse().map_err(|_|"invalid batch size")?;
    if batch==0 || batch>1024 || rows.len()%batch!=0 {return Err("batch must divide the bounded row count exactly, in1..1024".into());}
    if Path::new(&args[2]).exists() {return Err("output must be a NEW directory".into());}
    let count=rows.len();
    let inputs=ModelInputs::default().add_sparse("stm",(768,1),32)
        .add_sparse("other",(768,1),32).add_dense("hce_cp",(1,1)).add_dense("score_cp",(1,1));
    let mapper=ModelInputsMapper::build(&inputs,|row:&Row,_,(((stm,other),hce),score)|{
        stm.copy_from_slice(&row.stm);other.copy_from_slice(&row.other);hce[0]=row.hce;score[0]=row.score;
    });
    let definition=graph();
    let steps=TrainingSteps{batch_size:batch,batches_per_superbatch:count/batch,start_superbatch:1,end_superbatch:1};
    let loader=ReadMapLoader::new(Slice(Arc::new(rows)),mapper,1);
    if check_input {
        definition.lower_backward(&Default::default(),batch,false,false).map_err(|e|format!("backward IR: {e:?}"))?;
        measure_max_cpu_throughput(loader,steps).map_err(|e|format!("mapper smoke: {e:?}"))?;
        println!("INPUT_MAPPER_PASS rows{count} batches{}; no training; no output directory written",count/batch);
        return Ok(());
    }
    #[cfg(not(any(feature="rocm",feature="cuda")))]
    { return Err("GPU training not executed: enable rocm or cuda; CPU MockGpu cannot train".into()); }
    #[allow(unreachable_code)]
    let weights=ModelWeights::new(&definition,20261030);
    let device=DefaultDevice::new(0).map_err(|e|format!("GPU initialization: {e:?}"))?;
    let parameters=AdamWParams{decay:0.,beta1:0.9,beta2:0.999,min_weight:-32767./4096.,max_weight:32767./4096.};
    let mut optimizer=AdamW::new(definition,weights,device,parameters).map_err(|e|format!("optimizer: {e:?}"))?;
    fs::create_dir(&args[2]).map_err(|e|e.to_string())?;
    let schedule=TrainingSchedule{steps,log_rate:1,lr_schedule:Box::new(|_|0.0001),track_grad_norms:false};
    let mut nonfinite=false;
    train(&mut optimizer,schedule,loader,|_,step,loss|{nonfinite |= !loss.is_finite();println!("ORIGINAL_BATCH {} LOSS {}",step.total_batches(),loss);},|_,_|{})
        .map_err(|e|format!("GPU training failed, partial output retained: {e:?}"))?;
    if nonfinite {return Err("nonfinite training loss; no completed checkpoint claimed".into());}
    {
        let weights=optimizer.cpu_weights().map_err(|e|format!("CPU weight copy: {e:?}"))?;
        for (_,tensor) in weights.iter() {
            if tensor.values.f32().iter().any(|v|!v.is_finite()) {return Err("nonfinite final weights".into());}
        }
    }
    optimizer.write_to_checkpoint(&args[2]).map_err(|e|format!("checkpoint: {e:?}"))?;
    let mut receipt=fs::OpenOptions::new().write(true).create_new(true).open(Path::new(&args[2]).join("COMPLETE.txt")).map_err(|e|e.to_string())?;
    writeln!(receipt,"one epoch; rows{count}; batch{batch}; seed20261030; lr0.0001; HCE-conditioned pure-score target; no QAT; use lock_export manifest+export and native parity before use").map_err(|e|e.to_string())?;
    Ok(())
}
fn main(){if let Err(e)=run(){eprintln!("ERROR: {e}");process::exit(1);}}

#[cfg(test)]
mod tests {
    use super::*;
    #[test] fn real_training_graph_backward_ir_compiles_on_cpu() {
        graph().lower_backward(&Default::default(),64,false,false).unwrap();
    }
    #[test] fn size_count_and_truncation_rejected() {
        let p=env::temp_dir().join(format!("forge_bullet_bad_{}_{}.fbs",process::id(),std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos()));
        let mut f=fs::OpenOptions::new().write(true).create_new(true).open(&p).unwrap();
        f.write_all(b"FBS1\x01\x00\x00\x00\x00\x00\x00\x00").unwrap();drop(f);
        assert!(load(p.to_str().unwrap()).is_err());
        // Deliberately retain the generated rejection fixture; no source deletion.
    }
}
