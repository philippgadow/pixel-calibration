import logging
import numpy as np
import pandas as pd

from hist import Hist
from tqdm import tqdm
from os.path import join
from os import makedirs

from pixel_calibration.plotting import plot_hist, plot_map

class Calibration():
    def __init__(self, name="", file="", mask_file="", n_cols=128, n_rows=128, measure_tot=False):
        self.name=name
        self.log = logging.getLogger(name)
        self.log.setLevel(logging.INFO)

        self.file = str(file)
        self.mask_file = mask_file

        self.n_cols = n_cols
        self.n_rows = n_rows
        self.measure_tot = measure_tot

        # measurements, indiced by threshold
        self.measurements = {}

        # histograms with counts per threshold ("ths")
        self.hist_count = Hist.new.Reg(2299, 0, 2299, name="ths").Double()
        self.hist_count_even = Hist.new.Reg(2299, 0, 2299, name="ths").Double()
        self.hist_count_odd = Hist.new.Reg(2299, 0, 2299, name="ths").Double()

        # output folder
        self.output_folder = join("output", self.name)
        makedirs(join(self.output_folder, 'plots'), exist_ok=True)
        makedirs(join(self.output_folder, 'data'), exist_ok=True)

        # read mask file
        self.mask = None
        if self.mask_file: self.read_mask_file()


    def read_mask_file(self):
        columns = ['col', 'row']
        dtype = {
            'col': np.int32,
            'row': np.int32,
        }
        df = pd.read_csv(self.mask_file, comment='#', names=columns, dtype=dtype)
        self.mask = pd.MultiIndex.from_frame(df)


    def read_csv(self):
        columns = ['ths', 'col', 'row', 'hit', 'count']
        dtype = {
            'ths': np.int32,
            'col': np.int32,
            'row': np.int32,
            'hit': np.int32,
            'count': np.int32,
        }
        if self.measure_tot:
            columns = ['ths', 'col', 'row', 'hit', 'tot', 'count']
            dtype = {
                'ths': np.int32,
                'col': np.int32,
                'row': np.int32,
                'hit': np.int32,
                'tot': np.int32,
                'count': np.int32,
        }

        if self.file.endswith('.csv'):
            df = pd.read_csv(self.file, comment='#', names=columns, dtype=dtype, index_col='ths')
        elif self.file.endswith('.h5'):
            df = pd.read_hdf(self.file, columns=columns, index_col='ths')
        else:
            raise RuntimeError("Unknown input file format.")

        # sort full dataframe in individual measurements per threshold
        thresholds = df.index.unique()
        self.log.info(f'Reading input file {self.file}...')
        for ths in tqdm(thresholds):
            data = df.loc[[ths],["col", "row", "count"]]
            self.measurements[ths] = Measurement(f"ths_calib_{self.name}", ths, self.n_cols, self.n_rows, data, 'count', self.mask)


    def plot(self):
        plot_hist(self.hist_count.project("ths"), '', join(self.output_folder, 'plots', f'calib_{self.name}.png'))
        plot_hist(self.hist_count_even.project("ths"), 'even', join(self.output_folder, 'plots', f'calib_{self.name}_even.png'))
        plot_hist(self.hist_count_odd.project("ths"), 'odd', join(self.output_folder, 'plots', f'calib_{self.name}_odd.png'))

        # plot maps of measurements
        self.log.info(f'Plotting measurement results...')
        for ths, m in self.measurements.items():
            m.plot(join(self.output_folder, 'plots'))

    def evaluate(self):
        self.log.info(f'Evaluating measurements...')
        with open(join(self.output_folder, 'data', f'single_pixel_counts_{self.name}.csv'), 'w') as outfile:
            outfile.write("threshold,counts,counts_even,counts_odd\n")
            for ths, m in tqdm(self.measurements.items()):
                single_pixel_counts, single_pixel_counts_even, single_pixel_counts_odd = m.find_single_pixel()
                self.hist_count.fill([ths for i in single_pixel_counts], weight=single_pixel_counts)
                self.hist_count_even.fill([ths for i in single_pixel_counts_even], weight=single_pixel_counts_even)
                self.hist_count_odd.fill([ths for i in single_pixel_counts_odd], weight=single_pixel_counts_odd)
                outfile.write(f"{ths},{np.sum(single_pixel_counts)},{np.sum(single_pixel_counts_even)},{np.sum(single_pixel_counts_odd)}\n")

        # normalise histograms
        self.hist_count /= np.max(self.hist_count.values())
        self.hist_count_even /= np.max(self.hist_count_even.values())
        self.hist_count_odd /= np.max(self.hist_count_odd.values())

        # fit histograms


        
class Measurement():
    def __init__(self, name="", threshold=0, n_cols=128, n_rows=128, data=None, value='count', mask=None):
        self.name = name
        self.threshold = threshold
        self.value = value
        self.n_cols = n_cols
        self.n_rows = n_rows

        self.map = np.zeros((self.n_cols, self.n_rows))
        self.map_single = np.zeros((self.n_cols, self.n_rows))

        if data is not None: self.load(data, value, mask)


    def load(self, data, value='count', mask=None):
        # convert data from measurement to a map of the sensor
        # if there are multiple measurements for a given threshold, sum them up
        table = data.groupby(['col', 'row'])[value].sum().to_frame()
        # the measurement data is only recorded if there are counts
        # therefore, padding of empty rows and columns is applied to the map
        new_index = pd.MultiIndex.from_product([range(self.n_cols), range(self.n_rows)], names=('col', 'row'))
        self.map = table.reindex(new_index).fillna(0).astype(np.int32).to_numpy().reshape(self.n_cols,self.n_rows)
         # if mask map is provided, remove masked pixels (mask: column, row)
        if mask is not None:
            for i in mask: self.map[i[0]][i[1]] = 0

    def find_single_pixel(self):
        from itertools import product
        single_pixel_counts = []
        single_pixel_counts_even = []
        single_pixel_counts_odd = []

        for i, j in product(range(self.n_cols), range(self.n_rows)):
            # only consider pixels which had a count > 0
            single_pixel = (self.map[i][j] > 0)
            # scan for neighouring pixels
            for ii, jj in product(range(i-1, i+1), range(j-1, j+1)):
                if (ii==i and jj==j): continue
                if (ii < 0 or jj < 0 or ii > self.n_cols or jj > self.n_rows): continue
                # if neighbour exist, this is not a single pixel
                if (self.map[ii][jj] > 0): single_pixel = False
            self.map_single[i][j] = int(single_pixel)

            # if single pixel was found, add count to list
            # so that it can be filled in calibration histogram
            # for given threshold
            if single_pixel:
                single_pixel_counts.append(self.map[i][j])
                if (i%2==0): single_pixel_counts_even.append(self.map[i][j])
                else: single_pixel_counts_odd.append(self.map[i][j])

        return single_pixel_counts, single_pixel_counts_even, single_pixel_counts_odd

    def plot(self, output_folder):
        plot_map(self.map, self.value, join(output_folder, f"map_{self.name}_{self.threshold}"))
        plot_map(self.map_single, 'single pixel', join(output_folder, f"map_{self.name}_{self.threshold}_single_pixel.png"))
