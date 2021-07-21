#!/usr/bin/python3
"""
change_toolchain_version: change the toolchain version in the GitHub Actions
workflow configurations.
"""

import argparse

KEY_LSRT = r"# LOWEST SUPPORTED RUST TOOLCHAIN"


def main():
    """
    Main method
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    parser.add_argument("old_version")
    parser.add_argument("new_version")
    args = parser.parse_args()

    filename = args.file
    outfilename = filename + ".new"

    old_verstring = args.old_version + r"  " + KEY_LSRT
    new_verstring = args.new_version + r"  " + KEY_LSRT

    print("Test outfile: %s" % outfilename)
    print("Old version: %s" % args.old_version)
    print("New version: %s" % args.new_version)

    with open(filename, "r") as file:
        for line in file:

            if KEY_LSRT in line:
                templine = line.replace(old_verstring, new_verstring)
                if args.new_version not in templine:
                    raise ValueError("Old version not in file")
                print(templine)
            else:
                print(line)


if __name__ == "__main__":
    main()
