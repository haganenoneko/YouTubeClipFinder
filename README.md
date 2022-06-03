# YouTubeClipFinder

Experimental tool to find timestamps for YouTube clips.

### How it works (or maybe not)
Given a short audio clip (the 'query') and a link to its source video on YouTube, this tool uses `scipy.correlate` to identify where the query belongs in the source video. 

Since many videos are quite long, this tool 'discretizes' the source video into a set number of bins. The number, order, and width of each bin can be controlled. The bins are grouped into $K$ equally sized sets. The processing occurs after the clips for each set have been downloaded (using `yt-dlp` and `ffmpeg`), and stops when one or more candidate timepoints have been identified. This is to avoid having to download hundreds of clips. 

In general, a cross-correlation score above `0.5` is deemed a 'hit,' but, in truth, a score near or above `1.0` is often necessary. 

There are probably better ways to go about doing this. 

### Progress

An example for how to use this tool can be found at this notebook: [link](https://github.com/haganenoneko/YouTubeClipFinder/blob/main/example.ipynb).

The documentation for some of the functions is a bit outdated, so please bear with me.

### Dependencies
This package was written with `Python 3.10.1`. Besides the libraries in `requirements.txt`, please also make sure that you have `ffmpeg` installed correctly. 