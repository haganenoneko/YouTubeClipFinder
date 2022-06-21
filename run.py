import logging 
from finder.main import Finder, DATADIR
from finder.postplot import ReadLog

myfinder = Finder(
    source=r"https://youtu.be/mhw5m_hjHzQ",
    query=r"https://youtu.be/d98HkWvzCN4",
    start="00:00", stop="00:50", fmt=139, loc=DATADIR,
    # query="./data/OsqNklrWQw4.m4a",
    # logname="OsqNklrWQw4"
)

myfinder.get_bins(
    max_binwidth=150,
    clip_edges=600,
    binorder="mirrored",
    skipsize=5, 
)

candidates = []
max_dl = 50
start_bin = 1
max_bin = 150
max_wait_time = 180

run_dict = dict(
    max_dl=max_dl,
    fmt=139,
    loc=DATADIR,
    keepfiles=True,
    max_wait_time=max_wait_time
)

while len(candidates) < 1:
    candidates = myfinder.run(
        start_bin=start_bin,
        **run_dict
    )

    start_bin += max_dl
    if start_bin > max_bin:
        break

ReadLog(myfinder.logname).read(save_fig=True, save_csv=True)
