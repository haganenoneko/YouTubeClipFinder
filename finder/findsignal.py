import math
import logging
import audiofile
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from typing import Tuple, Union
from scipy.signal import correlate, correlation_lags

from common import InvalidArgumentException

# ---------------------------------------------------------------------------- #
#        Find endpoints of a query signal inside a larger source signal        #
# ---------------------------------------------------------------------------- #


def read_audio_data(
        name: str,
        dir: Union[Path, str],
        ext: str = "m4a",
        down_factor: int = 100) -> Tuple[np.ndarray, int]:
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

    > Reading... ./data/oHP7u5zHYSY.m4a
    > (17642,) 441
    > Reading... ./data/oHP7u5zHYSY_2.m4a
    > (17642,) 441
    ```
    """
    dataFiles = list(dir.glob(f"{name}*{ext}"))
    if not dataFiles:
        raise FileNotFoundError(
            f"No files found in {dir} with pattern {name}*{ext}")

    if len(dataFiles) < 1:
        raise FileNotFoundError(f"{dir}/{name}{ext}")

    for data in dataFiles:
        print(f"Reading... {str(data):<8}")
        signal, sampling_rate = audiofile.read(data)
        if down_factor > 0:
            signal = signal[0, ::down_factor]
            sampling_rate = int(sampling_rate / down_factor)
        else:
            signal = signal[0, :]

        yield signal, sampling_rate


class FindSignal:
    def __init__(
            self,
            data: np.ndarray,
            query: np.ndarray,
            rate: int,
            how_argmax='whole',
            how_t0='query') -> None:
        """Find start and stop times of a `query` signal inside a `data` signal

        Args:
            data (np.ndarray): data signal
            query (np.ndarray): query signal
            rate (int): sampling rate, number of data points per second.
            how_argmax (str, optional): how to compute the `argmax` of cross-correlated `data` and `query`. Defaults to 'whole'.

            * `whole` : `argmax` over the entire cross-correlation array
            * `inds` : pre-computes indices where cross-correlation is above 0.5, then finds the `argmax` over these

            how_t0 (str, optional): how to compute start time. Defaults to 'query'.

            * `query`: `stop time - query duration = start time`. 
            * `lags` : the start time is the `argmax` of cross-correlation lags.

            plot (bool, optional): whether to plot results. Defaults to False.

        Returns:
            Tuple[int, int]: start and stop times
        """

        if how_t0 not in ['query', 'lags']:
            raise InvalidArgumentException(
                'how_t0', how_t0, ['query', 'lags']
            )

        if how_argmax not in ['whole', 'inds']:
            raise InvalidArgumentException(
                'how_argmax', how_argmax, ['whole', 'inds']
            )

        self.data = data
        self.query = query
        self.rate = rate

        self._how_argmax = how_argmax
        self._how_t0 = how_t0

    def parse_times(self, corr: np.ndarray) -> Tuple[int, int]:

        if self._how_argmax == 'inds':
            inds = np.where(corr > 0.5)[0]
            t1 = inds[np.argmax(corr[inds])]
        else:
            t1 = np.argmax(corr)

        t1 = math.ceil(t1/self.rate)

        if self._how_t0 == 'query':
            dt = int(self.query.shape[0] / self.rate)
            t0 = t1 - dt
        else:
            lags = correlation_lags(
                self.data.size,
                self.query.size
            )
            t0 = int(lags[t1])

        return (t0, t1)

    def _plot_found_signal(
            self,
            corr: np.ndarray,
            ts: Tuple[int, int],
            msg: str) -> None:

        _, ax = plt.subplots(figsize=(5, 3), constrained_layout=True)
        ax.plot(
            np.arange(corr.shape[0]) / self.rate,
            corr, lw=0.5
        )
        ax.axvspan(ts[0], ts[1], alpha=0.4, c='lime', label=msg)
        ax.legend(loc='upper left', bbox_to_anchor=[0.9, 1.1])
        plt.show()

    def findsignal(self, plot=False) -> Tuple[tuple, float]:

        corr = correlate(self.data, self.query, method='fft')
        peak = np.max(corr)

        if corr[corr > 0.5].shape[0] < 1:
            t1 = np.argmax(corr)/self.rate
            logging.info(f"Peak: ({t1:.1f}, {peak:.1e})")
            return None, peak

        t0, t1 = self.parse_times(corr)
        msg = f"Corr: {peak:<10} Start: {t0:<10} Stop: {t1:<10}"
        logging.info(msg)

        if plot:
            self._plot_found_signal(corr, (t0, t1), msg)

        return (t0, t1), peak
