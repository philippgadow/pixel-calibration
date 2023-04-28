import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from hist import Hist
from pixel_calibration.plotting import plot_hist


def parse_args(args):
    parser = argparse.ArgumentParser(
        description="Run calibration",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--reference",
        required=True,
        type=Path,
        help="path to measurement",
    )

    parser.add_argument(
        "--iron",
        required=True,
        type=str,
        help="name for measurement",
    )

    return parser.parse_args(args)


def main(args=None):
    args = parse_args(args)

    df_reference = pd.read_csv(args.reference, index_col='threshold')
    df_iron = pd.read_csv(args.iron, index_col='threshold')
    idx = df_reference.index.intersection(df_iron.index)

    # normalise counts
    df_reference['counts'] = df_reference['counts'] / np.max(df_reference['counts'].to_numpy())
    df_iron['counts'] = df_iron['counts'] / np.max(df_iron['counts'].to_numpy())

    print(idx.min(), idx.max())

    df_iron_diff = df_iron.loc[idx] - df_reference.loc[idx]

    # plot histograms
    h = (
        Hist.new
        .Reg(idx.max() - idx.min(), idx.min(), idx.max(), name="ths", label="Threshold [ADC count]")
        .Double()
    )
    h.fill(idx.to_numpy(), weight=df_iron_diff['counts'].to_numpy())
    plot_hist(h.project("ths"), '', 'plotty_mcplotface.png')

    idx_max = np.argmax(h.values())
    ths_max = idx[idx_max]
    print(f"Maximum threshold for source: {ths_max}")

    

if __name__ == "__main__":
    main()
