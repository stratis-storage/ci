#!/usr/bin/python3
"""
Generate a list of integers for input to another program.
"""

# isort: STDLIB
import argparse


def gen_parser():
    """
    Generate parser.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Print a one column table of integers according to specifications."
        )
    )

    parser.add_argument(
        "--start",
        action="store",
        type=int,
        default=512 * 1024**2,
        help="Start value",
    )

    parser.add_argument(
        "--stop",
        action="store",
        type=int,
        default=8 * 1024**4,
        help="End value",
    )

    return parser


def _print_values(*, start, stop):
    """
    Print a succession of integer values. Each size is double that of the last.

    :param int start: the value to start at
    :param int stop: the value to end at
    """
    value = start
    while value <= stop:
        print(value)
        value = value * 2


def main():
    """
    Main method
    """

    parser = gen_parser()
    args = parser.parse_args()

    _print_values(start=args.start, stop=args.stop)


if __name__ == "__main__":
    main()
