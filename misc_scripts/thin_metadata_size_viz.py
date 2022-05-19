#!/usr/bin/python3
"""
thin_metadata_size_viz: visualize the relation of thin_metadata_size inputs
to output.
"""

# isort: STDLIB
import argparse
import subprocess

# isort: THIRDPARTY
import numpy
from matplotlib import pyplot


def gen_parser():
    """
    Generate parser.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Generate a graph of the result of invoking thin_metadata_size "
            "over a range of values for thin pool size and the number of thin "
            "devices"
        )
    )
    parser.add_argument("block_size", help="block size in sectors")
    parser.add_argument(
        "pool_size",
        help=(
            "comma-separated triple representing pool size range: minimum "
            "and maximum in sectors, followed by the number of divisions"
        ),
    )
    parser.add_argument(
        "max_thins",
        help=(
            "comma-separated triple representing range of maximum number of "
            "thin devices in pool: minimum and maximum in sectors, followed by "
            "the number of divisions"
        ),
    )
    return parser


def build_arrays(block_size, values):
    """
    Build three matrices of values where the z_values are the result of
    running thin_metadata_size on the x and y values.

    :param int block_size: block size in sectors
    :param values: the matrix of pairs of arguments

    :returns: a triple of arrays for x, y, and z values
    """

    (x_values, y_values, z_values) = ([], [], [])
    for row in values:
        (x_row, y_row, z_row) = ([], [], [])
        for (pool_size, num_thins) in row:
            command = [
                "thin_metadata_size",
                f"--block-size={block_size}",
                f"--pool-size={pool_size}",
                f"--max-thins={num_thins}",
                "-n",
            ]
            with subprocess.Popen(command, stdout=subprocess.PIPE) as proc:
                result = int(proc.stdout.readline().decode("utf-8").strip())
            x_row.append(pool_size)
            y_row.append(num_thins)
            z_row.append(result)
        x_values.append(x_row)
        y_values.append(y_row)
        z_values.append(z_row)

    return (numpy.array(x_values), numpy.array(y_values), numpy.array(z_values))


def plot_figure(x_inputs, y_inputs, z_inputs):
    """
    Plot a 3-d representation of the data.

    :param x_inputs: an array of x values
    :param y_inputs: an array of y values
    :param z_inputs: an array of z values
    """
    fig = pyplot.figure()
    axes = fig.add_subplot(
        projection="3d",
        xlabel="Pool Size",
        ylabel="Number of thin devices",
        zlabel="Metadata size",
    )
    axes.plot_wireframe(x_inputs, y_inputs, z_inputs)
    return fig


def main():  # pylint: disable=too-many-locals
    """
    Main method
    """

    parser = gen_parser()
    args = parser.parse_args()

    block_size = args.block_size
    (min_pool_size, max_pool_size, pool_size_intervals) = [
        int(x) for x in args.pool_size.split(",")
    ]
    (min_num_thins, max_num_thins, num_thins_intervals) = [
        int(x) for x in args.max_thins.split(",")
    ]

    pool_size_step = (max_pool_size - min_pool_size) // pool_size_intervals
    if pool_size_step <= 0:
        raise RuntimeError(
            f"Pool size increment is {pool_size_step} which is not a positive number"
        )

    num_thins_step = (max_num_thins - min_num_thins) // num_thins_intervals
    if num_thins_step <= 0:
        raise RuntimeError(
            f"Number of thin devices increment is {num_thins_step} which is not a positive number"
        )

    x_values = list(
        range(min_pool_size, max_pool_size + pool_size_step, pool_size_step)
    )
    y_values = list(
        range(min_num_thins, max_num_thins + num_thins_step, num_thins_step)
    )

    values = [[(x, y) for x in x_values] for y in y_values]

    (x_inputs, y_inputs, z_inputs) = build_arrays(block_size, values)

    fig = plot_figure(x_inputs, y_inputs, z_inputs)
    fig.savefig("metadata.svg")


if __name__ == "__main__":
    main()
