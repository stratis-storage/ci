#!/bin/bash
set -e
set -x

if ! groups | grep mock; then
        echo 'No mock group membership; be sure to install mock'
        echo 'and add the current user to the "mock" group'
        exit 1
fi

DIST="fc37"
MOCKCONFIG="/etc/mock/fedora-rawhide-x86_64.cfg"

for mockdir in SOURCES SPECS SRPMS RPMS; do
        if [ -d $mockdir ]; then
                echo 'Clearing old mock rpm directories...'
                rm -rf $mockdir
        fi
done

mkdir {SOURCES,SPECS,SRPMS,RPMS}
mkdir {SRPMS,RPMS}/stratisd

cp stratisd.spec SPECS

if [ -d upstream ]; then
        rm -rf upstream
fi

mkdir upstream
cd upstream
git clone https://github.com/stratis-storage/stratisd
cd stratisd
../../../release_management/create_stratisd_artifacts.py ../../SOURCES/
cd ../..

mock --buildsrpm -r $MOCKCONFIG --spec SPECS/stratisd.spec --sources SOURCES/ --resultdir=SRPMS/stratisd/
mock --rebuild --without=check -r $MOCKCONFIG SRPMS/stratisd/stratisd-3.1.0-77.$DIST.src.rpm 
mock shell --no-clean -r $MOCKCONFIG 'for j in $(rpm -qa | grep "rust-.*-devel"); do rpm -q $j --qf "%{LICENSE}\n"; done | sort | uniq -c'
mock shell --no-clean -r $MOCKCONFIG 'for j in $(rpm -qa | grep "rust-.*-devel"); do rpm -q $j --qf "%{NAME} -- %{LICENSE}\n"; done'
