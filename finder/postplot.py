import re
import numpy as np
import pandas as pd
from pathlib import Path
from ast import literal_eval
import matplotlib.pyplot as plt
from typing import List, Union, Tuple
from datetime import datetime, timedelta

from finder.main import Finder

# ---------------------------------------------------------------------------- #
#         Post-processing and visualization of candidates in a log file        #
# ---------------------------------------------------------------------------- #

# ------------------ Helper functions to parse the log file ------------------ #


def remove_loginfo_header(s: str) -> str:
    return re.sub("INFO:root:", '', s.strip())


vec_remove_loginfo_header = np.vectorize(remove_loginfo_header)


CORR_PATTERN = re.compile(
    r"^(?:Corr:\s)([\d\.]*)\sStart:\s(\-{0,1}\d+)\s*Stop:\s(\-{0,1}\d+)"
)


def parse_corr_lines(s: str, patt=CORR_PATTERN) -> Tuple[float, int, int]:
    res = re.search(patt, s)

    if not res:
        raise ValueError(f"Could not parse corr from {s}")

    res = res.groups()
    if len(res) != 3:
        raise ValueError(f"Expected 3 values, got:\n{res}")
    return float(res[0]), int(res[1]), int(res[2])


def parse_ts(s: str) -> List[datetime]:
    try:
        lst = literal_eval(s.replace("' '", "','"))
    except:
        raise ValueError(f"Could not parse {s} as a list")

    return [datetime.strptime(s, "%H:%M:%S") for s in lst]

# ------ Main class for processing and visualizing data in the log file ------ #


class ReadLog:
    def __init__(self, path: Union[str, Path]) -> None:
        self.log = path

    def validate_path(self, path: Union[str, Path]) -> bool:

        if isinstance(path, str):
            path = Path(path)
        elif isinstance(path, Path):
            pass
        else:
            raise TypeError

        if not path.is_file():
            raise FileNotFoundError(path)

        self.log = path
        return path

    def _load(self, path: Path) -> List[str]:
        path: Path = self.validate_path(path)
        with open(path, 'r') as io:
            lines = io.readlines()

        ind = next(
            i for i, line in enumerate(lines)
            if "INFO:root:Corr:" in line
        )

        return lines[ind:]

    def _parse(self, lines: List[str]) -> List[Tuple[datetime, float]]:
        lines = vec_remove_loginfo_header(lines)

        parsed = []
        for i in range(0, len(lines), 2):
            corr, ts = lines[i:i+2]
            if 'Corr:' != corr[:5]:
                continue

            try:
                corr, start, _ = parse_corr_lines(corr)
                bin = parse_ts(ts)
            except Exception as e:
                print(e)
                continue

            parsed.append(
                (bin[0] + timedelta(seconds=start), corr)
            )
        return parsed

    def _savecsv(self, outpath: str, parsed: np.ndarray, sort: bool) -> None:

        df = pd.DataFrame(parsed, columns=['Time', 'Correlation'])
        df['Time'] = pd.to_datetime(df['Time']).dt.strftime("%H:%M:%S")

        if sort:
            df.sort_values(
                by='Correlation',
                ascending=False,
                inplace=True
            )

        if Path(outpath).is_file():
            repl = None 
            while repl not in ['y', 'n']:
                repl = input(
                    f"{str(outpath)} exists. Replace? (y/n)"
                ).lower()
                
            if repl == 'n':
                raise FileExistsError(str(outpath))
            
        df.to_csv(outpath)

        print(
            f"Parsed data saved to {outpath}",
            df.head(),
            sep="\n"
        )

    def read(
        self,
        save_fig=False,
        save_csv=False,
        sort_by_corr=True,
        outpath: Union[str, Path] = None) -> None:
        """Read and process a log file containing search results

        Args:
            save_fig (bool, optional): whether to save the figure to a png file. Defaults to False.
            save_csv (bool, optional): whether to save the results to a csv file. Defaults to False.
            sort_by_corr (bool, optional): whether to sort the csv file by correlation. Defaults to True.
            outpath (Union[str, Path], optional): path to save the files at. Defaults to None.
        """

        lines = self._load(self.log)
        parsed = self._parse(lines)

        if outpath is None:
            outpath = Path.cwd()
        elif isinstance(outpath, str):
            outpath = Path(outpath)

        if not outpath.is_dir():
            outpath.mkdir()

        outpath = str(outpath / self.log.stem)

        figpath = outpath + "_log.png" if save_fig else None
        Finder._plot_peak_corr(
            np.array(parsed),
            title=self.log.stem,
            save_path=figpath
        )

        if save_csv:
            self._savecsv(
                outpath + "_parsed.csv",
                parsed,
                sort_by_corr
            )
