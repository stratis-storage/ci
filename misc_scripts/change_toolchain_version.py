#!/usr/bin/python3
"""
change_toolchain_version: change the toolchain version in the GitHub Actions
workflow configurations.
"""

# isort: STDLIB
import argparse

KEY_LSRT = r"# LOWEST SUPPORTED RUST TOOLCHAIN"
KEY_CDRT = r"# CURRENT DEVELOPMENT RUST TOOLCHAIN"


def main():
    """
    Main method
    """

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "toolchain", choices=["lowest", "current"], help="the toolchain to change"
    )
    parser.add_argument("file", help="the configuration file to change")
    parser.add_argument("old_version", help="the old Rust version")
    parser.add_argument("new_version", help="the new Rust version")
    args = parser.parse_args()

    filename = args.file

    if args.toolchain == "lowest":
        search_key = KEY_LSRT
    elif args.toolchain == "current":
        search_key = KEY_CDRT

    old_verstring = args.old_version + r"  " + search_key
    new_verstring = args.new_version + r"  " + search_key

    with open(filename, "r") as file:
        for line in file:

            if search_key in line:
                templine = line.replace(old_verstring, new_verstring)
                if args.new_version not in templine:
                    raise ValueError("Old version not in file")
                print(templine)
            else:
                print(line)


if __name__ == "__main__":
    main()
