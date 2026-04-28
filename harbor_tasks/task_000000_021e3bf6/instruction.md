Trying to get a handle on memory usage across our staging boxes — dumped /proc/meminfo snapshots from 8 hosts into /home/user/memstats/, one file per host (host01.txt through host08.txt). Need a summary showing which hosts have less than 20% of their MemTotal available as MemAvailable, sorted worst-first. Output to /home/user/low_memory_report.txt, just want hostname and the percentage available, tab-separated.

Also noticed host03's file looks weird, might be truncated or corrupted from the collection script — deal with it gracefully, don't want the whole thing to blow up if one file is bad.
