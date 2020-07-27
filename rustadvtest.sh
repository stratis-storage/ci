#!/bin/bash

# Install rust and cargo from a Fedora advisory,
# then run the stratisd.sh test suite.

set -e

PRESTAGE=$(pwd)

ADVISORY=$1

if [ -z $ADVISORY ]
then
	echo "Usage: $0 <advisory>"
	echo "  (where <advisory> is the FEDORA-YYYY-XXXXXXXXXX string)"
	echo "   used in the --advisory parameter of a dnf command"
	echo "   for installing an updates-testing package)"
	exit 1
fi

if [ ! -s /etc/stratis/test_config.json ]
then
	echo "This script requires test devices to be defined"
	echo "in the file /etc/stratis/test_config.json."
	exit 1
fi

./dependencies_fedora.sh

dnf -y install cargo rust --enablerepo=updates-testing --advisory=$ADVISORY

if [ -d workspace ]
then
	echo -n "Removing prior workspace directory..."
	rm -rf workspace
	echo " done."
fi
mkdir workspace
cd workspace

git clone https://github.com/stratis-storage/stratisd.git
cd stratisd
export WORKSPACE=$(pwd)

$PRESTAGE/stratisd.sh test-real
