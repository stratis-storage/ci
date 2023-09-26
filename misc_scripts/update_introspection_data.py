#!/usr/bin/env python3

# Copyright 2016 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Update Stratis introspection data.
"""

# isort: STDLIB
import argparse
import os
import sys
import xml.etree.ElementTree as ET
from enum import Enum

# isort: THIRDPARTY
import dbus
from semantic_version import Version

# isort: FIRSTPARTY
from dbus_python_client_gen import make_class


class ProxyType(Enum):
    """
    Type of D-Bus proxy object.
    """

    MANAGER = "manager"
    POOL = "pool"
    FILESYSTEM = "filesystem"
    BLOCKDEV = "blockdev"

    def __str__(self):
        return self.value


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
</interface>
""",
}

_SERVICE = "org.storage.stratis3"

_INTROSPECTABLE_IFACE = "org.freedesktop.DBus.Introspectable"
_MANAGER_IFACE = "org.storage.stratis3.Manager.r0"
_POOL_IFACE = "org.storage.stratis3.pool.r0"
_TIMEOUT = 120000

# pylint: disable=invalid-name
Introspectable = make_class(
    "Introspectable", ET.fromstring(SPECS[_INTROSPECTABLE_IFACE]), _TIMEOUT
)
Manager = make_class("Manager", ET.fromstring(SPECS[_MANAGER_IFACE]), _TIMEOUT)
Pool = make_class("Pool", ET.fromstring(SPECS[_POOL_IFACE]), _TIMEOUT)

OBJECT_MANAGER_INTERFACE = "org.freedesktop.DBus.ObjectManager"

TOP_OBJECT_INTERFACE_PREFIXES = [
    "org.storage.stratis3.Manager",
    "org.storage.stratis3.Report",
]
POOL_OBJECT_INTERFACE_PREFIXES = ["org.storage.stratis3.pool"]
BLOCKDEV_OBJECT_INTERFACE_PREFIXES = ["org.storage.stratis3.blockdev"]
FILESYSTEM_OBJECT_INTERFACE_PREFIXES = ["org.storage.stratis3.filesystem"]


def _xml_object_to_str(xml_object):
    """
    Convert XML object read from D-Bus to a string.

    :param xml_bytes: the bytes representing some XML
    """
    return ET.tostring(xml_object).decode("utf-8").rstrip(" \n")


def setup_minimal_object_set(bus):
    """
    Set up the minimal set of objects to be introspected on.

    :param bus: the bus
    :returns: a dict of proxy objects
    :rtype: dict of str * dbus proxy object
    """
    proxy = bus.get_object(_SERVICE, "/org/storage/stratis3", introspect=False)

    (
        (_, (pool_object_path, dev_object_paths)),
        return_code,
        return_msg,
    ) = Manager.Methods.CreatePool(
        proxy,
        {
            "name": "pool_name",
            "redundancy": (True, 0),
            "devices": ["/fake/fake"],
            "key_desc": (False, ""),
            "clevis_info": (False, ("", "")),
        },
    )

    if return_code != 0:
        sys.exit(return_msg)

    pool_proxy = bus.get_object(_SERVICE, pool_object_path, introspect=False)

    blockdev_proxy = bus.get_object(_SERVICE, dev_object_paths[0], introspect=False)

    ((_, (filesystems)), return_code, return_msg,) = Pool.Methods.CreateFilesystems(
        pool_proxy,
        {
            "specs": [("fs_name", (False, ""))],
        },
    )

    if return_code != 0:
        sys.exit(return_msg)

    filesystem_object_path = filesystems[0][0]
    filesystem_proxy = bus.get_object(
        _SERVICE, filesystem_object_path, introspect=False
    )

    return {
        ProxyType.MANAGER: proxy,
        ProxyType.POOL: pool_proxy,
        ProxyType.FILESYSTEM: filesystem_proxy,
        ProxyType.BLOCKDEV: blockdev_proxy,
    }


def _make_python_spec(proxies):
    """
    Make the introspection spec for python consumption.
    """

    revision = (
        f"r{Version(Manager.Properties.Version.Get(proxies[ProxyType.MANAGER])).minor}"
    )

    def get_current_interfaces(interface_prefixes):
        return [f"{prefix}.{revision}" for prefix in interface_prefixes]

    specs = {}

    def _add_data(proxy_key, interfaces):
        """
        Introspect on the proxy, get the information for the specified
        interfaces, and add it to specs.

        :param proxy: dbus Proxy object
        :param list interfaces: list of interesting interface names
        :raises: RuntimeError if some interface not found
        """
        string_data = Introspectable.Methods.Introspect(proxies[proxy_key], {})
        xml_data = ET.fromstring(string_data)

        for interface_name in interfaces:
            try:
                interface = next(
                    interface
                    for interface in xml_data
                    if interface.attrib["name"] == interface_name
                )
                specs[interface_name] = _xml_object_to_str(interface)
            except StopIteration as err:
                raise RuntimeError(
                    f"interface {interface_name} not found in introspection data"
                ) from err

    _add_data(ProxyType.MANAGER, [OBJECT_MANAGER_INTERFACE])

    _add_data(
        ProxyType.MANAGER,
        get_current_interfaces(TOP_OBJECT_INTERFACE_PREFIXES),
    )
    _add_data(
        ProxyType.POOL,
        get_current_interfaces(POOL_OBJECT_INTERFACE_PREFIXES),
    )

    _add_data(
        ProxyType.BLOCKDEV,
        get_current_interfaces(BLOCKDEV_OBJECT_INTERFACE_PREFIXES),
    )
    _add_data(
        ProxyType.FILESYSTEM,
        get_current_interfaces(FILESYSTEM_OBJECT_INTERFACE_PREFIXES),
    )

    return specs


