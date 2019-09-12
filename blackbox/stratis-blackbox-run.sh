#!/bin/bash
set -e

if [ ! -e /etc/stratis/test_config.json ]
then
	echo "No test device config found; create a ~/test_config.json"
	echo "file with three devices that can be overwritten for testing."
	exit 8
fi

# Create an array of test devices from the ~/test_config.json file.
# This is a naive search for device paths starting with "/dev", then
# stripping out the quote and comma characters.
TESTDEVS=($(grep \/dev /etc/stratis/test_config.json | tr -d \"\,))

if [ ! -e stratisd.spec -o ! -e stratis-cli.spec ]
then
	echo "Both stratisd.spec and stratis-cli.spec must be present."
	exit 4
fi

STRATISD_REPO="https://github.com/stratis-storage/stratisd.git"
STRATIS_CLI_REPO="https://github.com/stratis-storage/stratis-cli.git"

BASEDEPPKGS=(
	python3-dbus-client-gen
	python3-dbus-python-client-gen
	python3-justbytes
	rpm-build
	rpmdevtools
	asciidoc
	python3-devel
	dbus-devel
	rust-toolset
	systemd-devel
	rust
	cargo
	openssl-devel
	make
)

dnf -y install "${BASEDEPPKGS[@]}"

STRATISD_N=$(rpmspec -P stratisd.spec | grep ^Name | awk {'print $2'})
STRATISD_V=$(rpmspec -P stratisd.spec | grep ^Version | awk {'print $2'})
STRATISD_R=$(rpmspec -P stratisd.spec | grep ^Release | awk {'print $2'})
STRATISD_RPMBASENAME="${STRATISD_N}-${STRATISD_V}-${STRATISD_R}"
echo "stratisd package target: $STRATISD_RPMBASENAME"
STRATIS_CLI_N=$(rpmspec -P stratis-cli.spec | grep ^Name | awk {'print $2'})
STRATIS_CLI_V=$(rpmspec -P stratis-cli.spec | grep ^Version | awk {'print $2'})
STRATIS_CLI_R=$(rpmspec -P stratis-cli.spec | grep ^Release | awk {'print $2'})
STRATIS_CLI_RPMBASENAME="${STRATIS_CLI_N}-${STRATIS_CLI_V}-${STRATIS_CLI_R}"
echo "stratis-cli package target: $STRATIS_CLI_RPMBASENAME"

if [ -d output_rpms ]
then
	echo "output_rpms directory already exists.  Recreating..."
	rm -rvf output_rpms
fi
mkdir output_rpms
mkdir -p ~/rpmbuild/{BUILD,RPMS,SOURCES,SPECS}/

# Remove the previously created repository directories
rm -rf ${STRATISD_N}-${STRATISD_V}
rm -rf ${STRATIS_CLI_N}-${STRATIS_CLI_V}


# Build the stratisd package (along with the rust cargo vendor tarball)
echo "Building stratisd test package..."
git clone $STRATISD_REPO
echo "Most recent commits for ${STRATISD_N}:"
( cd $STRATISD_N; git status; git log --format="%h %ai :: %s" | head -10 )
mv -v ${STRATISD_N} ${STRATISD_N}-${STRATISD_V}
mkdir ${STRATISD_N}-${STRATISD_V}/vendor
tar czvf ~/rpmbuild/SOURCES/${STRATISD_N}-${STRATISD_V}.tar.gz ${STRATISD_N}-${STRATISD_V}
cd ${STRATISD_N}-${STRATISD_V}/
cargo vendor && tar cJf ../${STRATISD_N}-${STRATISD_V}-vendor.tar.xz vendor/
cd ..
cp ${STRATISD_N}-${STRATISD_V}-vendor.tar.xz ~/rpmbuild/SOURCES
echo "Executing rpmbuild for stratisd..."
rpmbuild -bb stratisd.spec

# Build the stratis-cli package
echo "Building stratis-cli test package..."
git clone $STRATIS_CLI_REPO
echo "Most recent commits for ${STRATIS_CLI_N}:"
( cd $STRATIS_CLI_N; git status; git log --format="%h %ai :: %s" | head -10 )
mv -v ${STRATIS_CLI_N} ${STRATIS_CLI_N}-${STRATIS_CLI_V}
tar czvf ~/rpmbuild/SOURCES/${STRATIS_CLI_N}-${STRATIS_CLI_V}.tar.gz ${STRATIS_CLI_N}-${STRATIS_CLI_V}
echo "Executing rpmbuild for stratis-cli..."
rpmbuild -bb stratis-cli.spec

# Find all of the stratis-related RPM files output via the rpmbuild
# stage, (including debuginfo and debugsource), and copy them to the
# staging directory.
find ~/rpmbuild/RPMS/ -name stratis*.rpm -exec cp -v {} output_rpms/ \;

dnf -y install output_rpms/$STRATISD_RPMBASENAME*.rpm output_rpms/$STRATIS_CLI_RPMBASENAME*.rpm

# Start running blackbox tests.
echo "----------"
echo "Test devices: ${TESTDEVS[0]} ${TESTDEVS[1]} ${TESTDEVS[2]}"
echo "Executing blackbox test 'python3 stratis_cli_cert.py' against test devices..."
python3 stratis-cli-1.0.9/tests/blackbox/stratis_cli_cert.py -v --disk ${TESTDEVS[0]} --disk ${TESTDEVS[1]} --disk ${TESTDEVS[2]} || echo "Test failed: stratis_cli_cert"

echo "----------"
echo "Test devices: ${TESTDEVS[0]} ${TESTDEVS[1]} ${TESTDEVS[2]}"
echo "Executing blackbox test 'python3 stratisd_cert.py' against test devices..."
python3 stratis-cli-1.0.9/tests/blackbox/stratisd_cert.py -v --disk ${TESTDEVS[0]} --disk ${TESTDEVS[1]} --disk ${TESTDEVS[2]} || echo "Test failed: stratisd_cert"

echo "----------"
echo "Cleaning rpmbuild directories"

rm -rfv ~/rpmbuild/RPMS/*
rm -rfv ~/rpmbuild/SOURCES/*
rm -rfv ~/rpmbuild/SPECS/*

dnf -y remove $STRATISD_RPMBASENAME $STRATIS_CLI_RPMBASENAME
