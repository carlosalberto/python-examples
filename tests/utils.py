from __future__ import print_function

import logging
import six
import threading
import time


class RefCount(object):
    '''Thread-safe counter'''
    def __init__(self, count=1):
        self._lock = threading.Lock()
        self._count = count

    def incr(self):
        with self._lock:
            self._count += 1
            return self._count

    def decr(self):
        with self._lock:
            self._count -= 1
            return self._count


def await_until(func, timeout=5.0):
    '''Polls for func() to return True'''
    end_time = time.time() + timeout
    while time.time() < end_time and not func():
        time.sleep(0.01)


def get_logger(name):
    '''Returns a logger with log level set to INFO'''
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger(name)


def get_one_by_tag(spans, key, value):
    '''Return a single Span with a tag value/key from a list,
    errors if more than one is found.'''

    found = []
    for span in spans:
        if span.tags.get(key) == value:
            found.append(span)

    if len(found) > 1:
        raise RuntimeError('Too many values')

    return found[0] if len(found) > 0 else None


def get_one_by_operation_name(spans, name):
    '''Return a single Span with a name from a list,
    errors if more than one is found.'''
    found = []
    for span in spans:
        if span.operation_name == name:
            found.append(span)

    if len(found) > 1:
        raise RuntimeError('Too many values')

    return found[0] if len(found) > 0 else None


def get_tags_count(span, prefix):
    '''Returns the tag count with the given prefix from a Span'''
    test_keys = set()
    for key in six.iterkeys(span.tags):
        if key.startswith(prefix):
            test_keys.add(key)

    return len(test_keys)
