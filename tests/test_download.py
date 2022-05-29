import pytest
from pathlib import Path 

import sys 
sys.path.append(
    str(Path.cwd())
)

from finder import download as dl  

def test_remove_nonnnumeric():
    assert all(
        dl.removeNonNumeric(u) == "010304" 
        for u in ["01:03:04", "01a03b04c"]
    )

def test_get_timestamp():
    valtest = [
        "103:45:02", "1034502",
        "03:23:11", "3:23:11",
        "00:23:45", "2345",
        "00:70:90", "7090",
        "00:03:34", "03:34", "334",
        "00:00:34", "34"
    ]
    for v in valtest:
        print(
            dl.getTimestamp(v)
        )

class Download:
    def __init__(self, *args, **kwargs) -> None:
        self.cmd = dl.get_cmd(*args, **kwargs)

@pytest.fixture
def create_download():
    return Download(
        url = r"https://youtu.be/H8a2odhdruY",
        start = "1:40",
        stop = "1:50",
        fmt = 139, 
        loc = Path.cwd() / 'data'
    )

test_get_timestamp()