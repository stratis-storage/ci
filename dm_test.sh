#!/bin/bash
set -e

if [ -z "$RUST_CARGO_PATH" ]
then
    echo "Required RUST_CARGO_PATH environment variable not set"
    exit 1
fi

echo "Current Rust cargo path: $RUST_CARGO_PATH"

export PATH="$RUST_CARGO_PATH/bin:$PATH"
echo "Current path: $PATH"

# Set WORKSPACE to the top level directory that contains
# the devicemapper-rs git repo
if [ -z "$WORKSPACE" ]
then
    echo "Required WORKSPACE environment variable not set"
    exit 1
fi

cd $WORKSPACE

rustup default 1.37.0
cargo clean
STRATIS_DESTRUCTIVE_TEST=1 make sudo_test

# Cleanup the provided cargo directory's cache and registry
rm $RUST_CARGO_PATH/.package-cache
rm -r $RUST_CARGO_PATH/registry
