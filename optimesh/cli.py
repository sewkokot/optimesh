# -*- coding: utf-8 -*-
#
import argparse
import math
import sys

import meshio
import numpy

from .__about__ import __version__
from .laplace import laplace
from .lloyd import lloyd
from .odt import odt
from . import chen_holst


def _get_parser():
    parser = argparse.ArgumentParser(description="Mesh smoothing/optimization.")

    parser.add_argument(
        "input_file", metavar="INPUT_FILE", type=str, help="Input mesh file"
    )

    parser.add_argument(
        "output_file", metavar="OUTPUT_FILE", type=str, help="Output mesh file"
    )

    parser.add_argument(
        "--method",
        "-m",
        required=True,
        choices=["laplace", "lloyd", "odt", "chen_odt", "chen_cpt"],
        help="smoothing method",
    )

    parser.add_argument(
        "--max-num-steps",
        "-n",
        metavar="MAX_NUM_STEPS",
        type=int,
        default=math.inf,
        help="maximum number of steps (default: infinity)",
    )

    parser.add_argument(
        "--tolerance",
        "-t",
        metavar="TOL",
        default=0.0,
        type=float,
        help="convergence criterion (method dependent, default: 0.0)",
    )

    parser.add_argument(
        "--verbosity", choices=[0, 1, 2], help="verbosity level (default: 1)", default=1
    )

    # parser.add_argument(
    #     "--output-step-filetype",
    #     "-s",
    #     dest="output_steps_filetype",
    #     default=None,
    #     help="write mesh after each Lloyd step",
    # )

    parser.add_argument(
        "--version",
        "-v",
        help="display version information",
        action="version",
        version="%(prog)s {}, Python {}".format(__version__, sys.version),
    )
    return parser


def main(argv=None):
    parser = _get_parser()
    args = parser.parse_args(argv)

    if not (args.max_num_steps or args.tolerance):
        parser.error('At least one of --max-num_steps or --tolerance required.')

    mesh = meshio.read(args.input_file)

    if mesh.points.shape[1] == 3:
        assert numpy.all(numpy.abs(mesh.points[:, 2]) < 1.0e-13)
        mesh.points = mesh.points[:, :2]

    if args.method == "laplace":
        X, cells = laplace(
            mesh.points,
            mesh.cells["triangle"],
            args.tolerance,
            args.max_num_steps,
            verbosity=args.verbosity,
        )
    elif args.method == "odt":
        X, cells = odt(
            mesh.points,
            mesh.cells["triangle"],
            args.tolerance,
            args.max_num_steps,
            verbosity=args.verbosity,
        )
    elif args.method == "lloyd":
        X, cells = lloyd(
            mesh.points,
            mesh.cells["triangle"],
            args.tolerance,
            args.max_num_steps,
            verbosity=args.verbosity,
            fcc_type="boundary",
            skip_inhomogenous=True,
        )
    elif args.method == "chen_odt":
        X, cells = chen_holst.odt(
            mesh.points,
            mesh.cells["triangle"],
            args.tolerance,
            args.max_num_steps,
            verbosity=args.verbosity,
        )
    else:
        assert args.method == "chen_cpt"
        X, cells = chen_holst.cpt(
            mesh.points,
            mesh.cells["triangle"],
            args.tolerance,
            args.max_num_steps,
            verbosity=args.verbosity,
        )

    if X.shape[1] != 3:
        X = numpy.column_stack([X[:, 0], X[:, 1], numpy.zeros(X.shape[0])])

    meshio.write_points_cells(args.output_file, X, {"triangle": cells})
    return
