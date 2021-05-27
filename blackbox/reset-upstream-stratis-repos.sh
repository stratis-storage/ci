#!/bin/bash
set -e

STRATISD_REPO="https://github.com/stratis-storage/stratisd.git"
STRATIS_CLI_REPO="https://github.com/stratis-storage/stratis-cli.git"

STRATISD_N=$(rpmspec -P stratisd.spec | grep ^Name | awk {'print $2'})
STRATISD_V=$(rpmspec -P stratisd.spec | grep ^Version | awk {'print $2'})
STRATISD_R=$(rpmspec -P stratisd.spec | grep ^Release | awk {'print $2'})
STRATISD_DIR=${STRATISD_N}-${STRATISD_V}
STRATISD_RPMBASENAME="${STRATISD_N}-${STRATISD_V}-${STRATISD_R}"
STRATIS_CLI_N=$(rpmspec -P stratis-cli.spec | grep ^Name | awk {'print $2'})
STRATIS_CLI_V=$(rpmspec -P stratis-cli.spec | grep ^Version | awk {'print $2'})
STRATIS_CLI_R=$(rpmspec -P stratis-cli.spec | grep ^Release | awk {'print $2'})
STRATIS_CLI_DIR=${STRATIS_CLI_N}-${STRATIS_CLI_V}
STRATIS_CLI_RPMBASENAME="${STRATIS_CLI_N}-${STRATIS_CLI_V}-${STRATIS_CLI_R}"

# Remove the previously created repository directories
echo "Removing the previously created stratisd repo directory"
rm -rf $STRATISD_DIR
echo "Removing the previously created stratis-cli repo directory"
rm -rf $STRATIS_CLI_DIR

git clone $STRATISD_REPO $STRATISD_DIR
echo "Most recent commits for ${STRATISD_N}:"
( cd $STRATISD_DIR; git status; git log --format="%h %ci :: %s" | head -20 )

if [ ! -z "$STRATISD_REMOTE" ] && [ ! -z "$STRATISD_BRANCH" ]
then
	cd $STRATISD_DIR
	git remote add blackbox $STRATISD_REMOTE
	git fetch blackbox
	git checkout -b blackbox blackbox/$STRATISD_BRANCH
	cd ..
fi

git clone $STRATIS_CLI_REPO $STRATIS_CLI_DIR
echo "Most recent commits for ${STRATIS_CLI_N}:"
( cd $STRATIS_CLI_DIR; git status; git log --format="%h %ci :: %s" | head -20 )

if [ ! -z "$STRATIS_CLI_REMOTE" ] && [ ! -z "$STRATIS_CLI_BRANCH" ]
then
	cd $STRATIS_CLI_DIR
	git remote add blackbox $STRATIS_CLI_REMOTE
	git fetch blackbox
	git checkout -b blackbox blackbox/$STRATIS_CLI_BRANCH
	cd ..
fi
