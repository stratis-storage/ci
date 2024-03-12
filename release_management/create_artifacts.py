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
    calc_pre_release_suffix,
    edit_specfile,
    get_bundled_provides,
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

    parser.add_argument(
        "output_dir",
        action="store",
        help="directory for artifacts",
        type=os.path.abspath,
    )
    parser.add_argument(
        "--specfile-path",
        action="store",
        default=None,
        help="path to specfile to edit",
        type=lambda p: p if p is None else os.path.abspath(p),
    )
    parser.add_argument(
        "--pre-release",
        action="store_true",
        default=False,
        help="do automatic actions for a pre-release version",
    )

    subparsers = parser.add_subparsers(title="subcommands")

    stratisd_parser = subparsers.add_parser(
        "stratisd", help="Generate artifacts for a stratisd release."
    )

    stratisd_parser.set_defaults(func=_stratisd_artifacts)
    stratisd_parser.add_argument(
        "--vendor-method",
        action="store",
        help="Method of Rust vendoring",
        choices=["standard", "filtered"],
        default="standard",
    )

    stratis_cli_parser = subparsers.add_parser(
        "stratis-cli", help="Generate artifacts for a stratis-cli release."
    )

    stratis_cli_parser.set_defaults(func=_stratis_cli_artifacts)

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

    output_path = namespace.output_dir
    os.makedirs(output_path, exist_ok=True)

    (source_version, _) = get_package_info(manifest_abs_path, "stratisd")

    pre_release_suffix = calc_pre_release_suffix() if namespace.pre_release else None

    specfile_path = namespace.specfile_path
    if specfile_path is None and pre_release_suffix is not None:
        raise RuntimeError("must specify specfile using --specfile-path option")

    release_version = ReleaseVersion(source_version, suffix=pre_release_suffix)

    filtered = namespace.vendor_method == "filtered"

    source_tarfile_path = make_source_tarball(
        "stratisd", f"stratisd-v{release_version}", output_path
    )
    print(os.path.relpath(source_tarfile_path))

    vendor_tarfile_name = vendor(
        manifest_abs_path,
        release_version,
        filterer=filtered,
    )

    vendor_tarfile_path = os.path.join(output_path, vendor_tarfile_name)

    os.rename(vendor_tarfile_name, vendor_tarfile_path)

    def insert_bundled_provides(spec):
        """
        Insert bundled provides in the spec file.
        """
        with spec.sections() as sections:
            preamble = sections.package
            preamble.append("%if 0%{?rhel}")
            preamble.extend(get_bundled_provides(vendor_tarfile_path))
            preamble.append("%endif")
            preamble.append("")

    edit_specfile(
        specfile_path,
        release_version=release_version,
        sources=[
            os.path.basename(path)
            for path in [source_tarfile_path, vendor_tarfile_path]
        ],
        arbitrary=insert_bundled_provides,
    )


def _stratis_cli_artifacts(namespace):
    """
    Generate artifacts for stratis_cli.
    """
    output_path = namespace.output_dir
    os.makedirs(output_path, exist_ok=True)

    (source_version, _) = get_python_package_info("stratis-cli")

    pre_release_suffix = calc_pre_release_suffix() if namespace.pre_release else None
    specfile_path = namespace.specfile_path

    if specfile_path is None and pre_release_suffix is not None:
        raise RuntimeError("must specify specfile using --specfile-path option")

    release_version = ReleaseVersion(source_version, suffix=pre_release_suffix)

    source_tarfile = make_source_tarball(
        "stratis-cli",
        release_version,
        output_path,
    )

    def remove_stratisd_requires(spec):
        """
        Remove stratisd-related Requires line, if present.
        """
        with spec.tags() as tags:
            index = next(
                (
                    index
                    for index, tag in enumerate(tags)
                    if tag.name == "Requires" and "stratisd" in tag.value
                ),
                None,
            )

            if index is not None:
                del tags[index]

    edit_specfile(
        specfile_path,
        release_version=release_version,
        sources=[os.path.basename(source_tarfile)],
        arbitrary=remove_stratisd_requires,
    )

    print(os.path.relpath(source_tarfile))


if __name__ == "__main__":
    try:
        main()
    except Exception as err:  # pylint: disable=broad-except
        print(err)
        sys.exit(1)
