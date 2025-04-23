from datetime import time, timedelta, datetime

def generate_time_slots(start_time=time(6, 0), end_time=time(22, 0), duration=timedelta(minutes=90)):
    slots = []
    current = datetime.combine(datetime.today(), start_time)
    end = datetime.combine(datetime.today(), end_time)
    while current + duration <= end:
        slots.append((current.time(), (current + duration).time()))
        current += duration
    return slots
