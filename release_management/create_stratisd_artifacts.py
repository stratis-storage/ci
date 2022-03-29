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
Create stratisd artifacts for packaging tests.

Assumes that the stratisd version number in Cargo.toml is the correct one.
"""

# isort: STDLIB
import argparse
import os
import subprocess
import sys

# isort: LOCAL
from _utils import MANIFEST_PATH, get_package_info, vendor


def _make_stratisd_tarball(release_version, output_dir):
    """
    Make the stratisd tarball and place it in the output dir.
    """
    output_file = os.path.join(output_dir, "stratisd-%s.tar.gz" % release_version)
    subprocess.run(
        [
            "tar",
            "--exclude-vcs",
            "--exclude-vcs-ignore",
            "--directory=%s" % "..",
            "--create",
            "--verbose",
            "--gzip",
            "--transform=/^stratisd/stratisd-%s/" % release_version,
            "--file=%s" % output_file,
            "stratisd",
        ],
        check=True,
    )


def main():
    """
    Main function
    """

    parser = argparse.ArgumentParser(
        description=("Generate artifacts for a stratisd release.")
    )

    parser.add_argument("output_dir", action="store", help="directory for artifacts")

    args = parser.parse_args()

    manifest_abs_path = os.path.abspath(MANIFEST_PATH)
    if not os.path.exists(manifest_abs_path):
        raise RuntimeError(
            "Need script to run at top-level of package, in same directory as Cargo.toml"
        )

    output_abs_path = os.path.abspath(args.output_dir)
    os.makedirs(output_abs_path, exist_ok=True)

    (release_version, _) = get_package_info(manifest_abs_path, "stratisd")
    vendor_tarfile_name = vendor(manifest_abs_path, release_version)

    os.rename(vendor_tarfile_name, os.path.join(output_abs_path, vendor_tarfile_name))

    crate_name = "stratisd-%s.crate" % release_version
    crate_path = os.path.join("target", "package", crate_name)
    os.rename(crate_path, os.path.join(output_abs_path, crate_name))

    _make_stratisd_tarball(release_version, output_abs_path)


if __name__ == "__main__":
    try:
        main()
    except Exception as err:  # pylint: disable=broad-except
        print(err)
        sys.exit(1)
