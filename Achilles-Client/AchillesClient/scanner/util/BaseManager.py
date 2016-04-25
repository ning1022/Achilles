#!/usr/bin/env python
# -*- encoding:utf-8 -*-

"""
File:       BaseManager.py
Author:     Himyth
"""

# ###########################################
# Template for low level module manager
# ###########################################


class BaseManager(object):

    def put(self, tasks):
        pass

    def kill(self):
        pass

    def __init__(self, tasks, results, module):
        self.tasks = tasks
        self.results = results
        self.module = module

    def start(self):
        self.module.start()

    def get(self):
        _ = []
        while not self.results.empty():
            _.append(self.results.get())
        return _

    def join(self):
        self.module.join()
