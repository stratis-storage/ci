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
from urllib.parse import urlparse

# isort: THIRDPARTY
import requests
from github import Github


def _get_stratisd_info(manifest_abs_path):
    """
    Extract the version string and repo URL from Cargo.toml and return it.

    :param str manifest_path: absolute path to a Cargo.toml file
    :returns: stratisd version string and repository URL
    :rtype: str * ParseResult
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
    github_repo = urlparse(package["repository"].rstrip("/"))
    assert github_repo.netloc == "github.com", "specified repo is not on GitHub"
    return (package["version"], github_repo)


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


def main():  # pylint: disable=too-many-locals
    """
    Main function
    """

    parser = argparse.ArgumentParser(
        description=(
            "Prepare a stratisd release for GitHub and upload it. Essentially "
            "cargo-publish but for a GitHub release not a cargo registry. The "
            "manifest path is mandatory, as the manifest path determines the "
            "location of the 'package' directory. If a tag does not exist for "
            "the release specified in Cargo.toml, tag the current commit. "
            "Push the specified tag and create a draft release on GitHub."
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

    manifest_abs_path = os.path.abspath(args.manifest_path)
    vendor_dir = args.vendor_dir

    (release_version, repository) = _get_stratisd_info(manifest_abs_path)

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
        ["cargo", "vendor", "--manifest-path=%s" % package_manifest, vendor_dir],
        check=True,
    )

    vendor_tarfile_name = "stratisd-%s-vendor.tar.gz" % release_version

    subprocess.run(
        ["tar", "-czvf", vendor_tarfile_name, vendor_dir],
        check=True,
    )

    changelog_url = "%s/blob/%s/CHANGES.txt" % (repository.geturl(), _get_branch())

    requests_var = requests.get(changelog_url)
    if requests_var.status_code != 200:
        raise RuntimeError("Page at URL %s not found" % changelog_url)

    if args.no_tag:
        return

    tag = "v%s" % release_version

    if not _verify_tag(tag):
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

    api_key = os.environ.get("GITHUB_API_KEY")
    if api_key is None:
        api_key = getpass("API key: ")

    git = Github(api_key)

    repo = git.get_repo(repository.path.strip("/"))

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
