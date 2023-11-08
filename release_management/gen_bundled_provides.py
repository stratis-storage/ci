#!/usr/bin/python3
#
# Copyright 2023 Red Hat, Inc.
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
Generate vendored provides list from vendor tarfile.
"""

# isort: STDLIB
import argparse
import os
import sys

# isort: LOCAL
from _utils import get_bundled_provides


def main():
    """
    Main function
    """

    parser = argparse.ArgumentParser(
        description=(
            "Generate a list of bundled provides suitable for including in an "
            "rpm spec file. Include in the list only those dependencies which "
            "have source code in the vendor tarfile. Prints list to stdout."
        )
    )

    parser.add_argument(
        "vendor_tarfile",
        action="store",
        help="path to vendor tarfile",
        type=os.path.abspath,
    )

    namespace = parser.parse_args()

    for line in get_bundled_provides(namespace.vendor_tarfile):
        print(line)

    return 0


if __name__ == "__main__":
    try:
        main()
    except Exception as err:  # pylint: disable=broad-except
        print(err)
        sys.exit(1)
