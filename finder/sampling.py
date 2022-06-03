import math
import time
import yt_dlp
import logging
import numpy as np
from random import shuffle
import matplotlib.pyplot as plt
from typing import List, Tuple, Dict, Any

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


def get_bins(
        duration: int,
        nbins: int = 10,
        binorder: str = 'mirrored',
        min_binwidth: int = 30,
        max_binwidth: int = 120,
        clip_edges: int = 60,
        plot=False) -> np.ndarray:
    """Get bins containing start and stop times that cover the given duration

    Args:
        duration (int): duration in seconds
        nbins (int, optional): initial number of bins. Defaults to 10.
        min_binwidth (int, optional): minimum bin duration. Defaults to 30.
        max_binwidth (int, optional): maximum bin duration. Defaults to 120.
        clip_edges (int, optional): number of seconds to clip from the edges. Defaults to 60 (1 minute).
        plot (bool, optional): whether to plot bin order and duration. Defaults to False.

    Returns:
        np.ndarray: 2D array of `[start times, end times]` 
    """

    if binorder not in ['linear', 'mirrored', 'random']:
        raise InvalidArgumentException(
            'binorder', binorder,
            ['linear', 'mirrored', 'random']
        )

    bins: List[List[int]] = []

    if clip_edges > 0:
        duration -= 2*clip_edges

    binwidth = math.floor(duration / nbins)

    if binwidth < min_binwidth:
        binwidth = min_binwidth
    elif binwidth > max_binwidth:
        binwidth = max_binwidth

    nbins = math.floor(duration / binwidth)

    logging.info(
        f"nbins: {nbins:<8} binwidth: {binwidth:>8} edge clip: {clip_edges:>8}"
    )

    bininds = np.arange(1, nbins+1)
    rbinedges = bininds * binwidth
    ind0 = int(np.median(bininds))

    if plot:
        _, ax = plt.subplots()

        text_kw = dict(
            fontdict=dict(ha='center', va='bottom'),
            transform=ax.transData
        )

    for i in range(1, nbins+1):

        try:
            edges = get_bin_edges(
                i, ind0, nbins, rbinedges, binorder=binorder
            )
        except ValueError:
            break

        if edges is None:
            continue

        bins.append(edges)

        if not plot:
            continue

        ax.plot(edges, [i]*2, )
        ax.text(sum(edges)/2, i, str(i), **text_kw)

    if binorder == 'mirrored':
        bins.append((1, rbinedges[0]))
    else:
        bins.insert(0, (1, rbinedges[0]))

    if binorder == 'random':
        shuffle(bins)

    if plot:
        plt.show()

    return np.array(bins) + clip_edges


def bins2str(bin_arr: np.ndarray) -> np.ndarray:
    print(f"Min Time: {np.min(bin_arr):<8} Max Time: {np.max(bin_arr):<8}")
    return vec_seconds2str(bin_arr)
