#!/usr/bin/python3
"""
Estimate filesystem size consumption for logical filesystem sizes.
"""

# isort: STDLIB
import argparse
import json
import os
import subprocess
import sys

_STRATIS_PREDICT_USAGE = os.environ["STRATIS_PREDICT_USAGE"]


def _call_predict_usage(encrypted, overprovision, device_sizes, *, fs_size=None):
    """
    Call stratis-predict-usage and return JSON result.

    :param bool encrypted: true if pool is to be encrypted
    :param bool overprovision: true if pool is overprovisioned
    :param device_sizes: list of sizes of devices for pool
    :type device_sizes: list of str
    :param str fs_size: logical size of filesystem
    """
    with subprocess.Popen(
        [_STRATIS_PREDICT_USAGE, "pool"]
        + ["--device-size=%s" % size for size in device_sizes]
        + ([] if fs_size is None else ["--filesystem-size=%s" % fs_size])
        + (["--encrypted"] if encrypted else [])
        + ([] if overprovision else ["--no-overprovision"]),
        stdout=subprocess.PIPE,
    ) as command:
        outs, errs = command.communicate()
        if command.returncode != 0:
            raise RuntimeError(
                "Invocation of %s returned an error: %s, %s"
                % (_STRATIS_PREDICT_USAGE, command.returncode, errs)
            )
        prediction = json.loads(outs)

    return prediction


def gen_parser():
    """
    Generate parser.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Calculate results for filesystem sizes from output of "
            "stratis-predict-usage."
        )
    )
    parser.add_argument(
        "--device-size",
        action="extend",
        dest="device_size",
        nargs="+",
        type=str,
        required=True,
        help="Size of devices with which to instantiate the pool.",
    )
    parser.add_argument(
        "--encrypted", action="store_true", help="Whether pool is to be encrypted."
    )
    parser.add_argument(
        "--no-overprovision",
        action="store_true",
        help="Whether pool is to prohbit overprovisioning.",
    )
    return parser


def _print_values(device_sizes, encrypted, overprovision):
    """
    Print table of filesystem size values.

    :param device_sizes: list of device sizes
    :type device_sizes: list of str
    :param bool encrypted: whether or not pool is encrypted
    """

    key = "used"
    pre_prediction = _call_predict_usage(encrypted, overprovision, device_sizes)
    pre_usage = int(pre_prediction[key])
    admin_usage = int(pre_prediction["stratis-admin-space"])
    metadata_usage = int(pre_prediction["stratis-metadata-space"])

    for line in sys.stdin:
        size = line.rstrip()
        post_prediction = _call_predict_usage(
            encrypted, overprovision, device_sizes, fs_size=size
        )

        post_usage = int(post_prediction[key])

        print(
            "%s %s %s %s %s"
            % (size, pre_usage, admin_usage, metadata_usage, post_usage - pre_usage)
        )


def main():
    """
    Main method
    """

    parser = gen_parser()
    args = parser.parse_args()

    _print_values(args.device_size, args.encrypted, not args.no_overprovision)


if __name__ == "__main__":
    main()
