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

import argparse
import os
import sys
import xml.etree.ElementTree as ET
from enum import Enum
from typing import List, Mapping, MutableMapping, Sequence

import dbus
from dbus.proxies import ProxyObject
from semantic_version import Version

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


def _xml_object_to_str(xml_object: ET.Element) -> str:
    """
    Convert XML object read from D-Bus to a string.
    """
    xml_object[:] = sorted(xml_object, key=lambda child: (child.tag, child.get("name")))
    return ET.tostring(xml_object).decode("utf-8").rstrip(" \n")


def setup_minimal_object_set(bus: dbus.SystemBus) -> dict[ProxyType, ProxyObject]:
    """
    Set up the minimal set of objects to be introspected on.

    :param bus: the bus
    :returns: a dict of proxy objects
    :rtype: dict of str * dbus proxy object
    """
    proxy = bus.get_object(_SERVICE, "/org/storage/stratis3", introspect=False)

    ((_, (pool_object_path, dev_object_paths)), return_code, return_msg) = (
        Manager.Methods.CreatePool(
            proxy,
            {
                "name": "pool_name",
                "redundancy": (True, 0),
                "devices": ["/fake/fake"],
                "key_desc": (False, ""),
                "clevis_info": (False, ("", "")),
            },
        )
    )

    if return_code != 0:
        sys.exit(return_msg)

    pool_proxy = bus.get_object(_SERVICE, pool_object_path, introspect=False)

    blockdev_proxy = bus.get_object(_SERVICE, dev_object_paths[0], introspect=False)

    ((_, (filesystems)), return_code, return_msg) = Pool.Methods.CreateFilesystems(
        pool_proxy, {"specs": [("fs_name", (False, ""))]}
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


def _get_revision_ext(
    manager: ProxyObject, maybe_revision_number: int | None = None
) -> str:
    """
    Return revision extension.
    """
    return f"r{
        Version(Manager.Properties.Version.Get(manager)).minor
        if maybe_revision_number is None
        else maybe_revision_number
    }"


def _get_current_interfaces(
    revision_ext: str, interface_prefixes: Sequence[str]
) -> List[str]:
    """
    Return a list of interfaces names.
    """
    return [f"{prefix}.{revision_ext}" for prefix in interface_prefixes]


def _add_data(
    specs: MutableMapping[str, str],
    proxy_object: ProxyObject,
    interfaces: Sequence[str],
):
    """
    Introspect on the proxy, get the information for the specified
    interfaces, and add it to specs.

    :param proxy: dbus Proxy object
    :param list interfaces: list of interesting interface names
    :raises: RuntimeError if some interface not found
    """
    string_data = Introspectable.Methods.Introspect(proxy_object, {})
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


def _make_python_spec(
    proxies: Mapping[ProxyType, ProxyObject], *, revision_number: int | None = None
) -> dict[str, str]:
    """
    Make the introspection spec for python consumption.
    """
    revision_ext = _get_revision_ext(proxies[ProxyType.MANAGER], revision_number)

    specs = {}

    _add_data(specs, proxies[ProxyType.MANAGER], [OBJECT_MANAGER_INTERFACE])

    _add_data(
        specs,
        proxies[ProxyType.MANAGER],
        _get_current_interfaces(revision_ext, TOP_OBJECT_INTERFACE_PREFIXES),
    )
    _add_data(
        specs,
        proxies[ProxyType.POOL],
        _get_current_interfaces(revision_ext, POOL_OBJECT_INTERFACE_PREFIXES),
    )

    _add_data(
        specs,
        proxies[ProxyType.BLOCKDEV],
        _get_current_interfaces(revision_ext, BLOCKDEV_OBJECT_INTERFACE_PREFIXES),
    )
    _add_data(
        specs,
        proxies[ProxyType.FILESYSTEM],
        _get_current_interfaces(revision_ext, FILESYSTEM_OBJECT_INTERFACE_PREFIXES),
    )

    return specs


def _print_python_spec(specs: Mapping[str, str]):
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


def _python_output(namespace: argparse.Namespace):
    """
    Generate python output
    """
    bus = dbus.SystemBus()
    proxies = setup_minimal_object_set(bus)
    specs = _make_python_spec(proxies, revision_number=namespace.revision_number)
    _print_python_spec(specs)


def _make_docs_spec(
    proxies: Mapping[ProxyType, ProxyObject], revision_number: int | None
) -> dict[str, str]:
    """
    Make the introspection spec for use in docs repo.
    """
    revision_ext = _get_revision_ext(proxies[ProxyType.MANAGER], revision_number)
    specs = {}

    _add_data(
        specs,
        proxies[ProxyType.MANAGER],
        _get_current_interfaces(revision_ext, TOP_OBJECT_INTERFACE_PREFIXES),
    )
    _add_data(
        specs,
        proxies[ProxyType.POOL],
        _get_current_interfaces(revision_ext, POOL_OBJECT_INTERFACE_PREFIXES),
    )

    _add_data(
        specs,
        proxies[ProxyType.BLOCKDEV],
        _get_current_interfaces(revision_ext, BLOCKDEV_OBJECT_INTERFACE_PREFIXES),
    )
    _add_data(
        specs,
        proxies[ProxyType.FILESYSTEM],
        _get_current_interfaces(revision_ext, FILESYSTEM_OBJECT_INTERFACE_PREFIXES),
    )
    return specs


def _print_docs_spec(specs: Mapping[str, str], namespace: argparse.Namespace):
    """
    Print spec for inclusion on docs website.

    :param specs: the specification to print
    :type specs: dict of str * str
    :param namespace: the namespace parsed from the command-line arguments
    """

    abs_output_dir = os.path.abspath(namespace.output_dir)
    try:
        os.mkdir(abs_output_dir)
    except FileExistsError as err:
        raise RuntimeError("Cannot create output dir for files") from err

    for interface_name, introspection_data in specs.items():
        file_path = os.path.join(abs_output_dir, f"{interface_name}.xml")
        with open(file_path, "w", encoding="utf-8") as file:
            print(introspection_data, file=file)


def _docs_output(namespace: argparse.Namespace):
    """
    Generate python output
    """
    bus = dbus.SystemBus()
    proxies = setup_minimal_object_set(bus)
    specs = _make_docs_spec(proxies, revision_number=namespace.revision_number)
    _print_docs_spec(specs, namespace)


def _gen_parser() -> argparse.ArgumentParser:
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

    parser.add_argument(
        "--revision-number", help="D-Bus interface revision number", type=int
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
