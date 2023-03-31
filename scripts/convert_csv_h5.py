import numpy as np
import pandas as pd

filename = 'data/test.csv'
dtypes = {'ths': int, 'col': int, 'row': int, 'hit': int, 'count': int}
columns = ['ths', 'col', 'row', 'hit', 'count']

iter_csv = pd.read_csv(
    filename,
    iterator=True,
    comment='#',
    index_col='ths',
    names=columns,
    dtype=dtypes,
    encoding='utf-8',
    chunksize=1_000)

for chunk in iter_csv:
    chunk.to_hdf(
        filename.replace('.csv', '.h5'),
        'data',
        format='table',
        append=True
    )
