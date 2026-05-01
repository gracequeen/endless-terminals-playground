FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    cron \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

RUN pip3 install pytz pytest

RUN ln -fs /usr/share/zoneinfo/Etc/UTC /etc/localtime && \
    echo "Etc/UTC" > /etc/timezone && \
    dpkg-reconfigure -f noninteractive tzdata

RUN useradd -m -s /bin/bash user && \
    chmod 0777 /home/user

RUN mkdir -p /home/user/scheduler && \
    chown user:user /home/user/scheduler && \
    chmod 0777 /home/user/scheduler

RUN cat <<'EOF' > /home/user/scheduler/app.py
#!/usr/bin/env python3
"""
Meeting reminder application.
Sends reminders 15 minutes before each meeting.
Converts UTC times to Europe/Berlin timezone.
"""

import json
import pytz
from datetime import datetime, timedelta

MEETINGS_FILE = '/home/user/scheduler/meetings.json'
BERLIN_TZ = pytz.timezone('Europe/Berlin')
UTC_TZ = pytz.utc

def load_meetings():
    """Load meetings from JSON file."""
    with open(MEETINGS_FILE, 'r') as f:
        return json.load(f)

def convert_to_berlin(utc_time_str):
    """
    Convert UTC time string to Berlin timezone.
    """
    # Parse the UTC time string
    utc_dt = datetime.strptime(utc_time_str, '%Y-%m-%dT%H:%M:%S')

    # Convert to Berlin time
    # BUG: This incorrectly localizes the UTC datetime as if it were already Berlin time
    berlin_dt = BERLIN_TZ.localize(utc_dt)

    return berlin_dt

def get_current_time_berlin():
    """Get current time in Berlin timezone."""
    return datetime.now(BERLIN_TZ)

def check_reminders():
    """Check for meetings that need reminders (15-75 minutes from now)."""
    meetings = load_meetings()
    now = get_current_time_berlin()

    reminder_start = now + timedelta(minutes=15)
    reminder_end = now + timedelta(minutes=75)

    reminders = []

    for meeting in meetings:
        berlin_time = convert_to_berlin(meeting['utc_time'])

        # Check if meeting falls within reminder window
        if reminder_start <= berlin_time <= reminder_end:
            reminders.append({
                'title': meeting['title'],
                'time': berlin_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')
            })

    return reminders

def main():
    """Main entry point."""
    reminders = check_reminders()

    if reminders:
        print("=== Meeting Reminders ===")
        for reminder in reminders:
            print(f"REMINDER: {reminder['title']} at {reminder['time']}")
    else:
        print("No upcoming meetings in the next 15-75 minutes.")

if __name__ == '__main__':
    main()
EOF

RUN chown user:user /home/user/scheduler/app.py && \
    chmod 0755 /home/user/scheduler/app.py

RUN cat <<'EOF' > /home/user/scheduler/meetings.json
[
    {
        "title": "Daily Standup",
        "utc_time": "2024-03-31T08:00:00"
    },
    {
        "title": "Maintenance Window Prep",
        "utc_time": "2024-03-31T01:30:00"
    },
    {
        "title": "Weekly Review",
        "utc_time": "2024-04-01T14:00:00"
    },
    {
        "title": "Client Call",
        "utc_time": "2024-03-30T15:30:00"
    },
    {
        "title": "Team Lunch",
        "utc_time": "2024-03-29T11:00:00"
    }
]
EOF

RUN chown user:user /home/user/scheduler/meetings.json && \
    chmod 0644 /home/user/scheduler/meetings.json

RUN cat <<'EOF' > /home/user/scheduler/crontab
# Scheduler crontab - runs at the top of every hour
0 * * * * cd /home/user/scheduler && python3 app.py >> /home/user/scheduler/output.log 2>&1
EOF

RUN chown user:user /home/user/scheduler/crontab && \
    chmod 0644 /home/user/scheduler/crontab

RUN cat <<'EOF' > /home/user/scheduler/test_conversion.py
#!/usr/bin/env python3
"""
Test script for timezone conversions.
Used by dev team for manual testing.
"""

import pytz
from datetime import datetime

def test_berlin_conversion():
    """Test that Berlin timezone conversion works."""
    berlin = pytz.timezone('Europe/Berlin')

    # This test passes because it uses datetime.now() with timezone
    # which handles DST correctly
    now_berlin = datetime.now(berlin)
    print(f"Current time in Berlin: {now_berlin}")

    # This also works correctly because we're creating a timezone-aware datetime
    test_dt = berlin.localize(datetime(2024, 6, 15, 12, 0, 0))
    print(f"Test datetime in Berlin: {test_dt}")

    # Convert to UTC and back
    utc = pytz.utc
    test_utc = test_dt.astimezone(utc)
    back_to_berlin = test_utc.astimezone(berlin)
    print(f"Round-trip conversion: {back_to_berlin}")

    assert test_dt == back_to_berlin, "Round-trip conversion failed!"
    print("All tests passed!")

if __name__ == '__main__':
    test_berlin_conversion()
EOF

RUN chown user:user /home/user/scheduler/test_conversion.py && \
    chmod 0755 /home/user/scheduler/test_conversion.py

RUN crontab -u user /home/user/scheduler/crontab

USER user
WORKDIR /home/user

CMD ["/bin/bash"]
