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
usage: analyse [-h] --file FILE --name NAME [--mask MASK] [--threshold THRESHOLD] [--tot] [--find_hot_pixels FIND_HOT_PIXELS]

Run calibration

optional arguments:
  -h, --help            show this help message and exit
  --file FILE           path to measurement (default: None)
  --name NAME           name for measurement (default: None)
  --mask MASK           path to mask file to eliminate pixels from calibration (default: None)
  --threshold THRESHOLD
                        Threshold of measurement, use only if processing data taking with acquire mode as opposed to threshold scan (default: None)
  --tot                 Analyse time over threshold measurement (default: False)
  --find_hot_pixels FIND_HOT_PIXELS
                        if set, determine hot pixels (with specified percent of highest counts) (default: None)
```

Note that you can provide a mask file, which contains in csv format the column and row of pixels which should be masked for the calibration.

As a result, you find the outputs from the calibration in the `output` directory.

```bash
usage: calibrate_threshold [-h] --reference REFERENCE --iron IRON

Run calibration

optional arguments:
  -h, --help            show this help message and exit
  --reference REFERENCE
                        path to measurement (default: None)
  --iron IRON           name for measurement (default: None)
```