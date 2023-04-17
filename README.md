# Pixel calibration

This project contains software for calibrating silicon pixel detectors.

## Installation

The software relies on several python packages. A convenient way to install these is using a conda environment:

```bash
conda env create -f environment.yml
```

After creating the environment, you can activate it and install the local version of the pixel_calibration software.

```bash
conda activate pixel-calibration 
python -m pip install -e .
```

## Run calibration

Assuming you have acquired data with peary, you can use the csv files to run the calibration code:

```bash
calibrate_threshold --reference data/cal.csv --iron data/iron.csv
```

As a result, you find the outputs from the calibration in the `output` directory.
