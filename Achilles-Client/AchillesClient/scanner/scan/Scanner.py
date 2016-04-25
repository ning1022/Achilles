#!/usr/bin/env python
# -*- encoding:utf-8 -*-

"""
File:       Scanner.py
Author:     Himyth
"""

from .sql.SqlScanner import SqlScannerManager
from .xss.XssScanner import XssScannerManager

from ..util.BaseAdministrator import BaseAdministrator
from ..util.Constant import TASK_MAX_SIZE, RESULT_SQL_INJECTION, \
    RESULT_DOM_XSS, RESULT_REFLECT_XSS
from ..util.BaseManager import BaseManager
from ..util.Constant import TASK_NO_MORE

from logging import getLogger
from Queue import Queue

# monkey patch will take effect globally, this should be notice.
# Theoretically, this will only affect the module that involves
# gevent, and will act just normal in a regular module.
# But it does affect others in some ways. be careful.
# This patch is for serveral modules down below.
from gevent import monkey
monkey.patch_socket()

__all__ = ['ScannerManager']
logger = getLogger(__name__)

SQL_SCANNER = 0
XSS_SCANNER = 1


class Scanner(BaseAdministrator):

    def __init__(self, tasks, results, args):
        super(Scanner, self).__init__(tasks, results)

        self.managers = [(SqlScannerManager(tasks=Queue(maxsize=TASK_MAX_SIZE),
                                            results=Queue(),
                                            args=args['sql_scanner'])
                          if args['sql_scanner']['on'] else None),
                         (XssScannerManager(tasks=Queue(maxsize=TASK_MAX_SIZE),
                                            results=Queue(),
                                            args=args['xss_scanner'])
                          if args['xss_scanner']['on'] else None),
                         # add more managers here
                         ]

    def handle_result(self):
        # handle result of sql_scanner
        # [(url, payload), ...]
        if self.managers[SQL_SCANNER] is not None:
            sql_injections = self.managers[SQL_SCANNER].get()
            self.hand_in(RESULT_SQL_INJECTION, sql_injections)

        # handle result of xss_scanner
        # [(type, (url, payload)), ...]
        if self.managers[XSS_SCANNER] is not None:
            xsss = self.managers[XSS_SCANNER].get()
            self.hand_in(RESULT_DOM_XSS,
                         [_[1] for _ in xsss if _[0] == RESULT_DOM_XSS])
            self.hand_in(RESULT_REFLECT_XSS,
                         [_[1] for _ in xsss if _[0] == RESULT_REFLECT_XSS])

# ################ This is for Manager ################


class ScannerManager(BaseManager):

    def __init__(self, tasks, results, args):
        scanner = Scanner(tasks=tasks,
                          results=results,
                          args=args)
        super(ScannerManager, self).__init__(tasks, results, scanner)
        logger.debug('Started')

    def put(self, task):
        """
        :param task:    different tasks will be passed down as
                        (type, body), filter here
        """
        # maybe some filter for future usage
        self.tasks.put(task)

    def kill(self):
        # kill the scanner
        self.tasks.put(TASK_NO_MORE)

        logger.debug('Exit')
