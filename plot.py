from finder.postplot import ReadLog
from pathlib import Path 

p = r"C:/Users/delbe/Documents/CodeRepositories/Miscellaneous/YouTubeClipFinder/8KWnymfSczU_2c.log"

ReadLog(p).read(
    save_csv=True, 
    save_fig=True,
    outpath=Path.cwd() / 'output'
)