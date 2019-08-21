#!/bin/bash

# Run all tests from the Stratis CI test suite
# Current distro: Fedora (29)

PRESTAGE=`pwd`

dnf -y install git \
	make \
	dbus-devel \
	gcc \
	systemd-devel \
	xfsprogs \
	python3-tox \
	python3-pytest \
	dbus-python \
	make \
	device-mapper-persistent-data \
	xfsprogs \
	python3-hypothesis \
	dbus-glib-devel \
	python3-justbytes.noarch \
	python3-setuptools \
	dbus-python-devel \
	python3-pyudev \
	python3-dateutil \
	python3-wcwidth \
	python3-pyparsing \
	dbus-devel.x86_64 \
	systemd-devel.x86_64 \
	glibc-devel.x86_64 \
	dbus-devel.i686 \
	systemd-devel.i686 \
	glibc-devel.i686 \
	openssl-devel

# The instructions for rustup say to run "curl https://sh.rustup.rs -sSf | sh".
# The resulting script has an interactive prompt, which would hang.
# Instead, download it to a shell script, and execute with the "-y" switch
# to automatically install.
curl -o install_rustup.sh https://sh.rustup.rs
chmod +x install_rustup.sh
./install_rustup.sh -y

source $HOME/.cargo/env

rustup default 1.36.0

# Then, choose the directory of the test to be executed, and prep
# the $WORKSPACE environment variable.
# cd stratisd
# export WORKSPACE="/root/workspace/stratisd"

mkdir workspace
cd workspace

if [ -s "$HOME/test_config.json" ]
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

echo "Executing devicemapper-rs test..."
git clone https://github.com/stratis-storage/devicemapper-rs.git
cd devicemapper-rs
export WORKSPACE=`pwd`
$PRESTAGE/dm_test.sh
RC_DEVMAPPER=$?
echo "Completed devicemapper-rs test: status $RC_DEVMAPPER"
cd $PRESTAGE/workspace

echo "End of prestage script."
echo "Results:"
echo "stratisd-$STRATISD_MODE: $RC_STRATISD"
echo "stratisd_nonrust: $RC_STRATISD_NONRUST"
echo "stratis-cli: $RC_STRATISCLI"
echo "devicemapper-rs: $RC_DEVMAPPER"
