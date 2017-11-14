import os
import re
import time
import whisper
import datetime as dt
from operator import add

FORMAT = "%Y-%m-%d %H:%M:%S"

from_t = time.mktime(dt.datetime.strptime("2017-11-12 00:00:00", FORMAT).timetuple())
until_t = time.mktime(dt.datetime.strptime("2017-11-12 23:59:59", FORMAT).timetuple())


def match(directory, *patterns):
    """
    :param directory:  path file directory
    :param patterns: re pattern
    :return: paths list which match patterns
    """
    result = []
    compiled = []
    for p in patterns:
        compiled.append(re.compile(p))
        result.append([])

    for path in os.listdir(directory):
        for i, p in enumerate(compiled):
            if p.match(path):
                result[i].append(path)

    return result


if __name__ == '__main__':

    patterns = [
        '\d+_up_traffic',
        '\d+_down_traffic',
        '\d+_up_slave_traffic',
        '\d+_down_slave_traffic'
    ]

    for i, paths in enumerate(match('.', *patterns)):
        print('------- %s Mbit/s -------' % patterns[i])
        first = True
        last_values = None
        start = step = None
        for p in paths:
            times, values = whisper.fetch(p, from_t, until_t)
            if first:
                last_values = values
                first = False
            else:
                last_values = map(add, last_values, values)

            start, _, step = times

        t = start
        result = []
        for v in last_values:
            s = time.strftime(FORMAT, time.localtime(t))
            result.append((s, v))
            t += step

        result.sort(key=lambda x: x[1])  # sort by value
        result.reverse()
        t, v = result[0]
        v = v * 8 / 1024 / 1024 / 60
        print(t, v)
