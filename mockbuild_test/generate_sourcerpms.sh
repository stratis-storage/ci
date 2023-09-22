#!/bin/bash
set -e
set -x

if ! groups | grep mock; then
	echo 'No mock group membership; be sure to install mock'
	echo 'and add the current user to the "mock" group'
	exit 1
fi

DIST_RELEASE=$1

STRATISD_SPEC_VERSION=$(rpmspec -q --srpm --qf "%{version}\n" stratisd.spec)
STRATISCLI_SPEC_VERSION=$(rpmspec -q --srpm --qf "%{version}\n" stratis-cli.spec)

if [ -z "$DIST_RELEASE" ]; then
	echo "Usage: $0 centos-stream | fedora-rawhide"
	exit 1
fi

case $DIST_RELEASE in
"centos-stream")
	MOCKCONFIG="/etc/mock/centos-stream-9-x86_64.cfg"
	;;

"fedora-rawhide")
	MOCKCONFIG="/etc/mock/fedora-rawhide-x86_64.cfg"
	;;

"fedora-latest")
	MOCKCONFIG="/etc/mock/fedora-38-x86_64.cfg"
	;;

*)
	echo "Usage: $0 centos-stream | fedora-rawhide | fedora-latest"
	exit 1
	;;
esac

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
mkdir output/{stratisd,stratis-cli}

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
../../../release_management/create_artifacts.py ../../SOURCES/ --pre-release --specfile-path=../../SPECS/stratisd.spec stratisd "$STRATISD_SPEC_VERSION" --vendor-method=filtered
cd ..
cd stratis-cli
../../../release_management/create_artifacts.py ../../SOURCES/ --pre-release --specfile-path=../../SPECS/stratis-cli.spec stratis-cli "$STRATISCLI_SPEC_VERSION"
cd ../..

# Remove the "Requires: stratisd" line in stratis-cli.spec.
sed -i "/Requires.*stratisd/d" SPECS/stratis-cli.spec

mock --buildsrpm -r $MOCKCONFIG --spec SPECS/stratisd.spec --sources SOURCES/ --resultdir=SRPMS/stratisd/
mock --buildsrpm -r $MOCKCONFIG --spec SPECS/stratis-cli.spec --sources SOURCES/ --resultdir=SRPMS/stratis-cli/

for package in stratisd stratis-cli; do
	find SRPMS -name "$package*.rpm" -exec cp -v -t output/$package {} +
done
