use cargo_metadata::{CargoOpt, MetadataCommand};

fn main() {
    let metadata = MetadataCommand::new()
        .features(CargoOpt::AllFeatures)
        .exec()
        .unwrap();
    print!("Root package: {}\n", metadata.root_package().unwrap().name);
    for package in metadata.packages {
        print!("{}\n", package.name);
    }
}
