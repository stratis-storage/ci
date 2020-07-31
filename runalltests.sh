#!/bin/bash

# Run all tests from the Stratis CI test suite
# Current distro: Fedora (29)

PRESTAGE=`pwd`

./dependencies_fedora.sh

# The instructions for rustup say to run "curl https://sh.rustup.rs -sSf | sh".
# The resulting script has an interactive prompt, which would hang.
# Instead, download it to a shell script, and execute with the "-y" switch
# to automatically install.
curl -o install_rustup.sh https://sh.rustup.rs
chmod +x install_rustup.sh
./install_rustup.sh -y

source $HOME/.cargo/env

rustup default 1.45.0

# Then, choose the directory of the test to be executed, and prep
# the $WORKSPACE environment variable.
# cd stratisd
# export WORKSPACE="/root/workspace/stratisd"

mkdir workspace
cd workspace

if [ -s "/etc/stratis/test_config.json" ]
then
	STRATISD_MODE="test-real"
else
	STRATISD_MODE="test-loop"
fi
echo "Executing stratisd test ($STRATISD_MODE)"
git clone https://github.com/stratis-storage/stratisd.git
cd stratisd
export WORKSPACE=`pwd`
$PRESTAGE/stratisd.sh $STRATISD_MODE
RC_STRATISD=$?
echo "Completed stratisd test ($STRATISD_MODE): status $RC_STRATISD"
echo "Executing stratisd_nonrust test..."
$PRESTAGE/stratisd_nonrust.sh
RC_STRATISD_NONRUST=$?
echo "Completed stratisd_nonrust test: status $RC_STRATISD_NONRUST"
cd $PRESTAGE/workspace

echo "Executing stratis-cli test..."
git clone https://github.com/stratis-storage/stratis-cli
cd stratis-cli
export WORKSPACE=`pwd`
$PRESTAGE/cli.sh
RC_STRATISCLI=$?
echo "Completed stratis-cli test: status $RC_STRATISCLI"
cd $PRESTAGE/workspace

echo "End of prestage script."
echo "Results:"
echo "stratisd-$STRATISD_MODE: $RC_STRATISD"
echo "stratisd_nonrust: $RC_STRATISD_NONRUST"
echo "stratis-cli: $RC_STRATISCLI"

if [ $RC_STRATISD -gt 0 ]
then
	exit 1
fi

if [ $RC_STRATISCLI -gt 0 ]
then
	exit 2
fi

if [ $RC_STRATISD_NONRUST -gt 0 ]
then
	exit 4
fi
