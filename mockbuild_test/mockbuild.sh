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
	DIST="el9"
	MOCKCONFIG="/etc/mock/centos-stream-9-x86_64.cfg"
	;;

"fedora-rawhide")
	DIST="fc38"
	MOCKCONFIG="/etc/mock/fedora-rawhide-x86_64.cfg"
	;;

"fedora-next")
	DIST="fc37"
	MOCKCONFIG="/etc/mock/fedora-37-x86_64.cfg"
	;;

"fedora-latest")
	DIST="fc36"
	MOCKCONFIG="/etc/mock/fedora-36-x86_64.cfg"
	;;

"fedora-previous")
	DIST="fc35"
	MOCKCONFIG="/etc/mock/fedora-35-x86_64.cfg"
	;;

*)
	echo "Usage: $0 centos-stream | fedora-rawhide | fedora-next | fedora-latest | fedora-previous"
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
../../../release_management/create_artifacts.py ../../SOURCES/ stratisd "$STRATISD_SPEC_VERSION"
cd ..
cd stratis-cli
../../../release_management/create_artifacts.py ../../SOURCES/ stratis-cli "$STRATISCLI_SPEC_VERSION"
cd ../..

mock --buildsrpm -r $MOCKCONFIG --spec SPECS/stratisd.spec --sources SOURCES/ --resultdir=SRPMS/stratisd/
mock --buildsrpm -r $MOCKCONFIG --spec SPECS/stratis-cli.spec --sources SOURCES/ --resultdir=SRPMS/stratis-cli/
mock --rebuild -r $MOCKCONFIG SRPMS/stratisd/stratisd-"$STRATISD_SPEC_VERSION"-77.$DIST.src.rpm --resultdir=RPMS/stratisd/
mock --rebuild -r $MOCKCONFIG SRPMS/stratis-cli/stratis-cli-"$STRATISCLI_SPEC_VERSION"-77.$DIST.src.rpm --resultdir=RPMS/stratis-cli/

for package in stratisd stratis-cli; do
	find RPMS -name "$package*.rpm" -exec cp -v -t output/$package {} +
	find SRPMS -name "$package*.rpm" -exec cp -v -t output/$package {} +
done
