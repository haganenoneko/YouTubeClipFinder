from email.mime import audio
import math 
import logging
import audiofile
import numpy as np 
from pathlib import Path 
import matplotlib.pyplot as plt 
from typing import Tuple, Union  
from scipy.signal import correlate

def read_audio_data(
    name: str, 
    dir: Union[Path, str], 
    ext: str="m4a",
    down_factor: int=100) -> Tuple[np.ndarray, int]:
    """Read audio files as numpy ndarrays

    Args:
        name (str): prefix, equivalent to `.stem` of a `PurePath`
        dir (Union[Path, str]): directory containing audio files
        ext (str, optional): extension. Defaults to ".m4a".
        down_factor (int, optional): downsampling factor. Defaults to 100.

    Raises:
        FileNotFoundError: raised if no files matching `dir/name*.ext` are found

    Returns:
        Tuple[np.ndarray, int]: amplitudes and sampling rates for each file in a generator
    
    Example:
    Assume there are files `./data/oHP7u5zHYSY_%d.m4a`. These can will be parsed as:
    ```python 
    files = read_audio_data(
        "oHP7u5zHYSY", "Path.cwd() / 'data'",
        ext='m4a', down_factor=100
    )
    for f in files:
        signal, rate = f 
        print(signal.shape, rate)
    
    >>> Reading... C:\Users\delbe\Documents\CodeRepositories\Miscellaneous\YouTubeClipFinder\data\oHP7u5zHYSY.m4a
    >>> (17642,) 441
    >>> Reading... C:\Users\delbe\Documents\CodeRepositories\Miscellaneous\YouTubeClipFinder\data\oHP7u5zHYSY_2.m4a
    >>> (17642,) 441
    ```
    """
    dataFiles = list(dir.glob(f"{name}*.{ext}"))
    if not dataFiles:
        raise FileNotFoundError(f"No files found in {dir} with pattern {name}*.{ext}")
    
    for data in dataFiles:
        print(f"Reading... {str(data):<8}")
        signal, sampling_rate = audiofile.read(data)
        if down_factor > 0:
            signal = signal[0, ::down_factor]
            sampling_rate = int(sampling_rate / down_factor)
        else:
            signal = signal[0, :]
        
        yield signal, sampling_rate



def findsignal(
    data: np.ndarray, 
    query: np.ndarray, 
    rate: int, 
    how='whole', 
    plot=False) -> Tuple[int, int]:
    """Find start and stop times of a `query` signal inside a `data` signal

    Args:
        data (np.ndarray): data signal
        query (np.ndarray): query signal
        rate (int): sampling rate, number of data points per second.
        how (str, optional): how to compute the `argmax` of cross-correlated `data` and `query`. Defaults to 'whole'.
        plot (bool, optional): whether to plot results. Defaults to False.

    Returns:
        Tuple[int, int]: start and stop times
    """    
    
    corr = correlate(data, query, method='fft')

    if how == 'inds':
        inds = np.where(corr > 0.5)[0]
        t1 = inds[np.argmax(corr[inds])] 
    else:
        t1 = np.argmax(corr)
    
    t1 = math.ceil(t1/rate)
    dt = int(query.shape[0] / rate)
    t0 = t1 - dt 

    msg = f"Start: {t0:>10} Stop: {t1:<10}"
    logging.info(msg)

    if plot:
        _, ax = plt.subplots(figsize=(5, 3), constrained_layout=True)
        ax.plot(
            np.arange(corr.shape[0]) / rate,
            corr, lw=0.5
        )
        ax.axvspan(
            t0, t1, alpha=0.4, c='lime', label=msg
        )
        ax.legend(loc='upper left', bbox_to_anchor=[0.9, 1.1])
        plt.show()
    
    return t0, t1
