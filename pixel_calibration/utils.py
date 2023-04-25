import numpy as np
import pandas as pd

def cast_df_to_array(data, value='count', n_cols=128, n_rows=128):
    # convert data from measurement to a map of the sensor
    # if there are multiple measurements for a given threshold, sum them up
    table = data.groupby(['col', 'row'])[value].sum().to_frame()
    # the measurement data is only recorded if there are counts
    # therefore, padding of empty rows and columns is applied to the map
    new_index = pd.MultiIndex.from_product([range(n_cols), range(n_rows)], names=('col', 'row'))
    return table.reindex(new_index).fillna(0).astype(np.int32).to_numpy().reshape(n_cols,n_rows)


def find_hottest_pixel(data, value='count', hottest_percent=0.01):
    # determine (1 - hottest_percent) of hottest pixels
    cut_value = data[value].quantile(q=(1. - hottest_percent))
    df_hottest = data[data[value] > cut_value].sort_values(by=[value], ascending=False)
    return df_hottest, cut_value
