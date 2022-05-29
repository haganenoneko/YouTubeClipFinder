import pytest
from typing import List, Tuple 
from pathlib import Path 

import sys 
sys.path.append(
    str(Path.cwd())
)

from finder import download as dl  

# ---------------------------------------------------------------------------- #
#                         Tests for finder/download.py                         #
# ---------------------------------------------------------------------------- #

def test_remove_nonnnumeric():
    assert all(
        dl.removeNonNumeric(u) == "010304" 
        for u in ["01:03:04", "01a03b04c"]
    )

# ---------------------------------------------------------------------------- #

@pytest.fixture
def timestamp_testdata():
    valtest = [
        "103:45:02", "1034502",
        "03:23:11", "3:23:11",
        "00:23:45", "2345",
        "00:70:90", "7090",
        "00:03:34", "03:34", "334",
        "00:00:34", "34"
    ]

    valtrue = [
        "103:45:02",
        "103:45:02",
        "03:23:11",
        "03:23:11",
        "00:23:45",
        "00:23:45",
        "01:11:30",
        "01:11:30",
        "00:03:34",
        "00:03:34",
        "00:03:34",
        "00:00:34",
        "00:00:34"
    ]

    return valtest, valtrue 

def test_get_timestamp(timestamp_testdata: Tuple[List[str]]):
    for x, y in zip(*timestamp_testdata):
        assert dl.getTimestamp(x) == y 

    with pytest.raises(ValueError):
        dl.getTimestamp('')
        dl.getTimestamp('abc')
        dl.getTimestamp('*&@^#')

# ---------------------------------------------------------------------------- #

class Download:
    def __init__(self, *args, **kwargs) -> None:
        self.cmd, self.filename = dl.get_cmd(*args, **kwargs)
    
    def __eq__(self, other: Tuple[str, str]) -> bool:
        cmd, filename = other 
        return (self.cmd == cmd) and (self.filename == filename) 
        
@pytest.fixture
def create_download():
    return Download(
        url = r"https://youtu.be/H8a2odhdruY",
        start = "1:40",
        stop = "1:50",
        fmt = 139, 
        loc = Path.cwd() / 'data'
    )

def test_download_cmd(create_download):
    with open(Path.cwd() / 'tests/test_download_cmd.txt', 'r') as io:
        cmd, f = [line.strip() for line in io.readlines()]
        assert cmd == repr(create_download.cmd)
        assert f == repr(create_download.filename)


