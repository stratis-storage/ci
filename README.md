# ci

A set of scripts intended to facilitate Continuous Integration (CI) testing for the various Stratis projects.

## General script:

"runalltests.sh": Install the dependency packages, and run all of the CI tests.  (Run this script if setting up on a new system.)

Note that the "runalltests.sh" script will clone the "stratisd" and "stratis-cli" repositories, and execute the appropriate tests.

## CI scripts:

"cli.sh": stratis-cli test suite CI script

"stratisd.sh": stratisd test suite CI script (for the rust tests)

"stratisd_nonrust.sh": stratisd test suite CI script (for the client-dbus tests)

# Running the stratisd test with real devices

To run the stratisd test with scratch test devices, create the file `/etc/stratis/test_config.json`.

The stratisd test requires four scratch devices, which should be at least about 8 GiB in size.

The contents of the `test_config.json` file should be a JSON array of paths to the scratch devices.  For example:

```
{
    "ok_to_destroy_dev_array_key": [
    				   "/dev/vdb",
    				   "/dev/vdc",
    				   "/dev/vdd",
    				   "/dev/vde"
    ]
}
```

Be sure that the last item in the array does not have a trailing comma.
