import logging 
from finder.main import Finder, DATADIR

myfinder = Finder(
    source=r"https://youtu.be/bCdnJazCDb0",
    # query=r"https://youtu.be/jJd98IWDn54",
    # start="5:32", stop="5:50", fmt=139, loc=DATADIR,
    query="./data/OsqNklrWQw4.m4a",
    logname="OsqNklrWQw4"
)

myfinder.get_bins(
    max_binwidth=150,
    clip_edges=220,
    binorder="mirrored",
    skipsize=5, 
)

logging.info(myfinder._bins_str)
exit()

candidates = []
max_dl = 20
start_bin = 39
max_bin = 58
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
