Batch job at /home/user/pipeline/run.sh keeps dying partway through — says it wrote the checkpoint but when I restart it just reprocesses everything from the beginning. The data's like 50k json records in /home/user/pipeline/data/events.json, supposed to aggregate them into /home/user/pipeline/output/summary.db (sqlite). There's a checkpoint file it writes to /home/user/pipeline/.checkpoint that should let it resume from where it left off if it crashes.

Thing is, I can see the checkpoint file exists after a run, and it has content, but somehow it's not working. Tried adding some prints and the checkpoint-loading code definitely runs, it just acts like there's nothing to resume from. Might be a race condition? Or maybe the checkpoint format is wrong? idk. The sqlite output looks fine for the records it does process before I kill it.

Need it to actually resume properly — kill it midway, restart, it should pick up where it left off without re-doing work or losing data.
