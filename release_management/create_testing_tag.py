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
Tags a testing release
"""

# isort: STDLIB
import argparse
import subprocess
import sys

# isort: LOCAL
from _utils import set_tag

GITHUB_URL = "https://github.com/stratis-storage/testing"


def main():
    """
    Main function
    """

    parser = argparse.ArgumentParser(
        description=(
            "Tag a testing release for GitHub and push the tag. If the "
            "specified tag does not exist, create it. Push the tag, unless the "
            "--no-release option is specified."
        )
    )

    parser.add_argument(
        "release",
        action="store",
        help="release version",
    )

    parser.add_argument(
        "--no-release",
        action="store_true",
        default=False,
        dest="no_release",
        help="stop before pushing release changes to GitHub repo",
    )

    args = parser.parse_args()

    release_version = args.release

    tag = f"v{release_version}"

    set_tag(tag, f"version {release_version}")

    if args.no_release:
        return

    subprocess.run(
        ["git", "push", GITHUB_URL, tag],
        check=True,
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as err:  # pylint: disable=broad-except
        print(err)
        sys.exit(1)
