#!/bin/bash
set -e

STRATISD_REPO="https://github.com/stratis-storage/stratisd.git"
STRATIS_CLI_REPO="https://github.com/stratis-storage/stratis-cli.git"

STRATISD_N=$(rpmspec -P stratisd.spec | grep ^Name | awk {'print $2'})
STRATISD_V=$(rpmspec -P stratisd.spec | grep ^Version | awk {'print $2'})
STRATISD_R=$(rpmspec -P stratisd.spec | grep ^Release | awk {'print $2'})
STRATISD_RPMBASENAME="${STRATISD_N}-${STRATISD_V}-${STRATISD_R}"
STRATIS_CLI_N=$(rpmspec -P stratis-cli.spec | grep ^Name | awk {'print $2'})
STRATIS_CLI_V=$(rpmspec -P stratis-cli.spec | grep ^Version | awk {'print $2'})
STRATIS_CLI_R=$(rpmspec -P stratis-cli.spec | grep ^Release | awk {'print $2'})
STRATIS_CLI_RPMBASENAME="${STRATIS_CLI_N}-${STRATIS_CLI_V}-${STRATIS_CLI_R}"

# Remove the previously created repository directories
echo "Removing the previously created stratisd repo directory"
rm -rf ${STRATISD_N}-${STRATISD_V}
echo "Removing the previously created stratis-cli repo directory"
rm -rf ${STRATIS_CLI_N}-${STRATIS_CLI_V}

git clone $STRATISD_REPO
echo "Most recent commits for ${STRATISD_N}:"
( cd $STRATISD_N; git status; git log --format="%h %ci :: %s" | head -20 )
mv -v ${STRATISD_N} ${STRATISD_N}-${STRATISD_V}

if [ ! -z "$STRATISD_REMOTE" ] && [ ! -z "STRATISD_BRANCH" ]
then
	git remote add blackbox $STRATISD_REMOTE
	git checkout -b blackbox blackbox/$STRATISD_BRANCH
fi

git clone $STRATIS_CLI_REPO
echo "Most recent commits for ${STRATIS_CLI_N}:"
( cd $STRATIS_CLI_N; git status; git log --format="%h %ci :: %s" | head -20 )
mv -v ${STRATIS_CLI_N} ${STRATIS_CLI_N}-${STRATIS_CLI_V}

if [ ! -z "$STRATIS_CLI_REMOTE" ] && [ ! -z "STRATIS_CLI_BRANCH" ]
then
	git remote add blackbox $STRATIS_CLI_REMOTE
	git checkout -b blackbox blackbox/$STRATIS_CLI_BRANCH
fi
