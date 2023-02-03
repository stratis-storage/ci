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
Calculates values useful for making a release.
"""

# isort: STDLIB
import json
import os
import subprocess
import tarfile
from getpass import getpass
from urllib.parse import urlparse

# isort: THIRDPARTY
import requests
from github import Github

MANIFEST_PATH = "./Cargo.toml"


class ReleaseVersion:
    """
    Release version for the package.
    """

    def __init__(self, base, suffix):
        """
        Initializer.
        :param str base: Base version
        :param suffix: Version suffix
        :type suffix: str or Nonetype
        """
        self.base = base
        self.suffix = "" if suffix is None else suffix

    def __str__(self):
        return self.base + self.suffix

    def to_crate_str(self):
        """
        Return the release version in a crates.io-friendly string.
        """
        return (self.base + self.suffix).replace("~", "-")

    def base_only(self):
        """
        Return only the base.
        """
        return self.base


def get_python_package_info(github_url):
    """
    Get info about the python package.

    :param str github_url: the github URL
    :returns: str * ParseResult
    """
    command = ["python", "setup.py", "--version"]
    with subprocess.Popen(command, stdout=subprocess.PIPE) as proc:
        release_version = proc.stdout.readline().strip().decode("utf-8")

    github_repo = urlparse(github_url)
    assert github_repo.netloc == "github.com", "specified repo is not on GitHub"
    return (release_version, github_repo)


def get_package_info(manifest_abs_path, package_name):
    """
    Extract the version string and repo URL from Cargo.toml and return it.

    :param str manifest_path: absolute path to a Cargo.toml file
    :param str package_name: the expected name of the package
    :returns: stratisd version string and repository URL
    :rtype: str * ParseResult
    """
    assert os.path.isabs(manifest_abs_path)

    command = [
        "cargo",
        "metadata",
        "--format-version=1",
        "--no-deps",
        f"--manifest-path={manifest_abs_path}",
    ]

    with subprocess.Popen(command, stdout=subprocess.PIPE) as proc:
        metadata_str = proc.stdout.readline()

    metadata = json.loads(metadata_str)
    packages = metadata["packages"]
    assert len(packages) == 1, "Unexpected Cargo metadata format"
    package = packages[0]
    assert package["name"] == package_name, (
        f'crate name in Cargo.toml ({package["name"]}) != specified'
        "package name ({package_name})"
    )
    github_repo = urlparse(package["repository"].rstrip("/"))
    assert github_repo.netloc == "github.com", "specified repo is not on GitHub"
    return (package["version"], github_repo)


def verify_tag(tag):
    """
    Verify that the designated tag exists and point at current HEAD.

    :param str tag: the tag to check
    :returns: true if the tag exists, otherwise false
    :rtype: bool
    """
    command = ["git", "tag", "--points-at"]
    with subprocess.Popen(command, stdout=subprocess.PIPE) as proc:
        tag_str = proc.stdout.readline()
    return tag_str.decode("utf-8").rstrip() == tag


def set_tag(tag, message):
    """
    Set specified tag on HEAD if it does not already exist.

    :param str tag: the tag to set
    :param str message: attach message to the tag
    :raises CalledProcessError:
    """
    if not verify_tag(tag):
        subprocess.run(
            ["git", "tag", "--annotate", tag, f'--message="{message}"'],
            check=True,
        )


def get_branch():
    """
    Get the current git branch as a string.

    :rtype: str
    """
    command = ["git", "branch", "--show-current"]
    with subprocess.Popen(command, stdout=subprocess.PIPE) as proc:
        branch_str = proc.stdout.readline()
    return branch_str.decode("utf-8").rstrip()


def create_release(repository, tag, release_version, changelog_url):
    """
    Create draft release from a pre-established GitHub tag for this repository.

    :param ParseResult repository: Git repository
    :param str tag: release tag
    :param str release_version: release version
    :param str changelog_url: changelog URL for the release notes
    :return: GitHub release object
    """
    api_key = os.environ.get("GITHUB_API_KEY")
    if api_key is None:
        api_key = getpass("API key: ")

    git = Github(api_key)

    repo = git.get_repo(repository.path.strip("/"))

    release = repo.create_git_release(
        tag,
        f"Version {release_version}",
        f"See {changelog_url}",
        draft=True,
    )

    return release


def vendor(manifest_abs_path, release_version, *, omit_packaging=False):
    """
    Makes a vendor tarfile, suitable for uploading.

    :param str manifest_abs_path: manifest path (absolute)
    :param ReleaseVersion release_version: the release version
    :param bool omit_packaging. do not vendor packaged project
    :return name of vendored tarfile:
    :rtype: str
    """

    vendor_dir = "vendor"

    if omit_packaging:
        package_manifest = manifest_abs_path
    else:
        subprocess.run(
            ["cargo", "package", f"--manifest-path={manifest_abs_path}"], check=True
        )

        package_manifest = os.path.join(
            os.path.dirname(manifest_abs_path),
            "target/package",
            f"stratisd-{release_version.base_only()}",
            "Cargo.toml",
        )

    subprocess.run(
        ["cargo", "vendor", f"--manifest-path={package_manifest}", vendor_dir],
        check=True,
    )

    vendor_tarfile_name = f"stratisd-{release_version}-vendor.tar.gz"

    subprocess.run(
        [
            "tar",
            "--owner=0",
            "--group=0",
            "--numeric-owner",
            "--sort=name",
            "--pax-option=exthdr.name=%d/PaxHeaders/%f,delete=atime,delete=ctime",
            "-czvf",
            vendor_tarfile_name,
            vendor_dir,
        ],
        check=True,
    )

    return vendor_tarfile_name


def make_source_tarball(package_name, release_version, output_dir):
    """
    Make the source tarball and place it in the output dir.

    Imitate what GitHub does on a tag to the best of our ability.

    :param str package_name: the package name
    :param ReleaseVersion release_version: the release version
    :param str output_dir: the output directory
    """
    prefix = f"{package_name}-{release_version}"

    output_file = os.path.join(output_dir, f"{prefix}.tar.gz")

    with tarfile.open(output_file, "w:gz") as tar:
        for root, _, files in os.walk("."):
            for filename in files:
                name = os.path.normpath(os.path.join(root, filename))
                if name.startswith(".git"):
                    continue
                tar.add(
                    name,
                    arcname=os.path.normpath(os.path.join(prefix, name)),
                    recursive=False,
                )


def get_changelog_url(repository_url, branch):
    """
    Get the URL for the changelog in the release message.

    :param str repository_url: object representing the GitHub repo
    :param str branch: the git branch
    """
    changelog_url = f"{repository_url}/blob/{branch}/CHANGES.txt"
    requests_var = requests.get(changelog_url)
    if requests_var.status_code != 200:
        raise RuntimeError("Page at URL {changelog_url} not found")

    return changelog_url
