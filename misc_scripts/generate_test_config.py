#!/usr/bin/env python3

# Copyright 2021 Red Hat, Inc.
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
generate_test_config: generate JSON text to use in a stratis test
config file (with path /etc/stratis/test_config.json), using the
given arguments as the array items.

Example: "generate_test_config /dev/vdb1 /dev/vdb2 /dev/vdb3"
"""

import json
import sys


def main():
    """
    Main method
    """
    drives = sys.argv[1:]
    jsonout = json.dumps({"ok_to_destroy_dev_array_key": (drives)}, indent=4)
    print(jsonout)


if __name__ == "__main__":
    main()
