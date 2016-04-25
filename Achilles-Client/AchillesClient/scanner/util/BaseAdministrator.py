#!/usr/bin/env python
# -*- encoding:utf-8 -*-

"""
File:       BaseAdministrator.pyr.py
Author:     Himyth
"""

# ###########################################
# Template for top level administration module
# ###########################################

from threading import Thread
from .Constant import TASK_NOTHING_YET, TASK_NO_MORE


class BaseAdministrator(Thread):

    # override needed
    def handle_result(self):
        pass

    def __init__(self, tasks, results):
        super(BaseAdministrator, self).__init__()
        self.tasks, self.results = tasks, results
        self.managers = []

    def run(self):
        # start all the modules
        self.invoke_all('start')

        while True:
            # waiting for tasks
            try:
                task = self.tasks.get(timeout=1)
            except:
                task = TASK_NOTHING_YET
            if task is TASK_NO_MORE:
                break

            #  task retrived, then feed the children
            if task != TASK_NOTHING_YET:
                self.invoke_all('put', task)

            # take the result
            self.handle_result()

        # kill all the children and join
        self.invoke_all('kill')
        self.invoke_all('join')

        # take the result after children died
        self.handle_result()

    def hand_in(self, _type, obj):
        if len(obj) != 0:
            self.results.put((_type, obj))

    def invoke_all(self, method, *args):
        for manager in self.managers:
            if manager is not None:
                getattr(manager, method)(*args)
