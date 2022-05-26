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
Creates a devicemapper-rs release
"""

# isort: STDLIB
import argparse
import os
import shutil
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

PACKAGE_NAME = "devicemapper"

LINE1_MATCH = "        hdr.version[0] = dmi::DM_VERSION_MAJOR;"
LINE2_MATCH = "        hdr.version[1] = dmi::DM_VERSION_MINOR;"
LINE3_MATCH = "        hdr.version[2] = dmi::DM_VERSION_PATCHLEVEL;"
LINE1_REPLACE = "        hdr.version[0] = 4;"
LINE2_REPLACE = "        hdr.version[1] = 41;"
LINE3_REPLACE = "        hdr.version[2] = 0;"

PATCH_FILE = "src/core/dm.rs"


def make_patch_branch(release_version, manifest_abs_path, repository_url):
    """
    Make a special patch branch to be used during stratisd development.

    This branch is identical to the released version except that its version
    number is patched in the generated ioctl.

    This patching will become unnecessary if stratisd testing stops using
    containers.

    :param str release_version:
    :param str manifest_abs_path: Cargo.toml absolute path
    :param str repository_url: the URL of the GitHub repository
    """
    patch_branch = f"crates-io-patch-{release_version}"
    subprocess.run(  # pylint: disable=subprocess-run-check
        ["git", "branch", "-D", patch_branch]
    )
    subprocess.run(["git", "checkout", "-b", patch_branch], check=True)

    subprocess.run(
        ["cargo", "package", f"--manifest-path={manifest_abs_path}"], check=True
    )

    package_manifest = os.path.join(
        os.path.dirname(manifest_abs_path),
        "target/package",
        f"{PACKAGE_NAME}-{release_version}",
        "Cargo.toml",
    )

    shutil.copyfile(package_manifest, manifest_abs_path)

    subprocess.run(["git", "add", "Cargo.toml"], check=True)
    subprocess.run(
        ["git", "commit", "-s", "-m", "Use Cargo.toml from cargo-package result"],
        check=True,
    )

    subprocess.run(["git", "clean", "-xdf"], check=True)

    with open(PATCH_FILE, "r", encoding="utf-8") as dm_file:
        lines = dm_file.readlines()

    with open(PATCH_FILE, "w", encoding="utf-8") as dm_file:
        for line in lines:
            line = line.rstrip(os.linesep)
            if line == LINE1_MATCH:
                print(LINE1_REPLACE, file=dm_file)
            elif line == LINE2_MATCH:
                print(LINE2_REPLACE, file=dm_file)
            elif line == LINE3_MATCH:
                print(LINE3_REPLACE, file=dm_file)
            else:
                print(line, file=dm_file)

    subprocess.run(["git", "add", PATCH_FILE], check=True)

    subprocess.run(
        ["git", "commit", "-s", "-m", "Patch version # in ioctl header"],
        check=True,
    )

    subprocess.run(
        [
            "git",
            "push",
            "-f",
            "-u",
            repository_url,
            f"{patch_branch}:{patch_branch}",
        ],
        check=True,
    )

    subprocess.run(["git", "checkout", "-"], check=True)


def main():
    """
    Main function
    """

    parser = argparse.ArgumentParser(
        description=(
            "Prepare a devicemappe-rs release for GitHub and upload it. "
            "Essentially cargo-publish but for a GitHub release not a cargo "
            "registry. If a tag does not exist for the release specified in "
            "Cargo.toml, tag the current commit. Push the specified tag and "
            "create a draft release on GitHub."
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
        "--no-patch-branch",
        action="store_true",
        default=False,
        dest="no_patch_branch",
        help="only create artifacts and tag",
    )

    parser.add_argument(
        "--no-release",
        action="store_true",
        default=False,
        dest="no_release",
        help="stop before pushing release changes to GitHub repo",
    )

    args = parser.parse_args()

    manifest_abs_path = os.path.abspath(MANIFEST_PATH)
    if not os.path.exists(manifest_abs_path):
        raise RuntimeError(
            "Need script to run at top-level of package, in same directory as Cargo.toml"
        )

    (release_version, repository) = get_package_info(manifest_abs_path, PACKAGE_NAME)

    if args.no_tag:
        return

    tag = f"v{release_version}"

    if not verify_tag(tag):
        message = f"version {release_version}"
        subprocess.run(
            ["git", "tag", "--annotate", tag, f'--message="{message}"'],
            check=True,
        )

    if args.no_patch_branch:
        return

    make_patch_branch(release_version, manifest_abs_path, repository.geturl())

    if args.no_release:
        return

    repository_url = repository.geturl()

    subprocess.run(
        ["git", "push", repository_url, tag],
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
