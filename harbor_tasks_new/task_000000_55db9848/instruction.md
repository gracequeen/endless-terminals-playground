I'm a storage admin and I just ran `du -ab /var/data` to get a byte-level inventory of our data directory, but the output is a mess and I need to generate some reports from it. The raw dump is saved at /home/user/disk_inventory.txt.

I need you to process this file and create three specific reports:

**Report 1: /home/user/reports/large_files.txt**
List all regular files (not directories) that are 10MB or larger (10485760 bytes or more). Format each line as:
```
<size_in_mb>MB <filepath>
```
Where size_in_mb is the size converted to megabytes, rounded DOWN to the nearest integer (floor). Sort by size descending (largest first). If two files have the same MB size, sort alphabetically by filepath ascending.

**Report 2: /home/user/reports/extension_summary.csv**
A CSV summarizing total bytes used by each file extension. The extension is whatever comes after the last dot in the filename (e.g., "log" for "app.log", "gz" for "backup.tar.gz"). Files without an extension should be grouped under "NO_EXTENSION". The CSV must have a header row and two columns:
```
extension,total_bytes
```
Sort by total_bytes descending. Extensions should be lowercase.

**Report 3: /home/user/reports/directory_rollup.txt**
For each immediate subdirectory of /var/data (one level deep only), show the total size of all contents within it. Format:
```
<dirname> <total_bytes> <percentage>%
```
Where dirname is just the directory name (not full path), total_bytes is the sum of all files recursively under that directory, and percentage is that directory's share of the total /var/data usage, rounded to one decimal place. Sort by total_bytes descending.

Make sure the /home/user/reports/ directory exists before writing the files. The disk_inventory.txt file uses the standard `du -ab` output format: each line is `<bytes>\t<path>`.
