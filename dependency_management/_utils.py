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
Calculates information comparing the versions of dependencies in a Rust project
to the versions of dependencies available on Fedora Rawhide.
"""


# isort: STDLIB
import json
import re
import subprocess

# isort: THIRDPARTY
import requests
from semantic_version import SimpleSpec, Version

CARGO_TREE_RE = re.compile(
    r"^[|`]-- (?P<crate>[a-z0-9_\-]+) v(?P<version>[0-9\.]+)( \(.*\))?$"
)
KOJI_RE = re.compile(
    r"^toplink/packages/rust-(?P<name>[^\/]*?)/(?P<version>[^\/]*?)/[^]*)]*"
)


def build_koji_repo_dict(crates, release):
    """
    :param crates: a set of crates
    :type cargo_tree: set of str
    :param str release: release of fedora for which to build the dict
    :returns: a dictionary containing information from the koji repo webpage
    the keys are the string representations of dependencies
    the values are the versions of dependencies
    :rtype: dict of str * Version
    :raises: RuntimeError
    """
    if release != "rawhide":
        try:
            if release[0] != "f":
                raise RuntimeError(
                    f'release argument must be "rawhide" or f<n> '
                    f'where n is an integer, was "{release}"'
                )

            release_number = int(release[1:])

            if release_number < 34:
                raise RuntimeError(
                    f"release number must be at least 34, was {release_number}"
                )
        except (IndexError, ValueError) as err:
            raise RuntimeError(
                f'release must be "rawhide" or f<n> where n is an integer, was "{release}"'
            ) from err

    url = (
        "https://kojipkgs.fedoraproject.org/repos/"
        f"{release if release == 'rawhide' else f'{release}-build'}/latest/x86_64/pkglist"
    )

    requests_var = requests.get(url, timeout=30)
    if requests_var.status_code != 200:
        raise RuntimeError(f"Page at URL {url} not found")

    packages = requests_var.text

    koji_repo_dict = {}
    for line in packages.splitlines():
        matches = KOJI_RE.match(line)
        if matches is None:
            continue
        name = matches.group("name")
        if name in crates:
            # Fedora appears to be using non-SemVer standard version strings:
            # the standard seems to be to use a "~" instead of a "-" in some
            # places. See https://semver.org/ for the canonical grammar that
            # the semantic_version library adheres to.
            version = matches.group("version").replace("~", "-")
            koji_repo_dict[name] = Version(version)

    # Post-condition: koji_repo_dict.keys() <= cargo_tree.keys().
    # cargo tree may show internal dependencies that are not separate packages
    return koji_repo_dict


def build_cargo_metadata(manifest_path, *, skip_path=False):
    """
    Build a dict mapping crate to version spec from Cargo.toml.

    :param manifest_path: the path to the Cargo manifest file
    :type manifest_path: str or NoneType
    :param bool skip_path: if True, skip path dependencies
    :returns: a dict mapping crate name to version specification
    :rtype: str * SimpleSpec
    """
    command = [
        "cargo",
        "metadata",
        "--format-version=1",
        "--no-deps",
        "--all-features",
    ]
    if manifest_path is not None:
        command.append(f"--manifest-path={manifest_path}")

    with subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ) as proc:
        result = proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(
                f'"cargo metadata" failed to process Cargo.toml: {bytes(result[1]).decode("utf-8")}'
            )
        metadata_str = bytes(result[0]).decode("utf-8")

    metadata = json.loads(metadata_str)
    packages = metadata["packages"]
    package = packages[0]
    dependencies = package["dependencies"]

    # cargo-metadata insert spaces into "req" value; SimpleSpec constructor
    # rejects specifications that contain spaces.
    return {
        item["name"]: SimpleSpec(item["req"].replace(" ", ""))
        for item in dependencies
        if not skip_path or not "path" in item
    }
