# ci

A set of scripts intended to facilitate Continuous Integration (CI) testing for the various Stratis projects.

## General script:

"runalltests.sh": Install the dependency packages, and run all of the CI tests.  (Run this script if setting up on a new system.)

Note that the "runalltests.sh" script will clone the "stratisd", "stratis-cli", and "devicemapper-rs" repositories, and execute the appropriate tests.

## CI scripts:

"cli.sh": stratis-cli test suite CI script

"dm_test.sh": devicemapper-rs test suite CI script

"stratisd.sh": stratisd test suite CI script (for the rust tests)

"stratisd_nonrust.sh": stratisd test suite CI script (for the client-dbus tests)
