import validators
import time
import logging
import numpy as np
from pathlib import Path
from subprocess import Popen

import matplotlib.pyplot as plt

from datetime import datetime, timedelta

from types import NoneType
from typing import List, Tuple, Union

from finder import sampling
from finder.download import get_cmd, run_cmd
from finder.common import str2hms, create_figure
from finder.findsignal import FindSignal, read_audio_data

# ---------------------------------------------------------------------------- #
#                   Download and compare clips by their audio                  #
# ---------------------------------------------------------------------------- #

DATADIR = Path.cwd() / 'data'

def create_logger(name: str) -> None:
    logging.basicConfig(
        filename=Path.cwd() / f'{name}.log',
        encoding='utf-8',
        level=logging.INFO
    )

# -------------------------------- Main class -------------------------------- #


class Finder:
    def __init__(
            self,
            source: str,
            query: Union[str, np.ndarray],
            logname: str = None,
            **query_kwargs) -> None:

        self.url = source
        self.query = self.get_query(
            query, **query_kwargs)
        
        if logname is None:
            create_logger(query)
        else:
            create_logger(logname)

    def get_query(
            self,
            query: Union[str, np.ndarray],
            **query_kwargs) -> np.ndarray:

        if isinstance(query, np.ndarray):
            return query
        if not isinstance(query, str):
            raise TypeError(
                f"`query` must be of type `np.ndarray` or `str`, not {type(query)}"
            )

        if Path(query).is_file():
            query = Path(query)
            return next(read_audio_data(
                query.stem, query.parent, query.suffix
            ))[0]
        else:
            raise FileNotFoundError(query)

        cmd, fn = get_cmd(query, **query_kwargs)

        try:
            proc = run_cmd(cmd, concurrent=False, shell=True)
        except KeyboardInterrupt:
            proc.kill()

        fn = Path(fn)
        if fn.is_file():
            query, _ = next(read_audio_data(
                fn.stem, fn.parent, fn.suffix
            ))
            logging.info(
                f"Query downloaded from {query} to {str(fn)}"
            )
            return query
        else:
            raise FileNotFoundError(f"Query: {str(fn):>8}")

    def get_bins(
            self,
            nbins: int = 10,
            binorder: str = 'mirrored',
            min_binwidth: int = 30,
            max_binwidth: int = 120,
            clip_edges: int = 60, **binkwargs) -> None:

        dur_int, _ = sampling.get_video_duration(self.url)

        bins_int = sampling.get_bins(
            dur_int,
            nbins=nbins,
            binorder=binorder,
            min_binwidth=min_binwidth,
            max_binwidth=max_binwidth,
            clip_edges=clip_edges,
            **binkwargs
        )

        self._bins_str = sampling.bins2str(bins_int)
        logging.debug(self._bins_str)

    def run_ytdl(
            self,
            start_bin: int,
            max_dl: int,
            fmt: int,
            wait: bool,
            loc: Path,
            max_wait_time: int) -> None:

        cmd_kw = dict(fmt=fmt, loc=loc)

        self._fnames: List[Path] = []
        self._running: List[Union[Popen, NoneType]] = []

        for i, bin in enumerate(self._bins_str[start_bin:]):
            start, stop = bin

            cmd, fn = get_cmd(
                self.url, start, stop,
                suffix=f"_{i+start_bin}",
                **cmd_kw
            )

            if Path(fn).is_file():
                proc = None
            else:
                proc = run_cmd(cmd, shell=True)

            self._running.append(proc)
            self._fnames.append(Path(fn))

            if i + 1 >= max_dl:
                break

        if isinstance(self._running[-1], NoneType):
            logging.info("All bins already exist on the file system.")
            return

        if wait:
            while not self._fnames[0].is_file():
                time.sleep(max_wait_time/10)

    def find_times(
            self,
            fname: Path) -> Union[None, Tuple[int, int]]:

        data, rate = next(read_audio_data(
            fname.stem,
            fname.parent,
            fname.suffix,
        ))

        return FindSignal(
            data, self.query, rate
        ).findsignal()

    def _compare_signals(
            self,
            i: int,
            fname: Path,
            max_wait_time: int,
            wait: bool) -> Tuple[Union[tuple, NoneType], float]:

        if not fname.is_file():
            if isinstance(self._running[i], NoneType):
                raise FileNotFoundError(fname)
            elif wait:
                logging.info(f"Waiting for {max_wait_time} seconds.")
                time.sleep(max_wait_time)

        if not fname.is_file():
            proc = self._running[i]
            proc.kill()
            logging.error(proc.communicate()[1])

        return self.find_times(fname)

    def _midtime(self, ind: int, delta: timedelta = None) -> datetime:

        bin = self._bins_str[ind, :]
        if isinstance(bin[0], np.ndarray):
            bin = bin[0]

        a, b = [str2hms(s) for s in bin]

        if delta is None:
            return a + (b-a)/2
        else:
            return a + delta

    @staticmethod
    def _plot_peak_corr(peaks: np.ndarray, title: str=None, save_path=None):
        peaks = np.array(peaks)

        _, ax = create_figure()
        kw = dict(ls='none', marker='o', ms=4)

        xvals = peaks[:, 0]
        yvals = peaks[:, 1].astype(np.float64)
        mask = yvals > 0.5

        ax.plot(xvals[mask], yvals[mask], c='r', label=">0.5", **kw)
        ax.plot(xvals[~mask], yvals[~mask], c='b', alpha=0.5, **kw)

        indmax = np.argmax(yvals)
        ax.plot(
            xvals[indmax], yvals[indmax], 
            marker='o', mec='purple', mew=2, 
            ms=16, mfc='none', ls='none'
        )
        print(xvals[indmax], yvals[indmax])

        if title:
            ax.set_title(title)
        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
            print(f"Figure saved at {save_path}")

        plt.show()

    def run(
            self,
            start_bin: int = 0,
            max_dl: int = 5,
            wait=True,
            fmt=139,
            keepfiles=True,
            loc=DATADIR,
            max_wait_time: int = 120) -> List[Tuple[int, int]]:

        # download clips from source
        self.run_ytdl(
            start_bin=start_bin,
            max_dl=max_dl,
            wait=wait,
            fmt=fmt,
            loc=loc,
            max_wait_time=max_wait_time
        )

        # if download was not successful
        if not self._fnames[0].is_file():
            raise FileNotFoundError(str(self._fnames))

        candidates: List[Tuple[int, int]] = []
        peak_corr: List[float] = []

        bins_str = self._bins_str
        delta = self._midtime(0) - self._midtime(1)

        logging.info("Comparing query and source audio...")

        for i, fname in enumerate(self._fnames):
            k = i + start_bin
            result, peak = self._compare_signals(
                i, fname,
                max_wait_time=max_wait_time,
                wait=wait
            )

            if result is None:
                logging.info(f"Not in {bins_str[k]}")
                peak_corr.append([
                    self._midtime(k),
                    peak
                ])
            else:
                logging.info(bins_str[k])
                candidates.append(result)

                peak_corr.append([
                    self._midtime(k),
                    peak
                ])

            if not keepfiles:
                fname.unlink()

        self._plot_peak_corr(peak_corr)
        return candidates

