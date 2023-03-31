import numpy as np
import pandas as pd
import dask.dataframe as dd
import matplotlib.pyplot as plt
import mplhep as hep

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

    def read_csv(self, use_dask=False):
        columns = ['ths', 'col', 'row', 'hit', 'count']
        if self.measure_tot: columns = ['ths', 'col', 'row', 'hit', 'tot', 'count']
        if use_dask:
            if self.file.endswith('.csv'):
                df = dd.read_csv(self.file, comment='#', names=columns, blocksize=5_000).set_index('ths')
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
        thresholds = df.index.unique().values
        for ths in thresholds:
            data = df.loc[[ths],["col", "row", "count"]]
            self.measurements[ths] = MeasurementSeries(ths, self.n_cols, self.n_rows, data, 'count')

    def plot(self):
        for ths, m in self.measurements.items():
            m.plot()

    def evaluate(self):
        for ths, m in self.measurements.items():
            m.evaluate()


class MeasurementSeries():
    def __init__(self, threshold=0., n_cols=128, n_rows=128, data=None, value='count'):
        self.n_cols = n_cols
        self.n_rows = n_rows

        # measurements
        self.threshold = threshold
        self.n_measurements = 0
        self.measurements = []
        
        if data is not None: self.load(data, value)
            
    def load(self, data, value='count'):
        m = Measurement(f"{value}_{self.threshold}_0", self.n_cols, self.n_rows, data, value)
        self.measurements.append(m)
        self.n_measurements += 1
       
    def plot(self):
        for m in self.measurements:
            m.plot()

    def evaluate(self):
        for m in self.measurements:
            m.find_single_pixel()


class Measurement():
    def __init__(self, name="", n_cols=128, n_rows=128, data=None, value='count'):
        self.name = name
        self.value = value
        self.n_cols = n_cols
        self.n_rows = n_rows

        self.map = np.zeros((self.n_cols, self.n_rows))
        self.map_single = np.zeros((self.n_cols, self.n_rows))
        if data is not None: self.load(data, value)
       
    def load(self, data, value='count'):
        for i, r in data.iterrows():
            self.map[r['col']][r['row']] += r[value]

    def find_single_pixel(self):
        from itertools import product
        for i, j in product(range(self.n_cols), range(self.n_rows)):
            single_pixel = True
            # scan for neighouring pixels
            for ii, jj in product(range(i-1, i+1), range(j-1, j+1)):
                if (ii==i and jj==j): continue
                if (ii < 0 or jj < 0 or ii > self.n_cols or jj > self.n_rows): continue
                # if neighbour exist, this is not a single pixel
                if (self.map[ii][jj] != 0): single_pixel = False

    def plot(self):
        def _plot(data, value, name):
            plt.style.use(hep.style.ROOT)
            fig, ax = plt.subplots()
            hep.hist2dplot(data, ax=ax)
            ax.set_title(value)
            ax.set_xlabel('Columns')
            ax.set_ylabel('Rows')
            fig.savefig(join("plots", f"plot_{name}.png"))
            plt.close()

        _plot(self.map, self.value, self.name)
        _plot(self.map_single, 'single pixel', self.name + '_single_pixel')


test = Calibration('test', 'data/cal.csv')
test.read_csv()
test.evaluate()
test.plot()
