FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

RUN pip3 install pytest

RUN mkdir -p /home/user/profiler /home/user/workload && \
    chmod 0777 /home/user /home/user/profiler /home/user/workload

RUN cat > /home/user/profiler/trace.ini << 'EOF'
[timing]
clock_source = monotonic
include_children = yes
aggregation = cumulative

[output]
format = summary
precision = 6

[filters]
min_duration_ms = 0.1
EOF

RUN cat > /home/user/profiler/trace.py << 'ENDOFFILE'
"""
Custom function-timing profiler with configurable options.
"""

import time
import functools
import configparser
import os
import atexit
from collections import defaultdict

# Load configuration
_config = configparser.ConfigParser()
_config_path = os.path.join(os.path.dirname(__file__), 'trace.ini')
_config.read(_config_path)

# Parse configuration
_clock_source = _config.get('timing', 'clock_source', fallback='monotonic')
_include_children = _config.get('timing', 'include_children', fallback='no')
_aggregation = _config.get('timing', 'aggregation', fallback='cumulative')

_output_format = _config.get('output', 'format', fallback='summary')
_precision = _config.getint('output', 'precision', fallback=6)

_min_duration_ms = _config.getfloat('filters', 'min_duration_ms', fallback=0.0)

# Select clock function
if _clock_source == 'monotonic':
    _clock = time.monotonic
elif _clock_source == 'perf_counter':
    _clock = time.perf_counter
elif _clock_source == 'process_time':
    _clock = time.process_time
else:
    _clock = time.monotonic

# Storage for timing data
_call_stack = []
_timing_data = defaultdict(lambda: {'total_time': 0.0, 'call_count': 0, 'spans': []})
_start_wallclock = None
_end_wallclock = None


def _record_span(func_name, duration):
    """Record a timing span, applying filters."""
    global _min_duration_ms

    # Convert to milliseconds for comparison
    duration_ms = duration * 1000

    # Filter out spans shorter than min_duration_ms
    if duration_ms < _min_duration_ms:
        return  # Drop this span

    _timing_data[func_name]['spans'].append(duration)
    _timing_data[func_name]['call_count'] += 1

    # Handle aggregation based on include_children setting
    if _include_children:
        # This branch is taken because "yes" is truthy
        # But the actual accumulation logic below checks for True specifically
        pass

    if _include_children == True:
        # Cumulative: include time spent in children
        _timing_data[func_name]['total_time'] += duration
    else:
        # Exclusive: this path is taken because "yes" != True
        # Only count exclusive time (subtract nested call time)
        _timing_data[func_name]['total_time'] += duration


def trace(func):
    """Decorator to trace function execution time."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        global _start_wallclock

        if _start_wallclock is None:
            _start_wallclock = _clock()

        func_name = func.__name__
        start_time = _clock()

        # Push onto call stack for nested tracking
        _call_stack.append((func_name, start_time))

        try:
            result = func(*args, **kwargs)
        finally:
            end_time = _clock()

            # Pop from call stack
            _call_stack.pop()

            # Calculate elapsed time
            elapsed = end_time - start_time

            # If we have a parent and include_children is working,
            # we'd attribute this time to parent too
            # But due to the bug, nested time accounting is broken

            _record_span(func_name, elapsed)

        return result

    return wrapper


def _print_summary():
    """Print timing summary at program exit."""
    global _end_wallclock, _start_wallclock

    _end_wallclock = _clock()

    if not _timing_data:
        return

    if _output_format != 'summary':
        return

    print("\n" + "=" * 60)
    print("PROFILER TIMING SUMMARY")
    print("=" * 60)

    total_traced = 0.0

    # Sort by total time descending
    sorted_funcs = sorted(_timing_data.items(), 
                          key=lambda x: x[1]['total_time'], 
                          reverse=True)

    for func_name, data in sorted_funcs:
        total_time = data['total_time']
        call_count = data['call_count']
        avg_time = total_time / call_count if call_count > 0 else 0

        total_traced += total_time

        print(f"{func_name:30s} | "
              f"total: {total_time:.{_precision}f}s | "
              f"calls: {call_count:6d} | "
              f"avg: {avg_time:.{_precision}f}s")

    print("-" * 60)
    print(f"{'TOTAL TRACED TIME':30s} | {total_traced:.{_precision}f}s")

    if _start_wallclock is not None:
        wallclock = _end_wallclock - _start_wallclock
        coverage = (total_traced / wallclock * 100) if wallclock > 0 else 0
        print(f"{'WALLCLOCK TIME':30s} | {wallclock:.{_precision}f}s")
        print(f"{'COVERAGE':30s} | {coverage:.2f}%")

    print("=" * 60)


# Register summary printing at exit
atexit.register(_print_summary)
ENDOFFILE

RUN cat > /home/user/workload/compute.py << 'ENDOFFILE'
"""
Workload script with nested function calls for profiler testing.
"""

import sys
sys.path.insert(0, '/home/user')

from profiler.trace import trace
import time
import math


@trace
def normalize(value):
    """Small helper function - normalizes a value. ~0.05ms each."""
    # Simulate small amount of work
    result = value
    for _ in range(50):
        result = math.sin(result) + math.cos(result)
    return result / 100.0


@trace  
def validate(value):
    """Small helper function - validates a value. ~0.05ms each."""
    # Simulate small amount of work
    result = True
    for _ in range(50):
        result = result and (math.sqrt(abs(value) + 1) > 0)
    return result


@trace
def transform(data):
    """Transform a single data item. Calls normalize and validate."""
    normalized = normalize(data)
    is_valid = validate(normalized)

    if is_valid:
        # Small amount of own work
        result = normalized * 2.0
        for _ in range(20):
            result = math.log(abs(result) + 1)
        return result
    return 0.0


@trace
def process_batch(batch_id, items):
    """Process a batch of items. Calls transform for each."""
    results = []
    for i, item in enumerate(items):
        transformed = transform(item + batch_id * 0.1)
        results.append(transformed)

    # Some own work
    total = sum(results)
    for _ in range(100):
        total = math.sqrt(abs(total) + 1)

    return total


@trace
def main():
    """Main entry point. Processes multiple batches."""
    all_results = []

    # Process 10 batches, each with 100 items
    # This creates deep nesting: main -> process_batch -> transform -> normalize/validate
    for batch_id in range(10):
        items = [float(i) for i in range(100)]
        batch_result = process_batch(batch_id, items)
        all_results.append(batch_result)

    # Final aggregation
    final = sum(all_results)
    for _ in range(200):
        final = math.sin(final) + 1

    print(f"Computation complete. Final result: {final:.6f}")
    return final


if __name__ == '__main__':
    main()
ENDOFFILE

RUN chmod 0666 /home/user/profiler/trace.py /home/user/profiler/trace.ini /home/user/workload/compute.py
