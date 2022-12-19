#!/usr/bin/python3
#
# Copyright 2022 Red Hat, Inc.
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
Create artifacts for packaging tests.
"""

# isort: STDLIB
import argparse
import os
import sys

# isort: LOCAL
from _utils import (
    MANIFEST_PATH,
    ReleaseVersion,
    get_package_info,
    get_python_package_info,
    make_source_tarball,
    vendor,
)


def main():
    """
    Main function
    """

    parser = argparse.ArgumentParser(
        description=(
            "Generate artifacts for packaging tests. Expects to be run in "
            "clean top-level directory. Makes output dir if it does "
            "not already exist, but does not clean it."
        )
    )

    parser.add_argument("output_dir", action="store", help="directory for artifacts")
    parser.add_argument(
        "--pre-release-suffix",
        action="store",
        help="pre-release suffix to add to the version",
    )

    subparsers = parser.add_subparsers(title="subcommands")

    stratisd_parser = subparsers.add_parser(
        "stratisd", help="Generate artifacts for a stratisd release."
    )

    stratisd_parser.set_defaults(func=_stratisd_artifacts)
    stratisd_parser.add_argument("version", action="store", help="version")
    stratisd_parser.add_argument(
        "--omit-packaging",
        action="store_true",
        default=False,
        dest="omit_packaging",
        help="Do not package crate; use source Cargo.toml for vendoring.",
    )

    stratis_cli_parser = subparsers.add_parser(
        "stratis-cli", help="Generate artifacts for a stratis-cli release."
    )

    stratis_cli_parser.set_defaults(func=_stratis_cli_artifacts)
    stratis_cli_parser.add_argument("version", action="store", help="version")

    parser.set_defaults(func=lambda _: parser.error("missing sub-command"))

    namespace = parser.parse_args()

    namespace.func(namespace)

    return 0


def _stratisd_artifacts(namespace):
    """
    Generate stratisd artifacts.
    """
    manifest_abs_path = os.path.abspath(MANIFEST_PATH)
    if not os.path.exists(manifest_abs_path):
        raise RuntimeError(
            "Need script to run at top-level of package, in same directory as Cargo.toml"
        )

    output_abs_path = os.path.abspath(namespace.output_dir)
    os.makedirs(output_abs_path, exist_ok=True)

    (release_version, _) = get_package_info(manifest_abs_path, "stratisd")

    if release_version != namespace.version:
        raise RuntimeError("Version mismatch.")

    r_v = ReleaseVersion(release_version, namespace.pre_release_suffix)

    make_source_tarball("stratisd", r_v, output_abs_path)
    vendor_tarfile_name = vendor(
        manifest_abs_path, r_v, omit_packaging=namespace.omit_packaging
    )
    os.rename(vendor_tarfile_name, os.path.join(output_abs_path, vendor_tarfile_name))

    if not namespace.omit_packaging:
        crate_name = f"stratisd-{r_v.base_only()}.crate"
        crate_path = os.path.join("target", "package", crate_name)
        crate_suffix_name = f"stratisd-{r_v.to_crate_str()}.crate"
        os.rename(crate_path, os.path.join(output_abs_path, crate_suffix_name))


def _stratis_cli_artifacts(namespace):
    """
    Generate artifacts for stratis_cli.
    """
    output_abs_path = os.path.abspath(namespace.output_dir)
    os.makedirs(output_abs_path, exist_ok=True)

    (release_version, _) = get_python_package_info(
        "https://github.com/stratis-storage/stratis-cli"
    )

    if release_version != namespace.version:
        raise RuntimeError("Version mismatch.")

    r_v = ReleaseVersion(release_version, namespace.pre_release_suffix)

    make_source_tarball("stratis-cli", r_v, output_abs_path)


if __name__ == "__main__":
    try:
        main()
    except Exception as err:  # pylint: disable=broad-except
        print(err)
        sys.exit(1)
