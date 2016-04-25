#!/usr/bin/env python
# -*- encoding:utf-8 -*-

"""
File:       BaseGeventThread.pyd.py
Author:     Himyth
"""

from threading import Thread
from .GeventQueueFix import GQueue
import gevent

__all__ = ['BaseGeventThread']


class BaseGeventThread(Thread):

    def __init__(self, tasks, results, cort_num, _cort_num, logger):
        super(BaseGeventThread, self).__init__()

        # tasks have to be of GeventQueue, and bind
        self.results = results
        self._tasks = tasks
        self.tasks = None   # just avoid "declare out of init-scope" warning

        if not str(cort_num).isdigit() or cort_num <= 0:
            cort_num = _cort_num
            name = logger.name.split('.')[-1]
            logger.debug('No valid coroutine number found for [%s], '
                         'set to %d by default' % (name, _cort_num))
        self.coroutine_num = cort_num

        self.worker_args = None

    def run(self):
        # REMEMBER
        # no gevent-related stuff between different threads.
        # this will block forever
        self.tasks = GQueue(self._tasks)
        spawns = [gevent.spawn(self.worker, *self.worker_args)
                  for _ in xrange(self.coroutine_num)]
        gevent.joinall(spawns)

    def worker(self):
        pass
