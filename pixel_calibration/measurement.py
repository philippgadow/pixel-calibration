import logging
import numpy as np
import pandas as pd

from hist import Hist
from tqdm import tqdm
from os.path import join
from os import makedirs

from pixel_calibration.plotting import plot_hist, plot_map, plot_hotpixel
from pixel_calibration.utils import cast_df_to_array, find_hottest_pixel


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
        self.value = "count"

        # pandas dataframe with full measurement
        self.data_df = None

        # measurements, indiced by threshold
        self.measurements = {}

        # 2D histogram of all counts for all measurements
        self.map = np.zeros((self.n_cols, self.n_rows))
       
        # output folder
        self.output_folder = join("output", self.name)

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


    def read_csv(self, threshold=None):
        if threshold is None:
            self.read_csv_scan_threshold()
        else:
            self.read_csv_acquire(threshold)



    def read_csv_scan_threshold(self):
        columns = ['ths', 'col', 'row', 'hit', self.value]
        dtype = {
            'ths': np.int32,
            'col': np.int32,
            'row': np.int32,
            'hit': np.int32,
            self.value: np.int32,
        }
        if self.measure_tot:
            columns = ['ths', 'col', 'row', 'hit', 'tot', self.value]
            dtype = {
                'ths': np.int32,
                'col': np.int32,
                'row': np.int32,
                'hit': np.int32,
                'tot': np.int32,
                self.value: np.int32,
            }

        self.log.info(f'Loading input file {self.file}...')
        if self.file.endswith('.csv'):
            self.data_df = pd.read_csv(self.file, comment='#', names=columns, dtype=dtype, index_col='ths')
        elif self.file.endswith('.h5'):
            self.data_df = pd.read_hdf(self.file, columns=columns, index_col='ths')
        else:
            raise RuntimeError("Unknown input file format.")
        self.log.info(f'Loading done!')


    def read_csv_acquire(self, threshold):
        columns = ['col', 'row', 'hit', self.value]
        dtype = {
                'col': np.int32,
                'row': np.int32,
                'hit': np.int32,
                self.value: np.int32,
        }
        if self.measure_tot:
            columns = ['col', 'row', 'hit', 'tot', self.value]
            dtype = {
                    'col': np.int32,
                    'row': np.int32,
                    'hit': np.int32,
                    'tot': np.int32,
                    self.value: np.int32,
            }
        # first six rows are comments by peary, individual acquisitions are indexed with === number === and need to be filtered out
        self.log.info(f'Loading input file {self.file}...')
        if self.file.endswith('.csv'):
            df = pd.read_csv(self.file, comment='=', skiprows=6, names=columns, dtype=dtype)
            df.insert(0, "ths", threshold)
            self.data_df = df.set_index('ths')
        else:
            raise RuntimeError("Unknown input file format.")
        self.log.info(f'Loading done!')


    def evaluate(self, plot_maps=False):
        self.log.info(f'Processing measurements...')
        makedirs(join(self.output_folder, 'plots'), exist_ok=True)
        makedirs(join(self.output_folder, 'data'), exist_ok=True)
        # convert all measurements into 2D array
        self.map = cast_df_to_array(self.data_df.loc[:,["col", "row", self.value]], self.value, self.n_cols, self.n_rows)

        # sort full dataframe in individual measurements per threshold
        thresholds = self.data_df.index.unique()
        for ths in tqdm(thresholds):
            data = self.data_df.loc[[ths],["col", "row", self.value]]
            self.measurements[ths] = Measurement(f"ths_calib_{self.name}", ths, self.n_cols, self.n_rows, data, self.value, self.mask)

        # analyse single pixel
        self.log.info(f'Starting analysis...')
        hist_count_totalpixel = Hist.new.Reg(2299, 0, 2299, name="ths").Double()
        hist_count_totalpixel_even = Hist.new.Reg(2299, 0, 2299, name="ths").Double()
        hist_count_totalpixel_odd = Hist.new.Reg(2299, 0, 2299, name="ths").Double()

        hist_count_singlepixel = Hist.new.Reg(2299, 0, 2299, name="ths").Double()
        hist_count_singlepixel_even = Hist.new.Reg(2299, 0, 2299, name="ths").Double()
        hist_count_singlepixel_odd = Hist.new.Reg(2299, 0, 2299, name="ths").Double()


        with open(join(self.output_folder, 'data', f'total_pixel_counts_{self.name}.csv'), 'w') as outfile_total, \
             open(join(self.output_folder, 'data', f'single_pixel_counts_{self.name}.csv'), 'w') as outfile_single:
            outfile_total.write("threshold,counts,counts_even,counts_odd\n")
            outfile_single.write("threshold,counts,counts_even,counts_odd\n")
            for ths, m in tqdm(self.measurements.items()):
                # sum all pixels
                total_pixel_counts, total_pixel_counts_even, total_pixel_counts_odd = m.find_total_pixel()
                hist_count_totalpixel.fill(ths, weight=total_pixel_counts)
                hist_count_totalpixel_even.fill(ths, weight=total_pixel_counts_even)
                hist_count_totalpixel_odd.fill(ths, weight=total_pixel_counts_odd)
                outfile_total.write(f"{ths},{np.sum(total_pixel_counts)},{np.sum(total_pixel_counts_even)},{np.sum(total_pixel_counts_odd)}\n")

                # find single pixels
                single_pixel_counts, single_pixel_counts_even, single_pixel_counts_odd = m.find_single_pixel()
                hist_count_singlepixel.fill(ths, weight=single_pixel_counts)
                hist_count_singlepixel_even.fill(ths, weight=single_pixel_counts_even)
                hist_count_singlepixel_odd.fill(ths, weight=single_pixel_counts_odd)
                outfile_single.write(f"{ths},{np.sum(single_pixel_counts)},{np.sum(single_pixel_counts_even)},{np.sum(single_pixel_counts_odd)}\n")

        # normalise histograms
        hist_count_totalpixel /= np.max(hist_count_totalpixel.values())
        hist_count_totalpixel_even /= np.max(hist_count_totalpixel_even.values())
        hist_count_totalpixel_odd /= np.max(hist_count_totalpixel_odd.values())

        hist_count_singlepixel /= np.max(hist_count_singlepixel.values())
        hist_count_singlepixel_even /= np.max(hist_count_singlepixel_even.values())
        hist_count_singlepixel_odd /= np.max(hist_count_singlepixel_odd.values())

        # fit histograms

        # plot histograms
        self.log.info(f'Plotting results...')
        plot_hist(hist_count_totalpixel.project("ths"), '', join(self.output_folder, 'plots', f'calib_totalpixel_{self.name}.png'))
        plot_hist(hist_count_totalpixel_even.project("ths"), 'even', join(self.output_folder, 'plots', f'calib_totalpixel_{self.name}_even.png'))
        plot_hist(hist_count_totalpixel_odd.project("ths"), 'odd', join(self.output_folder, 'plots', f'calib_totalpixel_{self.name}_odd.png'))

        plot_hist(hist_count_singlepixel.project("ths"), '', join(self.output_folder, 'plots', f'calib_singlepixel_{self.name}.png'))
        plot_hist(hist_count_singlepixel_even.project("ths"), 'even', join(self.output_folder, 'plots', f'calib_singlepixel_{self.name}_even.png'))
        plot_hist(hist_count_singlepixel_odd.project("ths"), 'odd', join(self.output_folder, 'plots', f'calib_singlepixel_{self.name}_odd.png'))

        # plot 2D map of total counts
        plot_map(self.map, self.value, join(self.output_folder, 'plots', f"total_map_{self.name}.png"))

        # plot maps of measurements
        if plot_maps:
            for ths, m in self.measurements.items():
                m.plot(join(self.output_folder, 'plots'))


    def find_hot_pixels(self, hottest_percent=0.01):
        makedirs(join(self.output_folder, 'hotpixel', 'plots'), exist_ok=True)
        makedirs(join(self.output_folder, 'hotpixel', 'data'), exist_ok=True)
        makedirs(join(self.output_folder, 'hotpixel', 'mask'), exist_ok=True)

        thresholds = self.data_df.index.unique()
        for ths in tqdm(thresholds):
            data = self.data_df.loc[[ths],["col", "row", self.value]]
            data = data.groupby(['col', 'row'])[self.value].sum().to_frame()
            df_hottest_pixel, cut_value = find_hottest_pixel(data, value=self.value, hottest_percent=hottest_percent)

            max_count = data[self.value].max()
            hist_hotpixel = Hist.new.Reg(100, 0, max_count, name="count").Double()
            hist_hotpixel.fill(data[self.value].values)
            plot_hotpixel(hist_hotpixel.project("count"), cut_value, join(self.output_folder, 'hotpixel', 'plots', f'hotpixel_{self.name}_{ths}.png'))

            f_hotpixel_count = open(join(self.output_folder, 'hotpixel', 'data', f'hot_pixel_counts_{self.name}_{ths}.csv'), 'w')
            f_hotpixel_count.write("col,row,counts\n")
            f_hotpixel_mask = open(join(self.output_folder, 'hotpixel', 'mask', f'hot_pixel_mask_{self.name}_{ths}.csv'), 'w')
            
            table_hottest_pixel_total = df_hottest_pixel.sort_values(by=[self.value], ascending=False)
            for index, row in table_hottest_pixel_total.iterrows():
                f_hotpixel_count.write(f"{index[0]},{index[1]},{row.values[0]}\n")
                f_hotpixel_mask.write(f"{index[0]},{index[1]}\n")

            f_hotpixel_count.close()
            f_hotpixel_mask.close()

            # only scan the first few 30 thresholds
            if ths > 1170: break

        
