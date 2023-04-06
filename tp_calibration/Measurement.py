import numpy as np
import pandas as pd
import dask.dataframe as dd
import matplotlib.pyplot as plt
import mplhep as hep

from hist import Hist
from tqdm import tqdm
from os.path import join

class Calibration():
    def __init__(self, name="", file="", n_cols=128, n_rows=128, measure_tot=False):
        self.name=name,
        self.file = file

        self.n_cols = n_cols
        self.n_rows = n_rows
        self.measure_tot = measure_tot

        # measurements, indiced by threshold
        self.measurements = {}

        self.hist_count = Hist.new.Reg(2299, 0, 2299, name="ths").Double()
        self.hist_count_even = Hist.new.Reg(2299, 0, 2299, name="ths").Double()
        self.hist_count_odd = Hist.new.Reg(2299, 0, 2299, name="ths").Double()

    def read_csv(self, use_dask=False):
        columns = ['ths', 'col', 'row', 'hit', 'count']
        if self.measure_tot: columns = ['ths', 'col', 'row', 'hit', 'tot', 'count']
        def _daskwrapper(obj, use_dask):
            if use_dask: return obj.compute()
            return obj
        if use_dask:
            if self.file.endswith('.csv'):
                df = dd.read_csv(self.file, comment='#', names=columns, blocksize=25e6).set_index('ths')
            else:
                raise RuntimeError("Unknown input file format.")
        else:
            if self.file.endswith('.csv'):
                df = pd.read_csv(self.file, comment='#', names=columns, index_col='ths')
            elif self.file.endswith('.h5'):
                df = pd.read_hdf(self.file, columns=columns, index_col='ths')
            else:
                raise RuntimeError("Unknown input file format.")

        # sort full dataframe in individual measurements per threshold
        thresholds = _daskwrapper(df.index.unique(), use_dask)
        for ths in tqdm(thresholds):
            data = _daskwrapper(df.loc[[ths],["col", "row", "count"]], use_dask)
            self.measurements[ths] = Measurement(f"timepix2_ths_calib_{self.name}", ths, self.n_cols, self.n_rows, data, 'count')


    def plot(self):
        # plot histograms
        def _plot_hist(data, title, name):
            plt.style.use(hep.style.ROOT)
            fig, ax = plt.subplots()
            hep.histplot(data, ax=ax)
            ax.set_title(title)
            ax.set_xlabel('Threshold [a.u.]')
            ax.set_ylabel('Single pixel counts [a.u.]')
            fig.savefig(join("plots", f"hist_{name}.png"))
            plt.close()

        _plot_hist(self.hist_count.project("ths"), '', f'calib_{self.name}')
        _plot_hist(self.hist_count_even.project("ths"), 'even', f'calib_{self.name}_even')
        _plot_hist(self.hist_count_odd.project("ths"), 'odd', f'calib_{self.name}_odd')

        # plot maps of measurements
        for ths, m in self.measurements.items():
            m.plot()

    def evaluate(self):
        with open(f'single_pixel_counts_{self.name}.csv', 'w') as outfile:
            outfile.write("threshold,counts,counts_even,counts_odd\n")
            for ths, m in tqdm(self.measurements.items()):
                single_pixel_counts, single_pixel_counts_even, single_pixel_counts_odd = m.find_single_pixel()
                thresholds = [ths for i in single_pixel_counts]
                self.hist_count.fill(thresholds, weight=single_pixel_counts)
                self.hist_count_even.fill(thresholds, weight=single_pixel_counts_even)
                self.hist_count_odd.fill(thresholds, weight=single_pixel_counts_odd)
                outfile.write(f"{ths},{np.sum(single_pixel_counts)},{np.sum(single_pixel_counts_even)},{np.sum(single_pixel_counts_odd)}\n")


class Measurement():
    def __init__(self, name="", threshold=0, n_cols=128, n_rows=128, data=None, value='count'):
        self.name = name
        self.threshold = threshold
        self.value = value
        self.n_cols = n_cols
        self.n_rows = n_rows

        self.map = np.zeros((self.n_cols, self.n_rows))
        self.map_single = np.zeros((self.n_cols, self.n_rows))

        if data is not None: self.load(data, value)
       

    def load(self, data, value='count'):
        table = pd.pivot_table(data, values=value, index='row', columns='col', aggfunc='sum')
        for i, r in table.iterrows():
            self.map[r.index.to_numpy()[0]][i] += np.nan_to_num(r.to_numpy()[0])
        del(table)


    def find_single_pixel(self):
        from itertools import product
        single_pixel_counts = []
        single_pixel_counts_even = []
        single_pixel_counts_odd = []

        for i, j in product(range(self.n_cols), range(self.n_rows)):
            # only consider pixels which had a count > 0
            single_pixel = (self.map[i][j] != 0)
            # scan for neighouring pixels
            for ii, jj in product(range(i-1, i+1), range(j-1, j+1)):
                if (ii==i and jj==j): continue
                if (ii < 0 or jj < 0 or ii > self.n_cols or jj > self.n_rows): continue
                # if neighbour exist, this is not a single pixel
                if (self.map[ii][jj] != 0): single_pixel = False
            self.map_single[i][j] = int(single_pixel)

            # if single pixel was found, add count to list
            # so that it can be filled in calibration histogram
            # for given threshold
            if single_pixel:
                single_pixel_counts.append(self.map[i][j])
                if (i%2==0): single_pixel_counts_even.append(self.map[i][j])
                else: single_pixel_counts_odd.append(self.map[i][j])

        return single_pixel_counts, single_pixel_counts_even, single_pixel_counts_odd

    def plot(self):
        def _plot_map(data, value, name):
            plt.style.use(hep.style.ROOT)
            fig, ax = plt.subplots()
            hep.hist2dplot(data, ax=ax)
            ax.set_title(value)
            ax.set_xlabel('Columns')
            ax.set_ylabel('Rows')
            fig.savefig(join("plots", f"map_{name}.png"))
            plt.close()

        _plot_map(self.map, self.value, f"{self.name}_{self.threshold}")
        _plot_map(self.map_single, 'single pixel', f"{self.name}_{self.threshold}_single_pixel")


calib_ref = Calibration('reference', 'data/cal.csv')
calib_ref.read_csv()
calib_ref.evaluate()
calib_ref.plot()

calib_source_fe = Calibration('iron', 'data/iron.csv')
calib_source_fe.read_csv()
calib_source_fe.evaluate()
calib_source_fe.plot()