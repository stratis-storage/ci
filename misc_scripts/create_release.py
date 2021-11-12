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
Uploads the vendored dependency tarball as a release asset.
"""

# isort: STDLIB
import argparse
import json
import os
import subprocess
import sys
from getpass import getpass

# isort: THIRDPARTY
import requests
from github import Github


def _get_stratisd_version(manifest_abs_path):
    """
    Extract the version string from Cargo.toml and return it.

    :param str manifest_path: absolute path to a Cargo.toml file
    :returns: stratisd version string
    :rtype: str
    """
    assert os.path.isabs(manifest_abs_path)

    command = [
        "cargo",
        "metadata",
        "--format-version=1",
        "--no-deps",
        "--manifest-path=%s" % manifest_abs_path,
    ]

    with subprocess.Popen(command, stdout=subprocess.PIPE) as proc:
        metadata_str = proc.stdout.readline()

    metadata = json.loads(metadata_str)
    packages = metadata["packages"]
    assert len(packages) == 1
    package = packages[0]
    assert package["name"] == "stratisd"
    return package["version"]


def _verify_tag(tag):
    """
    Verify that the designated tag exists.

    :param str tag: the tag to check
    :returns: true if the tag exists, otherwise false
    :rtype: bool
    """
    command = ["git", "tag", "--list", tag]
    with subprocess.Popen(command, stdout=subprocess.PIPE) as proc:
        tag_str = proc.stdout.readline()
    return tag_str.decode("utf-8").rstrip() == tag


def _get_branch():
    """
    Get the current git branch as a string.

    :rtype: str
    """
    command = ["git", "branch", "--show-current"]
    with subprocess.Popen(command, stdout=subprocess.PIPE) as proc:
        branch_str = proc.stdout.readline()
    return branch_str.decode("utf-8").rstrip()


def main():
    """
    Main function
    """

    parser = argparse.ArgumentParser(
        description=(
            "Prepare a stratisd release for GitHub and upload it. Essentially "
            "cargo-publish but for a GitHub release not a cargo registry. The "
            "manifest path is mandatory, as the manifest path determines the "
            "location of the 'package' directory."
        )
    )

    parser.add_argument(
        "manifest_path",
        action="store",
        help="path to Cargo.toml",
    )

    parser.add_argument(
        "vendor_dir", action="store", help="path to cargo-vendor output directory"
    )

    parser.add_argument(
        "--no-release",
        action="store_true",
        default=False,
        dest="no_release",
        help="only create artifacts, do not upload to GitHub",
    )

    args = parser.parse_args()

    manifest_abs_path = os.path.abspath(args.manifest_path)
    vendor_abs_path = os.path.abspath(args.vendor_dir)

    release_version = _get_stratisd_version(manifest_abs_path)

    subprocess.run(
        ["cargo", "package", "--manifest-path=%s" % manifest_abs_path], check=True
    )

    package_manifest = os.path.join(
        os.path.dirname(manifest_abs_path),
        "target/package",
        "stratisd-%s" % release_version,
        "Cargo.toml",
    )

    subprocess.run(
        ["cargo", "vendor", "--manifest-path=%s" % package_manifest, vendor_abs_path],
        check=True,
    )

    vendor_tarfile_name = "stratisd-%s-vendor.tar.gz" % release_version

    subprocess.run(
        ["tar", "-czvf", vendor_tarfile_name, vendor_abs_path],
        check=True,
    )

    if args.no_release:
        return

    changelog_url = (
        "https://github.com/stratis-storage/stratisd/blob/%s/CHANGES.txt"
        % _get_branch()
    )

    requests_var = requests.get(changelog_url)
    if requests_var.status_code != 200:
        raise RuntimeError("Page at URL %s not found" % changelog_url)

    tag = "v%s" % release_version
    if not _verify_tag(tag):
        raise RuntimeError(
            "Unable to make release for tag %s which is not present in your "
            "local copy of the stratisd repo" % tag
        )

    api_key = os.environ.get("GITHUB_API_KEY")
    if api_key is None:
        api_key = getpass("API key: ")

    git = Github(api_key)

    repo = git.get_repo("stratis-storage/stratisd")

    release = repo.create_git_release(
        tag,
        "Version %s" % release_version,
        "See %s" % changelog_url,
        draft=True,
    )

    release.upload_asset(vendor_tarfile_name, label=vendor_tarfile_name)


if __name__ == "__main__":
    try:
        main()
    except Exception as err:  # pylint: disable=broad-except
        print(err)
        sys.exit(1)
