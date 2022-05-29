import math
import time 
import yt_dlp
import logging
import numpy as np 
import matplotlib.pyplot as plt 
from typing import List, Tuple

def seconds2str(secs: int, fmt=r"%H:%M:%S") -> str:
    return time.strftime(fmt, time.gmtime(secs))

vec_seconds2str = np.vectorize(seconds2str)

def get_video_duration(
    url: str) -> Tuple[int, str]:
    """Get duration of a YouTube video

    Args:
        url (str): video URL

    Returns:
        Tuple[int, str]: duration in seconds, and as a HH:MM:SS string
    """
    meta: dict = yt_dlp.YoutubeDL().extract_info(
        url, download=False
    )
    seconds = meta['duration']

    return seconds, seconds2str(seconds)

def get_bins(
    duration: int, 
    nbins: int=10,
    binorder: str='mirrored',
    min_binwidth: int=30,
    max_binwidth: int=120, 
    plot=False) -> List[List[int]]:
    """Get bins containing start and stop times that cover the given duration

    Args:
        duration (int): duration in seconds
        nbins (int, optional): initial number of bins. Defaults to 10.
        min_binwidth (int, optional): minimum bin duration. Defaults to 30.
        max_binwidth (int, optional): maximum bin duration. Defaults to 120.
        plot (bool, optional): whether to plot bin order and duration. Defaults to False.

    Returns:
        List[List[int, int]]: list of bins
    """

    if binorder not in ['linear', 'mirrored']:
        raise ValueError(f"`binorder` must be one of 'linear' or 'mirrored', not {binorder}")

    bins: List[List[int]] = [] 
    binwidth = math.floor(duration / nbins)
    
    if binwidth < min_binwidth:
        binwidth = min_binwidth 
    elif binwidth > max_binwidth:
        binwidth = max_binwidth

    nbins = math.floor(duration / binwidth)

    logging.info(
        f"nbins: {nbins:<8} binwidth: {binwidth:>8}"
    )

    bininds = np.arange(1, nbins+1)
    rbinedges = bininds * binwidth
    ind0 = int(np.median(bininds))

    if plot:
        _, ax = plt.subplots()

    for i in range(1, nbins+1):
        
        if binorder == 'mirrored':
            ind = (i // 2) * (-1)**(i % 2)
            ind += ind0 
        else:
            ind = i 

        if ind >= nbins: continue 

        left, right = rbinedges[ind-1] + 1, rbinedges[ind]
        
        if left > right: break         

        bins.append([left, right])
        
        if not plot: 
            continue 

        ax.plot(
            [left, right],
            [i]*2, 
        )
        ax.text(
            (left+right)/2, i, str(i), 
            fontdict=dict(ha='center', va='bottom'),
            transform=ax.transData
        )

    if binorder == 'linear':
        bins.insert(0, [1, rbinedges[0]])
    else:
        bins.append([1, rbinedges[0]])

    if plot:
        plt.show()
    
    return bins 

def bins2str(bins: List[List[int]]) -> np.ndarray:
    bin_arr = np.array(bins)
    print(f"Min Time: {np.min(bin_arr):<8} Max Time: {np.max(bin_arr):<8}")
    return vec_seconds2str(bin_arr)

# dur_int, dur_str = get_video_duration(
#     'https://youtu.be/oHP7u5zHYSY')
