use cargo_metadata::{CargoOpt, MetadataCommand};

fn main() {
    let metadata = MetadataCommand::new()
        .features(CargoOpt::AllFeatures)
        .exec()
        .unwrap();

    let resolve = metadata.resolve.as_ref().unwrap();

    let root_package = metadata.root_package().unwrap();
    let dependency_specs = &root_package.dependencies;

    let tree_root_id = resolve.root.as_ref().unwrap();

    assert!(&root_package.id == tree_root_id);

    let root_node = resolve
        .nodes
        .iter()
        .find(|n| &n.id == tree_root_id)
        .unwrap();
    let concrete_deps = &root_node.deps;

    assert!(concrete_deps.len() == dependency_specs.len());
}
