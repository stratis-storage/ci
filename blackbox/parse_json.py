#!/usr/bin/python3

import json
import sys

def parse_json(path):
    with open(path) as test_config_file:
        json_string = test_config_file.read()

    json_data = json.loads(json_string)
    ok_to_destroy = json_data.get("ok_to_destroy_dev_array_key")
    if ok_to_destroy is None:
        raise RuntimeError("Required JSON key 'ok_to_destroy_dev_array_key' is missing in file %s" % path)
    print(','.join(ok_to_destroy))

if __name__ == "__main__":
    try:
        test_config_path = sys.argv[1]
    except IndexError:
        raise RuntimeError("Required argument of test_config.json path is missing")

    try:
        parse_json(test_config_path)
    except Exception as e:
        raise RuntimeError("Parsing JSON in %s failed: %s" % (test_config_path, error))
