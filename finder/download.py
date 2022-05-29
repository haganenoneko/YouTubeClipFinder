from pathlib import Path
import re
import logging
from typing import List, Tuple
from subprocess import call, Popen
from datetime import datetime, timedelta
import validators


def removeNonNumeric(s: str) -> str:
    """Remove non-numeric characters from `s`"""
    return re.sub("[^0-9]*", '', s)

HMSFMTSTRING = r"{H:02}:{M:02}:{S:02}"
def clip_minsec(hms: List[str]) -> str:

    ss, mm, hh = hms 
    mm += ss // 60 
    hh += mm // 60 
    
    return HMSFMTSTRING.format(
        S=(ss % 60), M=(mm % 60), H=hh
    )

def extract_hms(s: str, n: int) -> str:
        
    ssmmhh = [0]*3
    for i in range(0, 6, 2):
        if i >= n: 
            break 
        elif i > 2 or n < i+2: 
            ssmmhh[i // 2] = int(
                s[:n-i]
            )
            break 
        else:
            ssmmhh[i // 2] = int(
                s[n-(i+2):n-i]
            )

    return clip_minsec(ssmmhh)

def getTimestamp(s: str) -> str:  
    
    s = removeNonNumeric(s)
    n = len(s)
    
    if n < 1:
        raise ValueError(f"Empty timestamp: {s}")
      
    return extract_hms(s, n)


def run_cmd(cmd: List[str], concurrent=True, **kwargs) -> Tuple[str, str]:
    """Run command `cmd` as a concurrent process"""
    if concurrent:
        proc = Popen(cmd, **kwargs)
    else:
        proc = call(cmd, **kwargs)

    return proc


def get_filename(url: str, loc: Path = None) -> str:
    """Get output filename from download

    Args:
        url (str): YouTube url
        loc (Path, optional): output directory. Defaults to None.

    Raises:
        TypeError: Raised if `loc` is not `NoneType` or `Path` type.
    """
    if loc is None:
        fn = url.split("/")[-1] + '.m4a'
    elif isinstance(loc, Path):
        fn = loc / "{}.m4a*".format(
            url.split("/")[-1]
        )
    else:
        raise TypeError(
            f"Argument `loc` should be NoneType or Path, not {type(loc)}"
        )

    if isinstance(fn, Path) and fn.is_file():
        files = fn.parent.glob(f"{fn.stem}*")
        files = list(files)

        logging.info(f"{fn.name} already exists.\n{files}")

        n = len(files) + 1
        fn = f"{fn.parent}/{fn.stem}_{n}.{fn.suffix}"

    else:
        fn = str(fn)

    return fn


def get_cmd(
        url: str,
        start: str,
        stop: str,
        fmt: int,
        loc: Path = None) -> Tuple[str, str]:
    """Create command line input for downloading YouTube video

    Args:
                url (str): YouTube url
                start (str): start timestamp, in HH:MM:SS
                stop (str): stop timestamp, in HH:MM:SS
                fmt (int): `yt-dl` format code
                loc (str, optional): output directory. Defaults to None (current directory).
                run (bool, optional): whether to run the command via `subprocess.Popen`. Defaults to True.

    Returns:
                Tuple[str, str]: command line input, filename                 
    """

    validators.url(url)

    if not fmt in [139, 140]:
        raise ValueError(
            f"Currently, only audio formats (139, 140) are supported, not {fmt}.")

    start = getTimestamp(start)
    stop = getTimestamp(stop)
    filename = get_filename(url, loc=loc)

    ffmpeg_header = "--external-downloader ffmpeg --external-downloader-args"
    ffmpeg_cmd = f"\"ffmpeg_i:-ss {start} -to {stop}\""
    cmd = [
        f"yt-dlp -f {fmt}",
        f"-o \"{filename}\"",
        ffmpeg_header,
        ffmpeg_cmd, url
    ]
    cmd = ' '.join(cmd)

    try:
        assert all(isinstance(x, str) for x in cmd)
    except AssertionError:
        raise TypeError(f"All arguments to `Popen` must be strings:\n{cmd}")

    logging.info(f"\n\nffmpeg cmd:\n{cmd}")
    return cmd, filename
