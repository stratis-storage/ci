#!/usr/bin/python3
"""
Estimate filesystem size consumption for logical filesystem sizes.
"""

# isort: STDLIB
import argparse
import sys
import xml.etree.ElementTree as ET

# isort: THIRDPARTY
import dbus

# isort: FIRSTPARTY
from dbus_python_client_gen import make_class

# a minimal chunk of introspection data, enough for the methods needed.
SPECS = {
    "org.freedesktop.DBus.Introspectable": """
<interface name="org.freedesktop.DBus.Introspectable">
<method name="Introspect">
<arg name="xml_data" type="s" direction="out"/>
</method>
</interface>
""",
    "org.storage.stratis3.Manager.r0": """
<interface name="org.storage.stratis3.Manager.r0">
<method name="CreatePool">
<arg name="name" type="s" direction="in"/>
<arg name="redundancy" type="(bq)" direction="in"/>
<arg name="devices" type="as" direction="in"/>
<arg name="key_desc" type="(bs)" direction="in"/>
<arg name="clevis_info" type="(b(ss))" direction="in" />
<arg name="result" type="(b(oao))" direction="out"/>
<arg name="return_code" type="q" direction="out"/>
<arg name="return_string" type="s" direction="out"/>
</method>
<method name="DestroyPool">
<arg name="pool" type="o" direction="in" />
<arg name="result" type="(bs)" direction="out" />
<arg name="return_code" type="q" direction="out" />
<arg name="return_string" type="s" direction="out" />
</method>
<property name="Version" type="s" access="read">
<annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="const" />
</property>
</interface>
""",
    "org.storage.stratis3.pool.r0": """
<interface name="org.storage.stratis3.pool.r0">
<method name="CreateFilesystems">
<arg name="specs" type="a(s(bs))" direction="in"/>
<arg name="results" type="(ba(os))" direction="out"/>
<arg name="return_code" type="q" direction="out"/>
<arg name="return_string" type="s" direction="out"/>
</method>
<method name="DestroyFilesystems">
<arg name="filesystems" type="ao" direction="in" />
<arg name="results" type="(bas)" direction="out" />
<arg name="return_code" type="q" direction="out" />
<arg name="return_string" type="s" direction="out" />
</method>
<property name="TotalPhysicalUsed" type="(bs)" access="read" />
</interface>
""",
    "org.storage.stratis3.filesystem.r0": """
<interface name="org.storage.stratis3.filesystem.r0">
    <property name="Created" type="s" access="read">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="const" />
    </property>
    <property name="Devnode" type="s" access="read">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="invalidates" />
    </property>
    <property name="Name" type="s" access="read" />
    <property name="Pool" type="o" access="read">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="const" />
    </property>
    <property name="Size" type="s" access="read" />
    <property name="Used" type="(bs)" access="read" />
    <property name="Uuid" type="s" access="read">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="const" />
    </property>
  </interface>
""",
}

_SERVICE = "org.storage.stratis3"
_TOP_OBJECT = "/org/storage/stratis3"

_MANAGER_IFACE = "org.storage.stratis3.Manager.r0"
_POOL_IFACE = "org.storage.stratis3.pool.r0"
_FILESYSTEM_IFACE = "org.storage.stratis3.filesystem.r0"

_TIMEOUT = 120000

# pylint: disable=invalid-name
Manager = make_class("Manager", ET.fromstring(SPECS[_MANAGER_IFACE]), _TIMEOUT)
Pool = make_class("Pool", ET.fromstring(SPECS[_POOL_IFACE]), _TIMEOUT)
Filesystem = make_class("Filesystem", ET.fromstring(SPECS[_FILESYSTEM_IFACE]), _TIMEOUT)


def gen_parser():
    """
    Generate parser.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Generate a table of two columns: 1) filesystem logical size, "
            "2) space consumed by the filesystem on a thin device. Values "
            "for the first column are read from stdin and must be in bytes. "
            "The values for the second column are in bytes. This script must "
            "be run with root permissions. stratisd must have already been "
            "started. Pool 'pool_name' must not have been created."
        )
    )
    parser.add_argument(
        "--device",
        action="extend",
        nargs="+",
        type=str,
        help="Devices with which to instantiate the pool.",
    )
    return parser


def _do_one(size, bus, pool_proxy):
    """
    Get data for specified size.

    :param str size: filesystem size to specify
    :param bus: system bus
    :param pool_proxy: proxy to invoke methods on pool
    :returns: a 4-tuple of values
    :rtype: (str, srt or NoneType, str or NoneType, str or NoneType)
    """
    (real, pool_used_pre) = Pool.Properties.TotalPhysicalUsed.Get(pool_proxy)
    if not real:
        pool_used_pre = None

    ((_, (filesystems)), return_code, return_msg,) = Pool.Methods.CreateFilesystems(
        pool_proxy,
        {
            "specs": [("fs_name", (True, size))],
        },
    )

    if return_code != 0:
        sys.exit(return_msg)

    (real, pool_used_post) = Pool.Properties.TotalPhysicalUsed.Get(pool_proxy)
    if not real:
        pool_used_post = None

    filesystem_object_path = filesystems[0][0]
    filesystem_proxy = bus.get_object(
        _SERVICE, filesystem_object_path, introspect=False
    )

    (real, used) = Filesystem.Properties.Used.Get(filesystem_proxy)
    if not real:
        used = None

    (_, return_code, return_msg) = Pool.Methods.DestroyFilesystems(
        pool_proxy, {"filesystems": [filesystem_object_path]}
    )

    if return_code != 0:
        sys.exit(return_msg)

    return (size, used if real else None, pool_used_pre, pool_used_post)


def _print_values(devices):
    """
    Print table of filesystem size values.

    :param devices: list of devices
    """
    bus = dbus.SystemBus()

    proxy = bus.get_object(_SERVICE, _TOP_OBJECT, introspect=False)

    ((_, (pool_object_path, _)), return_code, return_msg,) = Manager.Methods.CreatePool(
        proxy,
        {
            "name": "pool_name",
            "redundancy": (True, 0),
            "devices": devices,
            "key_desc": (False, ""),
            "clevis_info": (False, ("", "")),
        },
    )

    if return_code != 0:
        sys.exit(return_msg)

    pool_proxy = bus.get_object(_SERVICE, pool_object_path, introspect=False)

    for line in sys.stdin:
        size = line.rstrip()

        (size, fs_used, pool_used_pre, pool_used_post) = _do_one(size, bus, pool_proxy)
        print(
            "%s %s %s %s"
            % (
                size,
                "ERROR" if fs_used is None else fs_used,
                "ERROR" if pool_used_pre is None else pool_used_pre,
                "ERROR" if pool_used_post is None else pool_used_post,
            )
        )

    (_, return_code, return_msg) = Manager.Methods.DestroyPool(
        proxy, {"pool": pool_object_path}
    )

    if return_code != 0:
        sys.exit(return_msg)


def main():
    """
    Main method
    """

    parser = gen_parser()
    args = parser.parse_args()

    _print_values(args.device)


if __name__ == "__main__":
    main()
