# Stratis blackbox test run script

The stratis-blackbox-run.sh script runs a series of "blackbox" tests against the stratisd and stratis-cli packages installed on the system.

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

This blackbox test is intended to execute on a Red Hat Enterprise Linux test system.
