import numpy as np 
import logging, time
from pathlib import Path 
from subprocess import Popen
from typing import List, Tuple, Union 

from findsignal import FindSignal, read_audio_data
from download import get_cmd, run_cmd
import sampling 

DATADIR = Path.cwd() / 'data'
MAXDOWNLOADS = 6
MAXWAITIME = 240

logging.basicConfig(
    filename=Path.cwd() / 'main.log', 
    encoding='utf-8', 
    level=logging.DEBUG
)

url = r"https://youtu.be/kkni4RCxM0A"

class Finder:
    def __init__(
        self, 
        source: str, 
        query: np.ndarray) -> None:
    
        self.url = source 
        self.query = query 
    
    def get_bins(self) -> None:
        dur_int, _ = sampling.get_video_duration(url)
        bins_int = sampling.get_bins(dur_int, clip_edges=100)
        self._bins_str  = sampling.bins2str(bins_int)         

    def run_ytdl(self, **kwargs) -> None:
        cmd_kw = dict(fmt=140, loc=DATADIR)

        self._fnames: List[str] = [] 
        self._running: List[Popen] = []
    
        for i, bin in enumerate(self._bins_str):
            start, stop = bin 
            cmd, fn = get_cmd(url, start, stop, **cmd_kw)
            
            proc = run_cmd(cmd, shell=True, timeout=MAXWAITIME)
            
            self._running.append(proc)
            self._fnames.append(Path(fn))

            if i + 1 >= MAXDOWNLOADS:
                break 
    
        time.sleep(MAXWAITIME)
    
    def find_times(
        self, 
        fname: Path) -> Union[None, Tuple[int, int]]:

        data, rate = read_audio_data(
            fname.stem,
            fname.parent,
            fname.suffix,
        )
        
        result = FindSignal(
            data, self.query, rate
        ).findsignal()
        
        return result 

    def run(self) -> List[Tuple[int, int]]:
        self.get_bins()
        self.run_ytdl()
        
        if not self._fnames[0].is_file(): 
            raise FileNotFoundError(
                self._fnames[0]
            )

        candidates: List[Tuple[int, int]] = [] 

        for i, fname in self._fnames: 
            if not fname.is_file():
                time.sleep(MAXWAITIME/4)
            if not fname.is_file(): 
                proc = self._running[i]
                proc.kill()
                logging.error(
                    proc.communicate()[1])
            
            result = self.find_times(fname)
            if result is None:
                logging.info(f"Not in {self._bins_str[i]}")
                continue 
            else:
                logging.info(f"Candidate: {result}")
                candidates.append(result)

        return candidates 
            

