#!/usr/bin/env python3

# Copyright 2024 Red Hat, Inc.
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
Use the thin pool metadata output to visualize the Stratis stack.
"""

# isort: STDLIB
import argparse
import json


def print_cap_device(cap_device_metadata):
    """
    Print cap device info.
    """
    print(f"{cap_device_metadata['allocs'][0][1]}")


def print_data_tier(data_tier_metadata):
    """
    Print data tier info.
    """
    devices = data_tier_metadata["blockdev"]["allocs"][0]

    start_width = len(str(max(devices, key=lambda t: len(str(t["start"])))["start"]))
    length_width = len(str(max(devices, key=lambda t: len(str(t["length"])))["length"]))

    for items in devices:
        print(
            f" {items['parent']} {items['start']:>{start_width}} "
            f"{items['length']:>{length_width}}"
        )


def print_flex_layer(flex_devs_metadata):
    """
    Print flex layer info.
    """
    flattened_items = [
        (key, pair) for key, value in flex_devs_metadata.items() for pair in value
    ]
    sorted_items = list(sorted(flattened_items, key=lambda item: item[1][0]))

    last_item = sorted_items[-1]
    last_value = last_item[1]
    last_total = int(last_value[0]) + int(last_value[1])
    width = len(str(last_total))

    for key, value in sorted_items:
        print(
            f"{value[0]:>{width}} {value[1]:>{width}} "
            f"{int(value[0]) + int(value[1]):>{width}} {key}"
        )

    print()

    totals = {}
    for key, value in sorted_items:
        totals[key] = (totals[key] + value[1]) if key in totals else value[1]

    for key, value in totals.items():
        print(f"{value:>{width}} {key}")

    print()

    print(f"Flex Total: {sum(v for v in totals.values())}")


def _interpret_metadata(filename):
    """
    Interpret Stratis pool-level metadata.
    """
    with open(filename, "r", encoding="utf-8") as md_fd:
        metadata = json.load(md_fd)

    print("Data Tier:")
    print_data_tier(metadata["backstore"]["data_tier"])
    print()

    print("Cap:")
    print_cap_device(metadata["backstore"]["cap"])
    print()

    print("Flex:")
    print_flex_layer(metadata["flex_devs"])


def main():
    """
    Main method
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "metadata_file",
        action="store",
        help="file containing Stratis pool-level metadata",
    )
    args = parser.parse_args()
    _interpret_metadata(args.metadata_file)


if __name__ == "__main__":
    main()
