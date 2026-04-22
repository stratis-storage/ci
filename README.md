# ci

A set of scripts intended to facilitate Continuous Integration (CI) testing for the various Stratis projects.

## CI scripts:

"stratisd.sh": stratisd test suite CI script (for the rust tests)

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
