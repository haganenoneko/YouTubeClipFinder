import validators
import numpy as np 
import logging, time
from pathlib import Path 
from subprocess import Popen
import matplotlib.pyplot as plt 
from datetime import datetime, timedelta

from types import NoneType
from typing import List, Tuple, Union

from findsignal import FindSignal, read_audio_data
from download import get_cmd, run_cmd
import sampling 

DATADIR = Path.cwd() / 'data'

logging.basicConfig(
    filename=Path.cwd() / 'main.log', 
    encoding='utf-8', 
    level=logging.INFO
)

url = r"https://youtu.be/kkni4RCxM0A"

class Finder:
    def __init__(
        self, 
        source: str, 
        query: Union[str, np.ndarray],
        **query_kwargs) -> None:
    
        self.url = source 
        self.query = self.get_query(
            query, **query_kwargs)

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

        cmd, fn = get_cmd(query, **query_kwargs)

        try:
            proc = run_cmd(cmd, concurrent=False, shell=True)
        except KeyboardInterrupt:
            proc.kill()
        
        fn = Path(fn)
        if fn.is_file():
           query, _ = read_audio_data(
               fn.stem, fn.parent, fn.suffix
           )
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
        clip_edges: int = 60) -> None:

        dur_int, _ = sampling.get_video_duration(url)
        
        bins_int = sampling.get_bins(
            dur_int,
            nbins=nbins, 
            binorder=binorder,
            min_binwidth=min_binwidth,
            max_binwidth=max_binwidth,
            clip_edges=clip_edges
        )

        self._bins_str  = sampling.bins2str(bins_int)   
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
        self._running: List[Union[Popen, NoneType]]= []
    
        for i, bin in enumerate(self._bins_str[start_bin:]):
            start, stop = bin 
            
            cmd, fn = get_cmd(
                url, start, stop, 
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

    def _midtime(self, ind: int, delta: timedelta=None) -> datetime:
        
        bin = self._bins_str[ind, :]
        if isinstance(bin[0], np.ndarray):
            bin = bin[0] 

        a, b = [datetime.strptime(t, "%H:%M:%S") for t in bin]

        if delta is None:
            return a + (b-a)/2 
        else:
            return a + delta 

    @staticmethod 
    def process_peak_corr(peaks: np.ndarray):
        peaks = np.array(peaks)
        
        _, ax = plt.subplots(
            figsize=(8, 4), 
            constrained_layout=True, 
            dpi=150)
        
        ax.set_xlabel("Time")
        ax.set_ylabel("Cross-Correlation")
        ax.axhline(0.5, color='k', ls='--', lw=1, alpha=0.5)
        ax.grid(True, lw=0.5, color='gray', alpha=0.5)
        
        kw = dict(ls='none', marker='o', ms=4)

        y = peaks[peaks[:,1] > 0.5]
        ax.plot(y[:,0], y[:,1], c='r', label=">0.5", **kw)

        y = peaks[peaks[:,1] <= 0.5]
        ax.plot(y[:,0], y[:,1], c='b', alpha=0.5, **kw)

        plt.show()

    def run(
        self, 
        start_bin: int=0,
        max_dl: int=5, 
        wait=True, 
        fmt=139, 
        keepfiles=True,
        loc=DATADIR,
        max_wait_time: int=120) -> List[Tuple[int, int]]:
        
        # download clips from source 
        try:
            self.run_ytdl(
                start_bin=start_bin, 
                max_dl=max_dl,
                wait=wait,
                fmt=fmt,
                loc=loc,
                max_wait_time=max_wait_time
            )

        except KeyboardInterrupt:
            raise KeyboardInterrupt
        
        if not self._fnames[0].is_file(): 
            raise FileNotFoundError(
                str(self._fnames)
            )

        candidates: List[Tuple[int, int]] = [] 
        peak_corr: List[float] = []

         
        bins_str = self._bins_str
        delta = self._midtime(0) - self._midtime(1)

        for i, fname in enumerate(self._fnames): 
            
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
            
            result, peak = self.find_times(fname)

            if result is None:
                logging.info(f"Not in {bins_str[i+start_bin]}")
                peak_corr.append([
                    self._midtime(i+start_bin, delta), 
                    peak
                ])
            else:
                logging.info(bins_str[i+start_bin])
                candidates.append(result)
                
                peak_corr.append([
                    self._midtime(
                        [i+start_bin],
                        timedelta(seconds=result[0])
                    ), peak 
                ])
            
            if not keepfiles:
                fname.unlink()

        self.process_peak_corr(peak_corr)
        return candidates 
            
myfinder = Finder(
    source=r"https://youtu.be/kkni4RCxM0A",
    # query=r"https://youtu.be/H8a2odhdruY",
    # start="1:40", stop="1:50", fmt=139, loc=DATADIR,
    query="./data/H8a2odhdruY.m4a"
)

myfinder.get_bins(
    max_binwidth=120,
    clip_edges=100
)

candidates = [] 
max_dl = 15 
start_bin = 0
max_bin = 60
max_wait_time = 200

run_dict = dict(
    max_dl=max_dl,
    fmt=139, 
    loc=DATADIR,
    keepfiles=True,
    max_wait_time=max_wait_time
)

while len(candidates) < 1:
    myfinder.run(
        start_bin=start_bin,
        **run_dict
    )

    start_bin += max_dl 
    if start_bin > max_bin: 
        break 