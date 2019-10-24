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
# the stratis-cli git repo
if [ -z "$WORKSPACE" ]
then
    echo "Required WORKSPACE environment variable not set"
    exit 1
fi

export STRATIS_DEPS_DIR=$WORKSPACE/stratis-deps

cd $WORKSPACE

# If there is a stale STRATIS_DEPS_DIR remove it
if [ -d $STRATIS_DEPS_DIR ]
then
    rm -rf $STRATIS_DEPS_DIR
fi


mkdir $STRATIS_DEPS_DIR
cd $STRATIS_DEPS_DIR

# Clone the dependencies
git clone https://github.com/stratis-storage/dbus-python-client-gen.git
git clone https://github.com/stratis-storage/dbus-client-gen.git
git clone https://github.com/stratis-storage/into-dbus-python.git
git clone https://github.com/stratis-storage/dbus-signature-pyparsing.git
git clone https://github.com/stratis-storage/stratis-cli.git

if [ ! -f  /etc/dbus-1/system.d/stratisd.conf ]
then
    cp $WORKSPACE/stratisd.conf /etc/dbus-1/system.d/
fi

# Switch to the stratisd directory, which is the $WORKSPACE directory.
cd $WORKSPACE
make build

for STRATIS_DEP in dbus-client-gen dbus-signature-pyparsing dbus-python-client-gen into-dbus-python
do
    cd $STRATIS_DEPS_DIR/$STRATIS_DEP
    git fetch --tags
    LATEST_TAG=$(git describe --tags `git rev-list --tags --max-count=1`)
    echo "checking out $STRATIS_DEP $LATEST_TAG"
    git checkout $LATEST_TAG
done

# Now switch to the stratis-cli directory, which is in $STRATIS_DEPS_DIR.
cd $STRATIS_DEPS_DIR/stratis-cli
# Set the PYTHONPATH to use the dependencies
export PYTHONPATH=src:$STRATIS_DEPS_DIR/dbus-client-gen/src:$STRATIS_DEPS_DIR/dbus-python-client-gen/src:$STRATIS_DEPS_DIR/into-dbus-python/src:$STRATIS_DEPS_DIR/dbus-signature-pyparsing/src
# Set the stratisd binary base location to $WORKSPACE
export STRATISD=$WORKSPACE/target/debug/stratisd
make dbus-tests

# Cleanup the provided cargo directory's cache and registry
rm $RUST_CARGO_PATH/.package-cache
rm -r $RUST_CARGO_PATH/registry
