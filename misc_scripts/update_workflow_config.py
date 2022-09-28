#!/usr/bin/python3
"""
update_workflow_config: update the GitHub Actions workflow configuration,
either by changing the Rusttoolchain version, or changing the Fedora
version.
"""

# isort: STDLIB
import argparse

KEY_LSRT = r"# LOWEST SUPPORTED RUST TOOLCHAIN"
KEY_CDRT = r"# CURRENT DEVELOPMENT RUST TOOLCHAIN"
TOOLCHAIN_CHOICES = ["lowest", "current"]

KEY_LFDE = r"# LOWEST DEVELOPMENT ENVIRONMENT"
KEY_CFDE = r"# CURRENT DEVELOPMENT ENVIRONMENT"
KEY_NFDE = r"# NEXT DEVELOPMENT ENVIRONMENT"
ENV_CHOICES = ["lowest", "current", "next"]


def search_file(search_key, old_verstring, new_verstring, filename):
    """
    Read the file.

    :param str search_key: the search key for the line to replace
    :param str old_verstring: old version string
    :param str new_verstring: new version string
    :param str filename: the name of the file to read
    """

    output = []

    with open(filename, "r", encoding="utf-8") as file:
        for line in file:

            if search_key in line:
                templine = line.replace(old_verstring, new_verstring)
                if new_verstring not in templine:
                    raise RuntimeError(f'Old version "{old_verstring}" not in file')
                output.append(templine)
            else:
                output.append(line)

    return output


def gen_parser():
    """
    Generate parser.
    """
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    parser_r = subparsers.add_parser("rust", help="Rust version")
    parser_r.add_argument(
        "toolchain", choices=TOOLCHAIN_CHOICES, help="the toolchain to change"
    )
    parser_r.add_argument("file", help="the configuration file to read")
    parser_r.add_argument("outfile", help="the configuration file to write")
    parser_r.add_argument("old_version", help="the old Rust version")
    parser_r.add_argument("new_version", help="the new Rust version")
    parser_r.set_defaults(func=process_toolchain)

    parser_e = subparsers.add_parser("fedora", help="Fedora version")
    parser_e.add_argument(
        "fedora", choices=ENV_CHOICES, help="the environment to change"
    )
    parser_e.add_argument("file", help="the configuration file to read")
    parser_e.add_argument("outfile", help="the configuration file to write")
    parser_e.add_argument("old_version", help="the old Fedora version")
    parser_e.add_argument("new_version", help="the new Fedora version")
    parser_e.set_defaults(func=process_env)

    return parser


def process_file(search_key, args):
    """
    Process the file.

    :param str search_key: the search key for the line to replace
    :param args: the arguments passed on the command line
    """
    filename = args.file
    outfilename = args.outfile
    old_verstring = args.old_version + r"  " + search_key
    new_verstring = args.new_version + r"  " + search_key

    output = search_file(search_key, old_verstring, new_verstring, filename)

    with open(outfilename, "w+", encoding="utf-8") as outfile:
        for outline in output:
            outfile.write(outline)


def process_toolchain(args):
    """
    Process toolchain change command.

    :param args: the arguments passed on the command line
    """
    if args.toolchain == "lowest":
        search_key = KEY_LSRT
    elif args.toolchain == "current":
        search_key = KEY_CDRT
    process_file(search_key, args)


def process_env(args):
    """
    Process environment change command.

    :param args: the arguments passed on the command line
    """
    if args.fedora == "lowest":
        search_key = KEY_LFDE
    elif args.fedora == "current":
        search_key = KEY_CFDE
    elif args.fedora == "next":
        search_key = KEY_NFDE
    process_file(search_key, args)


def main():
    """
    Main method
    """

    parser = gen_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
