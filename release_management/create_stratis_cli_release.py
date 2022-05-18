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
Creates a stratis-cli release
"""

# isort: STDLIB
import argparse
import subprocess
import sys

# isort: LOCAL
from _utils import (
    create_release,
    get_branch,
    get_changelog_url,
    get_python_package_info,
    verify_tag,
)

PACKAGE_NAME = "stratis-cli"

GITHUB_URL = "https://github.com/stratis-storage/stratis-cli"


def main():
    """
    Main function
    """

    parser = argparse.ArgumentParser(
        description=(
            "Prepare a stratis-cli release for GitHub and upload it. If a tag "
            "does not exist for the release specified in setup.py, tag the "
            "current commit. Push the specified tag and create a draft release "
            "on GitHub."
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
        help="stop before pushing release changes to GitHub repo",
    )

    args = parser.parse_args()

    (release_version, repository) = get_python_package_info(GITHUB_URL)

    if args.no_tag:
        return

    tag = f"v{release_version}"

    if not verify_tag(tag):
        message = f"version {release_version}"
        subprocess.run(
            ["git", "tag", "--annotate", tag, f'--message="{message}"'],
            check=True,
        )

    repository_url = repository.geturl()

    subprocess.run(
        ["git", "push", repository_url, tag],
        check=True,
    )

    if args.no_release:
        return

    changelog_url = get_changelog_url(repository_url, get_branch())

    create_release(repository, tag, release_version, changelog_url)


if __name__ == "__main__":
    try:
        main()
    except Exception as err:  # pylint: disable=broad-except
        print(err)
        sys.exit(1)
