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
Manage the stratisd GitHub release.

Assumes that the stratisd version number in Cargo.toml is the correct one.

Will tag the release and push the tag if the correct tag does not exist.

Creates a GitHub Draft release and uploads the vendored tarball.
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
    verify_tag,
)


def _vendor(manifest_abs_path, release_version):
    """
    Makes a vendor tarfile, suitable for uploading.

    ;param str manifest_abs_path: manifest path (absolute)
    :param str release_version: the release version
    :return name of vendored tarfile:
    :rtype: str
    """

    vendor_dir = "vendor"

    subprocess.run(
        ["cargo", "package", "--allow-dirty", "--manifest-path=%s" % manifest_abs_path], check=True
    )

    package_manifest = os.path.join(
        os.path.dirname(manifest_abs_path),
        "target/package",
        "stratisd-%s" % release_version,
        "Cargo.toml",
    )

    subprocess.run(
        ["cargo", "vendor", "--manifest-path=%s" % package_manifest, vendor_dir],
        check=True,
    )

    vendor_tarfile_name = "stratisd-%s-vendor.tar.gz" % release_version

    subprocess.run(
        ["tar", "-czvf", vendor_tarfile_name, vendor_dir],
        check=True,
    )

    return vendor_tarfile_name


def main():
    """
    Main function
    """

    parser = argparse.ArgumentParser(
        description=(
            "Prepare a stratisd release for GitHub and upload it. Essentially "
            "cargo-publish but for a GitHub release not a cargo registry. If a "
            "tag does not exist for the release specified in Cargo.toml, tag "
            "the current commit. Push the specified tag and create a draft "
            "release on GitHub."
        )
    )

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

    args = parser.parse_args()

    manifest_abs_path = os.path.abspath(MANIFEST_PATH)
    if not os.path.exists(manifest_abs_path):
        raise RuntimeError(
            "Need script to run at top-level of package, in same directory as Cargo.toml"
        )

    (release_version, repository) = get_package_info(manifest_abs_path, "stratisd")

    vendor_tarfile_name = _vendor(manifest_abs_path, release_version)

    if args.no_tag:
        return

    tag = "v%s" % release_version

    if not verify_tag(tag):
        message = "version %s" % release_version
        subprocess.run(
            ["git", "tag", "--annotate", tag, '--message="%s"' % message],
            check=True,
        )

    if args.no_release:
        return

    subprocess.run(
        ["git", "push", repository.geturl(), tag],
        check=True,
    )

    changelog_url = get_changelog_url(repository.geturl(), get_branch())

    release = create_release(repository, tag, release_version, changelog_url)

    release.upload_asset(vendor_tarfile_name, label=vendor_tarfile_name)


if __name__ == "__main__":
    try:
        main()
    except Exception as err:  # pylint: disable=broad-except
        print(err)
        sys.exit(1)
