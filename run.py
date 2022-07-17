from typing import Any
from pathlib import Path 
import logging 
import re 

from finder.main import Finder, DATADIR
from finder.postplot import ReadLog

# ---------------------------------------------------------------------------- #

default_bin_kwargs = dict(
    max_binwidth=150,
    binorder="mirrored",
    skipsize=5, 
)

# ---------------------------------------------------------------------------- #

def read_log(*args, **kwargs):
    ReadLog(*args).read(**kwargs)

def main(
    source_url: str, 
    source_start: str, 
    source_stop: str, 
    dl_fmt: int=139,
    keepfiles=True,
    query_path: Path=None,
    query_url: str=None, 
    dl_query_kwargs: dict[str, Any]={},
    bin_kwargs: dict[str, Any]=default_bin_kwargs,
    max_dl: int=50, 
    start_bin: int=1, 
    max_bin: int=50,
    max_wait_time: int=180,
    datadir: Path=DATADIR) -> None:
        
    if query_path is None:
        if query_url is None:
            raise ValueError(
                "At least one of query_path or query_url must be provided")
        query = query_url 
        query_kwargs = dl_query_kwargs
    else:
        if query_path.is_file():
            query = query_path 
            query_kwargs = {}  
        else:
            raise FileNotFoundError(f"Query does not exist:\n{query_path}")
    
    if not datadir.is_dir():
        raise FileNotFoundError(f"Invalid directory:\n{datadir}")

    myfinder = Finder(
        source=source_url, 
        source_start=source_start, 
        source_stop=source_stop, 
        query=query,
        fmt=dl_fmt, 
        loc=datadir,
        **query_kwargs
    )

    myfinder.get_bins(**bin_kwargs)
    if myfinder.logname.is_file():
        skip = input(
            "Skip to processing the log? [y/n]"
        ).lower()
        
        if skip == 'y':
            read_log(
                myfinder.logname, 
                save_fig=True, save_csv=True
            )
            return 

    logging.info(myfinder._bins_str)
    candidates = []
    run_dict = dict(
        max_dl=max_dl,
        fmt=dl_fmt,
        loc=datadir,
        keepfiles=keepfiles,
        max_wait_time=max_wait_time
    )

    while len(candidates) < 1:
        candidates = myfinder.run(
            start_bin=start_bin,
            **run_dict
        )

        start_bin += max_dl
        if start_bin > max_bin:
            print(f"Finished checking max bins: {max_bin}")
            break
    
    read_log(
        myfinder.logname, 
        save_fig=True, save_csv=True
    )

# ---------------------------------------------------------------------------- #

if __name__ == '__main__':
    main(
        source_url="https://youtu.be/o3JPmWOvfkI",
        source_start="00:05:00",
        source_stop="00:30:00",
        query_path=DATADIR / "uruha_predator_family.m4a",
        max_bin=200,
        keepfiles=True
    )