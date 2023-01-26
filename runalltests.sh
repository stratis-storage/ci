#!/bin/bash

# Run all tests from the Stratis CI test suite
# Current distro: Fedora (29)

PRESTAGE=$(pwd)

./dependencies_fedora.sh

# The instructions for rustup say to run "curl https://sh.rustup.rs -sSf | sh".
# The resulting script has an interactive prompt, which would hang.
# Instead, download it to a shell script, and execute with the "-y" switch
# to automatically install.
curl -o install_rustup.sh https://sh.rustup.rs
chmod +x install_rustup.sh
./install_rustup.sh -y

# Load the Rust cargo env script.  Disable shellcheck, since it is
# intended to be in the home directory.
# shellcheck source=/dev/null
source $HOME/.cargo/env

rustup default 1.66.1

# Then, choose the directory of the test to be executed, and prep
# the $WORKSPACE environment variable.
# cd stratisd
# export WORKSPACE="/root/workspace/stratisd"

mkdir workspace
cd workspace || exit

if [ -s "/etc/stratis/test_config.json" ]; then
	STRATISD_MODE="test-real"
else
	STRATISD_MODE="test-loop"
fi
echo "Executing stratisd test ($STRATISD_MODE)"
git clone https://github.com/stratis-storage/stratisd.git
cd stratisd || exit
WORKSPACE=$(pwd)
export WORKSPACE
$PRESTAGE/stratisd.sh $STRATISD_MODE
RC_STRATISD=$?
echo "Completed stratisd test ($STRATISD_MODE): status $RC_STRATISD"
cd $PRESTAGE/workspace || exit

echo "End of prestage script."
echo "Results:"
echo "stratisd-$STRATISD_MODE: $RC_STRATISD"

if [ $RC_STRATISD -gt 0 ]; then
	exit 1
fi
