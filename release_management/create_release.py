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

# isort: THIRDPARTY
from semantic_version import Version

# isort: LOCAL
from _utils import (
    MANIFEST_PATH,
    ReleaseVersion,
    create_release,
    get_branch,
    get_changelog_url,
    get_package_info,
    get_python_package_info,
    set_tag,
    vendor,
)


def _push_tag(repository_url, tag):
    """
    Push a tag.

    :param str repository_url: the repo to push to
    :param str tag: the tag to push
    """
    subprocess.run(
        ["git", "push", repository_url, "tag", tag],
        check=True,
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

    stratisd_parser.add_argument(
        "--no-publish",
        action="store_true",
        default=False,
        dest="no_publish",
        help="Do not publish to crates.io",
    )

    devicemapper_parser = subparsers.add_parser(
        "dm", help="Create a devicemapper-rs release."
    )

    devicemapper_parser.set_defaults(func=_devicemapper_release)

    libcryptsetup_parser = subparsers.add_parser(
        "libcryptsetup", help="Create a libcryptsetup-rs release."
    )

    libcryptsetup_parser.set_defaults(func=_libcryptsetup_release)

    libcryptsetup_rs_sys_parser = subparsers.add_parser(
        "libcryptsetup-rs-sys", help="Create a libcryptsetup-rs-sys release."
    )

    libcryptsetup_rs_sys_parser.set_defaults(func=_libcryptsetup_rs_sys_release)

    libblkid_parser = subparsers.add_parser(
        "libblkid", help="Create a libblkid-rs release."
    )

    libblkid_parser.set_defaults(func=_libblkid_release)

    libblkid_rs_sys_parser = subparsers.add_parser(
        "libblkid-rs-sys", help="Create a libblkid-rs-sys release."
    )

    libblkid_rs_sys_parser.set_defaults(func=_libblkid_rs_sys_release)

    stratisd_proc_macros_parser = subparsers.add_parser(
        "stratisd_proc_macros", help="Create a stratisd_proc_macros release."
    )

    stratisd_proc_macros_parser.set_defaults(func=_stratisd_proc_macros_release)

    stratis_cli_parser = subparsers.add_parser(
        "stratis-cli", help="Create a stratis-cli release"
    )

    stratis_cli_parser.set_defaults(func=_stratis_cli_release)

    pyudev_parser = subparsers.add_parser("pyudev", help="Create a pyudev release")

    pyudev_parser.set_defaults(func=_pyudev_release)

    testing_parser = subparsers.add_parser("testing", help="Create a testing tag")
    testing_parser.add_argument(
        "release", action="store", type=Version, help="release_version"
    )

    testing_parser.set_defaults(func=_testing_release)

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

    r_v = ReleaseVersion(release_version, None)
    vendor_tarfile_name = vendor(manifest_abs_path, r_v)

    if namespace.no_tag:
        return

    tag = f"v{release_version}"

    set_tag(tag, f"version {release_version}")

    if namespace.no_release:
        return

    _push_tag(repository.geturl(), tag)

    changelog_url = get_changelog_url(repository.geturl(), get_branch())

    release = create_release(repository, tag, release_version, changelog_url)

    release.upload_asset(vendor_tarfile_name, label=vendor_tarfile_name)

    if namespace.no_publish:
        return

    subprocess.run(["git", "clean", "-xdf"], check=True)
    subprocess.run(["cargo", "clean"], check=True)
    subprocess.run(["cargo", "publish"], check=True)


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

    _push_tag(repository.geturl(), tag)

    changelog_url = get_changelog_url(repository.geturl(), get_branch())

    create_release(repository, tag, release_version, changelog_url)


def _tag_rust_library(namespace, name):
    """
    Set new tag for rust library.

    :param namespace: parser namespace
    :param str name: the Rust name (as in Cargo.toml) and the GitHub repo name
    """
    manifest_abs_path = os.path.abspath(MANIFEST_PATH)
    if not os.path.exists(manifest_abs_path):
        raise RuntimeError(
            "Need script to run at top-level of package, in same directory as Cargo.toml"
        )

    (release_version, repository) = get_package_info(manifest_abs_path, name)

    if namespace.no_tag:
        return

    tag = f"{name}-v{release_version}"

    set_tag(tag, f"{name} version {release_version}")

    if namespace.no_release:
        return

    _push_tag(repository.geturl(), tag)


def _libcryptsetup_release(namespace):
    """
    Create a libcryptsetup release.
    """
    return _tag_rust_library(namespace, "libcryptsetup-rs")


def _libcryptsetup_rs_sys_release(namespace):
    """
    Create a libcryptsetup release.
    """
    return _tag_rust_library(namespace, "libcryptsetup-rs-sys")


def _libblkid_release(namespace):
    """
    Create a libblkid release.
    """
    return _tag_rust_library(namespace, "libblkid-rs")


def _libblkid_rs_sys_release(namespace):
    """
    Create a libblkid-rs-sys release.
    """
    return _tag_rust_library(namespace, "libblkid-rs-sys")


def _stratisd_proc_macros_release(namespace):
    """
    Create a stratisd_proc_macros release.
    """
    return _tag_rust_library(namespace, "stratisd_proc_macros")


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

    _push_tag(repository_url, tag)

    changelog_url = get_changelog_url(repository_url, get_branch())

    create_release(repository, tag, release_version, changelog_url)


def _pyudev_release(namespace):
    """
    Create a pyudev release.
    """

    (release_version, repository) = get_python_package_info(
        "https://github.com/pyudev/pyudev"
    )

    if namespace.no_tag:
        return

    tag = f"v{release_version}"

    set_tag(tag, f"version {release_version}")

    if namespace.no_release:
        return

    _push_tag(repository.geturl(), tag)


def _testing_release(namespace):
    """
    Tag a testing release.
    """

    release_version = namespace.release

    if namespace.no_tag:
        return

    tag = f"v{release_version}"

    set_tag(tag, f"version {release_version}")

    if namespace.no_release:
        return

    _push_tag("https://github.com/stratis-storage/testing", tag)


if __name__ == "__main__":
    try:
        main()
    except Exception as err:  # pylint: disable=broad-except
        print(err)
        sys.exit(1)
