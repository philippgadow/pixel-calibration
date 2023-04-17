import argparse
from pathlib import Path
from pixel_calibration import Calibration


def parse_args(args):
    parser = argparse.ArgumentParser(
        description="Run calibration",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--reference",
        required=True,
        type=Path,
        help="path to reference measurement",
    )

    parser.add_argument(
        "--iron",
        required=True,
        type=Path,
        help="path to iron source measurement",
    )

    return parser.parse_args(args)


def main(args=None):
    args = parse_args(args)

    calib_ref = Calibration('reference', args.reference)
    calib_ref.read_csv()
    calib_ref.evaluate()
    calib_ref.plot()

    calib_source_fe = Calibration("iron", args.iron)
    calib_source_fe.read_csv()
    calib_source_fe.evaluate()
    calib_source_fe.plot()


if __name__ == "__main__":
    main()
