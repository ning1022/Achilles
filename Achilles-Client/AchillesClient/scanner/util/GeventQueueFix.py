#!/usr/bin/env python
# -*- encoding:utf-8 -*-

"""
File:       GeventQueueFix.py
Author:     Himyth

since queue in gevent is not a thread-safe struct, and it needs
at least one event to be in the event loop, as discussed before.
it will be a good idea to have a Queue-putter spawn and a few
Queue-getter spawns, and of course, set the thread-safe Queue.Queue
and un-thread-safe gevent.queue.Queue apart.
this binder here i wrote trying to build a spawn and it will bind
the up-stream queue(safe one) and the down-stream queue(not safe).
whenever need to use not-safe-get, remember to set the binder-spawn.
"""

from gevent.queue import Queue

__all__ = ['GQueue']


# only thing to export
class GQueue(Queue):

    def __init__(self, sys_queue, *args):
        super(GQueue, self).__init__(*args)
        from gevent import spawn
        spawn(_queue_binder, sys_queue, self)


# this bind the up-down stream
def _queue_binder(sys_queue, gevt_queue):
    from gevent import sleep
    while True:
        if sys_queue.empty():
            sleep(0.1)
        else:
            gevt_queue.put(sys_queue.get())
    return
