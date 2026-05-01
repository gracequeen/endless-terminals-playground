FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python2.7 \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN ln -sf /usr/bin/python2.7 /usr/bin/python2

RUN pip3 install pytest

RUN mkdir -p /home/user/sensors && chmod 0777 /home/user && chmod 0777 /home/user/sensors

RUN cat << 'EOF' > /home/user/sensors/collect.py
#!/usr/bin/env python
"""
Sensor data collection script.
Aggregates readings from multiple sensors.
"""

import time
import random

# Configuration
SENSORS = ['sensor_1', 'sensor_2', 'sensor_3']
COLLECTION_INTERVAL = 0.1  # seconds between readings


def generate_reading(sensor_id):
    """Generate a simulated sensor reading."""
    base_value = hash(sensor_id) % 100
    noise = random.uniform(-5, 5)
    return round(base_value + noise, 2)


def collect_sensor_data(sensors):
    """Collect data from all configured sensors."""
    readings = {}
    for sensor in sensors:
        print(f"Reading from {sensor}")
        value = generate_reading(sensor)
        readings[sensor] = value
        time.sleep(COLLECTION_INTERVAL)
    return readings


def format_output(readings):
    """Format the readings for output."""
    lines = []
    for sensor, value in readings.items():
        lines.append("{}: {}".format(sensor, value))
    return lines


def main():
    """Main entry point for sensor collection."""
    data = collect_sensor_data(SENSORS)
    output_lines = format_output(data)

    for line in output_lines:
        print(line, flush=True)

    print("Done")
    return 0


if __name__ == '__main__':
    exit(main())
EOF

RUN chmod 0666 /home/user/sensors/collect.py

RUN useradd -m -d /home/user -s /bin/bash user || true

WORKDIR /home/user

USER user

CMD ["/bin/bash"]