class Measurement():
    def __init__(self, name="", threshold=0, n_cols=128, n_rows=128, data=None, value='count', mask=None):
        self.name = name
        self.threshold = threshold
        self.value = value
        self.n_cols = n_cols
        self.n_rows = n_rows

        # numpy 2D arrays with n_cols x c_rows entries with value
        self.map = np.zeros((self.n_cols, self.n_rows))
        self.map_single = np.zeros((self.n_cols, self.n_rows))

        if data is not None: self.load(data, value, mask)


    def load(self, data, value='count', mask=None):
        # copy data to local member variable of dataframe
        self.map = cast_df_to_array(data, value, self.n_cols, self.n_rows)
         # if mask map is provided, remove masked pixels (mask: column, row)
        if mask is not None:
            for i in mask: self.map[i[0]][i[1]] = 0


    def find_single_pixel(self):
        from itertools import product
        single_pixel_counts = 0
        single_pixel_counts_even = 0
        single_pixel_counts_odd = 0

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
                single_pixel_counts += self.map[i][j]
                if (i%2==0): single_pixel_counts_even += self.map[i][j]
                else: single_pixel_counts_odd += self.map[i][j]

        return single_pixel_counts, single_pixel_counts_even, single_pixel_counts_odd

    def find_total_pixel(self):
        total_pixel_counts = np.sum(self.map)

        select_even = np.zeros((self.n_cols, self.n_rows), dtype=int)
        select_even[0::2,:] = 1
        total_pixel_counts_even = np.sum(self.map, where=select_even.astype(bool))

        select_odd = np.zeros((self.n_cols, self.n_rows), dtype=int)
        select_odd[1::2,:] = 1
        total_pixel_counts_odd = np.sum(self.map, where=select_odd.astype(bool))
        
        return total_pixel_counts, total_pixel_counts_even, total_pixel_counts_odd


    def plot(self, output_folder):
        plot_map(self.map, self.value, join(output_folder, f"map_{self.name}_{self.threshold}"))
        plot_map(self.map_single, 'single pixel', join(output_folder, f"map_{self.name}_{self.threshold}_single_pixel.png"))
