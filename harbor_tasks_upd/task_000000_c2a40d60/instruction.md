Profiler's giving me bogus numbers on /home/user/workload/compute.py — I instrumented it with the custom tracer at /home/user/profiler/trace.py and the timing breakdown doesn't add up. The config is at /home/user/profiler/trace.ini. Total wallclock for the run is about 2.3s but the profiler reports ~0.8s of traced time across all sections. That's like 65% of execution vanishing.

I've triple-checked that every function in compute.py is decorated, so it's not missing annotations. Feels like the tracer is dropping time somewhere — maybe the way it handles nested calls? Or something with how it reads the ini for the timing mode? idk. The ini has a bunch of knobs for clock sources and aggregation, one of them might be misconfigured but they all look sane to me.

Need the profiler to account for at least 95% of wallclock when I run `python /home/user/workload/compute.py`.
