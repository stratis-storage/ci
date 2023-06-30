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
from unittest.mock import patch

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


def _with_dry_run(dry_run):
    """
    Run closure either w/ or w/out patch for name.

    :param bool dry_run: True if dry_run only
    """

    def func_patch(to_patch_str):
        """
        Make a generic patch for an imported method.

        :param str to_patch_str: the string that identifies the method
        """

        def side_effect(name):
            """
            Utility method for printing a message when mocking a method.

            :param str name: the method name to print
            """

            def print_message(*args, **kwargs):
                print(f"Mocking {name}: {args} {kwargs}")

            return print_message

        return patch(
            to_patch_str,
            return_value=None,
            side_effect=side_effect(to_patch_str),
        )

    def func(name, closure, *, skip=False):
        """
        :param str name: the name of the method to mock
        :param closure: the closure to run, invoked w/ no arguments
        :param bool skip: If True, just skip.
        """
        if skip:
            return

        if dry_run:
            with func_patch(name):
                closure()
        else:
            closure()

    return func


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


class RustCrates:
    """
    Methods for assisting in building and releasing Rust crates.
    """

    @staticmethod
    def set_up_subcommand(
        subcmd,
        subparsers,
        *,
        add_github_release_option=False,
        add_vendor_option=False,
        subcmd_aliases=None,
    ):
        """
        Set up subcommand parsers
        :param str subcmd: the name of the subcommand
        :param argparse subparsers: the subparsers variable
        :param bool add_github_release_option: whether to pass no-github-release option
        :param bool add_vendor_option: whether to allow no-vendor option
        """

        subcmd_aliases = [] if subcmd_aliases is None else subcmd_aliases

        new_subparser = subparsers.add_parser(
            subcmd, help=f"Create a release for {subcmd}.", aliases=subcmd_aliases
        )

        new_subparser.set_defaults(
            func=lambda namespace: RustCrates.tag_rust_library(namespace, subcmd)
        )

        new_subparser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            dest="dry_run",
            help="Only report actions, do not do them",
        )

        new_subparser.add_argument(
            "--no-publish",
            action="store_true",
            default=False,
            dest="no_publish",
            help="Do not publish to crates.io",
        )

        if add_github_release_option:
            new_subparser.add_argument(
                "--no-github-release",
                action="store_true",
                default=False,
                dest="no_github_release",
                help="Do not release to GitHub",
            )
        else:
            new_subparser.set_defaults(no_github_release=True)

        if add_vendor_option:
            new_subparser.add_argument(
                "--no-vendor",
                action="store_true",
                default=False,
                dest="no_vendor",
                help="Do not make a vendor tarfile",
            )
        else:
            new_subparser.set_defaults(no_vendor=True)

    @staticmethod
    def tag_rust_library(namespace, name):
        """
        Set new tag for rust library.

        :param namespace: parser namespace
        :param str name: the Rust name (as in Cargo.toml) and the GitHub repo name
        """
        dry_run_caller = _with_dry_run(namespace.dry_run)

        manifest_abs_path = os.path.abspath(MANIFEST_PATH)
        if not os.path.exists(manifest_abs_path):
            raise RuntimeError(
                "Need script to run at top-level of package, in same directory as Cargo.toml"
            )

        (release_version, repository) = get_package_info(manifest_abs_path, name)

        try:
            subprocess.run(
                [
                    "cargo",
                    "package",
                    "--manifest-path",
                    MANIFEST_PATH,
                ],
                check=True,
            )
        finally:
            subprocess.run(["cargo", "clean"], check=True)

        additional_assets = []
        if not namespace.no_vendor:
            r_v = ReleaseVersion(release_version, None)
            (vendor_tarfile_name, _) = vendor(manifest_abs_path, r_v)
            additional_assets = [vendor_tarfile_name]

            vendor_tarfile_abs_path = os.path.abspath(vendor_tarfile_name)
            subprocess.run(["sha512sum", vendor_tarfile_abs_path], check=True)

        if namespace.no_tag:
            return

        tag = f"{name}-v{release_version}"

        dry_run_caller(
            "__main__.set_tag",
            lambda: set_tag(tag, f"{name} version {release_version}"),
        )

        if namespace.no_release:
            return

        dry_run_caller(
            "__main__._push_tag", lambda: _push_tag(repository.geturl(), tag)
        )

        changelog_url = get_changelog_url(repository.geturl(), get_branch())

        dry_run_caller(
            "__main__.create_release",
            lambda: create_release(
                repository,
                tag,
                release_version,
                changelog_url,
                additional_assets=additional_assets,
            ),
            skip=namespace.no_github_release,
        )

        # pylint: disable=unnecessary-lambda
        # The lambda is necessary in order to prevent the interpreter from
        # resolving _publish before the mock method is put into place.
        dry_run_caller(
            "__main__._publish", lambda: _publish(), skip=namespace.no_publish
        )


