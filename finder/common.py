from typing import List, Tuple 

import matplotlib.pyplot as plt 
from matplotlib.dates import DateFormatter

from datetime import datetime
from numpy import vectorize
import time

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

# --------------------------------- Plotting --------------------------------- #

def create_figure() -> Tuple[plt.Figure, plt.Axes]:
    fig, ax = plt.subplots(
        figsize=(8, 4),
        constrained_layout=True,
        dpi=150
    )

    ax.set_xlabel("Time")
    ax.set_ylabel("Cross-Correlation")
    ax.axhline(0.5, color='k', ls='--', lw=1, alpha=0.5)
    ax.grid(True, lw=0.5, color='gray', alpha=0.5)

    ax.xaxis.set_major_formatter(DateFormatter("%H:%M:%S"))
    ax.tick_params(axis='x', labelsize=8, labelrotation=40)

    return fig, ax 