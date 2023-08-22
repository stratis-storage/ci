#!/bin/bash
set -e
set -x

if ! groups | grep mock; then
	echo 'No mock group membership; be sure to install mock'
	echo 'and add the current user to the "mock" group'
	exit 1
fi

DATECODE=$(date +%Y%m%d)
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
STRATISD_HEADREV=$(git rev-parse --short HEAD)
STRATISD_SUFFIX="~${DATECODE}git${STRATISD_HEADREV}"
../../../release_management/create_artifacts.py ../../SOURCES/ --pre-release-suffix="${STRATISD_SUFFIX}" stratisd "$STRATISD_SPEC_VERSION"
cd ..
cd stratis-cli
STRATISCLI_HEADREV=$(git rev-parse --short HEAD)
STRATISCLI_SUFFIX="~${DATECODE}git${STRATISCLI_HEADREV}"
../../../release_management/create_artifacts.py ../../SOURCES/ --pre-release-suffix="${STRATISCLI_SUFFIX}" stratis-cli "$STRATISCLI_SPEC_VERSION"
cd ../..

# Fix the "Requires: stratisd" line in stratis-cli.spec.
sed --in-place -E "s/(^Requires.*stratisd.*)${STRATISD_SPEC_VERSION}/\1${STRATISD_SPEC_VERSION}${STRATISD_SUFFIX}/g" SPECS/stratis-cli.spec

# Before running mock, the spec versions need to be changed.
sed --in-place -E "s/(^Version.*)${STRATISD_SPEC_VERSION}/\1${STRATISD_SPEC_VERSION}${STRATISD_SUFFIX}/g" SPECS/stratisd.spec
sed --in-place -E "s/(^Version.*)${STRATISCLI_SPEC_VERSION}/\1${STRATISCLI_SPEC_VERSION}${STRATISCLI_SUFFIX}/g" SPECS/stratis-cli.spec

mock --buildsrpm -r $MOCKCONFIG --spec SPECS/stratisd.spec --sources SOURCES/ --resultdir=SRPMS/stratisd/
mock --buildsrpm -r $MOCKCONFIG --spec SPECS/stratis-cli.spec --sources SOURCES/ --resultdir=SRPMS/stratis-cli/

for package in stratisd stratis-cli; do
	find SRPMS -name "$package*.rpm" -exec cp -v -t output/$package {} +
done
