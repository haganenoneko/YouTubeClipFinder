from pathlib import Path
import re
import logging
from typing import List, Tuple, Type
from subprocess import call, Popen, TimeoutExpired
from datetime import datetime
import validators

__all__ = ['get_cmd']


def removeNonNumeric(s: str) -> str:
    """Remove non-numeric characters from `s`"""
    return re.sub("[^0-9]*", '', s)


def getTimestamp(s: str) -> str:

    # pad with leading zeroes
    n = 6 - len(s)
    if n > 0:
        s = '0'*n + s

    try:
        s = removeNonNumeric(s)
        t = datetime.strptime(s, "%H%M%S")
        return datetime.strftime(t, "%H:%M:%S")
    except ValueError:
        return None


def run_cmd(cmd: List[str], concurrent=True, **kwargs) -> Tuple[str, str]:
    """Run command `cmd` as a concurrent process"""
    if concurrent:
        proc = Popen(cmd, **kwargs)
    else:
        proc = call(cmd, **kwargs)

    return proc


def get_cmd(
        url: str,
        start: str,
        stop: str,
        fmt: int,
        loc: Path = None,
        run=True) -> str:
    """Create command line input for downloading YouTube video

    Args:
                url (str): YouTube url
                start (str): start timestamp, in HH:MM:SS
                stop (str): stop timestamp, in HH:MM:SS
                fmt (int): `yt-dl` format code
                loc (str, optional): output directory. Defaults to None (current directory).
                run (bool, optional): whether to run the command via `subprocess.Popen`. Defaults to True.

    Returns:
                str: command line input
    """

    validators.url(url)
    start = getTimestamp(start)
    stop = getTimestamp(stop)

    if loc:
        filename = loc / "{}.m4a".format(url.split("/")[-1])
    else:
        filename = url.split("/")[-1] + '.m4a'

    if isinstance(filename, Path) and filename.is_file():
        files = list(filename.parent.glob(f"{filename.stem}*"))
        logging.info(f"{filename.name} already exists.\n{files}")
        n = len(files) + 1
        filename = f"{filename.parent}/{filename.stem}_{n}.{filename.suffix}"
    else:
        filename = str(filename)

    if not fmt in [139, 140]:
        raise ValueError(
            f"Currently, only audio formats (139, 140) are supported, not {fmt}.")

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
    return cmd 
