from typing import List
from datetime import datetime
import time
from numpy import vectorize

# ---------------------------------------------------------------------------- #
#                        Common functions and exceptions                       #
# ---------------------------------------------------------------------------- #


class InvalidArgumentException(ValueError):
    def __init__(
            self,
            parname: str,
            val: str,
            allowed: List[str]) -> None:
        super().__init__(
            f"`{parname}` must be one of {allowed}, not {val}"
        )


class NoSignalException(RuntimeError):
    def __init__(self) -> None:
        super().__init__("No signal found.")

# ------------------------ Time and string conversions ----------------------- #


def seconds2str(secs: int, fmt=r"%H:%M:%S") -> str:
    return time.strftime(fmt, time.gmtime(secs))


vec_seconds2str = vectorize(seconds2str)


def str2hms(t: str) -> datetime:
    return datetime.strptime(t, "%H:%M:%S")


def hms2str(s: datetime) -> str:
    return datetime.strftime(s, "%H:%M:%S")
