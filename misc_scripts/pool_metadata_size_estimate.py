#!/usr/bin/python3
"""
pool_metadata_size_estimate: estimate the inrease of pool level metadata due
to addition of blockdevs.
"""

# isort: STDLIB
import argparse

# isort: THIRDPARTY
from justbytes import Range

STRING = 255
UUID = 36


def metadata_str(value):
    """
    Parse a value representing the size of a metadata string.
    """
    value = int(value)
    if value > 255:
        raise argparse.ArgumentTypeError(
            f"Exceeds maximum length {STRING} for metadata string."
        )

    if value < 0:
        raise argparse.ArgumentTypeError("Negative lengths prohbited.")

    return value


def nat(value):
    """
    Parse a value representing a natural number.
    """
    value = int(value)
    if value < 0:
        raise argparse.ArgumentTypeError("Must be a natural number.")
    return value


def gen_parser():
    """
    Generate parser.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Calculate size increase in Stratis pool-level metadata due to "
            "addition of new devices."
        )
    )

    parser.add_argument(
        "num_devices",
        help="Number of devices to be added",
        type=nat,
    )

    parser.add_argument(
        "--hardware-info",
        dest="hardware_info",
        help="Bytes required to represent hardware info.",
        type=metadata_str,
    )

    parser.add_argument(
        "--user-info",
        dest="user_info",
        help="Bytes required to represent user info.",
        type=metadata_str,
    )

    return parser


def f(*, hardware_info=None, user_info=None):
    """
    Calculate the bytes required to store num_devices in metadata.

    :param hardware_info: the len of the hardware info
    :param user_info: the len of the user info
    """
    commas = (0 if hardware_info is None else 1) + (0 if user_info is None else 1)

    m = (
        commas
        + (0 if hardware_info is None else hardware_info + 18)
        + (0 if user_info is None else user_info + 13)
        + (UUID + 9)
        + 3
    )

    return m


def main():
    """
    Main method
    """

    parser = gen_parser()
    args = parser.parse_args()

    num_devices = args.num_devices

    user_info = args.user_info
    hardware_info = args.hardware_info

    m = f(hardware_info=hardware_info, user_info=user_info)
    print(f"Slope: {m} bytes")
    prediction = m * num_devices
    print(f"Predicted use: {prediction} bytes, approx {Range(prediction)}")


if __name__ == "__main__":
    main()
