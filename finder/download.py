from pathlib import Path
import re
import logging
from types import NoneType
from typing import List, Tuple, Union
from subprocess import call, Popen
from datetime import datetime, timedelta
import validators

from finder.common import InvalidArgumentException

# ---------------------------------------------------------------------------- #
#                         Download videos from YouTube                         #
# ---------------------------------------------------------------------------- #

# ------------------------ Setup and helper functions ------------------------ #


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

# ---------- Main functions that create and send command line inputs --------- #


def run_cmd(cmd: List[str], concurrent=True, **kwargs) -> Tuple[str, str]:
    """Run command `cmd` as a concurrent process"""
    if concurrent:
        proc = Popen(cmd, **kwargs)
    else:
        proc = call(cmd, **kwargs)

    return proc


def get_filename(
        url: str,
        loc: Path,
        suffix: Union[str, int],
        how_exists: str = "ignore") -> str:
    """Get output filename from download

    Args:
        url (str): YouTube url
        loc (Path): output directory.
        suffix (str, int): suffix to append to end of filename stem.
    Raises:
        TypeError: Raised if `loc` is not `NoneType` or `Path` type.
    """

    try:
        suffix = '' if (suffix is None) else f"{suffix}"
    except TypeError:
        suffix = ''

    if loc is None:
        fn = url.split("/")[-1] + suffix + '.m4a'
    elif isinstance(loc, Path):
        fn = loc / "{}.m4a".format(
            url.split("/")[-1] + suffix
        )

    if isinstance(fn, Path) and fn.is_file():
        msg = f"{fn.name} already exists."
        if how_exists == 'overwrite':
            logging.info(msg + "\nOverwriting...")
        elif how_exists == 'create':
            logging.info(msg + "\nCreating new file...")
            files = fn.parent.glob(f"{fn.stem}*")
            files = list(files)
            n = len(files) + 1
            fn = f"{fn.parent}/{fn.stem}_{n}.{fn.suffix}"
        elif how_exists == 'ignore':
            logging.info(msg + "\nIgnoring...")
            fn = str(fn)
    else:
        fn = str(fn)

    return fn


def validate_cmd_args(
        url: str,
        fmt: int,
        loc: Path,
        how_exists: str) -> bool:
    """Validates arguments of `get_cmd`"""

    validators.url(url)

    if not fmt in [139, 140]:
        raise ValueError(
            f"Currently, only audio formats (139, 140) are supported, not {fmt}.")

    if not how_exists in ['overwrite', 'create', 'ignore']:
        raise InvalidArgumentException(
            'how_exists', how_exists,
            ['overwrite', 'create', 'ignore']
        )

    if not isinstance(loc, (NoneType, Path)):
        raise TypeError(
            f"Argument `loc` should be NoneType or Path, not {type(loc)}"
        )

    return True


def get_cmd(
        url: str,
        start: str,
        stop: str,
        fmt: int,
        suffix: Union[int, str] = None,
        how_exists: str = 'create',
        loc: Path = None) -> Tuple[str, str]:
    """Create command line input for downloading YouTube video

    Args:
        url (str): YouTube url
        start (str): start timestamp, in HH:MM:SS
        stop (str): stop timestamp, in HH:MM:SS
        fmt (int): `yt-dl` format code
        loc (str, optional): output directory. Defaults to None (`Path.cwd()`).
        suffix (str, int): suffix to append to end of filename stem.
        how_exists (str, Optional): what to do when a file already exists. Defaults to `create`, which creates a new file. 

    Returns:
                Tuple[str, str]: command line input, filename                 
    """

    validate_cmd_args(url, fmt, loc, how_exists)

    start = getTimestamp(start)
    stop = getTimestamp(stop)
    filename = get_filename(url, loc=loc, suffix=suffix)

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
        raise TypeError(
            f"All arguments to `Popen` must be strings:\n{cmd}"
        )

    logging.debug(f"\n\nffmpeg cmd:\n{cmd}")
    return cmd, filename
