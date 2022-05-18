#!/usr/bin/python3
"""
Helper module for parsing a JSON configuration file into a usable
format for bash.
"""

# isort: STDLIB
import json
import sys


def parse_json(path):
    """
    Opens the provided JSON file and searches for the required key.
    The return value is a comma-delimited string of device names.
    """

    with open(path, encoding="utf-8") as test_config_file:
        json_string = test_config_file.read()

    json_data = json.loads(json_string)
    ok_to_destroy = json_data.get("ok_to_destroy_dev_array_key")
    if ok_to_destroy is None:
        raise RuntimeError(
            f"Required JSON key 'ok_to_destroy_dev_array_key' is missing in file {path}"
        )
    print(",".join(ok_to_destroy))


if __name__ == "__main__":
    try:
        TEST_CONFIG_PATH = sys.argv[1]
    except IndexError as err:
        raise RuntimeError(
            "Required argument of test_config.json path is missing"
        ) from err

    try:
        parse_json(TEST_CONFIG_PATH)
    except Exception as err:
        raise RuntimeError(f"Parsing JSON in {TEST_CONFIG_PATH} failed: {err}") from err
