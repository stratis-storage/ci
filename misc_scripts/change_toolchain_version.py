#!/usr/bin/python3
"""
change_toolchain_version: change the toolchain version in the GitHub Actions
workflow configurations.
"""

# isort: STDLIB
import argparse

KEY_LSRT = r"# LOWEST SUPPORTED RUST TOOLCHAIN"
KEY_CDRT = r"# CURRENT DEVELOPMENT RUST TOOLCHAIN"
TOOLCHAIN_CHOICES = ["lowest", "current"]


def search_file(new_version, search_key, old_verstring, new_verstring, filename):
    """
    Read the file.
    """

    output = []

    with open(filename, "r") as file:
        for line in file:

            if search_key in line:
                templine = line.replace(old_verstring, new_verstring)
                if new_version not in templine:
                    raise RuntimeError("Old version not in file")
                output.append(templine)
            else:
                output.append(line)

    return output


def main():
    """
    Main method
    """

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "toolchain", choices=TOOLCHAIN_CHOICES, help="the toolchain to change"
    )
    parser.add_argument("file", help="the configuration file to change")
    parser.add_argument("old_version", help="the old Rust version")
    parser.add_argument("new_version", help="the new Rust version")
    args = parser.parse_args()

    new_version = args.new_version
    filename = args.file

    if args.toolchain == "lowest":
        search_key = KEY_LSRT
    elif args.toolchain == "current":
        search_key = KEY_CDRT

    old_verstring = args.old_version + r"  " + search_key
    new_verstring = args.new_version + r"  " + search_key

    output = search_file(
        new_version, search_key, old_verstring, new_verstring, filename
    )

    for line in output:
        print(line, end="")


if __name__ == "__main__":
    main()
