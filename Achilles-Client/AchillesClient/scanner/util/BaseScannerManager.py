#!/usr/bin/env python
# -*- encoding:utf-8 -*-

"""
File:       BaseScannerManager.py
Author:     Himyth
"""

from .BaseManager import BaseManager
from .Constant import TASK_URL, HTTP_GET, TASK_NO_MORE
from .UrlUtilities import get_path

import re

__all__ = ['BaseScannerManager']


class BaseScannerManager(BaseManager):

    def __init__(self, tasks, results, module):
        self.logout = re.compile(r'.*?(?:sign|check|log)out', re.IGNORECASE)
        super(BaseScannerManager, self).__init__(tasks, results, module)

    def put(self, task):
        if task[0] != TASK_URL:
            return

        task = task[1]

        # only take what carries parameters
        if task.method == HTTP_GET:
            return

        # careful with logout url, save the cookies
        if self.logout.match(get_path(task.url)):
            return

        self.tasks.put(task)

    def kill(self):
        # kill the coroutines
        for i in xrange(self.module.coroutine_num):
            self.tasks.put(TASK_NO_MORE)
