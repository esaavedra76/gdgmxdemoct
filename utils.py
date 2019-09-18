from datetime import datetime


def unix_time_millis(dt):
    epoch = datetime.utcfromtimestamp(0)
    return int((dt - epoch).total_seconds() * 1000.0)


def get_utc_timestamp():
    ts = datetime.utcnow()
    return unix_time_millis(ts), ts
