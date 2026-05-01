Ran a backup last night off our PostgreSQL replica — 47 tables should've dumped to /home/user/backup/tables/, one sql.gz per table. Restore test this morning is failing on maybe a third of them, gunzip throws "unexpected end of file". Thing is the job reported success and the file sizes look reasonable, nothing truncated to zero.

    Best guess is something interrupted gzip mid-stream but the wrapper script kept going? Or maybe the parallel jobs clobbered each other writing to the same files somehow. Logs are at /home/user/backup/backup.log if that helps.

    Need the corrupted dumps recovered to valid gzip that pg can actually restore. Whatever's salvageable — I know some might be truly gone. Don't re-dump from the DB, replica's already been promoted and the data's changed.
