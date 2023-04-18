import argparse
from pathlib import Path
from pixel_calibration import Calibration


def parse_args(args):
    parser = argparse.ArgumentParser(
        description="Run calibration",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--file",
        required=True,
        type=Path,
        help="path to measurement",
    )

    parser.add_argument(
        "--name",
        required=True,
        type=str,
        help="name for measurement",
    )

    parser.add_argument(
        "--mask",
        default=None,
        help="path to mask file to eliminate pixels from calibration",
    )

    return parser.parse_args(args)


def main(args=None):
    args = parse_args(args)

    calib = Calibration(args.name, args.file, args.mask)
    calib.read_csv()
    calib.evaluate()
    calib.plot()


if __name__ == "__main__":
    main()
