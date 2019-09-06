# Stratis blackbox test run script

The stratis-blackbox-run.sh script builds a set of testing RPM packages of the stratisd and stratis-cli master branches, runs a series of "blackbox" tests against the version of Stratis installed by these packages, and then uninstalls the packages.

The blackbox test requires three scratch devices, loaded from the `/etc/stratis/test_config.json` file, which contains a JSON array of paths to the scratch devices.

Example `/etc/stratis/test_config.json` file:

```
{
    "ok_to_destroy_dev_array_key": [
                                   "/dev/vdb",
                                   "/dev/vdc",
                                   "/dev/vdd"
    ]
}
```

The RPMs are built with spec files that originate from the RHEL source RPMs, with one key modification: the version number and changelog dates are set in the future, for testing purposes.

This blackbox test is intended to execute on a Red Hat Enterprise Linux test system.
