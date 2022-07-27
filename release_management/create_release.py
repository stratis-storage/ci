#!/usr/bin/python3
#
# Copyright 2020 Red Hat, Inc.
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
Make a GitHub Draft release.
"""

# isort: STDLIB
import argparse
import os
import subprocess
import sys

# isort: LOCAL
from _utils import (
    MANIFEST_PATH,
    create_release,
    get_branch,
    get_changelog_url,
    get_package_info,
    get_python_package_info,
    set_tag,
    vendor,
)


def main():
    """
    Main function
    """

    parser = argparse.ArgumentParser(description=("Create a GitHub Draft release."))

    parser.add_argument(
        "--no-tag",
        action="store_true",
        default=False,
        dest="no_tag",
        help="only create artifacts",
    )

    parser.add_argument(
        "--no-release",
        action="store_true",
        default=False,
        dest="no_release",
        help="stop before pushing any changes to GitHub repo",
    )

    subparsers = parser.add_subparsers(title="subcommands")

    stratisd_parser = subparsers.add_parser(
        "stratisd", help="Create a stratisd release."
    )

    stratisd_parser.set_defaults(func=_stratisd_release)

    devicemapper_parser = subparsers.add_parser(
        "dm", help="Create a devicemapper-rs release."
    )

    devicemapper_parser.set_defaults(func=_devicemapper_release)

    libcryptsetup_parser = subparsers.add_parser(
        "libcryptsetup", help="Create a libcryptsetup-rs release."
    )

    libcryptsetup_parser.set_defaults(func=_libcryptsetup_release)

    stratis_cli_parser = subparsers.add_parser(
        "stratis-cli", help="Create a stratis-cli release"
    )

    stratis_cli_parser.set_defaults(func=_stratis_cli_release)

    namespace = parser.parse_args()

    namespace.func(namespace)

    return 0


def _stratisd_release(namespace):
    """
    Create a stratisd release.
    """
    manifest_abs_path = os.path.abspath(MANIFEST_PATH)
    if not os.path.exists(manifest_abs_path):
        raise RuntimeError(
            "Need script to run at top-level of package, in same directory as Cargo.toml"
        )

    (release_version, repository) = get_package_info(manifest_abs_path, "stratisd")

    vendor_tarfile_name = vendor(manifest_abs_path, release_version)

    if namespace.no_tag:
        return

    tag = f"v{release_version}"

    set_tag(tag, f"version {release_version}")

    if namespace.no_release:
        return

    subprocess.run(
        ["git", "push", repository.geturl(), "tag", tag],
        check=True,
    )

    changelog_url = get_changelog_url(repository.geturl(), get_branch())

    release = create_release(repository, tag, release_version, changelog_url)

    release.upload_asset(vendor_tarfile_name, label=vendor_tarfile_name)


def _devicemapper_release(namespace):
    """
    Create a devicemapper release.
    """
    manifest_abs_path = os.path.abspath(MANIFEST_PATH)
    if not os.path.exists(manifest_abs_path):
        raise RuntimeError(
            "Need script to run at top-level of package, in same directory as Cargo.toml"
        )

    (release_version, repository) = get_package_info(manifest_abs_path, "devicemapper")

    if namespace.no_tag:
        return

    tag = f"v{release_version}"

    set_tag(tag, f"version {release_version}")

    if namespace.no_release:
        return

    subprocess.run(
        ["git", "push", repository.geturl(), "tag", tag],
        check=True,
    )

    changelog_url = get_changelog_url(repository.geturl(), get_branch())

    create_release(repository, tag, release_version, changelog_url)


def _libcryptsetup_release(namespace):
    """
    Create a libcryptsetup release.
    """
    manifest_abs_path = os.path.abspath(MANIFEST_PATH)
    if not os.path.exists(manifest_abs_path):
        raise RuntimeError(
            "Need script to run at top-level of package, in same directory as Cargo.toml"
        )

    (release_version, repository) = get_package_info(
        manifest_abs_path, "libcryptsetup-rs"
    )

    if namespace.no_tag:
        return

    tag = f"libcryptsetup-rs-v{release_version}"

    set_tag(tag, f"libcryptsetup-rs version {release_version}")

    if namespace.no_release:
        return

    subprocess.run(
        ["git", "push", repository.geturl(), "tag", tag],
        check=True,
    )


def _stratis_cli_release(namespace):
    """
    Create a stratis-cli release.
    """

    (release_version, repository) = get_python_package_info(
        "https://github.com/stratis-storage/stratis-cli"
    )

    if namespace.no_tag:
        return

    tag = f"v{release_version}"

    set_tag(tag, f"version {release_version}")

    if namespace.no_release:
        return

    repository_url = repository.geturl()

    subprocess.run(
        ["git", "push", repository_url, "tag", tag],
        check=True,
    )

    changelog_url = get_changelog_url(repository_url, get_branch())

    create_release(repository, tag, release_version, changelog_url)


if __name__ == "__main__":
    try:
        main()
    except Exception as err:  # pylint: disable=broad-except
        print(err)
        sys.exit(1)
