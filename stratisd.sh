#!/bin/bash
set -e

export PATH="$HOME/.cargo/bin:$PATH"
export RUST_LOG=libstratis=info
export TEST_BLOCKDEVS_FILE=/etc/stratis/test_config.json

TARGET=$1

if [ -z $TARGET ]
then
   echo "Usage: $0 test-loop | test-real"
   exit 1
fi

# Set WORKSPACE to the top level directory that contains the stratisd git repo
if [ -z $WORKSPACE ]
then
    echo "Required WORKSPACE variable not set. Set WORKSPACE to directory that contains"
    echo "stratisd git repo."
    exit 1
fi

if [ ! -d $WORKSPACE/tests/ ]
then
    echo "$WORKSPACE/tests/ does not exist.  Verify WORKSPACE is set to correct directory."
    exit 1
fi

# Each CI system must have a TEST_BLOCKDEVS_FILE file populated with
# block devices that are safe to use/overwrite on the system.
# Only check for this for "make test-real".
if [ $TARGET == "test-real" ]
then
    if [ -s "$TEST_BLOCKDEVS_FILE" ]
    then
        cp $TEST_BLOCKDEVS_FILE $WORKSPACE/tests/.
    else
        echo "Required file $TEST_BLOCKDEVS_FILE not found."
        exit 1
    fi
fi

cd $WORKSPACE
rustup default 1.38.0
cargo clean
make $TARGET
