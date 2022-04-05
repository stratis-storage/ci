#!/bin/bash
set -e
set -x

mkdir {SOURCES,SPECS,SRPMS,RPMS}
mkdir {SRPMS,RPMS}/{stratisd,stratis-cli}
mkdir output

cp stratisd.spec SPECS
cp stratis-cli.spec SPECS

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

mock --buildsrpm -r /etc/mock/centos-stream-9-x86_64.cfg --spec SPECS/stratisd.spec --sources SOURCES/ --resultdir=SRPMS/stratisd/
mock --buildsrpm -r /etc/mock/centos-stream-9-x86_64.cfg --spec SPECS/stratis-cli.spec --sources SOURCES/ --resultdir=SRPMS/stratis-cli/
mock --rebuild -r /etc/mock/centos-stream-9-x86_64.cfg SRPMS/stratisd/stratisd-3.1.0-77.el9.src.rpm --resultdir=RPMS/stratisd/
mock --rebuild -r /etc/mock/centos-stream-9-x86_64.cfg SRPMS/stratis-cli/stratis-cli-3.1.0-77.el9.src.rpm --resultdir=RPMS/stratis-cli/

find RPMS -name '*.rpm' | xargs cp -v -t output
find SRPMS -name '*.rpm' | xargs cp -v -t output
