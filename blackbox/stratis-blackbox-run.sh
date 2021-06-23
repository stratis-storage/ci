#!/bin/bash
set -e

export STRATIS_DBUS_TIMEOUT=300000

if [ ! -e /etc/stratis/test_config.json ]
then
	echo "No test device config found; create a test_config.json"
	echo "file in /etc/stratis with three devices that can be"
	echo "overwritten for testing."
	exit 8
fi

# Create an array of test devices from the test_config.json file.
# This is a naive search for device paths starting with "/dev", then
# stripping out the quote and comma characters.
TESTDEVS_RESULT=$(./parse_json.py /etc/stratis/test_config.json)
IFS="," read -a TESTDEVS <<< "$(echo $TESTDEVS_RESULT)"

if [ ! -e stratisd.spec ] || [ ! -e stratis-cli.spec ]
then
	echo "Both stratisd.spec and stratis-cli.spec must be present."
	exit 4
fi

BASEDEPPKGS=(
	python3-dbus-client-gen
	python3-dbus-python-client-gen
	python3-justbytes
	python3-psutil
	rpm-build
	rpmdevtools
	asciidoc
	python3-devel
	dbus-devel
	systemd-devel
	rust
	cargo
	openssl-devel
	clang
	llvm
	llvm-devel
	cryptsetup-devel
	libblkid-devel
	make
)

dnf -y install "${BASEDEPPKGS[@]}"

STRATISD_N=$(rpmspec -P stratisd.spec | grep ^Name | awk '{print $2}')
STRATISD_V=$(rpmspec -P stratisd.spec | grep ^Version | awk '{print $2}')
STRATISD_R=$(rpmspec -P stratisd.spec | grep ^Release | awk '{print $2}')
STRATISD_RPMBASENAME="${STRATISD_N}-${STRATISD_V}-${STRATISD_R}"
echo "stratisd package target: $STRATISD_RPMBASENAME"
STRATIS_CLI_N=$(rpmspec -P stratis-cli.spec | grep ^Name | awk '{print $2}')
STRATIS_CLI_V=$(rpmspec -P stratis-cli.spec | grep ^Version | awk '{print $2}')
STRATIS_CLI_R=$(rpmspec -P stratis-cli.spec | grep ^Release | awk '{print $2}')
STRATIS_CLI_RPMBASENAME="${STRATIS_CLI_N}-${STRATIS_CLI_V}-${STRATIS_CLI_R}"
echo "stratis-cli package target: $STRATIS_CLI_RPMBASENAME"

./reset-upstream-stratis-repos.sh

echo "Starting build and package process..."
./build-and-package.sh

dnf -y install output_rpms/$STRATISD_RPMBASENAME*.rpm output_rpms/$STRATIS_CLI_RPMBASENAME*.rpm

# Start running blackbox tests.
RC_BLACKBOX_STRATISD=0
RC_BLACKBOX_STRATIS_CLI=0

if [ -d testing ]
then
	rm -rf testing
fi

git clone https://github.com/stratis-storage/testing

echo "----------"
echo "Stratisd dbus timeout: $STRATIS_DBUS_TIMEOUT"
echo "Test devices: ${TESTDEVS[0]} ${TESTDEVS[1]} ${TESTDEVS[2]}"
echo "Executing blackbox test 'python3 stratisd_cert.py' against test devices..."
python3 ./testing/stratisd_cert.py -v --disk ${TESTDEVS[0]} --disk ${TESTDEVS[1]} --disk ${TESTDEVS[2]} || RC_BLACKBOX_STRATISD=1

echo "----------"
echo "Stratisd dbus timeout: $STRATIS_DBUS_TIMEOUT"
echo "Test devices: ${TESTDEVS[0]} ${TESTDEVS[1]} ${TESTDEVS[2]}"
echo "Executing blackbox test 'python3 stratis_cli_cert.py' against test devices..."
python3 ./testing/stratis_cli_cert.py -v --disk ${TESTDEVS[0]} --disk ${TESTDEVS[1]} --disk ${TESTDEVS[2]} || RC_BLACKBOX_STRATIS_CLI=1

echo "----------"
echo "Cleaning rpmbuild directories"

rm -rfv ~/rpmbuild/RPMS/*
rm -rfv ~/rpmbuild/SOURCES/*
rm -rfv ~/rpmbuild/SPECS/*

dnf -y remove $STRATISD_RPMBASENAME $STRATIS_CLI_RPMBASENAME

echo "stratisd_cert result: $RC_BLACKBOX_STRATISD"
echo "stratis_cli_cert result: $RC_BLACKBOX_STRATIS_CLI"

if [ $RC_BLACKBOX_STRATISD -gt 0 ] && [ $RC_BLACKBOX_STRATIS_CLI -gt 0 ]
then
	exit 3
fi

if [ $RC_BLACKBOX_STRATIS_CLI -gt 0 ]
then
	exit 2
fi

if [ $RC_BLACKBOX_STRATISD -gt 0 ]
then
	exit 1
fi