def _print_python_spec(specs):
    """
    Print spec formatted according to stratis-cli and black's requirements.

    :param specs: the specification to print
    :type specs: dict of str * str
    """
    print("SPECS = {")

    print(
        ",\n".join(
            f'    "{key}": """\n{value}\n"""' for (key, value) in sorted(specs.items())
        )
        + ","
    )
    print("}")


def _python_output(_namespace):
    """
    Generate python output
    """
    bus = dbus.SystemBus()
    proxies = setup_minimal_object_set(bus)
    specs = _make_python_spec(proxies)
    _print_python_spec(specs)


def _make_docs_spec(proxies):
    """
    Make the introspection spec for use in docs repo.
    """

    specs = {}

    def _add_data(proxy_key):
        """
        Get the introspection data, and add it to the spec.

        :param proxy_key: key for proxies
        """
        string_data = Introspectable.Methods.Introspect(proxies[proxy_key], {})
        specs[proxy_key] = _xml_object_to_str(ET.fromstring(string_data))

    _add_data(ProxyType.MANAGER)
    _add_data(ProxyType.POOL)
    _add_data(ProxyType.BLOCKDEV)
    _add_data(ProxyType.FILESYSTEM)

    return specs


def _print_docs_spec(specs, namespace):
    """
    Print spec for inclusion on docs website.

    :param specs: the specification to print
    :type specs: dict of ProxyType * XML object
    :param namespace: the namespace parsed from the command-line arguments
    """

    def _proxy_type_to_filename(proxy_type):
        """
        Return filename for proxy type.
        """
        if proxy_type == ProxyType.MANAGER:
            return namespace.manager_file_name
        if proxy_type == ProxyType.POOL:
            return namespace.pool_file_name
        if proxy_type == ProxyType.FILESYSTEM:
            return namespace.filesystem_file_name
        if proxy_type == ProxyType.BLOCKDEV:
            return namespace.blockdev_file_name

        assert False, "unreachable"

    abs_output_dir = os.path.abspath(namespace.output_dir)
    try:
        os.mkdir(abs_output_dir)
    except FileExistsError as err:
        raise RuntimeError("Cannot create output dir for files") from err

    for proxy_type, introspection_data in specs.items():
        file_path = os.path.join(abs_output_dir, _proxy_type_to_filename(proxy_type))
        with open(file_path, "w", encoding="utf-8") as file:
            print(introspection_data, file=file)


def _docs_output(namespace):
    """
    Generate python output
    """
    bus = dbus.SystemBus()
    proxies = setup_minimal_object_set(bus)
    specs = _make_docs_spec(proxies)
    _print_docs_spec(specs, namespace)


def _gen_parser():
    """
    Generate the parser.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Generate D-Bus introspection data for interfaces defined by "
            "Stratis and print the data in the specified format. Must be "
            "run with root permissions, as it calls stratisd D-Bus methods "
            "that require root permissions."
        )
    )

    subparsers = parser.add_subparsers(title="subcommands")

    python_parser = subparsers.add_parser(
        "python", help="Generate introspection data for consumption by Python scripts"
    )
    python_parser.set_defaults(func=_python_output)

    docs_parser = subparsers.add_parser(
        "docs", help="Generate introspection data for consumption by website docs"
    )
    docs_parser.add_argument("output_dir", help="directory for output files")
    docs_parser.add_argument(
        "--manager-file-name",
        dest="manager_file_name",
        default="manager.xml",
        help="filename for manager object introspection data",
    )
    docs_parser.add_argument(
        "--pool-file-name",
        dest="pool_file_name",
        default="pool.xml",
        help="filename for pool object introspection data",
    )
    docs_parser.add_argument(
        "--filesystem-file-name",
        dest="filesystem_file_name",
        default="filesystem.xml",
        help="filename for filesystem object introspection data",
    )
    docs_parser.add_argument(
        "--blockdev-file-name",
        dest="blockdev_file_name",
        default="blockdev.xml",
        help="filename for blockdev object introspection data",
    )
    docs_parser.set_defaults(func=_docs_output)

    parser.set_defaults(func=lambda _: parser.error("missing sub-command"))

    return parser


def main():
    """
    The main method.
    """

    parser = _gen_parser()

    namespace = parser.parse_args()

    namespace.func(namespace)

    return 0


if __name__ == "__main__":
    main()
