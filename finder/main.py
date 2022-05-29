from cProfile import run
from turtle import down
from download import get_cmd, run_cmd
from pathlib import Path 
import logging 
import yt_dlp
import time 
from typing import Union 

logging.basicConfig(
    filename=Path.cwd() / 'main.log', 
    encoding='utf-8', 
    level=logging.DEBUG
)

def get_video_duration(url: str, fmt=None) -> Union[int, str]:
    meta: dict = yt_dlp.YoutubeDL().extract_info(
        url, download=False
    )
    seconds = meta['duration']

    if fmt:
        return time.strftime(fmt, seconds)
    else:
        return time 
    
url = r"https://youtu.be/oHP7u5zHYSY"
datadir = Path.cwd() / 'data'

cmd = get_cmd(url, '5030', '5110', 140, 
    loc=datadir, 
    run=True
)

run_cmd(cmd, shell=True)