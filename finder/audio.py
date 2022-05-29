import enum
import numpy as np 
import audiofile
from pathlib import Path 
from typing import List 
import logging
import matplotlib.pyplot as plt 

data = list( (Path.cwd() / 'data').glob("*.m4a") )[0]
signal, sampling_rate = audiofile.read(data)

down_factor = 100
signal = signal[0, ::down_factor]
sampling_rate = int(sampling_rate/down_factor)

ts_true = np.array([15, 22], dtype=int) * sampling_rate
query = signal[ts_true[0]-1:ts_true[1]]

bins = 2
new_signal = np.reshape(signal, [-1, bins])
print(new_signal.shape)

d = new_signal.shape[0] - query.shape[0]

_, ax = plt.subplots(bins, 1, figsize=(8, 5), constrained_layout=True)
sigma = np.std(new_signal, axis=0)

xvals = None 

for i in range(bins):
    if d >= 0:
        res = new_signal[:query.shape[0],i] - query
    elif d < 0:
        res = new_signal[:,i] - query[:new_signal.shape[1]]
    
    res = np.square(res) / sigma[i] 
    if xvals is None:
        xvals = np.arange(0, res.shape[0])
    else:
        xvals += xvals[-1]

    ax[i].plot(
        xvals, res, color='b', lw=0.5, alpha=0.5
    )
plt.show()

