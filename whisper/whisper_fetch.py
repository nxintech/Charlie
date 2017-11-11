#!/usr/bin/env python
import time
import whisper
import argparse
import datetime as dt

_DROP_FUNCTIONS = {
    'zeroes': lambda x: x != 0,
    'nulls': lambda x: x is not None,
    'empty': lambda x: x != 0 and x is not None
}
FORMAT = "%Y-%m-%d %H:%M:%S"


def parse_args():
    parser = argparse.ArgumentParser(description="whisper fetch")
    parser.add_argument(
        "--from", dest="from_time", type=str,
        help="Time of the beginning of your requested interval"
             "format: %s, (default: 24 hours ago)" % FORMAT)
    parser.add_argument(
        "--until", dest="until_time", type=str,
        help="Time of the end of your requested interval"
             "format: %s, (default: now)" % FORMAT)

    parser.add_argument(
        '-t', '--time-format', default=FORMAT, dest="time_format",
        action='store', type=str,
        help="Time format for showing human-readable timestamps,"
        " (default: %s)" % FORMAT)

    parser.add_argument(
        '--drop', choices=_DROP_FUNCTIONS.keys(), action='store',
        help="Specify 'nulls' to drop all null values. "
             "Specify 'zeroes' to drop all zero values. "
             "Specify 'empty' to drop both null and zero values")

    parser.add_argument(
        "-f", "--file", action="store", help="data file")

    return parser.parse_args()


def fetch(args):
    now = int(time.time())
    yesterday = now - (24 * 60 * 60)

    if args.from_time:
        from_time = time.mktime(
            dt.datetime.strptime(args.from_time, FORMAT).timetuple())
    else:
        from_time = now

    if args.until_time:
        until_time = time.mktime(
            dt.datetime.strptime(args.until_time, FORMAT).timetuple())
    else:
        until_time = yesterday

    times, values = whisper.fetch(args.file, from_time, until_time)

    if args.drop:
        fn = _DROP_FUNCTIONS.get(args.drop)
        values = [x for x in values if fn(x)]

    start, end, step = times

    t = start
    for value in values:

        if args.time_format:
            s = time.strftime(args.time_format, time.localtime(t))
        else:
            s = time.ctime(t)

        print("%s\t%f" % (s, value))

        t += step


if __name__ == '__main__':
    args = parse_args()
    fetch(args)
