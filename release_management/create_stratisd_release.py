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
import os
import subprocess
import sys
from getpass import getpass

# isort: THIRDPARTY
import requests
from github import Github

# isort: LOCAL
from _utils import get_branch, get_package_info, verify_tag


def _create_release(
    repository, tag, release_version, changelog_url, vendor_tarfile_name
):
    """
    Create draft release from a pre-established GitHub tag for this repository.

    :param ParseResult repository: Git repository
    :param str tag: release tag
    :param str release_version: release version
    :param str changelog_url: changelog URL for the release notes
    :param str vendor_tarfle_name: the name of the tarfile of vendored sources
    """
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


def main():
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

    (release_version, repository) = get_package_info(manifest_abs_path, "stratisd")

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

    changelog_url = "%s/blob/%s/CHANGES.txt" % (repository.geturl(), get_branch())

    requests_var = requests.get(changelog_url)
    if requests_var.status_code != 200:
        raise RuntimeError("Page at URL %s not found" % changelog_url)

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

    _create_release(
        repository, tag, release_version, changelog_url, vendor_tarfile_name
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as err:  # pylint: disable=broad-except
        print(err)
        sys.exit(1)