class PythonPackages:  # pylint: disable=too-few-public-methods
    """
    Methods for assisting in building and releasing Python packages.
    """

    @staticmethod
    def set_up_subcommand(subcmd, subparsers, target_func):
        """
        Set up subcommand parsers
        :param str subcmd: the name of the subcommand
        :param argparse subparsers: the subparsers variable
        :param function target_func: the target function to call
        """
        new_subparser = subparsers.add_parser(
            subcmd, help=f"Create a release for {subcmd}"
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

    RustCrates.set_up_subcommand(
        "stratisd",
        subparsers,
        add_github_release_option=True,
        add_vendor_option=True,
    )

    RustCrates.set_up_subcommand(
        "devicemapper",
        subparsers,
        add_github_release_option=True,
        subcmd_aliases=["devicemapper-rs"],
    )

    RustCrates.set_up_subcommand(
        "devicemapper-sys", subparsers, subcmd_aliases=["devicemapper-rs-sys"]
    )

    RustCrates.set_up_subcommand(
        "libcryptsetup-rs",
        subparsers,
    )

    RustCrates.set_up_subcommand(
        "libcryptsetup-rs-sys",
        subparsers,
    )

    RustCrates.set_up_subcommand("libblkid-rs", subparsers)

    RustCrates.set_up_subcommand(
        "libblkid-rs-sys",
        subparsers,
    )

    RustCrates.set_up_subcommand("stratisd_proc_macros", subparsers)

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

    PythonPackages.set_up_subcommand(
        "dbus-signature-pyparsing", subparsers, _dbus_signature_pyparsing_release
    )

    PythonPackages.set_up_subcommand("justbases", subparsers, _justbases_release)

    PythonPackages.set_up_subcommand("justbytes", subparsers, _justbytes_release)

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


def _tag_python_library(namespace, name):
    """
    Tag a Python library.

    :param namespace: parser namespace
    :param str name: package_name
    """
    (release_version, repository) = get_python_package_info(name)

    if namespace.no_tag:
        return

    tag = f"v{release_version}"

    set_tag(tag, f"version {release_version}")

    if namespace.no_release:
        return

    _push_tag(repository.geturl(), tag)


def _stratis_cli_release(namespace):
    """
    Create a stratis-cli release.
    """

    (release_version, repository) = get_python_package_info("stratis-cli")

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
    _tag_python_library(namespace, "dbus-python-client-gen")


def _dbus_client_gen_release(namespace):
    """
    Create a dbus_client_gen release.
    """
    _tag_python_library(namespace, "dbus-client-gen")


def _into_dbus_python_release(namespace):
    """
    Create a into_dbus_python release.
    """
    _tag_python_library(namespace, "into-dbus-python")


def _dbus_signature_pyparsing_release(namespace):
    """
    Create a into_dbus_python release.
    """
    _tag_python_library(namespace, "dbus-signature-pyparsing")


def _justbases_release(namespace):
    """
    Create a justbases release.
    """
    _tag_python_library(namespace, "justbases")


def _justbytes_release(namespace):
    """
    Create a justbytes release.
    """
    _tag_python_library(namespace, "justbytes")


def _pyudev_release(namespace):
    """
    Create a pyudev release.
    """

    _tag_python_library(namespace, "pyudev")


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
    main()
