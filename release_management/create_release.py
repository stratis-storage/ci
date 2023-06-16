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


def _publish():
    """
    Run git commands to publish a crate to crates.io.
    """
    subprocess.run(["git", "clean", "-xdf"], check=True)
    subprocess.run(["cargo", "clean"], check=True)
    subprocess.run(["cargo", "publish"], check=True)


def _set_up_subcommand(subcmd, subparsers, target_func):
    """
    Set up subcommand parsers
    :param str subcmd: the name of the subcommand
    :param argparse subparsers: the subparsers variable
    :param function target_func: the target function to call
    """
    new_subparser = subparsers.add_parser(
        subcmd, help=f"Create a release for {subcmd}."
    )
    new_subparser.set_defaults(func=target_func)


def _get_parser():
    """
    Build parser
    """
    parser = argparse.ArgumentParser(description="Create a GitHub Draft release.")

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

    devicemapper_parser.add_argument(
        "--no-publish",
        action="store_true",
        default=False,
        dest="no_publish",
        help="Do not publish to crates.io",
    )

    _set_up_subcommand("devicemapper-rs-sys", subparsers, _devicemapper_sys_release)

    _set_up_subcommand(
        "libcryptsetup-rs",
        subparsers,
        _libcryptsetup_rs_release,
    )

    _set_up_subcommand(
        "libcryptsetup-rs-sys",
        subparsers,
        _libcryptsetup_rs_sys_release,
    )

    _set_up_subcommand("libblkid-rs", subparsers, _libblkid_rs_release)

    _set_up_subcommand(
        "libblkid-rs-sys",
        subparsers,
        _libblkid_rs_sys_release,
    )

    _set_up_subcommand(
        "stratisd_proc_macros", subparsers, _stratisd_proc_macros_release
    )

    stratis_cli_parser = subparsers.add_parser(
        "stratis-cli", help="Create a stratis-cli release"
    )

    stratis_cli_parser.set_defaults(func=_stratis_cli_release)

    pyudev_parser = subparsers.add_parser("pyudev", help="Create a pyudev release")

    pyudev_parser.set_defaults(func=_pyudev_release)

    dbus_python_client_gen_parser = subparsers.add_parser(
        "dbus-python-client-gen", help="Create a dbus-python-client-gen release"
    )

    dbus_python_client_gen_parser.set_defaults(func=_dbus_python_client_gen_release)

    dbus_client_gen_parser = subparsers.add_parser(
        "dbus-client-gen", help="Create a dbus-client-gen release"
    )

    dbus_client_gen_parser.set_defaults(func=_dbus_client_gen_release)

    into_dbus_python_parser = subparsers.add_parser(
        "into-dbus-python", help="Create a into-dbus-python release"
    )

    into_dbus_python_parser.set_defaults(func=_into_dbus_python_release)

    dbus_signature_pyparsing_parser = subparsers.add_parser(
        "dbus-signature-pyparsing", help="Create a dbus-signature-pyparsing release"
    )

    dbus_signature_pyparsing_parser.set_defaults(func=_dbus_signature_pyparsing_release)

    justbases_parser = subparsers.add_parser(
        "justbases", help="Create a into-dbus-python release"
    )

    justbases_parser.set_defaults(func=_justbases_release)

    justbytes_parser = subparsers.add_parser(
        "justbytes", help="Create a into-dbus-python release"
    )

    justbytes_parser.set_defaults(func=_justbytes_release)

    testing_parser = subparsers.add_parser("testing", help="Create a testing tag")
    testing_parser.add_argument(
        "release", action="store", type=Version, help="release_version"
    )

    testing_parser.set_defaults(func=_testing_release)

    return parser


def main():
    """
    Main function
    """

    parser = _get_parser()

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
    (vendor_tarfile_name, _) = vendor(manifest_abs_path, r_v)
    vendor_tarfile_abs_path = os.path.abspath(vendor_tarfile_name)
    subprocess.run(["sha512sum", vendor_tarfile_abs_path], check=True)

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

    _publish()


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

    if namespace.no_publish:
        return

    _publish()


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

    package_rc = subprocess.run(
        ["cargo", "package", "--all-features", "--manifest-path", MANIFEST_PATH],
        check=True,
    )
    subprocess.run(["cargo", "clean"], check=True)
    if not package_rc:
        return

    if namespace.no_tag:
        return

    tag = f"{name}-v{release_version}"

    set_tag(tag, f"{name} version {release_version}")

    if namespace.no_release:
        return

    _push_tag(repository.geturl(), tag)


def _tag_python_library(namespace, git_url):
    """
    Tag a Python library.

    :param namespace: parser namespace
    :param str git_url: git URL
    """
    (release_version, repository) = get_python_package_info(git_url)

    if namespace.no_tag:
        return

    tag = f"v{release_version}"

    set_tag(tag, f"version {release_version}")

    if namespace.no_release:
        return

    _push_tag(repository.geturl(), tag)


def _devicemapper_sys_release(namespace):
    """
    Create a devicemapper-rs-sys release.
    """
    return _tag_rust_library(namespace, "devicemapper-sys")


def _libcryptsetup_rs_release(namespace):
    """
    Create a libcryptsetup-rs release.
    """
    return _tag_rust_library(namespace, "libcryptsetup-rs")


def _libcryptsetup_rs_sys_release(namespace):
    """
    Create a libcryptsetup-rs-sys release.
    """
    return _tag_rust_library(namespace, "libcryptsetup-rs-sys")


def _libblkid_rs_release(namespace):
    """
    Create a libblkid-rs release.
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


def _dbus_python_client_gen_release(namespace):
    """
    Create a dbus_python_clietn_gen release.
    """
    _tag_python_library(
        namespace, "https://github.com/stratis-storage/dbus-python-client-gen"
    )


def _dbus_client_gen_release(namespace):
    """
    Create a dbus_client_gen release.
    """
    _tag_python_library(namespace, "https://github.com/stratis-storage/dbus-client-gen")


def _into_dbus_python_release(namespace):
    """
    Create a into_dbus_python release.
    """
    _tag_python_library(
        namespace, "https://github.com/stratis-storage/into-dbus-python"
    )


def _dbus_signature_pyparsing_release(namespace):
    """
    Create a into_dbus_python release.
    """
    _tag_python_library(
        namespace, "https://github.com/stratis-storage/dbus-signature-pyparsing"
    )


def _justbases_release(namespace):
    """
    Create a justbases release.
    """
    _tag_python_library(namespace, "https://github.com/mulkieran/justbases")


def _justbytes_release(namespace):
    """
    Create a justbytes release.
    """
    _tag_python_library(namespace, "https://github.com/mulkieran/justbytes")


def _pyudev_release(namespace):
    """
    Create a pyudev release.
    """

    _tag_python_library(namespace, "https://github.com/pyudev/pyudev")


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
