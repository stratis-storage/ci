#!/usr/bin/python3
#
# Copyright 2023 Red Hat, Inc.
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
Generate vendored provides list from vendor tarfile.
"""

# isort: STDLIB
import argparse
import os
import sys
import tarfile
import tomllib


def main():
    """
    Main function
    """

    parser = argparse.ArgumentParser(
        description=(
            "Generate a list of bundled provides suitable for including in an "
            "rpm spec file. Include in the list only those dependencies which "
            "have source code in the vendor tarfile. Prints list to stdout."
        )
    )

    parser.add_argument(
        "vendor_tarfile",
        action="store",
        help="path to vendor tarfile",
        type=os.path.abspath,
    )

    namespace = parser.parse_args()

    with tarfile.open(namespace.vendor_tarfile, "r") as tar:
        for member in tar.getmembers():
            components = member.name.split("/")

            if (
                len(components) == 3
                and components[0] == "vendor"
                and components[2] == "Cargo.toml"
            ):
                manifest = tar.extractfile(member)
                metadata = tomllib.load(manifest)
                directory_name = components[1]
                package = metadata["package"]
                package_version = package["version"]
                package_name = package["name"]
                if directory_name != package_name and (
                    not directory_name.startswith(package_name)
                    and directory_name[-len(package_version) :] != package_version
                ):
                    raise RuntimeError(
                        "Unexpected disagreement between directory name "
                        f"{directory_name} and package name in Cargo.toml, "
                        f"{package_name}"
                    )
                continue

            if (
                len(components) == 4
                and components[0] == "vendor"
                and components[2] == "src"
                and components[3] == "lib.rs"
            ):
                size = member.size
                if size != 0:
                    if components[1] == directory_name:
                        print(
                            f"Provides: bundled(crate({package_name})) = {package_version}"
                        )
                    else:
                        raise RuntimeError(
                            "Found an entry for bundled provides, but no version information"
                        )

    return 0


if __name__ == "__main__":
    try:
        main()
    except Exception as err:  # pylint: disable=broad-except
        print(err)
        sys.exit(1)
