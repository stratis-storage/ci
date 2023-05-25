#!/bin/bash
set -e

export STRATIS_DBUS_TIMEOUT=300000

if [ ! -e /etc/stratis/test_config.json ]; then
	echo "No test device config found; create a test_config.json"
	echo "file in /etc/stratis with three devices that can be"
	echo "overwritten for testing."
	exit 8
fi

# Create an array of test devices from the test_config.json file.
TESTDEVS_RESULT=$(./parse_json.py /etc/stratis/test_config.json)
IFS="," read -a TESTDEVS <<<"$(echo $TESTDEVS_RESULT)"

# Start running blackbox tests.
RC_BLACKBOX_STRATISD=0
RC_BLACKBOX_STRATIS_CLI=0

if [ -d testing ]; then
	rm -rf testing
fi

git clone https://github.com/stratis-storage/testing

echo "----------"
echo "Stratisd dbus timeout: $STRATIS_DBUS_TIMEOUT"
echo "Test devices: ${TESTDEVS[0]} ${TESTDEVS[1]} ${TESTDEVS[2]}"
echo "Executing blackbox test 'python3 stratisd_cert.py' against test devices..."
python3 ./testing/stratisd_cert.py -v --disk ${TESTDEVS[0]} --disk ${TESTDEVS[1]} --disk ${TESTDEVS[2]} || RC_BLACKBOX_STRATISD=1

echo "----------"
echo "Stratisd dbus timeout: $STRATIS_DBUS_TIMEOUT"
echo "Test devices: ${TESTDEVS[0]} ${TESTDEVS[1]} ${TESTDEVS[2]}"
echo "Executing blackbox test 'python3 stratis_cli_cert.py' against test devices..."
python3 ./testing/stratis_cli_cert.py -v --disk ${TESTDEVS[0]} --disk ${TESTDEVS[1]} --disk ${TESTDEVS[2]} || RC_BLACKBOX_STRATIS_CLI=1

echo "stratisd_cert result: $RC_BLACKBOX_STRATISD"
echo "stratis_cli_cert result: $RC_BLACKBOX_STRATIS_CLI"

if [ $RC_BLACKBOX_STRATISD -gt 0 ] && [ $RC_BLACKBOX_STRATIS_CLI -gt 0 ]; then
	exit 3
fi

if [ $RC_BLACKBOX_STRATIS_CLI -gt 0 ]; then
	exit 2
fi

if [ $RC_BLACKBOX_STRATISD -gt 0 ]; then
	exit 1
fi
