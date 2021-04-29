#!/bin/bash
set -e

if [ ! -d SOURCES ]
then
	mkdir SOURCES
fi

if [ ! -d SPECS ]
then
	mkdir SPECS
fi

if [ -d stratisd-77.77.77 ]
then
	rm -rf stratisd-77.77.77
fi

if [ -d ci ]
then
	rm -rf ci
fi

if [ -d output_rpms ]
then
	rm -rf output_rpms
fi
mkdir output_rpms


dnf config-manager --set-enable updates-testing
dnf -y install rpm-build mock cargo git

git clone https://github.com/stratis-storage/stratisd stratisd-77.77.77
git clone https://github.com/stratis-storage/ci.git
cd stratisd-77.77.77/
git checkout v2.3.0
cd ..
tar czf ./SOURCES/stratisd-77.77.77.tar.gz stratisd-77.77.77
sha512sum SOURCES/stratisd-77.77.77.tar.gz
cd stratisd-77.77.77/
cargo vendor && tar czvf ../SOURCES/stratisd-77.77.77-vendor.tar.gz vendor/
cd ..
sha512sum SOURCES/stratisd-77.77.77-vendor.tar.gz
cp ci/unified/stratisd.spec SPECS/
rpmbuild -bs --define "_topdir $(pwd)" SPECS/stratisd.spec
mock -r fedora-rawhide-x86_64 SRPMS/stratisd-77.77.77-77.fc32.src.rpm
mock_status=$?

echo "mock status: $mock_status"
sha512sum SOURCES/stratisd-77.77.77.tar.gz
sha512sum SOURCES/stratisd-77.77.77-vendor.tar.gz

cp -v /var/lib/mock/fedora-rawhide-x86_64/result/*.rpm output_rpms/
