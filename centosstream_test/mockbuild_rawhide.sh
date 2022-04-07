#!/bin/bash
set -e
set -x

if ! groups | grep mock; then
	echo 'No mock group membership; be sure to install mock'
	echo 'and add the current user to the "mock" group'
	exit 1
fi

if [ -d output ]; then
	echo 'Clearing old output directory...'
	rm -rf output
fi

for mockdir in SOURCES SPECS SRPMS RPMS; do
	if [ -d $mockdir ]; then
		echo 'Clearing old mock rpm directories...'
		rm -rf $mockdir
	fi
done

mkdir {SOURCES,SPECS,SRPMS,RPMS}
mkdir {SRPMS,RPMS}/{stratisd,stratis-cli}
mkdir output

cp stratisd.spec SPECS
cp stratis-cli.spec SPECS

if [ -d upstream ]; then
	rm -rf upstream
fi

mkdir upstream
cd upstream
git clone https://github.com/stratis-storage/stratisd
git clone https://github.com/stratis-storage/stratis-cli
cd stratisd
../../../release_management/create_stratisd_artifacts.py ../../SOURCES/
cd ..
cd stratis-cli
../../../release_management/create_stratis_cli_artifacts.py ../../SOURCES/
cd ../..

mock --buildsrpm -r /etc/mock/fedora-rawhide-x86_64.cfg --spec SPECS/stratisd.spec --sources SOURCES/ --resultdir=SRPMS/stratisd/
mock --buildsrpm -r /etc/mock/fedora-rawhide-x86_64.cfg --spec SPECS/stratis-cli.spec --sources SOURCES/ --resultdir=SRPMS/stratis-cli/
mock --rebuild -r /etc/mock/fedora-rawhide-x86_64.cfg SRPMS/stratisd/stratisd-3.1.0-77.fc37.src.rpm --resultdir=RPMS/stratisd/
mock --rebuild -r /etc/mock/fedora-rawhide-x86_64.cfg SRPMS/stratis-cli/stratis-cli-3.1.0-77.fc37.src.rpm --resultdir=RPMS/stratis-cli/

find RPMS -name '*.rpm' -exec cp -v -t output {} +
find SRPMS -name '*.rpm' -exec cp -v -t output {} +
