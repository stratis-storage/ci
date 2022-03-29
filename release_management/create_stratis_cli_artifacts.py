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
Create stratis-cli artifacts for packaging tests.

Assumes that the stratis-cli version number in setup.py is the correct one.
"""

# isort: STDLIB
import argparse
import os
import sys

# isort: LOCAL
from _utils import get_python_package_info, make_source_tarball

GITHUB_URL = "https://github.com/stratis-storage/stratis-cli"


def main():
    """
    Main function
    """

    parser = argparse.ArgumentParser(
        description=(
            "Generate artifacts for a stratis-cli release. Expects to be run "
            "in clean stratis-cli top-level directory. Makes output dir if it "
            "does not already exist, but does not clean it."
        )
    )

    parser.add_argument("output_dir", action="store", help="directory for artifacts")

    args = parser.parse_args()

    output_abs_path = os.path.abspath(args.output_dir)
    os.makedirs(output_abs_path, exist_ok=True)

    (release_version, _) = get_python_package_info(GITHUB_URL)

    make_source_tarball("stratis-cli", release_version, output_abs_path)


if __name__ == "__main__":
    try:
        main()
    except Exception as err:  # pylint: disable=broad-except
        print(err)
        sys.exit(1)
