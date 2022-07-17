from ast import Assert
import math
import time
import yt_dlp
import logging
import numpy as np
from random import shuffle
import matplotlib.pyplot as plt
from typing import List, Tuple, Dict, Any, Union

from finder.common import InvalidArgumentException, seconds2str, vec_seconds2str

# ---------------------------------------------------------------------------- #
#         Functions that discretize a video into bins of equal duration        #
# ---------------------------------------------------------------------------- #


def get_video_duration(
        url: str) -> Tuple[int, str]:
    """Get duration of a YouTube video

    Args:
        url (str): video URL

    Returns:
        Tuple[int, str]: duration in seconds, and as a HH:MM:SS string
    """
    meta: Dict[str, Any] = yt_dlp.YoutubeDL().extract_info(
        url, download=False
    )
    seconds = meta['duration']

    return seconds, seconds2str(seconds)


def get_bin_edges(
        i: int,
        start: int,
        nbins: int,
        rbinedges: List[int],
        binorder: str = 'mirrored') -> Tuple[int, int]:

    if binorder == 'mirrored':
        ind = (i // 2) * (-1)**(i % 2)
        ind += start
    else:
        ind = i

    if ind >= nbins:
        return None

    left, right = rbinedges[ind-1] + 1, rbinedges[ind]

    if left > right:
        raise ValueError
    else:
        return left, right

def _plotbins(bins: List[List[int]]) -> None:
    _, ax = plt.subplots()

    text_kw = dict(
        fontdict=dict(ha='center', va='bottom'),
        transform=ax.transData
    )

    for i, bin in enumerate(bins):
        ax.plot(bin, [i]*2, )
        ax.text(sum(bin)/2, i, str(i), **text_kw)
    
    plt.show()

def _randomize_bins(
    bins: List[List[int]],
    inds: List[int], 
    nbins: int) -> List[List[int]]:
    
    shuffle(inds)
    logging.info("Shuffled bin indices:\n", inds, '\n')
    return [bins[i] for i in inds]

def _skip_bins(
    bins: List[List[int]], 
    inds: List[int],
    nbins: int, 
    skipsize: int) -> List[List[int]]:

    skipped: List[int] = [] 
    for i in range(skipsize):
        skipped.extend(inds[i:nbins:skipsize])
    
    if len(skipped) == nbins:
        skipped.extend(
            [i for i in range(nbins) if i not in skipped]
        )
    
    out = [bins[i] for i in skipped]
    try:
        assert len(out) == nbins 
    except AssertionError:
        raise ValueError(
            f"Number of bins do not match before ({nbins}) and after ({len(out)} applying skip size {skipsize}."
        )

    return out 

def get_bins(
        duration: int,
        nbins: int = 10,
        binorder: Union[str, List[int]] = 'mirrored',
        skipsize: int = 0,
        min_binwidth: int = 30,
        max_binwidth: int = 120,
        start_delta: int = 0,
        plot=False) -> np.ndarray:
    """Get bins containing start and stop times that cover the given duration

    Args:
        duration (int): duration in seconds
        nbins (int, optional): initial number of bins. Defaults to 10.
        binorder (Union[str, List[int], optional): bin order, string or list of indices. Defaults to 'mirrored.' 
        skipsize (int, optional): number of bins to skip between `i` and `i+1`-th elements of the final sequence of bins. Defaults to 0.
        min_binwidth (int, optional): minimum bin duration. Defaults to 30.
        max_binwidth (int, optional): maximum bin duration. Defaults to 120.
        start_delta (int, optional): offset for beginning. Defaults to 0.
        plot (bool, optional): whether to plot bin order and duration. Defaults to False.

    Returns:
        np.ndarray: 2D array of `[start times, end times]` 
    """

    if (not isinstance(binorder, list)) and\
        (binorder not in ['linear', 'mirrored', 'random']):
        raise InvalidArgumentException(
            'binorder', binorder,
            ['linear', 'mirrored', 'random']
        )

    bins: List[List[int]] = []
    binwidth = math.floor(duration / nbins)

    if binwidth < min_binwidth:
        binwidth = min_binwidth
    elif binwidth > max_binwidth:
        binwidth = max_binwidth

    nbins = math.floor(duration / binwidth)

    print(
        f"""
        nbins: {nbins:<8} binwidth: {binwidth:>8} start offset: {start_delta:>8}
        """
    )

    bininds = np.arange(1, nbins+1)
    rbinedges = bininds * binwidth
    ind0 = int(np.median(bininds))

    for i in range(1, nbins+1):
        try:
            edges = get_bin_edges(
                i, ind0, nbins, rbinedges, binorder=binorder
            )
        except ValueError:
            break

        if edges is not None:
            bins.append(edges)
            
    if binorder == 'mirrored':
        bins.append((1, rbinedges[0]))
    else:
        bins.insert(0, (1, rbinedges[0]))

    if binorder == 'random' or skipsize > 0:
        inds = list(range(len(bins)))
        if binorder == 'random':
            bins = _randomize_bins(
                bins, inds, nbins)
        elif skipsize > 0:
            bins = _skip_bins(
                bins, inds, nbins, skipsize)
            
    if plot:
        _plotbins(bins)

    # N x 2 array
    return np.array(bins) + start_delta 

def bins2str(bin_arr: np.ndarray) -> np.ndarray:
    print(f"Min Time: {np.min(bin_arr[:,0]):<8} Max Time: {np.max(bin_arr[:,1]):<8}")
    return vec_seconds2str(bin_arr)
